from django.core.exceptions import PermissionDenied
from django.urls import path
from apps.shop.views import reviews
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

app_name = 'reviews'

urlpatterns = [
    path('product/<slug:product_slug>/add-review/', reviews.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', reviews.edit_review, name='edit_review'),
]
