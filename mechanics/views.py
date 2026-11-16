from decimal import Decimal
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from bookings.models import Booking, Notification, WhatsAppLog
from billing.models import Invoice, Payment, Review
from services.models import Service
from vehicle_service.notifications import notify_service_completed, notify_booking_accepted
from .models import MechanicService
from .forms import CompleteJobForm, MechanicServiceForm, ProvideEstimateForm, WorkshopPaymentSettingsForm

logger = logging.getLogger(__name__)

def mechanic_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'mechanic_profile'):
            messages.error(request, "Access restricted to Mechanic accounts.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


@mechanic_required
def mechanic_dashboard(request):
    mechanic = request.user.mechanic_profile
    all_bookings = Booking.objects.filter(mechanic=mechanic)

    pending_requests = all_bookings.filter(status='PENDING')
    active_jobs = all_bookings.filter(status__in=['ACCEPTED', 'VEHICLE_RECEIVED', 'ESTIMATE_SENT', 'IN_PROGRESS'])
    completed_jobs = all_bookings.filter(status='COMPLETED')
    pending_estimates_count = all_bookings.filter(status='ESTIMATE_SENT').count()

    # Earnings
    invoices = Invoice.objects.filter(booking__mechanic=mechanic, booking__status='COMPLETED')
    total_earnings = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Average rating & reviews
    reviews = Review.objects.filter(mechanic=mechanic).order_by('-created_at')[:5]

    context = {
        'mechanic': mechanic,
        'pending_requests': pending_requests,
        'active_jobs': active_jobs,
        'pending_estimates_count': pending_estimates_count,
        'completed_jobs_count': completed_jobs.count(),
        'total_earnings': total_earnings,
        'recent_reviews': reviews,
    }
    return render(request, 'mechanic/dashboard.html', context)


@mechanic_required
def toggle_availability(request):
    mechanic = request.user.mechanic_profile
    if request.method == 'POST':
        mechanic.is_available = not mechanic.is_available
        mechanic.save()
        status_text = "Available for bookings" if mechanic.is_available else "Marked as Busy / Unavailable"
        messages.success(request, f"Availability status updated: {status_text}")
    return redirect('mechanic_dashboard')


@mechanic_required
def booking_requests(request):
    mechanic = request.user.mechanic_profile
    requests_list = Booking.objects.filter(mechanic=mechanic, status='PENDING').order_by('-created_at')
    return render(request, 'mechanic/booking_requests.html', {'requests': requests_list})


@mechanic_required
def accept_booking(request, booking_id):
    mechanic = request.user.mechanic_profile
    booking = get_object_or_404(Booking, id=booking_id, mechanic=mechanic)

    if booking.status != 'PENDING':
        messages.warning(request, "This booking has already been processed.")
        return redirect('mechanic_dashboard')

    if request.method == 'POST':
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking.pk, mechanic=mechanic)
            if booking.status != 'PENDING':
                messages.warning(request, "This booking has already been processed.")
                return redirect('mechanic_dashboard')
            booking.status = 'ACCEPTED'
            booking.save(update_fields=['status', 'updated_at'])

        try:
            notify_booking_accepted(booking)
        except Exception:
            logger.exception("Booking acceptance notification failed for booking %s", booking.booking_number)
        wa_log = WhatsAppLog.objects.filter(booking=booking, message_type='BOOKING_ACCEPTED').first()
        if wa_log and wa_log.status in ('SENT', 'DELIVERED', 'READ'):
            messages.success(request, f"Booking #{booking.booking_number} accepted. WhatsApp status: {wa_log.get_status_display()}.")
        else:
            reason = wa_log.api_response if wa_log else 'Notification could not be recorded.'
            messages.warning(request, f"Booking #{booking.booking_number} accepted, but WhatsApp was not sent. {reason[:180]}")
        return redirect('active_jobs')

    return render(request, 'mechanic/booking_action.html', {'booking': booking, 'action': 'accept'})


@mechanic_required
def reject_booking(request, booking_id):
    mechanic = request.user.mechanic_profile
    booking = get_object_or_404(Booking, id=booking_id, mechanic=mechanic)

    if booking.status != 'PENDING':
        messages.warning(request, "This booking has already been processed.")
        return redirect('mechanic_dashboard')

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip()
        booking.status = 'REJECTED'
        booking.rejection_reason = reason or "Mechanic unavailable at requested schedule."
        booking.save()
        messages.info(request, f"Booking #{booking.booking_number} rejected.")
        return redirect('mechanic_dashboard')

    return render(request, 'mechanic/booking_action.html', {'booking': booking, 'action': 'reject'})


