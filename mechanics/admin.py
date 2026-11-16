from django.contrib import admin
from .models import MechanicService

@admin.register(MechanicService)
class MechanicServiceAdmin(admin.ModelAdmin):
    list_display = ('mechanic', 'service', 'custom_price', 'estimated_time', 'is_available')
    list_filter = ('is_available', 'service')
    search_fields = ('mechanic__user__username', 'service__service_name')
