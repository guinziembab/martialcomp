"""
Tags de template pour la gestion des tenants.
"""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
import os

register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_name(context):
    """
    Retourne le nom du tenant actuel.
    """
    tenant = context.get('tenant')
    if tenant:
        return tenant.name
    return "MartialComp"


@register.simple_tag(takes_context=True)
def tenant_logo(context, size='default'):
    """
    Retourne le HTML du logo du tenant actuel.
    """
    tenant = context.get('tenant')
    if not tenant or not hasattr(tenant, 'logos'):
        # Logo par défaut
        return mark_safe(f'<img src="{settings.STATIC_URL}img/logo.png" alt="MartialComp" class="logo-{size}">')
    
    logos = tenant.logos
    
    if size == 'small':
        width = "30"
        height = "30"
    elif size == 'large':
        width = "200"
        height = "60"
    else:
        width = "120"
        height = "40"
    
    return mark_safe(f'<img src="{logos.logo.url}" alt="{tenant.name}" width="{width}" height="{height}" class="logo-{size}">')


@register.simple_tag(takes_context=True)
def tenant_social_links(context):
    """
    Retourne les liens sociaux du tenant.
    """
    tenant = context.get('tenant')
    if not tenant or not hasattr(tenant, 'social_links'):
        return ""
    
    links = tenant.social_links.all()
    if not links.exists():
        return ""
    
    html = '<div class="tenant-social-links">'
    for link in links:
        html += f'<a href="{link.url}" target="_blank" class="social-link" title="{link}">'
        html += f'<i class="{link.icon_class}"></i></a> '
    html += '</div>'
    
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def tenant_css_variables(context):
    """
    Génère les variables CSS pour le tenant.
    """
    tenant = context.get('tenant')
    if not tenant or not hasattr(tenant, 'theme'):
        return ""
    
    theme = tenant.theme
    
    css = """
    <style>
        :root {
            --primary-color: %s;
            --secondary-color: %s;
            --accent-color: %s;
            --text-color: %s;
            --background-color: %s;
        }
    </style>
    """ % (
        theme.primary_color,
        theme.secondary_color,
        theme.accent_color,
        theme.text_color,
        theme.background_color
    )
    
    return mark_safe(css)


@register.simple_tag(takes_context=True)
def tenant_analytics(context):
    """
    Génère les scripts d'analytics pour le tenant.
    """
    tenant = context.get('tenant')
    if not tenant or not hasattr(tenant, 'analytics'):
        return ""
    
    analytics = tenant.analytics
    html = ""
    
    # Google Analytics
    if analytics.ga_tracking_id:
        html += """
        <script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '%s');
        </script>
        """ % (analytics.ga_tracking_id, analytics.ga_tracking_id)
    
    # Facebook Pixel
    if analytics.facebook_pixel_id:
        html += """
        <script>
            !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
            n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
            document,'script','https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', '%s');
            fbq('track', 'PageView');
        </script>
        <noscript>
            <img height="1" width="1" style="display:none" 
                 src="https://www.facebook.com/tr?id=%s&ev=PageView&noscript=1"/>
        </noscript>
        """ % (analytics.facebook_pixel_id, analytics.facebook_pixel_id)
    
    # Hotjar
    if analytics.hotjar_id:
        html += """
        <script>
            (function(h,o,t,j,a,r){
                h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
                h._hjSettings={hjid:%s,hjsv:6};
                a=o.getElementsByTagName('head')[0];
                r=o.createElement('script');r.async=1;
                r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
                a.appendChild(r);
            })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
        </script>
        """ % analytics.hotjar_id
    
    # Autres scripts
    if analytics.other_scripts:
        html += analytics.other_scripts
    
    return mark_safe(html)


@register.filter
def file_exists(file_path):
    """
    Vérifie si un fichier statique existe.
    """
    if not file_path:
        return False
    
    # Chemins Ã  vérifier
    paths_to_check = [
        os.path.join(settings.STATIC_ROOT, file_path),
        os.path.join(settings.BASE_DIR, 'static', file_path),
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            return True
    
    return False


@register.simple_tag(takes_context=True)
def tenant_menu(context):
    """
    Génère le menu du tenant.
    """
    tenant = context.get('tenant')
    if not tenant or not hasattr(tenant, 'menu_items'):
        return ""
    
    menu_items = tenant.menu_items.filter(
        parent__isnull=True, 
        is_active=True
    ).order_by('position')
    
    if not menu_items.exists():
        return ""
    
    html = '<ul class="navbar-nav tenant-menu">'
    for item in menu_items:
        active = context.get('request').path == item.url
        target = '_blank' if item.open_in_new_tab else '_self'
        
        html += f'<li class="nav-item {" active" if active else ""}">'
        html += f'<a href="{item.url}" target="{target}" class="nav-link">{item.title}</a>'
        html += '</li>'
    
    html += '</ul>'
    
    return mark_safe(html)


@register.simple_tag
def tenant_asset(tenant, asset_type, default=None):
    """
    Retourne l'URL d'un asset du tenant (logo, favicon, etc.).
    """
    if not tenant:
        return default or ""
    
    # Logo
    if asset_type == 'logo' and hasattr(tenant, 'logos'):
        return tenant.logos.logo.url
    
    # Logo alternatif
    elif asset_type == 'logo_alt' and hasattr(tenant, 'logos') and tenant.logos.logo_alt:
        return tenant.logos.logo_alt.url
    
    # Favicon
    elif asset_type == 'favicon' and hasattr(tenant, 'logos') and tenant.logos.favicon:
        return tenant.logos.favicon.url
    
    # Logo pour impression
    elif asset_type == 'logo_print' and hasattr(tenant, 'logos') and tenant.logos.logo_print:
        return tenant.logos.logo_print.url
    
    # Retourner la valeur par défaut si aucun asset trouvé
    return default or ""
