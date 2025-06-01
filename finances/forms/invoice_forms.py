from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from finances.models import Invoice, InvoiceItem, AccountingCategory


class InvoiceItemForm(forms.ModelForm):
    """
    Formulaire pour un élément de facture.
    """
    
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'reference', 'category']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }
        

class InvoiceItemFormSet(forms.BaseInlineFormSet):
    """
    Formset pour les éléments de facture.
    """
    def clean(self):
        """
        Validation du formset: au moins un élément doit être présent.
        """
        super().clean()
        
        if any(self.errors):
            return
        
        if not any(form.cleaned_data and not form.cleaned_data.get('DELETE', False) 
                   for form in self.forms):
            raise forms.ValidationError(_("Au moins un élément de facture est requis."))


class InvoiceForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre à jour une facture.
    """
    
    # Champs pour faciliter la sélection des entités liées
    issuer_type = forms.ChoiceField(
        label=_("Type d'émetteur"),
        choices=[],
        required=True
    )
    issuer_id = forms.CharField(
        label=_("ID de l'émetteur"),
        widget=forms.HiddenInput(),
        required=True
    )
    
    recipient_type = forms.ChoiceField(
        label=_("Type de destinataire"),
        choices=[],
        required=True
    )
    recipient_id = forms.CharField(
        label=_("ID du destinataire"),
        widget=forms.HiddenInput(),
        required=True
    )
    
    class Meta:
        model = Invoice
        fields = ['issued_date', 'due_date', 'notes', 'terms']
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'terms': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        
        # Options pour les émetteurs et destinataires
        issuer_options = kwargs.pop('issuer_options', [])
        recipient_options = kwargs.pop('recipient_options', [])
        
        super().__init__(*args, **kwargs)
        
        # Mettre à jour les choix pour les émetteurs et destinataires
        self.fields['issuer_type'].choices = [('', _('Sélectionnez un type'))] + [
            (f"{ct.app_label}.{ct.model}|{option.pk}", option.name) 
            for ct, option in issuer_options
        ]
        
        self.fields['recipient_type'].choices = [('', _('Sélectionnez un type'))] + [
            (f"{ct.app_label}.{ct.model}|{option.pk}", option.name) 
            for ct, option in recipient_options
        ]
        
        # Si c'est une mise à jour, initialiser les champs
        if self.instance.pk:
            if self.instance.issuer_content_type and self.instance.issuer_object_id:
                issuer_type = f"{self.instance.issuer_content_type.app_label}.{self.instance.issuer_content_type.model}"
                self.fields['issuer_type'].initial = f"{issuer_type}|{self.instance.issuer_object_id}"
                self.fields['issuer_id'].initial = self.instance.issuer_object_id
            
            if self.instance.recipient_content_type and self.instance.recipient_object_id:
                recipient_type = f"{self.instance.recipient_content_type.app_label}.{self.instance.recipient_content_type.model}"
                self.fields['recipient_type'].initial = f"{recipient_type}|{self.instance.recipient_object_id}"
                self.fields['recipient_id'].initial = self.instance.recipient_object_id
        
        # Définir des valeurs par défaut pour les nouvelles factures
        if not self.instance.pk:
            self.fields['issued_date'].initial = timezone.now().date()
            self.fields['due_date'].initial = (timezone.now() + timezone.timedelta(days=30)).date()
            
            # Termes par défaut
            self.fields['terms'].initial = _("""Paiement à réception de facture.
