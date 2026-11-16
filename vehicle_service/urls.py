from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, admin_views

urlpatterns = [
    path('webhooks/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('django-admin/', admin.site.urls),
    
    # Home & Global
    path('', views.home, name='home'),
    
    # Accounts & Authentication
    path('accounts/', include('accounts.urls')),
    
    # Customer Module
    path('customer/', include('customers.urls')),
    
    # Mechanic Module
    path('mechanic/', include('mechanics.urls')),
    
    # Services
    path('services/', include('services.urls')),
    
    # Billing & Invoices
    path('billing/', include('billing.urls')),
    
    # Custom Admin Portal
    path('admin-portal/', admin_views.admin_portal_dashboard, name='admin_portal_dashboard'),
    path('admin-portal/mechanics/', admin_views.admin_all_mechanics, name='admin_all_mechanics'),
    path('admin-portal/mechanics/<int:mechanic_id>/<str:action>/', admin_views.admin_approve_mechanic, name='admin_approve_mechanic'),
    path('admin-portal/services/', admin_views.admin_manage_services, name='admin_manage_services'),
    path('admin-portal/bookings/', admin_views.admin_all_bookings, name='admin_all_bookings'),
    path('admin-portal/payments/', admin_views.admin_all_payments, name='admin_all_payments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
