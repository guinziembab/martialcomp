from django.urls import path
from shop.views import account

app_name = 'account'

urlpatterns = [
    # Commandes
    path('orders/', account.order_list, name='order_list'),
    path('order/<uuid:order_id>/', account.order_detail, name='order_detail'),
    path('order/<uuid:order_id>/invoice/', account.order_invoice, name='order_invoice'),
    
    # Adresses
    path('addresses/', account.address_list, name='address_list'),
    path('address/add/', account.address_add, name='address_add'),
    path('address/<int:address_id>/edit/', account.address_edit, name='address_edit'),
    path('address/<int:address_id>/delete/', account.address_delete, name='address_delete'),
    path('address/<int:address_id>/set-default/<str:address_type>/', account.set_default_address, name='set_default_address'),
    
    # Avis produits
    path('reviews/', account.review_list, name='review_list'),
    path('review/<int:review_id>/edit/', account.review_edit, name='review_edit'),
    path('review/<int:review_id>/delete/', account.review_delete, name='review_delete'),
]