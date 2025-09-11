from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Tableau de bord des abonnements
    path('dashboard/', views.subscription_dashboard, name='subscription_dashboard'),
    
    # Plans d'abonnement
    path('plans/', views.subscription_plans, name='subscription_plans'),
    path('upgrade/<int:plan_id>/', views.upgrade_subscription, name='upgrade_subscription'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Méthodes de paiement
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('add-payment-method/', views.add_payment_method, name='add_payment_method'),
    
    # Historique et remboursements
    path('history/', views.payment_history, name='payment_history'),
    path('refund/<int:payment_id>/', views.request_refund, name='request_refund'),
    
    # Webhook
    path('webhook/', views.payment_webhook, name='payment_webhook'),
    
    # API endpoints
    path('api/subscription-status/', views.api_subscription_status, name='api_subscription_status'),
    path('api/extend-trial/', views.api_extend_trial, name='api_extend_trial'),
] 
