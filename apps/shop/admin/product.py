from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from apps.shop.models import Product, ProductImage, ProductVariation, ProductAttributeValue


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main', 'order')
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('order')


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ('attribute_value', )
    

class ProductVariationInline(admin.StackedInline):
    model = ProductVariation
    extra = 0
    fields = ('sku', 'price_adjustment', 'stock_quantity', 'is_active', 'image')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('attributes')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_category', 'price_display', 'stock_status', 'organization', 'is_public', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'is_new', 'is_certified', 'is_public', 'organization', 'categories', 'brand')
    search_fields = ('name', 'description', 'short_description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('name', 'slug', 'short_description', 'description', 'categories')
        }),
        (_("Prix et stock"), {
            'fields': ('price', 'sale_price', 'stock_quantity', 'low_stock_threshold', 'tax_rate')
        }),
        (_("Caractéristiques"), {
            'fields': ('sku', 'barcode', 'brand', 'supplier', 'practice_level', 'disciplines')
        }),
        (_("Certifications"), {
            'fields': ('is_certified', 'certification_details', 'certificate_file'),
            'classes': ('collapse',),
        }),
        (_("Dimensions et poids"), {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',),
        }),
        (_("Métadonnées SEO"), {
            'fields': ('meta_title', 'meta_description', 'tags'),
            'classes': ('collapse',),
        }),
        (_("Organisation et visibilité"), {
            'fields': ('organization', 'is_public'),
        }),
        (_("Statut et affichage"), {
            'fields': ('is_active', 'is_featured', 'is_new'),
        }),
    )
    
    inlines = [ProductImageInline, ProductVariationInline]
    filter_horizontal = ('disciplines',)
    
    def price_display(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="text-decoration: line-through">{}</span> <span style="color: red; font-weight: bold">{}</span>',
                f"{obj.price} â‚¬", f"{obj.sale_price} â‚¬"
            )
        return f"{obj.price} â‚¬"
    price_display.short_description = _("Prix")
    
    def stock_status(self, obj):
        if not obj.is_in_stock:
            return format_html('<span style="color: red">â¨¯ {}</span>', _("Ã‰puisé"))
        elif obj.is_low_stock:
            return format_html('<span style="color: orange">âš  {}</span>', _("Stock bas"))
        else:
            return format_html('<span style="color: green">âœ“ {}</span>', _("En stock"))
    stock_status.short_description = _("Stock")
    
    def main_category(self, obj):
        """Affiche la première catégorie du produit."""
        category = obj.categories.first()
        return category.name if category else "-"
    main_category.short_description = _("Catégorie principale")
    
    list_editable = ('is_active', 'is_featured', 'is_public')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            'brand', 'organization'
        ).prefetch_related('categories')
        if not request.user.is_superuser:
            from apps.competitions.models.users import UserProfile
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.organization:
                    return qs.filter(organization=profile.organization)
            except UserProfile.DoesNotExist:
                pass
        return qs


@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'get_attributes', 'price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'product__categories')
    search_fields = ('sku', 'product__name')
    list_editable = ('stock_quantity', 'is_active')
    
    inlines = [ProductAttributeValueInline]
    
    def get_attributes(self, obj):
        attributes = obj.productattributevalue_set.all()
        if not attributes:
            return "-"
        return ", ".join([str(attr) for attr in attributes])
    get_attributes.short_description = _("Attributs")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product').prefetch_related('productattributevalue_set', 'productattributevalue_set__attribute_value', 'productattributevalue_set__attribute_value__attribute_type')


