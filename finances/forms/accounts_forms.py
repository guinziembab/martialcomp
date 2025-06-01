from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from finances.models import AccountingCategory, FinancialAccount, MembershipFee


class AccountingCategoryForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre à jour une catégorie comptable.
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
        
        # Filtrer les catégories parentes pour ne pas inclure la catégorie actuelle ni ses sous-catégories
        if self.instance.pk:
            self.fields['parent'].queryset = AccountingCategory.objects.exclude(
                pk=self.instance.pk
            ).exclude(
                parent=self.instance
            )
        
        # Filtrer les catégories parentes selon le type de la catégorie courante
        if self.is_bound and self.data.get('type'):
            self.fields['parent'].queryset = self.fields['parent'].queryset.filter(
                type=self.data.get('type')
            )
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        
        # Vérifier que le parent est du même type que la catégorie
        if parent and cleaned_data.get('type') != parent.type:
            self.add_error('parent', _("La catégorie parente doit être du même type que cette catégorie."))
        
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
    Formulaire pour créer ou mettre à jour un compte financier.
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
        
        # Si c'est une mise à jour, désactiver le solde d'ouverture
        if self.instance.pk:
            self.fields['opening_balance'].disabled = True
            self.fields['opening_balance'].help_text = _("Le solde d'ouverture ne peut pas être modifié après la création.")
    
    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        
        # Si c'est une mise à jour et que le solde d'ouverture a été modifié, restaurer la valeur d'origine
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
    Formulaire pour créer ou mettre à jour une configuration de cotisation.
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
            self.add_error('end_date', _("La date de fin doit être postérieure ou égale à la date de début."))
        
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