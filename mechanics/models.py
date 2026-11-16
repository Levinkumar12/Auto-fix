from django.db import models
from accounts.models import MechanicProfile
from services.models import Service

class MechanicService(models.Model):
    mechanic = models.ForeignKey(MechanicProfile, on_delete=models.CASCADE, related_name='offered_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='mechanic_services')
    custom_price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Mechanic's price for this service in INR")
    estimated_time = models.CharField(max_length=50, default='1-2 hours', help_text="e.g., 45 mins, 2 hours")
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('mechanic', 'service')

    def __str__(self):
        return f"{self.mechanic.user.username} - {self.service.service_name} (₹{self.custom_price})"
