from django.urls import path, include

from competitions.views import (
    competition_list,
    competition_create,
    competition_detail,
    competition_update,
    competition_delete,
    manage_competition_registrations,
    register_for_competition,
    export_competition_registrations,
    competition_categories,
    get_competition_types,
    get_competition_types_by_discipline
)
from competitions.views.categories import (
    category_create,
    category_update,
    category_delete
)
from competitions.views import roles

app_name = 'competitions'

urlpatterns = [
    # URLs principales pour les compétitions
    path('', competition_list, name='list'),
    path('create/', competition_create, name='create'),
    path('<int:pk>/', competition_detail, name='detail'),
    path('<int:pk>/update/', competition_update, name='update'),
    path('<int:pk>/delete/', competition_delete, name='delete'),
    
    # URLs pour les catégories
    path('<int:competition_id>/categories/', 
         competition_categories,  
         name='categories'),
    
    path('<int:competition_id>/categories/create/<int:type_id>/', 
         category_create,  
         name='category_create'),
    
    path('categories/<int:pk>/update/', 
         category_update,  
         name='category_update'),
    
    path('categories/<int:category_id>/delete/', 
         category_delete,  
         name='category_delete'),
    
    # Gestion des inscriptions
    path('<int:competition_id>/registrations/', 
         manage_competition_registrations, 
         name='manage_registrations'),
    
    path('<int:competition_id>/register/', 
         register_for_competition, 
         name='register'),
         
    path('<int:competition_id>/export-registrations/', 
         export_competition_registrations, 
         name='export_registrations'),
    
    # APIs
    path('api/competition-types/', 
         get_competition_types, 
         name='api_competition_types'),
    
    path('api/discipline/<int:discipline_id>/types/', 
         get_competition_types_by_discipline, 
         name='discipline_competition_types'),
    
    # URLs pour la gestion des rôles
     path('club/roles/', roles.manage_roles, name='manage_roles'),
     path('club/roles/create/', roles.create_role, name='create_role'),
     path('club/roles/<int:role_id>/edit/', roles.edit_role, name='edit_role'),
     path('club/roles/<int:role_id>/delete/', roles.delete_role, name='delete_role'),
     path('club/roles/assign/', roles.assign_role, name='assign_role'),
     path('club/roles/revoke/<int:user_role_id>/', roles.revoke_role, name='revoke_role'),
     ]