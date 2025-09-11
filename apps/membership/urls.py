# -*- coding: utf-8 -*-
"""
URLs pour le système d'adhésion MartialComp v2.0
"""
from django.urls import path, include
from . import views

app_name = 'membership'

urlpatterns = [
    # Dashboard adhésions
    path('', views.membership_dashboard, name='dashboard'),
    
    # Gestion des packages
    path('packages/', views.package_list, name='package_list'),
    path('packages/create/', views.package_create, name='package_create'),
    path('packages/<uuid:pk>/edit/', views.package_edit, name='package_edit'),
    path('packages/<uuid:pk>/delete/', views.package_delete, name='package_delete'),
    
    # Gestion des souscriptions
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/create/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<uuid:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<uuid:pk>/edit/', views.subscription_edit, name='subscription_edit'),
    path('subscriptions/<uuid:pk>/renew/', views.subscription_renew, name='subscription_renew'),
    path('subscriptions/<uuid:pk>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    
    # Formulaires en ligne
    path('forms/', views.form_list, name='form_list'),
    path('forms/create/', views.form_create, name='form_create'),
    path('forms/<uuid:pk>/edit/', views.form_edit, name='form_edit'),
    path('forms/<str:slug>/', views.public_form, name='public_form'),
    path('forms/<str:slug>/submit/', views.form_submit, name='form_submit'),
    
    # Soumissions de formulaires
    path('submissions/', views.submission_list, name='submission_list'),
    path('submissions/<uuid:pk>/', views.submission_detail, name='submission_detail'),
    path('submissions/<uuid:pk>/process/', views.submission_process, name='submission_process'),
    
    # Workflows
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/create/', views.workflow_create, name='workflow_create'),
    path('workflows/<uuid:pk>/edit/', views.workflow_edit, name='workflow_edit'),
    path('workflows/<uuid:pk>/test/', views.workflow_test, name='workflow_test'),
    
    # Alertes
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/<uuid:pk>/resolve/', views.alert_resolve, name='alert_resolve'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('analytics/export/', views.analytics_export, name='analytics_export'),
    
    # API endpoints (à implémenter plus tard)
    # path('api/', include('apps.membership.api.urls')),
]