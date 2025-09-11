"""
Vues pour les sites d'organisations en sous-domaine.
Gestion des templates spécialisés par type d'organisation.
"""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

from multitenant.models import Tenant
from competitions.models import Club, Federation, CoachProfile
from organizations.models import Organization
from competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
from competitions.utils.subdomain_generator import SubdomainGenerator
import logging

logger = logging.getLogger(__name__)

class OrganizationSiteView(TemplateView):
    """Vue de base pour les sites d'organisations."""
    
    def get_organization(self):
        """Récupère l'organisation associée au tenant actuel."""
        if not hasattr(self.request, 'tenant'):
            return None
        
        tenant = self.request.tenant
        
        # Essayer de récupérer via l'organisation moderne
        if hasattr(tenant, 'primary_organization_id') and tenant.primary_organization_id:
            try:
                return Organization.objects.get(id=tenant.primary_organization_id)
            except Organization.DoesNotExist:
                pass
        
        # Fallback : chercher dans les modèles legacy
        try:
            # Chercher un club associé au domaine
            clubs = Club.objects.filter(
                name__icontains=tenant.domain.split('.')[0].replace('-', ' ')
            )
            if clubs.exists():
                club = clubs.first()
                return getattr(club, 'organization', club)
            
            # Chercher une fédération
            federations = Federation.objects.filter(
                nom__icontains=tenant.domain.split('.')[0].replace('-', ' ')
            )
            if federations.exists():
                federation = federations.first()
                return getattr(federation, 'organization', federation)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'organisation: {e}")
        
        return None
    
    def get_organization_type(self, organization):
        """Détermine le type d'organisation."""
        if isinstance(organization, Club):
            return 'club'
        elif isinstance(organization, Federation):
            return 'federation'
        elif hasattr(organization, 'organization_type'):
            return organization.organization_type
        elif hasattr(organization, 'type'):
            return organization.type
        else:
            # Déduire du nom du modèle
            model_name = organization._meta.model_name.lower()
            if 'coach' in model_name:
                return 'coach'
            elif 'event' in model_name:
                return 'event'
            else:
                return 'club'  # Default
    
    def get_template_names(self):
        """Retourne le template approprié selon le type d'organisation."""
        organization = self.get_organization()
        if not organization:
            return ['organizations/sites/default_template.html']
        
        org_type = self.get_organization_type(organization)
        
        template_mapping = {
            'federation': 'organizations/sites/federation_template.html',
            'club': 'organizations/sites/club_template.html',
            'coach': 'organizations/sites/coach_template.html',
            'event': 'organizations/sites/event_template.html'
        }
        
        return [template_mapping.get(org_type, 'organizations/sites/club_template.html')]
    
    def get_context_data(self, **kwargs):
        """Ajoute les données de l'organisation au contexte."""
        context = super().get_context_data(**kwargs)
        
        organization = self.get_organization()
        if not organization:
            context.update({
                'organization': None,
                'error': 'Organisation non trouvée'
            })
            return context
        
        org_type = self.get_organization_type(organization)
        
        # Données de base
        context.update({
            'organization': organization,
            'organization_type': org_type,
            'tenant': getattr(self.request, 'tenant', None)
        })
        
        # Données spécifiques selon le type
        if org_type == 'federation':
            context.update(self.get_federation_context(organization))
        elif org_type == 'club':
            context.update(self.get_club_context(organization))
        elif org_type == 'coach':
            context.update(self.get_coach_context(organization))
        
        return context
    
    def get_federation_context(self, federation):
        """Context spécifique aux fédérations."""
        return {
            'upcoming_competitions': self.get_upcoming_competitions(federation),
            'recent_news': self.get_recent_news(federation),
            'affiliated_clubs': self.get_affiliated_clubs(federation),
            'disciplines': self.get_disciplines(federation),
            'statistics': self.get_federation_statistics(federation)
        }
    
    def get_club_context(self, club):
        """Context spécifique aux clubs."""
        return {
            'courses': self.get_courses(club),
            'instructors': self.get_instructors(club),
            'schedule': self.get_schedule(club),
            'testimonials': self.get_testimonials(club),
            'recent_events': self.get_recent_events(club),
            'next_competitions': self.get_next_competitions(club)
        }
    
    def get_coach_context(self, coach):
        """Context spécifique aux coachs."""
        return {
            'services': self.get_coach_services(coach),
            'availability': self.get_coach_availability(coach),
            'certifications': self.get_coach_certifications(coach),
            'client_testimonials': self.get_coach_testimonials(coach),
            'specializations': self.get_coach_specializations(coach)
        }
    
    def get_upcoming_competitions(self, organization):
        """Récupère les compétitions à venir."""
        try:
            from competitions.models import Competition
            return Competition.objects.filter(
                date_debut__gte=timezone.now(),
                is_active=True
            ).order_by('date_debut')[:5]
        except:
            return []
    
    def get_recent_news(self, organization):
        """Récupère les actualités récentes."""
        # Placeholder - à implémenter selon le modèle d'actualités
        return []
    
    def get_affiliated_clubs(self, federation):
        """Récupère les clubs affiliés à une fédération."""
        try:
            if hasattr(federation, 'affiliated_clubs'):
                return federation.affiliated_clubs.filter(is_active=True)
            return []
        except:
            return []
    
    def get_disciplines(self, organization):
        """Récupère les disciplines de l'organisation."""
        try:
            if hasattr(organization, 'disciplines'):
                return organization.disciplines.all()
            return []
        except:
            return []
    
    def get_courses(self, club):
        """Récupère les cours du club."""
        try:
            if hasattr(club, 'courses'):
                return club.courses.filter(is_active=True)
            return []
        except:
            return []
    
    def get_instructors(self, club):
        """Récupère les instructeurs du club."""
        try:
            if hasattr(club, 'instructors'):
                return club.instructors.filter(is_active=True)
            return []
        except:
            return []
    
    def get_schedule(self, club):
        """Récupère le planning du club."""
        # Placeholder - à implémenter selon le modèle de planning
        return {}
    
    def get_testimonials(self, organization):
        """Récupère les témoignages."""
        # Placeholder - à implémenter selon le modèle de témoignages
        return []
    
    def get_recent_events(self, organization):
        """Récupère les événements récents."""
        return []
    
    def get_next_competitions(self, organization):
        """Récupère les prochaines compétitions."""
        return self.get_upcoming_competitions(organization)
    
    def get_federation_statistics(self, federation):
        """Récupère les statistiques d'une fédération."""
        try:
            return {
                'member_count': getattr(federation, 'member_count', 0),
                'club_count': self.get_affiliated_clubs(federation).count(),
                'discipline_count': self.get_disciplines(federation).count(),
                'competition_count': self.get_upcoming_competitions(federation).count()
            }
        except:
            return {
                'member_count': 0,
                'club_count': 0,
                'discipline_count': 0,
                'competition_count': 0
            }
    
    def get_coach_services(self, coach):
        """Récupère les services d'un coach."""
        # Placeholder
        return []
    
    def get_coach_availability(self, coach):
        """Récupère les disponibilités d'un coach."""
        # Placeholder
        return {}
    
    def get_coach_certifications(self, coach):
        """Récupère les certifications d'un coach."""
        try:
            if hasattr(coach, 'certifications'):
                return coach.certifications.all()
            return []
        except:
            return []
    
    def get_coach_testimonials(self, coach):
        """Récupère les témoignages clients d'un coach."""
        return []
    
    def get_coach_specializations(self, coach):
        """Récupère les spécialisations d'un coach."""
        try:
            if hasattr(coach, 'specializations'):
                return coach.specializations.all()
            return []
        except:
            return []

