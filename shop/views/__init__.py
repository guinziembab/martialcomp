from shop.views.catalog import (
    product_list, product_search, category_detail, product_detail,
    brand_list, brand_detail, new_arrivals, on_sale, featured_products,
    discipline_products, product_suggestions, filter_options
)

from shop.views.cart import (
    cart_detail, cart_summary, add_to_cart, update_cart,
    remove_from_cart, clear_cart, apply_coupon, remove_coupon
)

from shop.views.reviews import (
    add_review, edit_review
)

from shop.views.checkout import (
    checkout_view, shipping_address, edit_address, delete_address,
    order_confirmation, update_shipping_method
)

from shop.views.account import (
    order_list, order_detail, order_invoice,
    address_list, address_add, address_edit, address_delete, set_default_address,
    review_list, review_edit, review_delete
)

# Export all views
__all__ = [
    # Catalog views
    'product_list', 'product_search', 'category_detail', 'product_detail',
    'brand_list', 'brand_detail', 'new_arrivals', 'on_sale', 'featured_products',
    'discipline_products', 'product_suggestions', 'filter_options',
    
    # Cart views
    'cart_detail', 'cart_summary', 'add_to_cart', 'update_cart',
    'remove_from_cart', 'clear_cart', 'apply_coupon', 'remove_coupon',
    
    # Review views
    'add_review', 'edit_review',
    
    # Checkout views
    'checkout_view', 'shipping_address', 'edit_address', 'delete_address',
    'order_confirmation', 'update_shipping_method',
    
    # Account views
    'order_list', 'order_detail', 'order_invoice',
    'address_list', 'address_add', 'address_edit', 'address_delete', 'set_default_address',
    'review_list', 'review_edit', 'review_delete',
]