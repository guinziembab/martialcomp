from django.urls import path, include
from shop.views import dashboard

app_name = 'dashboard'

urlpatterns = [
    # Club Dashboard URLs
    path('club/', dashboard.shop_club_dashboard, name='club_dashboard'),
    path('club/orders/', dashboard.club_orders, name='club_orders'),
    path('club/order/<uuid:order_id>/', dashboard.club_order_detail, name='club_order_detail'),
    path('club/order/<uuid:order_id>/update-status/', dashboard.club_order_update_status, name='club_order_update_status'),
    path('club/order/<uuid:order_id>/invoice/', dashboard.club_order_invoice, name='club_order_invoice'),
    path('club/products/', dashboard.club_products, name='club_products'),
    path('club/product/create/', dashboard.club_product_create, name='club_product_create'),
    path('club/product/<int:product_id>/', dashboard.club_product_detail, name='club_product_detail'),
    path('club/product/<int:product_id>/edit/', dashboard.club_product_edit, name='club_product_edit'),
    path('club/product/<int:product_id>/delete/', dashboard.club_product_delete, name='club_product_delete'),
    path('club/inventory/', dashboard.club_inventory, name='club_inventory'),
    
    # Federation Dashboard URLs
    path('federation/', dashboard.shop_federation_dashboard, name='federation_dashboard'),
    path('federation/catalog/', dashboard.federation_product_catalog, name='federation_catalog'),
    path('federation/orders/', dashboard.federation_orders, name='federation_orders'),
    path('federation/product/create/', dashboard.federation_product_create, name='federation_product_create'),
    path('federation/product/<int:product_id>/', dashboard.federation_product_detail, name='federation_product_detail'),
    
    # Sales reports
    path('club/sales/', dashboard.club_sales_report, name='club_sales_report'),
    path('federation/sales/', dashboard.federation_sales_report, name='federation_sales_report'),
    
    # Detailed reports are included from reports.py at the main shop/urls.py level
]