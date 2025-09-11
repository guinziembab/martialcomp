from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime
from django.conf import settings
from apps.grades.services import CertificateNumberGenerator
from apps.competitions.services import LicenseNumberGenerator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@csrf_exempt
def generate_certificate_number(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        discipline_id = data.get('discipline_id')
        organization_id = data.get('organization_id')
        birth_date = data.get('birth_date')
        certificate_number = CertificateNumberGenerator.generate(
            discipline_id=discipline_id,
            organization_id=organization_id,
            birth_date=birth_date
        )
        return JsonResponse({'certificate_number': certificate_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def generate_license_number(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        discipline_id = data.get('discipline_id')
        club_id = data.get('club_id')
        birth_date = data.get('birth_date')
        license_number = LicenseNumberGenerator.generate(
            discipline_id=discipline_id,
            club_id=club_id,
            birth_date=birth_date
        )
        return JsonResponse({'license_number': license_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400) 


def health(request):
    """Simple health check endpoint for mobile/web clients."""
    return JsonResponse({
        'status': 'ok',
        'time': datetime.utcnow().isoformat() + 'Z',
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
    })


def info(request):
    """Basic info endpoint to expose minimal runtime details."""
    return JsonResponse({
        'app': 'MartialComp',
        'version': getattr(settings, 'APP_VERSION', 'dev'),
        'debug': getattr(settings, 'DEBUG', False),
    })


def recent_notifications(request):
    """Return a small list of recent notifications (placeholder)."""
    data = [
        { 'id': 1, 'title': 'Bienvenue sur MartialComp', 'message': 'Votre compte est prêt.', 'type': 'system' },
        { 'id': 2, 'title': 'Événement', 'message': 'Nouvelle compétition publiée.', 'type': 'competition' },
        { 'id': 3, 'title': 'Paiement', 'message': 'Paiement enregistré.', 'type': 'payment' },
    ]
    return JsonResponse({'notifications': data})


class MobileDashboardView(APIView):
    """Minimal mobile dashboard endpoint to satisfy mobile app.
    Returns a lightweight descriptor; can be expanded later.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = getattr(request, 'user', None)
        organization = getattr(user, 'organization', None) if user else None
        return Response({
            'role': getattr(user, 'role', 'guest') if user else 'guest',
            'organization': {
                'id': getattr(organization, 'id', None),
                'name': getattr(organization, 'name', None),
                'type': getattr(organization, 'organization_type', None),
            } if organization else None,
            'statistics': {},
            'modules': [],
            'capabilities': getattr(user, 'permissions', []) if user and hasattr(user, 'permissions') else [],
        })


class PaymentMethodsView(APIView):
    """Basic list of payment methods for mobile app."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {'id': 'card', 'name': 'Carte bancaire', 'enabled': True},
            {'id': 'paypal', 'name': 'PayPal', 'enabled': True},
            {'id': 'bank_transfer', 'name': 'Virement bancaire', 'enabled': False},
        ])