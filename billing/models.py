import uuid
from decimal import Decimal
from django.db import models
from accounts.models import CustomerProfile, MechanicProfile
from bookings.models import Booking

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=25, unique=True, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    parts_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    parts_details = models.TextField(blank=True, help_text="e.g. Engine Oil (₹450), Brake Pad (₹350)")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        subtotal = (self.service_charge or Decimal('0.00')) + (self.labour_charge or Decimal('0.00')) + (self.parts_charge or Decimal('0.00'))
        # 18% GST calculation
        self.tax_amount = round(subtotal * Decimal('0.18'), 2)
        self.total_amount = subtotal + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} for {self.booking.booking_number} (₹{self.total_amount})"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI / QR Code Scan'),
        ('CASH', 'Cash at Workshop'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('SUCCESS', 'Successful'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='UPI')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='SUCCESS')
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - ₹{self.amount} ({self.payment_status})"


class Review(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='reviews_given')
    mechanic = models.ForeignKey(MechanicProfile, on_delete=models.CASCADE, related_name='reviews_received')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer.user.username} for {self.mechanic.user.username} - {self.rating}★"
