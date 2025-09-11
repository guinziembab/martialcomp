from django.urls import path
from apps.competitions.views.qr_scanner import (
    scan_practitioner_qr, 
    scan_history, 
    mark_attendance_ajax, 
    process_qr_scan,
    view_qr,
    qr_code_image
)

app_name = 'qr'

urlpatterns = [
    # Scanner QR Code
    path('scan/', scan_practitioner_qr, name='scan'),
    
    # Historique des scans
    path('history/', scan_history, name='history'),
    
    # Marquer la présence via AJAX
    path('mark-attendance/', mark_attendance_ajax, name='mark_attendance_ajax'),
    
    # Traiter un scan QR
    path('process-scan/', process_qr_scan, name='process_scan'),
    
    # Voir le QR code d'un pratiquant
    path('view/<int:practitioner_id>/', view_qr, name='view_qr'),
    
    # Image du QR code
    path('image/<int:practitioner_id>/', qr_code_image, name='qr_image'),
]

