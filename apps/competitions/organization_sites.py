"""
URLs pour les sites d'organisations en sous-domaine.
"""
from django.urls import path, include
from django.views.generic import RedirectView
from apps.competitions.views.organization_sites import (
    organization_site_view,
    public_organization_site,
    public_organization_register_view,
    public_organization_qr_code_view,
    public_organization_admin_view,
    public_organization_payment_view,
    organization_register_view,
    organization_qr_code_view,
    organization_admin_view,
    organization_contact_view,
    organization_check_in_view,
    create_organization_site,
    organization_site_status,
    # API endpoints pour galerie et bannière
    api_upload_gallery_image,
    api_delete_gallery_image,
    api_update_gallery_description,
    api_upload_banner,
    api_delete_banner,
    # API pour le contenu du site
    api_update_site_content,
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

    # Fallback public routes by slug (when tenant middleware is disabled)
    path('org/<slug:slug>/', public_organization_site, name='public_site'),
    path('org/<slug:slug>/signup/', public_organization_register_view, name='public_signup'),
    path('org/<slug:slug>/qr/', public_organization_qr_code_view, name='public_qr_default'),
    path('org/<slug:slug>/qr/<str:qr_type>/', public_organization_qr_code_view, name='public_qr'),
    path('org/<slug:slug>/admin/site/', public_organization_admin_view, name='public_admin'),
    path('org/<slug:slug>/payment/', public_organization_payment_view, name='public_payment'),

    # API endpoints pour galerie et bannière
    path('org/<slug:slug>/api/gallery/upload/', api_upload_gallery_image, name='api_gallery_upload'),
    path('org/<slug:slug>/api/gallery/<int:image_id>/delete/', api_delete_gallery_image, name='api_gallery_delete'),
    path('org/<slug:slug>/api/gallery/<int:image_id>/description/', api_update_gallery_description, name='api_gallery_description'),
    path('org/<slug:slug>/api/banner/upload/', api_upload_banner, name='api_banner_upload'),
    path('org/<slug:slug>/api/banner/delete/', api_delete_banner, name='api_banner_delete'),
    # API pour le contenu du site
    path('org/<slug:slug>/api/content/update/', api_update_site_content, name='api_content_update'),
]

# URLs pour l'administration des sites (Ã  inclure dans le projet principal)
admin_urlpatterns = [
    path('organizations/sites/', include([
        path('create/', create_organization_site, name='create_organization_site'),
        path('<int:organization_id>/status/', organization_site_status, name='organization_status'),
        path('<int:organization_id>/qr/<str:qr_type>/', organization_qr_code_view, name='organization_qr'),
    ])),
]

