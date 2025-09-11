from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from apps.finances.models import AccountingCategory, FinancialAccount, MembershipFee


class AccountingCategoryForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour une catégorie comptable.
    """
    
    class Meta:
        model = AccountingCategory
        fields = ['name', 'type', 'description', 'code', 'parent', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Construire la queryset de base pour le parent
        parent_qs = AccountingCategory.objects.all()

        # Exclure la catégorie actuelle et ses enfants en cas d'édition
        if self.instance.pk:
            parent_qs = parent_qs.exclude(pk=self.instance.pk).exclude(parent=self.instance)

        # Restreindre au type sélectionné si disponible (POST) ou au type de l'instance (GET)
        current_type = None
        if self.is_bound:
            current_type = self.data.get('type') or None
        else:
            current_type = getattr(self.instance, 'type', None)
        if current_type:
            parent_qs = parent_qs.filter(type=current_type)

        # Restreindre à l'organisation si fournie
        if self.organization is not None:
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(self.organization.__class__)
            parent_qs = parent_qs.filter(
                models.Q(organization_content_type__isnull=True, organization_id__isnull=True) |
                models.Q(organization_content_type=ct, organization_id=str(self.organization.pk))
            )

        self.fields['parent'].queryset = parent_qs.order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        
        # Vérifier que le parent est du mÃªme type que la catégorie
        if parent and cleaned_data.get('type') != parent.type:
            self.add_error('parent', _("La catégorie parente doit Ãªtre du mÃªme type que cette catégorie."))
        
        # Vérifier qu'il n'y a pas de boucle dans la hiérarchie
        if parent:
            current_parent = parent
            while current_parent:
                if current_parent == self.instance:
                    self.add_error('parent', _("La hiérarchie des catégories ne peut pas contenir de boucle."))
                    break
                current_parent = current_parent.parent
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ajouter l'organisation si elle est fournie
        if self.organization and not instance.organization_id:
            instance.organization_content_type = ContentType.objects.get_for_model(self.organization)
            instance.organization_id = str(self.organization.pk)
        
        if commit:
            instance.save()
        
        return instance


class FinancialAccountForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour un compte financier.
    """
    
    class Meta:
        model = FinancialAccount
        fields = ['name', 'type', 'description', 'currency', 'opening_balance', 
                  'is_active', 'is_default', 'bank_name', 'account_number', 'iban', 'bic']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'opening_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        
        # Si c'est une mise Ã  jour, désactiver le solde d'ouverture
        if self.instance.pk:
            self.fields['opening_balance'].disabled = True
            self.fields['opening_balance'].help_text = _("Le solde d'ouverture ne peut pas Ãªtre modifié après la création.")
    
    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        
        # Si c'est une mise Ã  jour et que le solde d'ouverture a été modifié, restaurer la valeur d'origine
        if self.instance.pk and 'opening_balance' in self.changed_data:
            cleaned_data['opening_balance'] = self.instance.opening_balance
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ajouter le propriétaire du compte si fourni
        if self.owner and not instance.owner_id:
            instance.owner_content_type = ContentType.objects.get_for_model(self.owner)
            instance.owner_id = str(self.owner.pk)
        
        if commit:
            instance.save()
        
        return instance


class MembershipFeeForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre Ã  jour une configuration de cotisation.
    """
    
    class Meta:
        model = MembershipFee
        fields = ['name', 'description', 'amount', 'currency', 'period', 
                  'start_date', 'end_date', 'grace_period_days', 'is_active', 
                  'is_prorated', 'member_type', 'age_min', 'age_max', 
                  'accounting_category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'grace_period_days': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les catégories comptables pour n'afficher que les revenus
        self.fields['accounting_category'].queryset = AccountingCategory.objects.filter(
            type='income', is_active=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Valider les dates
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _("La date de fin doit Ãªtre postérieure ou égale Ã  la date de début."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ajouter l'organisation si elle est fournie
        if self.organization and not instance.organization_id:
            instance.organization_content_type = ContentType.objects.get_for_model(self.organization)
            instance.organization_id = str(self.organization.pk)
        
        if commit:
            instance.save()
        
        return instance

