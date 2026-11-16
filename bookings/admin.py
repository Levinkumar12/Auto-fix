from django.contrib import admin
from .models import Booking, Notification, WhatsAppLog

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'customer', 'vehicle', 'mechanic', 'service', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('booking_number', 'customer__user__username', 'mechanic__user__username', 'vehicle__vehicle_number')
    date_hierarchy = 'appointment_date'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'recipient__username')

@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_phone', 'recipient_name', 'message_type', 'status', 'created_at')
    list_filter = ('status', 'message_type')
    search_fields = ('recipient_phone', 'recipient_name', 'message_body')

