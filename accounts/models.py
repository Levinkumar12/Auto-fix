import urllib.parse
from django.db import models
from django.contrib.auth.models import User

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customer: {self.user.get_full_name() or self.user.username} ({self.phone})"


class MechanicProfile(models.Model):
    APPROVAL_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mechanic_profile')
    phone = models.CharField(max_length=15)
    experience_years = models.PositiveIntegerField(default=1, help_text="Years of professional mechanical experience")
    specialization = models.CharField(max_length=200, help_text="e.g., Two-Wheeler Engine Specialist, Car Diagnostics, Brake & Clutch")
    workshop_name = models.CharField(max_length=150, blank=True, help_text="Garage / Workshop Name")
    address = models.TextField()
    city = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=300.00, help_text="Base labour rate in INR")
    is_available = models.BooleanField(default=True, help_text="Toggle mechanic availability for new bookings")
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='PENDING')
    bio = models.TextField(blank=True, help_text="Short bio and certifications")
    upi_id = models.CharField(max_length=100, blank=True, default='', help_text="Workshop UPI ID (e.g. garage@okhdfcbank, 9840123456@paytm)")
    qr_code_image = models.ImageField(upload_to='workshop_qr/', blank=True, null=True, help_text="Workshop QR Code scanner image")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mechanic: {self.user.get_full_name() or self.user.username} - {self.specialization} [{self.approval_status}]"

    def get_upi_qr_url(self, amount=None, invoice_number=''):
        """
        Returns URL of workshop QR code:
        If mechanic uploaded physical QR image -> returns that image URL.
        Else -> generates dynamic UPI QR Code with pre-filled amount and invoice ref!
        """
        if self.qr_code_image:
            return self.qr_code_image.url
        
        upi = self.upi_id or f"{self.phone}@upi"
        name = self.workshop_name or self.user.get_full_name() or self.user.username
        amt_str = f"{amount:.2f}" if amount else ""
        
        # Build standard UPI Intent payload
        upi_payload = f"upi://pay?pa={upi}&pn={urllib.parse.quote(name)}"
        if amt_str:
            upi_payload += f"&am={amt_str}&cu=INR"
        if invoice_number:
            upi_payload += f"&tn=Invoice%20{invoice_number}"
        
        encoded_payload = urllib.parse.quote(upi_payload, safe='')
        return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded_payload}"

    @property
    def average_rating(self):
        from billing.models import Review
        reviews = Review.objects.filter(mechanic=self)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            return round(total / reviews.count(), 1)
        return 0.0

    @property
    def total_reviews_count(self):
        from billing.models import Review
        return Review.objects.filter(mechanic=self).count()

    @property
    def completed_services_count(self):
        from bookings.models import Booking
        return Booking.objects.filter(mechanic=self, status='COMPLETED').count()
