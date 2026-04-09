"""
URLs pour l'API Mobile MartialComp
==================================
"""

from django.urls import path
from .mobile_api import (
    # QR Scanner
    QRScanProcessView,
    QRScanHistoryView,
    QRPractitionerView,
    QROfflineTokenView,
    QRVerifyOfflineTokenView,
    QRSyncOfflineView,
    EventCheckInView,

    # Offline
    OfflineProfilesListView,
    OfflineSyncView,

    # Documents
    DocumentsListView,
    DocumentDetailView,
    DocumentCategoriesView,
    DocumentUploadView,
    DocumentDownloadView,
    DocumentDeleteView,

    # Training
    TrainingSessionsListView,
    TrainingCategoriesView,
    TrainingAttendanceView,

    # Communication
    CommunicationMessagesView,
    CommunicationAnnouncementsView,

    # Password Reset
    PasswordResetRequestView,

    # Practitioner CRUD
    MobilePractitionerFormOptionsView,
    MobilePractitionerListCreateView,
    MobilePractitionerDetailView,
    MobilePractitionerActivateAccountView,
    MobilePractitionerAssignRoleView,

    # Event Registration (Club Manager)
    MobileEventRegistrationOptionsView,
    MobileEventBulkRegistrationView,
    MobileEventRegistrationsListView,

    # Registration Category Management
    MobileRegistrationCategoriesView,
    MobileRegistrationUpdateCategoriesView,

    # Task Management
    MobileTaskBoardListView,
    MobileTaskBoardDetailView,
    MobileTaskMyTasksView,
    MobileTaskDetailView,
    MobileTaskCreateView,
    MobileTaskUpdateView,
    MobileTaskMoveView,
    MobileTaskCommentView,
    MobileTaskAssigneesView,

    # Practitioner Transfer
    MobilePractitionerTransferRequestView,
    MobileTransferRequestsListView,
    MobileTransferRequestApproveView,
    MobileTransferRequestRejectView,
)

app_name = 'mobile_api'