@mechanic_required
def active_jobs(request):
    mechanic = request.user.mechanic_profile
    jobs = Booking.objects.filter(mechanic=mechanic, status__in=['ACCEPTED', 'VEHICLE_RECEIVED', 'ESTIMATE_SENT', 'IN_PROGRESS']).order_by('appointment_date')
    return render(request, 'mechanic/active_jobs.html', {'jobs': jobs})


@mechanic_required
def provide_estimate(request, booking_id):
    mechanic = request.user.mechanic_profile
    booking = get_object_or_404(Booking, id=booking_id, mechanic=mechanic)

    if booking.status not in ['VEHICLE_RECEIVED', 'ESTIMATE_SENT', 'ACCEPTED']:
        messages.warning(request, "Cost estimate can only be submitted once the vehicle reaches your workshop.")
        return redirect('active_jobs')

    if request.method == 'POST':
        form = ProvideEstimateForm(request.POST)
        if form.is_valid():
            labour = form.cleaned_data['estimated_labour']
            parts = form.cleaned_data['estimated_parts']
            notes = form.cleaned_data['estimate_notes']
            total = labour + parts

            booking.estimated_labour = labour
            booking.estimated_parts = parts
            booking.estimated_total = total
            booking.estimate_notes = notes
            booking.estimate_created_at = timezone.now()
            booking.status = 'ESTIMATE_SENT'
            booking.save()

            messages.success(request, f"Estimate of ₹{total} sent to customer {booking.customer.user.get_full_name() or booking.customer.user.username} for approval!")
            return redirect('active_jobs')
    else:
        default_labour = booking.estimated_labour if (booking.estimated_labour and booking.estimated_labour > 0) else mechanic.hourly_rate
        default_parts = booking.estimated_parts if booking.estimated_parts is not None else Decimal('0.00')
        default_notes = booking.estimate_notes or (f"Vehicle Inspection & Problem Diagnosis:\nCustomer Reported: {booking.customer_notes or 'General Checkup'}\nFindings & Recommended Replacements: ")
        form = ProvideEstimateForm(initial={
            'estimated_labour': default_labour,
            'estimated_parts': default_parts,
            'estimate_notes': default_notes
        })

    return render(request, 'mechanic/provide_estimate.html', {'booking': booking, 'form': form})


@mechanic_required
def update_job_status(request, booking_id):
    mechanic = request.user.mechanic_profile
    booking = get_object_or_404(Booking, id=booking_id, mechanic=mechanic)

    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        notes = request.POST.get('mechanic_notes', '').strip()

        allowed_transitions = {
            'ACCEPTED': ['VEHICLE_RECEIVED'],
            'VEHICLE_RECEIVED': ['IN_PROGRESS'],
            'IN_PROGRESS': ['COMPLETED'],
        }

        if new_status in allowed_transitions.get(booking.status, []):
            if new_status == 'COMPLETED':
                return redirect('complete_job', booking_id=booking.id)
            booking.status = new_status
            if notes:
                booking.mechanic_notes = notes
            booking.save()
            messages.success(request, f"Job #{booking.booking_number} updated to '{booking.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status transition.")

    return redirect('active_jobs')


