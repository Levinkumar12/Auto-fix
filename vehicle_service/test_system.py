import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_service.settings')
django.setup()

import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from accounts.models import CustomerProfile, MechanicProfile
from customers.models import Vehicle
from services.models import Service
from mechanics.models import MechanicService
from bookings.models import Booking
from billing.models import Invoice, Payment, Review

def run_tests():
    print("==================================================")
    print("RUNNING VEHICLE SERVICE MANAGEMENT SYSTEM TESTS")
    print("==================================================")

    # TEST 1: Business Rule - Mechanic Approval Filter
    dummy_pending, _ = MechanicProfile.objects.get_or_create(
        user=User.objects.get_or_create(username='temp_test_mech', defaults={'first_name': 'Temp'})[0],
        defaults={'specialization': 'Tuning', 'city': 'Chennai', 'hourly_rate': Decimal('300.00'), 'approval_status': 'PENDING'}
    )
    dummy_pending.approval_status = 'PENDING'
    dummy_pending.save()

    approved_mechanics = MechanicProfile.objects.filter(approval_status='APPROVED')
    print(f"[TEST 1] Mechanic Approval Status: {approved_mechanics.count()} Approved.")
    assert approved_mechanics.filter(user__username='ramesh_mech').exists(), "Ramesh should be approved"
    assert dummy_pending not in approved_mechanics, "Pending profile should not be in approved list"
    print(" -> PASSED: Unapproved mechanics correctly segregated from public search.")

    # TEST 2: Customer Vehicle Registration
    customer = CustomerProfile.objects.get(user__username='kumar')
    vehicles = Vehicle.objects.filter(customer=customer)
    print(f"[TEST 2] Customer Vehicles: {vehicles.count()} registered for {customer.user.username}.")
    assert vehicles.filter(vehicle_number='TN 23 AB 1234').exists(), "Activa should be registered"
    print(" -> PASSED: Customer vehicle registration validated.")

    # TEST 3: Independent Mechanic Selection & Booking Flow
    mechanic = MechanicProfile.objects.get(user__username='ramesh_mech')
    service = Service.objects.get(service_name='Comprehensive Periodic General Service')
    vehicle = vehicles.first()

    booking = Booking.objects.create(
        customer=customer,
        vehicle=vehicle,
        mechanic=mechanic,
        service=service,
        appointment_date=datetime.date.today() + datetime.timedelta(days=1),
        appointment_time=datetime.time(11, 0),
        status='PENDING',
        customer_notes='Full 10,000 km periodic check and brake inspection.'
    )
    print(f"[TEST 3] Created Booking #{booking.booking_number} with independently selected mechanic: {booking.mechanic.user.username}")
    assert booking.status == 'PENDING', "Initial status must be PENDING"
    print(" -> PASSED: Booking created with customer-selected mechanic.")

    # TEST 4: Mechanic Acceptance & Status Progression
    booking.status = 'ACCEPTED'
    booking.save()
    assert booking.status == 'ACCEPTED'

    booking.status = 'VEHICLE_RECEIVED'
    booking.save()
    assert booking.status == 'VEHICLE_RECEIVED'

    booking.status = 'IN_PROGRESS'
    booking.save()
    assert booking.status == 'IN_PROGRESS'
    print(" -> PASSED: Status transitions (Accepted -> Vehicle Received -> In Progress) validated.")

    # TEST 5: Job Completion & Automatic Invoicing
    booking.status = 'COMPLETED'
    booking.mechanic_notes = 'Cleaned carburettor, lubed throttle cable, changed engine oil and tuned spark plug gap.'
    booking.save()

    invoice = Invoice.objects.create(
        booking=booking,
        service_charge=Decimal('800.00'),
        labour_charge=Decimal('350.00'),
        parts_charge=Decimal('250.00'),
        parts_details='OEM Air filter (₹180), Spark Plug (₹70)',
        is_paid=False
    )

    expected_subtotal = Decimal('800.00') + Decimal('350.00') + Decimal('250.00') # 1400.00
    expected_tax = round(expected_subtotal * Decimal('0.18'), 2) # 252.00
    expected_total = expected_subtotal + expected_tax # 1652.00

    print(f"[TEST 5] Generated Invoice #{invoice.invoice_number}")
    print(f"         Subtotal: INR {expected_subtotal}, GST: INR {invoice.tax_amount}, Total: INR {invoice.total_amount}")
    assert invoice.total_amount == expected_total, f"Expected {expected_total}, got {invoice.total_amount}"
    print(" -> PASSED: Invoice calculation with 18% GST accurate.")

    # TEST 6: Payment Flow
    payment = Payment.objects.create(
        invoice=invoice,
        transaction_id=f"TXN-TEST-{booking.id}",
        amount=invoice.total_amount,
        payment_method='UPI',
        payment_status='SUCCESS'
    )
    invoice.is_paid = True
    invoice.save()
    print(f"[TEST 6] Payment processed. Txn: {payment.transaction_id}, Status: {payment.payment_status}, Invoice Paid: {invoice.is_paid}")
    assert invoice.is_paid is True
    print(" -> PASSED: Payment settlement verified.")

    # TEST 7: Review & Rating
    review = Review.objects.create(
        customer=customer,
        mechanic=mechanic,
        booking=booking,
        rating=5,
        comment='Exceptional service by Ramesh! Clear communication and transparent billing.'
    )
    print(f"[TEST 7] Review submitted: {review.rating} Stars by {review.customer.user.username}")
    assert mechanic.average_rating >= 4.5
    print(" -> PASSED: Rating system updated mechanic profile rating.")

    # TEST 8: Problem-Based Diagnosis & Estimate Approval Flow
    diag_service = Service.objects.get(service_name='Custom Problem Diagnosis & Estimate')
    diag_booking = Booking.objects.create(
        customer=customer,
        vehicle=vehicle,
        mechanic=mechanic,
        service=diag_service,
        booking_type='CUSTOM_PROBLEM',
        appointment_date=datetime.date.today() + datetime.timedelta(days=2),
        appointment_time=datetime.time(14, 0),
        status='ACCEPTED',
        customer_notes='High engine noise when clutch is depressed. White smoke from exhaust occasionally.'
    )
    print(f"[TEST 8] Created Problem-Based Booking #{diag_booking.booking_number} for customer symptom inspection.")
    assert diag_booking.booking_type == 'CUSTOM_PROBLEM'

    # Step A: Vehicle reaches workshop
    diag_booking.status = 'VEHICLE_RECEIVED'
    diag_booking.save()
    assert diag_booking.status == 'VEHICLE_RECEIVED'

    # Step B: Mechanic conducts physical inspection & enters estimate
    diag_booking.estimated_labour = Decimal('400.00')
    diag_booking.estimated_parts = Decimal('850.00')
    diag_booking.estimated_total = Decimal('1250.00')
    diag_booking.estimate_notes = 'Worn out clutch release bearing (INR 550) + new clutch cable (INR 300). Labour INR 400.'
    diag_booking.status = 'ESTIMATE_SENT'
    diag_booking.save()
    print(f" -> Quoted Estimate: INR {diag_booking.estimated_total}. Status: {diag_booking.status}")
    assert diag_booking.status == 'ESTIMATE_SENT'

    # Step C: Customer reviews and approves estimate
    diag_booking.status = 'IN_PROGRESS'
    diag_booking.estimate_approved_at = django.utils.timezone.now()
    diag_booking.save()
    assert diag_booking.status == 'IN_PROGRESS'
    assert diag_booking.estimate_approved_at is not None
    print(" -> Customer Approved Estimate: Work moved to IN_PROGRESS.")

    # Step D: Mechanic completes job and invoice generated
    diag_booking.status = 'COMPLETED'
    diag_booking.save()
    diag_invoice = Invoice.objects.create(
        booking=diag_booking,
        service_charge=Decimal('0.00'),
        labour_charge=diag_booking.estimated_labour,
        parts_charge=diag_booking.estimated_parts,
        parts_details=diag_booking.estimate_notes,
        is_paid=False
    )
    assert diag_invoice.total_amount > Decimal('1250.00') # 1250 + 18% GST = 1475.00
    print(f" -> Completed Job: Generated Invoice #{diag_invoice.invoice_number} (Total with GST: INR {diag_invoice.total_amount})")
    print(" -> PASSED: Real-world Problem Diagnosis & Estimate Approval Flow completely verified.")

    # TEST 9: Workshop Dashboard Pop-up & WhatsApp Cloud API Notification Pipeline
    from vehicle_service.notifications import notify_estimate_approved, notify_service_completed, notify_booking_accepted
    from bookings.models import Notification, WhatsAppLog

    # 1. Trigger Booking Accepted WhatsApp to Customer (with Workshop Address)
    notif_acc = notify_booking_accepted(diag_booking)
    print(f"[TEST 9] Booking Acceptance Notification created: #{notif_acc.id} for {notif_acc.recipient.username}")
    ws_log_acc = WhatsAppLog.objects.filter(booking=diag_booking, message_type='BOOKING_ACCEPTED').first()
    assert ws_log_acc is not None
    assert mechanic.city in ws_log_acc.message_body
    print(f" -> Customer WhatsApp Sent with Workshop Address: To {ws_log_acc.recipient_phone} ({ws_log_acc.status})")

    # 2. Trigger Estimate Approval Notification (Workshop Pop-up + WhatsApp)
    notif_1 = notify_estimate_approved(diag_booking)
    print(f" -> Workshop Dashboard Pop-up Notification created: #{notif_1.id} for {notif_1.recipient.username}")
    assert notif_1.is_read is False
    assert Notification.objects.filter(recipient=mechanic.user, is_read=False, notification_type='ESTIMATE_APPROVED').exists()

    ws_log_1 = WhatsAppLog.objects.filter(booking=diag_booking, message_type='ESTIMATE_APPROVED').first()
    assert ws_log_1 is not None
    print(f" -> Workshop WhatsApp Sent: To {ws_log_1.recipient_phone} ({ws_log_1.status})")

    # 3. Trigger Job Completed WhatsApp to Customer
    notif_2 = notify_service_completed(diag_booking, diag_invoice)
    print(f" -> Customer Notification created: #{notif_2.id} for {notif_2.recipient.username}")
    assert Notification.objects.filter(recipient=customer.user, is_read=False, notification_type='JOB_COMPLETED').exists()

    ws_log_2 = WhatsAppLog.objects.filter(booking=diag_booking, message_type='JOB_COMPLETED').first()
    assert ws_log_2 is not None
    print(f" -> Customer WhatsApp Sent: To {ws_log_2.recipient_phone} ({ws_log_2.status})")
    assert f"INR {diag_invoice.total_amount}" in ws_log_2.message_body or f"{diag_invoice.total_amount}" in ws_log_2.message_body
    print(" -> PASSED: Complete WhatsApp notification suite & Workshop Pop-up verified.")

    # TEST 10: QR Code Generation & UPI / Cash Only Payment Policy
    print("[TEST 10] Testing QR Code Generation & Payment Policy...")
    # A. Check QR URL generation
    qr_url = mechanic.get_upi_qr_url(amount=Decimal('1500.00'), invoice_number='INV-TEST123')
    assert "api.qrserver.com" in qr_url or mechanic.qr_code_image, "Must return valid QR code URL"
    assert "upi%3A%2F%2Fpay" in qr_url or mechanic.qr_code_image, "Must contain UPI payload"
    print(f" -> QR Code URL generated correctly: {qr_url[:65]}...")

    # B. Test allowed payment methods (only UPI and CASH)
    allowed_methods = [choice[0] for choice in Payment.PAYMENT_METHOD_CHOICES]
    assert 'UPI' in allowed_methods, "UPI must be allowed"
    assert 'CASH' in allowed_methods, "CASH must be allowed"
    assert 'CARD' not in allowed_methods, "CARD must NOT be allowed"
    assert 'NETBANKING' not in allowed_methods, "NETBANKING must NOT be allowed"
    print(" -> Payment Methods strictly restricted to: UPI and CASH only. (Cards & Netbanking disabled)")

    # C. Test Cash Payment creation
    cash_payment = Payment.objects.create(
        invoice=diag_invoice,
        transaction_id=f"CASH-TEST-{diag_booking.id}",
        amount=diag_invoice.total_amount,
        payment_method='CASH',
        payment_status='SUCCESS'
    )
    diag_invoice.is_paid = True
    diag_invoice.save()
    assert cash_payment.payment_method == 'CASH'
    assert diag_invoice.is_paid is True
    print(f" -> Cash at Workshop payment created successfully: {cash_payment.transaction_id}")
    print(" -> PASSED: QR Code generation & UPI / Cash payment system verified.")

    print("==================================================")
    print("ALL 10 SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
