from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from shop.models import AttributeType, AttributeValue


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ('value', 'display_value', 'color_code', 'order')


@admin.register(AttributeType)
class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'value_count')
    search_fields = ('name', 'display_name')
    inlines = [AttributeValueInline]
    
    def value_count(self, obj):
        return obj.values.count()
    value_count.short_description = _("Nombre de valeurs")
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('values')


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('display_value', 'attribute_type', 'value', 'order')
    list_filter = ('attribute_type',)
    search_fields = ('value', 'display_value')
    list_editable = ('order',)
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('attribute_type', 'value', 'display_value')
        }),
        (_("Affichage"), {
            'fields': ('color_code', 'order')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('attribute_type')