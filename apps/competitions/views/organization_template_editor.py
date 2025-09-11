from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DetailView
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from apps.competitions.models import Organization
from apps.competitions.models.organization_templates import OrganizationTemplate
from apps.competitions.forms.organization_template import OrganizationTemplateForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@method_decorator(staff_member_required, name='dispatch')
class OrganizationTemplateEditorView(UpdateView):
    """Ã‰diteur de template d'organisation avec prévisualisation"""
    model = OrganizationTemplate
    form_class = OrganizationTemplateForm
    template_name = 'organizations/admin/template_editor.html'
    
    def get_object(self):
        organization = get_object_or_404(Organization, pk=self.kwargs['pk'])
        template, created = OrganizationTemplate.objects.get_or_create(organization=organization)
        return template
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object.organization
        context['themes'] = OrganizationTemplate.THEME_CHOICES
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Template mis Ã  jour avec succès'
            })
        return response

@method_decorator(staff_member_required, name='dispatch')
class OrganizationTemplatePreviewView(DetailView):
    """Prévisualisation du template d'organisation"""
    model = OrganizationTemplate
    template_name = 'organizations/admin/template_preview.html'
    
    def get_object(self):
        organization = get_object_or_404(Organization, pk=self.kwargs['pk'])
        template, created = OrganizationTemplate.objects.get_or_create(organization=organization)
        return template
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object.organization
        context['theme_colors'] = self.object.get_theme_colors()
        context['videos'] = self.object.get_videos()
        context['images'] = self.object.get_images()
        context['social_links'] = self.object.get_social_links()
        return context

def preview_template_ajax(request, pk):
    """Prévisualisation AJAX du template"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    organization = get_object_or_404(Organization, pk=pk)
    template, created = OrganizationTemplate.objects.get_or_create(organization=organization)
    
    # Mise Ã  jour des données depuis la requÃªte AJAX
    if request.method == 'POST':
        data = request.POST
        template.theme = data.get('theme', template.theme)
        template.primary_color = data.get('primary_color', template.primary_color)
        template.secondary_color = data.get('secondary_color', template.secondary_color)
        template.accent_color = data.get('accent_color', template.accent_color)
        template.background_color = data.get('background_color', template.background_color)
        template.hero_title = data.get('hero_title', template.hero_title)
        template.hero_subtitle = data.get('hero_subtitle', template.hero_subtitle)
        template.about_title = data.get('about_title', template.about_title)
        template.about_content = data.get('about_content', template.about_content)
        template.save()
    
    return JsonResponse({
        'theme_colors': template.get_theme_colors(),
        'videos': template.get_videos(),
        'images': template.get_images(),
        'social_links': template.get_social_links(),
        'content': {
            'hero_title': template.hero_title,
            'hero_subtitle': template.hero_subtitle,
            'about_title': template.about_title,
            'about_content': template.about_content,
        }
    }) 

