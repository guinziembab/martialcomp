from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

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