from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Sum
from decimal import Decimal

from apps.shop.models import Product, ProductVariation, Cart, CartItem, Coupon
from apps.shop.forms.cart import CartAddProductForm, CouponApplyForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


def get_cart(request):
    """
    Fonction utilitaire pour obtenir ou créer le panier de l'utilisateur.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            converted_to_order=False,
            defaults={'session_id': None}
        )
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
            
        cart, created = Cart.objects.get_or_create(
            session_id=session_id,
            converted_to_order=False,
            defaults={'user': None}
        )
    
    return cart


def cart_detail(request):
    """
    Affiche le contenu du panier avec options de modification.
    """
    cart = get_cart(request)
    cart_items = cart.items.select_related('product', 'variation').order_by('product__name')
    
    # Vérifier les disponibilités des produits
    for item in cart_items:
        if item.variation:
            item.is_available = item.variation.stock_quantity >= item.quantity
        else:
            item.is_available = item.product.stock_quantity >= item.quantity
    
    # Formulaire pour appliquer un coupon
    coupon_form = CouponApplyForm()
    
    # Récupérer les informations de coupon appliqué
    coupon_id = request.session.get('coupon_id')
    coupon = None
    discount = Decimal('0.00')
    
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            if coupon.is_valid:
                discount = coupon.get_discount_amount(cart.subtotal)
            else:
                # Supprimer le coupon s'il n'est plus valide
                del request.session['coupon_id']
                messages.warning(request, _("Le coupon appliqué n'est plus valide."))
        except Coupon.DoesNotExist:
            # Supprimer le coupon s'il n'existe plus
            del request.session['coupon_id']
    
    # Calculer les totaux
    subtotal = cart.subtotal
    total = subtotal - discount
    
    # Vous pouvez ajouter ici les frais de livraison estimés, taxes, etc.
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'coupon_form': coupon_form,
        'coupon': coupon,
    }
    
    return render(request, 'shop/cart/cart_detail.html', context)


def cart_summary(request):
    """
    Affiche un résumé rapide du panier (utilisé dans le mini-panier).
    """
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': cart.subtotal,
    }
    
    return render(request, 'shop/cart/cart_summary.html', context)


def add_to_cart(request):
    """
    Ajoute un produit au panier.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')}, status=405)
    
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        product_id = form.cleaned_data['product_id']
        variation_id = form.cleaned_data['variation_id']
        quantity = form.cleaned_data['quantity']
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Vérifier si une variation est spécifiée
            variation = None
            if variation_id:
                variation = ProductVariation.objects.get(id=variation_id, product=product, is_active=True)
                
                # Vérifier le stock de la variation
                if variation.stock_quantity < quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': _('Stock insuffisant pour cette variation.')
                    }, status=400)
            else:
                # Vérifier le stock du produit
                if product.stock_quantity < quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': _('Stock insuffisant pour ce produit.')
                    }, status=400)
            
            # Ajouter au panier
            cart = get_cart(request)
            cart_item = cart.add_item(product, quantity, variation)
            
            # Retourner la réponse
            return JsonResponse({
                'status': 'success',
                'message': _('Produit ajouté au panier'),
                'cart_count': cart.total_quantity,
                'cart_subtotal': float(cart.subtotal),
            })
            
        except (Product.DoesNotExist, ProductVariation.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': _('Produit ou variation introuvable')
            }, status=404)
    
    return JsonResponse({
        'status': 'error',
        'message': _('Formulaire invalide'),
        'errors': form.errors
    }, status=400)


def update_cart(request):
    """
    Met Ã  jour les quantités des articles du panier.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')}, status=405)
    
    cart = get_cart(request)
    
    try:
        item_id = int(request.POST.get('item_id'))
        quantity = int(request.POST.get('quantity'))
        
        if quantity < 1:
            return JsonResponse({'status': 'error', 'message': _('Quantité invalide')}, status=400)
        
        # Mettre Ã  jour la quantité
        success = cart.update_item_quantity(item_id, quantity)
        
        if not success:
            return JsonResponse({'status': 'error', 'message': _('Article introuvable')}, status=404)
        
        # Recalculer les totaux pour la réponse
        subtotal = cart.subtotal
        
        # Appliquer la réduction du coupon si présent
        discount = Decimal('0.00')
        coupon_id = request.session.get('coupon_id')
        
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                if coupon.is_valid:
                    discount = coupon.get_discount_amount(subtotal)
            except Coupon.DoesNotExist:
                pass
        
        total = subtotal - discount
        
        return JsonResponse({
            'status': 'success',
            'message': _('Panier mis Ã  jour'),
            'cart_count': cart.total_quantity,
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(total),
        })
        
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': _('Paramètres invalides')}, status=400)


def remove_from_cart(request, item_id):
    """
    Supprime un article du panier.
    """
    cart = get_cart(request)
    
    try:
        # Trouver l'article du panier
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        messages.success(request, _('Article supprimé du panier.'))
        return redirect('shop:cart:detail')
        
    except CartItem.DoesNotExist:
        messages.error(request, _('Article introuvable.'))
        return redirect('shop:cart:detail')


def clear_cart(request):
    """
    Vide complètement le panier.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')}, status=405)
    
    cart = get_cart(request)
    cart.clear()
    
    # Supprimer également le coupon appliqué
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
    
    messages.success(request, _('Votre panier a été vidé.'))
    
    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'message': _('Panier vidé'),
            'cart_count': 0,
            'subtotal': 0,
        })
    
    return redirect('shop:cart:detail')


def apply_coupon(request):
    """
    Applique un code promo au panier.
    """
    if request.method != 'POST':
        return redirect('shop:cart:detail')
    
    form = CouponApplyForm(request.POST)
    
    if form.is_valid():
        code = form.cleaned_data['code']
        
        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            
            # Vérifier la validité du coupon
            if not coupon.is_valid:
                messages.error(request, _('Ce coupon n\'est plus valide.'))
                return redirect('shop:cart:detail')
            
            # Vérifier les conditions d'application
            cart = get_cart(request)
            
            # Vérifier le montant minimum d'achat
            if coupon.min_purchase_amount and cart.subtotal < coupon.min_purchase_amount:
                messages.error(
                    request, 
                    _('Ce coupon nécessite un montant minimum d\'achat de {}.').format(coupon.min_purchase_amount)
                )
                return redirect('shop:cart:detail')
            
            # Vérifier si c'est la première commande (si requis)
            if coupon.is_for_first_order and request.user.is_authenticated:
                if request.user.orders.filter(is_paid=True).exists():
                    messages.error(request, _('Ce coupon est réservé aux premières commandes.'))
                    return redirect('shop:cart:detail')
            
            # Appliquer le coupon
            request.session['coupon_id'] = coupon.id
            messages.success(request, _('Coupon appliqué avec succès!'))
            
        except Coupon.DoesNotExist:
            messages.error(request, _('Ce code promo n\'existe pas ou n\'est plus valide.'))
    
    return redirect('shop:cart:detail')


def remove_coupon(request):
    """
    Supprime le coupon appliqué au panier.
    """
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.success(request, _('Coupon supprimé.'))
    
    return redirect('shop:cart:detail')

