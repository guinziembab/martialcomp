# apps/competitions/urls/federations.py
from django.urls import path
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from ..views.dashboard import federations

# Vues stub pour les URLs manquantes (fonctionnalités avancées)
@login_required
def stub_view(request, federation_id):
    """Vue temporaire pour les fonctionnalités en développement"""
    messages.info(request, _("Cette fonctionnalité sera bientôt disponible."))
    return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

@login_required
def upload_photos(request, federation_id):
    if request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Upload photos temporairement désactivé'}, status=501)
    return stub_view(request, federation_id)

@login_required
def update_site_info(request, federation_id):
    if request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Update site info temporairement désactivé'}, status=501)
    return stub_view(request, federation_id)

app_name = 'federations'

urlpatterns = [
    # Dashboard principal
    path('<int:federation_id>/dashboard/', federations.federation_dashboard, name='federation_dashboard'),
    
    # Vues fonctionnelles (Actions rapides)
    path('<int:federation_id>/clubs/', federations.federation_manage_clubs, name='clubs'),
    path('<int:federation_id>/competitions/', federations.federation_manage_competitions, name='competitions'),
    path('<int:federation_id>/judges/', federations.federation_manage_judges, name='judges'),
    path('<int:federation_id>/settings/', federations.federation_manage_settings, name='settings'),
    path('<int:federation_id>/managed-competitions/', federations.federation_managed_competitions, name='managed_competitions'),
    
    # Nouvelles vues fonctionnelles (créées aujourd'hui)
    path('<int:federation_id>/calendar/', federations.federation_calendar, name='calendar'),
    path('<int:federation_id>/certifications/', federations.federation_manage_certifications, name='certifications'),
    path('<int:federation_id>/create-competition/', federations.federation_create_competition, name='create_competition'),
    path('<int:federation_id>/examens/', federations.federation_examens, name='examens'),
    path('<int:federation_id>/import-export/', federations.federation_import_export, name='import_export'),
    
    # Vues stub (fonctionnalités avancées en développement)
    path('<int:federation_id>/customize-theme/', stub_view, name='customize_theme'),
    path('<int:federation_id>/generate-qr/', stub_view, name='generate_qr'),
    path('<int:federation_id>/manage-content/', stub_view, name='manage_content'),
    path('<int:federation_id>/roles/', stub_view, name='roles'),
    path('<int:federation_id>/upload-photos/', upload_photos, name='upload_photos'),
    path('<int:federation_id>/update-site-info/', update_site_info, name='update_site_info'),
]

