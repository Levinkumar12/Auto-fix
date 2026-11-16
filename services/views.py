from django.shortcuts import render, get_object_or_404
from .models import Service
from mechanics.models import MechanicService

def service_list(request):
    vehicle_filter = request.GET.get('vehicle_type', '')
    services = Service.objects.filter(is_active=True)

    if vehicle_filter:
        services = services.filter(vehicle_type__in=[vehicle_filter, 'ALL'])

    return render(request, 'services/service_list.html', {
        'services': services,
        'vehicle_filter': vehicle_filter,
    })


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)
    mechanics_offering = MechanicService.objects.filter(
        service=service,
        is_available=True,
        mechanic__approval_status='APPROVED'
    ).select_related('mechanic', 'mechanic__user')

    return render(request, 'services/service_detail.html', {
        'service': service,
        'mechanics_offering': mechanics_offering,
    })
