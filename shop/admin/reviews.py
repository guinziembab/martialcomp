from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from shop.models import ProductReview, ReviewImage


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    fields = ('image', 'caption', 'order')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_link', 'user_link', 'rating_stars', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_featured', 'purchased_item')
    search_fields = ('title', 'comment', 'user__username', 'product__name')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('product', 'user', 'created_at')
        }),
        (_("Évaluation"), {
            'fields': ('rating', 'title', 'comment', 'purchased_item')
        }),
        (_("Notes détaillées"), {
            'fields': ('quality_rating', 'value_rating', 'durability_rating'),
            'classes': ('collapse',),
        }),
        (_("Modération"), {
            'fields': ('is_approved', 'is_featured', 'reported_count', 'admin_response')
        }),
        (_("Votes"), {
            'fields': ('helpful_votes', 'not_helpful_votes', 'helpfulness_score'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'helpfulness_score')
    inlines = [ReviewImageInline]
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:gold;">{}</span>', stars)
    rating_stars.short_description = _("Note")
    
    def product_link(self, obj):
        url = f"/admin/shop/product/{obj.product.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = _("Produit")
    
    def user_link(self, obj):
        url = f"/admin/auth/user/{obj.user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _("Utilisateur")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')