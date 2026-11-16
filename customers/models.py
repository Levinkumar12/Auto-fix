from django.db import models
from accounts.models import CustomerProfile

class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('2_WHEELER', 'Two-Wheeler (Bike / Scooter)'),
        ('4_WHEELER', 'Four-Wheeler (Car / SUV)'),
    ]

    FUEL_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('EV', 'Electric'),
        ('CNG', 'CNG'),
    ]

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='2_WHEELER')
    vehicle_name = models.CharField(max_length=100, help_text="e.g. Honda Activa 6G, Royal Enfield Classic 350, Maruti Swift")
    vehicle_number = models.CharField(max_length=20, help_text="e.g. TN 23 AB 1234")
    model_year = models.PositiveIntegerField(default=2022)
    color = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='PETROL')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_name} ({self.vehicle_number})"
