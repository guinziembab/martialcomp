from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import gettext as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

def features_view(request):
    return render(request, 'competitions/pages/features.html')

def competitions_view(request):
    return render(request, 'competitions/pages/competitions.html')

def clubs_view(request):
    return render(request, 'competitions/pages/clubs.html')

def contact_view(request):
    return render(request, 'competitions/pages/contact.html')

@login_required
def translations_test(request):
    """
    Vue pour tester les traductions.
    """
    return render(request, 'translations_test.html')

@staff_member_required
def translation_debug(request):
    """
    Vue de diagnostic complet pour les traductions.
    """
    from django.conf import settings
    from django.middleware.locale import LocaleMiddleware
    import os
    
    # Récupérer les informations de configuration
    context = {
        'LANGUAGE_CODE': getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE),
        'LANGUAGES': settings.LANGUAGES,
        'USE_I18N': settings.USE_I18N,
        'LOCALE_PATHS': settings.LOCALE_PATHS,
        'middleware': [m.__module__ + '.' + m.__name__ if hasattr(m, '__module__') and hasattr(m, '__name__') 
                       else str(m) for m in settings.MIDDLEWARE],
    }
    
    # Informations sur les cookies et la session
    context['cookies_display'] = '\n'.join([f"{key}: {request.COOKIES.get(key)}" 
                                          for key in request.COOKIES.keys()])
    
    session_data = {}
    for key in request.session.keys():
        try:
            session_data[key] = request.session.get(key)
        except:
            session_data[key] = "Error retrieving value"
    
    context['session_display'] = '\n'.join([f"{key}: {value}" for key, value in session_data.items()])
    
    # Informations sur les fichiers de traduction
    mo_files = []
    for root, dirs, files in os.walk(os.path.join(settings.BASE_DIR, 'locale')):
        for file in files:
            if file.endswith('.mo'):
                mo_files.append(os.path.join(root, file).replace(str(settings.BASE_DIR), ''))
    
    context['mo_files'] = '\n'.join(mo_files)
    
    return render(request, 'translation_debug.html', context)

def privacy_policy_view(request):
    """
    Vue pour la politique de confidentialité - Obligatoire pour les API sociales
    """
    return render(request, 'competitions/pages/privacy_policy.html')

def terms_of_service_view(request):
    """
    Vue pour les conditions de service - Obligatoire pour les API sociales
    """
    return render(request, 'competitions/pages/terms_of_service.html')

@login_required
def delete_account_view(request):
    """
    Vue pour la suppression du compte utilisateur - Conformité GDPR
    """
    if request.method == 'POST':
        confirm = request.POST.get('confirm_deletion')
        if confirm == 'DELETE':
            user = request.user
            username = user.username
            
            # Déconnexion avant suppression
            logout(request)
            
            # Suppression du compte (cascade automatique des données liées)
            user.delete()
            
            messages.success(request, _('Votre compte a été supprimé avec succès.'))
            return redirect('welcome')
        else:
            messages.error(request, _('Veuillez taper "DELETE" pour confirmer la suppression.'))
    
    return render(request, 'competitions/pages/delete_account.html')
