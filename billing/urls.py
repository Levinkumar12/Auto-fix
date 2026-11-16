from django.urls import path
from . import views

urlpatterns = [
    path('invoice/<int:booking_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/pay/', views.pay_invoice, name='pay_invoice'),
    path('review/<int:booking_id>/', views.submit_review, name='submit_review'),
]

