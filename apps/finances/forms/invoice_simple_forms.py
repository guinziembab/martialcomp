from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.finances.models.invoices import Invoice


class SimpleInvoiceForm(forms.ModelForm):
    """
    Formulaire simplifié pour créer une facture sans les complications de content types.
    """
    
    # Champs simplifiés pour émetteur et destinataire
    issuer_name = forms.CharField(
        label=_("Nom de l'émetteur"),
        max_length=200,
        help_text=_("Nom de la personne ou organisation qui émet la facture")
    )
    
    recipient_name = forms.CharField(
        label=_("Nom du destinataire"),
        max_length=200,
        help_text=_("Nom de la personne ou organisation qui recevra la facture")
    )
    
    class Meta:
        model = Invoice
        fields = ['issued_date', 'due_date', 'notes', 'terms']
        widgets = {
            'issued_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Notes additionnelles pour cette facture...')
            }),
            'terms': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Conditions de paiement et termes...')
            }),
        }
        labels = {
            'issued_date': _('Date d\'émission'),
            'due_date': _('Date d\'échéance'),
            'notes': _('Notes'),
            'terms': _('Conditions de paiement'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Définir des valeurs par défaut pour les nouvelles factures
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['issued_date'].initial = today
            self.fields['due_date'].initial = today + timezone.timedelta(days=30)
            
            # Termes par défaut
            self.fields['terms'].initial = _(
                "Paiement dÃ» sous 30 jours Ã  compter de la date d'émission. "
                "Pénalités de retard applicables selon les conditions générales."
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir des content types par défaut si nécessaire
        if not instance.issuer_content_type_id:
            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth.models import User
            
            try:
                from apps.organizations.models import Organization
                org_ct = ContentType.objects.get_for_model(Organization)
                user_ct = ContentType.objects.get_for_model(User)
                
                # Utiliser le premier organization disponible ou l'utilisateur
                try:
                    first_org = Organization.objects.first()
                    if first_org:
                        instance.issuer_content_type = org_ct
                        instance.issuer_object_id = str(first_org.id)
                        instance.recipient_content_type = org_ct
                        instance.recipient_object_id = str(first_org.id)
                    else:
                        raise Organization.DoesNotExist()
                except Organization.DoesNotExist:
                    # Fallback to user
                    instance.issuer_content_type = user_ct
                    instance.issuer_object_id = str(self.user.id if self.user else 1)
                    instance.recipient_content_type = user_ct
                    instance.recipient_object_id = str(self.user.id if self.user else 1)
                    
            except Exception as e:
                # Dernier recours - utiliser User
                user_ct = ContentType.objects.get_for_model(User)
                instance.issuer_content_type = user_ct
                instance.issuer_object_id = str(self.user.id if self.user else 1)
                instance.recipient_content_type = user_ct
                instance.recipient_object_id = str(self.user.id if self.user else 1)
        
        # Définir les champs de création
        if self.user:
            if not instance.pk:  # Nouvelle facture
                instance.created_by = self.user
            instance.updated_by = self.user
        
        if commit:
            instance.save()
        
        return instance

