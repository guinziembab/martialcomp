"""
Configuration des URLs pour MartialComp
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from apps.competitions.views.custom_set_language import custom_set_language
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect

# Import des vues principales
from apps.competitions.views.welcome import welcome
from apps.competitions.views.custom_login import custom_login_view
from apps.competitions.views.ajax_login import ajax_login_view
from apps.competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view, contact_view, contact_ajax_view
from apps.competitions.views.competitions import competition_detail

# Import de la vue d'inscription personnalisÃ©e pour django-allauth
from apps.competitions.views.allauth_override import CustomSignupView

# Import des vues DeepL
from config.rosetta_views import DeepLTranslationView, deepl_status, batch_translate

# Import de la vue protÃ©gÃ©e pour le profil
from apps.competitions.views.auth import profile_view, manage_organization_disciplines_view, sso_login_view

# Import de la vue de debug
from config.views import debug_host
# Import du webhook Stripe (hors i18n_patterns)
from apps.finances.views.stripe_views import stripe_webhook
from apps.competitions.views.organization_sites import (
    public_organization_site,
    public_organization_register_view,
    public_organization_referral_view,
    public_organization_qr_code_view,
    public_organization_admin_view,
    public_organization_payment_view,
    public_organization_shop_view,
    # API endpoints pour galerie et bannière
    api_upload_gallery_image,
    api_delete_gallery_image,
    api_update_gallery_description,
    api_upload_banner,
    api_delete_banner,
    # API endpoints pour vidéos YouTube
    api_add_video_link,
    api_delete_video_link,
    api_update_video_link,
    # API endpoint pour personnalisation (couleurs, description, etc.)
    api_customize_organization,
    # API endpoints pour les actualités (news)
    api_get_news,
    api_create_news,
    api_update_news,
    api_delete_news,
    api_toggle_news_publish,
)


# URLs principales (sans prÃ©fixe de langue)
urlpatterns = [
    # URLs d'authentification - notre login en prioritÃ©, puis allauth
    path('accounts/login/', custom_login_view, name='account_login'),
    path('ajax/login/', ajax_login_view, name='ajax_login'),
    
    # IMPORTANT: Override de la vue d'inscription de django-allauth
    # Cela doit Ãªtre placÃ© AVANT l'inclusion de allauth.urls
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    
    # Inclusion des URLs de django-allauth
    path('accounts/', include('allauth.urls')),
    
    # URLs d'authentification Django standard
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    
    # Changement de langue - utilise la vue custom avec meilleure gestion
    path('set_language/', custom_set_language, name='set_language'),
    
    # Redirection de l'admin sans préfixe vers l'admin avec préfixe
    path('admin/', lambda request: redirect('/fr/admin/')),
    path('admin/<path:path>', lambda request, path: redirect(f'/fr/admin/{path}')),

    # URL de debug
    path('debug-host/', debug_host),

    # Public organization site fallback (no language prefix)
    path('org/<slug:slug>/', public_organization_site, name='public_org_site'),
    path('org/<slug:slug>/signup/', public_organization_register_view, name='public_org_signup'),
    path('org/<slug:slug>/qr/', public_organization_qr_code_view, name='public_org_qr_default'),
    path('org/<slug:slug>/qr/<str:qr_type>/', public_organization_qr_code_view, name='public_org_qr'),
    path('org/<slug:slug>/admin/site/', public_organization_admin_view, name='public_org_admin'),
    path('org/<slug:slug>/payment/', public_organization_payment_view, name='public_org_payment'),
    path('org/<slug:slug>/shop/', public_organization_shop_view, name='public_org_shop'),
    path('org/<slug:slug>/referral/', public_organization_referral_view, name='public_org_referral'),

    # API endpoints pour galerie et bannière (sans préfixe de langue)
    path('org/<slug:slug>/api/gallery/upload/', api_upload_gallery_image, name='api_org_gallery_upload'),
    path('org/<slug:slug>/api/gallery/<int:image_id>/delete/', api_delete_gallery_image, name='api_org_gallery_delete'),
    path('org/<slug:slug>/api/gallery/<int:image_id>/description/', api_update_gallery_description, name='api_org_gallery_description'),
    path('org/<slug:slug>/api/banner/upload/', api_upload_banner, name='api_org_banner_upload'),
    path('org/<slug:slug>/api/banner/delete/', api_delete_banner, name='api_org_banner_delete'),

    # API endpoints pour vidéos YouTube
    path('org/<slug:slug>/api/videos/add/', api_add_video_link, name='api_org_video_add'),
    path('org/<slug:slug>/api/videos/<int:video_id>/delete/', api_delete_video_link, name='api_org_video_delete'),
    path('org/<slug:slug>/api/videos/<int:video_id>/update/', api_update_video_link, name='api_org_video_update'),

    # API endpoints pour les actualités (news)
    path('org/<slug:slug>/api/news/<int:news_id>/', api_get_news, name='api_org_news_get'),
    path('org/<slug:slug>/api/news/create/', api_create_news, name='api_org_news_create'),
    path('org/<slug:slug>/api/news/<int:news_id>/update/', api_update_news, name='api_org_news_update'),
    path('org/<slug:slug>/api/news/<int:news_id>/delete/', api_delete_news, name='api_org_news_delete'),
    path('org/<slug:slug>/api/news/<int:news_id>/toggle-publish/', api_toggle_news_publish, name='api_org_news_toggle'),

    # API endpoint pour personnalisation complète (couleurs, description, modules)
    path('api/organizations/<int:organization_id>/customize/', api_customize_organization, name='api_org_customize'),

    # Lien de partage public pour les compétitions (sans préfixe de langue)
    # Permet l'accès public aux compétitions publiées
    path('competitions/<int:pk>/', competition_detail, name='public_competition_share'),

    # URL courte pour QR code de compétition
    path('c/<int:pk>/', competition_detail, name='short_competition_link'),

    # SSO Login (mobile -> web) - sans préfixe de langue pour fonctionner depuis l'app mobile
    path('sso/login/', sso_login_view, name='sso_login'),

    # Page upgrade (hors i18n pour URL stable référencée par les décorateurs)
    path('upgrade/', __import__('apps.finances.views.upgrade', fromlist=['upgrade_required_view']).upgrade_required_view, name='upgrade_required'),

    # Stripe webhook (hors i18n pour URL stable sans préfixe de langue)
    path('finances/stripe/webhook/', stripe_webhook, name='stripe_webhook'),

    # Password reset confirmation (lien envoyé par email depuis l'API mobile)
    path('reset-password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='account/api_password_reset_confirm.html',
        success_url='/reset-password/done/',
    ), name='api_password_reset_confirm'),
    path('reset-password/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_from_key_done.html',
    ), name='api_password_reset_complete'),

    # API root (no language prefix)
    path('api/', include('api.urls')),
    # Aliases versionnés pour mobile (compat)
    path('api/v1/auth/', include('api_auth.urls', namespace='api_auth')),
    # API Combat V3 - IMPORTANT: Placer après api.urls pour éviter les conflits
    # Les URLs de combat_api_urls commencent par 'combat/', donc pas de conflit
    path('api/', include('apps.competitions.combat_api_urls')),
]

# URLs avec prÃ©fixe de langue (fr/, en/, es/, etc.)
urlpatterns += i18n_patterns(

    # Accès direct dashboard anti-scroll (PRIORITÉ)
    path('dashboard/antiscroll/', lambda request: redirect('competitions:dashboard:club_anti_scroll', permanent=False)),
    
    # Application competitions (avec URLs d'onboarding)
    path('competitions/', include('apps.competitions.urls', namespace='competitions')),
    # DeepL Translation API endpoints (AVANT admin pour Ã©viter conflicts)
    path('admin/deepl/translate/', DeepLTranslationView.as_view(), name='deepl_translate_api'),
    path('admin/deepl/status/', deepl_status, name='deepl_status'),
    path('admin/deepl/batch/', batch_translate, name='batch_translate'),
    
    # Admin Django (avec prÃ©fixe de langue)
    path('admin/', admin.site.urls),

    # Super Admin (interface avancée)
    path('superadmin/', include('apps.superadmin.urls')),
    
    # Page d'accueil
    path('', welcome, name='welcome'),
    
    # Pages lÃ©gales
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_of_service_view, name='terms_of_service'),

    # Contact
    path('contact/', contact_view, name='contact'),
    path('contact/ajax/', contact_ajax_view, name='contact_ajax'),
    
    # Gestion de compte
    path('account/delete/', delete_account_view, name='delete_account'),
    path('profile/', profile_view, name='profile'),
    path('profile/manage-disciplines/', manage_organization_disciplines_view, name='manage_organization_disciplines'),
    
    # Page de connexion Django standard (corrige le 404 sur /fr/login/)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # =========================================================
    # APPLICATIONS PRINCIPALES - TOUTES LES URLS NÃ‰CESSAIRES
    # =========================================================
    
    # Application principale competitions (inclut le dashboard club)
    path('competitions/api/', include('apps.competitions.api')),
    
    # Accès direct au dashboard anti-scroll (placé avant competitions/ pour priorité)
    path('dashboard-antiscroll/', lambda request: redirect('/fr/competitions/dashboard/club/anti-scroll/', permanent=False)),
    
    
    # =========================================================
    # APPLICATIONS DASHBOARD CLUB - LIENS CASSÃ‰S CORRIGÃ‰S
    # =========================================================
    
    # Gestion des grades (ceintures, niveaux)
    path('grades/', include('apps.grades.urls')),
    
    # Gestion financiÃ¨re du club
    path('finances/', include('apps.finances.urls')),
    
    # Boutique/Shop du club
    path('shop/', include('apps.shop.urls')),
    
    # Gestion des documents
    path('documents/', include('apps.documents.urls')),
    
    # Gestion des tâches Kanban
    path('task-management/', include('apps.task_management.urls')),
    
    # Système d'adhésion MartialComp v2.0 (NOUVEAU)
    path('membership/', include('apps.membership.urls')),
    
    # =========================================================
    # APPLICATIONS SUPPLÃ‰MENTAIRES OPTIONNELLES
    # =========================================================
    
    # Gestion des organisations/fÃ©dÃ©rations
    path('organizations/', include('apps.organizations.urls')),
    
    # SystÃ¨me de permissions avancÃ©es
    path('permissions/', include('apps.permissions_manager.urls')),
    
    # Sites d'organisations (sous-domaines)
    path('', include('apps.competitions.organization_sites')),
    
    # Support multi-tenant (si utilisÃ©)
    # path('tenant/', include('apps.multitenant.urls')),
    
    # Gestion familiale
    path('family_management/', include('apps.family_management.urls')),

    # SystÃ¨me de paiement et abonnements
    path('payment/', include('apps.payment.urls')),

    # Système de messagerie interne (Chat) - désactivé si non déployé
    # path('chat/', include('apps.chat.urls', namespace='chat')),

    # Inclure le module d'administration des organisations
    path('admin/organizations/', include('apps.competitions.organization_admin')),
    
    prefix_default_language=True,
)

# Servir les fichiers media en dÃ©veloppement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Ajouter les URLs de Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

# Interface de traduction Rosetta (conditionnel - seulement si installé)
try:
    import rosetta
    urlpatterns += [
        path('rosetta/', include('rosetta.urls')),
    ]
except ImportError:
    pass

# Configuration pour les erreurs (dÃ©sactivÃ©e car les vues n'existent pas)
# handler404 = 'competitions.views.pages.custom_404'
# handler500 = 'competitions.views.pages.custom_500'

