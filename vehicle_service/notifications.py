import logging
import re
import urllib.parse
import requests
from django.conf import settings
from django.urls import reverse
from django.db import IntegrityError
from bookings.models import Notification, WhatsAppLog

logger = logging.getLogger(__name__)

def clean_phone_number(raw_phone):
    """
    Cleans phone string: strips non-digits and ensures international country code.
    Defaults to 91 (India) if 10 digits provided.
    """
    if not raw_phone:
        return ""
    digits = re.sub(r'\D', '', str(raw_phone))
    if len(digits) == 10:
        digits = f"91{digits}"
    return digits if 10 <= len(digits) <= 15 else ""


def send_whatsapp_message(to_phone, message_text, recipient_name='', message_type='GENERIC', booking=None, template_parameters=None):
    """
    Sends WhatsApp message via Meta WhatsApp Business Cloud API.
    Never simulates a send. SENT means the configured provider accepted the request;
    delivery and read receipts are updated separately by the webhook.
    """
    cleaned_phone = clean_phone_number(to_phone)
    idempotency_key = f'{message_type}:{booking.pk}' if booking and message_type == 'BOOKING_ACCEPTED' else ''
    if idempotency_key:
        existing = WhatsAppLog.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing.status in ('SENT', 'DELIVERED', 'READ'), existing

    if not cleaned_phone:
        logger.warning("WhatsApp send aborted: invalid recipient phone number.")

    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v19.0')
    enabled = getattr(settings, 'WHATSAPP_ENABLED', True)

    has_live_credentials = bool(phone_number_id and access_token and enabled and cleaned_phone)

    initial_status = 'PENDING' if has_live_credentials else 'FAILED'
    initial_reason = '' if has_live_credentials else (
        'Invalid recipient phone number.' if not cleaned_phone else
        'WhatsApp Cloud API is disabled or credentials are not configured.'
    )
    try:
        log_entry = WhatsAppLog.objects.create(
            recipient_phone=cleaned_phone or str(to_phone or '')[:20],
            recipient_name=recipient_name,
            message_type=message_type,
            message_body=message_text,
            status=initial_status,
            api_response=initial_reason,
            booking=booking,
            idempotency_key=idempotency_key or None,
        )
    except IntegrityError:
        log_entry = WhatsAppLog.objects.get(idempotency_key=idempotency_key)
        return log_entry.status in ('SENT', 'DELIVERED', 'READ'), log_entry

    if not has_live_credentials:
        logger.warning("WhatsApp unavailable for %s: %s", idempotency_key or message_type, initial_reason)
        return False, log_entry

    template_name = getattr(settings, 'WHATSAPP_BOOKING_ACCEPTED_TEMPLATE', '') if message_type == 'BOOKING_ACCEPTED' else ''
    if message_type == 'BOOKING_ACCEPTED' and not template_name:
        log_entry.status = 'FAILED'
        log_entry.api_response = 'Configure an approved Meta template in WHATSAPP_BOOKING_ACCEPTED_TEMPLATE.'
        log_entry.save(update_fields=['status', 'api_response'])
        logger.error("WhatsApp booking template not configured; booking=%s", getattr(booking, 'pk', None))
        return False, log_entry

    if has_live_credentials:
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": cleaned_phone,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message_text
            }
        }
        if template_name:
            payload['type'] = 'template'
            payload['template'] = {
                'name': template_name,
                'language': {'code': getattr(settings, 'WHATSAPP_TEMPLATE_LANGUAGE', 'en_US')},
                'components': [{'type': 'body', 'parameters': [
                    {'type': 'text', 'text': str(value)[:1024]}
                    for value in (template_parameters or [])
                ]}],
            }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            resp_data = response.text
            try:
                data = response.json()
            except ValueError:
                data = {}
            accepted = response.status_code == 200 and bool(data.get('messages'))
            status = 'SENT' if accepted else 'FAILED'
            log_entry.status = status
            log_entry.provider_message_id = (data.get('messages') or [{}])[0].get('id', '') if accepted else ''
            log_entry.api_response = resp_data[:1000]
            log_entry.save(update_fields=['status', 'provider_message_id', 'api_response'])
            logger.info("WhatsApp API request for booking=%s status=%s", getattr(booking, 'pk', None), status)
            return (status == 'SENT'), log_entry
        except Exception as e:
            logger.exception("WhatsApp Cloud API request failed for booking=%s", getattr(booking, 'pk', None))
            log_entry.status = 'FAILED'
            log_entry.api_response = f"{type(e).__name__}: {str(e)[:900]}"
            log_entry.save(update_fields=['status', 'api_response'])
            return False, log_entry


