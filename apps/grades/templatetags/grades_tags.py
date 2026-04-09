from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé."""
    if not dictionary:
        return None

    # Tentative de conversion en int si c'est une clé numérique
    try:
        key = int(key)
    except (ValueError, TypeError):
        pass

    return dictionary.get(key)


@register.inclusion_tag('grades/grade_image.html', takes_context=True)
def grade_image(context, grade, size=30, show_name=False, css_class=''):
    """
    Affiche l'image d'un grade avec fallback sur les initiales si pas d'image.

    Usage dans les templates:
        {% load grades_tags %}
        {% grade_image grade %}                          {# Taille 30px par défaut #}
        {% grade_image grade size=20 %}                  {# Taille 20px pour les tableaux #}
        {% grade_image grade size=50 show_name=True %}   {# Avec le nom du grade #}
        {% grade_image grade css_class="my-class" %}     {# Avec classe CSS personnalisée #}

    Args:
        grade: Instance du modèle Grade ou dictionnaire avec les infos du grade
        size: Taille en pixels (défaut: 30)
        show_name: Afficher le nom du grade à côté de l'image (défaut: False)
        css_class: Classes CSS additionnelles

    Returns:
        Template HTML avec l'image ou le fallback SVG
    """
    if not grade:
        return {
            'has_grade': False,
            'size': size,
            'show_name': show_name,
            'css_class': css_class,
        }

    # Gérer le cas où grade est un dictionnaire (API) ou un objet Grade
    if isinstance(grade, dict):
        image_url = grade.get('image_url') or grade.get('image')
        color = grade.get('color_code') or grade.get('color') or '#6c757d'
        name = grade.get('name', '')
        icon = grade.get('icon', '')
        # Calculer les initiales depuis le nom
        words = name.split() if name else []
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1 and len(words[0]) >= 2:
            initials = words[0][:2].upper()
        else:
            initials = name[:2].upper() if name else 'GR'
    else:
        # C'est un objet Grade
        image_url = grade.image_url if hasattr(grade, 'image_url') else None
        color = grade.get_display_color() if hasattr(grade, 'get_display_color') else (grade.color_code or grade.color or '#6c757d')
        name = grade.name if hasattr(grade, 'name') else str(grade)
        icon = grade.icon if hasattr(grade, 'icon') else ''
        initials = grade.initials if hasattr(grade, 'initials') else name[:2].upper()

    return {
        'has_grade': True,
        'image_url': image_url,
        'color': color,
        'name': name,
        'icon': icon,
        'initials': initials,
        'size': size,
        'show_name': show_name,
        'css_class': css_class,
        'font_size': max(10, size // 3),  # Taille de police proportionnelle
    }


@register.simple_tag
def grade_image_inline(grade, size=30):
    """
    Version inline du tag grade_image qui retourne directement le HTML.
    Utile quand on ne peut pas utiliser inclusion_tag (ex: dans des boucles complexes).

    Usage:
        {% load grades_tags %}
        {% grade_image_inline grade 30 %}
    """
    if not grade:
        return mark_safe('<span class="text-muted">-</span>')

    # Gérer le cas où grade est un dictionnaire ou un objet
    if isinstance(grade, dict):
        image_url = grade.get('image_url') or grade.get('image')
        color = grade.get('color_code') or grade.get('color') or '#6c757d'
        name = grade.get('name', '')
        words = name.split() if name else []
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1 and len(words[0]) >= 2:
            initials = words[0][:2].upper()
        else:
            initials = name[:2].upper() if name else 'GR'
    else:
        image_url = grade.image_url if hasattr(grade, 'image_url') else None
        color = grade.get_display_color() if hasattr(grade, 'get_display_color') else (getattr(grade, 'color_code', '') or getattr(grade, 'color', '') or '#6c757d')
        name = getattr(grade, 'name', str(grade))
        initials = grade.initials if hasattr(grade, 'initials') else name[:2].upper()

    font_size = max(10, size // 3)

    if image_url:
        html = (
            f'<img src="{escape(image_url)}" alt="{escape(name)}" '
            f'style="width: {size}px; height: {size}px; border-radius: 4px; object-fit: cover; '
            f'border: 2px solid {escape(color)};" title="{escape(name)}" />'
        )
    else:
        html = (
            f'<div class="grade-image-fallback" style="width: {size}px; height: {size}px; '
            f'background-color: {escape(color)}; border-radius: 4px; display: inline-flex; '
            f'align-items: center; justify-content: center; color: white; font-weight: bold; '
            f'font-size: {font_size}px;" title="{escape(name)}">{escape(initials)}</div>'
        )

    return mark_safe(html)
