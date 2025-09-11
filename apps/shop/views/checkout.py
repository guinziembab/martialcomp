from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import JsonResponse
from django.conf import settings

from django.utils import timezone
from apps.shop.models import Cart, CartItem, Order, OrderItem, Address
from apps.shop.forms.checkout import CheckoutForm, ShippingAddressForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def checkout_view(request):
    """
    Page principale du processus de checkout.
    """
    # Vérifier que le panier n'est pas vide
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.warning(request, _("Votre panier est vide. Ajoutez des produits avant de procéder au paiement."))
        return redirect('shop:cart:detail')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Créer une nouvelle commande
            order = Order.objects.create(
                user=request.user,
                shipping_address=form.cleaned_data['shipping_address'],
                shipping_method=form.cleaned_data['shipping_method'],
                payment_method=form.cleaned_data['payment_method'],
                status='pending',
                total=cart.get_total_price(),
                subtotal=cart.get_subtotal(),
                shipping_cost=form.cleaned_data.get('shipping_cost', 0),
                # Autres champs comme discount, etc.
            )
            
            # Copier les articles du panier vers la commande
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku if hasattr(cart_item.product, 'sku') else '',
                    variation=cart_item.variation if hasattr(cart_item, 'variation') else None,
                    variation_description=cart_item.variation.name if hasattr(cart_item, 'variation') and cart_item.variation else '',
                    quantity=cart_item.quantity,
                    price=cart_item.get_unit_price(),
                    # Autres informations Ã  stocker
                )
            
            # Vider le panier
            cart.items.all().delete()
            
            # Rediriger vers la page de paiement
            return redirect('shop:payment_methods', order_id=order.id)
    else:
        # Initialiser le formulaire avec les données de l'utilisateur
        initial = {}
        # Récupérer l'adresse par défaut si disponible
        default_address = Address.objects.filter(user=request.user, is_default_shipping=True).first()
        if default_address:
            initial['shipping_address'] = default_address.id
        form = CheckoutForm(initial=initial, user=request.user)
    
    # Récupérer les articles du panier
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variation')
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'cart_subtotal': cart.get_subtotal(),
        'cart_total': cart.get_total_price(),
        'shipping_methods': get_available_shipping_methods(cart),
    }
    
    return render(request, 'shop/checkout/checkout.html', context)


@login_required
def shipping_address(request):
    """
    Gestion des adresses de livraison.
    """
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # L'adresse par défaut est gérée dans la méthode save() du formulaire
            address.save()
            
            messages.success(request, _("Adresse enregistrée avec succès."))
            
            # Rediriger vers le processus de checkout ou la liste des adresses
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('shop:addresses')
    else:
        form = ShippingAddressForm()
    
    context = {
        'form': form,
        'addresses': addresses,
    }
    
    return render(request, 'shop/checkout/shipping_address.html', context)


@login_required
def edit_address(request, address_id):
    """
    Modifier une adresse existante.
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            # L'adresse par défaut est gérée dans la méthode save() du formulaire
            updated_address.save()
            
            messages.success(request, _("Adresse mise Ã  jour avec succès."))
            
            # Rediriger vers le processus de checkout ou la liste des adresses
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('shop:addresses')
    else:
        form = ShippingAddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
    }
    
    return render(request, 'shop/checkout/edit_address.html', context)


@login_required
def delete_address(request, address_id):
    """
    Supprimer une adresse.
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, _("Adresse supprimée avec succès."))
        
        # Rediriger vers le processus de checkout ou la liste des adresses
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('shop:addresses')
    
    context = {
        'address': address,
    }
    
    return render(request, 'shop/checkout/delete_address.html', context)


@login_required
def order_confirmation(request, order_reference):
    """
    Page de confirmation de commande.
    """
    order = get_object_or_404(Order, order_number=order_reference, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'shop/checkout/order_confirmation.html', context)


@login_required
def update_shipping_method(request):
    """
    API pour mettre Ã  jour la méthode de livraison et recalculer les coÃ»ts.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    shipping_method = request.POST.get('shipping_method')
    if not shipping_method:
        return JsonResponse({'error': 'Shipping method required'}, status=400)
    
    # Récupérer le panier de l'utilisateur
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    
    # Calculer les frais de livraison en fonction de la méthode
    shipping_cost = calculate_shipping_cost(cart, shipping_method)
    
    # Mettre Ã  jour le total
    total = cart.get_subtotal() + shipping_cost - cart.get_discount()
    
    # Formater les montants pour l'affichage
    return JsonResponse({
        'shipping_cost': format_price(shipping_cost),
        'total': format_price(total),
    })


# Fonctions d'aide
def get_available_shipping_methods(cart):
    """
    Renvoie les méthodes de livraison disponibles pour le panier actuel.
    """
    methods = [
        {
            'id': 'standard',
            'name': _('Livraison standard'),
            'description': _('3-5 jours ouvrés'),
            'price': 5.90,
            'formatted_price': '5,90 â‚¬',
        },
        {
            'id': 'express',
            'name': _('Livraison express'),
            'description': _('1-2 jour ouvré'),
            'price': 9.90,
            'formatted_price': '9,90 â‚¬',
        },
    ]
    
    # Ajouter la livraison gratuite si le montant du panier est suffisant
    if cart.get_subtotal() >= 50:
        methods.append({
            'id': 'free',
            'name': _('Livraison gratuite'),
            'description': _('4-6 jours ouvrés'),
            'price': 0,
            'formatted_price': '0,00 â‚¬',
        })
    
    return methods


def calculate_shipping_cost(cart, shipping_method):
    """
    Calcule les frais de livraison en fonction de la méthode choisie.
    """
    if shipping_method == 'standard':
        return 5.90
    elif shipping_method == 'express':
        return 9.90
    elif shipping_method == 'free' and cart.get_subtotal() >= 50:
        return 0
    
    # Valeur par défaut
    return 5.90


def format_price(price):
    """
    Formate un prix pour l'affichage.
    """
    return f"{price:.2f} â‚¬".replace('.', ',')

