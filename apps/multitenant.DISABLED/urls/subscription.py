from django.urls import path
from ..views import subscription_views

app_name = 'multitenant'

urlpatterns = [
    path('dashboard/', subscription_views.subscription_dashboard, name='subscription_dashboard'),
    path('plans/', subscription_views.subscription_plans, name='subscription_plans'),
    path('subscribe/', subscription_views.subscribe, name='subscribe'),
    path('cancel/', subscription_views.cancel_subscription, name='cancel_subscription'),
    path('validate-promo/', subscription_views.validate_promo_code, name='validate_promo_code'),
    path('usage-history/', subscription_views.feature_usage_history, name='feature_usage_history'),
    path('customer-portal/', subscription_views.customer_portal, name='customer_portal'),
]