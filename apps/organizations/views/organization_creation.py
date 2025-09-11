from django.core.exceptions import PermissionDenied
"""
Vues pour la création d'organisations avec feedback en temps réel.
"""
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils.translation import gettext as _

from ..models import Organization, OrganizationType
from ..forms import OrganizationForm
try:
    from apps.multitenant.models import Tenant
except Exception:
    Tenant = None
from apps.competitions.utils.subdomain_generator import SubdomainGenerator
from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def create_organization_with_feedback(request):
    """
    Vue pour créer une organisation avec feedback en temps réel.
    """
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Création de l'organisation
                    organization = form.save(commit=False)
                    organization.created_by = request.user
                    organization.save()
                    
                    # Les signaux automatiques s'occupent du reste
                    # (création du tenant, génération des QR codes, notifications)
                    
                    messages.success(request, _("Organisation créée avec succès! Site web en cours de génération."))
                    
                    return redirect('organizations:detail', pk=organization.pk)
                    
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'organisation: {e}")
                messages.error(request, _("Erreur lors de la création de l'organisation."))
        else:
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = OrganizationForm()
    
    return render(request, 'organizations/create_with_feedback.html', {
        'form': form,
        'organization_types': OrganizationType.choices
    })

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_organization_ajax(request):
    """
    Vue AJAX pour créer une organisation avec feedback en temps réel.
    """
    try:
        data = json.loads(request.body)
        form = OrganizationForm(data, request.FILES)
        
        if form.is_valid():
            with transaction.atomic():
                # Création de l'organisation
                organization = form.save(commit=False)
                organization.created_by = request.user
                organization.save()
                
                # Attendre un peu pour que les signaux se déclenchent
                import time
                time.sleep(1)
                
                # Récupérer les informations générées
                tenant = getattr(organization, 'tenant', None)
                qr_codes = generate_organization_qr_codes_set(organization)
                
                response_data = {
                    'success': True,
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'site_url': f"https://{tenant.domain}" if tenant else None,
                    'admin_url': f"https://{tenant.domain}/admin/" if tenant else None,
                    'qr_codes_count': len(qr_codes),
                    'qr_codes': list(qr_codes.keys()),
                    'message': _("Organisation créée avec succès!")
                }
                
                return JsonResponse(response_data)
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(error) for error in field_errors]
            
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': _("Veuillez corriger les erreurs dans le formulaire.")
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Données invalides.")
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la création AJAX de l'organisation: {e}")
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la création de l'organisation.")
        }, status=500)

@login_required
def organization_preview(request):
    """
    Vue de prévisualisation du site web avant création.
    """
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            # Créer une prévisualisation
            organization_data = form.cleaned_data
            
            # Générer le sous-domaine préliminaire
            generator = SubdomainGenerator()
            subdomain = generator.generate_subdomain_preview(organization_data['name'])
            
            preview_data = {
                'name': organization_data['name'],
                'organization_type': organization_data['organization_type'],
                'description': organization_data.get('description', ''),
                'subdomain': subdomain,
                'full_domain': f"{subdomain}.martialcomp.com",
                'template': 'default',  # Template par défaut
                'colors': {
                    'primary': '#e74c3c',
                    'secondary': '#2c3e50',
                    'accent': '#3498db'
                }
            }
            
            return render(request, 'organizations/preview.html', preview_data)
    else:
        form = OrganizationForm()
    
    return render(request, 'organizations/create_with_preview.html', {
        'form': form,
        'organization_types': OrganizationType.choices
    })

@login_required
def organization_status(request, organization_id):
    """
    API pour vérifier le statut de création d'une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id, created_by=request.user)
        
        tenant = getattr(organization, 'tenant', None)
        qr_codes = generate_organization_qr_codes_set(organization)
        
        status = {
            'organization_id': organization.id,
            'organization_name': organization.name,
            'organization_type': organization.get_organization_type_display(),
            'tenant_domain': tenant.domain if tenant else None,
            'site_active': tenant.is_active if tenant else False,
            'has_qr_codes': len(qr_codes) > 0,
            'qr_codes_count': len(qr_codes),
            'qr_codes_types': list(qr_codes.keys()),
            'site_url': f"https://{tenant.domain}" if tenant else None,
            'admin_url': f"https://{tenant.domain}/admin/" if tenant else None,
            'creation_complete': tenant is not None and len(qr_codes) > 0
        }
        
        return JsonResponse(status)
        
    except Organization.DoesNotExist:
        return JsonResponse({
            'error': _("Organisation non trouvée.")
        }, status=404)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        return JsonResponse({
            'error': _("Erreur lors de la vérification du statut.")
        }, status=500)

@login_required
def organization_qr_codes(request, organization_id):
    """
    Vue pour afficher et télécharger les QR codes d'une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id, created_by=request.user)
        
        # Générer ou récupérer les QR codes
        qr_codes = generate_organization_qr_codes_set(organization)
        
        context = {
            'organization': organization,
            'qr_codes': qr_codes,
            'tenant': getattr(organization, 'tenant', None)
        }
        
        return render(request, 'organizations/qr_codes.html', context)
        
    except Organization.DoesNotExist:
        messages.error(request, _("Organisation non trouvée."))
        return redirect('organizations:list')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des QR codes: {e}")
        messages.error(request, _("Erreur lors de l'affichage des QR codes."))
        return redirect('organizations:list')

@login_required
def organization_site_admin(request, organization_id):
    """
    Vue d'administration du site web d'une organisation.
    """
    try:
        organization = Organization.objects.get(id=organization_id, created_by=request.user)
        
        tenant = getattr(organization, 'tenant', None)
        qr_codes = generate_organization_qr_codes_set(organization)
        
        context = {
            'organization': organization,
            'tenant': tenant,
            'qr_codes': qr_codes,
            'site_url': f"https://{tenant.domain}" if tenant else None,
            'admin_url': f"https://{tenant.domain}/admin/" if tenant else None
        }
        
        return render(request, 'organizations/site_admin.html', context)
        
    except Organization.DoesNotExist:
        messages.error(request, _("Organisation non trouvée."))
        return redirect('organizations:list')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'administration: {e}")
        messages.error(request, _("Erreur lors de l'affichage de l'administration."))
        return redirect('organizations:list') 

