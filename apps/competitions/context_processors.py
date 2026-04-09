# Fichier: competitions/context_processors.py

from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

def url_checker(request):
    """
    Ajoute un dictionnaire des URLs disponibles au contexte de tous les templates.
    Cela permet de vérifier si une URL existe avant d'essayer de la générer.
    """
    # Ensemble qui contiendra les URLs disponibles
    available_urls = set()

    # Liste des URLs à vérifier (ajustez selon vos besoins)
    urls_to_check = [
        'competitions:club:practitioners',
        'competitions:club:practitioner_add',
        'competitions:club:registrations_list',
        'competitions:club:available_competitions',
        'competitions:club:bulk_registration',
        'competitions:club:register_practitioner',
        'competitions:club:import_export',
        'competitions:club:judges_list',
        'competitions:dashboard',
        'competitions:dashboard:club',
        'competitions:dashboard:admin',
        'competitions:dashboard:manager',
        'competitions:dashboard:participant',
        'competitions:dashboard:pro',
        'competitions:dashboard:referee',
        'competitions:dashboard:spectator',
        'competitions:competitions:list',
        'competitions:competitions:register',
    ]

    # Vérifier chaque URL
    for url_name in urls_to_check:
        try:
            reverse(url_name)
            available_urls.add(url_name)
        except NoReverseMatch:
            # Ignorer les URLs qui ne sont pas disponibles
            pass

    return {
        'available_urls': available_urls
    }

def global_context(request):
    """
    Contexte global disponible dans tous les templates.
    """
    return {
        'current_year': timezone.now().year,
        'is_user_authenticated': request.user.is_authenticated,
    }

def category_cache(request):
    """
    Contexte qui fournit une fonction pour récupérer des objets de catégorie par ID.
    """
    from apps.competitions.models import CompetitionCategory

    # Création d'une fonction de cache locale pour éviter les requêtes multiples
    _category_cache = {}

    def get_category(category_id):
        """Récupère une catégorie depuis le cache ou la base de données."""
        if not category_id:
            return None

        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return None

        if category_id not in _category_cache:
            try:
                _category_cache[category_id] = CompetitionCategory.objects.get(id=category_id)
            except CompetitionCategory.DoesNotExist:
                _category_cache[category_id] = None

        return _category_cache[category_id]

    return {
        'get_category': get_category,
    }

def federation_sidebar_context(request):
    """
    Ajoute les données du menu latéral pour les fédérations
    au contexte des templates.
    Note: Les URLs sont vérifiées avant d'être ajoutées pour éviter les NoReverseMatch.
    """
    sidebar_items = []

    # Liste des items avec leurs URLs potentielles
    potential_items = [
        {'name': _('Tableau de bord'), 'url': 'competitions:federations:list', 'icon': 'fas fa-tachometer-alt'},
        {'name': _('Compétitions'), 'url': 'competitions:competitions:list', 'icon': 'fas fa-trophy'},
        {'name': _('Clubs'), 'url': 'competitions:federations:list', 'icon': 'fas fa-building'},
        {'name': _('Juges'), 'url': 'competitions:club:judges_list', 'icon': 'fas fa-gavel'},
    ]

    # Vérifier chaque URL avant de l'ajouter
    for item in potential_items:
        try:
            reverse(item['url'])
            sidebar_items.append(item)
        except NoReverseMatch:
            # Ignorer les URLs qui n'existent pas
            pass

    return {
        'federation_sidebar_items': sidebar_items
    }

def language_context(request):
    """
    Ajoute des informations sur les langues au contexte des templates.
    """
    from django.conf import settings
    from django.utils import translation

    # Obtenir la langue actuelle
    current_language = translation.get_language()

    # Créer une liste des langues disponibles avec des informations complètes
    available_languages = []
    for lang_code, lang_name in settings.LANGUAGES:
        available_languages.append({
            'code': lang_code,
            'name': lang_name,
            'active': lang_code == current_language
        })

    return {
        'LANGUAGES': settings.LANGUAGES,
        'LANGUAGE_CODE': current_language,
        'available_languages': available_languages,
    }


def judge_context(request):
    """
    PROMPT 7 - Context processor pour les badges et informations juge technique.
    Ajoute au contexte global:
    - can_switch_to_judge: booléen indiquant si l'utilisateur peut basculer en mode juge
    - pending_judge_performances_count: nombre de performances en attente de notation
    - current_dashboard_mode: mode actuel du dashboard (participant ou judge_technical)
    """
    context = {
        'can_switch_to_judge': False,
        'pending_judge_performances_count': 0,
        'current_dashboard_mode': 'participant',
    }

    if not request.user.is_authenticated:
        return context

    try:
        from apps.competitions.models import Practitioner, Judge
        from apps.competitions.services.judge_service import JudgeService

        # Récupérer le mode actuel depuis la session
        context['current_dashboard_mode'] = request.session.get('dashboard_mode', 'participant')

        # Chercher le practitioner lié à l'utilisateur
        practitioner = Practitioner.objects.filter(user=request.user).first()

        if practitioner:
            # Vérifier si le practitioner peut basculer en mode juge
            can_switch = JudgeService.can_switch_to_judge_view(practitioner)
            context['can_switch_to_judge'] = can_switch

            if can_switch:
                # Récupérer le juge et le nombre de performances en attente
                judge = JudgeService.get_judge_for_practitioner(practitioner)
                if judge:
                    context['pending_judge_performances_count'] = JudgeService.get_pending_performances_count(judge)

    except ImportError:
        pass
    except Exception:
        pass

    return context
