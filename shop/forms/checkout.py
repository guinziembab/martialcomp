from django import forms
from django.utils.translation import gettext_lazy as _
from shop.models import Address


class CheckoutForm(forms.Form):
    """
    Formulaire pour le processus de paiement.
    """
    # Adresse de livraison
    shipping_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        label=_("Adresse de livraison")
    )
    
    # Méthode de livraison
    SHIPPING_CHOICES = [
        ('standard', _('Livraison standard (3-5 jours ouvrés)')),
        ('express', _('Livraison express (1-2 jour ouvré)')),
        ('free', _('Livraison gratuite (4-6 jours ouvrés)')),
    ]
    
    shipping_method = forms.ChoiceField(
        choices=SHIPPING_CHOICES,
        widget=forms.RadioSelect,
        label=_("Mode de livraison")
    )
    
    # Méthode de paiement
    PAYMENT_CHOICES = [
        ('card', _('Carte bancaire')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Virement bancaire')),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        label=_("Mode de paiement")
    )
    
    # Notes de commande
    order_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label=_("Notes de commande"),
        help_text=_("Instructions spéciales pour la livraison ou toute autre information")
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user is not None and user.is_authenticated:
            self.fields['shipping_address'].queryset = Address.objects.filter(user=user)
        
        # Ajouter les classes CSS pour le style
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})


class ShippingAddressForm(forms.ModelForm):
    """
    Formulaire pour la gestion des adresses de livraison.
    """
    # Ajout d'un champ pour simplifier la définition d'adresse par défaut
    is_default = forms.BooleanField(
        label=_("Définir comme adresse par défaut"), 
        required=False,
        help_text=_("Utiliser cette adresse comme adresse par défaut pour les livraisons")
    )
    
    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'company', 'address_line1', 
            'address_line2', 'postal_code', 'city', 'country', 
            'phone', 'delivery_instructions'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialiser le champ is_default avec la valeur de is_default_shipping
        if self.instance.pk:
            self.fields['is_default'].initial = self.instance.is_default_shipping
        
        # Ajouter les classes CSS pour le style
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
                
        # Rendre certains champs obligatoires
        for field_name in ['first_name', 'last_name', 'address_line1', 'postal_code', 'city', 'country']:
            self.fields[field_name].required = True
            
    def save(self, commit=True):
        address = super().save(commit=False)
        
        # Définir l'adresse par défaut pour la livraison si demandé
        if self.cleaned_data.get('is_default'):
            address.is_default_shipping = True
        
        if commit:
            address.save()
        
        return address