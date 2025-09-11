from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from apps.finances.models import PaymentMethod, PaymentAttempt, Transaction


class PaymentMethodForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour une méthode de paiement.
    """
    
    class Meta:
        model = PaymentMethod
        fields = ['name', 'type', 'description', 'is_active',
                  'fee_fixed', 'fee_percentage', 'api_key', 'api_secret', 'config']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'fee_fixed': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'fee_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'api_key': forms.PasswordInput(render_value=True),
            'api_secret': forms.PasswordInput(render_value=True),
            'config': forms.Textarea(attrs={'rows': 5, 'class': 'json-editor'})
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Ajouter un champ pour confirmer les données sensibles lors de la modification
        if self.instance.pk:
            self.fields['confirm_sensitive'] = forms.BooleanField(
                label=_("Confirmer la modification des données sensibles"),
                required=False,
                help_text=_("Cochez cette case pour modifier les clés API et autres données sensibles.")
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier la confirmation pour les données sensibles
        if self.instance.pk and not cleaned_data.get('confirm_sensitive'):
            # Si la confirmation n'est pas cochée, restaurer les valeurs originales
            cleaned_data['api_key'] = self.instance.api_key
            cleaned_data['api_secret'] = self.instance.api_secret
        
        # Valider le format JSON du champ config
        try:
            import json
            config = cleaned_data.get('config')
            if config and isinstance(config, str):
                json.loads(config)
        except json.JSONDecodeError:
            self.add_error('config', _("La configuration doit Ãªtre un JSON valide."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ajouter l'organisation si elle est fournie
        if self.organization and not instance.organization_id:
            from django.contrib.contenttypes.models import ContentType
            instance.organization_content_type = ContentType.objects.get_for_model(self.organization)
            instance.organization_id = str(self.organization.pk)
        
        if commit:
            instance.save()
        
        return instance


class PaymentAttemptForm(forms.ModelForm):
    """
    Formulaire pour créer une nouvelle tentative de paiement.
    """
    
    class Meta:
        model = PaymentAttempt
        fields = ['payment_method', 'amount', 'currency', 'transaction']
        widgets = {
            'transaction': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les méthodes de paiement actives uniquement
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True)
        
        # Si une facture est fournie, pré-remplir les champs
        if self.invoice:
            self.fields['amount'].initial = self.invoice.total
            self.fields['currency'].initial = self.invoice.currency
            if hasattr(self.invoice, 'transaction') and self.invoice.transaction:
                self.fields['transaction'].initial = self.invoice.transaction
                self.fields['transaction'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        amount = cleaned_data.get('amount')
        
        # Calculer les frais si une méthode de paiement est sélectionnée
        if payment_method and amount:
            fee = payment_method.calculate_fee(amount)
            cleaned_data['fee_amount'] = fee
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir le statut initial
        instance.status = 'initiated'
        
        # Calculer et définir les frais
        if instance.payment_method and instance.amount:
            instance.fee_amount = instance.payment_method.calculate_fee(instance.amount)
        
        # Enregistrer l'adresse IP et le User-Agent si disponibles
        if self.user and hasattr(self.user, 'request'):
            request = self.user.request
            instance.ip_address = request.META.get('REMOTE_ADDR')
            instance.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if commit:
            instance.save()
        
        return instance


class PaymentProcessForm(forms.Form):
    """
    Formulaire pour traiter un paiement pour une transaction existante.
    """
    transaction = forms.ModelChoiceField(
        queryset=Transaction.objects.filter(status='pending'),
        label=_("Transaction"),
        widget=forms.HiddenInput()
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        label=_("Méthode de paiement"),
        empty_label=_("Sélectionnez une méthode de paiement")
    )
    # Des champs supplémentaires seront ajoutés dynamiquement en fonction de la méthode de paiement
    
    def __init__(self, *args, **kwargs):
        transaction = kwargs.pop('transaction', None)
        payment_methods = kwargs.pop('payment_methods', None)
        super().__init__(*args, **kwargs)
        
        if transaction:
            self.fields['transaction'].initial = transaction
            self.fields['transaction'].queryset = Transaction.objects.filter(id=transaction.id)
            
            # Ajouter le montant Ã  payer en lecture seule
            self.fields['amount'] = forms.DecimalField(
                label=_("Montant"),
                initial=transaction.amount,
                disabled=True,
                widget=forms.NumberInput(attrs={'readonly': 'readonly'})
            )
            
            self.fields['currency'] = forms.CharField(
                label=_("Devise"),
                initial=transaction.currency,
                disabled=True,
                widget=forms.TextInput(attrs={'readonly': 'readonly'})
            )
        
        if payment_methods:
            self.fields['payment_method'].queryset = payment_methods
    
    def clean(self):
        cleaned_data = super().clean()
        transaction = cleaned_data.get('transaction')
        payment_method = cleaned_data.get('payment_method')
        
        # Vérifier que la transaction est toujours en attente
        if transaction and transaction.status != 'pending':
            self.add_error('transaction', _("Cette transaction n'est plus en attente de paiement."))
        
        # Calculer les frais si une méthode de paiement est sélectionnée
        if transaction and payment_method:
            fee = payment_method.calculate_fee(transaction.amount)
            self.fee_amount = fee
            self.total_with_fees = payment_method.get_total_with_fees(transaction.amount)
        
        return cleaned_data

