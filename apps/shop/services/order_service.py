"""
Service pour la gestion des commandes dans la fiche pratiquant.
Fournit les données d'historique, statistiques et suivi des commandes.
"""
import logging
from decimal import Decimal
from django.db.models import Sum, Count, F
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class OrderService:
    """
    Service pour récupérer les informations de commandes d'un pratiquant.
    """

    # Mapping des statuts vers les couleurs et icônes
    STATUS_CONFIG = {
        'pending': {
            'color': 'warning',
            'icon': 'fas fa-clock',
            'emoji': '🟡',
            'label': _('En attente')
        },
        'processing': {
            'color': 'info',
            'icon': 'fas fa-cog fa-spin',
            'emoji': '🔵',
            'label': _('En préparation')
        },
        'shipped': {
            'color': 'purple',
            'icon': 'fas fa-truck',
            'emoji': '🟣',
            'label': _('Expédiée')
        },
        'delivered': {
            'color': 'success',
            'icon': 'fas fa-check-circle',
            'emoji': '🟢',
            'label': _('Livrée')
        },
        'cancelled': {
            'color': 'secondary',
            'icon': 'fas fa-times-circle',
            'emoji': '⚫',
            'label': _('Annulée')
        },
        'refunded': {
            'color': 'danger',
            'icon': 'fas fa-undo',
            'emoji': '🔴',
            'label': _('Remboursée')
        },
        'on_hold': {
            'color': 'warning',
            'icon': 'fas fa-pause-circle',
            'emoji': '🟠',
            'label': _('En attente de paiement')
        }
    }

    def __init__(self, practitioner):
        """
        Initialise le service avec un pratiquant.

        Args:
            practitioner: Instance du modèle Practitioner
        """
        self.practitioner = practitioner
        self.user = getattr(practitioner, 'user', None)

    def get_orders_summary(self):
        """
        Retourne un résumé complet des commandes du pratiquant.

        Returns:
            dict: Données complètes des commandes
        """
        if not self.user:
            return None

        try:
            from apps.shop.models import Order, OrderItem

            # Récupérer toutes les commandes de l'utilisateur
            orders = Order.objects.filter(user=self.user).prefetch_related('items', 'items__product')

            if not orders.exists():
                return {
                    'has_orders': False,
                    'statistics': self._get_empty_statistics(),
                    'pending_orders': [],
                    'recent_orders': [],
                    'favorite_product': None
                }

            return {
                'has_orders': True,
                'statistics': self._get_statistics(orders),
                'pending_orders': self._get_pending_orders(orders),
                'recent_orders': self._get_recent_orders(orders),
                'favorite_product': self._get_favorite_product()
            }

        except ImportError as e:
            logger.warning(f"Module shop non disponible: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du chargement des commandes: {str(e)}")
            return None

    def _get_statistics(self, orders):
        """
        Calcule les statistiques des commandes.

        Args:
            orders: QuerySet des commandes

        Returns:
            dict: Statistiques des commandes
        """
        # Total dépensé (uniquement commandes payées/livrées)
        paid_orders = orders.filter(status__in=['delivered', 'shipped', 'processing'])
        total_spent = paid_orders.aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00'))
        )['total']

        # Nombre de commandes
        total_orders = orders.count()

        # Commandes par statut
        orders_by_status = {}
        for status, config in self.STATUS_CONFIG.items():
            count = orders.filter(status=status).count()
            if count > 0:
                orders_by_status[status] = {
                    'count': count,
                    **config
                }

        # Commandes en cours (non livrées, non annulées)
        pending_count = orders.exclude(
            status__in=['delivered', 'cancelled', 'refunded']
        ).count()

        return {
            'total_spent': float(total_spent),
            'total_orders': total_orders,
            'pending_count': pending_count,
            'orders_by_status': orders_by_status,
            'average_order': float(total_spent / total_orders) if total_orders > 0 else 0
        }

    def _get_empty_statistics(self):
        """
        Retourne des statistiques vides.

        Returns:
            dict: Statistiques vides
        """
        return {
            'total_spent': 0,
            'total_orders': 0,
            'pending_count': 0,
            'orders_by_status': {},
            'average_order': 0
        }

    def _get_pending_orders(self, orders):
        """
        Récupère les commandes en cours (non livrées).

        Args:
            orders: QuerySet des commandes

        Returns:
            list: Liste des commandes en cours
        """
        pending = orders.exclude(
            status__in=['delivered', 'cancelled', 'refunded']
        ).order_by('-created_at')[:5]

        result = []
        for order in pending:
            items_summary = self._get_order_items_summary(order)
            status_config = self.STATUS_CONFIG.get(order.status, self.STATUS_CONFIG['pending'])

            result.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'created_at': order.created_at,
                'total': float(order.total),
                'status': order.status,
                'status_display': status_config['label'],
                'status_color': status_config['color'],
                'status_icon': status_config['icon'],
                'status_emoji': status_config['emoji'],
                'items_summary': items_summary,
                'items_count': order.items.count(),
                'tracking_number': order.tracking_number,
                'estimated_delivery': order.estimated_delivery_date,
                'can_cancel': order.can_cancel,
                'days_since_order': order.days_since_order
            })

        return result

    def _get_recent_orders(self, orders, limit=5):
        """
        Récupère les dernières commandes (historique).

        Args:
            orders: QuerySet des commandes
            limit: Nombre maximum de commandes

        Returns:
            list: Liste des dernières commandes
        """
        recent = orders.order_by('-created_at')[:limit]

        result = []
        for order in recent:
            items_summary = self._get_order_items_summary(order)
            status_config = self.STATUS_CONFIG.get(order.status, self.STATUS_CONFIG['pending'])

            result.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'created_at': order.created_at,
                'total': float(order.total),
                'status': order.status,
                'status_display': status_config['label'],
                'status_color': status_config['color'],
                'status_icon': status_config['icon'],
                'status_emoji': status_config['emoji'],
                'items_summary': items_summary,
                'items_count': order.items.count(),
                'is_paid': order.is_paid,
                'invoice_number': order.invoice_number
            })

        return result

    def _get_order_items_summary(self, order):
        """
        Génère un résumé textuel des articles d'une commande.

        Args:
            order: Instance Order

        Returns:
            str: Résumé des articles
        """
        items = order.items.all()[:3]

        if not items:
            return _("Aucun article")

        names = [item.product_name for item in items]
        summary = ", ".join(names)

        total_items = order.items.count()
        if total_items > 3:
            summary += f" (+{total_items - 3})"

        return summary

    def _get_favorite_product(self):
        """
        Détermine le produit le plus acheté par l'utilisateur.

        Returns:
            dict: Informations sur le produit favori ou None
        """
        if not self.user:
            return None

        try:
            from apps.shop.models import OrderItem, Order

            # Trouver le produit le plus commandé
            favorite = OrderItem.objects.filter(
                order__user=self.user,
                order__status__in=['delivered', 'shipped', 'processing']
            ).values(
                'product_name', 'product_id'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_spent=Sum(F('price') * F('quantity'))
            ).order_by('-total_quantity').first()

            if favorite:
                return {
                    'name': favorite['product_name'],
                    'product_id': favorite['product_id'],
                    'total_quantity': favorite['total_quantity'],
                    'total_spent': float(favorite['total_spent'] or 0)
                }

            return None

        except Exception as e:
            logger.warning(f"Erreur lors de la recherche du produit favori: {str(e)}")
            return None

    def get_order_detail(self, order_id):
        """
        Récupère les détails complets d'une commande.

        Args:
            order_id: ID de la commande

        Returns:
            dict: Détails de la commande ou None
        """
        if not self.user:
            return None

        try:
            from apps.shop.models import Order

            order = Order.objects.filter(
                id=order_id,
                user=self.user
            ).prefetch_related(
                'items', 'items__product'
            ).select_related(
                'shipping_address', 'billing_address'
            ).first()

            if not order:
                return None

            status_config = self.STATUS_CONFIG.get(order.status, self.STATUS_CONFIG['pending'])

            # Récupérer tous les articles
            items = []
            for item in order.items.all():
                items.append({
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'variation': item.variation_description,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.subtotal),
                    'discount': float(item.discount),
                    'total': float(item.total)
                })

            return {
                'id': str(order.id),
                'order_number': order.order_number,
                'created_at': order.created_at,
                'status': order.status,
                'status_display': status_config['label'],
                'status_color': status_config['color'],
                'status_icon': status_config['icon'],
                'subtotal': float(order.subtotal),
                'shipping_cost': float(order.shipping_cost),
                'tax_amount': float(order.tax_amount),
                'discount_amount': float(order.discount_amount),
                'total': float(order.total),
                'is_paid': order.is_paid,
                'paid_at': order.paid_at,
                'payment_method': order.get_payment_method_display() if order.payment_method else None,
                'shipping_method': order.get_shipping_method_display() if order.shipping_method else None,
                'tracking_number': order.tracking_number,
                'estimated_delivery': order.estimated_delivery_date,
                'shipped_at': order.shipped_at,
                'delivered_at': order.delivered_at,
                'customer_notes': order.customer_notes,
                'invoice_number': order.invoice_number,
                'items': items,
                'items_count': len(items),
                'can_cancel': order.can_cancel,
                'shipping_address': self._format_address(order.shipping_address),
                'billing_address': self._format_address(order.billing_address)
            }

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la commande {order_id}: {str(e)}")
            return None

    def _format_address(self, address):
        """
        Formate une adresse pour l'affichage.

        Args:
            address: Instance Address

        Returns:
            dict: Adresse formatée ou None
        """
        if not address:
            return None

        return {
            'full_name': address.full_name,
            'company': address.company,
            'address_line1': address.address_line1,
            'address_line2': address.address_line2,
            'city': address.city,
            'postal_code': address.postal_code,
            'country': address.country,
            'phone': address.phone,
            'formatted': address.formatted_address
        }
