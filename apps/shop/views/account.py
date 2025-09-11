from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import datetime

from ..models.order import Order, Address
from ..models.product import Product
from ..models.reviews import ProductReview as Review
from ..forms.checkout import ShippingAddressForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def order_list(request):
    """
    Affiche la liste des commandes de l'utilisateur
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'title': _('Mes commandes'),
    }
    
    return render(request, 'shop/account/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """
    Affiche le détail d'une commande
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'title': _('Détail de la commande #{0}').format(order.order_number),
    }
    
    return render(request, 'shop/account/order_detail.html', context)


@login_required
def order_invoice(request, order_id):
    """
    Télécharge la facture d'une commande
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier que la facture existe
    if not order.invoice_pdf:
        messages.warning(request, _("La facture n'est pas encore disponible pour cette commande."))
        return redirect('shop:account:order_detail', order_id=order.id)
    
    # Retourner le fichier PDF
    response = HttpResponse(order.invoice_pdf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.invoice_number}.pdf"'
    return response


@login_required
def address_list(request):
    """
    Affiche la liste des adresses de l'utilisateur
    """
    addresses = Address.objects.filter(user=request.user)
    
    context = {
        'addresses': addresses,
        'title': _('Mes adresses'),
    }
    
    return render(request, 'shop/account/address_list.html', context)


@login_required
def address_add(request):
    """
    Ajoute une nouvelle adresse
    """
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            
            messages.success(request, _("Adresse ajoutée avec succès."))
            return redirect('shop:account:address_list')
    else:
        form = ShippingAddressForm()
    
    context = {
        'form': form,
        'title': _('Ajouter une adresse'),
    }
    
    return render(request, 'shop/account/address_form.html', context)


@login_required
def address_edit(request, address_id):
    """
    Modifie une adresse existante
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Adresse mise Ã  jour avec succès."))
            return redirect('shop:account:address_list')
    else:
        form = ShippingAddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
        'title': _('Modifier une adresse'),
    }
    
    return render(request, 'shop/account/address_form.html', context)


@login_required
def address_delete(request, address_id):
    """
    Supprime une adresse
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, _("Adresse supprimée avec succès."))
        return redirect('shop:account:address_list')
    
    context = {
        'address': address,
        'title': _('Supprimer une adresse'),
    }
    
    return render(request, 'shop/account/address_delete.html', context)


@login_required
def set_default_address(request, address_id, address_type):
    """
    Définit une adresse comme adresse par défaut
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if address_type == 'shipping':
        Address.objects.filter(user=request.user, is_default_shipping=True).update(is_default_shipping=False)
        address.is_default_shipping = True
    elif address_type == 'billing':
        Address.objects.filter(user=request.user, is_default_billing=True).update(is_default_billing=False)
        address.is_default_billing = True
    
    address.save()
    messages.success(request, _("Adresse par défaut mise Ã  jour avec succès."))
    
    return redirect('shop:account:address_list')


@login_required
def review_list(request):
    """
    Affiche la liste des avis de l'utilisateur
    """
    reviews = Review.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    
    context = {
        'reviews': reviews,
        'title': _('Mes avis'),
    }
    
    return render(request, 'shop/account/review_list.html', context)


@login_required
def review_edit(request, review_id):
    """
    Modifie un avis existant
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if not rating or not title or not comment:
            messages.error(request, _("Tous les champs sont requis."))
        else:
            review.rating = int(rating)
            review.title = title
            review.comment = comment
            review.save()
            
            messages.success(request, _("Avis mis Ã  jour avec succès."))
            return redirect('shop:account:review_list')
    
    context = {
        'review': review,
        'title': _('Modifier un avis'),
    }
    
    return render(request, 'shop/account/review_form.html', context)


@login_required
def review_delete(request, review_id):
    """
    Supprime un avis
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, _("Avis supprimé avec succès."))
        return redirect('shop:account:review_list')
    
    context = {
        'review': review,
        'title': _('Supprimer un avis'),
    }
    
    return render(request, 'shop/account/review_delete.html', context)