urlpatterns = [
    # ==========================================================================
    # QR Scanner Endpoints
    # ==========================================================================
    path('qr/scan/process/', QRScanProcessView.as_view(), name='qr_scan_process'),
    path('qr/scan/history/', QRScanHistoryView.as_view(), name='qr_scan_history'),
    path('qr/scan/sync-offline/', QRSyncOfflineView.as_view(), name='qr_sync_offline'),
    path('qr/scan/verify-offline-token/', QRVerifyOfflineTokenView.as_view(), name='qr_verify_offline_token'),

    # QR Practitioner endpoints
    path('qr/practitioner/<int:practitioner_id>/', QRPractitionerView.as_view(), name='qr_practitioner'),
    path('qr/practitioner/<int:practitioner_id>/offline-token/', QROfflineTokenView.as_view(), name='qr_offline_token'),

    # Event check-in
    path('qr/event/<int:event_id>/check-in/', EventCheckInView.as_view(), name='qr_event_checkin'),

    # ==========================================================================
    # Offline Endpoints
    # ==========================================================================
    path('offline/profiles/', OfflineProfilesListView.as_view(), name='offline_profiles'),
    path('offline/sync/', OfflineSyncView.as_view(), name='offline_sync'),

    # ==========================================================================
    # Documents Endpoints
    # ==========================================================================
    path('documents/', DocumentsListView.as_view(), name='documents_list'),
    path('documents/upload/', DocumentUploadView.as_view(), name='documents_upload'),
    path('documents/categories/', DocumentCategoriesView.as_view(), name='documents_categories'),
    path('documents/<uuid:document_id>/', DocumentDetailView.as_view(), name='documents_detail'),
    path('documents/<uuid:document_id>/download/', DocumentDownloadView.as_view(), name='documents_download'),
    path('documents/<uuid:document_id>/delete/', DocumentDeleteView.as_view(), name='documents_delete'),

    # ==========================================================================
    # Training Endpoints
    # ==========================================================================
    path(
        'training/sessions/',
        TrainingSessionsListView.as_view(),
        name='training_sessions'
    ),
    path(
        'training/categories/',
        TrainingCategoriesView.as_view(),
        name='training_categories'
    ),
    path(
        'training/attendance/',
        TrainingAttendanceView.as_view(),
        name='training_attendance'
    ),

    # ==========================================================================
    # Communication Endpoints
    # ==========================================================================
    path('communication/messages/', CommunicationMessagesView.as_view(), name='communication_messages'),
    path('communication/announcements/', CommunicationAnnouncementsView.as_view(), name='communication_announcements'),

    # ==========================================================================
    # Practitioner CRUD Endpoints (Mobile)
    # ==========================================================================
    path(
        'v1/mobile/practitioners/form-options/',
        MobilePractitionerFormOptionsView.as_view(),
        name='mobile_practitioners_form_options'
    ),
    path(
        'v1/mobile/practitioners/',
        MobilePractitionerListCreateView.as_view(),
        name='mobile_practitioners_list'
    ),
    path(
        'v1/mobile/practitioners/<int:practitioner_id>/',
        MobilePractitionerDetailView.as_view(),
        name='mobile_practitioner_detail'
    ),
    path(
        'v1/mobile/practitioners/<int:practitioner_id>/activate-account/',
        MobilePractitionerActivateAccountView.as_view(),
        name='mobile_practitioner_activate_account'
    ),
    path(
        'v1/mobile/practitioners/<int:practitioner_id>/assign-role/',
        MobilePractitionerAssignRoleView.as_view(),
        name='mobile_practitioner_assign_role'
    ),

    # ==========================================================================
    # Event Registration Endpoints (Club Manager Bulk Registration)
    # ==========================================================================
    path(
        'v1/mobile/events/<int:event_id>/registration-options/',
        MobileEventRegistrationOptionsView.as_view(),
        name='mobile_event_registration_options'
    ),
    path(
        'v1/mobile/events/<int:event_id>/register-practitioners/',
        MobileEventBulkRegistrationView.as_view(),
        name='mobile_event_bulk_registration'
    ),
    path(
        'v1/mobile/events/<int:event_id>/registrations/',
        MobileEventRegistrationsListView.as_view(),
        name='mobile_event_registrations_list'
    ),

    # Registration Category Management
    path(
        'v1/mobile/events/<int:event_id>/registrations/<int:registration_id>/categories/',
        MobileRegistrationCategoriesView.as_view(),
        name='mobile_registration_categories'
    ),
    path(
        'v1/mobile/events/<int:event_id>/registrations/<int:registration_id>/update-categories/',
        MobileRegistrationUpdateCategoriesView.as_view(),
        name='mobile_registration_update_categories'
    ),

    # ==========================================================================
    # Task Management Endpoints (Mobile)
    # ==========================================================================
    path(
        'v1/mobile/tasks/boards/',
        MobileTaskBoardListView.as_view(),
        name='mobile_task_boards'
    ),
    path(
        'v1/mobile/tasks/boards/<int:board_id>/',
        MobileTaskBoardDetailView.as_view(),
        name='mobile_task_board_detail'
    ),
    path(
        'v1/mobile/tasks/my-tasks/',
        MobileTaskMyTasksView.as_view(),
        name='mobile_my_tasks'
    ),
    path(
        'v1/mobile/tasks/<int:task_id>/',
        MobileTaskDetailView.as_view(),
        name='mobile_task_detail'
    ),
    path(
        'v1/mobile/tasks/create/',
        MobileTaskCreateView.as_view(),
        name='mobile_task_create'
    ),
    path(
        'v1/mobile/tasks/<int:task_id>/update/',
        MobileTaskUpdateView.as_view(),
        name='mobile_task_update'
    ),
    path(
        'v1/mobile/tasks/<int:task_id>/move/',
        MobileTaskMoveView.as_view(),
        name='mobile_task_move'
    ),
    path(
        'v1/mobile/tasks/<int:task_id>/comment/',
        MobileTaskCommentView.as_view(),
        name='mobile_task_comment'
    ),
    path(
        'v1/mobile/tasks/<int:task_id>/assignees/',
        MobileTaskAssigneesView.as_view(),
        name='mobile_task_assignees'
    ),
    # ==========================================================================
    # Practitioner Transfer Endpoints
    # ==========================================================================
    path(
        'v1/mobile/practitioners/<int:practitioner_id>/request-transfer/',
        MobilePractitionerTransferRequestView.as_view(),
        name='mobile_practitioner_request_transfer'
    ),
    path(
        'v1/mobile/transfer-requests/',
        MobileTransferRequestsListView.as_view(),
        name='mobile_transfer_requests_list'
    ),
    path(
        'v1/mobile/transfer-requests/<int:transfer_id>/approve/',
        MobileTransferRequestApproveView.as_view(),
        name='mobile_transfer_request_approve'
    ),
    path(
        'v1/mobile/transfer-requests/<int:transfer_id>/reject/',
        MobileTransferRequestRejectView.as_view(),
        name='mobile_transfer_request_reject'
    ),
]

# Password reset dans api_auth
password_reset_urlpatterns = [
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_mobile'),
]
