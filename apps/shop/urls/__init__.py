from django.urls import path, include

app_name = 'shop'

urlpatterns = [
    path('', include('apps.shop.urls.catalog')),           # ✅ Chemin absolu correct
    path('cart/', include('apps.shop.urls.cart')),         # ✅ Chemin absolu correct  
    path('checkout/', include('apps.shop.urls.checkout')), # ✅ Chemin absolu correct
    path('payment/', include('apps.shop.urls.payment')),   # ✅ Chemin absolu correct
    path('account/', include('apps.shop.urls.account')),   # ✅ Chemin absolu correct
    path('dashboard/', include('apps.shop.urls.dashboard')), # ✅ Chemin absolu correct
]