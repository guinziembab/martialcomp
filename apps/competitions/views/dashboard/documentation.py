from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from django.utils.translation import get_language
import os
import markdown
from ...models import UserProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger('django')

@login_required
def dashboard_documentation(request, dashboard_type=None):
    """
    Vue pour afficher la documentation des tableaux de bord.
    Si dashboard_type est spécifié, affiche la documentation spécifique Ã  ce type de dashboard.
    Sinon, affiche la documentation générale.
    """
    # Vérifier que l'utilisateur a un profil
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        logger.error(f"Profil non trouvé pour l'utilisateur {request.user.username}")
        return redirect('welcome')
    
    # Chemin de base pour la documentation
    docs_base_path = os.path.join(settings.BASE_DIR, 'docs', 'dashboards')
    
    # Si aucun type de dashboard n'est spécifié, afficher la documentation générale
    if not dashboard_type:
        file_path = os.path.join(docs_base_path, 'README.md')
        template = 'competitions/dashboard/documentation/index.html'
        context_title = "Documentation des Tableaux de Bord"
    else:
        # Mappage des types de dashboard aux dossiers de documentation
        dashboard_mapping = {
            'participant': 'participants',
            'club': 'clubs',
            'federation': 'federations',
            'referee': 'referees',
            'coach_multidiscipline': 'coaches',
            'combat': 'combat',
            'neutrality': 'neutrality',
            'admin': 'admin',  # Ã€ créer si nécessaire
            'spectator': 'spectators',  # Ã€ créer si nécessaire
        }
        
        # Vérifier si le type de dashboard est valide
        if dashboard_type not in dashboard_mapping:
            logger.error(f"Type de dashboard invalide: {dashboard_type}")
            raise Http404("Documentation non trouvée")
        
        # Construire le chemin vers le fichier README.md du dashboard spécifique
        doc_folder = dashboard_mapping[dashboard_type]
        file_path = os.path.join(docs_base_path, doc_folder, 'README.md')
        template = 'competitions/dashboard/documentation/dashboard_doc.html'
        context_title = f"Documentation du Dashboard {dashboard_type.capitalize()}"
    
    # Charger la version localisée si disponible
    lang = get_language()
    if lang and lang[:2] != 'fr':
        lang_code = lang[:2]
        localized_path = file_path.replace('.md', f'_{lang_code}.md')
        if os.path.exists(localized_path):
            file_path = localized_path

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        logger.error(f"Fichier de documentation non trouvé: {file_path}")
        raise Http404("Documentation non trouvée")

    # Lire et convertir le contenu Markdown en HTML
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

    # Vérifier si un guide d'utilisation existe
    guide_exists = False
    if dashboard_type:
        guide_path = os.path.join(docs_base_path, dashboard_mapping[dashboard_type], 'guide_utilisation.md')
        guide_exists = os.path.exists(guide_path)
    
    # Construire le contexte
    context = {
        'title': context_title,
        'content': html_content,
        'dashboard_type': dashboard_type,
        'guide_exists': guide_exists,
    }
    
    return render(request, template, context)

@login_required
def dashboard_guide(request, dashboard_type):
    """
    Vue pour afficher le guide d'utilisation d'un tableau de bord spécifique.
    """
    # Vérifier que l'utilisateur a un profil
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        logger.error(f"Profil non trouvé pour l'utilisateur {request.user.username}")
        return redirect('welcome')
    
    # Mappage des types de dashboard aux dossiers de documentation
    dashboard_mapping = {
        'participant': 'participants',
        'club': 'clubs',
        'federation': 'federations',
        'referee': 'referees',
        'coach_multidiscipline': 'coaches',
        'combat': 'combat',
        'admin': 'admin',  # Ã€ créer si nécessaire
        'spectator': 'spectators',  # Ã€ créer si nécessaire
    }
    
    # Vérifier si le type de dashboard est valide
    if dashboard_type not in dashboard_mapping:
        logger.error(f"Type de dashboard invalide pour guide: {dashboard_type}")
        raise Http404("Guide d'utilisation non trouvé")
    
    # Construire le chemin vers le fichier guide_utilisation.md du dashboard spécifique
    doc_folder = dashboard_mapping[dashboard_type]
    file_path = os.path.join(settings.BASE_DIR, 'docs', 'dashboards', doc_folder, 'guide_utilisation.md')

    # Charger la version localisée si disponible
    lang = get_language()
    if lang and lang[:2] != 'fr':
        lang_code = lang[:2]
        localized_path = file_path.replace('.md', f'_{lang_code}.md')
        if os.path.exists(localized_path):
            file_path = localized_path

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        logger.error(f"Fichier de guide non trouvé: {file_path}")
        raise Http404("Guide d'utilisation non trouvé")

    # Lire et convertir le contenu Markdown en HTML
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])
    
    # Construire le contexte
    context = {
        'title': f"Guide d'Utilisation du Dashboard {dashboard_type.capitalize()}",
        'content': html_content,
        'dashboard_type': dashboard_type,
    }
    
    return render(request, 'competitions/dashboard/documentation/guide.html', context)
