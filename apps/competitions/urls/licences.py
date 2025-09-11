from django.urls import path
from apps.competitions.views.federation import licences

app_name = 'licences'

urlpatterns = [
    # Liste des licences
    path('<int:federation_id>/', licences.licences_list, name='list'),
    path('<int:federation_id>/list/', licences.licences_list, name='licence_list'),
    
    # Création d'une nouvelle licence
    path('<int:federation_id>/create/', licences.licence_create, name='create'),
    path('<int:federation_id>/new/', licences.licence_create, name='licence_create'),
    
    # Modification d'une licence
    path('<int:federation_id>/<int:licence_id>/edit/', licences.licence_edit, name='edit'),
    path('<int:federation_id>/<int:licence_id>/update/', licences.licence_edit, name='licence_edit'),
    
    # Suppression d'une licence
    path('<int:federation_id>/<int:licence_id>/delete/', licences.licence_delete, name='delete'),
    path('<int:federation_id>/<int:licence_id>/remove/', licences.licence_delete, name='licence_delete'),
]