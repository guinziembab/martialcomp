from django.urls import path, include
from django.contrib.auth.decorators import login_required

from .views.debug_access import DebugDashboardView, DebugPaymentMethodListView

# URLs pour le débogage de l'application finances
urlpatterns = [
    # Dashboard de débogage
    path('', DebugDashboardView.as_view(), name='debug_dashboard'),
    
    # Méthodes de paiement
    path('payments/methods/', DebugPaymentMethodListView.as_view(), name='debug_payment_methods'),
]