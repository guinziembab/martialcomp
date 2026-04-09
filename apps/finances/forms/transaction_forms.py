from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.finances.models.transactions import Transaction, TransactionCategory, TransactionAttachment
from django.db import models
from apps.finances.models.accounts import AccountingCategory


class TransactionForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour une transaction.
    """
    
    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'currency', 'date', 'description', 'category',
                  'payment_method', 'financial_account', 'practitioner', 'receipt_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.source = kwargs.pop('source', None)
        self.destination = kwargs.pop('destination', None)
        # request peut être passé par la vue
        self.request = kwargs.pop('request', None)
        
        super().__init__(*args, **kwargs)

        # Configurer le champ date pour HTML5 date input
        if 'date' in self.fields:
            self.fields['date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            # S'assurer que la valeur initiale est au bon format pour le widget HTML5
            if self.instance and self.instance.pk and self.instance.date:
                self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')

        # Filtrer les catégories et pratiquants selon l'organisation
        try:
            from django.contrib.contenttypes.models import ContentType
            from apps.finances.models.accounts import AccountingCategory
            from apps.finances.currency_service import _get_request_organization
            from apps.competitions.models import Practitioner

            # Déterminer l'organisation
            organization = None
            request = getattr(self, 'request', None)
            if request is not None:
                organization = _get_request_organization(request)

            # Filtrer les pratiquants par organisation
            if 'practitioner' in self.fields:
                if organization:
                    # Filtrer directement par l'organisation du pratiquant
                    self.fields['practitioner'].queryset = Practitioner.objects.filter(
                        organization=organization, is_active=True
                    ).order_by('last_name', 'first_name')
                else:
                    # Fallback: limiter aux 100 premiers pratiquants actifs
                    self.fields['practitioner'].queryset = Practitioner.objects.filter(
                        is_active=True
                    ).order_by('last_name', 'first_name')[:100]

                # Améliorer le widget avec recherche
                self.fields['practitioner'].widget.attrs.update({
                    'class': 'form-select select2-practitioner',
                    'data-placeholder': _('Sélectionner un membre...')
                })

            # Déterminer le type
            transaction_type = None
            if self.is_bound:
                transaction_type = self.data.get('type')
            else:
                transaction_type = getattr(self.instance, 'type', None)

            # Base queryset: catégories de transactions legacy
            tx_cat_qs = TransactionCategory.objects.filter(active=True)
            if transaction_type:
                tx_cat_qs = tx_cat_qs.filter(transaction_type__in=[transaction_type, 'both'])
            self.fields['category'].queryset = tx_cat_qs

            # Si AccountingCategory est disponible: on peut proposer un champ alternatif (non destructif)
            # On laisse 'category' tel quel pour compatibilité; mais on filtre aussi un queryset utilitaire
            acc_qs = AccountingCategory.objects.all()
            if organization:
                ct = ContentType.objects.get_for_model(organization.__class__)
                acc_qs = acc_qs.filter(
                    models.Q(organization_content_type__isnull=True, organization_id__isnull=True) |
                    models.Q(organization_content_type=ct, organization_id=str(organization.pk))
                )
            if transaction_type == 'income':
                acc_qs = acc_qs.filter(type='income')
            elif transaction_type == 'expense':
                acc_qs = acc_qs.filter(type='expense')
            # Expose pour le template si utilisé
            self.accounting_categories_qs = acc_qs.order_by('name')

            # Auto-provisionnement: si aucune TransactionCategory n'est disponible pour ce type,
            # créer des catégories de transaction à partir des AccountingCategory visibles
            if not tx_cat_qs.exists() and acc_qs.exists():
                created_any = False
                for acc in acc_qs[:50]:  # limite de sécurité
                    tc, created = TransactionCategory.objects.get_or_create(
                        name=acc.name,
                        defaults={
                            'transaction_type': 'income' if acc.type == 'income' else 'expense',
                            'description': acc.description or '',
                            'active': True,
                        }
                    )
                    created_any = created_any or created
                if created_any:
                    # Recharger le queryset
                    tx_cat_qs = TransactionCategory.objects.filter(active=True)
                    if transaction_type:
                        tx_cat_qs = tx_cat_qs.filter(transaction_type__in=[transaction_type, 'both'])
                    self.fields['category'].queryset = tx_cat_qs.order_by('name')
        except Exception:
            # Fallback initial
            if self.is_bound and self.data.get('type'):
                transaction_type = self.data.get('type')
                self.fields['category'].queryset = TransactionCategory.objects.filter(
                    transaction_type__in=[transaction_type, 'both'], active=True
                )
            else:
                self.fields['category'].queryset = TransactionCategory.objects.filter(
                    active=True
                )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ajouter les informations de l'utilisateur
        if self.user:
            if not instance.pk:  # Nouvelle transaction
                instance.created_by = self.user
            # Toujours mettre Ã  jour le updater
            instance.updated_by = self.user
        
        # Ajouter les relations source/destination
        if self.source:
            instance.source_content_type = ContentType.objects.get_for_model(self.source)
            instance.source_object_id = str(self.source.pk)
        
        if self.destination:
            instance.destination_content_type = ContentType.objects.get_for_model(self.destination)
            instance.destination_object_id = str(self.destination.pk)
        
        if commit:
            instance.save()
        
        return instance


class TransactionFilterForm(forms.Form):
    """
    Formulaire pour filtrer et rechercher des transactions.
    """
    PERIOD_CHOICES = [
        ('', _('Toutes les périodes')),
        ('today', _('Aujourd\'hui')),
        ('yesterday', _('Hier')),
        ('this_week', _('Cette semaine')),
        ('last_week', _('Semaine dernière')),
        ('this_month', _('Ce mois')),
        ('last_month', _('Mois dernier')),
        ('this_year', _('Cette année')),
        ('custom', _('Période personnalisée')),
    ]
    
    search = forms.CharField(
        label=_('Recherche'), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Rechercher par référence, description...')})
    )
    type = forms.ChoiceField(
        label=_('Type'),
        choices=[('', _('Tous'))] + Transaction.TYPE_CHOICES,
        required=False
    )
    status = forms.ChoiceField(
        label=_('Statut'),
        choices=[('', _('Tous'))] + Transaction.STATUS_CHOICES,
        required=False
    )
    category = forms.ModelChoiceField(
        label=_('Catégorie'),
        queryset=TransactionCategory.objects.filter(active=True),
        required=False,
        empty_label=_('Toutes les catégories')
    )
    period = forms.ChoiceField(
        label=_('Période'),
        choices=PERIOD_CHOICES,
        required=False,
        initial='this_month'
    )
    start_date = forms.DateField(
        label=_('Date de début'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
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
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Valider les dates de la période personnalisée
        if period == 'custom':
            if not start_date:
                self.add_error('start_date', _('La date de début est requise pour une période personnalisée.'))
            if not end_date:
                self.add_error('end_date', _('La date de fin est requise pour une période personnalisée.'))
            elif start_date and end_date and start_date > end_date:
                self.add_error('end_date', _('La date de fin doit Ãªtre postérieure Ã  la date de début.'))
        
        return cleaned_data
    
    def get_date_range(self):
        """
        Retourne les dates de début et de fin en fonction de la période sélectionnée.
        """
        period = self.cleaned_data.get('period')
        today = timezone.now().date()
        
        if period == 'today':
            return today, today
        
        elif period == 'yesterday':
            yesterday = today - timezone.timedelta(days=1)
            return yesterday, yesterday
        
        elif period == 'this_week':
            start_of_week = today - timezone.timedelta(days=today.weekday())
            return start_of_week, today
        
        elif period == 'last_week':
            start_of_last_week = today - timezone.timedelta(days=today.weekday() + 7)
            end_of_last_week = start_of_last_week + timezone.timedelta(days=6)
            return start_of_last_week, end_of_last_week
        
        elif period == 'this_month':
            start_of_month = today.replace(day=1)
            return start_of_month, today
        
        elif period == 'last_month':
            if today.month == 1:
                start_of_last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                start_of_last_month = today.replace(month=today.month-1, day=1)
            
            if today.month == 1:
                end_of_last_month = today.replace(year=today.year-1, month=12, day=31)
            else:
                # Dernier jour du mois précédent
                if today.month == 3:
                    # Février (gérer les années bissextiles)
                    if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0):
                        end_day = 29
                    else:
                        end_day = 28
                elif today.month in [5, 7, 10, 12]:
                    end_day = 30
                else:
                    end_day = 31
                
                end_of_last_month = today.replace(month=today.month-1, day=end_day)
            
            return start_of_last_month, end_of_last_month
        
        elif period == 'this_year':
            start_of_year = today.replace(month=1, day=1)
            return start_of_year, today
        
        elif period == 'custom':
            return self.cleaned_data.get('start_date'), self.cleaned_data.get('end_date')
        
        return None, None


class TransactionCategoryForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour une catégorie de transaction.
    """
    class Meta:
        model = TransactionCategory
        fields = ['name', 'transaction_type', 'description', 'parent', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Exclure l'instance actuelle et ses descendants de la liste des parents possibles
        if self.instance.pk:
            descendants = self.instance.get_descendants()
            descendants_ids = [desc.pk for desc in descendants]
            descendants_ids.append(self.instance.pk)
            
            self.fields['parent'].queryset = TransactionCategory.objects.exclude(
                pk__in=descendants_ids
            )


class TransactionAttachmentForm(forms.ModelForm):
    """
    Formulaire pour ajouter une pièce jointe Ã  une transaction.
    """
    class Meta:
        model = TransactionAttachment
        fields = ['file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': _('Description du document')}),
        }


class BulkTransactionApprovalForm(forms.Form):
    """
    Formulaire pour approuver ou rejeter plusieurs transactions en masse.
    """
    ACTION_CHOICES = [
        ('validate', _('Valider')),
        ('reject', _('Rejeter')),
    ]
    
    action = forms.ChoiceField(
        label=_('Action'),
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(),
        initial='validate'
    )
    
    transactions = forms.MultipleChoiceField(
        label=_('Transactions'),
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        error_messages={
            'required': _('Vous devez sélectionner au moins une transaction.')
        }
    )
    
    notes = forms.CharField(
        label=_('Notes'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _('Notes optionnelles sur cette action')})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer les transactions en attente
        transactions = Transaction.objects.filter(status='pending')
        
        # Créer les choix pour le champ transactions
        choices = []
        for tx in transactions:
            # Utiliser la date de transaction pour l'affichage
            date_display = tx.date.strftime('%d/%m/%Y') if tx.date else ''
            label = f"{tx.reference} - {date_display} - {tx.amount} {tx.currency} - {tx.description[:50]}"
            choices.append((str(tx.id), label))
        
        self.fields['transactions'].choices = choices