# Vue principale pour les sites d'organisations
organization_site_view = OrganizationSiteView.as_view()

def organization_register_view(request):
    """Vue d'inscription spécifique à une organisation."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return render(request, 'error.html', {'error': 'Organisation non trouvée'})
    
    # Rediriger vers le processus d'onboarding avec le contexte de l'organisation
    from django.urls import reverse
    from django.shortcuts import redirect
    
    # Ajouter l'organisation en session pour le processus d'onboarding
    request.session['organization_context'] = {
        'id': organization.id,
        'type': OrganizationSiteView().get_organization_type(organization),
        'name': getattr(organization, 'name', '') or getattr(organization, 'nom', '')
    }
    
    return redirect('onboarding:role')

def organization_qr_code_view(request, qr_type='register'):
    """Vue pour afficher les QR codes d'une organisation."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return JsonResponse({'error': 'Organisation non trouvée'}, status=404)
    
    # Générer ou récupérer les QR codes
    cache_key = f"qr_codes_{organization.id}_{qr_type}"
    qr_codes = cache.get(cache_key)
    
    if not qr_codes:
        try:
            qr_codes = generate_organization_qr_codes_set(organization)
            cache.set(cache_key, qr_codes, 3600)  # Cache for 1 hour
        except Exception as e:
            logger.error(f"Erreur génération QR codes pour {organization}: {e}")
            return JsonResponse({'error': 'Erreur génération QR codes'}, status=500)
    
    if qr_type not in qr_codes:
        return JsonResponse({'error': 'Type de QR code non trouvé'}, status=404)
    
    url, file_path = qr_codes[qr_type]
    
    return JsonResponse({
        'qr_url': url,
        'qr_image': f"{settings.MEDIA_URL}{file_path}",
        'organization': {
            'name': getattr(organization, 'name', '') or getattr(organization, 'nom', ''),
            'type': OrganizationSiteView().get_organization_type(organization)
        }
    })

