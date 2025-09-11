from django.core.exceptions import PermissionDenied
"""
Vue pour le tableau de bord de gestion des traductions
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import polib
import os


@staff_member_required
def translation_dashboard(request):
    """Affiche un tableau de bord de la progression des traductions."""
    stats = []
    
    source_lang = settings.LANGUAGE_CODE
    
    for lang_code, lang_name in settings.LANGUAGES:
        if lang_code == source_lang:
            continue
        
        po_path = os.path.join('locale', lang_code, 'LC_MESSAGES', 'django.po')
        js_po_path = os.path.join('locale', lang_code, 'LC_MESSAGES', 'djangojs.po')
        
        lang_stats = {
            'code': lang_code,
            'name': lang_name,
            'total': 0,
            'translated': 0,
            'percentage': 0,
            'files': []
        }
        
        # Analyser fichier principal
        if os.path.exists(po_path):
            po = polib.pofile(po_path)
            file_total = len(po)
            file_translated = len(po.translated_entries())
            lang_stats['total'] += file_total
            lang_stats['translated'] += file_translated
            lang_stats['files'].append({
                'name': 'django.po',
                'total': file_total,
                'translated': file_translated,
                'percentage': round(file_translated / file_total * 100, 1) if file_total > 0 else 0
            })
        
        # Analyser fichier JavaScript
        if os.path.exists(js_po_path):
            js_po = polib.pofile(js_po_path)
            file_total = len(js_po)
            file_translated = len(js_po.translated_entries())
            lang_stats['total'] += file_total
            lang_stats['translated'] += file_translated
            lang_stats['files'].append({
                'name': 'djangojs.po',
                'total': file_total,
                'translated': file_translated,
                'percentage': round(file_translated / file_total * 100, 1) if file_total > 0 else 0
            })
        
        # Calculer pourcentage global
        if lang_stats['total'] > 0:
            lang_stats['percentage'] = round(lang_stats['translated'] / lang_stats['total'] * 100, 1)
        
        stats.append(lang_stats)
    
    # Calculer les statistiques globales
    total_strings = sum(stat['total'] for stat in stats)
    total_translated = sum(stat['translated'] for stat in stats)
    global_percentage = round(total_translated / total_strings * 100, 1) if total_strings > 0 else 0
    
    context = {
        'stats': stats,
        'source_language': dict(settings.LANGUAGES)[source_lang],
        'total_strings': total_strings,
        'total_translated': total_translated,
        'global_percentage': global_percentage,
        'title': 'Tableau de bord des traductions'
    }
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse(context)
    
    return render(request, 'admin/translation_dashboard.html', context)


@staff_member_required
def translation_stats_api(request):
    """API pour obtenir les statistiques de traduction en JSON"""
    # Réutiliser la logique de translation_dashboard
    response = translation_dashboard(request)
    if hasattr(response, 'context_data'):
        return JsonResponse(response.context_data)
    return response


def detect_untranslated_strings(request):
    """
    Détecte les chaÃ®nes non traduites dans les templates
    """
    import re
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist
    
    untranslated_patterns = [
        r'>\s*[A-Za-z][^<>]*[a-z]\s*<',  # Texte entre balises
        r'placeholder\s*=\s*["\'][^"\']*[a-z][^"\']*["\']',  # Placeholders
        r'title\s*=\s*["\'][^"\']*[a-z][^"\']*["\']',  # Titres
    ]
    
    # Cette fonction pourrait Ãªtre étendue pour scanner réellement les templates
    # et détecter les chaÃ®nes non marquées pour traduction
    
    return JsonResponse({
        'message': 'Fonctionnalité en développement',
        'patterns': untranslated_patterns
    })
