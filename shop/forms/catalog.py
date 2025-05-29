from django import forms
from django.utils.translation import gettext_lazy as _
from shop.models import Product, Category, Brand
from competitions.models import Discipline


class ProductFilterForm(forms.Form):
    """
    Formulaire pour filtrer les produits du catalogue.
    """
    category = forms.CharField(required=False)
    brand = forms.CharField(required=False)
    practice_level = forms.ChoiceField(
        choices=[('', _('Tous niveaux'))] + Product.LEVEL_CHOICES,
        required=False
    )
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        required=False,
        empty_label=_("Toutes disciplines")
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    in_stock = forms.BooleanField(required=False)
    is_certified = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir les widgets
        self.fields['category'].widget = forms.Select(choices=[('', _('Toutes catégories'))])
        self.fields['brand'].widget = forms.Select(choices=[('', _('Toutes marques'))])
        
        # Ajouter les classes pour le stylage
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})


class ProductSearchForm(forms.Form):
    """
    Formulaire de recherche pour les produits.
    """
    q = forms.CharField(
        label=_("Rechercher"),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _("Que recherchez-vous ?"),
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label=_("Toutes catégories"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProductReviewForm(forms.Form):
    """
    Formulaire pour soumettre un avis sur un produit.
    """
    rating = forms.IntegerField(
        label=_("Note"),
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'range',
            'min': '1',
            'max': '5',
            'step': '1'
        })
    )
    title = forms.CharField(
        label=_("Titre"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    comment = forms.CharField(
        label=_("Commentaire"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    quality_rating = forms.IntegerField(
        label=_("Qualité"),
        min_value=1,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'range',
            'min': '1',
            'max': '5',
            'step': '1'
        })
    )
    value_rating = forms.IntegerField(
        label=_("Rapport qualité-prix"),
        min_value=1,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'range',
            'min': '1',
            'max': '5',
            'step': '1'
        })
    )
    durability_rating = forms.IntegerField(
        label=_("Durabilité"),
        min_value=1,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'range',
            'min': '1',
            'max': '5',
            'step': '1'
        })
    )
    # Pour l'instant, utilisons un seul champ d'image simple
    image = forms.ImageField(
        label=_("Image"),
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )