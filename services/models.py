from django.db import models

class Service(models.Model):
    VEHICLE_COMPATIBILITY_CHOICES = [
        ('2_WHEELER', 'Two-Wheeler'),
        ('4_WHEELER', 'Four-Wheeler'),
        ('ALL', 'All Vehicles'),
    ]

    PRICE_TYPE_CHOICES = [
        ('FIXED', 'Fixed Package Price'),
        ('ESTIMATE', 'Estimate After Inspection'),
    ]

    service_name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default='FIXED', help_text="Fixed standard price or estimate after problem inspection")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_COMPATIBILITY_CHOICES, default='ALL')
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=500.00, help_text="Base standard service price in INR (0 for estimate based)")
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.5, help_text="Estimated turnaround hours")
    icon = models.CharField(max_length=50, default='bi-tools', help_text="Bootstrap icon class name, e.g. bi-droplet for oil change")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.price_type == 'ESTIMATE':
            return f"{self.service_name} (Estimate after Inspection)"
        return f"{self.service_name} (₹{self.base_price})"
