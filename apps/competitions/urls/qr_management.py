from django.urls import path
from apps.competitions.views.qr_management import (
    dashboard_qr_management,
    create_organization_qr_code,
    view_qr_code,
    download_qr_code,
    create_referral_link,
    view_referral_link
)

app_name = 'qr_management'

urlpatterns = [
    path('', dashboard_qr_management, name='dashboard'),
    path('create/', create_organization_qr_code, name='create_qr_code'),
    path('view/<int:qr_code_id>/', view_qr_code, name='view_qr_code'),
    path('download/<int:qr_code_id>/', download_qr_code, name='download_qr_code'),
    path('referral/create/', create_referral_link, name='create_referral_link'),
    path('referral/view/<int:referral_link_id>/', view_referral_link, name='view_referral_link'),
]
