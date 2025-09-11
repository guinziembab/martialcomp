"""
Template tags pour améliorer la gestion des traductions
"""
from django import template
from django.utils.translation import get_language, gettext
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def smart_trans(context, text):
    """
    Template tag qui tente de traduire le texte,
    et applique un style spécial si la traduction est manquante.
    """
    current_lang = get_language()
    translated = gettext(text)
    
    # Si nous ne sommes pas dans la langue par défaut et la traduction est identique au texte original
    if current_lang != settings.LANGUAGE_CODE and translated == text:
        if settings.DEBUG:
            return mark_safe(f'<span class="translation-missing" title="Traduction manquante pour: {current_lang}">{text}</span>')
        else:
            return text
    return translated


@register.simple_tag
def martial_arts_term(term, show_origin=False):
    """
    Gère les termes d'arts martiaux avec leur origine culturelle
    """
    # Dictionnaire des termes avec leur origine
    martial_terms = {
        # Termes japonais
        'kata': {'origin': 'japonais', 'meaning': 'forme'},
        'kumite': {'origin': 'japonais', 'meaning': 'combat'},
        'dojo': {'origin': 'japonais', 'meaning': 'lieu d\'entraÃ®nement'},
        'sensei': {'origin': 'japonais', 'meaning': 'professeur'},
        'karate': {'origin': 'japonais', 'meaning': 'main vide'},
        'judo': {'origin': 'japonais', 'meaning': 'voie de la souplesse'},
        
        # Termes coréens
        'taekwondo': {'origin': 'coréen', 'meaning': 'voie du pied et du poing'},
        'dobok': {'origin': 'coréen', 'meaning': 'tenue d\'entraÃ®nement'},
        'dojang': {'origin': 'coréen', 'meaning': 'lieu d\'entraÃ®nement'},
        
        # Termes chinois
        'kung fu': {'origin': 'chinois', 'meaning': 'accomplissement par l\'effort'},
        'wushu': {'origin': 'chinois', 'meaning': 'art martial'},
        'tai chi': {'origin': 'chinois', 'meaning': 'boxe du faÃ®te suprÃªme'},
    }
    
    term_lower = term.lower()
    if term_lower in martial_terms:
        info = martial_terms[term_lower]
        if show_origin:
            return mark_safe(f'<span class="martial-term" title="{info["origin"]}: {info["meaning"]}">{term}</span>')
        else:
            return mark_safe(f'<span class="martial-term">{term}</span>')
    
    # Si le terme n'est pas reconnu, le traduire normalement
    return gettext(term)


@register.inclusion_tag('competitions/includes/language_selector.html', takes_context=True)
def language_selector(context):
    """
    Affiche un sélecteur de langue avec les options disponibles
    """
    current_language = get_language()
    available_languages = []
    
    for lang_code, lang_name in settings.LANGUAGES:
        available_languages.append({
            'code': lang_code,
            'name': lang_name,
            'active': lang_code == current_language
        })
    
    return {
        'current_language': current_language,
        'available_languages': available_languages,
        'request': context['request']
    }


@register.filter
def in_language(value, language_code):
    """
    Filtre pour afficher une valeur dans une langue spécifique
    Utilisé avec django-modeltranslation
    """
    if hasattr(value, f'_{language_code}'):
        return getattr(value, f'_{language_code}') or value
    return value


@register.simple_tag
def get_translation_coverage():
    """
    Retourne le pourcentage de couverture des traductions pour la langue actuelle
    """
    # Cette fonction pourrait Ãªtre étendue pour calculer réellement la couverture
    # En comptant les chaÃ®nes traduites vs non traduites
    current_lang = get_language()
    
    # Valeurs fictives pour l'exemple - Ã  remplacer par une vraie logique
    coverage_data = {
        'fr': 100,  # Langue source
        'en': 85,
        'es': 78,
        'it': 72,
        'de': 68,
    }
    
    return coverage_data.get(current_lang, 0)


@register.simple_tag
def get_current_language():
    """
    Retourne le code de la langue actuelle
    """
    return get_language()


@register.simple_tag
def get_available_languages():
    """
    Retourne la liste des langues disponibles
    """
    return settings.LANGUAGES
