from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.http import JsonResponse
from competitions.views import welcome
from competitions.views.auth import signup_view, logout_view, login_view
from competitions.views.management.results import public_results
from competitions.views.pages import translations_test, translation_debug
from competitions.views.debug_csrf import debug_csrf, debug_csrf_template
from competitions.views.test_csrf import test_csrf_login
from competitions.views.api import get_grades_for_disciplines

# Vue de debug pour la configuration des langues
def language_debug(request):
    from django.conf import settings
    return JsonResponse({
        'active_language': request.LANGUAGE_CODE,
        'available_languages': {code: name for code, name in settings.LANGUAGES},
        'default_language': settings.LANGUAGE_CODE,
        'session': {key: str(request.session.get(key)) for key in request.session.keys()},
        'cookies': {key: request.COOKIES.get(key) for key in request.COOKIES.keys()},
    })

# Assurez-vous que cette ligne est correcte
admin.autodiscover()  # Assurez-vous que tous les sites d'administration sont découverts

from django.conf.urls.i18n import i18n_patterns

# URLs sans préfixe de langue
urlpatterns = [
    # Language selection
    path('set-language/', set_language, name='set_language'),
    path('language-debug/', language_debug, name='language_debug'),
    path('translation-debug/', translation_debug, name='translation_debug'),
    
    # Débogage CSRF
    path('debug-csrf/', debug_csrf, name='debug_csrf'),
    path('debug-csrf-template/', debug_csrf_template, name='debug_csrf_template'),
    path('test-csrf-login/', test_csrf_login, name='test_csrf_login'),
    
    # API REST
    path('api/', include('api.urls')),
    # API pour les grades par disciplines
    path('api/grades/disciplines/', get_grades_for_disciplines, name='api_grades_for_disciplines'),
]

# URLs avec préfixe de langue
urlpatterns += i18n_patterns(
    # Admin (placé en premier pour éviter les conflits)
    path('admin/', admin.site.urls),
    
    # Authentication personnalisée
    path('logout/', logout_view, name='logout'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('accounts/login/', login_view, name='accounts_login'),
    path('accounts/logout/', logout_view, name='accounts_logout'),
    
    # Page de test des traductions
    path('translations-test/', translations_test, name='translations_test'),
    
    # Routes d'authentification restantes de Django
    path('accounts/', include('django.contrib.auth.urls')),
    # Routes des rôles et permissions
    path('permissions/', include(('permissions_manager.urls', 'permissions_manager'), namespace='permissions_manager')),
    
    # Modules des compétitions - avec namespace principal 'competitions'
    path('competitions/', include(('competitions.urls', 'competitions'), namespace='competitions')),
    path('competitions/clubs/', include(('competitions.urls.club', 'competitions'), namespace='clubs')),
    
    # Module de gestion des grades - Nouvelle approche
    path('grades/', include(('grades.urls', 'grades'), namespace='grades')),
    # path('api/grades/', include('grades.urls.api')), 
    
    # path('api/', include('competitions.urls.api')),
    
    # Page d'accueil
    path('', welcome, name='welcome'),
    
    # Tableau de bord - intégré directement
    path('dashboard/', include(('competitions.urls.dashboard', 'competitions'), namespace='dashboard')),
    
    # Onboarding
    path('onboarding/', include(('competitions.urls.onboarding', 'competitions'), namespace='onboarding')),
    # Inclure les URLs de management
    path('management/', include(('competitions.urls.management', 'competitions'), namespace='management')),
    
    # Interfaces publiques
    # path('<int:competition_id>/results/public/<str:token>/', 'competitions.views.management.results.public_results', name='public_results'),
    path('<int:competition_id>/results/public/<str:token>/', public_results, name='public_results'),
    
    # URL organisations - CORRECTION ICI
    # Changé de 'competitions.urls.organizations' à 'organizations.urls'
    path('organizations/', include(('organizations.urls', 'organizations'), namespace='organizations')),
    
    # Module de gestion des finances
    path('finances/', include(('finances.urls', 'finances'), namespace='finances')),
    # URLs de débogage pour les finances (sans vérification de permission)
    path('finances-debug/', include('finances.debug_urls')),
    
    # Module boutique d'équipements
    path('shop/', include(('shop.urls', 'shop'), namespace='shop')),
    
    # Module multi-tenant
    path('tenant/', include(('multitenant.urls', 'multitenant'), namespace='multitenant')),
    
    # Module de gestion documentaire
    # path('documents/', include(('documents.urls', 'documents'), namespace='documents')),
    
    # Module de gestion familiale
    path('families/', include(('family_management.urls', 'family_management'), namespace='family_management')),
)

# Ajouter la gestion des fichiers statiques
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)