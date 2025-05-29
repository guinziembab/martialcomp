from django.urls import path
from ..views import qr_scanner as views
from ..views import qr_management

app_name = 'qr'

urlpatterns = [
    # Scan d'un QR code organisation
    path('organization/<str:qr_code>/', qr_management.scan_qr_code, name='scan_organization_qr'),
    # Interface de scan
    path('scan/', views.scan_practitioner_qr, name='scan'),
    path('scan/process/', views.process_qr_scan, name='process_scan'),
    
    # Visualisation QR code
    path('practitioner/<int:practitioner_id>/', views.view_practitioner_qr, name='view_qr'),
    path('practitioner/<int:practitioner_id>/image/', views.qr_code_image, name='qr_image'),
    
    # Historique
    path('history/', views.scan_history, name='history'),
    
    # Validation fédération
    path('practitioner/<int:practitioner_id>/validate/', views.validate_federation_qr, name='validate_federation'),
    
    # QR code événement
    path('event/<int:event_id>/check-in/', views.generate_event_check_in_qr, name='event_check_in'),
    
    # Support hors-ligne
    path('practitioner/<int:practitioner_id>/offline-token/', views.qr_code_offline_token, name='offline_token'),
    path('scan/verify-offline-token/', views.verify_offline_token, name='verify_offline_token'),
    path('scan/process-offline/', views.process_offline_scan, name='process_offline_scan'),
    path('scan/sync-offline/', views.sync_offline_scans, name='sync_offline_scans'),
    
    # Support pour profil hors-ligne
    path('practitioner/<int:practitioner_id>/offline-profile/', views.qr_code_offline_profile, name='offline_profile'),
    path('scan/verify-offline-profile/', views.verify_offline_profile, name='verify_offline_profile'),
    path('profile/offline/', views.view_offline_profile_public, name='view_offline_profile'),
    path('profile/offline/<str:token>/', views.view_offline_profile_public, name='view_offline_profile_with_token'),
    
    # Mobile-friendly URLs
    path('mobile/<int:practitioner_id>/', views.view_practitioner_qr, name='mobile_qr'),
]