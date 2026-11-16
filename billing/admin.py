from django.contrib import admin
from .models import Invoice, Payment, Review

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'booking', 'service_charge', 'labour_charge', 'parts_charge', 'tax_amount', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('invoice_number', 'booking__booking_number')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'invoice', 'amount', 'payment_method', 'payment_status', 'paid_at')
    list_filter = ('payment_method', 'payment_status')
    search_fields = ('transaction_id', 'invoice__invoice_number')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'customer', 'mechanic', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__user__username', 'mechanic__user__username', 'comment')
