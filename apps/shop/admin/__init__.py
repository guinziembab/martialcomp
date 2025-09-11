# -*- coding: utf-8 -*-
"""
SHOP ADMIN FINAL - Sans decorateurs @admin.register
Utilisation exclusive de safe_register pour eviter les conflits
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import messages
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

# Désactiver les actions de masse par défaut pour éviter les erreurs
try:
    admin.site.disable_action('delete_selected')
except KeyError:
    pass

# =============================================================================
# UTILITAIRE DE DESENREGISTREMENT SECURISE
# =============================================================================

def safe_register(model_class, admin_class):
    """
    Enregistre un modele en desenregistrant d'abord s'il existe deja
    """
    try:
        # Verifier si le modele est deja enregistre
        if admin.site.is_registered(model_class):
            # Desenregistrer l'ancien admin
            admin.site.unregister(model_class)
            logger.info(f"Modele {model_class.__name__} desenregistre avec succes")
        
        # Enregistrer le nouveau admin
        admin.site.register(model_class, admin_class)
        logger.info(f"Modele {model_class.__name__} enregistre avec succes")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de {model_class.__name__}: {e}")
        return False

# =============================================================================
# SHOP ADMIN - AVEC DESENREGISTREMENT SECURISE UNIQUEMENT
# =============================================================================

# 1. CATEGORY ADMIN
try:
    from apps.shop.models import Category
    
    class CategoryAdmin(admin.ModelAdmin):
        """Administration des categories - Version finale"""
        
        list_display = [
            'name', 'get_slug_display', 'get_active_status', 
            'get_product_count', 'get_created_date'
        ]
        list_filter = []
        search_fields = ['name', 'description']
        readonly_fields = ['get_slug_display', 'get_created_date', 'get_updated_date']
        ordering = ['name']
        
        def get_slug_display(self, obj):
            slug = self._get_field_value(obj, ['slug', 'url_slug', 'permalink'])
            return slug or '-'
        get_slug_display.short_description = _('Slug')
        
        def get_active_status(self, obj):
            is_active = self._get_field_value(obj, ['is_active', 'active', 'enabled'])
            if is_active is not None:
                return '[OK] Actif' if is_active else '[X] Inactif'
            return '[OK] Actif'
        get_active_status.short_description = _('Statut')
        
        def get_product_count(self, obj):
            try:
                if hasattr(obj, 'products'):
                    return obj.products.count()
                elif hasattr(obj, 'product_set'):
                    return obj.product_set.count()
                elif hasattr(obj, 'category_products'):
                    return obj.category_products.count()
                return 0
            except Exception as e:
                logger.warning(f"Erreur lors du calcul des produits pour la categorie {obj.id}: {e}")
                return 0
        get_product_count.short_description = _('Nb produits')
        
        def get_created_date(self, obj):
            date_value = self._get_field_value(obj, ['created_at', 'date_created', 'timestamp'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_created_date.short_description = _('Date de creation')
        
        def get_updated_date(self, obj):
            date_value = self._get_field_value(obj, ['updated_at', 'date_updated', 'modified_at'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_updated_date.short_description = _('Derniere MAJ')
        
        @staticmethod
        def _get_field_value(obj, field_names, default=None):
            for field_name in field_names:
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    if value is not None:
                        return value
            return default

    # Enregistrement securise - PAS de decorateur
    safe_register(Category, CategoryAdmin)

except ImportError as e:
    logger.warning(f"Category model non disponible: {e}")

# 2. PRODUCT ADMIN
try:
    from apps.shop.models import Product
    
    class ProductAdmin(admin.ModelAdmin):
        """Administration des produits - Version finale"""
        
        list_display = [
            'name', 'get_category_display', 'get_price_display', 
            'get_stock_status', 'get_active_status', 'get_created_date'
        ]
        list_filter = []
        search_fields = ['name', 'description']
        readonly_fields = [
            'get_created_date', 'get_updated_date', 'get_stock_info',
            'get_sales_info'
        ]
        ordering = ['name']
        actions = ['mark_as_active', 'mark_as_inactive', 'calculate_stock_value']
        
        def get_category_display(self, obj):
            category = self._get_field_value(obj, ['category'])
            if category:
                return str(category)
            return _('Sans categorie')
        get_category_display.short_description = _('Categorie')
        
        def get_price_display(self, obj):
            price = self._get_field_value(obj, ['price', 'unit_price', 'cost'])
            currency = self._get_field_value(obj, ['currency', 'devise'], default='EUR')
            if price is not None:
                return f"{price} {currency}"
            return '-'
        get_price_display.short_description = _('Prix')
        
        def get_stock_status(self, obj):
            stock_value = self._get_field_value(obj, [
                'stock', 'stock_quantity', 'quantity', 'inventory'
            ])
            
            if stock_value is not None:
                if stock_value > 20:
                    return f'[OK] En stock ({stock_value})'
                elif stock_value > 5:
                    return f'[!] Stock faible ({stock_value})'
                elif stock_value > 0:
                    return f'[!!] Stock critique ({stock_value})'
                else:
                    return '[X] Rupture de stock'
            return '[?] Stock non defini'
        get_stock_status.short_description = _('Stock')
        
        def get_active_status(self, obj):
            is_active = self._get_field_value(obj, ['is_active', 'active', 'enabled', 'available'])
            if is_active is not None:
                return '[OK] Actif' if is_active else '[X] Inactif'
            return '[OK] Actif'
        get_active_status.short_description = _('Statut')
        
        def get_created_date(self, obj):
            date_value = self._get_field_value(obj, ['created_at', 'date_created', 'timestamp'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_created_date.short_description = _('Date de creation')
        
        def get_updated_date(self, obj):
            date_value = self._get_field_value(obj, ['updated_at', 'date_updated', 'modified_at'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_updated_date.short_description = _('Derniere MAJ')
        
        def get_stock_info(self, obj):
            info_parts = []
            
            stock = self._get_field_value(obj, ['stock', 'stock_quantity', 'quantity'])
            if stock is not None:
                info_parts.append(f"Stock: {stock}")
            
            min_stock = self._get_field_value(obj, ['min_stock', 'minimum_stock', 'reorder_level'])
            if min_stock is not None:
                info_parts.append(f"Min: {min_stock}")
            
            reserved = self._get_field_value(obj, ['reserved_stock', 'reserved_quantity'])
            if reserved is not None:
                info_parts.append(f"Reserve: {reserved}")
            
            return ' | '.join(info_parts) if info_parts else 'Aucune information'
        get_stock_info.short_description = _('Details stock')
        
        def get_sales_info(self, obj):
            try:
                sales_count = 0
                total_sales = 0
                
                for relation_name in ['orderitem_set', 'order_items', 'sales']:
                    if hasattr(obj, relation_name):
                        items = getattr(obj, relation_name).all()
                        sales_count = items.count()
                        for item in items:
                            quantity = self._get_field_value(item, ['quantity'], default=1)
                            price = self._get_field_value(item, ['price', 'unit_price'], default=0)
                            total_sales += quantity * price
                        
                        if sales_count > 0:
                            return f"{sales_count} vente(s) - Total: {total_sales}EUR"
                        break
                
                return "Aucune vente"
                
            except Exception as e:
                logger.warning(f"Erreur lors du calcul des ventes pour le produit {obj.id}: {e}")
                return "Erreur de calcul"
        get_sales_info.short_description = _('Ventes')
        
        def mark_as_active(self, request, queryset):
            """Action pour marquer comme actif"""
            updated = 0
            for obj in queryset:
                for field_name in ['is_active', 'active', 'enabled']:
                    if hasattr(obj, field_name):
                        setattr(obj, field_name, True)
                        obj.save()
                        updated += 1
                        break
            self.message_user(request, f"{updated} produit(s) marque(s) comme actif(s).")
        mark_as_active.short_description = "Marquer comme actif"
        
        def mark_as_inactive(self, request, queryset):
            """Action pour marquer comme inactif"""
            updated = 0
            for obj in queryset:
                for field_name in ['is_active', 'active', 'enabled']:
                    if hasattr(obj, field_name):
                        setattr(obj, field_name, False)
                        obj.save()
                        updated += 1
                        break
            self.message_user(request, f"{updated} produit(s) marque(s) comme inactif(s).")
        mark_as_inactive.short_description = "Marquer comme inactif"
        
        def calculate_stock_value(self, request, queryset):
            """Action pour calculer la valeur du stock"""
            total_value = 0
            count = 0
            for product in queryset:
                stock = self._get_field_value(product, ['stock', 'stock_quantity', 'quantity'], default=0)
                price = self._get_field_value(product, ['price', 'unit_price', 'cost'], default=0)
                if stock and price:
                    total_value += stock * price
                    count += 1
            self.message_user(request, f"Valeur totale du stock: {total_value}EUR pour {count} produit(s).")
        calculate_stock_value.short_description = "Calculer valeur stock"
        
        @staticmethod
        def _get_field_value(obj, field_names, default=None):
            for field_name in field_names:
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    if value is not None:
                        return value
            return default

    # Enregistrement securise - PAS de decorateur
    safe_register(Product, ProductAdmin)

except ImportError as e:
    logger.warning(f"Product model non disponible: {e}")

# 3. ORDER ADMIN
try:
    from apps.shop.models import Order
    
    class OrderAdmin(admin.ModelAdmin):
        """Administration des commandes - Version finale"""
        
        list_display = [
            'get_order_number', 'get_customer_info', 'get_total_display',
            'get_status_display', 'get_items_count', 'get_order_date'
        ]
        list_filter = []
        search_fields = ['customer__username', 'user__username']
        readonly_fields = [
            'get_order_number', 'get_order_date', 'get_updated_date',
            'get_total_display', 'get_items_summary'
        ]
        ordering = ['-id']
        
        def get_order_number(self, obj):
            number = self._get_field_value(obj, ['order_number', 'number', 'reference'])
            return number or f"CMD-{obj.id:06d}"
        get_order_number.short_description = _('N° Commande')
        
        def get_customer_info(self, obj):
            customer = self._get_field_value(obj, ['user', 'customer', 'client'])
            if customer:
                if hasattr(customer, 'get_full_name'):
                    return customer.get_full_name() or customer.username
                return str(customer)
            
            customer_name = self._get_field_value(obj, ['customer_name', 'client_name'])
            return customer_name or '-'
        get_customer_info.short_description = _('Client')
        
        def get_total_display(self, obj):
            total = self._get_field_value(obj, ['total', 'total_amount', 'amount'])
            
            if total is not None:
                currency = self._get_field_value(obj, ['currency'], default='EUR')
                return f"{total} {currency}"
            
            try:
                calculated_total = 0
                items_relations = ['items', 'orderitem_set', 'order_items']
                
                for relation_name in items_relations:
                    if hasattr(obj, relation_name):
                        items = getattr(obj, relation_name).all()
                        for item in items:
                            quantity = self._get_field_value(item, ['quantity'], default=1)
                            price = self._get_field_value(item, ['price', 'unit_price'], default=0)
                            calculated_total += quantity * price
                        
                        if calculated_total > 0:
                            return f"{calculated_total} EUR"
                        break
                
                return "0 EUR"
                
            except Exception as e:
                logger.warning(f"Erreur lors du calcul du total pour la commande {obj.id}: {e}")
                return "Erreur de calcul"
        get_total_display.short_description = _('Total')
        
        def get_status_display(self, obj):
            status = self._get_field_value(obj, ['status', 'state', 'order_status'])
            if status:
                color_map = {
                    'completed': 'success', 'delivered': 'success', 'paid': 'success',
                    'processing': 'info', 'shipped': 'info', 'confirmed': 'info',
                    'pending': 'warning', 'payment_pending': 'warning',
                    'cancelled': 'danger', 'refunded': 'danger', 'failed': 'danger'
                }
                color = color_map.get(status.lower(), 'secondary')
                return format_html('<span class="badge bg-{}">{}</span>', color, status)
            return '-'
        get_status_display.short_description = _('Statut')
        
        def get_items_count(self, obj):
            try:
                for relation_name in ['items', 'orderitem_set', 'order_items']:
                    if hasattr(obj, relation_name):
                        return getattr(obj, relation_name).count()
                return 0
            except:
                return 0
        get_items_count.short_description = _('Nb articles')
        
        def get_order_date(self, obj):
            date_value = self._get_field_value(obj, ['created_at', 'order_date', 'date_created'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_order_date.short_description = _('Date commande')
        
        def get_updated_date(self, obj):
            date_value = self._get_field_value(obj, ['updated_at', 'date_updated', 'modified_at'])
            return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
        get_updated_date.short_description = _('Derniere MAJ')
        
        def get_items_summary(self, obj):
            try:
                for relation_name in ['items', 'orderitem_set', 'order_items']:
                    if hasattr(obj, relation_name):
                        items = getattr(obj, relation_name).all()
                        if items:
                            summary = []
                            for item in items[:5]:
                                product_name = self._get_field_value(item, ['product__name', 'product_name'])
                                if not product_name and hasattr(item, 'product'):
                                    product_name = str(item.product)
                                quantity = self._get_field_value(item, ['quantity'], default=1)
                                price = self._get_field_value(item, ['price', 'unit_price'], default=0)
                                summary.append(f"{product_name} (x{quantity}) - {price}EUR")
                            
                            if items.count() > 5:
                                summary.append(f"... et {items.count() - 5} autres articles")
                            
                            return mark_safe('<br>'.join(summary))
                        break
                
                return 'Aucun article'
            except Exception as e:
                logger.warning(f"Erreur lors de la generation du resume pour la commande {obj.id}: {e}")
                return 'Erreur de lecture'
        get_items_summary.short_description = _('Detail articles')
        
        @staticmethod
        def _get_field_value(obj, field_names, default=None):
            for field_name in field_names:
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    if value is not None:
                        return value
            return default

    # Enregistrement securise - PAS de decorateur
    safe_register(Order, OrderAdmin)

except ImportError as e:
    logger.warning(f"Order model non disponible: {e}")

# 4. ORDER ITEM ADMIN
try:
    from apps.shop.models import OrderItem
    
    class OrderItemAdmin(admin.ModelAdmin):
        """Administration des articles de commande - Version finale"""
        
        list_display = [
            'get_order_info', 'get_product_info', 'quantity', 
            'get_unit_price', 'get_total_price'
        ]
        list_filter = []
        search_fields = ['product__name', 'order__id']
        readonly_fields = ['get_total_price', 'get_order_date']
        
        def get_order_info(self, obj):
            order = self._get_field_value(obj, ['order'])
            if order:
                order_number = self._get_field_value(order, ['order_number', 'number'], default=f'CMD-{order.id:06d}')
                return f"{order_number}"
            return '-'
        get_order_info.short_description = _('Commande')
        
        def get_product_info(self, obj):
            product = self._get_field_value(obj, ['product'])
            if product:
                return str(product)
            
            product_name = self._get_field_value(obj, ['product_name', 'item_name'])
            return product_name or '-'
        get_product_info.short_description = _('Produit')
        
        def get_unit_price(self, obj):
            price = self._get_field_value(obj, ['price', 'unit_price', 'item_price'])
            currency = self._get_field_value(obj, ['currency'], default='EUR')
            return f"{price} {currency}" if price is not None else '-'
        get_unit_price.short_description = _('Prix unitaire')
        
        def get_total_price(self, obj):
            quantity = self._get_field_value(obj, ['quantity'], default=1)
            unit_price = self._get_field_value(obj, ['price', 'unit_price'], default=0)
            
            if unit_price is not None and quantity is not None:
                total = quantity * unit_price
                currency = self._get_field_value(obj, ['currency'], default='EUR')
                return f"{total} {currency}"
            return '-'
        get_total_price.short_description = _('Total ligne')
        
        def get_order_date(self, obj):
            order = self._get_field_value(obj, ['order'])
            if order:
                date_value = self._get_field_value(order, ['created_at', 'order_date'])
                return date_value.strftime('%d/%m/%Y %H:%M') if date_value else '-'
            return '-'
        get_order_date.short_description = _('Date commande')
        
        @staticmethod
        def _get_field_value(obj, field_names, default=None):
            for field_name in field_names:
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    if value is not None:
                        return value
            return default

    # Enregistrement securise - PAS de decorateur
    safe_register(OrderItem, OrderItemAdmin)

except ImportError as e:
    logger.warning(f"OrderItem model non disponible: {e}")

# =============================================================================
# CONFIGURATION GLOBALE ADMIN
# =============================================================================

# Configuration du site admin
admin.site.site_header = _("Administration MartialComp - Shop")
admin.site.site_title = _("Admin Shop")
admin.site.index_title = _("Gestion E-commerce")

# Message de confirmation du chargement
logger.info("Admin shop final charge avec succes - Sans decorateurs")
print("[OK] Admin shop final charge avec succes - SANS DECORATEURS")