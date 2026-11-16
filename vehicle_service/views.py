import json
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from accounts.models import MechanicProfile, CustomerProfile
from services.models import Service
from bookings.models import Booking
from billing.models import Review
from .notifications import update_whatsapp_delivery

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == 'GET':
        if (request.GET.get('hub.mode') == 'subscribe' and
                request.GET.get('hub.verify_token') == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN and
                settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN):
            return HttpResponse(request.GET.get('hub.challenge', ''), content_type='text/plain')
        return HttpResponse(status=403)
    try:
        payload = json.loads(request.body or b'{}')
        count = 0
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                for item in change.get('value', {}).get('statuses', []):
                    errors = item.get('errors', [])
                    count += update_whatsapp_delivery(item.get('id'), item.get('status'), json.dumps(errors) if errors else '')
        return JsonResponse({'ok': True, 'updated': count})
    except (ValueError, TypeError, AttributeError):
        logger.exception('Invalid WhatsApp webhook payload')
        return JsonResponse({'ok': False}, status=400)

def home(request):
    featured_services = Service.objects.filter(is_active=True)[:6]
    top_mechanics = MechanicProfile.objects.filter(approval_status='APPROVED', is_available=True)[:4]
    
    total_customers = CustomerProfile.objects.count()
    total_mechanics = MechanicProfile.objects.filter(approval_status='APPROVED').count()
    total_completed = Booking.objects.filter(status='COMPLETED').count()
    recent_reviews = Review.objects.select_related('customer__user', 'mechanic__user').order_by('-created_at')[:3]

    context = {
        'featured_services': featured_services,
        'top_mechanics': top_mechanics,
        'total_customers': total_customers,
        'total_mechanics': total_mechanics,
        'total_completed': total_completed,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'home.html', context)

