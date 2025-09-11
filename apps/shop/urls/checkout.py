from django.urls import path
from apps.shop.views import checkout

app_name = 'checkout'

urlpatterns = [
    path('', checkout.checkout_view, name='checkout'),
    path('addresses/', checkout.shipping_address, name='addresses'),
    path('addresses/edit/<int:address_id>/', checkout.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', checkout.delete_address, name='delete_address'),
    path('confirmation/<str:order_reference>/', checkout.order_confirmation, name='order_confirmation'),
    path('update-shipping-method/', checkout.update_shipping_method, name='update_shipping_method'),
]