@login_required
def organization_admin_view(request):
    """Vue d'administration pour les organisations."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return render(request, 'error.html', {'error': 'Organisation non trouvée'})
    
    # Vérifier les permissions
    if not request.user.has_perm('competitions.change_organization', organization):
        return render(request, 'error.html', {'error': 'Permissions insuffisantes'})
    
    # Générer les QR codes si nécessaire
    qr_codes = generate_organization_qr_codes_set(organization)
    
    context = {
        'organization': organization,
        'qr_codes': qr_codes,
        'tenant': getattr(request, 'tenant', None),
        'subdomain_url': SubdomainGenerator().get_organization_subdomain_url(organization)
    }
    
    return render(request, 'organizations/admin/site_management.html', context)

def organization_contact_view(request):
    """Vue de contact pour une organisation."""
    if request.method == 'POST':
        # Traiter le formulaire de contact
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Ici on pourrait envoyer un email, enregistrer en base, etc.
        # Pour l'instant, on retourne juste un succès
        
        return JsonResponse({
            'success': True,
            'message': 'Message envoyé avec succès!'
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def organization_check_in_view(request):
    """Vue pour le check-in via QR code."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode POST requise'}, status=405)
    
    qr_data = request.POST.get('qr_data')
    if not qr_data:
        return JsonResponse({'error': 'Données QR manquantes'}, status=400)
    
    # Traiter le check-in
    # Cette logique dépendrait du système de gestion des présences
    
    return JsonResponse({
        'success': True,
        'message': 'Check-in effectué avec succès!'
    })

def create_organization_site(request):
    """Vue pour créer un site d'organisation (pour les admins)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissions insuffisantes'}, status=403)
    
    if request.method == 'POST':
        organization_id = request.POST.get('organization_id')
        
        try:
            organization = Organization.objects.get(id=organization_id)
            generator = SubdomainGenerator()
            tenant = generator.create_tenant_for_organization(organization)
            
            # Générer les QR codes initiaux
            qr_codes = generate_organization_qr_codes_set(organization)
            
            return JsonResponse({
                'success': True,
                'tenant_domain': tenant.domain,
                'site_url': f"https://{tenant.domain}",
                'qr_codes_generated': len(qr_codes)
            })
            
        except Organization.DoesNotExist:
            return JsonResponse({'error': 'Organisation non trouvée'}, status=404)
        except Exception as e:
            logger.error(f"Erreur création site organisation: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - afficher le formulaire
    organizations = Organization.objects.filter(tenant__isnull=True)
    context = {
        'organizations': organizations
    }
    
    return render(request, 'organizations/admin/create_site.html', context)

def organization_site_status(request):
    """API pour vérifier le statut d'un site d'organisation."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return JsonResponse({'error': 'Organisation non trouvée'}, status=404)
    
    tenant = getattr(request, 'tenant', None)
    
    status = {
        'organization_id': organization.id,
        'organization_name': getattr(organization, 'name', '') or getattr(organization, 'nom', ''),
        'organization_type': OrganizationSiteView().get_organization_type(organization),
        'tenant_domain': tenant.domain if tenant else None,
        'site_active': tenant.is_active if tenant else False,
        'has_qr_codes': bool(getattr(organization, 'qr_code_register', None)),
        'member_count': getattr(organization, 'member_count', 0),
        'last_activity': timezone.now().isoformat()
    }
    
    return JsonResponse(status)