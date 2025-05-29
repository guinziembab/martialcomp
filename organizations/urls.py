from django.urls import path
from .views import (
    # Vues d'organisations
    OrganizationListView,
    OrganizationDetailView,
    OrganizationCreateView,
    OrganizationUpdateView,
    OrganizationDeleteView,
    
    # Vues d'affiliations
    AffiliationCreateView,
    AffiliationUpdateView,
    delete_affiliation,
    
    # Vues de membres
    OrganizationMemberListView,
    OrganizationMemberCreateView,
    OrganizationMemberUpdateView,
    delete_member,
    transfer_ownership,
    
    # Vues d'API
    api_get_organizations,
    api_get_user_organizations,
    
    # Vue de tableau de bord
    organization_dashboard
)

app_name = 'organizations'

urlpatterns = [
    # URLs pour les organisations
    path('', OrganizationListView.as_view(), name='list'),
    path('create/', OrganizationCreateView.as_view(), name='create'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', OrganizationUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', OrganizationDeleteView.as_view(), name='delete'),
    
    # URLs pour les affiliations
    path('<int:organization_id>/add-parent-affiliation/', 
         AffiliationCreateView.as_view(), 
         kwargs={'direction': 'parent'},
         name='add_parent_affiliation'),
    path('<int:organization_id>/add-child-affiliation/', 
         AffiliationCreateView.as_view(), 
         kwargs={'direction': 'child'},
         name='add_child_affiliation'),
    path('affiliation/<int:pk>/update/',
         AffiliationUpdateView.as_view(),
         name='update_affiliation'),
    path('affiliation/<int:pk>/delete/',
         delete_affiliation,  # Fonction au lieu de vue basée sur classe
         name='delete_affiliation'),
    
    # URLs pour les membres
    path('<int:organization_id>/members/', 
         OrganizationMemberListView.as_view(), 
         name='members'),
    path('<int:organization_id>/members/add/', 
         OrganizationMemberCreateView.as_view(), 
         name='add_member'),
    path('member/<int:pk>/update/',
         OrganizationMemberUpdateView.as_view(),
         name='update_member'),
    path('member/<int:pk>/delete/',
         delete_member,  # Fonction au lieu de vue basée sur classe
         name='delete_member'),
    
    # API URLs 
    path('api/organizations/', api_get_organizations, name='api_organizations'),
    path('api/user-organizations/', api_get_user_organizations, name='api_user_organizations'),
    
    # URL pour le tableau de bord
    path('dashboard/', organization_dashboard, name='dashboard'),
    
    # URL pour le transfert de propriété
    path('member/<int:pk>/transfer-ownership/', 
         transfer_ownership, 
         name='transfer_ownership'),
]