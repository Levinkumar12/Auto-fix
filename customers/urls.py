from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('profile/', views.customer_profile, name='customer_profile'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_add, name='vehicle_add'),
    path('vehicles/<int:vehicle_id>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:vehicle_id>/delete/', views.vehicle_delete, name='vehicle_delete'),
    
    path('mechanics/', views.browse_mechanics, name='browse_mechanics'),
    path('mechanics/<int:mechanic_id>/', views.mechanic_detail, name='mechanic_detail'),
    path('book/', views.book_service, name='book_service'),
    path('book/<int:mechanic_id>/', views.book_service, name='book_service_with_mechanic'),
    
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/approve-estimate/', views.approve_estimate, name='approve_estimate'),
    path('bookings/<int:booking_id>/reject-estimate/', views.reject_estimate, name='reject_estimate'),
]