def notify_estimate_approved(booking):
    """
    Called when customer clicks [Approve Estimate]:
    1. Creates Django Notification in MySQL for Workshop Dashboard pop-up.
    2. Sends WhatsApp message to Workshop official number.
    """
    mechanic = booking.mechanic
    customer = booking.customer
    customer_name = customer.user.get_full_name() or customer.user.username
    mechanic_name = mechanic.workshop_name or mechanic.user.get_full_name() or mechanic.user.username
    site_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')

    title = "Estimate Approved by Customer! 🎉"
    message = (
        f"Customer {customer_name} has APPROVED your repair estimate of ₹{booking.estimated_total} "
        f"for {booking.vehicle.vehicle_name} ({booking.vehicle.vehicle_number}). "
        f"You can now proceed with the repair work."
    )

    # 1. In-App Notification (triggers Workshop Dashboard pop-up)
    notification = Notification.objects.create(
        recipient=mechanic.user,
        title=title,
        message=message,
        notification_type='ESTIMATE_APPROVED',
        booking=booking,
        action_url='/mechanic/jobs/active/'
    )

    # 2. WhatsApp Message to Workshop Official Number
    whatsapp_body = (
        f"🔔 *Auto Fix Notification: Repair Estimate APPROVED!* 🔔\n\n"
        f"Hello *{mechanic_name}*,\n"
        f"Great news! Customer *{customer_name}* has officially approved your repair estimate.\n\n"
        f"🚗 *Vehicle:* {booking.vehicle.vehicle_name} ({booking.vehicle.vehicle_number})\n"
        f"📋 *Booking ID:* {booking.booking_number}\n"
        f"💰 *Approved Estimate:* ₹{booking.estimated_total}\n"
        f"   • Labour Charge: ₹{booking.estimated_labour}\n"
        f"   • Parts Quote: ₹{booking.estimated_parts}\n"
        f"📝 *Diagnosis:* {booking.estimate_notes or 'Standard overhaul'}\n\n"
        f"✅ *Action:* You can now proceed with the repair work at your workshop!\n"
        f"👉 Manage active jobs: {site_url}/mechanic/jobs/active/"
    )

    send_whatsapp_message(
        to_phone=mechanic.phone,
        message_text=whatsapp_body,
        recipient_name=mechanic_name,
        message_type='ESTIMATE_APPROVED',
        booking=booking
    )

    return notification


def notify_service_completed(booking, invoice):
    """
    Called when mechanic completes job and generates invoice:
    1. Creates Django Notification in MySQL for Customer.
    2. Sends WhatsApp message to Customer with final bill & invoice link.
    """
    customer = booking.customer
    mechanic = booking.mechanic
    customer_name = customer.user.get_full_name() or customer.user.username
    mechanic_name = mechanic.workshop_name or mechanic.user.get_full_name() or mechanic.user.username
    site_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')

    title = "Vehicle Service Completed! 🏁"
    message = (
        f"Your {booking.vehicle.vehicle_name} ({booking.vehicle.vehicle_number}) service is COMPLETED by {mechanic_name}! "
        f"Total bill: ₹{invoice.total_amount}. Vehicle is ready for pickup."
    )

    # 1. In-App Notification for Customer
    notification = Notification.objects.create(
        recipient=customer.user,
        title=title,
        message=message,
        notification_type='JOB_COMPLETED',
        booking=booking,
        action_url=f"/billing/invoice/{booking.id}/"
    )

    # 2. WhatsApp Message to Customer
    whatsapp_body = (
        f"✅ *Auto Fix: Vehicle Service Completed!* 🏁\n\n"
        f"Hello *{customer_name}*,\n"
        f"Your vehicle service has been successfully *COMPLETED* by *{mechanic_name}*.\n\n"
        f"🚗 *Vehicle:* {booking.vehicle.vehicle_name} ({booking.vehicle.vehicle_number})\n"
        f"📋 *Booking ID:* {booking.booking_number}\n"
        f"📄 *Invoice No:* {invoice.invoice_number}\n"
        f"💵 *Total Amount:* *₹{invoice.total_amount}* (includes 18% GST)\n\n"
        f"📍 *Pickup Location:*\n"
        f"{mechanic.address or mechanic_name}, {mechanic.city}\n"
        f"📞 Workshop Contact: {mechanic.phone}\n\n"
        f"💳 *View itemized bill & pay online:*\n"
        f"{site_url}/billing/invoice/{booking.id}/\n\n"
        f"Thank you for trusting Auto Fix!"
    )

    send_whatsapp_message(
        to_phone=customer.phone,
        message_text=whatsapp_body,
        recipient_name=customer_name,
        message_type='JOB_COMPLETED',
        booking=booking
    )

    return notification


