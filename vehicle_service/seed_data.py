import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
import datetime
from decimal import Decimal

DEMO_PASSWORD = os.environ.get('SEED_DEMO_PASSWORD')
if not DEMO_PASSWORD:
    raise RuntimeError('Set SEED_DEMO_PASSWORD before running this demo seed script.')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_service.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import CustomerProfile, MechanicProfile
from customers.models import Vehicle
from services.models import Service
from mechanics.models import MechanicService
from bookings.models import Booking
from billing.models import Invoice, Payment, Review

def seed():
    print("Seeding initial data into MySQL database...")

    # 1. Admin Superuser
    admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@vsms.com', 'first_name': 'Admin', 'last_name': 'User', 'is_staff': True, 'is_superuser': True})
    if created:
        admin_user.set_password(DEMO_PASSWORD)
        admin_user.save()
        print("Demo superuser seeded. Password is supplied via SEED_DEMO_PASSWORD.")

    # 2. Standard Services Catalog
    services_data = [
        {
            'name': 'Engine Oil & Filter Replacement',
            'desc': 'Complete drain of old lubricant, new OEM grade semi/fully synthetic engine oil, oil filter replacement, and fluid checks.',
            'vtype': 'ALL',
            'price': Decimal('450.00'),
            'hours': Decimal('1.0'),
            'icon': 'bi-droplet-half'
        },
        {
            'name': 'Comprehensive Periodic General Service',
            'desc': 'Multi-point inspection including spark plug check, throttle body cleaning, air filter replacement, chain lubrication, brake adjustment, and vehicle washing.',
            'vtype': '2_WHEELER',
            'price': Decimal('850.00'),
            'hours': Decimal('2.5'),
            'icon': 'bi-wrench-adjustable'
        },
        {
            'name': 'Brake Disc & Pad Overhaul',
            'desc': 'Front and rear brake pad replacement, rotor caliper inspection, brake fluid bleed and top-up.',
            'vtype': 'ALL',
            'price': Decimal('600.00'),
            'hours': Decimal('1.5'),
            'icon': 'bi-disc'
        },
        {
            'name': 'Car Major Periodic Maintenance',
            'desc': 'Engine diagnostics, coolant flush, AC cabin filter replacement, suspension check, spark plugs, full chassis inspection.',
            'vtype': '4_WHEELER',
            'price': Decimal('2400.00'),
            'hours': Decimal('3.5'),
            'icon': 'bi-car-front'
        },
        {
            'name': 'Battery & Electrical Diagnostics',
            'desc': 'Computerized OBD-II diagnostic scanning, alternator charging test, starter motor check, battery health report.',
            'vtype': 'ALL',
            'price': Decimal('400.00'),
            'hours': Decimal('1.0'),
            'icon': 'bi-battery-charging'
        },
        {
            'name': 'Clutch Plate & Transmission Repair',
            'desc': 'Clutch cable and plate replacement, pressure plate inspection, flywheel check, smooth gear engagement tuning.',
            'vtype': 'ALL',
            'price': Decimal('1200.00'),
            'hours': Decimal('3.0'),
            'icon': 'bi-gear-wide-connected'
        },
        {
            'name': 'Custom Problem & Diagnosis',
            'desc': 'Mechanic inspects the reported issue and submits an estimate before repair work begins.',
            'vtype': 'ALL',
            'price': Decimal('0.00'),
            'hours': Decimal('1.5'),
            'icon': 'bi-search',
            'price_type': 'ESTIMATE'
        }
    ]

    services = {}
    for s in services_data:
        obj, _ = Service.objects.get_or_create(
            service_name=s['name'],
            defaults={
                'description': s['desc'],
                'price_type': s.get('price_type', 'FIXED'),
                'vehicle_type': s['vtype'],
                'base_price': s['price'],
                'estimated_hours': s['hours'],
                'icon': s['icon'],
                'is_active': True
            }
        )
        services[s['name']] = obj

    print(f"Verified {len(services)} standard services in catalog.")

    # 3. Mechanics
    # Mechanic 1: Ramesh Kumar (Approved, 2-Wheeler expert)
    m1_user, _ = User.objects.get_or_create(username='ramesh_mech', defaults={'email': 'ramesh@workshop.com', 'first_name': 'Ramesh', 'last_name': 'Kumar'})
    m1_user.set_password(DEMO_PASSWORD)
    m1_user.save()
    m1_profile, _ = MechanicProfile.objects.get_or_create(
        user=m1_user,
        defaults={
            'phone': '9840123456',
            'workshop_name': 'Ramesh Two-Wheeler Care',
            'experience_years': 9,
            'specialization': 'Two-Wheeler Engine & Fuel Injection Tuning',
            'hourly_rate': Decimal('350.00'),
            'address': 'No. 14, Anna Nagar Main Road',
            'city': 'Chennai',
            'bio': 'Specialized factory-trained technician with 9+ years experience in Honda, Royal Enfield, Yamaha, and TVS vehicles. Fast turnaround and guaranteed genuine spare parts.',
            'approval_status': 'APPROVED',
            'is_available': True
        }
    )

    # Mechanic 2: Suresh Auto Works (Approved, Car expert)
    m2_user, _ = User.objects.get_or_create(username='suresh_mech', defaults={'email': 'suresh@workshop.com', 'first_name': 'Suresh', 'last_name': 'Prabhu'})
    m2_user.set_password(DEMO_PASSWORD)
    m2_user.save()
    m2_profile, _ = MechanicProfile.objects.get_or_create(
        user=m2_user,
        defaults={
            'phone': '9840987654',
            'workshop_name': 'Suresh Auto Tech Garage',
            'experience_years': 12,
            'specialization': 'Four-Wheeler Diagnostics & Engine Overhauling',
            'hourly_rate': Decimal('500.00'),
            'address': 'Plot 45, Industrial Estate, Guindy',
            'city': 'Chennai',
            'bio': 'Bosch certified master technician. Equipped with advanced scanning tools, hydraulic lifts, and automated AC gas recharge units. Trusted by over 500+ car owners.',
            'approval_status': 'APPROVED',
            'is_available': True
        }
    )

    # Mechanic 3: Vignesh (Pending Approval - for demonstrating admin approval queue!)
    m3_user, _ = User.objects.get_or_create(username='vignesh_mech', defaults={'email': 'vignesh@workshop.com', 'first_name': 'Vignesh', 'last_name': 'Rajan'})
    m3_user.set_password(DEMO_PASSWORD)
    m3_user.save()
    m3_profile, _ = MechanicProfile.objects.get_or_create(
        user=m3_user,
        defaults={
            'phone': '9789123456',
            'workshop_name': 'SpeedWheel Motors',
            'experience_years': 4,
            'specialization': 'Brake Systems & Suspension Tuning',
            'hourly_rate': Decimal('300.00'),
            'address': '88, GST Road, Tambaram',
            'city': 'Chennai',
            'bio': 'Passionate young technician specializing in precision brake upgrades and monoshock rebuilds.',
            'approval_status': 'PENDING',
            'is_available': True
        }
    )

    # Custom rates for mechanics
    MechanicService.objects.get_or_create(
        mechanic=m1_profile,
        service=services['Engine Oil & Filter Replacement'],
        defaults={'custom_price': Decimal('400.00'), 'estimated_time': '45 mins', 'is_available': True}
    )
    MechanicService.objects.get_or_create(
        mechanic=m1_profile,
        service=services['Comprehensive Periodic General Service'],
        defaults={'custom_price': Decimal('800.00'), 'estimated_time': '2 hours', 'is_available': True}
    )
    MechanicService.objects.get_or_create(
        mechanic=m2_profile,
        service=services['Car Major Periodic Maintenance'],
        defaults={'custom_price': Decimal('2200.00'), 'estimated_time': '3 hours', 'is_available': True}
    )
    MechanicService.objects.get_or_create(
        mechanic=m2_profile,
        service=services['Brake Disc & Pad Overhaul'],
        defaults={'custom_price': Decimal('650.00'), 'estimated_time': '1.5 hours', 'is_available': True}
    )

    # 4. Customer: Kumar (as in the prompt scenario!)
    c_user, _ = User.objects.get_or_create(username='kumar', defaults={'email': 'kumar@example.com', 'first_name': 'Kumar', 'last_name': 'S'})
    c_user.set_password(DEMO_PASSWORD)
    c_user.save()
    c_profile, _ = CustomerProfile.objects.get_or_create(
        user=c_user,
        defaults={
            'phone': '9876543210',
            'address': '22, Velachery Bypass Road',
            'city': 'Chennai'
        }
    )

    # Customer Vehicles
    v1, _ = Vehicle.objects.get_or_create(
        customer=c_profile,
        vehicle_number='TN 23 AB 1234',
        defaults={
            'vehicle_name': 'Honda Activa 6G',
            'vehicle_type': '2_WHEELER',
            'model_year': 2023,
            'color': 'Pearl Metallic Black',
            'fuel_type': 'PETROL'
        }
    )
    v2, _ = Vehicle.objects.get_or_create(
        customer=c_profile,
        vehicle_number='TN 07 CD 5678',
        defaults={
            'vehicle_name': 'Maruti Suzuki Swift VXi',
            'vehicle_type': '4_WHEELER',
            'model_year': 2022,
            'color': 'Arctic White',
            'fuel_type': 'PETROL'
        }
    )

    # 5. Completed Sample Booking with Invoice and Review
    past_date = datetime.date.today() - datetime.timedelta(days=2)
    b_completed, b_created = Booking.objects.get_or_create(
        booking_number='BK-ACTIVA-001',
        defaults={
            'customer': c_profile,
            'vehicle': v1,
            'mechanic': m1_profile,
            'service': services['Engine Oil & Filter Replacement'],
            'appointment_date': past_date,
            'appointment_time': datetime.time(10, 0),
            'status': 'COMPLETED',
            'customer_notes': 'Engine makes slight rattling noise when accelerating and periodic oil change due.',
            'mechanic_notes': 'Drained old oil, installed new Castrol Active 10W-30 oil (0.8L), cleaned oil strainer and adjusted idle RPM.'
        }
    )

    if b_created:
        inv, _ = Invoice.objects.get_or_create(
            booking=b_completed,
            defaults={
                'service_charge': Decimal('400.00'),
                'labour_charge': Decimal('250.00'),
                'parts_charge': Decimal('450.00'),
                'parts_details': 'Castrol 10W-30 Semi-Synthetic Engine Oil 800ml (₹380), Drain Bolt Gasket (₹20), Air Filter O-Ring (₹50)',
                'is_paid': True
            }
        )
        Payment.objects.get_or_create(
            invoice=inv,
            defaults={
                'transaction_id': 'TXN-KUMAR-998811',
                'amount': inv.total_amount,
                'payment_method': 'UPI',
                'payment_status': 'SUCCESS'
            }
        )
        Review.objects.get_or_create(
            booking=b_completed,
            defaults={
                'customer': c_profile,
                'mechanic': m1_profile,
                'rating': 5,
                'comment': 'Ramesh did an outstanding job! The engine feels super smooth and quiet now. Transparent pricing and completed well within 45 minutes. Highly recommended!'
            }
        )

    print("Seed completed successfully! Ready for testing.")

if __name__ == '__main__':
    seed()
