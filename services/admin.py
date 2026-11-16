from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'vehicle_type', 'base_price', 'estimated_hours', 'is_active')
    list_filter = ('vehicle_type', 'is_active')
    search_fields = ('service_name', 'description')
