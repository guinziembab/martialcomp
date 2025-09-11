from django.core.exceptions import PermissionDenied
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


def product_list(request):
    """
    Vue principale du catalogue de produits avec filtres et pagination.
    """
    products = Product.objects.filter(is_active=True)
    
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
            
        # Filtrer par niveau de pratique
        practice_level = filter_form.cleaned_data.get('practice_level')
        if practice_level:
            products = products.filter(practice_level=practice_level)
            
        # Filtrer par discipline
        discipline_id = filter_form.cleaned_data.get('discipline')
        if discipline_id:
            products = products.filter(disciplines__id=discipline_id)
            
        # Filtrer par prix
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        
        if min_price is not None:
            products = products.filter(Q(sale_price__gte=min_price) | 
                                      (Q(sale_price__isnull=True) & Q(price__gte=min_price)))
        
        if max_price is not None:
            products = products.filter(Q(sale_price__lte=max_price) | 
                                      (Q(sale_price__isnull=True) & Q(price__lte=max_price)))
        
        # Filtrer par disponibilité
        in_stock = filter_form.cleaned_data.get('in_stock')
        if in_stock:
            products = products.filter(stock_quantity__gt=0)
            
        # Filtrer par certification
        is_certified = filter_form.cleaned_data.get('is_certified')
        if is_certified:
            products = products.filter(is_certified=True)
    
    # Trier les résultats
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('sale_price', 'price')
    elif sort_by == 'price_high':
        products = products.order_by('-sale_price', '-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 produits par page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les facettes pour les filtres
    if page_number == 1:  # Calculer les facettes uniquement sur la première page pour éviter les requÃªtes inutiles
        price_range = products.aggregate(min_price=Min('price'), max_price=Max('price'))
        categories = Category.objects.filter(products__in=products).annotate(
            product_count=Count('products')
        ).distinct().order_by('name')
        
        # Get brand names from products instead of Brand objects
        brand_names = products.values_list('brand', flat=True).distinct().exclude(brand='')
        brands = [{'name': brand, 'slug': brand.lower().replace(' ', '-')} for brand in brand_names if brand]
        
        context = {
            'page_obj': page_obj,
            'filter_form': filter_form,
            'sort_by': sort_by,
            'price_range': price_range,
            'categories': categories,
            'brands': brands,
            'active_filters': {key: value for key, value in request.GET.items() if key != 'page' and value},
            'total_products': products.count(),
        }
    else:
        context = {
            'page_obj': page_obj,
            'filter_form': filter_form,
            'sort_by': sort_by,
            'active_filters': {key: value for key, value in request.GET.items() if key != 'page' and value},
            'total_products': products.count(),
        }
    
    # Détecter le rôle utilisateur et adapter le template
    user_role = None
    is_coach = False
    template_name = 'shop/catalog/product_list.html'
    
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        is_coach = user_role == 'coach'
        if is_coach:
            template_name = 'shop/coach/catalog/product_list.html'
    
    context['user_role'] = user_role
    context['is_coach'] = is_coach
    
    return render(request, template_name, context)


def product_search(request):
    """
    Recherche de produits par mots-clés.
    """
    query = request.GET.get('q', '')
    form = ProductSearchForm(request.GET)
    products = Product.objects.filter(is_active=True)
    
    if query:
        # Rechercher dans le nom, la description, les tags, etc.
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(tags__icontains=query) |
            Q(meta_title__icontains=query) |
            Q(meta_description__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'search_form': form,
        'query': query,
        'page_obj': page_obj,
        'total_results': products.count(),
    }
    
    return render(request, 'shop/catalog/product_search.html', context)


def category_detail(request, slug):
    """
    Affiche les produits d'une catégorie spécifique.
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Inclure les sous-catégories
    descendants = category.get_descendants()
    category_ids = [category.id] + [desc.id for desc in descendants]
    
    # Récupérer les produits de cette catégorie et ses sous-catégories
    products = Product.objects.filter(
        categories__id__in=category_ids,
        is_active=True
    )
    
    # Filtres et tri
    filter_form = ProductFilterForm(request.GET)
    sort_by = request.GET.get('sort', 'newest')
    
    # Appliquer les filtres si le formulaire est valide
    if filter_form.is_valid():
        # Appliquer les mÃªmes filtres que dans product_list
        # (code omis pour éviter la répétition, utiliser une fonction d'aide dans une situation réelle)
        pass
    
    # Appliquer le tri
    if sort_by == 'price_low':
        products = products.order_by('sale_price', 'price')
    elif sort_by == 'price_high':
        products = products.order_by('-sale_price', '-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Sous-catégories
    subcategories = category.children.filter(is_active=True)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'subcategories': subcategories,
        'filter_form': filter_form,
        'sort_by': sort_by,
        'breadcrumbs': category.get_ancestors(include_self=True),
        'total_products': products.count(),
    }
    
    return render(request, 'shop/catalog/category_detail.html', context)


def product_detail(request, slug):
    """
    Affiche les détails d'un produit spécifique.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Charger les images du produit
    images = product.images.all().order_by('order', '-is_main')
    
    # Charger les variations du produit
    variations = product.variations.filter(is_active=True).select_related('product')
    
    # Obtenir les valeurs d'attributs distinctes pour chaque type
    attributes = {}
    
    for variation in variations:
        for attr_value in variation.attributes.all():
            attr_type = attr_value.attribute_type
            if attr_type.id not in attributes:
                attributes[attr_type.id] = {
                    'type': attr_type,
                    'values': []
                }
            
            if attr_value not in attributes[attr_type.id]['values']:
                attributes[attr_type.id]['values'].append(attr_value)
    
    # Récupérer les avis sur le produit
    reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
    
    # Calculer la note moyenne
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Distribution des notes
    rating_distribution = {
        i: reviews.filter(rating=i).count() for i in range(1, 6)
    }
    
    # Produits associés (mÃªme catégorie ou mÃªme marque)
    related_products = Product.objects.filter(
        is_active=True
    ).filter(
        Q(category=product.category) | Q(brand=product.brand)
    ).exclude(
        id=product.id
    ).distinct()[:4]
    
    # Produits similaires basés sur les disciplines
    similar_products = None
    if product.disciplines.exists():
        discipline_ids = product.disciplines.values_list('id', flat=True)
        similar_products = Product.objects.filter(
            disciplines__id__in=discipline_ids,
            is_active=True
        ).exclude(
            id=product.id
        ).distinct()[:4]
    
    # Construire le fil d'Ariane
    breadcrumbs = [
        {'name': _('Accueil'), 'url': '/'},
        {'name': _('Boutique'), 'url': '/shop/'}
    ]
    
    # Ajouter la catégorie principale si elle existe
    main_category = product.categories.first()
    if main_category:
        breadcrumbs.append({
            'name': main_category.name, 
            'url': f'/shop/category/{main_category.slug}/'
        })
    
    # Ajouter le nom du produit
    breadcrumbs.append({'name': product.name, 'url': None})
    
    context = {
        'product': product,
        'images': images,
        'variations': variations,
        'attributes': attributes,
        'reviews': reviews[:5],  # Limiter Ã  5 avis initiaux
        'reviews_count': reviews.count(),
        'avg_rating': avg_rating,
        'rating_distribution': rating_distribution,
        'related_products': related_products,
        'similar_products': similar_products,
        'breadcrumbs': breadcrumbs,
    }
    
    return render(request, 'shop/catalog/product_detail.html', context)


def brand_list(request):
    """
    Affiche la liste des marques disponibles.
    """
    # Get parameter to show empty brands
    show_empty = request.GET.get('show_empty', False)
    
    # Get unique brand names from products instead of Brand objects
    brand_names = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().exclude(brand='')
    
    # Create brand data with product counts
    brands = []
    for brand_name in brand_names:
        if brand_name:
            product_count = Product.objects.filter(brand=brand_name, is_active=True).count()
            # Only add brands with products, unless show_empty is True
            if product_count > 0 or show_empty:
                brands.append({
                    'name': brand_name,
                    'slug': brand_name.lower().replace(' ', '-'),
                    'product_count': product_count
                })
    
    # Sort by name
    brands = sorted(brands, key=lambda x: x['name'])
    
    # For compatibility, create empty featured brands
    featured_brands = []
    
    context = {
        'brands': brands,
        'featured_brands': featured_brands,
        'show_empty': show_empty,
    }
    
    return render(request, 'shop/catalog/brand_list.html', context)


def brand_detail(request, slug):
    """
    Affiche les produits d'une marque spécifique.
    """
    # Convert slug back to brand name
    brand_name = slug.replace('-', ' ').title()
    
    # Check if brand exists by checking if products exist
    products = Product.objects.filter(brand__icontains=brand_name, is_active=True)
    if not products.exists():
        # Try exact match
        products = Product.objects.filter(brand=brand_name, is_active=True)
        if not products.exists():
            from django.http import Http404
            raise Http404("Brand not found")
    
    # Create brand object for template compatibility
    brand = {'name': brand_name, 'slug': slug}
    
    # Appliquer les filtres et le tri comme pour product_list
    # (code omis pour éviter la répétition)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'brand': brand,
        'page_obj': page_obj,
        'total_products': products.count(),
    }
    
    return render(request, 'shop/catalog/brand_detail.html', context)