@mechanic_required
def complete_job(request, booking_id):
    mechanic = request.user.mechanic_profile
    booking = get_object_or_404(Booking, id=booking_id, mechanic=mechanic)

    if booking.status == 'COMPLETED':
        messages.info(request, "This job is already marked as completed.")
        return redirect('invoice_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = CompleteJobForm(request.POST)
        if form.is_valid():
            notes = form.cleaned_data.get('mechanic_notes')
            labour_charge = form.cleaned_data['labour_charge']
            parts_charge = form.cleaned_data['parts_charge']
            parts_details = form.cleaned_data.get('parts_details', '')

            # If estimate-based, service_charge is 0.00 (labour + parts cover it)
            if booking.service.price_type == 'ESTIMATE':
                service_charge = Decimal('0.00')
            else:
                mech_service = MechanicService.objects.filter(mechanic=mechanic, service=booking.service).first()
                service_charge = mech_service.custom_price if mech_service else booking.service.base_price

            # Update booking status
            booking.status = 'COMPLETED'
            if notes:
                booking.mechanic_notes = notes
            booking.save()

            # Create or update invoice
            invoice, created = Invoice.objects.get_or_create(
                booking=booking,
                defaults={
                    'service_charge': service_charge,
                    'labour_charge': labour_charge,
                    'parts_charge': parts_charge,
                    'parts_details': parts_details,
                    'is_paid': False
                }
            )
            if not created:
                invoice.service_charge = service_charge
                invoice.labour_charge = labour_charge
                invoice.parts_charge = parts_charge
                invoice.parts_details = parts_details
                invoice.save()

            # Automatic WhatsApp & in-app notification to customer
            try:
                notify_service_completed(booking, invoice)
            except Exception as e:
                pass

            messages.success(request, f"Job #{booking.booking_number} completed, Invoice #{invoice.invoice_number} generated, and WhatsApp notification sent to customer!")
            return redirect('invoice_detail', booking_id=booking.id)
    else:
        # Prepopulate with estimate values if available, else standard defaults
        initial_labour = booking.estimated_labour if (booking.estimated_labour and booking.estimated_labour > 0) else mechanic.hourly_rate
        initial_parts = booking.estimated_parts if booking.estimated_parts is not None else Decimal('0.00')
        initial_parts_details = booking.estimate_notes or ''
        form = CompleteJobForm(initial={
            'labour_charge': initial_labour,
            'parts_charge': initial_parts,
            'parts_details': initial_parts_details,
            'mechanic_notes': booking.mechanic_notes or booking.estimate_notes
        })

    return render(request, 'mechanic/complete_job.html', {'booking': booking, 'form': form})


@mechanic_required
def mechanic_services(request):
    mechanic = request.user.mechanic_profile
    current_services = MechanicService.objects.filter(mechanic=mechanic)
    all_services = Service.objects.filter(is_active=True)

    if request.method == 'POST':
        form = MechanicServiceForm(request.POST)
        if form.is_valid():
            mech_service = form.save(commit=False)
            mech_service.mechanic = mechanic
            mech_service.save()
            messages.success(request, f"Service '{mech_service.service.service_name}' added to your portfolio!")
            return redirect('mechanic_services')
    else:
        form = MechanicServiceForm()

    return render(request, 'mechanic/manage_services.html', {
        'current_services': current_services,
        'all_services': all_services,
        'form': form,
    })


@mechanic_required
def mechanic_earnings(request):
    mechanic = request.user.mechanic_profile
    invoices = Invoice.objects.filter(booking__mechanic=mechanic, booking__status='COMPLETED').order_by('-created_at')
    total_earnings = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    paid_earnings = invoices.filter(is_paid=True).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    return render(request, 'mechanic/earnings.html', {
        'invoices': invoices,
        'total_earnings': total_earnings,
        'paid_earnings': paid_earnings,
    })


@mechanic_required
def confirm_cash_received(request, invoice_id):
    if request.method != 'POST':
        return redirect('mechanic_earnings')
    mechanic = request.user.mechanic_profile
    with transaction.atomic():
        invoice = get_object_or_404(
            Invoice.objects.select_for_update(), id=invoice_id, booking__mechanic=mechanic
        )
        payment = Payment.objects.select_for_update().filter(
            invoice=invoice, payment_method='CASH', payment_status='PENDING'
        ).order_by('-paid_at').first()
        if invoice.is_paid:
            messages.info(request, f"Invoice {invoice.invoice_number} is already paid.")
        elif not payment:
            messages.error(request, 'No pending cash payment was found for this invoice.')
        else:
            payment.payment_status = 'SUCCESS'
            payment.save(update_fields=['payment_status'])
            invoice.is_paid = True
            invoice.save(update_fields=['is_paid', 'updated_at'])
            messages.success(request, f"Cash of ₹{payment.amount} received and recorded for invoice {invoice.invoice_number}.")
    return redirect('mechanic_earnings')


@mechanic_required
def get_unread_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:5]
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'action_url': n.action_url or '/mechanic/jobs/active/',
            'created_at': n.created_at.strftime('%I:%M %p')
        }
        for n in notifications
    ]
    return JsonResponse({'unread_count': len(data), 'notifications': data})


@mechanic_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        Notification.objects.filter(id=notification_id, recipient=request.user).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'invalid method'}, status=400)


@mechanic_required
def whatsapp_logs(request):
    mechanic = request.user.mechanic_profile
    logs = WhatsAppLog.objects.filter(booking__mechanic=mechanic).order_by('-created_at')[:30]
    return render(request, 'mechanic/whatsapp_logs.html', {'logs': logs})


@mechanic_required
def workshop_qr_settings(request):
    mechanic = request.user.mechanic_profile
    if request.method == 'POST':
        form = WorkshopPaymentSettingsForm(request.POST, request.FILES, instance=mechanic)
        if form.is_valid():
            form.save()
            messages.success(request, "Workshop payment QR and UPI settings updated successfully!")
            return redirect('workshop_qr_settings')
    else:
        form = WorkshopPaymentSettingsForm(instance=mechanic)

    current_qr_url = mechanic.get_upi_qr_url(amount=100.00, invoice_number='SAMPLE')

    return render(request, 'mechanic/qr_settings.html', {
        'mechanic': mechanic,
        'form': form,
        'current_qr_url': current_qr_url,
    })

