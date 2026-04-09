import logging
import traceback
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from apps.shop.models.category import Category
from apps.shop.models.product import Product
from apps.shop.models.cart import Cart, CartItem

logger = logging.getLogger(__name__)


def _get_user_organization(user):
    """Get the organization associated with a user for shop isolation."""
    if user.is_superuser or user.is_staff:
        return None  # superuser/staff see all products
    try:
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.get(user=user)
        if profile.organization:
            return profile.organization
    except Exception:
        pass
    # Fallback: check via practitioner
    try:
        if hasattr(user, 'practitioners'):
            practitioner = user.practitioners.first()
            if practitioner and practitioner.organization:
                return practitioner.organization
    except Exception:
        pass
    return None


def _filter_products_for_user(qs, user):
    """Filter products queryset based on user's organization.

    Visibility rules:
    - Superuser/staff: see all products
    - Products with is_public=True: visible to everyone
    - Products with organization=NULL: visible to everyone (legacy/global)
    - Products with organization set: only visible to members of that organization
    """
    if user.is_superuser or user.is_staff:
        return qs
    org = _get_user_organization(user)
    if org:
        # Show: public products + global products (no org) + own org products
        return qs.filter(
            Q(is_public=True) | Q(organization__isnull=True) | Q(organization=org)
        )
    else:
        # No org: only public + global products
        return qs.filter(
            Q(is_public=True) | Q(organization__isnull=True)
        )


class ShopProductsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        qs = Product.objects.filter(is_active=True).order_by('-created_at')
        # Apply organization isolation
        qs = _filter_products_for_user(qs, request.user)
        featured = request.GET.get('featured')
        if featured in ('1', 'true', 'True'):
            qs = qs.filter(is_featured=True)
        category_id = request.GET.get('category')
        if category_id:
            qs = qs.filter(categories__id=category_id)

        def abs_url(path: str):
            try:
                return request.build_absolute_uri(path)
            except Exception:
                return path

        data = []
        for p in qs[:100]:
            first_img = p.images.first() if hasattr(p, 'images') else None
            featured_url = abs_url(first_img.image.url) if (first_img and getattr(first_img, 'image', None)) else None
            images_urls = []
            if hasattr(p, 'images'):
                for im in p.images.all():
                    if getattr(im, 'image', None):
                        images_urls.append(abs_url(im.image.url))
            item = {
                'id': str(p.id),
                'name': p.name,
                'slug': p.slug,
                'price': float(p.price),
                'sale_price': float(p.sale_price) if p.sale_price else None,
                'currency': 'EUR',
                'featured_image': featured_url,
                'images': images_urls,
                'in_stock': p.is_in_stock,
                'stock_quantity': p.stock if hasattr(p, 'stock') else 0,
                'category': {'id': str(p.category.id), 'name': p.category.name} if p.category else None,
            }
            data.append(item)
        return Response({'products': data, 'count': len(data)})


class ShopCategoriesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        # Get categories that have at least one visible product for this user
        visible_products = Product.objects.filter(is_active=True)
        visible_products = _filter_products_for_user(visible_products, request.user)
        visible_category_ids = set(
            visible_products.values_list('categories__id', flat=True)
        )
        # Also include parent categories of visible categories
        visible_cats = Category.objects.filter(
            id__in=visible_category_ids, is_active=True
        )
        parent_ids = set(
            visible_cats.values_list('parent_id', flat=True)
        ) - {None}

        all_visible_ids = visible_category_ids | parent_ids

        qs = Category.objects.filter(
            is_active=True, id__in=all_visible_ids
        ).order_by('order', 'name')

        data = [
            {
                'id': str(c.id),
                'name': c.name,
                'slug': c.slug,
                'parent': str(c.parent_id) if c.parent_id else None,
            }
            for c in qs
        ]
        return Response({'categories': data, 'count': len(data)})


