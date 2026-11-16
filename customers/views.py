import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.utils import timezone

from accounts.models import MechanicProfile
from services.models import Service
from mechanics.models import MechanicService
from bookings.models import Booking, WhatsAppLog
from billing.models import Invoice, Review
from vehicle_service.notifications import notify_estimate_approved
from .models import Vehicle
from .forms import CustomerProfileForm, VehicleForm

def customer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'customer_profile'):
            messages.error(request, "Access restricted to Customer accounts.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


@customer_required
def customer_dashboard(request):
    customer = request.user.customer_profile
    vehicles = Vehicle.objects.filter(customer=customer)
    bookings = Booking.objects.filter(customer=customer).order_by('-created_at')
    
    total_vehicles = vehicles.count()
    active_bookings = bookings.filter(status__in=['PENDING', 'ACCEPTED', 'VEHICLE_RECEIVED', 'ESTIMATE_SENT', 'IN_PROGRESS']).count()
    pending_estimates = bookings.filter(status='ESTIMATE_SENT').count()
    completed_services = bookings.filter(status='COMPLETED').count()
    pending_bills = Invoice.objects.filter(booking__customer=customer, is_paid=False, booking__status='COMPLETED').count()

    recent_bookings = bookings[:5]

    context = {
        'customer': customer,
        'vehicles': vehicles,
        'recent_bookings': recent_bookings,
        'total_vehicles': total_vehicles,
        'active_bookings': active_bookings,
        'pending_estimates': pending_estimates,
        'completed_services': completed_services,
        'pending_bills': pending_bills,
    }
    return render(request, 'customer/dashboard.html', context)


@customer_required
def customer_profile(request):
    profile = request.user.customer_profile
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('customer_profile')
    else:
        form = CustomerProfileForm(instance=profile, user=request.user)
    return render(request, 'customer/profile.html', {'form': form, 'customer': profile})


@customer_required
def vehicle_list(request):
    customer = request.user.customer_profile
    vehicles = Vehicle.objects.filter(customer=customer)
    return render(request, 'customer/vehicle_list.html', {'vehicles': vehicles})


@customer_required
def vehicle_add(request):
    customer = request.user.customer_profile
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            vehicle.save()
            messages.success(request, f"Vehicle '{vehicle.vehicle_name}' registered successfully!")
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'customer/vehicle_form.html', {'form': form, 'title': 'Add New Vehicle'})


@customer_required
def vehicle_edit(request, vehicle_id):
    customer = request.user.customer_profile
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer=customer)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle details updated successfully!")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'customer/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle'})


@customer_required
def vehicle_delete(request, vehicle_id):
    customer = request.user.customer_profile
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer=customer)
    if request.method == 'POST':
        name = vehicle.vehicle_name
        vehicle.delete()
        messages.success(request, f"Vehicle '{name}' removed.")
        return redirect('vehicle_list')
    return render(request, 'customer/vehicle_confirm_delete.html', {'vehicle': vehicle})


def browse_mechanics(request):
    """
    Search and filter approved mechanics.
    Customers can independently select their preferred mechanics based on:
    - Specialization
    - Experience
    - City
    - Rating
    - Availability
    """
    query = request.GET.get('q', '').strip()
    specialization = request.GET.get('specialization', '').strip()
    city = request.GET.get('city', '').strip()
    availability = request.GET.get('availability', '')

    mechanics = MechanicProfile.objects.filter(approval_status='APPROVED')

    if query:
        mechanics = mechanics.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(workshop_name__icontains=query) |
            Q(specialization__icontains=query)
        )
    if specialization:
        mechanics = mechanics.filter(specialization__icontains=specialization)
    if city:
        mechanics = mechanics.filter(city__icontains=city)
    if availability == '1':
        mechanics = mechanics.filter(is_available=True)

    # Distinct cities and specializations for filter dropdowns
    available_cities = MechanicProfile.objects.filter(approval_status='APPROVED').values_list('city', flat=True).distinct()

    context = {
        'mechanics': mechanics,
        'query': query,
        'specialization': specialization,
        'city': city,
        'availability': availability,
        'available_cities': available_cities,
    }
    return render(request, 'customer/browse_mechanics.html', context)


def mechanic_detail(request, mechanic_id):
    mechanic = get_object_or_404(MechanicProfile, id=mechanic_id, approval_status='APPROVED')
    services_offered = MechanicService.objects.filter(mechanic=mechanic, is_available=True)
    reviews = Review.objects.filter(mechanic=mechanic).order_by('-created_at')

    context = {
        'mechanic': mechanic,
        'services_offered': services_offered,
        'reviews': reviews,
    }
    return render(request, 'customer/mechanic_detail.html', context)


