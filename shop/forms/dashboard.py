from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.text import slugify

from shop.models import (
    Product, ProductImage, ProductVariation, Order, Category
)


class CategoryForm(forms.ModelForm):
    """
    Formulaire pour créer rapidement une nouvelle catégorie.
    """
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Description optionnelle de la catégorie')}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Gants de boxe, Kimonos, etc.')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].empty_label = _("Aucune (catégorie principale)")
        self.fields['parent'].queryset = Category.objects.filter(parent=None)


class ProductForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification de produits.
    """
    # Champ pour créer une nouvelle catégorie à la volée
    new_category_name = forms.CharField(
        label=_("Créer une nouvelle catégorie"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Nom de la nouvelle catégorie (optionnel)')
        }),
        help_text=_("Si aucune catégorie existante ne convient, vous pouvez en créer une nouvelle ici.")
    )
    
    new_category_parent = forms.ModelChoiceField(
        label=_("Catégorie parente"),
        queryset=Category.objects.filter(parent=None),
        required=False,
        empty_label=_("Aucune (catégorie principale)"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_("Catégorie parente pour la nouvelle catégorie.")
    )

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'short_description', 'description', 'categories',
            'price', 'sale_price', 'stock_quantity', 'low_stock_threshold',
            'brand', 'supplier', 'sku', 'barcode', 'practice_level', 'disciplines',
            'is_certified', 'certification_details', 'certificate_file',
            'weight', 'length', 'width', 'height',
            'meta_title', 'meta_description', 'tags',
            'is_active', 'is_featured', 'is_new', 'tax_rate'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'product_name',
                'placeholder': _('Ex: Gants de boxe cuir 12oz')
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'product_slug',
                'placeholder': _('URL-friendly (généré automatiquement)')
            }),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'rich-text-editor'}),
            'categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8',
                'style': 'height: auto;'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Nike, Adidas, Venum...')
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Distributeur Sport, Martial Arts Shop...')
            }),
            'certification_details': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
            'price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Organiser les catégories de manière hiérarchique
        categories = Category.objects.filter(is_active=True).select_related('parent')
        choices = []
        
        # Catégories principales d'abord
        main_categories = categories.filter(parent=None).order_by('order', 'name')
        for main_cat in main_categories:
            choices.append((main_cat.id, main_cat.name))
            
            # Puis ses sous-catégories
            sub_categories = categories.filter(parent=main_cat).order_by('order', 'name')
            for sub_cat in sub_categories:
                choices.append((sub_cat.id, f"→ {sub_cat.name}"))
        
        self.fields['categories'].choices = choices
        
        # Rendre certains champs optionnels plus clairs
        self.fields['slug'].help_text = _("Laissez vide pour générer automatiquement à partir du nom du produit")
        self.fields['sku'].help_text = _("Code produit unique (ex: BOX-GANT-12OZ-001)")
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.cleaned_data.get('name', '').strip()
        
        if not slug and name:
            # Générer automatiquement le slug à partir du nom
            slug = slugify(name)
        
        # Vérifier l'unicité du slug
        if slug:
            existing_product = Product.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                existing_product = existing_product.exclude(pk=self.instance.pk)
            
            if existing_product.exists():
                # Ajouter un suffixe numérique si le slug existe déjà
                counter = 1
                original_slug = slug
                while existing_product.exists():
                    slug = f"{original_slug}-{counter}"
                    existing_product = Product.objects.filter(slug=slug)
                    if self.instance and self.instance.pk:
                        existing_product = existing_product.exclude(pk=self.instance.pk)
                    counter += 1
        
        return slug
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        sale_price = cleaned_data.get('sale_price')
        
        if sale_price and price and sale_price >= price:
            self.add_error('sale_price', _("Le prix de vente doit être inférieur au prix normal."))
        
        # Créer une nouvelle catégorie si spécifiée
        new_category_name = cleaned_data.get('new_category_name', '').strip()
        if new_category_name:
            new_category_parent = cleaned_data.get('new_category_parent')
            
            # Vérifier si la catégorie n'existe pas déjà
            existing_category = Category.objects.filter(
                name__iexact=new_category_name,
                parent=new_category_parent
            ).first()
            
            if not existing_category:
                # Créer la nouvelle catégorie
                new_category = Category.objects.create(
                    name=new_category_name,
                    parent=new_category_parent,
                    slug=slugify(new_category_name),
                    is_active=True
                )
                
                # Ajouter la nouvelle catégorie aux catégories sélectionnées
                selected_categories = list(cleaned_data.get('categories', []))
                selected_categories.append(new_category)
                cleaned_data['categories'] = selected_categories
                
            else:
                # Utiliser la catégorie existante
                selected_categories = list(cleaned_data.get('categories', []))
                if existing_category not in selected_categories:
                    selected_categories.append(existing_category)
                cleaned_data['categories'] = selected_categories
        
        return cleaned_data


# FormSets pour les images et variations de produit
ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    fields=('image', 'alt_text', 'is_main', 'order'),
    extra=1
)

ProductVariationFormSet = inlineformset_factory(
    Product, 
    ProductVariation, 
    fields=('sku', 'price_adjustment', 'stock_quantity', 'is_active', 'image'),
    extra=1
)


class OrderStatusUpdateForm(forms.ModelForm):
    """
    Formulaire pour mettre à jour le statut d'une commande.
    """
    class Meta:
        model = Order
        fields = ['status', 'tracking_number', 'admin_notes']
        widgets = {
            'admin_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Mettre à jour les dates en fonction du statut
        if 'status' in self.changed_data:
            now = timezone.now()
            
            if instance.status == 'shipped' and not instance.shipped_at:
                instance.shipped_at = now
            elif instance.status == 'delivered' and not instance.delivered_at:
                instance.delivered_at = now
            elif instance.status == 'cancelled' and not instance.cancelled_at:
                instance.cancelled_at = now
        
        if commit:
            instance.save()
        
        return instance


class OrderFilterForm(forms.Form):
    """
    Formulaire pour filtrer les commandes.
    """
    status = forms.ChoiceField(
        choices=[('', _('Tous les statuts'))] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_start = forms.DateField(
        label=_("Date de début"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_end = forms.DateField(
        label=_("Date de fin"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    min_total = forms.DecimalField(
        label=_("Montant minimum"),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    )
    max_total = forms.DecimalField(
        label=_("Montant maximum"),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    )
    search = forms.CharField(
        label=_("Recherche"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Numéro de commande, email client...")
        })
    )


class SalesReportForm(forms.Form):
    """
    Formulaire pour configurer les rapports de vente.
    """
    date_start = forms.DateField(
        label=_("Date de début"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_end = forms.DateField(
        label=_("Date de fin"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    group_by = forms.ChoiceField(
        label=_("Regrouper par"),
        choices=[
            ('day', _('Jour')),
            ('week', _('Semaine')),
            ('month', _('Mois')),
        ],
        initial='day',
        widget=forms.Select(attrs={'class': 'form-select'})
    )