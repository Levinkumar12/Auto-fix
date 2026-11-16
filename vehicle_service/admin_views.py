from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count

from accounts.models import CustomerProfile, MechanicProfile
from services.models import Service
from bookings.models import Booking
from billing.models import Invoice, Payment

def staff_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(staff_check, login_url='login')
def admin_portal_dashboard(request):
    total_customers = CustomerProfile.objects.count()
    total_mechanics = MechanicProfile.objects.count()
    pending_mechanics_count = MechanicProfile.objects.filter(approval_status='PENDING').count()
    approved_mechanics_count = MechanicProfile.objects.filter(approval_status='APPROVED').count()

    total_bookings = Booking.objects.count()
    completed_bookings = Booking.objects.filter(status='COMPLETED').count()

    revenue_data = Payment.objects.filter(payment_status='SUCCESS').aggregate(total=Sum('amount'))
    total_revenue = revenue_data['total'] or Decimal('0.00')

    # Pending mechanics list for quick approval
    pending_mechanics = MechanicProfile.objects.filter(approval_status='PENDING').order_by('-created_at')

    # Recent bookings
    recent_bookings = Booking.objects.select_related('customer__user', 'mechanic__user', 'service', 'vehicle').order_by('-created_at')[:8]

    context = {
        'total_customers': total_customers,
        'total_mechanics': total_mechanics,
        'pending_mechanics_count': pending_mechanics_count,
        'approved_mechanics_count': approved_mechanics_count,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'total_revenue': total_revenue,
        'pending_mechanics': pending_mechanics,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin_portal/dashboard.html', context)


@user_passes_test(staff_check, login_url='login')
def admin_approve_mechanic(request, mechanic_id, action):
    mechanic = get_object_or_404(MechanicProfile, id=mechanic_id)
    if action == 'approve':
        mechanic.approval_status = 'APPROVED'
        mechanic.save()
        messages.success(request, f"Mechanic '{mechanic.user.get_full_name() or mechanic.user.username}' has been APPROVED and will now appear in customer search!")
    elif action == 'reject':
        mechanic.approval_status = 'REJECTED'
        mechanic.save()
        messages.warning(request, f"Mechanic '{mechanic.user.get_full_name() or mechanic.user.username}' has been REJECTED.")
    return redirect('admin_portal_dashboard')


@user_passes_test(staff_check, login_url='login')
def admin_all_mechanics(request):
    status_filter = request.GET.get('status', '')
    mechanics = MechanicProfile.objects.select_related('user').order_by('-created_at')
    if status_filter:
        mechanics = mechanics.filter(approval_status=status_filter)

    return render(request, 'admin_portal/mechanics_list.html', {
        'mechanics': mechanics,
        'status_filter': status_filter,
    })


@user_passes_test(staff_check, login_url='login')
def admin_all_bookings(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.select_related('customer__user', 'mechanic__user', 'service', 'vehicle').order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'admin_portal/bookings_list.html', {
        'bookings': bookings,
        'status_filter': status_filter,
    })


@user_passes_test(staff_check, login_url='login')
def admin_all_payments(request):
    payments = Payment.objects.select_related('invoice__booking__customer__user', 'invoice__booking__mechanic__user').order_by('-paid_at')
    total_revenue = payments.filter(payment_status='SUCCESS').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return render(request, 'admin_portal/payments_list.html', {
        'payments': payments,
        'total_revenue': total_revenue,
    })


@user_passes_test(staff_check, login_url='login')
def admin_manage_services(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        name = request.POST.get('service_name')
        desc = request.POST.get('description')
        veh_type = request.POST.get('vehicle_type')
        price = request.POST.get('base_price')
        hours = request.POST.get('estimated_hours')
        icon = request.POST.get('icon', 'bi-tools')

        if service_id:
            service = get_object_or_404(Service, id=service_id)
            service.service_name = name
            service.description = desc
            service.vehicle_type = veh_type
            service.base_price = price
            service.estimated_hours = hours
            service.icon = icon
            service.save()
            messages.success(request, f"Service '{name}' updated successfully!")
        else:
            Service.objects.create(
                service_name=name,
                description=desc,
                vehicle_type=veh_type,
                base_price=price,
                estimated_hours=hours,
                icon=icon
            )
            messages.success(request, f"New service '{name}' created successfully!")
        return redirect('admin_manage_services')

    services = Service.objects.all().order_by('service_name')
    return render(request, 'admin_portal/manage_services.html', {'services': services})