def notify_booking_accepted(booking):
    """
    Called when mechanic accepts a booking:
    1. Creates Django in-app Notification for the Customer.
    2. Sends WhatsApp message to Customer's phone with the mechanic's WORKPLACE / WORKSHOP ADDRESS & contact info!
    """
    customer = booking.customer
    mechanic = booking.mechanic
    customer_name = customer.user.get_full_name() or customer.user.username
    mechanic_name = mechanic.workshop_name or mechanic.user.get_full_name() or mechanic.user.username
    site_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')

    title = "Booking Accepted by Mechanic! 🔧"
    message = (
        f"Your booking #{booking.booking_number} for {booking.vehicle.vehicle_name} was accepted by {mechanic_name}. "
        f"Workshop address: {mechanic.address}, {mechanic.city}."
    )

    # 1. In-app notification
    notification, _ = Notification.objects.get_or_create(
        recipient=customer.user,
        notification_type='NEW_BOOKING',
        booking=booking,
        defaults={'title': title, 'message': message, 'action_url': f"/customer/bookings/{booking.id}/"}
    )

    # 2. WhatsApp to Customer with Workshop Address
    maps_query = urllib.parse.quote(f"{mechanic.workshop_name or 'Workshop'} {mechanic.address} {mechanic.city}")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query}"

    whatsapp_body = (
        f"🎉 *Auto Fix: Booking Accepted by Mechanic!* 🔧\n\n"
        f"Hello *{customer_name}*,\n"
        f"Great news! Mechanic *{mechanic_name}* has accepted your service booking.\n\n"
        f"🚗 *Vehicle:* {booking.vehicle.vehicle_name} ({booking.vehicle.vehicle_number})\n"
        f"📋 *Booking ID:* {booking.booking_number}\n"
        f"🔧 *Service:* {booking.service.service_name}\n"
        f"📅 *Appointment:* {booking.appointment_date.strftime('%d %b %Y')} at {booking.appointment_time.strftime('%I:%M %p')}\n\n"
        f"📍 *Workshop Address to Drop Your Vehicle:*\n"
        f"*{mechanic.workshop_name or 'Workshop'}*\n"
        f"{mechanic.address or 'Address on file'}\n"
        f"{mechanic.city}\n"
        f"🗺️ *Directions:* {maps_link}\n"
        f"📞 *Mechanic Phone:* {mechanic.phone}\n\n"
        f"Please bring your vehicle to the workshop at the scheduled time.\n"
        f"👉 View booking details: {site_url}/customer/bookings/{booking.id}/\n\n"
        f"Thank you for choosing Auto Fix!"
    )

    full_address = ', '.join(part.strip() for part in (mechanic.address, mechanic.city) if part and part.strip())
    params = [customer_name, booking.booking_number, booking.vehicle.vehicle_name,
              booking.vehicle.vehicle_number, booking.service.service_name,
              mechanic_name, mechanic.workshop_name or mechanic_name,
              full_address, mechanic.phone,
              f"{booking.appointment_date:%d %b %Y} {booking.appointment_time:%I:%M %p}"]
    send_whatsapp_message(
        to_phone=customer.phone,
        message_text=whatsapp_body,
        recipient_name=customer_name,
        message_type='BOOKING_ACCEPTED',
        booking=booking,
        template_parameters=params,
    )

    return notification


def update_whatsapp_delivery(provider_message_id, status, details=''):
    """Apply a Meta webhook status update to the matching outbound message."""
    mapping = {'sent': 'SENT', 'delivered': 'DELIVERED', 'read': 'READ', 'failed': 'FAILED'}
    local_status = mapping.get((status or '').lower())
    if not local_status or not provider_message_id:
        return False
    updated = WhatsAppLog.objects.filter(provider_message_id=provider_message_id).update(
        status=local_status, api_response=(details or f'Meta webhook status: {status}')[:1000]
    )
    return bool(updated)