Tout retard de paiement entraînera des pénalités de 3% du montant total.
Merci de votre confiance.""")
    
    def clean(self):
        cleaned_data = super().clean()
        issued_date = cleaned_data.get('issued_date')
        due_date = cleaned_data.get('due_date')
        
        # Valider que la date d'échéance est après ou égale à la date d'émission
        if issued_date and due_date and due_date < issued_date:
            self.add_error('due_date', _("La date d'échéance doit être postérieure ou égale à la date d'émission."))
        
        # Traiter les types d'émetteur et de destinataire
        issuer_type = cleaned_data.get('issuer_type')
        recipient_type = cleaned_data.get('recipient_type')
        
        if issuer_type:
            try:
                app_model, object_id = issuer_type.split('|')
                app_label, model = app_model.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                cleaned_data['issuer_content_type'] = content_type
                cleaned_data['issuer_object_id'] = object_id
            except (ValueError, ContentType.DoesNotExist):
                self.add_error('issuer_type', _("Type d'émetteur invalide."))
        
        if recipient_type:
            try:
                app_model, object_id = recipient_type.split('|')
                app_label, model = app_model.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                cleaned_data['recipient_content_type'] = content_type
                cleaned_data['recipient_object_id'] = object_id
            except (ValueError, ContentType.DoesNotExist):
                self.add_error('recipient_type', _("Type de destinataire invalide."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir les champs de content type
        instance.issuer_content_type = self.cleaned_data.get('issuer_content_type')
        instance.issuer_object_id = self.cleaned_data.get('issuer_object_id')
        
        instance.recipient_content_type = self.cleaned_data.get('recipient_content_type')
        instance.recipient_object_id = self.cleaned_data.get('recipient_object_id')
        
        # Définir l'utilisateur qui a créé la facture
        if self.user and not instance.created_by:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class InvoiceSearchForm(forms.Form):
    """
    Formulaire pour rechercher des factures.
    """
    PERIOD_CHOICES = [
        ('', _('Toutes les périodes')),
        ('this_month', _('Ce mois')),
        ('last_month', _('Mois dernier')),
        ('this_quarter', _('Ce trimestre')),
        ('last_quarter', _('Trimestre dernier')),
        ('this_year', _('Cette année')),
        ('last_year', _('Année dernière')),
        ('custom', _('Période personnalisée')),
    ]
    
    search = forms.CharField(
        label=_('Recherche'), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Rechercher par numéro, notes...')})
    )
    status = forms.ChoiceField(
        label=_('Statut'),
        choices=[('', _('Tous'))] + Invoice.STATUS_CHOICES,
        required=False
    )
    period = forms.ChoiceField(
        label=_('Période'),
        choices=PERIOD_CHOICES,
        required=False,
        initial='this_month'
    )
    date_from = forms.DateField(
        label=_('Date de début'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('Date de fin'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    amount_min = forms.DecimalField(
        label=_('Montant minimum'),
        required=False,
        min_value=0,
        decimal_places=2
    )
    amount_max = forms.DecimalField(
        label=_('Montant maximum'),
        required=False,
        min_value=0,
        decimal_places=2
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Valider les dates de la période personnalisée
        if period == 'custom':
            if not date_from:
                self.add_error('date_from', _('La date de début est requise pour une période personnalisée.'))
            if not date_to:
                self.add_error('date_to', _('La date de fin est requise pour une période personnalisée.'))
            elif date_from and date_to and date_from > date_to:
                self.add_error('date_to', _('La date de fin doit être postérieure à la date de début.'))
        
        return cleaned_data
    
    def get_date_range(self):
        """
        Retourne les dates de début et de fin en fonction de la période sélectionnée.
        """
        period = self.cleaned_data.get('period')
        today = timezone.now().date()
        
        if not period:
            return None, None
        
        # Si période personnalisée, utiliser les dates saisies
        if period == 'custom':
            return self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        
        # Ce mois
        if period == 'this_month':
            return today.replace(day=1), today
        
        # Mois dernier
        if period == 'last_month':
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timezone.timedelta(days=1)
            first_day_previous_month = last_day_previous_month.replace(day=1)
            return first_day_previous_month, last_day_previous_month
        
        # Ce trimestre
        if period == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            first_month_of_quarter = 3 * (quarter - 1) + 1
            first_day_of_quarter = today.replace(month=first_month_of_quarter, day=1)
            return first_day_of_quarter, today
        
        # Trimestre dernier
        if period == 'last_quarter':
            quarter = (today.month - 1) // 3 + 1
            if quarter == 1:
                # Dernier trimestre de l'année précédente
                last_quarter = 4
                year = today.year - 1
            else:
                last_quarter = quarter - 1
                year = today.year
                
            first_month_of_last_quarter = 3 * (last_quarter - 1) + 1
            first_day_of_last_quarter = today.replace(year=year, month=first_month_of_last_quarter, day=1)
            
            # Calculer le dernier jour du trimestre précédent
            if last_quarter < 4:
                first_day_of_current_quarter = today.replace(month=first_month_of_last_quarter + 3, day=1)
                last_day_of_last_quarter = first_day_of_current_quarter - timezone.timedelta(days=1)
            else:
                # Dernier jour de l'année
                last_day_of_last_quarter = today.replace(year=year, month=12, day=31)
                
            return first_day_of_last_quarter, last_day_of_last_quarter
        
        # Cette année
        if period == 'this_year':
            return today.replace(month=1, day=1), today
        
        # Année dernière
        if period == 'last_year':
            first_day_of_last_year = today.replace(year=today.year-1, month=1, day=1)
            last_day_of_last_year = today.replace(year=today.year-1, month=12, day=31)
            return first_day_of_last_year, last_day_of_last_year
        
        return None, None

# Ajouter un alias pour InvoiceFilterForm (pour la compatibilité avec les vues)
InvoiceFilterForm = InvoiceSearchForm


class InvoicePaymentForm(forms.Form):
    """
    Formulaire pour enregistrer un paiement pour une facture.
    """
    payment_method = forms.ModelChoiceField(
        queryset=None,
        label=_("Méthode de paiement"),
        empty_label=_("Sélectionnez une méthode de paiement"),
        required=True
    )
    
    notes = forms.CharField(
        label=_("Notes"),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Récupérer les méthodes de paiement actives
        from finances.models import PaymentMethod
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True)
        
        # Ajouter des informations sur les frais (seront mises à jour via JavaScript)
        self.fields['fee_amount'] = forms.DecimalField(
            label=_("Frais"),
            initial=0,
            required=False,
            widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'fee_amount'})
        )
        
        self.fields['total_with_fees'] = forms.DecimalField(
            label=_("Total avec frais"),
            initial=self.invoice.total if self.invoice else 0,
            required=False,
            widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'total_with_fees'})
        )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        if not payment_method:
            self.add_error('payment_method', _("Une méthode de paiement est requise."))
        
        return cleaned_data