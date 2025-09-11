# Fichier: competitions/context_processors.py

from django.urls import reverse, NoReverseMatch
from django.utils import timezone

def url_checker(request):
    """
    Ajoute un dictionnaire des URLs disponibles au contexte de tous les templates.
    Cela permet de vérifier si une URL existe avant d'essayer de la générer.
    """
    # Ensemble qui contiendra les URLs disponibles
    available_urls = set()
    
    # Liste des URLs Ã  vérifier (ajustez selon vos besoins)
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
    
    # Création d'une fonction de cache locale pour éviter les requÃªtes multiples
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
    
# competitions/context_processors.py

def federation_sidebar_context(request):
    """
    Ajoute les données du menu latéral pour les fédérations
    au contexte des templates.
    """
    # Exemple de base - Ã  adapter selon vos besoins
    return {
        'federation_sidebar_items': [
            {'name': 'Tableau de bord', 'url': 'competitions:federation:dashboard', 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Compétitions', 'url': 'competitions:federation:competitions', 'icon': 'fas fa-trophy'},
            {'name': 'Clubs', 'url': 'competitions:federation:clubs', 'icon': 'fas fa-building'},
            {'name': 'Licences', 'url': 'competitions:federation:licences:list', 'icon': 'fas fa-id-card'},
            {'name': 'Paramètres', 'url': 'competitions:federation:settings', 'icon': 'fas fa-cog'},
        ]
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

