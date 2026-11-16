from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomerRegisterForm, MechanicRegisterForm
from .models import CustomerProfile, MechanicProfile

def register_customer(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            CustomerProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city']
            )
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CustomerRegisterForm()

    return render(request, 'accounts/register_customer.html', {'form': form})


def register_mechanic(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = MechanicRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            MechanicProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                workshop_name=form.cleaned_data.get('workshop_name', ''),
                experience_years=form.cleaned_data['experience_years'],
                specialization=form.cleaned_data['specialization'],
                hourly_rate=form.cleaned_data['hourly_rate'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                bio=form.cleaned_data.get('bio', ''),
                upi_id=form.cleaned_data.get('upi_id', ''),
                qr_code_image=form.cleaned_data.get('qr_code_image'),
                approval_status='PENDING'
            )
            messages.success(request, "Registration submitted successfully! Your account will be active once approved by our administrator.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MechanicRegisterForm()

    return render(request, 'accounts/register_mechanic.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('admin_portal_dashboard')
    elif hasattr(user, 'mechanic_profile'):
        return redirect('mechanic_dashboard')
    elif hasattr(user, 'customer_profile'):
        return redirect('customer_dashboard')
    else:
        messages.warning(request, "No specific profile associated with this account.")
        return redirect('home')
