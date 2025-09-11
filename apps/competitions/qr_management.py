"""
URLs pour la gestion des QR codes et des parrainages.
"""
from django.urls import path
from apps.competitions.views import qr_management

app_name = 'qr_management'

urlpatterns = [
    # Dashboard QR codes et parrainages
    path('', qr_management.dashboard_qr_management, name='dashboard'),
    
    # Gestion des QR codes
    path('create-qr-code/', qr_management.create_organization_qr_code, name='create_qr_code'),
    path('qr-code/<uuid:qr_code_id>/', qr_management.view_qr_code, name='view_qr_code'),
    path('qr-code/<uuid:qr_code_id>/regenerate/', qr_management.regenerate_qr_code, name='regenerate_qr_code'),
    path('qr-code/<uuid:qr_code_id>/deactivate/', qr_management.deactivate_qr_code, name='deactivate_qr_code'),
    path('qr-code/<uuid:qr_code_id>/reactivate/', qr_management.reactivate_qr_code, name='reactivate_qr_code'),
    path('qr-code/<uuid:qr_code_id>/download/', qr_management.download_qr_code, name='download_qr_code'),
    
    # Gestion des liens de parrainage
    path('create-referral-link/', qr_management.create_referral_link, name='create_referral_link'),
    path('referral-link/<uuid:referral_link_id>/', qr_management.view_referral_link, name='view_referral_link'),
    path('referral-link/<uuid:referral_link_id>/deactivate/', qr_management.deactivate_referral_link, name='deactivate_referral_link'),
    path('referral-link/<uuid:referral_link_id>/reactivate/', qr_management.reactivate_referral_link, name='reactivate_referral_link'),
]
