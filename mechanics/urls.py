from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.mechanic_dashboard, name='mechanic_dashboard'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('requests/', views.booking_requests, name='booking_requests'),
    path('requests/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('requests/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
    
    path('jobs/active/', views.active_jobs, name='active_jobs'),
    path('jobs/<int:booking_id>/status/', views.update_job_status, name='update_job_status'),
    path('jobs/<int:booking_id>/estimate/', views.provide_estimate, name='provide_estimate'),
    path('jobs/<int:booking_id>/complete/', views.complete_job, name='complete_job'),
    
    path('services/', views.mechanic_services, name='mechanic_services'),
    path('qr-settings/', views.workshop_qr_settings, name='workshop_qr_settings'),
    path('earnings/', views.mechanic_earnings, name='mechanic_earnings'),
    path('earnings/<int:invoice_id>/confirm-cash/', views.confirm_cash_received, name='confirm_cash_received'),
    path('whatsapp/logs/', views.whatsapp_logs, name='mechanic_whatsapp_logs'),
    path('api/notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]

