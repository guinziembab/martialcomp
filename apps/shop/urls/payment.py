from django.urls import path
from ..views import payment

app_name = 'payment'

urlpatterns = [
    # Customer payment flows
    path('methods/<uuid:order_id>/', payment.payment_methods, name='payment_methods'),
    path('process/<uuid:order_id>/', payment.process_payment, name='process_payment'),
    path('callback/<uuid:payment_id>/', payment.payment_callback, name='payment_callback'),
    
    # Simulation routes for demonstration
    path('simulate-paypal/<uuid:payment_id>/', payment.payment_simulate_paypal, name='simulate_paypal'),
    
    # Admin payment management
    path('refund/club/<uuid:payment_id>/', payment.club_refund_payment, name='club_refund_payment'),
    path('refund/federation/<uuid:payment_id>/', payment.federation_refund_payment, name='federation_refund_payment'),
]