from django.core.exceptions import PermissionDenied
# competitions/api_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import json

User = get_user_model()

def add_cors_headers(response):
    """Ajoute les headers CORS à une réponse"""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
    response["Access-Control-Allow-Credentials"] = "true"
    return response

@csrf_exempt
def handle_options(request):
    """Gère les requêtes OPTIONS pour CORS"""
    response = JsonResponse({})
    return add_cors_headers(response)

# ================================
# ENDPOINTS DE BASE ET SANTÉ
# ================================

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def api_health_check(request):
    """Health check endpoint pour l'app mobile"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    response = JsonResponse({
        'status': 'success',
        'message': 'API Django fonctionnelle',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health/',
            'info': '/api/info/',
            'auth': '/api/auth/',
            'competitions': '/api/competitions/',
            'organizations': '/api/organizations/',
        },
        'mobile_ready': True
    })
    return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_info(request):
    """Informations sur l'API pour l'app mobile"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    response = JsonResponse({
        'app_name': 'MartialComp',
        'description': 'Martial Arts Competition Management',
        'api_version': '1.0.0',
        'supported_languages': ['fr', 'en', 'es', 'de', 'it', 'pt', 'ru', 'vi', 'no', 'ja', 'zh-hans', 'hi', 'ar', 'sw', 'am', 'zu', 'yo', 'ko'],
        'features': {
            'competitions': True,
            'organizations': True,
            'qr_scanner': True,
            'notifications': True,
            'offline_mode': False,
            'multi_language': True,
        },
        'environment': 'development' if settings.DEBUG else 'production',
        'status': 'active'
    })
    return add_cors_headers(response)

# ================================
# AUTHENTIFICATION
# ================================

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_current_user(request):
    """Récupère l'utilisateur actuel (ou utilisateur anonyme)"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Pour le développement, on retourne un utilisateur fictif
    # En production, vous vérifierez request.user
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_data = {
            'id': str(request.user.id),
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_authenticated': True,
            'role': 'spectator',  # Valeur par défaut
            'profile': {
                'onboarding_completed': True,
                'onboarding_step': 'completed',
            }
        }
    else:
        # Utilisateur anonyme pour développement
        user_data = {
            'id': None,
            'username': 'anonymous',
            'email': '',
            'first_name': '',
            'last_name': '',
            'is_authenticated': False,
            'role': 'spectator',
            'profile': {
                'onboarding_completed': False,
                'onboarding_step': 'welcome',
            }
        }
    
    response = JsonResponse({
        'status': 'success',
        'user': user_data
    })
    return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_login(request):
    """Endpoint de connexion simplifié"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Pour le développement, simulation d'une connexion réussie
    response = JsonResponse({
        'status': 'success',
        'message': 'Connexion simulée réussie',
        'user': {
            'id': '1',
            'username': 'demo_user',
            'email': 'demo@martialcomp.com',
            'first_name': 'Demo',
            'last_name': 'User',
            'is_authenticated': True,
            'role': 'spectator',
        },
        'tokens': {
            'access': 'demo_access_token',
            'refresh': 'demo_refresh_token',
        }
    })
    return add_cors_headers(response)