def new_arrivals(request):
    """
    Affiche les nouveaux produits.
    """
    # Récupérer les produits marqués comme nouveaux
    products = Product.objects.filter(is_active=True, is_new=True).order_by('-created_at')
    
    # Pagination et contexte similaires Ã  product_list
    
    context = {
        'page_title': _('Nouveautés'),
        'page_description': _('Découvrez nos derniers produits'),
        # Autres éléments de contexte similaires Ã  product_list
    }
    
    return render(request, 'shop/catalog/product_list.html', context)


def on_sale(request):
    """
    Affiche les produits en promotion.
    """
    # Récupérer les produits avec un prix de vente inférieur au prix normal
    products = Product.objects.filter(
        is_active=True,
        sale_price__isnull=False
    ).filter(
        sale_price__lt=F('price')
    ).order_by('-created_at')
    
    # Pagination et contexte similaires Ã  product_list
    
    context = {
        'page_title': _('Promotions'),
        'page_description': _('Profitez de nos offres spéciales'),
        # Autres éléments de contexte
    }
    
    return render(request, 'shop/catalog/product_list.html', context)


def featured_products(request):
    """
    Affiche les produits mis en avant.
    """
    products = Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')
    
    # Pagination et contexte similaires Ã  product_list
    
    context = {
        'page_title': _('Produits Ã  la une'),
        'page_description': _('Notre sélection de produits recommandés'),
        # Autres éléments de contexte
    }
    
    return render(request, 'shop/catalog/product_list.html', context)


def discipline_products(request, discipline_id):
    """
    Affiche les produits associés Ã  une discipline spécifique.
    """
    discipline = get_object_or_404(Discipline, id=discipline_id)
    
    # Récupérer les produits liés Ã  cette discipline
    products = Product.objects.filter(
        disciplines=discipline,
        is_active=True
    ).order_by('-created_at')
    
    # Pagination et contexte similaires Ã  product_list
    
    context = {
        'discipline': discipline,
        'page_title': f"{_('Ã‰quipements pour')} {discipline.name}",
        'page_description': f"{_('Tous les produits adaptés Ã  la pratique du')} {discipline.name}",
        # Autres éléments de contexte
    }
    
    return render(request, 'shop/catalog/product_list.html', context)


def product_suggestions(request):
    """
    API pour les suggestions de produits (utilisé en AJAX).
    """
    query = request.GET.get('q', '')
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Rechercher des correspondances
    products = Product.objects.filter(
        is_active=True,
        name__icontains=query
    ).values('id', 'name', 'slug', 'price', 'sale_price')[:6]
    
    return JsonResponse({'suggestions': list(products)})


def filter_options(request):
    """
    API pour récupérer dynamiquement les options de filtre (utilisé en AJAX).
    """
    # Récupérer les filtres actifs pour affiner les résultats
    # Cette fonction renvoie les options de filtre disponibles en fonction des filtres déjÃ  appliqués
    
    # Get unique brand names from products
    brand_names = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().exclude(brand='')
    brands = [{'name': brand, 'slug': brand.lower().replace(' ', '-')} for brand in brand_names if brand]
    
    return JsonResponse({
        'brands': brands,
        'categories': list(Category.objects.values('id', 'name', 'slug')),
        'price_range': Product.objects.aggregate(min=Min('price'), max=Max('price')),
    })

