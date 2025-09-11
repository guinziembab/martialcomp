from django.urls import path
from apps.shop.views import cart

app_name = 'cart'

urlpatterns = [
    # Vues principales du panier
    path('', cart.cart_detail, name='detail'),
    path('summary/', cart.cart_summary, name='summary'),
    
    # Actions sur le panier (AJAX)
    path('add/', cart.add_to_cart, name='add'),
    path('update/', cart.update_cart, name='update'),
    path('remove/<int:item_id>/', cart.remove_from_cart, name='remove'),
    path('clear/', cart.clear_cart, name='clear'),
    
    # Coupons
    path('apply-coupon/', cart.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', cart.remove_coupon, name='remove_coupon'),
]
