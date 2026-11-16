from django.urls import path
from . import views

urlpatterns = [
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/mechanic/', views.register_mechanic, name='register_mechanic'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
]

