from django.urls import path, include

app_name = 'shop'

urlpatterns = [
    # Inclure les différents modules d'URL
    path('', include('shop.urls.catalog', namespace='catalog')),
    path('cart/', include('shop.urls.cart', namespace='cart')),
    path('checkout/', include('shop.urls.checkout', namespace='checkout')),
    path('payment/', include('shop.urls.payment', namespace='payment')),
    path('dashboard/', include('shop.urls.dashboard', namespace='dashboard')),
    path('reports/', include('shop.urls.reports', namespace='reports')),
    path('', include('shop.urls.reviews', namespace='reviews')),
    path('account/', include('shop.urls.account', namespace='account')),
]
