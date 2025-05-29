from django.urls import path
from shop.views import reviews

app_name = 'reviews'

urlpatterns = [
    path('product/<slug:product_slug>/add-review/', reviews.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', reviews.edit_review, name='edit_review'),
]