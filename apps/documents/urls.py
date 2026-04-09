from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Dashboard principal
    path('', views.documents_dashboard, name='dashboard'),
    
    # Navigation dans les dossiers
    path('folder/', views.folder_view, name='folder_root'),
    path('folder/<uuid:folder_id>/', views.folder_view, name='folder_view'),
    
    # Gestion des documents
    path('upload/', views.upload_document, name='upload'),
    path('upload/<uuid:folder_id>/', views.upload_document, name='upload_to_folder'),
    path('upload-ajax/', views.upload_document_ajax, name='upload_ajax'),
    path('create-folder/', views.create_folder_ajax, name='create_folder_ajax'),
    path('document/<uuid:document_id>/', views.document_detail, name='detail'),
    path('download/<uuid:document_id>/', views.download_document, name='download'),
    
    # Mes documents et partages
    path('my-documents/', views.my_documents, name='my_documents'),
    path('shared-with-me/', views.shared_with_me, name='shared_with_me'),
    
    # Partage
    path('share/<uuid:document_id>/', views.share_document_ajax, name='share_document'),
    path('revoke-share/<uuid:share_id>/', views.revoke_share_ajax, name='revoke_share'),
    path('search-targets/', views.search_share_targets, name='search_share_targets'),

    # Commentaires
    path('comment/<uuid:document_id>/', views.add_comment, name='add_comment'),
    
    # Vues spécifiques par rôle
    path('practitioner/', views.practitioner_documents, name='practitioner_documents'),
    path('judge/', views.judge_documents, name='judge_documents'),
    path('club/', views.club_documents, name='club_documents'),
]