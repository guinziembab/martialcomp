# permissions_manager/urls.py

from django.urls import path
from . import views

app_name = 'permissions_manager'

urlpatterns = [
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/', views.role_detail, name='role_detail'),
    path('roles/<int:pk>/edit/', views.role_update, name='role_update'),
    path('roles/<int:pk>/delete/', views.role_delete, name='role_delete'),
    
    path('user-roles/', views.user_role_list, name='user_role_list'),
    path('user-roles/create/', views.user_role_create, name='user_role_create'),
    path('user-roles/<int:pk>/edit/', views.user_role_update, name='user_role_update'),
    path('user-roles/<int:pk>/delete/', views.user_role_delete, name='user_role_delete'),
    
    # URLs pour l'administration avancée (optionnel)
    path('entity-roles/<str:content_type>/<int:object_id>/', views.entity_roles, name='entity_roles'),
    path('user/<int:user_id>/roles/', views.user_roles, name='user_roles'),
]