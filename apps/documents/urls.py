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
    path('document/<uuid:document_id>/', views.document_detail, name='detail'),
    path('download/<uuid:document_id>/', views.download_document, name='download'),
    
    # Mes documents et partages
    path('my-documents/', views.my_documents, name='my_documents'),
    path('shared-with-me/', views.shared_with_me, name='shared_with_me'),
    
    # Commentaires
    path('comment/<uuid:document_id>/', views.add_comment, name='add_comment'),
    
    # Vues spécifiques par rôle
    path('practitioner/', views.practitioner_documents, name='practitioner_documents'),
    path('judge/', views.judge_documents, name='judge_documents'),
    path('club/', views.club_documents, name='club_documents'),
]