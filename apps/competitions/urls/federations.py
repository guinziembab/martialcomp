# apps/competitions/urls/federations.py
from django.urls import path
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from ..views.dashboard import federations
from ..views.dashboard import federation_seasons
from ..views.dashboard import certification_management
from ..views.dashboard import federation_site_management
from ..views.competitions import competition_create

# Vues stub pour les URLs manquantes (fonctionnalites avancees)
@login_required
def stub_view(request, federation_id):
    """Vue temporaire pour les fonctionnalites en developpement"""
    messages.info(request, _("Cette fonctionnalite sera bientot disponible."))
    return redirect('competitions:dashboard:federation', federation_id=federation_id)

app_name = 'federations'

urlpatterns = [
    # Dashboard principal
    path('<int:federation_id>/dashboard/', federations.federation_dashboard, name='federation_dashboard'),

    # Vues fonctionnelles (Actions rapides) - version simplifiee
    path('<int:federation_id>/clubs/', federations.federation_manage_clubs, name='clubs'),
    path('<int:federation_id>/competitions/', federations.federation_manage_competitions, name='competitions'),
    path('<int:federation_id>/judges/', federations.federation_manage_judges, name='judges'),
    path('<int:federation_id>/settings/', federations.federation_manage_settings, name='settings'),
    path('<int:federation_id>/reports/', federations.federation_manage_reports, name='reports'),
    path('<int:federation_id>/grades/', federations.federation_manage_grades, name='grades'),

    # Export CSV - Rapports
    path('<int:federation_id>/export/clubs/', federations.export_clubs_csv, name='export_clubs_csv'),
    path('<int:federation_id>/export/practitioners/', federations.export_practitioners_csv, name='export_practitioners_csv'),
    path('<int:federation_id>/export/competitions/', federations.export_competitions_csv, name='export_competitions_csv'),
    path('<int:federation_id>/export/results/', federations.export_results_csv, name='export_results_csv'),
    path('<int:federation_id>/export/judges/', federations.export_judges_csv, name='export_judges_csv'),
    path('<int:federation_id>/export/certificates/', federations.export_certificates_csv, name='export_certificates_csv'),

    # Creation de competition - utilise la vue existante avec federation_id
    path('<int:federation_id>/create-competition/', competition_create, name='create_competition'),

    # Vues stub (fonctionnalites avancees en developpement)
    path('<int:federation_id>/calendar/', stub_view, name='calendar'),
    path('<int:federation_id>/certifications/',
         federations.federation_manage_certifications, name='certifications'),

    # Gestion avancée des certifications - Modèles de certificats
    path('<int:federation_id>/certifications/templates/',
         certification_management.certificate_templates_list,
         name='certificate_templates'),
    path('<int:federation_id>/certifications/templates/create/',
         certification_management.certificate_template_create,
         name='certificate_template_create'),
    path('<int:federation_id>/certifications/templates/<int:template_id>/edit/',
         certification_management.certificate_template_edit,
         name='certificate_template_edit'),
    path('<int:federation_id>/certifications/templates/<int:template_id>/delete/',
         certification_management.certificate_template_delete,
         name='certificate_template_delete'),

    # Demandes de certification
    path('<int:federation_id>/certifications/requests/',
         certification_management.certification_requests_list,
         name='certification_requests'),
    path('<int:federation_id>/certifications/requests/<int:request_id>/',
         certification_management.certification_request_detail,
         name='certification_request_detail'),
    path('<int:federation_id>/certifications/requests/<int:request_id>/process/',
         certification_management.certification_request_process,
         name='certification_request_process'),

    # Certificats émis
    path('<int:federation_id>/certifications/issued/',
         certification_management.issued_certificates_list,
         name='issued_certificates'),
    path('<int:federation_id>/certifications/issue/',
         certification_management.issue_certificate,
         name='issue_certificate'),
    path('<int:federation_id>/certifications/issued/<int:certificate_id>/',
         certification_management.certificate_detail,
         name='certificate_detail'),
    path('<int:federation_id>/certifications/issued/<int:certificate_id>/action/',
         certification_management.certificate_action,
         name='certificate_action'),
    path('<int:federation_id>/certifications/issued/<int:certificate_id>/pdf/',
         certification_management.certificate_download_pdf,
         name='certificate_download_pdf'),

    # Examens de certification
    path('<int:federation_id>/examens/',
         certification_management.exams_list, name='examens'),
    path('<int:federation_id>/examens/create/',
         certification_management.exam_create, name='exam_create'),
    path('<int:federation_id>/examens/<int:exam_id>/',
         certification_management.exam_detail, name='exam_detail'),
    path('<int:federation_id>/examens/<int:exam_id>/edit/',
         certification_management.exam_edit, name='exam_edit'),
    path('<int:federation_id>/examens/<int:exam_id>/registrations/<int:registration_id>/action/',
         certification_management.exam_registration_action,
         name='exam_registration_action'),
    path('<int:federation_id>/import-export/', stub_view, name='import_export'),
    path('<int:federation_id>/customize-theme/', federation_site_management.customize_theme, name='customize_theme'),
    path('<int:federation_id>/generate-qr/', federation_site_management.generate_qr, name='generate_qr'),
    path('<int:federation_id>/manage-content/', federation_site_management.manage_content, name='manage_content'),
    path('<int:federation_id>/roles/', stub_view, name='roles'),
    path('<int:federation_id>/upload-photos/', federation_site_management.upload_photos, name='upload_photos'),
    path('<int:federation_id>/update-site-info/', federation_site_management.update_site_info, name='update_site_info'),
    path('<int:federation_id>/site-analytics/', federation_site_management.site_analytics, name='site_analytics'),

    # Gestion des actualites / news
    path('<int:federation_id>/news/', federation_site_management.manage_news, name='manage_news'),
    path('<int:federation_id>/news/create/', federation_site_management.create_news, name='create_news'),
    path('<int:federation_id>/news/<int:news_id>/edit/', federation_site_management.edit_news, name='edit_news'),
    path('<int:federation_id>/news/<int:news_id>/delete/', federation_site_management.delete_news, name='delete_news'),
    path('<int:federation_id>/news/<int:news_id>/toggle-publish/', federation_site_management.toggle_news_publish, name='toggle_news_publish'),

    # Gestion des saisons sportives
    path('<int:federation_id>/seasons/', federation_seasons.manage_seasons, name='seasons'),
    path('<int:federation_id>/seasons/create/', federation_seasons.create_season, name='create_season'),
    path('<int:federation_id>/seasons/<int:season_id>/edit/', federation_seasons.edit_season, name='edit_season'),
    path('<int:federation_id>/seasons/<int:season_id>/fees/', federation_seasons.manage_fees, name='manage_fees'),

    # Demandes de renouvellement d'affiliation
    path('<int:federation_id>/renewal-requests/', federation_seasons.renewal_requests, name='renewal_requests'),
    path('<int:federation_id>/renewal-requests/<int:request_id>/process/', federation_seasons.process_renewal_request, name='process_renewal_request'),

    # Factures d'affiliation
    path('<int:federation_id>/affiliation-invoices/', federation_seasons.affiliation_invoices, name='affiliation_invoices'),
    path('<int:federation_id>/affiliation-invoices/<int:period_id>/generate/', federation_seasons.generate_invoice, name='generate_invoice'),
    path('<int:federation_id>/affiliation-invoices/<int:period_id>/payment/', federation_seasons.record_affiliation_payment, name='record_payment'),

    # Historique des périodes d'affiliation par club
    path('<int:federation_id>/affiliations/<int:affiliation_id>/periods/', federation_seasons.affiliation_periods, name='affiliation_periods'),

    # Gestion des entraînements fédération
    path('<int:federation_id>/training/programs/', federations.federation_training_programs, name='training_programs'),
    path('<int:federation_id>/training/programs/create/', federations.federation_create_training_program, name='create_training_program'),
    path('<int:federation_id>/training/sessions/', federations.federation_training_sessions, name='training_sessions'),
    path('<int:federation_id>/training/sessions/create/', federations.federation_create_training_session, name='create_training_session'),
    path('<int:federation_id>/training/slots/', federations.federation_training_slots, name='training_slots'),
    path('<int:federation_id>/training/slots/create/', federations.federation_create_training_slot, name='create_training_slot'),
]
