from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from shop.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_with_hierarchy', 'parent', 'products_count', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'parent', 'disciplines')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('name', 'slug', 'parent', 'description', 'is_active')
        }),
        (_("Affichage et organisation"), {
            'fields': ('order', 'image', 'disciplines')
        }),
        (_("Métadonnées SEO"), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
    )
    
    filter_horizontal = ('disciplines',)
    actions = ['activate_categories', 'deactivate_categories', 'create_martial_arts_categories']
    
    def name_with_hierarchy(self, obj):
        """Affiche le nom avec l'indentation hiérarchique."""
        if obj.parent:
            return format_html("&nbsp;&nbsp;→ {}", obj.name)
        return obj.name
    name_with_hierarchy.short_description = _("Nom")
    name_with_hierarchy.admin_order_field = 'name'
    
    def products_count(self, obj):
        """Compte le nombre de produits dans cette catégorie."""
        count = obj.products.count() if hasattr(obj, 'products') else 0
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    products_count.short_description = _("Produits")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent').prefetch_related('disciplines')
        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            # Exclure la catégorie elle-même des choix parents possibles pour éviter les cycles
            if 'object_id' in request.resolver_match.kwargs:
                kwargs["queryset"] = Category.objects.exclude(
                    id=request.resolver_match.kwargs['object_id']
                )
            # Ne montrer que les catégories principales comme parents possibles
            kwargs["queryset"] = Category.objects.filter(parent=None)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def activate_categories(self, request, queryset):
        """Active les catégories sélectionnées."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _("{} catégorie(s) activée(s) avec succès.").format(updated),
            messages.SUCCESS
        )
    activate_categories.short_description = _("Activer les catégories sélectionnées")
    
    def deactivate_categories(self, request, queryset):
        """Désactive les catégories sélectionnées."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _("{} catégorie(s) désactivée(s) avec succès.").format(updated),
            messages.SUCCESS
        )
    deactivate_categories.short_description = _("Désactiver les catégories sélectionnées")
    
    def create_martial_arts_categories(self, request, queryset):
        """Crée les catégories d'arts martiaux prédéfinies."""
        try:
            # Import ici pour éviter les imports circulaires
            import subprocess
            import os
            from django.conf import settings
            
            # Exécuter le script de création des catégories
            script_path = os.path.join(settings.BASE_DIR, 'create_martial_arts_categories.py')
            if os.path.exists(script_path):
                result = subprocess.run([
                    'python3', script_path
                ], capture_output=True, text=True, cwd=settings.BASE_DIR)
                
                if result.returncode == 0:
                    self.message_user(
                        request,
                        _("Catégories d'arts martiaux créées avec succès !"),
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request,
                        _("Erreur lors de la création des catégories: {}").format(result.stderr),
                        messages.ERROR
                    )
            else:
                self.message_user(
                    request,
                    _("Script de création des catégories non trouvé."),
                    messages.ERROR
                )
        except Exception as e:
            self.message_user(
                request,
                _("Erreur lors de l'exécution du script: {}").format(str(e)),
                messages.ERROR
            )
        
        # Rediriger vers la liste des catégories
        return HttpResponseRedirect(reverse('admin:shop_category_changelist'))
    
    create_martial_arts_categories.short_description = _("Créer les catégories d'arts martiaux prédéfinies")