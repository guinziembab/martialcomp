"""
URLs pour les sites d'organisations en sous-domaine.
"""
from django.urls import path, include
from django.views.generic import RedirectView
from competitions.views.organization_sites import (
    organization_site_view,
    organization_register_view, 
    organization_qr_code_view,
    organization_admin_view,
    organization_contact_view,
    organization_check_in_view,
    create_organization_site,
    organization_site_status
)

app_name = 'organization_sites'

urlpatterns = [
    # Page d'accueil de l'organisation
    path('', organization_site_view, name='home'),
    
    # Inscription via le site de l'organisation
    path('signup/', organization_register_view, name='register'),
    path('inscription/', organization_register_view, name='register_fr'),  # Alias français
    
    # API QR codes
    path('qr/<str:qr_type>/', organization_qr_code_view, name='qr_code'),
    path('qr/', organization_qr_code_view, name='qr_code_default'),
    
    # Contact
    path('contact/', organization_contact_view, name='contact'),
    
    # Check-in pour les membres
    path('check-in/', organization_check_in_view, name='check_in'),
    path('pointage/', organization_check_in_view, name='check_in_fr'),  # Alias français
    
    # Administration du site (pour les propriétaires d'organisation)
    path('admin/site/', organization_admin_view, name='admin'),
    path('gestion/', organization_admin_view, name='admin_fr'),  # Alias français
    
    # API de statut
    path('api/status/', organization_site_status, name='status'),
    
    # Redirections courantes
    path('home/', RedirectView.as_view(pattern_name='organization_sites:home', permanent=True)),
    path('accueil/', RedirectView.as_view(pattern_name='organization_sites:home', permanent=True)),
    
    # Pages spécifiques par type d'organisation
    path('competitions/', organization_site_view, {'section': 'competitions'}, name='competitions'),
    path('cours/', organization_site_view, {'section': 'courses'}, name='courses'),
    path('services/', organization_site_view, {'section': 'services'}, name='services'),
    path('horaires/', organization_site_view, {'section': 'schedule'}, name='schedule'),
    path('instructeurs/', organization_site_view, {'section': 'instructors'}, name='instructors'),
    path('equipe/', organization_site_view, {'section': 'team'}, name='team'),
    path('actualites/', organization_site_view, {'section': 'news'}, name='news'),
    path('galerie/', organization_site_view, {'section': 'gallery'}, name='gallery'),
    
    # Création de site (pour les admins système)
    path('create-site/', create_organization_site, name='create_site'),
]

# URLs pour l'administration des sites (à inclure dans le projet principal)
admin_urlpatterns = [
    path('organizations/sites/', include([
        path('create/', create_organization_site, name='create_organization_site'),
        path('<int:organization_id>/status/', organization_site_status, name='organization_status'),
        path('<int:organization_id>/qr/<str:qr_type>/', organization_qr_code_view, name='organization_qr'),
    ])),
]