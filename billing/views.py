import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking
from .models import Invoice, Payment, Review
from .forms import PaymentForm, ReviewForm

@login_required
def invoice_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

    # Security check: User must be customer, mechanic, or staff
    is_owner = hasattr(user, 'customer_profile') and booking.customer == user.customer_profile
    is_mechanic = hasattr(user, 'mechanic_profile') and booking.mechanic == user.mechanic_profile
    is_admin = user.is_staff or user.is_superuser

    if not (is_owner or is_mechanic or is_admin):
        messages.error(request, "You are not authorized to view this invoice.")
        return redirect('dashboard_redirect')

    invoice = get_object_or_404(Invoice, booking=booking)

    context = {
        'invoice': invoice,
        'booking': booking,
        'is_owner': is_owner,
        'is_mechanic': is_mechanic,
        'is_admin': is_admin,
    }
    return render(request, 'billing/invoice_detail.html', context)


@login_required
def pay_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    user = request.user

    # Ensure user is the customer
    if not (hasattr(user, 'customer_profile') and invoice.booking.customer == user.customer_profile):
        messages.error(request, "Only the customer who booked this service can pay this invoice.")
        return redirect('dashboard_redirect')

    if invoice.is_paid:
        messages.info(request, "This invoice is already paid.")
        return redirect('invoice_detail', booking_id=invoice.booking.id)

    pending_cash = invoice.payments.filter(payment_method='CASH', payment_status='PENDING').first()
    if pending_cash:
        messages.info(request, "Cash payment is awaiting confirmation from your mechanic after collection.")
        return redirect('invoice_detail', booking_id=invoice.booking.id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            txn_ref = form.cleaned_data.get('transaction_reference', '').strip()

            if txn_ref:
                txn_id = f"UPI-{txn_ref}"
            else:
                prefix = 'UPI' if payment_method == 'UPI' else 'CASH'
                txn_id = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

            payment = Payment.objects.create(
                invoice=invoice,
                transaction_id=txn_id,
                amount=invoice.total_amount,
                payment_method=payment_method,
                payment_status='PENDING' if payment_method == 'CASH' else 'SUCCESS'
            )

            if payment_method != 'CASH':
                invoice.is_paid = True
                invoice.save(update_fields=['is_paid', 'updated_at'])

            method_name = "UPI / QR Code Scan" if payment_method == 'UPI' else "Cash at Workshop"
            if payment_method == 'CASH':
                messages.info(request, f"Cash payment of ₹{invoice.total_amount} recorded as awaiting collection. The mechanic will confirm after receiving it. Reference: {txn_id}")
            else:
                messages.success(request, f"Payment of ₹{invoice.total_amount} processed successfully via {method_name}! Txn ID: {txn_id}")
            return redirect('invoice_detail', booking_id=invoice.booking.id)
    else:
        form = PaymentForm(initial={'payment_method': 'UPI'})

    mechanic = invoice.booking.mechanic
    qr_url = mechanic.get_upi_qr_url(invoice.total_amount, invoice.invoice_number) if mechanic else None

    return render(request, 'billing/payment_form.html', {
        'invoice': invoice,
        'form': form,
        'mechanic': mechanic,
        'qr_url': qr_url,
    })


@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

    # Only completed bookings can be reviewed by the customer who booked them
    if not (hasattr(user, 'customer_profile') and booking.customer == user.customer_profile):
        messages.error(request, "Only the customer for this booking can submit a review.")
        return redirect('dashboard_redirect')

    if booking.status != 'COMPLETED':
        messages.error(request, "Reviews can only be submitted for completed services.")
        return redirect('booking_detail', booking_id=booking.id)

    # Check if review already exists
    review = Review.objects.filter(booking=booking).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            rev = form.save(commit=False)
            rev.booking = booking
            rev.customer = booking.customer
            rev.mechanic = booking.mechanic
            rev.save()
            messages.success(request, "Thank you! Your review and rating have been posted.")
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'billing/review_form.html', {
        'booking': booking,
        'form': form,
        'review': review,
    })
