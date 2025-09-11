from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
"""
Vues du catalogue shop spécialisées pour les coaches
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Count, Min, Max, Avg, F
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from apps.shop.models import Product, Category, Brand, ProductReview
from apps.competitions.models import Discipline
from apps.shop.forms.catalog import ProductFilterForm, ProductSearchForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


def get_user_template_context(request):
    """Détermine le template et le contexte selon le rôle utilisateur"""
    user_role = None
    is_coach = False
    
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        is_coach = user_role == 'coach'
    
    base_template = 'shop/coach_base.html' if is_coach else 'shop/base.html'
    
    return {
        'user_role': user_role,
        'is_coach': is_coach,
        'base_template': base_template
    }


def coach_product_list(request):
    """
    Vue du catalogue de produits adaptée pour les coaches.
    """
    # Récupérer les produits
    products = Product.objects.filter(is_active=True).select_related('brand')
    
    # Appliquer les filtres
    filter_form = ProductFilterForm(request.GET)
    
    if filter_form.is_valid():
        # Filtrer par catégorie
        category_slug = filter_form.cleaned_data.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                descendants = category.get_descendants()
                category_ids = [category.id] + [desc.id for desc in descendants]
                products = products.filter(categories__id__in=category_ids)
            except Category.DoesNotExist:
                pass
                
        # Filtrer par marque
        brand_name = filter_form.cleaned_data.get('brand')
        if brand_name:
            products = products.filter(brand__icontains=brand_name)
            
        # Filtrer by niveau de pratique
        practice_level = filter_form.cleaned_data.get('practice_level')
        if practice_level:
            products = products.filter(practice_level=practice_level)
            
        # Filtrer par discipline
        discipline_id = filter_form.cleaned_data.get('discipline')
        if discipline_id:
            products = products.filter(disciplines__id=discipline_id)
            
        # Filtrer par prix
        min_price = filter_form.cleaned_data.get('min_price')
        if min_price:
            products = products.filter(price__gte=min_price)
            
        max_price = filter_form.cleaned_data.get('max_price')
        if max_price:
            products = products.filter(price__lte=max_price)
    
    # Tri
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtenir les catégories pour le filtre
    categories = Category.objects.filter(is_active=True)
    
    # Obtenir les disciplines disponibles
    disciplines = get_organization_queryset(Discipline, self.request.user).order_by('name')
    
    # Obtenir les marques disponibles
    brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct()
    brands = [brand for brand in brands if brand]  # Éliminer les valeurs None
    
    # Statistiques pour les filtres
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Contexte du template
    template_context = get_user_template_context(request)
    
    context = {
        'products': page_obj,
        'filter_form': filter_form,
        'categories': categories,
        'disciplines': disciplines,
        'brands': brands,
        'price_range': price_range,
        'total_products': paginator.count,
        'page_obj': page_obj,
        'sort_by': sort_by,
        **template_context
    }
    
    # Utiliser le template approprié selon le rôle
    template_name = 'shop/coach/catalog/product_list.html' if template_context['is_coach'] else 'shop/catalog/product_list.html'
    
    return render(request, template_name, context)


def coach_product_detail(request, slug):
    """
    Vue de détail d'un produit adaptée pour les coaches.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Récupérer les avis
    reviews = ProductReview.objects.filter(
        product=product, 
        is_approved=True
    ).select_related('user').order_by('-created_at')
    
    # Statistiques des avis
    reviews_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Produits similaires
    similar_products = Product.objects.filter(
        categories__in=product.categories.all(),
        is_active=True
    ).exclude(id=product.id).distinct()[:4]
    
    # Contexte du template
    template_context = get_user_template_context(request)
    
    context = {
        'product': product,
        'reviews': reviews,
        'reviews_stats': reviews_stats,
        'similar_products': similar_products,
        **template_context
    }
    
    # Utiliser le template approprié selon le rôle
    template_name = 'shop/coach/catalog/product_detail.html' if template_context['is_coach'] else 'shop/catalog/product_detail.html'
    
    return render(request, template_name, context)


def coach_category_list(request):
    """
    Vue de la liste des catégories adaptée pour les coaches.
    """
    categories = Category.objects.filter(
        is_active=True,
        parent=None  # Seulement les catégories racines
    ).prefetch_related('children')
    
    # Contexte du template
    template_context = get_user_template_context(request)
    
    context = {
        'categories': categories,
        **template_context
    }
    
    # Utiliser le template approprié selon le rôle
    template_name = 'shop/coach/catalog/category_list.html' if template_context['is_coach'] else 'shop/catalog/category_list.html'
    
    return render(request, template_name, context)


@login_required
def coach_product_search(request):
    """
    Vue de recherche de produits adaptée pour les coaches.
    """
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(categories__name__icontains=query)
        ).filter(is_active=True).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contexte du template
    template_context = get_user_template_context(request)
    
    context = {
        'products': page_obj,
        'query': query,
        'total_results': paginator.count,
        'page_obj': page_obj,
        **template_context
    }
    
    # Utiliser le template approprié selon le rôle
    template_name = 'shop/coach/catalog/search_results.html' if template_context['is_coach'] else 'shop/catalog/search_results.html'
    
    return render(request, template_name, context)