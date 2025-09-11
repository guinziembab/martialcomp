from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def trans(text):
    """
    Filtre pour traduire une chaÃ®ne dans un template.
    Usage: {{ "texte"|trans }}
    """
    return _(text)

@register.filter
def get_item(dictionary, key):
    """
    Récupère un élément d'un dictionnaire par sa clé
    Retourne un dictionnaire vide si la clé n'existe pas ou si le dictionnaire est None
    """
    if dictionary is None:
        return {}
    
    # Gestion des objets comme clés (conversion en ID si nécessaire)
    key_value = key
    if hasattr(key, 'id'):
        key_value = key.id
    
    # Si la clé est un nombre sous forme de chaÃ®ne, convertir en entier
    if isinstance(key_value, str) and key_value.isdigit():
        key_value = int(key_value)
    
    # Si la clé contient un point, c'est une clé imbriquée
    if isinstance(key_value, str) and '.' in key_value:
        parts = key_value.split('.')
        result = dictionary
        for part in parts:
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return {}
        return result
    
    # Récupération avec get() pour éviter KeyError, retourne un dictionnaire vide par défaut
    return dictionary.get(key_value, {})

@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise la valeur par l'argument"""
    try:
        if float(arg) == 0:  # Ã‰viter la division par zéro
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentof(value, total):
    """Calcule le pourcentage de value par rapport Ã  total"""
    try:
        if float(total) == 0:  # Ã‰viter la division par zéro
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Soustrait l'argument de la valeur"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='abs')
def abs_filter(value):
    """Retourne la valeur absolue d'un nombre"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def setvar(val=None):
    """Définit une variable dans un template"""
    return val

@register.filter
def filter_by_type(categories, type_id):
    """
    Filtre une liste de catégories par type de compétition.
    
    Usage:
    {% for category in categories|filter_by_type:comp_type.id %}
        ...
    {% endfor %}
    """
    return [category for category in categories if category.competition_type_id == int(type_id)]

@register.filter
def get_field(form, field_name):
    """
    Récupère un champ de formulaire par son nom.
    Utile pour accéder aux champs avec des noms dynamiques.
    
    Usage: {{ form|get_field:field_name }}
    """
    try:
        return form[field_name]
    except (KeyError, TypeError):
        return None

@register.filter
def get_field_value(form, field_name):
    """
    Récupère la valeur d'un champ de formulaire par son nom.
    
    Usage: {{ form|get_field_value:field_name }}
    """
    try:
        return form[field_name].value()
    except (KeyError, AttributeError, TypeError):
        return None

@register.filter
def get_field_errors(form, field_name):
    """
    Récupère les erreurs d'un champ de formulaire par son nom.
    
    Usage: {{ form|get_field_errors:field_name }}
    """
    try:
        return form[field_name].errors
    except (KeyError, AttributeError, TypeError):
        return None

@register.filter
@stringfilter
def get_category_object(category_id):
    """
    Récupère un objet de catégorie Ã  partir de son ID.
    Permet d'afficher les détails d'une catégorie dans un template.
    
    Usage: {{ category_id|get_category_object }}
    """
    from apps.competitions.models import CompetitionCategory
    
    try:
        return CompetitionCategory.objects.get(id=int(category_id))
    except (CompetitionCategory.DoesNotExist, ValueError, TypeError):
        return None

@register.filter
def format_weight(weight):
    """
    Formate un poids pour l'affichage
    
    Usage: {{ category.min_weight|format_weight }}
    """
    if weight is None:
        return ""
    
    try:
        weight_float = float(weight)
        if weight_float.is_integer():
            return str(int(weight_float))
        else:
            return str(weight_float)
    except (ValueError, TypeError):
        return str(weight)

@register.filter
def format_grade(grade):
    """
    Formate un grade pour l'affichage
    
    Usage: {{ category.min_grade|format_grade }}
    """
    if not grade:
        return ""
    
    # Remplacer les underscores par des espaces pour l'affichage
    return grade.replace('_', ' ')

@register.filter
def format_age(age):
    """
    Formate un Ã¢ge pour l'affichage
    
    Usage: {{ category.min_age|format_age }}
    """
    if age is None:
        return ""
    
    try:
        return str(int(age))
    except (ValueError, TypeError):
        return str(age)

@register.filter
def format_gender(gender):
    """
    Formate un genre pour l'affichage
    
    Usage: {{ category.gender|format_gender }}
    """
    if not gender:
        return _("Mixte")
    
    gender_map = {
        'male': _('Hommes'),
        'female': _('Femmes'),
        'mixed': _('Mixte')
    }
    
    return gender_map.get(gender.lower(), gender)

@register.filter
def has_category_for_type(registration, competition_type_id):
    """
    Vérifie si une inscription a une catégorie pour un type de compétition donné
    
    Usage: {% if registration|has_category_for_type:competition_type.id %}...{% endif %}
    """
    if not registration:
        return False
    
    try:
        from apps.competitions.models import ParticipantCategoryRegistration
        
        return ParticipantCategoryRegistration.objects.filter(
            registration=registration,
            competition_type_id=competition_type_id
        ).exists()
    except Exception:
        return False

@register.filter
def get_category_for_type(registration, competition_type_id):
    """
    Récupère la catégorie d'une inscription pour un type de compétition donné
    
    Usage: {{ registration|get_category_for_type:competition_type.id }}
    """
    if not registration:
        return None
    
    try:
        from apps.competitions.models import ParticipantCategoryRegistration
        
        category_reg = ParticipantCategoryRegistration.objects.filter(
            registration=registration,
            competition_type_id=competition_type_id
        ).first()
        
        if category_reg:
            return category_reg.category
        return None
    except Exception:
        return None

@register.filter
def get_nested_item(dictionary, keys_str):
    """
    Récupère une valeur imbriquée dans un dictionnaire en utilisant un chemin de clés.
    
    Usage: {{ competition_stats|get_nested_item:'competition.id.participants_count' }}
    """
    if dictionary is None:
        return None
    
    keys = keys_str.split('.')
    result = dictionary
    
    for key in keys:
        try:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        except (KeyError, TypeError, AttributeError):
            return None
    
    return result

@register.filter
def is_user_registered(event, user):
    """
    Vérifie si un utilisateur est inscrit Ã  un événement.
    
    Usage: {{ event|is_user_registered:user }}
    """
    if not event or not user:
        return False
    
    if not user.is_authenticated:
        return False
    
    # Utiliser la méthode du modèle si elle existe
    if hasattr(event, 'is_user_registered'):
        return event.is_user_registered(user)
    
    # Fallback : vérifier directement via les participants
    return event.participants.filter(user=user).exists()

@register.filter
def add_class(field, css_class):
    """
    Ajoute une classe CSS Ã  un champ de formulaire.
    
    Usage: {{ form.field|add_class:"form-control" }}
    """
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field

@register.filter
def add_error_class(field, css_class):
    """
    Ajoute une classe CSS Ã  un champ de formulaire s'il contient des erreurs.
    
    Usage: {{ form.field|add_error_class:"error" }}
    """
    if hasattr(field, 'errors') and field.errors:
        attrs = {'class': f"{field.field.widget.attrs.get('class', '')} {css_class}"}
        return field.as_widget(attrs=attrs)
    return field

@register.filter
def add_attr(field, attr_string):
    """
    Ajoute un ou plusieurs attributs Ã  un champ de formulaire.
    
    Usage: {{ form.field|add_attr:"placeholder:Entrez votre texte,autocomplete:off" }}
    """
    if not hasattr(field, 'as_widget'):
        return field
    
    attrs = {}
    pairs = attr_string.split(',')
    
    for pair in pairs:
        try:
            key, value = pair.split(':')
            attrs[key.strip()] = value.strip()
        except ValueError:
            continue
    
    return field.as_widget(attrs=attrs)

@register.filter
def placeholder(field, text):
    """
    Ajoute un attribut placeholder Ã  un champ de formulaire.
    
    Usage: {{ form.field|placeholder:"Entrez votre texte" }}
    """
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'placeholder': text})
    return field

@register.filter
def field_type(field):
    """
    Retourne le type d'un champ de formulaire.
    
    Usage: {% if form.field|field_type == 'CheckboxInput' %}...{% endif %}
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        return field.field.widget.__class__.__name__
    return ""

