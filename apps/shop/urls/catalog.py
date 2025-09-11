from django.urls import path
from apps.shop.views import catalog

app_name = 'catalog'

urlpatterns = [
    # Catalogue principal
    path('', catalog.product_list, name='product_list'),
    path('search/', catalog.product_search, name='product_search'),
    
    # Pages de catégorie
    path('category/<slug:slug>/', catalog.category_detail, name='category_detail'),
    
    # Pages produit
    path('product/<slug:slug>/', catalog.product_detail, name='product_detail'),
    
    # Marques
    path('brands/', catalog.brand_list, name='brand_list'),
    path('brand/<slug:slug>/', catalog.brand_detail, name='brand_detail'),
    
    # Filtres spéciaux
    path('new-arrivals/', catalog.new_arrivals, name='new_arrivals'),
    path('sale/', catalog.on_sale, name='on_sale'),
    path('featured/', catalog.featured_products, name='featured_products'),
    
    # Filtres par discipline
    path('discipline/<int:discipline_id>/', catalog.discipline_products, name='discipline_products'),
    
    # API pour le chargement dynamique
    path('api/products/suggest/', catalog.product_suggestions, name='product_suggestions'),
    path('api/filter-options/', catalog.filter_options, name='filter_options'),
]

