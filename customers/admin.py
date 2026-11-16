from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_name', 'vehicle_number', 'vehicle_type', 'fuel_type', 'customer', 'model_year')
    list_filter = ('vehicle_type', 'fuel_type')
    search_fields = ('vehicle_name', 'vehicle_number', 'customer__user__username')
