import uuid
from django.db import models
from django.contrib.auth.models import User
from accounts.models import CustomerProfile, MechanicProfile
from customers.models import Vehicle
from services.models import Service

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending - Waiting for mechanic response'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('VEHICLE_RECEIVED', 'Vehicle Received at Workshop'),
        ('ESTIMATE_SENT', 'Estimate Sent - Waiting Customer Approval'),
        ('IN_PROGRESS', 'In Progress (Approved)'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    BOOKING_TYPE_CHOICES = [
        ('FIXED', 'Fixed Price Package'),
        ('CUSTOM_PROBLEM', 'Custom Problem / Diagnosis & Estimate'),
    ]

    booking_number = models.CharField(max_length=25, unique=True, editable=False)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    mechanic = models.ForeignKey(MechanicProfile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default='FIXED')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    customer_notes = models.TextField(blank=True, help_text="Describe vehicle problems or special instructions")
    rejection_reason = models.TextField(blank=True, help_text="Reason provided if rejected by mechanic")
    mechanic_notes = models.TextField(blank=True, help_text="Work notes from mechanic during diagnosis/service")

    # Estimate fields for problem-based diagnosis
    estimated_labour = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    estimated_parts = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    estimate_notes = models.TextField(blank=True, help_text="Diagnosis findings and estimated parts breakdown")
    estimate_created_at = models.DateTimeField(null=True, blank=True)
    estimate_approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = f"BK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_number} - {self.customer.user.username} with {self.mechanic.user.username} ({self.status})"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('ESTIMATE_APPROVED', 'Estimate Approved by Customer'),
        ('NEW_BOOKING', 'New Booking Request'),
        ('JOB_COMPLETED', 'Service Completed'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='system_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='ESTIMATE_APPROVED')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    action_url = models.CharField(max_length=255, blank=True, help_text="Direct URL to redirect on click")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.recipient.username} ({'Read' if self.is_read else 'Unread'})"


class WhatsAppLog(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent / Accepted by provider'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    ]

    recipient_phone = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=150, blank=True)
    message_type = models.CharField(max_length=50)  # ESTIMATE_APPROVED, JOB_COMPLETED
    message_body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SIMULATED')
    api_response = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=120, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def whatsapp_click_url(self):
        import urllib.parse
        encoded = urllib.parse.quote(self.message_body)
        return f"https://wa.me/{self.recipient_phone}?text={encoded}"

    def __str__(self):
        return f"WhatsApp to {self.recipient_phone} ({self.status}) - {self.message_type}"