# ================================
# COMPÉTITIONS
# ================================

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_competitions_list(request):
    """Liste des compétitions"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Données fictives pour développement
    competitions = [
        {
            'id': '1',
            'title': 'Championnat National Karaté',
            'description': 'Compétition nationale de karaté traditionnel',
            'start_date': '2025-09-15',
            'end_date': '2025-09-17',
            'location': 'Paris, France',
            'status': 'published',
            'organization': {
                'id': '1',
                'name': 'Fédération Française de Karaté',
                'type': 'federation'
            },
            'discipline': {
                'id': '1',
                'name': 'Karaté',
                'code': 'karate'
            }
        },
        {
            'id': '2',
            'title': 'Tournoi Judo Junior',
            'description': 'Compétition régionale pour juniors',
            'start_date': '2025-10-20',
            'end_date': '2025-10-22',
            'location': 'Lyon, France',
            'status': 'published',
            'organization': {
                'id': '2',
                'name': 'Club Judo Lyon',
                'type': 'club'
            },
            'discipline': {
                'id': '2',
                'name': 'Judo',
                'code': 'judo'
            }
        }
    ]
    
    response = JsonResponse({
        'status': 'success',
        'count': len(competitions),
        'results': competitions
    })
    return add_cors_headers(response)

# ================================
# ORGANISATIONS
# ================================

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_organizations_list(request):
    """Liste des organisations"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Données fictives pour développement
    organizations = [
        {
            'id': '1',
            'name': 'Fédération Française de Karaté',
            'short_name': 'FFK',
            'description': 'Fédération officielle de karaté en France',
            'organization_type': 'federation',
            'city': 'Paris',
            'country': 'France',
            'email': 'contact@ffkarate.fr',
            'website': 'https://www.ffkarate.fr',
            'disciplines': [
                {'id': '1', 'name': 'Karaté', 'code': 'karate'}
            ]
        },
        {
            'id': '2',
            'name': 'Club Judo Lyon',
            'short_name': 'CJL',
            'description': 'Club de judo à Lyon',
            'organization_type': 'club',
            'city': 'Lyon',
            'country': 'France',
            'email': 'info@judolyon.fr',
            'disciplines': [
                {'id': '2', 'name': 'Judo', 'code': 'judo'}
            ]
        }
    ]
    
    response = JsonResponse({
        'status': 'success',
        'count': len(organizations),
        'results': organizations
    })
    return add_cors_headers(response)

# ================================
# DISCIPLINES
# ================================

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_disciplines_list(request):
    """Liste des disciplines"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    disciplines = [
        {
            'id': '1',
            'name': 'Karaté',
            'code': 'karate',
            'description': 'Art martial japonais',
            'category': 'Frappe',
            'is_active': True
        },
        {
            'id': '2',
            'name': 'Judo',
            'code': 'judo',
            'description': 'Art martial japonais de préhension',
            'category': 'Préhension',
            'is_active': True
        },
        {
            'id': '3',
            'name': 'Taekwondo',
            'code': 'taekwondo',
            'description': 'Art martial coréen',
            'category': 'Frappe',
            'is_active': True
        },
        {
            'id': '4',
            'name': 'Kung Fu',
            'code': 'kungfu',
            'description': 'Art martial chinois',
            'category': 'Mixte',
            'is_active': True
        },
        {
            'id': '5',
            'name': 'Qwan Ki Do',
            'code': 'qwankido',
            'description': 'Art martial vietnamien',
            'category': 'Mixte',
            'is_active': True
        }
    ]
    
    response = JsonResponse({
        'status': 'success',
        'count': len(disciplines),
        'results': disciplines
    })
    return add_cors_headers(response)

# ================================
# NOTIFICATIONS
# ================================

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_notifications_list(request):
    """Liste des notifications"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Retourne une liste vide pour éviter les erreurs
    response = JsonResponse({
        'status': 'success',
        'count': 0,
        'results': []
    })
    return add_cors_headers(response)

# ================================
# PROFIL UTILISATEUR
# ================================

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def api_profile(request):
    """Gestion du profil utilisateur"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # Profil fictif pour développement
    profile_data = {
        'id': '1',
        'user': {
            'id': '1',
            'username': 'demo_user',
            'email': 'demo@martialcomp.com',
            'first_name': 'Demo',
            'last_name': 'User',
        },
        'phone': '+33123456789',
        'birth_date': '1990-01-01',
        'bio': 'Pratiquant d\'arts martiaux depuis 10 ans',
        'onboarding_completed': True,
        'onboarding_step': 'completed',
        'role': 'spectator',
        'disciplines': [
            {'id': '1', 'name': 'Karaté', 'level': 'Ceinture noire 1er dan'}
        ]
    }
    
    response = JsonResponse({
        'status': 'success',
        'profile': profile_data
    })
    return add_cors_headers(response)