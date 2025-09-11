from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.shop.models.category import Category
from apps.shop.models.product import Product


class ShopProductsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        qs = Product.objects.filter(is_active=True).order_by('-created_at')
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
                'price': float(p.price),
                'sale_price': float(p.sale_price) if p.sale_price else None,
                'currency': 'EUR',
                'featured_image': featured_url,
                'images': images_urls,
                'in_stock': p.is_in_stock,
                'category': {'id': str(p.category.id), 'name': p.category.name} if p.category else None,
            }
            data.append(item)
        return Response({'products': data, 'count': len(data)})


class ShopCategoriesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        qs = Category.objects.filter(is_active=True).order_by('order', 'name')
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


from django.urls import path
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

urlpatterns = [
    path('products/', ShopProductsView.as_view(), name='shop_products_api'),
    path('categories/', ShopCategoriesView.as_view(), name='shop_categories_api'),
]
