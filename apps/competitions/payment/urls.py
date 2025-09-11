from django.urls import path, include
from django.views.generic import TemplateView

from . import views

app_name = 'payment'

urlpatterns = [
    # Tableau de bord et configuration
    path('dashboard/', views.payment_dashboard, name='dashboard'),
    path('capability/setup/', views.payment_capability_setup, name='capability_setup'),
    path('gateway/config/', views.payment_gateway_config, name='gateway_config'),
    path('gateway/config/<int:gateway_id>/', views.payment_gateway_config, name='gateway_config_edit'),
    
    # Gestion des paiements
    path('create/', views.create_payment, name='create_payment'),
    path('list/', views.payment_list, name='payment_list'),
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('cancel/<int:payment_id>/', views.payment_cancel, name='payment_cancel'),
    
    # Remboursements
    path('refund/<int:payment_id>/', views.refund_payment, name='refund_payment'),
    
    # Vérification manuelle
    path('manual/verification/<int:payment_id>/', views.manual_payment_verification, name='manual_verification'),
    
    # Tarification régionale
    path('pricing/', views.regional_pricing, name='regional_pricing'),
    
    # Webhooks (sans authentification)
    path('webhook/<str:provider>/', views.payment_webhook, name='webhook'),
    
    # APIs AJAX
    path('api/methods/', views.api_payment_methods, name='api_methods'),
    path('api/status/<int:payment_id>/', views.api_payment_status, name='api_status'),
    
    # Pages d'information
    path('info/', TemplateView.as_view(template_name='competitions/payment/info.html'), name='info'),
    path('help/', TemplateView.as_view(template_name='competitions/payment/help.html'), name='help'),
] 
