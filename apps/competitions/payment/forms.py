from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .models import (
    OrganizationPaymentCapability, PaymentGatewayConfig, 
    RegionalPaymentConfig, CountryPaymentConfig
)


class PaymentCapabilityForm(forms.Form):
    """Formulaire pour évaluer les capacités de paiement d'une organisation"""
    
    # Questions sur les capacités financières
    has_merchant_account = forms.BooleanField(
        required=False,
        label=_("Avez-vous un compte marchand (Stripe, PayPal, etc.) ?"),
        help_text=_("Un compte marchand vous permet d'accepter les paiements par carte directement.")
    )
    
    has_bank_account = forms.BooleanField(
        required=False,
        label=_("Avez-vous un compte bancaire professionnel ?"),
        help_text=_("Un compte bancaire vous permet d'accepter les virements bancaires.")
    )
    
    can_use_payment_links = forms.BooleanField(
        required=False,
        label=_("Pouvez-vous utiliser des liens de paiement ?"),
        help_text=_("Les liens de paiement permettent de recevoir des paiements sans intégration technique.")
    )
    
    has_mobile_money = forms.BooleanField(
        required=False,
        label=_("Utilisez-vous des solutions de paiement mobile ?"),
        help_text=_("Orange Money, M-Pesa, MTN Mobile Money, etc.")
    )
    
    has_digital_wallet = forms.BooleanField(
        required=False,
        label=_("Utilisez-vous des portefeuilles numériques ?"),
        help_text=_("PayPal, Alipay, WeChat Pay, etc.")
    )
    
    has_financial_partner = forms.BooleanField(
        required=False,
        label=_("Avez-vous un partenaire financier local ?"),
        help_text=_("Banque locale, agence de transfert, etc.")
    )
    
    # Questions sur les méthodes de paiement acceptées
    can_accept_card_payments = forms.BooleanField(
        required=False,
        label=_("Pouvez-vous accepter les paiements par carte ?"),
        help_text=_("Visa, Mastercard, etc.")
    )
    
    can_accept_bank_transfers = forms.BooleanField(
        required=False,
        label=_("Pouvez-vous accepter les virements bancaires ?"),
        help_text=_("Transferts directs vers votre compte bancaire.")
    )
    
    can_accept_mobile_money = forms.BooleanField(
        required=False,
        label=_("Pouvez-vous accepter les paiements mobile money ?"),
        help_text=_("Orange Money, M-Pesa, etc.")
    )
    
    can_accept_manual_payments = forms.BooleanField(
        required=False,
        label=_("Pouvez-vous gérer les paiements manuels ?"),
        help_text=_("Paiements en espèces, chèques, etc.")
    )
    
    # Informations détaillées
    mobile_money_providers = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('ORANGE_MONEY', 'Orange Money'),
            ('MTN_MOBILE_MONEY', 'MTN Mobile Money'),
            ('AIRTEL_MONEY', 'Airtel Money'),
            ('M_PESA', 'M-Pesa'),
            ('WAVE', 'Wave'),
            ('MOOV_MONEY', 'Moov Money'),
            ('VODAFONE_CASH', 'Vodafone Cash'),
            ('OTHER', 'Autre'),
        ],
        widget=forms.CheckboxSelectMultiple,
        label=_("Quels fournisseurs de mobile money utilisez-vous ?"),
        help_text=_("Sélectionnez tous les fournisseurs que vous utilisez.")
    )
    
    bank_account_info = forms.JSONField(
        required=False,
        label=_("Informations bancaires"),
        help_text=_("Informations sur votre compte bancaire (optionnel)"),
        widget=forms.HiddenInput
    )
    
    mobile_money_info = forms.JSONField(
        required=False,
        label=_("Informations mobile money"),
        help_text=_("Informations sur votre compte mobile money (optionnel)"),
        widget=forms.HiddenInput
    )
    
    financial_partner_info = forms.JSONField(
        required=False,
        label=_("Informations partenaire financier"),
        help_text=_("Informations sur votre partenaire financier (optionnel)"),
        widget=forms.HiddenInput
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation logique
        has_mobile_money = cleaned_data.get('has_mobile_money')
        mobile_money_providers = cleaned_data.get('mobile_money_providers')
        
        if has_mobile_money and not mobile_money_providers:
            self.add_error('mobile_money_providers', 
                          _("Veuillez spécifier les fournisseurs de mobile money que vous utilisez."))
        
        return cleaned_data


class PaymentGatewayConfigForm(forms.ModelForm):
    """Formulaire pour configurer une passerelle de paiement"""
    
    class Meta:
        model = PaymentGatewayConfig
        fields = ['provider', 'display_name', 'is_active', 'is_default', 'config_data']
        widgets = {
            'config_data': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter des choix pour les fournisseurs
        self.fields['provider'].choices = [
            ('STRIPE', 'Stripe'),
            ('PAYPAL', 'PayPal'),
            ('ORANGE_MONEY', 'Orange Money'),
            ('MTN_MOBILE_MONEY', 'MTN Mobile Money'),
            ('AIRTEL_MONEY', 'Airtel Money'),
            ('M_PESA', 'M-Pesa'),
            ('WAVE', 'Wave'),
            ('MOOV_MONEY', 'Moov Money'),
            ('VODAFONE_CASH', 'Vodafone Cash'),
            ('ALIPAY', 'Alipay'),
            ('WECHAT_PAY', 'WeChat Pay'),
            ('FAWRY', 'Fawry'),
            ('STC_PAY', 'STC Pay'),
            ('BANK_TRANSFER', 'Virement bancaire'),
            ('MANUAL', 'Paiement manuel'),
            ('CARD', 'Carte bancaire'),
        ]
        
        # Aide pour les champs
        self.fields['display_name'].help_text = _("Nom affiché aux utilisateurs (ex: 'Paiement par Orange Money')")
        self.fields['is_default'].help_text = _("Cette méthode sera proposée en premier aux utilisateurs")
        self.fields['config_data'].help_text = _("Configuration JSON spécifique au fournisseur (optionnel)")
    
    def clean_config_data(self):
        config_data = self.cleaned_data.get('config_data')
        if config_data:
            try:
                if isinstance(config_data, str):
                    import json
                    json.loads(config_data)
            except (ValueError, TypeError):
                raise forms.ValidationError(_("Le format JSON n'est pas valide."))
        return config_data


class RefundForm(forms.Form):
    """Formulaire pour demander un remboursement"""
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        label=_("Montant du remboursement"),
        help_text=_("Montant Ã  rembourser (ne peut pas dépasser le montant original)")
    )
    
    reason = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_("Raison du remboursement"),
        help_text=_("Expliquez pourquoi ce remboursement est nécessaire"),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        max_amount = kwargs.pop('max_amount', None)
        super().__init__(*args, **kwargs)
        
        if max_amount:
            self.fields['amount'].validators.append(MaxValueValidator(max_amount))
            self.fields['amount'].help_text = f"Montant maximum: {max_amount}"


class RegionalConfigForm(forms.ModelForm):
    """Formulaire pour configurer les paramètres régionaux"""
    
    class Meta:
        model = RegionalPaymentConfig
        fields = [
            'default_currency', 'available_currencies', 'enabled_payment_methods',
            'pricing_tier', 'transaction_fee_percentage', 'fixed_transaction_fee',
            'config_data'
        ]
        widgets = {
            'available_currencies': forms.TextInput(attrs={'placeholder': 'EUR,USD,GBP'}),
            'enabled_payment_methods': forms.TextInput(attrs={'placeholder': 'CARD,BANK_TRANSFER,PAYPAL'}),
            'config_data': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        }
    
    def clean_available_currencies(self):
        currencies = self.cleaned_data.get('available_currencies')
        if isinstance(currencies, str):
            # Convertir la chaÃ®ne en liste
            currencies = [c.strip() for c in currencies.split(',') if c.strip()]
        return currencies
    
    def clean_enabled_payment_methods(self):
        methods = self.cleaned_data.get('enabled_payment_methods')
        if isinstance(methods, str):
            # Convertir la chaÃ®ne en liste
            methods = [m.strip() for m in methods.split(',') if m.strip()]
        return methods


class CountryConfigForm(forms.ModelForm):
    """Formulaire pour configurer les paramètres par pays"""
    
    class Meta:
        model = CountryPaymentConfig
        fields = [
            'country_name', 'default_currency', 'primary_payment_methods',
            'secondary_payment_methods', 'vat_rate', 'requires_tax_id',
            'tax_id_format', 'config_data'
        ]
        widgets = {
            'primary_payment_methods': forms.TextInput(attrs={'placeholder': 'CARD,BANK_TRANSFER'}),
            'secondary_payment_methods': forms.TextInput(attrs={'placeholder': 'PAYPAL,MANUAL'}),
            'config_data': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        }
    
    def clean_primary_payment_methods(self):
        methods = self.cleaned_data.get('primary_payment_methods')
        if isinstance(methods, str):
            # Convertir la chaÃ®ne en liste
            methods = [m.strip() for m in methods.split(',') if m.strip()]
        return methods
    
    def clean_secondary_payment_methods(self):
        methods = self.cleaned_data.get('secondary_payment_methods')
        if isinstance(methods, str):
            # Convertir la chaÃ®ne en liste
            methods = [m.strip() for m in methods.split(',') if m.strip()]
        return methods


class PaymentSearchForm(forms.Form):
    """Formulaire de recherche pour les paiements"""
    
    STATUS_CHOICES = [
        ('', _('Tous les statuts')),
        ('PENDING', _('En attente')),
        ('PROCESSING', _('En cours de traitement')),
        ('SUCCESS', _('Succès')),
        ('FAILED', _('Ã‰choué')),
        ('CANCELLED', _('Annulé')),
        ('EXPIRED', _('Expiré')),
    ]
    
    METHOD_CHOICES = [
        ('', _('Toutes les méthodes')),
        ('CARD', _('Carte bancaire')),
        ('BANK_TRANSFER', _('Virement bancaire')),
        ('PAYPAL', _('PayPal')),
        ('ORANGE_MONEY', _('Orange Money')),
        ('MTN_MOBILE_MONEY', _('MTN Mobile Money')),
        ('MANUAL', _('Paiement manuel')),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label=_("Statut")
    )
    
    payment_method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        label=_("Méthode de paiement")
    )
    
    date_from = forms.DateField(
        required=False,
        label=_("Date de début"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        label=_("Date de fin"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    amount_min = forms.DecimalField(
        required=False,
        label=_("Montant minimum"),
        min_value=0
    )
    
    amount_max = forms.DecimalField(
        required=False,
        label=_("Montant maximum"),
        min_value=0
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_("La date de début doit Ãªtre antérieure Ã  la date de fin."))
        
        if amount_min and amount_max and amount_min > amount_max:
            raise forms.ValidationError(_("Le montant minimum ne peut pas Ãªtre supérieur au montant maximum."))
        
        return cleaned_data


class ManualPaymentForm(forms.Form):
    """Formulaire pour enregistrer un paiement manuel"""
    
    payment_method = forms.ChoiceField(
        choices=[
            ('CASH', _('Espèces')),
            ('CHECK', _('Chèque')),
            ('BANK_TRANSFER', _('Virement bancaire')),
            ('MOBILE_MONEY', _('Mobile Money')),
            ('OTHER', _('Autre')),
        ],
        label=_("Méthode de paiement")
    )
    
    payment_reference = forms.CharField(
        max_length=100,
        required=False,
        label=_("Référence du paiement"),
        help_text=_("Numéro de chèque, référence de virement, etc.")
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        label=_("Montant")
    )
    
    currency = forms.ChoiceField(
        choices=[
            ('EUR', 'EUR'),
            ('USD', 'USD'),
            ('GBP', 'GBP'),
            ('XOF', 'XOF'),
            ('XAF', 'XAF'),
            ('MAD', 'MAD'),
            ('EGP', 'EGP'),
        ],
        label=_("Devise")
    )
    
    payment_date = forms.DateTimeField(
        required=False,
        label=_("Date du paiement"),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text=_("Date et heure du paiement (optionnel)")
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_("Notes"),
        help_text=_("Informations supplémentaires sur le paiement")
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('payment_date'):
            from django.utils import timezone
            self.initial['payment_date'] = timezone.now() 