@customer_required
def book_service(request, mechanic_id=None):
    customer = request.user.customer_profile
    vehicles = Vehicle.objects.filter(customer=customer)

    if not vehicles.exists():
        messages.warning(request, "Please add at least one vehicle before booking a service.")
        return redirect('vehicle_add')

    selected_mechanic = None
    if mechanic_id:
        selected_mechanic = get_object_or_404(MechanicProfile, id=mechanic_id, approval_status='APPROVED')

    approved_mechanics = MechanicProfile.objects.filter(approval_status='APPROVED', is_available=True)
    services = Service.objects.filter(is_active=True)

    if request.method == 'POST':
        mechanic_post_id = request.POST.get('mechanic')
        vehicle_id = request.POST.get('vehicle')
        service_id = request.POST.get('service')
        appointment_date_str = request.POST.get('appointment_date')
        appointment_time_str = request.POST.get('appointment_time')
        notes = request.POST.get('customer_notes', '').strip()

        # Validation
        try:
            target_mechanic = MechanicProfile.objects.get(id=mechanic_post_id, approval_status='APPROVED')
        except MechanicProfile.DoesNotExist:
            messages.error(request, "Selected mechanic is not valid or no longer approved.")
            return redirect('browse_mechanics')

        # Double check mechanic availability
        if not target_mechanic.is_available:
            messages.error(request, f"Mechanic {target_mechanic.user.get_full_name() or target_mechanic.user.username} is currently unavailable. Please choose another mechanic.")
            return render(request, 'customer/book_service.html', {
                'vehicles': vehicles,
                'mechanics': approved_mechanics,
                'selected_mechanic': selected_mechanic,
                'services': services,
            })

        vehicle = get_object_or_404(Vehicle, id=vehicle_id, customer=customer)
        service = get_object_or_404(Service, id=service_id, is_active=True)

        try:
            appt_date = datetime.date.fromisoformat(appointment_date_str)
            if appt_date < datetime.date.today():
                messages.error(request, "Appointment date cannot be in the past.")
                return render(request, 'customer/book_service.html', {
                    'vehicles': vehicles,
                    'mechanics': approved_mechanics,
                    'selected_mechanic': target_mechanic,
                    'services': services,
                })
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('book_service')

        # Check for slot collision with the same mechanic
        existing = Booking.objects.filter(
            mechanic=target_mechanic,
            appointment_date=appt_date,
            appointment_time=appointment_time_str,
            status__in=['PENDING', 'ACCEPTED', 'IN_PROGRESS']
        ).exists()

        if existing:
            messages.warning(request, f"Mechanic already has an active appointment at {appointment_time_str} on {appt_date}. Please choose another time slot.")
            return render(request, 'customer/book_service.html', {
                'vehicles': vehicles,
                'mechanics': approved_mechanics,
                'selected_mechanic': target_mechanic,
                'services': services,
            })

        b_type = 'CUSTOM_PROBLEM' if service.price_type == 'ESTIMATE' else 'FIXED'

        booking = Booking.objects.create(
            customer=customer,
            vehicle=vehicle,
            mechanic=target_mechanic,
            service=service,
            booking_type=b_type,
            appointment_date=appt_date,
            appointment_time=appointment_time_str,
            customer_notes=notes,
            status='PENDING'
        )

        messages.success(request, f"Booking request #{booking.booking_number} sent to mechanic {target_mechanic.user.get_full_name() or target_mechanic.user.username}! Waiting for their acceptance.")
        return redirect('my_bookings')

    context = {
        'vehicles': vehicles,
        'mechanics': approved_mechanics,
        'selected_mechanic': selected_mechanic,
        'services': services,
        'today': datetime.date.today().isoformat(),
    }
    return render(request, 'customer/book_service.html', context)


@customer_required
def my_bookings(request):
    customer = request.user.customer_profile
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(customer=customer)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'customer/my_bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter,
    })


@customer_required
def booking_detail(request, booking_id):
    customer = request.user.customer_profile
    booking = get_object_or_404(Booking, id=booking_id, customer=customer)
    has_reviewed = hasattr(booking, 'review')
    has_invoice = hasattr(booking, 'invoice')
    whatsapp_logs = WhatsAppLog.objects.filter(booking=booking).order_by('-created_at')

    return render(request, 'customer/booking_detail.html', {
        'booking': booking,
        'has_reviewed': has_reviewed,
        'has_invoice': has_invoice,
        'whatsapp_logs': whatsapp_logs,
    })


@customer_required
def cancel_booking(request, booking_id):
    customer = request.user.customer_profile
    booking = get_object_or_404(Booking, id=booking_id, customer=customer)

    if booking.status != 'PENDING':
        messages.error(request, "Only bookings in 'PENDING' status can be cancelled.")
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save()
        messages.success(request, f"Booking #{booking.booking_number} has been cancelled.")
        return redirect('my_bookings')

    return render(request, 'customer/booking_confirm_cancel.html', {'booking': booking})


@customer_required
def approve_estimate(request, booking_id):
    customer = request.user.customer_profile
    booking = get_object_or_404(Booking, id=booking_id, customer=customer)

    if booking.status != 'ESTIMATE_SENT':
        messages.warning(request, "No pending estimate awaiting your approval.")
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        booking.status = 'IN_PROGRESS'
        booking.estimate_approved_at = timezone.now()
        booking.save()

        # Trigger Workshop Dashboard Pop-up + WhatsApp Message
        try:
            notify_estimate_approved(booking)
        except Exception as e:
            pass

        messages.success(request, f"Estimate of ₹{booking.estimated_total} approved! Mechanic notified via Dashboard Pop-up & WhatsApp to proceed with repair work.")
        return redirect('booking_detail', booking_id=booking.id)

    return render(request, 'customer/estimate_action.html', {'booking': booking, 'action': 'approve'})


@customer_required
def reject_estimate(request, booking_id):
    customer = request.user.customer_profile
    booking = get_object_or_404(Booking, id=booking_id, customer=customer)

    if booking.status != 'ESTIMATE_SENT':
        messages.warning(request, "No pending estimate to decline.")
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Cost estimate declined by customer.').strip()
        booking.status = 'CANCELLED'
        booking.rejection_reason = reason or "Cost estimate declined by customer."
        booking.save()
        messages.info(request, f"Booking #{booking.booking_number} cancelled because estimate was declined.")
        return redirect('my_bookings')

    return render(request, 'customer/estimate_action.html', {'booking': booking, 'action': 'reject'})

