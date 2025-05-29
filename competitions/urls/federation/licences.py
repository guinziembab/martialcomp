from django.urls import path
# Importation avec les noms exacts des fonctions
from competitions.views.federation.licences import (
    licences_list,  # avec un 's'
    licence_create, # sans 's'
    licence_edit,   # sans 's', et 'edit' au lieu de 'update'
    licence_delete  # sans 's'
)

app_name = 'licences'

urlpatterns = [
    path('', licences_list, name='list'),
    path('create/', licence_create, name='create'),
    path('<int:licence_id>/edit/', licence_edit, name='edit'),  # notez 'edit' et non 'update'
    path('<int:licence_id>/delete/', licence_delete, name='delete'),
]