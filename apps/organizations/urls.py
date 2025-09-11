from django.urls import path
from . import views
from .views.api import OrganizationListView, OrganizationDashboardView, OrganizationJoinView
from .views.organization_creation import (
    create_organization_with_feedback,
    create_organization_ajax,
    organization_preview,
    organization_status,
    organization_qr_codes,
    organization_site_admin
)

app_name = 'organizations'

urlpatterns = [
    # URLs existantes
    path('', views.organization_list, name='list'),
    path('create/', views.organization_create, name='create'),
    path('<int:pk>/', views.organization_detail, name='detail'),
    path('<int:pk>/edit/', views.organization_edit, name='edit'),
    path('<int:pk>/delete/', views.organization_delete, name='delete'),
    
    # Nouvelles URLs pour la création améliorée
    path('create-with-feedback/', create_organization_with_feedback, name='create_with_feedback'),
    path('create-ajax/', create_organization_ajax, name='create_ajax'),
    path('preview/', organization_preview, name='preview'),
    path('<int:organization_id>/status/', organization_status, name='status'),
    path('<int:organization_id>/qr-codes/', organization_qr_codes, name='qr_codes'),
    path('<int:organization_id>/site-admin/', organization_site_admin, name='site_admin'),
    # API endpoints
    path('api/', OrganizationListView.as_view(), name='api_list'),
    path('api/dashboard/', OrganizationDashboardView.as_view(), name='api_dashboard'),
    path('api/<int:organization_id>/join/', OrganizationJoinView.as_view(), name='api_join'),
]