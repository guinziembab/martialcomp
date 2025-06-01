from django.urls import path, include

app_name = 'shop'

urlpatterns = [
    path('', include('shop.urls.catalog')),
    path('cart/', include('shop.urls.cart')),
    path('checkout/', include('shop.urls.checkout')),
    path('payment/', include('shop.urls.payment')),
    path('account/', include('shop.urls.account')),
    path('dashboard/', include('shop.urls.dashboard')),
]