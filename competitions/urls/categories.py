# urls/categories.py
from django.urls import path
from ..views import categories

app_name = 'categories'

urlpatterns = [
    # Templates de catégories
    path('templates/', categories.category_templates_list, name='templates_list'),
    path('templates/create/', categories.category_template_create, name='template_create'),
    # Les méthodes edit et delete pour les templates ne semblent pas être implémentées dans views/categories.py
    # mais je les laisse pour cohérence avec la structure, à implémenter si nécessaire
    # path('templates/<int:pk>/edit/', categories.category_template_edit, name='template_edit'),
    # path('templates/<int:pk>/delete/', categories.category_template_delete, name='template_delete'),
    
    # Catégories de compétition
    path('competition/<int:competition_id>/', categories.competition_categories, name='competition_categories'),
    path('competition/<int:competition_id>/create/<int:type_id>/', categories.category_create, name='create'),
    path('<int:pk>/edit/', categories.category_update, name='update'),
    path('<int:category_id>/delete/', categories.category_delete, name='delete'),
    path('competition/<int:competition_id>/auto-generate/', categories.auto_generate_categories, name='auto_generate'),
    path('competition/<int:competition_id>/import-templates/', categories.import_templates, name='import_templates'),
    
    # Vue pour les participants d'une catégorie (si nécessaire)
    path('<int:category_id>/participants/', categories.category_participants, name='participants'),
]