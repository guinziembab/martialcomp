from django.urls import path
from apps.competitions.views.organization_admin import OrganizationAdminListView, OrganizationAdminDetailView, RegenerateQRCodesView
from apps.competitions.views.organization_template_editor import OrganizationTemplateEditorView, OrganizationTemplatePreviewView, preview_template_ajax
from apps.competitions.views.widget_manager import widget_builder_page, widget_config_api

urlpatterns = [
    path('', OrganizationAdminListView.as_view(), name='organization_admin_list'),
    path('<int:pk>/', OrganizationAdminDetailView.as_view(), name='organization_admin_detail'),
    path('<int:pk>/regenerate_qr/', RegenerateQRCodesView.as_view(), name='organization_admin_regenerate_qr'),
    path('<int:pk>/template/', OrganizationTemplateEditorView.as_view(), name='organization_template_editor'),
    path('<int:pk>/template/preview/', OrganizationTemplatePreviewView.as_view(), name='organization_template_preview'),
    path('<int:pk>/template/preview/ajax/', preview_template_ajax, name='preview_template_ajax'),
    path('<int:pk>/widgets/', widget_builder_page, name='organization_widget_builder'),
    path('<int:pk>/widgets/api/', widget_config_api, name='organization_widget_config_api'),
] 
