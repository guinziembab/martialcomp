import re
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.translation import activate

# Django 4.2+ utilise cette clé
LANGUAGE_SESSION_KEY = '_language'
import logging

logger = logging.getLogger(__name__)


def replace_language_prefix(url, new_language, available_languages):
    """
    Remplace le préfixe de langue dans l'URL par la nouvelle langue.
    Ex: /fr/competitions/ -> /en/competitions/
    """
    # Liste des codes de langue disponibles
    lang_codes = [lang[0] for lang in available_languages]

    # Pattern pour détecter le préfixe de langue (ex: /fr/, /en/, /es/)
    pattern = r'^/(' + '|'.join(re.escape(code) for code in lang_codes) + r')(/|$)'

    match = re.match(pattern, url)
    if match:
        # Remplacer l'ancien préfixe par le nouveau
        old_lang = match.group(1)
        new_url = '/' + new_language + url[len(old_lang) + 1:]
        return new_url
    else:
        # Pas de préfixe de langue, ajouter le nouveau
        if url.startswith('/'):
            return '/' + new_language + url
        else:
            return '/' + new_language + '/' + url


@never_cache
@csrf_protect
def custom_set_language(request):
    """
    Vue personnalisée pour changer de langue avec meilleure gestion d'erreur.
    Remplace la vue standard django.views.i18n.set_language.

    IMPORTANT: Cette vue gère correctement le changement de préfixe de langue
    dans l'URL (ex: /fr/... -> /en/...) pour fonctionner avec i18n_patterns.
    """
    # Support GET et POST pour contourner les problèmes de proxy
    if request.method in ['POST', 'GET']:
        # Récupérer la langue depuis POST ou GET
        language = request.POST.get('language') or request.GET.get('language')
        next_url = request.POST.get('next') or request.GET.get('next', '/')

        # Log pour debug
        logger.info(f"Set language request: method={request.method}, language={language}, next={next_url}")

        # Vérifier que la langue est valide
        available_languages = settings.LANGUAGES
        lang_codes = [lang[0] for lang in available_languages]

        if language and language in lang_codes:
            # Activer la langue
            activate(language)

            # Sauvegarder dans la session
            if hasattr(request, 'session'):
                request.session[LANGUAGE_SESSION_KEY] = language
                # Force la sauvegarde de la session
                request.session.modified = True

            # IMPORTANT: Remplacer le préfixe de langue dans l'URL de redirection
            next_url = replace_language_prefix(next_url, language, available_languages)

            # Vérifier l'URL de redirection (sécurité)
            if not url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = '/' + language + '/'

            # Log de la redirection
            logger.info(f"Redirecting to: {next_url}")

            # Créer la réponse avec redirection
            response = HttpResponseRedirect(next_url)

            # Définir le cookie de langue
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language,
                max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', 365 * 24 * 60 * 60),
                path=getattr(settings, 'LANGUAGE_COOKIE_PATH', '/'),
                domain=getattr(settings, 'LANGUAGE_COOKIE_DOMAIN', None),
                secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
                httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
                samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
            )

            # Log de succès
            logger.info(f"Language changed successfully to {language}")

            return response
        else:
            # Log d'erreur
            logger.error(f"Invalid language: {language}. Available: {lang_codes}")

            # Retourner une erreur JSON si AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Invalid language',
                    'available': lang_codes
                }, status=400)

    # Redirection par défaut
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))