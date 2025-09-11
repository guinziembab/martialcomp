"""
Middleware pour la gestion des thèmes personnalisés par tenant.
"""
from django.urls import resolve
from django.http import Http404
from django.utils.functional import SimpleLazyObject
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from apps.multitenant.models import Tenant
from apps.multitenant.utils import get_tenant_for_request


def get_tenant_theme(request):
    """
    Récupère les données de thème pour le tenant actuel.
    """
    if not hasattr(request, 'tenant') or not request.tenant:
        return None
    
    tenant = request.tenant
    
    # Créer un objet de données de thème
    theme_data = {
        'tenant': tenant,
        'name': tenant.name,
        'domain': tenant.domain,
        'subdomain': tenant.subdomain,
        'schema_name': tenant.schema_name,
        'subscription_plan': tenant.subscription_plan,
    }
    
    # Ajouter les données de thème si disponibles
    if hasattr(tenant, 'theme'):
        theme = tenant.theme
        theme_data.update({
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'accent_color': theme.accent_color,
            'text_color': theme.text_color,
            'background_color': theme.background_color,
            'navbar_class': theme.navbar_class,
            'footer_class': theme.footer_class,
            'custom_css': theme.custom_css,
            'custom_js': theme.custom_js,
            'display_name_in_navbar': theme.display_name_in_navbar,
            'white_label': theme.white_label,
        })
    
    # Ajouter les logos si disponibles
    if hasattr(tenant, 'logos'):
        logos = tenant.logos
        theme_data.update({
            'logo': logos.logo,
            'logo_alt': logos.logo_alt,
            'favicon': logos.favicon,
            'logo_print': logos.logo_print,
        })
    
    # Ajouter les infos de contact si disponibles
    if hasattr(tenant, 'contact_info'):
        contact = tenant.contact_info
        theme_data.update({
            'email': contact.email,
            'phone': contact.phone,
            'address': contact.address,
            'footer_text': contact.footer_text,
        })
    
    # Ajouter les liens sociaux s'ils existent
    if hasattr(tenant, 'social_links'):
        theme_data['social_links'] = tenant.social_links.all()
    
    # Ajouter les éléments de menu personnalisés s'ils existent
    if hasattr(tenant, 'menu_items'):
        # Récupérer seulement les éléments de premier niveau actifs
        theme_data['menu_items'] = tenant.menu_items.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('position')
    
    # Ajouter les données d'analytics si disponibles
    if hasattr(tenant, 'analytics'):
        analytics = tenant.analytics
        theme_data.update({
            'analytics_id': analytics.ga_tracking_id,
            'facebook_pixel_id': analytics.facebook_pixel_id,
            'hotjar_id': analytics.hotjar_id,
            'analytics_scripts': analytics.other_scripts,
        })
    
    # Déterminer si le tenant a droit au white-label (plan Champion seulement)
    if tenant.subscription_plan != 'champion' and 'white_label' in theme_data:
        theme_data['white_label'] = False
    
    return theme_data


class TenantThemeMiddleware(MiddlewareMixin):
    """
    Middleware qui ajoute les informations de thème du tenant Ã  la requÃªte.
    """
    def process_request(self, request):
        """
        Ajoute les données de thème Ã  la requÃªte.
        """
        # Utiliser un SimpleLazyObject pour la performance
        request.tenant_theme = SimpleLazyObject(lambda: get_tenant_theme(request))
    
    def process_template_response(self, request, response):
        """
        Ajoute le contexte de thème Ã  la réponse template.
        """
        if hasattr(response, 'context_data'):
            theme_data = getattr(request, 'tenant_theme', None)
            if theme_data:
                response.context_data['tenant_theme'] = theme_data
        
        return response


class TenantTemplateMiddleware(MiddlewareMixin):
    """
    Middleware qui sélectionne les templates spécifiques au tenant quand ils existent.
    """
    def process_template_response(self, request, response):
        """
        Modifie le template Ã  utiliser si une version spécifique au tenant existe.
        """
        if not hasattr(response, 'template_name') or not response.template_name:
            return response
        
        # Si pas de tenant, on ne fait rien
        if not hasattr(request, 'tenant') or not request.tenant:
            return response
        
        # Récupérer le template original
        original_template = response.template_name
        
        # S'il s'agit d'une liste, on traite chaque template
        if isinstance(original_template, (list, tuple)):
            # Créer une nouvelle liste avec les templates spécifiques au tenant en premier
            tenant_templates = []
            for template in original_template:
                # Convertir le nom du template pour inclure le tenant
                tenant_template = self._get_tenant_template_name(template, request.tenant)
                if tenant_template:
                    tenant_templates.append(tenant_template)
            
            # Ajouter les templates originaux après
            tenant_templates.extend(original_template)
            
            # Mettre Ã  jour le template_name dans la réponse
            response.template_name = tenant_templates
        else:
            # Template unique
            tenant_template = self._get_tenant_template_name(original_template, request.tenant)
            if tenant_template:
                # Créer une liste avec le template spécifique au tenant en premier
                response.template_name = [tenant_template, original_template]
        
        return response
    
    def _get_tenant_template_name(self, template_name, tenant):
        """
        Génère le nom de template spécifique au tenant.
        """
        # Ignore déjÃ  les templates tenant
        if template_name.startswith('tenant/'):
            return None
        
        # Construire le chemin du template spécifique au tenant
        parts = template_name.split('/')
        
        # Insérer le dossier du tenant avant le nom du fichier
        if len(parts) > 1:
            tenant_path = f"{'/'.join(parts[:-1])}/tenant/{tenant.schema_name}/{parts[-1]}"
        else:
            tenant_path = f"tenant/{tenant.schema_name}/{template_name}"
        
        return tenant_path

