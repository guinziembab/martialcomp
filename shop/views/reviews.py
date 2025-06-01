from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from shop.models import Product, ProductReview
from shop.forms.catalog import ProductReviewForm

@login_required
def add_review(request, product_slug):
    """
    Ajouter un avis sur un produit
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Vérifier si l'utilisateur a déjà laissé un avis
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, _("Vous avez déjà laissé un avis pour ce produit."))
        return redirect('shop:product_detail', slug=product_slug)
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Créer l'avis
            review = ProductReview(
                product=product,
                user=request.user,
                rating=form.cleaned_data['rating'],
                title=form.cleaned_data['title'],
                comment=form.cleaned_data['comment'],
            )
            
            # Ajouter les notes détaillées si présentes
            if form.cleaned_data.get('quality_rating'):
                review.quality_rating = form.cleaned_data['quality_rating']
            if form.cleaned_data.get('value_rating'):
                review.value_rating = form.cleaned_data['value_rating']
            if form.cleaned_data.get('durability_rating'):
                review.durability_rating = form.cleaned_data['durability_rating']
                
            # Sauvegarder l'avis
            review.save()
            
            # Traiter l'image si présente
            if form.cleaned_data.get('image'):
                from shop.models import ReviewImage
                image = ReviewImage(
                    review=review,
                    image=form.cleaned_data['image']
                )
                image.save()
            
            messages.success(request, _("Votre avis a été soumis avec succès et sera publié après modération."))
            return redirect('shop:product_detail', slug=product_slug)
    else:
        form = ProductReviewForm()
    
    context = {
        'form': form,
        'product': product,
    }
    
    return render(request, 'shop/catalog/add_review.html', context)


@login_required
def edit_review(request, review_id):
    """
    Modifier un avis existant
    """
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product = review.product
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Mettre à jour l'avis
            review.rating = form.cleaned_data['rating']
            review.title = form.cleaned_data['title']
            review.comment = form.cleaned_data['comment']
            
            # Mettre à jour les notes détaillées si présentes
            if form.cleaned_data.get('quality_rating'):
                review.quality_rating = form.cleaned_data['quality_rating']
            if form.cleaned_data.get('value_rating'):
                review.value_rating = form.cleaned_data['value_rating']
            if form.cleaned_data.get('durability_rating'):
                review.durability_rating = form.cleaned_data['durability_rating']
                
            # Réinitialiser le statut de modération
            review.is_approved = False
            review.save()
            
            # Traiter l'image si présente
            if form.cleaned_data.get('image'):
                from shop.models import ReviewImage
                # Supprimer les anciennes images
                ReviewImage.objects.filter(review=review).delete()
                # Ajouter la nouvelle image
                image = ReviewImage(
                    review=review,
                    image=form.cleaned_data['image']
                )
                image.save()
            
            messages.success(request, _("Votre avis a été mis à jour avec succès et sera publié après modération."))
            return redirect('shop:product_detail', slug=product.slug)
    else:
        # Préremplir le formulaire avec les données existantes
        initial_data = {
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'quality_rating': review.quality_rating,
            'value_rating': review.value_rating,
            'durability_rating': review.durability_rating,
        }
        form = ProductReviewForm(initial=initial_data)
    
    context = {
        'form': form,
        'review': review,
        'product': product,
    }
    
    return render(request, 'shop/catalog/edit_review.html', context)