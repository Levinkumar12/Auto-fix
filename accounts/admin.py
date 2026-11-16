from django.contrib import admin
from .models import CustomerProfile, MechanicProfile

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'city')
    list_filter = ('city',)

@admin.register(MechanicProfile)
class MechanicProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'workshop_name', 'specialization', 'experience_years', 'hourly_rate', 'approval_status', 'is_available')
    list_filter = ('approval_status', 'is_available', 'city')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'workshop_name', 'specialization')
    actions = ['approve_mechanics', 'reject_mechanics']

    def approve_mechanics(self, request, queryset):
        queryset.update(approval_status='APPROVED')
    approve_mechanics.short_description = "Approve selected mechanics"

    def reject_mechanics(self, request, queryset):
        queryset.update(approval_status='REJECTED')
    reject_mechanics.short_description = "Reject selected mechanics"
