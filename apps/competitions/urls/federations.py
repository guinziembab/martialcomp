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
    
    # Vues fonctionnelles (Actions rapides) - version simplifiée
    path('<int:federation_id>/clubs/', federations.federation_manage_clubs, name='clubs'),
    path('<int:federation_id>/competitions/', federations.federation_manage_competitions, name='competitions'),
    path('<int:federation_id>/judges/', federations.federation_manage_judges, name='judges'),
    path('<int:federation_id>/settings/', federations.federation_manage_settings, name='settings'),
    
    # Vues stub (fonctionnalités avancées en développement)
    path('<int:federation_id>/calendar/', stub_view, name='calendar'),
    path('<int:federation_id>/certifications/', stub_view, name='certifications'),
    path('<int:federation_id>/create-competition/', stub_view, name='create_competition'),
    path('<int:federation_id>/examens/', stub_view, name='examens'),
    path('<int:federation_id>/import-export/', stub_view, name='import_export'),
    path('<int:federation_id>/customize-theme/', stub_view, name='customize_theme'),
    path('<int:federation_id>/generate-qr/', stub_view, name='generate_qr'),
    path('<int:federation_id>/manage-content/', stub_view, name='manage_content'),
    path('<int:federation_id>/roles/', stub_view, name='roles'),
    path('<int:federation_id>/upload-photos/', upload_photos, name='upload_photos'),
    path('<int:federation_id>/update-site-info/', update_site_info, name='update_site_info'),
]