@method_decorator(csrf_exempt, name='dispatch')
class ShopCartView(APIView):
    """GET current cart, DELETE to clear cart."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def _get_cart(self, user):
        carts = Cart.objects.filter(user=user, converted_to_order=False)
        if carts.count() > 1:
            # Keep only the most recent cart
            cart = carts.order_by('-created_at').first()
            carts.exclude(id=cart.id).delete()
            return cart
        cart, _ = Cart.objects.get_or_create(user=user, converted_to_order=False)
        return cart

    def _serialize_cart(self, cart, request):
        def abs_url(path):
            try:
                return request.build_absolute_uri(path)
            except Exception:
                return path

        items = []
        for ci in cart.items.select_related('product').all():
            first_img = ci.product.images.first() if hasattr(ci.product, 'images') else None
            img_url = abs_url(first_img.image.url) if (first_img and getattr(first_img, 'image', None)) else None
            items.append({
                'id': str(ci.id),
                'product': {
                    'id': str(ci.product.id),
                    'name': ci.product.name,
                    'price': float(ci.product.price),
                    'featured_image': img_url,
                },
                'quantity': ci.quantity,
                'unit_price': float(ci.get_unit_price()),
                'total_price': float(ci.get_total_price()),
                'added_at': ci.added_at.isoformat() if ci.added_at else None,
            })
        return {
            'id': str(cart.id),
            'items': items,
            'total_amount': float(cart.get_subtotal()),
            'currency': 'EUR',
            'item_count': cart.total_quantity,
        }

    def get(self, request):
        cart = self._get_cart(request.user)
        return Response(self._serialize_cart(cart, request))

    def delete(self, request):
        try:
            cart = self._get_cart(request.user)
            try:
                cart.clear()
            except Exception:
                # Fallback: delete items directly
                cart.items.all().delete()
            return Response({'status': 'success', 'message': 'Cart cleared'})
        except Exception as e:
            logger.error(f"[ShopCartView.delete] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name='dispatch')
class ShopCartAddView(APIView):
    """POST to add a product to the cart."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                return Response(
                    {'status': 'error', 'message': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verify the user can access this product (organization isolation)
            visible = _filter_products_for_user(
                Product.objects.filter(id=product.id), request.user
            )
            if not visible.exists():
                return Response(
                    {'status': 'error', 'message': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Handle multiple carts for same user
            carts = Cart.objects.filter(user=request.user, converted_to_order=False)
            if carts.count() > 1:
                cart = carts.order_by('-created_at').first()
                carts.exclude(id=cart.id).delete()
            else:
                cart, _ = Cart.objects.get_or_create(user=request.user, converted_to_order=False)

            try:
                cart.add_item(product, quantity)
            except Exception:
                # Fallback: manually add/update cart item if add_item fails
                from django.db.models import F
                ci, created = CartItem.objects.get_or_create(
                    cart=cart, product=product, variation=None,
                    defaults={'quantity': quantity, 'price_at_addition': product.price},
                )
                if not created:
                    ci.quantity = F('quantity') + quantity
                    ci.save(update_fields=['quantity'])

            return Response({
                'status': 'success',
                'message': 'Product added to cart',
                'cart_count': cart.items.count(),
                'cart_subtotal': float(sum(
                    ci.get_total_price() for ci in cart.items.all()
                )),
            })
        except Exception as e:
            logger.error(f"[ShopCartAddView] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name='dispatch')
class ShopCartItemView(APIView):
    """PATCH to update quantity, DELETE to remove item."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def patch(self, request, item_id):
        quantity = int(request.data.get('quantity', 1))
        cart, _ = Cart.objects.get_or_create(user=request.user, converted_to_order=False)
        try:
            cart.update_item_quantity(item_id, quantity)
        except Exception:
            return Response(
                {'status': 'error', 'message': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'status': 'success', 'message': 'Cart item updated'})

    def delete(self, request, item_id):
        try:
            ci = CartItem.objects.get(id=item_id, cart__user=request.user)
            ci.delete()
        except CartItem.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'status': 'success', 'message': 'Item removed from cart'})


from apps.shop.models.order import Order, OrderItem
from apps.competitions.models import Club


def _serialize_order(order, request):
    """Serialize an Order object to dict."""
    def abs_url(path):
        try:
            return request.build_absolute_uri(path)
        except Exception:
            return path

    items = []
    for oi in order.items.select_related('product').all():
        img_url = None
        if oi.product and hasattr(oi.product, 'images'):
            first_img = oi.product.images.first()
            if first_img and getattr(first_img, 'image', None):
                img_url = abs_url(first_img.image.url)
        items.append({
            'id': str(oi.id),
            'product': {
                'id': str(oi.product.id) if oi.product else None,
                'name': oi.product_name or (oi.product.name if oi.product else ''),
                'price': float(oi.price),
                'featured_image': img_url,
            },
            'quantity': oi.quantity,
            'unit_price': float(oi.price),
            'total_price': float(oi.subtotal),
        })

    customer = None
    if order.user:
        customer = {
            'id': str(order.user.id),
            'first_name': order.user.first_name or '',
            'last_name': order.user.last_name or '',
            'email': order.user.email or '',
        }

    return {
        'id': str(order.id),
        'order_number': order.order_number,
        'status': order.status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
        'total_amount': float(order.total) if order.total else 0,
        'subtotal': float(order.subtotal) if order.subtotal else 0,
        'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0,
        'tax_amount': float(order.tax_amount) if order.tax_amount else 0,
        'discount_amount': float(order.discount_amount) if order.discount_amount else 0,
        'currency': 'EUR',
        'is_paid': order.is_paid,
        'payment_method': order.payment_method or '',
        'shipping_method': order.shipping_method or '',
        'tracking_number': order.tracking_number or '',
        'customer_notes': order.customer_notes or '',
        'customer': customer,
        'items': items,
    }


def _get_user_club(user):
    """Get the club associated with a user (same logic as club_required decorator)."""
    club = None
    if hasattr(user, 'club') and user.club and isinstance(user.club, Club):
        club = user.club
    else:
        club = Club.objects.filter(owner=user).first()
    if not club and hasattr(user, 'profile') and hasattr(user.profile, 'club'):
        club = user.profile.club
    # Fallback: check via practitioner → organization → club
    if not club and hasattr(user, 'practitioners'):
        practitioner = user.practitioners.first()
        if practitioner and practitioner.organization_id:
            club = Club.objects.filter(organization=practitioner.organization).first()
    return club


@method_decorator(csrf_exempt, name='dispatch')
class ShopOrdersView(APIView):
    """GET user's orders, POST to create order from cart."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        try:
            orders = Order.objects.filter(user=request.user).order_by('-created_at')
            status_filter = request.GET.get('status')
            if status_filter:
                orders = orders.filter(status=status_filter)
            data = [_serialize_order(o, request) for o in orders[:50]]
            return Response(data)
        except Exception as e:
            logger.error(f"[ShopOrdersView.get] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """Create an order from the current cart."""
        try:
            # Get user's cart
            carts = Cart.objects.filter(user=request.user, converted_to_order=False)
            if carts.count() > 1:
                cart = carts.order_by('-created_at').first()
                carts.exclude(id=cart.id).delete()
            else:
                try:
                    cart = Cart.objects.get(user=request.user, converted_to_order=False)
                except Cart.DoesNotExist:
                    return Response(
                        {'status': 'error', 'message': 'No active cart found'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if not cart.items.exists():
                return Response(
                    {'status': 'error', 'message': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get user's club
            club = _get_user_club(request.user)

            # Calculate subtotal from cart items
            subtotal = sum(ci.get_total_price() for ci in cart.items.all())

            # Create order
            from django.utils import timezone
            year = timezone.now().strftime('%y')
            month = timezone.now().strftime('%m')
            last_order = Order.objects.order_by('-created_at').first()
            if last_order and last_order.order_number:
                try:
                    last_number = int(last_order.order_number[4:])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1

            order = Order(
                order_number=f"MC{year}{month}{new_number:06d}",
                user=request.user,
                club=club,
                status=Order.PENDING,
                subtotal=subtotal,
                total=subtotal,
                shipping_method=request.data.get('shipping_method', Order.CLICK_COLLECT),
                payment_method=request.data.get('payment_method', ''),
                customer_notes=request.data.get('notes', ''),
            )
            order.save()

            # Create order items from cart items
            for ci in cart.items.select_related('product').all():
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.name,
                    product_sku=getattr(ci.product, 'sku', '') or '',
                    quantity=ci.quantity,
                    price=ci.product.price,
                )

            # Mark cart as converted
            try:
                cart.converted_to_order = True
                cart.save(update_fields=['converted_to_order'])
            except Exception:
                cart.items.all().delete()

            return Response({
                'status': 'success',
                'message': 'Order created',
                'order': _serialize_order(order, request),
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"[ShopOrdersView.post] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        """Practitioner cancels their own order (only pending/processing)."""
        try:
            order_id = request.data.get('order_id')
            action = request.data.get('action', 'cancel')
            if not order_id:
                return Response(
                    {'status': 'error', 'message': 'order_id is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Order not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if action == 'cancel':
                if order.status not in ('pending', 'processing'):
                    return Response(
                        {'status': 'error', 'message': 'Only pending or processing orders can be cancelled'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                from django.utils import timezone
                order.status = 'cancelled'
                order.cancelled_at = timezone.now()
                order.save()
                return Response({
                    'status': 'success',
                    'message': 'Order cancelled',
                    'order': _serialize_order(order, request),
                })
            return Response(
                {'status': 'error', 'message': f'Unknown action: {action}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"[ShopOrdersView.patch] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name='dispatch')
class ShopOrderDetailView(APIView):
    """GET order detail."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            return Response(_serialize_order(order, request))
        except Order.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND,
            )


@method_decorator(csrf_exempt, name='dispatch')
class ShopClubOrdersView(APIView):
    """GET all orders for the user's club (manager view)."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        try:
            club = _get_user_club(request.user)
            if not club:
                return Response(
                    {'status': 'error', 'message': 'No club found for this user'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            orders = Order.objects.filter(club=club).order_by('-created_at')
            status_filter = request.GET.get('status')
            if status_filter:
                orders = orders.filter(status=status_filter)

            # Stats
            total_count = orders.count()
            pending_count = orders.filter(status='pending').count()
            processing_count = orders.filter(status='processing').count()
            delivered_count = orders.filter(status='delivered').count()

            data = [_serialize_order(o, request) for o in orders[:100]]
            return Response({
                'orders': data,
                'count': len(data),
                'stats': {
                    'total': total_count,
                    'pending': pending_count,
                    'processing': processing_count,
                    'delivered': delivered_count,
                },
            })
        except Exception as e:
            logger.error(f"[ShopClubOrdersView.get] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        """Update order status (manager action)."""
        try:
            club = _get_user_club(request.user)
            if not club:
                return Response(
                    {'status': 'error', 'message': 'No club found'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            order_id = request.data.get('order_id')
            new_status = request.data.get('status')
            if not order_id or not new_status:
                return Response(
                    {'status': 'error', 'message': 'order_id and status are required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            valid_statuses = ['processing', 'shipped', 'delivered', 'cancelled']
            if new_status not in valid_statuses:
                return Response(
                    {'status': 'error', 'message': f'Invalid status. Must be one of: {valid_statuses}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                order = Order.objects.get(id=order_id, club=club)
            except Order.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Order not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            order.status = new_status
            if new_status == 'cancelled':
                from django.utils import timezone
                order.cancelled_at = timezone.now()
            elif new_status == 'shipped':
                from django.utils import timezone
                order.shipped_at = timezone.now()
            elif new_status == 'delivered':
                from django.utils import timezone
                order.delivered_at = timezone.now()

            order.save()
            return Response({
                'status': 'success',
                'message': f'Order updated to {new_status}',
                'order': _serialize_order(order, request),
            })
        except Exception as e:
            logger.error(f"[ShopClubOrdersView.patch] Error: {e}\n{traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


from django.urls import path
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

urlpatterns = [
    path('products/', ShopProductsView.as_view(), name='shop_products_api'),
    path('categories/', ShopCategoriesView.as_view(), name='shop_categories_api'),
    path('cart/', ShopCartView.as_view(), name='shop_cart_api'),
    path('cart/add/', ShopCartAddView.as_view(), name='shop_cart_add_api'),
    path('cart/items/<int:item_id>/', ShopCartItemView.as_view(), name='shop_cart_item_api'),
    path('cart/clear/', ShopCartView.as_view(), name='shop_cart_clear_api'),
    path('orders/', ShopOrdersView.as_view(), name='shop_orders_api'),
    path('orders/club/', ShopClubOrdersView.as_view(), name='shop_club_orders_api'),
    path('orders/<uuid:order_id>/', ShopOrderDetailView.as_view(), name='shop_order_detail_api'),
]
