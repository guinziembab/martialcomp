from django import forms
from django.utils.translation import gettext_lazy as _


class CartAddProductForm(forms.Form):
    """
    Formulaire pour ajouter un produit au panier.
    """
    product_id = forms.IntegerField(widget=forms.HiddenInput)
    variation_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control quantity-input',
            'min': '1',
            'step': '1'
        })
    )
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError(_("La quantité doit être au moins de 1"))
        return quantity


class CouponApplyForm(forms.Form):
    """
    Formulaire pour appliquer un code promo.
    """
    code = forms.CharField(
        label=_("Code promo"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Entrez votre code promo'),
            'autocomplete': 'off'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data['code']
        return code.upper()