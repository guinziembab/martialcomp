from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, date
from competitions.models import Club

def get_federation_from_request(request):
    """
    Récupère la fédération soit depuis request.federation, soit depuis les paramètres GET.
    """
    federation = getattr(request, 'federation', None)
    if not federation:
        federation_id = request.GET.get('federation_id')
        if federation_id:
            from competitions.models import Federation
            try:
                federation = Federation.objects.get(id=federation_id)
            except Federation.DoesNotExist:
                return None
        else:
            return None
    return federation

from shop.models import (
    Product, Category, Order, OrderItem, ProductReview
)
from competitions.models import ScoringCriterion
from shop.forms.dashboard import (
    ProductForm, ProductImageFormSet, ProductVariationFormSet,
    OrderStatusUpdateForm, OrderFilterForm, SalesReportForm
)
from competitions.utils.decorators import club_required, federation_required


# Vues pour le tableau de bord des clubs
@login_required
@club_required
def shop_club_dashboard(request):
    """
    Vue principale du tableau de bord boutique pour un club.
    """
    club = request.club
    
    # Statistiques récentes (30 derniers jours)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    recent_orders = Order.objects.filter(
        club=club,
        created_at__gte=thirty_days_ago
    )
    
    # Statistiques générales
    stats = {
        'recent_orders_count': recent_orders.count(),
        'recent_orders_total': recent_orders.aggregate(total=Sum('total'))['total'] or 0,
        'pending_orders': recent_orders.filter(status__in=['pending', 'processing']).count(),
        'completed_orders': recent_orders.filter(status__in=['shipped', 'delivered']).count(),
    }
    
    # Commandes récentes pour affichage rapide
    latest_orders = recent_orders.order_by('-created_at')[:5]
    
    # Produits populaires (basés sur les ventes du club)
    popular_products = (
        OrderItem.objects
        .filter(order__club=club, order__created_at__gte=thirty_days_ago)
        .values('product_id', 'product_name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )
    
    context = {
        'club': club,
        'stats': stats,
        'latest_orders': latest_orders,
        'popular_products': popular_products,
        'current_section': 'shop_dashboard'
    }
    
    return render(request, 'shop/dashboard/club/dashboard.html', context)


@login_required
@club_required
def club_orders(request):
    """
    Gestion des commandes pour un club.
    """
    club = request.club
    
    # Filtrer les commandes
    filter_form = OrderFilterForm(request.GET)
    orders = Order.objects.filter(club=club)
    
    if filter_form.is_valid():
        # Appliquer les filtres
        status = filter_form.cleaned_data.get('status')
        if status:
            orders = orders.filter(status=status)
            
        date_start = filter_form.cleaned_data.get('date_start')
        if date_start:
            orders = orders.filter(created_at__gte=date_start)
            
        date_end = filter_form.cleaned_data.get('date_end')
        if date_end:
            orders = orders.filter(created_at__lte=date_end)
            
        min_total = filter_form.cleaned_data.get('min_total')
        if min_total:
            orders = orders.filter(total__gte=min_total)
            
        max_total = filter_form.cleaned_data.get('max_total')
        if max_total:
            orders = orders.filter(total__lte=max_total)
            
        search_term = filter_form.cleaned_data.get('search')
        if search_term:
            orders = orders.filter(
                Q(order_number__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(user__username__icontains=search_term) |
                Q(shipping_address__first_name__icontains=search_term) |
                Q(shipping_address__last_name__icontains=search_term)
            )
    
    # Trier les commandes
    sort_by = request.GET.get('sort', '-created_at')
    orders = orders.order_by(sort_by)
    
    # Compter les commandes par statut pour les statistiques
    stats = {
        'total': orders.count(),
        'pending': orders.filter(status='pending').count(),
        'processing': orders.filter(status='processing').count(),
        'delivered': orders.filter(status='delivered').count()
    }
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'club': club,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'current_section': 'shop_orders',
        'stats': stats
    }
    
    return render(request, 'shop/dashboard/club/orders.html', context)


@login_required
@club_required
def club_order_detail(request, order_id):
    """
    Détails d'une commande spécifique pour un club.
    """
    club = request.club
    order = get_object_or_404(Order, id=order_id, club=club)
    
    # Formulaire de mise à jour du statut
    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, _("Statut de la commande mis à jour."))
            return redirect('shop:dashboard:club_order_detail', order_id=order_id)
    else:
        form = OrderStatusUpdateForm(instance=order)
    
    context = {
        'club': club,
        'order': order,
        'form': form,
        'current_section': 'shop_orders'
    }
    
    return render(request, 'shop/dashboard/club/order_detail.html', context)


@login_required
@club_required
def club_order_update_status(request, order_id):
    """
    Mise à jour du statut d'une commande via AJAX ou formulaire POST.
    """
    club = request.club
    order = get_object_or_404(Order, id=order_id, club=club)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['processing', 'shipped', 'delivered', 'cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, _("Statut de la commande mis à jour avec succès."))
        else:
            messages.error(request, _("Statut invalide."))
    
    # Rediriger vers la page des commandes
    return redirect('shop:dashboard:club_orders')


@login_required
@club_required
def club_order_invoice(request, order_id):
    """
    Génère et télécharge la facture d'une commande au format PDF.
    """
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    
    club = request.club
    order = get_object_or_404(Order, id=order_id, club=club)
    
    # Créer la réponse HTTP avec le type de contenu PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"facture_commande_{order.order_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Créer le document PDF avec ReportLab
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, height - inch, f"Facture - Commande #{order.order_number}")
    
    # Informations du club
    p.setFont("Helvetica", 10)
    p.drawString(inch, height - 1.5 * inch, f"Club: {club.name}")
    
    # Informations client
    y_position = height - 2.5 * inch
    p.drawString(inch, y_position, "Informations client:")
    p.drawString(inch, y_position - 0.3 * inch, f"Nom: {order.user.get_full_name()}")
    p.drawString(inch, y_position - 0.6 * inch, f"Email: {order.user.email}")
    
    # Date de commande
    p.drawString(inch, y_position - 1 * inch, f"Date: {order.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    # Tableau des produits
    y_position = height - 4.5 * inch
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, y_position, "Détails de la commande:")
    
    # En-tête du tableau
    p.setFont("Helvetica-Bold", 10)
    y_position -= 0.3 * inch
    p.drawString(inch, y_position, "Produit")
    p.drawString(4 * inch, y_position, "Quantité")
    p.drawString(5 * inch, y_position, "Prix unitaire")
    p.drawString(6.5 * inch, y_position, "Total")
    
    # Ligne de séparation
    p.line(inch, y_position - 0.1 * inch, 7.5 * inch, y_position - 0.1 * inch)
    
    # Lignes des produits
    p.setFont("Helvetica", 10)
    y_position -= 0.3 * inch
    
    for item in order.items.all():
        p.drawString(inch, y_position, item.product_name[:40])
        p.drawString(4 * inch, y_position, str(item.quantity))
        p.drawString(5 * inch, y_position, f"{item.price} €")
        p.drawString(6.5 * inch, y_position, f"{item.total} €")
        y_position -= 0.3 * inch
    
    # Total
    p.setFont("Helvetica-Bold", 12)
    p.drawString(5 * inch, y_position - 0.5 * inch, "Total:")
    p.drawString(6.5 * inch, y_position - 0.5 * inch, f"{order.total} €")
    
    # Finaliser le PDF
    p.showPage()
    p.save()
    
    return response


@login_required
@club_required
def club_products(request):
    """
    Gestion des produits pour un club.
    """
    club = request.club
    
    # Récupérer les produits vendus par ce club
    # On peut utiliser différentes approches :
    # 1. Produits des disciplines que le club pratique
    discipline_ids = club.disciplines.values_list('id', flat=True)
    products = Product.objects.filter(disciplines__in=discipline_ids).distinct()
    
    # Si aucun produit par discipline, récupérer tous les produits actifs
    if not products.exists():
        products = Product.objects.filter(is_active=True)
    
    # Filtrer et trier selon les paramètres
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Trier
    sort_by = request.GET.get('sort', '-created_at')
    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'club': club,
        'page_obj': page_obj,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/club/products.html', context)


@login_required
@club_required
def club_product_create(request):
    """
    Créer un nouveau produit pour un club.
    """
    club = request.club
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')
        variation_formset = ProductVariationFormSet(request.POST, prefix='variations')
        
        if form.is_valid() and image_formset.is_valid() and variation_formset.is_valid():
            # Créer le produit (sans club car Product n'a pas ce champ)
            product = form.save(commit=False)
            # Ajouter les disciplines du club si pas spécifiées
            product.save()
            form.save_m2m()  # Sauvegarder les relations many-to-many
            
            # S'assurer que le produit est associé aux disciplines du club
            if not product.disciplines.exists():
                product.disciplines.set(club.disciplines.all())
            
            # Sauvegarder les images
            images = image_formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()
            
            # Sauvegarder les variations
            variations = variation_formset.save(commit=False)
            for variation in variations:
                variation.product = product
                variation.save()
            
            messages.success(request, _("Produit créé avec succès."))
            return redirect('shop:dashboard:club_product_detail', product_id=product.id)
    else:
        form = ProductForm()
        image_formset = ProductImageFormSet(prefix='images')
        variation_formset = ProductVariationFormSet(prefix='variations')
    
    context = {
        'club': club,
        'form': form,
        'image_formset': image_formset,
        'variation_formset': variation_formset,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/club/product_form.html', context)


@login_required
@club_required
def club_product_edit(request, product_id):
    """
    Modifier un produit existant pour un club.
    """
    club = request.club
    # Récupérer le produit (sans filtrer par club car Product n'a pas ce champ)
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, 
                                          instance=product, prefix='images')
        variation_formset = ProductVariationFormSet(request.POST, 
                                                 instance=product, prefix='variations')
        
        if form.is_valid() and image_formset.is_valid() and variation_formset.is_valid():
            # Sauvegarder les modifications
            product = form.save()
            image_formset.save()
            variation_formset.save()
            
            messages.success(request, _("Produit mis à jour avec succès."))
            return redirect('shop:dashboard:club_product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(instance=product, prefix='images')
        variation_formset = ProductVariationFormSet(instance=product, prefix='variations')
    
    context = {
        'club': club,
        'product': product,
        'form': form,
        'image_formset': image_formset,
        'variation_formset': variation_formset,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/club/product_form.html', context)


@login_required
@club_required
def club_product_delete(request, product_id):
    """
    Supprimer un produit pour un club.
    """
    club = request.club
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, _("Produit supprimé avec succès."))
        return redirect('shop:dashboard:club_products')
    
    return redirect('shop:dashboard:club_product_detail', product_id=product_id)


@login_required
@club_required
def club_inventory(request):
    """
    Gestion de l'inventaire des produits pour un club.
    """
    club = request.club
    
    # Récupérer tous les produits vendus dans le club
    # Comme Product n'a pas de champ club, on peut soit:
    # 1. Récupérer tous les produits actifs
    # 2. Récupérer les produits des disciplines du club
    discipline_ids = club.disciplines.values_list('id', flat=True)
    if discipline_ids:
        products = Product.objects.filter(disciplines__in=discipline_ids).distinct().order_by('stock_quantity')
    else:
        products = Product.objects.filter(is_active=True).order_by('stock_quantity')
    
    # Filtrer les produits à faible stock en premier (moins de 10 unités)
    low_stock_products = products.filter(stock_quantity__lt=10)
    
    # Mise à jour du stock en masse si formulaire soumis
    if request.method == 'POST':
        # Récupérer les données du formulaire
        product_ids = request.POST.getlist('product_id')
        stock_values = request.POST.getlist('stock')
        
        # Mettre à jour chaque produit
        updated = 0
        for i, product_id in enumerate(product_ids):
            try:
                product = Product.objects.get(id=product_id)
                stock = int(stock_values[i])
                if stock >= 0:  # Validation basique
                    product.stock_quantity = stock
                    product.save()
                    updated += 1
            except (Product.DoesNotExist, ValueError):
                pass
        
        messages.success(request, _("Stock mis à jour pour {} produits.").format(updated))
        return redirect('shop:dashboard:club_inventory')
    
    context = {
        'club': club,
        'products': products,
        'low_stock_products': low_stock_products,
        'current_section': 'shop_products'  # Utiliser la même section que les produits
    }
    
    return render(request, 'shop/dashboard/club/inventory.html', context)


@login_required
@club_required
def club_product_detail(request, product_id):
    """
    Afficher les détails d'un produit pour un club.
    """
    club = request.club
    # Récupérer le produit (sans filtrer par club car Product n'a pas ce champ)
    product = get_object_or_404(Product, id=product_id)
    
    # Récupérer les informations associées
    images = product.images.all().order_by('order')
    variations = product.variations.all()
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Statistiques du produit
    stats = {
        'total_sold': OrderItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0,
        'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
        'review_count': reviews.count(),
    }
    
    context = {
        'club': club,
        'product': product,
        'images': images,
        'variations': variations,
        'reviews': reviews[:5],  # Limiter à 5 avis
        'stats': stats,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/club/product_detail.html', context)


@login_required
@club_required
def club_sales_report(request):
    """
    Rapports de vente pour un club.
    """
    club = request.club
    
    # Formulaire de configuration du rapport
    form = SalesReportForm(request.GET)
    
    # Période par défaut (30 derniers jours)
    default_start_date = timezone.now() - timezone.timedelta(days=30)
    default_end_date = timezone.now()
    
    date_start = default_start_date
    date_end = default_end_date
    group_by = 'day'
    
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        group_by = form.cleaned_data.get('group_by') or 'day'
        
        # Convertir les dates en datetime avec timezone si nécessaire
        if date_start:
            # Si c'est un objet date, le convertir en datetime
            if isinstance(date_start, datetime):
                if not timezone.is_aware(date_start):
                    date_start = timezone.make_aware(date_start)
            else:
                # C'est un objet date, le convertir en datetime avec le début du jour
                date_start = timezone.make_aware(datetime.combine(date_start, datetime.min.time()))
        else:
            date_start = default_start_date
            
        if date_end:
            # Si c'est un objet date, le convertir en datetime
            if isinstance(date_end, datetime):
                if not timezone.is_aware(date_end):
                    date_end = timezone.make_aware(date_end)
            else:
                # C'est un objet date, le convertir en datetime avec la fin du jour  
                date_end = timezone.make_aware(datetime.combine(date_end, datetime.max.time()))
        else:
            date_end = default_end_date
    
    # Filtre de base pour les commandes
    orders = Order.objects.filter(
        club=club,
        created_at__gte=date_start,
        created_at__lte=date_end,
    )
    
    # Statistiques générales
    total_orders = orders.count()
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    cancelled_orders = orders.filter(status='cancelled').count()
    
    completed_orders = orders.filter(status__in=['delivered', 'shipped']).count()
    
    general_stats = {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'average_order_value': orders.aggregate(avg=Avg('total'))['avg'] or 0,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'cancellation_rate': (cancelled_orders / total_orders * 100) if total_orders > 0 else 0,
        'in_progress_orders': total_orders - completed_orders - cancelled_orders,
    }
    
    # Graphique des ventes par période
    if group_by == 'day':
        trunc_func = TruncDay
    elif group_by == 'week':
        trunc_func = TruncWeek
    else:  # month
        trunc_func = TruncMonth
    
    sales_over_time = (
        orders
        .annotate(period=trunc_func('created_at'))
        .values('period')
        .annotate(
            total_orders=Count('id'),
            total_revenue=Sum('total')
        )
        .order_by('period')
    )
    
    # Formater les données pour le graphique
    chart_data = {
        'labels': [],
        'revenue': [],
        'orders': []
    }
    
    for item in sales_over_time:
        if item['period']:
            # Formater la date selon le regroupement
            if group_by == 'day':
                label = item['period'].strftime('%d/%m/%Y')
            elif group_by == 'week':
                label = f"Semaine {item['period'].strftime('%U')} - {item['period'].strftime('%Y')}"
            else:  # month
                label = item['period'].strftime('%B %Y')
            
            chart_data['labels'].append(label)
            chart_data['revenue'].append(float(item['total_revenue'] or 0))
            chart_data['orders'].append(item['total_orders'])
    
    # Meilleurs produits vendus
    top_products = (
        OrderItem.objects
        .filter(order__club=club, order__created_at__gte=date_start, order__created_at__lte=date_end)
        .values('product_name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        )
        .order_by('-total_revenue')[:10]
    )
    
    # Ajouter le pourcentage du CA total pour chaque produit
    for product in top_products:
        product['revenue_percentage'] = (product['total_revenue'] / total_sales * 100) if total_sales > 0 else 0
    
    context = {
        'club': club,
        'form': form,
        'general_stats': general_stats,
        'top_products': top_products,
        'chart_data': chart_data,
        'current_section': 'shop_reports',
        'date_start': date_start,
        'date_end': date_end,
        'group_by': group_by,
    }
    
    return render(request, 'shop/dashboard/club/sales_report.html', context)


# Vues pour le tableau de bord des fédérations
@login_required
def shop_federation_dashboard(request):
    """
    Vue principale du tableau de bord boutique pour une fédération.
    """
    federation = get_federation_from_request(request)
    if not federation:
        messages.error(request, _("Aucune fédération spécifiée ou fédération introuvable."))
        return redirect('competitions:dashboard:federations')
    
    # Statistiques récentes (30 derniers jours)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    # Clubs de la fédération
    federation_organization = getattr(federation, 'organization', None) or getattr(federation, 'as_organization', None)
    if federation_organization:
        federation_clubs = Club.objects.filter(organization=federation_organization)
    else:
        federation_clubs = []  # ou un QuerySet vide
    
    # Commandes des clubs de la fédération
    recent_orders = Order.objects.filter(
        club__in=federation_clubs,
        created_at__gte=thirty_days_ago
    )
    
    # Statistiques générales
    stats = {
        'recent_orders_count': recent_orders.count(),
        'recent_orders_total': recent_orders.aggregate(total=Sum('total'))['total'] or 0,
        'clubs_with_shop': federation_clubs.count(),  # Tous les clubs, comme has_shop n'existe pas
        'total_products': Product.objects.filter(disciplines__in=federation.disciplines.all()).count(),
    }
    
    # Classement des clubs par ventes
    top_clubs = (
        Order.objects
        .filter(club__in=federation_clubs, created_at__gte=thirty_days_ago)
        .values('club__name')
        .annotate(total_sales=Sum('total'))
        .order_by('-total_sales')[:5]
    )
    
    context = {
        'federation': federation,
        'stats': stats,
        'top_clubs': top_clubs,
        'current_section': 'shop_dashboard'
    }
    
    return render(request, 'shop/dashboard/federation/dashboard.html', context)


@login_required
@federation_required
def federation_product_catalog(request):
    """
    Gestion du catalogue de produits pour une fédération.
    """
    federation = request.federation
    
    # Tous les produits des clubs de la fédération
    federation_clubs = federation.clubs.all()
    products = Product.objects.filter(club__in=federation_clubs, is_active=True)
    
    # Filtres et tri
    # (à implémenter selon les besoins)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'federation': federation,
        'page_obj': page_obj,
        'current_section': 'federation_catalog'
    }
    
    return render(request, 'shop/dashboard/federation/product_catalog.html', context)


@login_required
def federation_orders(request):
    """
    Liste des commandes pour une fédération.
    """
    # Récupérer la fédération soit depuis la requête, soit depuis les paramètres GET
    federation = getattr(request, 'federation', None)
    if not federation:
        federation_id = request.GET.get('federation_id')
        if federation_id:
            from competitions.models import Federation
            federation = get_object_or_404(Federation, id=federation_id)
        else:
            messages.error(request, _("Aucune fédération spécifiée."))
            return redirect('competitions:dashboard:federations')
    
    # Récupérer toutes les commandes des clubs de la fédération
    club_ids = federation.affiliated_clubs.values_list('id', flat=True)
    orders = Order.objects.filter(club__id__in=club_ids).order_by('-created_at')
    
    # Filtrage
    form = OrderFilterForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        if status:
            orders = orders.filter(status=status)
        search = form.cleaned_data.get('search')
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'federation': federation,
        'orders': page_obj,
        'form': form,
        'current_section': 'shop_orders'
    }
    
    return render(request, 'shop/dashboard/federation/orders.html', context)


@login_required
def federation_product_create(request):
    """
    Création d'un produit pour une fédération.
    Les produits de fédération seront liés aux disciplines de la fédération.
    """
    # Récupérer la fédération soit depuis la requête, soit depuis les paramètres GET
    federation = getattr(request, 'federation', None)
    if not federation:
        federation_id = request.GET.get('federation_id')
        if federation_id:
            from competitions.models import Federation
            federation = get_object_or_404(Federation, id=federation_id)
        else:
            messages.error(request, _("Aucune fédération spécifiée."))
            return redirect('competitions:dashboard:federations')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            
            # Ajouter les disciplines de la fédération au produit
            federation_disciplines = federation.disciplines.all()
            product.disciplines.set(federation_disciplines)
            
            form.save_m2m()
            
            messages.success(request, _("Produit créé avec succès."))
            return redirect('shop:dashboard:federation_product_detail', product_id=product.id)
    else:
        form = ProductForm()
        # Préremplir avec les disciplines de la fédération
        form.fields['disciplines'].initial = federation.disciplines.all()
    
    context = {
        'federation': federation,
        'form': form,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/federation/product_form.html', context)


@login_required
@federation_required
def federation_product_detail(request, product_id):
    """
    Détail d'un produit de fédération.
    Un produit appartient à une fédération s'il est associé à l'une de ses disciplines.
    """
    federation = request.federation
    product = get_object_or_404(
        Product, 
        id=product_id, 
        disciplines__in=federation.disciplines.all()
    )
    
    # Statistiques du produit
    stats = {
        'total_sold': OrderItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0,
        'total_revenue': OrderItem.objects.filter(product=product).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0,
        'in_stock': product.stock_quantity,
    }
    
    # Avis récents
    recent_reviews = product.reviews.filter(is_approved=True).order_by('-created_at')[:5]
    
    context = {
        'federation': federation,
        'product': product,
        'stats': stats,
        'recent_reviews': recent_reviews,
        'current_section': 'shop_products'
    }
    
    return render(request, 'shop/dashboard/federation/product_detail.html', context)


@login_required
@federation_required
def federation_sales_report(request):
    """
    Rapports de vente au niveau de la fédération.
    """
    federation = request.federation
    federation_clubs = federation.clubs.all()
    
    # Formulaire de configuration du rapport
    form = SalesReportForm(request.GET)
    
    # Période par défaut (30 derniers jours)
    default_start_date = timezone.now() - timezone.timedelta(days=30)
    default_end_date = timezone.now()
    
    date_start = default_start_date
    date_end = default_end_date
    group_by = 'day'
    
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start') or default_start_date
        date_end = form.cleaned_data.get('date_end') or default_end_date
        group_by = form.cleaned_data.get('group_by') or 'day'
    
    # Filtre de base pour les commandes
    orders = Order.objects.filter(
        club__in=federation_clubs,
        created_at__gte=date_start,
        created_at__lte=date_end,
    )
    
    # Statistiques générales
    general_stats = {
        'total_orders': orders.count(),
        'total_sales': orders.aggregate(total=Sum('total'))['total'] or 0,
        'average_order_value': orders.aggregate(avg=Avg('total'))['avg'] or 0,
        'active_clubs': federation_clubs.count(),  # Tous les clubs, comme has_shop n'existe pas
    }
    
    # Performance par club
    club_performance = (
        orders
        .values('club__name')
        .annotate(
            total_orders=Count('id'),
            total_sales=Sum('total'),
            avg_order_value=Avg('total')
        )
        .order_by('-total_sales')
    )
    
    context = {
        'federation': federation,
        'form': form,
        'general_stats': general_stats,
        'club_performance': club_performance,
        'current_section': 'federation_reports',
        'date_start': date_start,
        'date_end': date_end,
    }
    
    return render(request, 'shop/dashboard/federation/sales_report.html', context)