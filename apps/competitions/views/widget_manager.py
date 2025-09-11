from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from apps.competitions.models import Organization
from apps.competitions.models.organization_templates import OrganizationTemplate
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import json

@staff_member_required
def widget_builder_page(request, pk):
    """Affiche la page React de gestion des widgets pour une organisation"""
    org = get_object_or_404(Organization, pk=pk)
    return render(request, 'organizations/admin/widget_builder.html', {'organization': org})

@staff_member_required
@csrf_exempt
def widget_config_api(request, pk):
    """API pour charger/sauvegarder la config des widgets d'une organisation"""
    try:
        template = OrganizationTemplate.objects.get(organization_id=pk)
    except OrganizationTemplate.DoesNotExist:
        return JsonResponse({'error': 'Template non trouvé'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({'widgets': template.get_widgets()}, status=200)
    elif request.method == 'POST':
        data = json.loads(request.body)
        template.widgets = data.get('widgets', {})
        template.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@staff_member_required
def widget_config(request, pk, widget_type):
    """Configuration d'un widget spécifique"""
    available_widgets = get_available_widgets()
    
    if widget_type not in available_widgets:
        return JsonResponse({'error': 'Widget non trouvé'}, status=404)
    
    widget_info = available_widgets[widget_type]
    
    if request.method == 'POST':
        config = json.loads(request.body)
        template = OrganizationTemplate.objects.get(organization_id=pk)
        template.add_widget(widget_type, config)
        return JsonResponse({'success': True, 'message': 'Widget configuré'})
    
    return JsonResponse({
        'widget': widget_info,
        'config': widget_info.get('config', {})
    }) 

