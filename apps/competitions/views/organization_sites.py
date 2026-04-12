from django.core.exceptions import PermissionDenied
"""
Vues pour les sites d'organisations en sous-domaine.
Gestion des templates spécialisés par type d'organisation.
"""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import datetime, timedelta

try:
    from apps.multitenant.models import Tenant
except Exception:
    Tenant = None
from apps.competitions.models import Club, Federation, CoachProfile
from apps.organizations.models import Organization
from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
from apps.competitions.utils.subdomain_generator import SubdomainGenerator
import logging

logger = logging.getLogger(__name__)

class OrganizationSiteView(TemplateView):
    """Vue de base pour les sites d'organisations."""
    # Permettre l'accès public aux sites d'organisations
    # pour que les visiteurs puissent voir le contenu
    
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
        
        # Nouvelle logique : chercher par slug du tenant
        try:
            # Extraire le slug de l'organisation du slug du tenant
            # fed-federation-test-fix -> federation-test-fix
            if tenant.slug.startswith('fed-'):
                federation_slug = tenant.slug[4:]  # Enlever 'fed-'
                federation = Federation.objects.filter(slug=federation_slug).first()
                if federation:
                    return federation.organization if federation.organization else federation
            
            # Chercher par nom tenant
            federation = Federation.objects.filter(name=tenant.name).first()
            if federation:
                return federation.organization if federation.organization else federation
                
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
            org_type = organization.organization_type
            # Normaliser les types de fédération vers 'federation'
            if 'federation' in org_type.lower():
                return 'federation'
            return org_type
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
                'error': _('Organisation non trouvée')
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
            'next_competitions': self.get_next_competitions(club),
            'recent_news': self.get_recent_news(club)
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
        """Récupère les compétitions ET événements à venir pour une organisation."""
        try:
            from apps.competitions.models import Competition, Event
            today = timezone.now().date()

            # Liste combinée d'événements
            upcoming_items = []

            # 1. Récupérer les compétitions
            try:
                competitions = Competition.objects.filter(
                    organizing_organization=organization,
                    start_date__gte=today
                ).select_related('discipline').order_by('start_date')[:6]

                for comp in competitions:
                    upcoming_items.append({
                        'type': 'competition',
                        'title': comp.title,
                        'start_date': comp.start_date,
                        'venue_name': getattr(comp, 'venue_name', '') or getattr(comp, 'location', ''),
                        'city': getattr(comp, 'city', ''),
                        'discipline': getattr(comp, 'discipline', None),
                        'obj': comp
                    })
                logger.info(f"[get_upcoming_competitions] Found {competitions.count()} competitions")
            except Exception as e:
                logger.debug(f"Erreur récupération compétitions: {e}")

            # 2. Récupérer les événements (stages, séminaires, etc.)
            try:
                events = Event.objects.filter(
                    organization=organization,
                    start_date__gte=today,
                    visibility__in=['public', 'members']  # Exclure les privés
                ).order_by('start_date')[:6]

                for event in events:
                    upcoming_items.append({
                        'type': 'event',
                        'title': event.title,
                        'start_date': event.start_date,
                        'venue_name': getattr(event, 'location', ''),
                        'city': getattr(event, 'city', ''),
                        'discipline': None,
                        'event_type': event.event_type,
                        'obj': event
                    })
                logger.info(f"[get_upcoming_competitions] Found {events.count()} events")
            except Exception as e:
                logger.debug(f"Erreur récupération événements: {e}")

            # Trier par date et limiter à 6
            upcoming_items.sort(key=lambda x: x['start_date'])
            upcoming_items = upcoming_items[:6]

            logger.info(f"[get_upcoming_competitions] Org ID={organization.id}, "
                       f"total {len(upcoming_items)} items for dates >= {today}")

            return upcoming_items
        except Exception as e:
            logger.error(f"Erreur récupération compétitions/events pour org {getattr(organization, 'id', 'unknown')}: {e}")
            return []
    
    def get_recent_news(self, organization):
        """Recupere les actualites recentes publiees."""
        try:
            from apps.organizations.models import OrganizationNews
            return OrganizationNews.get_published_for_organization(organization, limit=10)
        except Exception as e:
            logger.error(f"Erreur recuperation news pour org {getattr(organization, 'id', 'unknown')}: {e}")
            return []
    
    def get_affiliated_clubs(self, federation):
        """Récupère les clubs affiliés Ã  une fédération."""
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
        # Placeholder - Ã  implémenter selon le modèle de planning
        return {}
    
    def get_testimonials(self, organization):
        """Récupère les témoignages."""
        # Placeholder - Ã  implémenter selon le modèle de témoignages
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
    """Vue d'inscription spécifique Ã  une organisation."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Rediriger vers le processus d'onboarding avec le contexte de l'organisation
    from django.urls import reverse
    from django.shortcuts import redirect
    
    # Ajouter l'organisation en session pour le processus d'onboarding
    request.session['organization_context'] = {
        'id': organization.id,
        'type': OrganizationSiteView().get_organization_type(organization),
        'name': getattr(organization, 'name', '') or getattr(organization, 'nom', '')
    }
    
    # Redirection vers l'onboarding unifié
    try:
        return redirect('competitions:onboarding:role_selection')
    except Exception:
        # Fallback si le nom d'URL n'est pas disponible
        from django.urls import reverse
        return redirect(reverse('competitions:onboarding:role_selection'))

def organization_qr_code_view(request, qr_type='register'):
    """Vue pour afficher les QR codes d'une organisation."""
    organization = OrganizationSiteView().get_organization()
    if not organization:
        return JsonResponse({'error': _('Organisation non trouvée')}, status=404)
    
    # Générer ou récupérer les QR codes
    cache_key = f"qr_codes_{organization.id}_{qr_type}"
    qr_codes = cache.get(cache_key)
    
    if not qr_codes:
        try:
            qr_codes = generate_organization_qr_codes_set(organization)
            cache.set(cache_key, qr_codes, 3600)  # Cache for 1 hour
        except Exception as e:
            logger.error(f"Erreur génération QR codes pour {organization}: {e}")
            return JsonResponse({'error': _('Erreur génération QR codes')}, status=500)

    if qr_type not in qr_codes:
        return JsonResponse({'error': _('Type de QR code non trouvé')}, status=404)
    
    url, file_path = qr_codes[qr_type]
    try:
        file_path_url = f"{settings.MEDIA_URL}{file_path}".replace('\\\\', '/').replace('\\', '/')
    except Exception:
        file_path_url = f"{settings.MEDIA_URL}{file_path}"
    
    return JsonResponse({
        'qr_url': url,
        'qr_image': file_path_url,
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
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Vérifier les permissions
    if not request.user.has_perm('competitions.change_organization', organization):
        return render(request, 'error.html', {'error': _('Permissions insuffisantes')})
    
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
            'message': _('Message envoyé avec succès!')
        })
    
    return JsonResponse({'error': _('Méthode non autorisée')}, status=405)


def organization_check_in_view(request):
    """Vue pour le check-in via QR code."""
    if request.method != 'POST':
        return JsonResponse({'error': _('Méthode POST requise')}, status=405)

    qr_data = request.POST.get('qr_data')
    if not qr_data:
        return JsonResponse({'error': _('Données QR manquantes')}, status=400)
    
    # Traiter le check-in
    # Cette logique dépendrait du système de gestion des présences
    
    return JsonResponse({
        'success': True,
        'message': _('Check-in effectué avec succès!')
    })

def create_organization_site(request):
    """Vue pour créer un site d'organisation (pour les admins)."""
    if not request.user.is_staff:
        return JsonResponse({'error': _('Permissions insuffisantes')}, status=403)
    
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
            return JsonResponse({'error': _('Organisation non trouvée')}, status=404)
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
        return JsonResponse({'error': _('Organisation non trouvée')}, status=404)
    
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


# =============================
# Fallback public routes by slug (no tenant)
# =============================
def _get_org_by_slug(slug: str):
    """
    Récupère une organisation par son slug.
    Cherche dans Organization et Federation, privilégie celle avec le plus de données.
    """
    try:
        org = Organization.objects.filter(slug=slug).first()
        federation = Federation.objects.filter(slug=slug).first()

        # Si on a les deux, décider laquelle utiliser
        if org and federation:
            # Si l'Organization n'a pas de logo mais la Federation en a un,
            # utiliser la Federation
            if not org.logo and federation.logo:
                return federation
            # Sinon utiliser l'Organization (qui peut avoir plus de données)
            return org

        # Sinon retourner ce qu'on a trouvé
        if org:
            return org
        if federation:
            return federation

        return None
    except Exception as e:
        logger.error(f"Erreur _get_org_by_slug: {e}")
        return None

def public_news_detail(request, slug, news_slug):
    """Affiche le détail d'un article d'actualité."""
    from apps.organizations.models import Organization, OrganizationNews
    organization = get_object_or_404(Organization, slug=slug)
    article = get_object_or_404(
        OrganizationNews,
        organization=organization,
        slug=news_slug,
        is_published=True,
    )
    context = {
        'organization': organization,
        'article': article,
    }
    return render(request, 'organizations/sites/news_detail.html', context)


def public_organization_site(request, slug: str, section: str = None):
    """Public site rendering without tenant, resolved by slug."""
    from django.views.decorators.clickjacking import xframe_options_sameorigin

    organization = _get_org_by_slug(slug)

    # Template mapping based on slug for demo/placeholder pages
    slug_template_mapping = {
        'coach': 'organizations/sites/coach_template.html',
        'federation': 'organizations/sites/federation_template.html',
        'club': 'organizations/sites/club_template.html',
        'event': 'organizations/sites/event_template.html',
    }

    if not organization:
        # Use appropriate template based on slug for demo pages
        template = slug_template_mapping.get(slug, 'organizations/sites/default_template.html')
        response = render(request, template, {
            'organization': None,
            'error': _('Organisation non trouvée') if slug not in slug_template_mapping else None
        })
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    # Choose template like OrganizationSiteView
    view = OrganizationSiteView()
    view.request = request  # for helper methods reuse
    org_type = view.get_organization_type(organization)
    template_mapping = {
        'federation': 'organizations/sites/federation_template.html',
        'club': 'organizations/sites/club_template.html',
        'coach': 'organizations/sites/coach_template.html',
        'event': 'organizations/sites/event_template.html'
    }
    template = template_mapping.get(org_type, 'organizations/sites/club_template.html')

    # Generate QR codes for immediate display
    try:
        qr_codes = generate_organization_qr_codes_set(organization)
    except Exception:
        qr_codes = {}

    # Récupérer les images de galerie (max 10)
    gallery_images = []
    try:
        from apps.organizations.models import OrganizationGalleryImage
        gallery_images = list(OrganizationGalleryImage.objects.filter(
            organization=organization
        ).order_by('order', 'created_at')[:10])
    except Exception as e:
        logger.debug(f"Erreur récupération galerie: {e}")

    # Récupérer les liens vidéos YouTube (max 10)
    video_links = []
    try:
        from apps.organizations.models import OrganizationVideoLink
        video_links = list(OrganizationVideoLink.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('order', '-created_at')[:10])
    except Exception as e:
        logger.debug(f"Erreur récupération vidéos: {e}")

    # Récupérer les compétitions à venir
    upcoming_competitions = view.get_upcoming_competitions(organization)

    context = {
        'organization': organization,
        'organization_type': org_type,
        'tenant': None,
        'qr_codes': qr_codes,
        'gallery_images': gallery_images,
        'video_links': video_links,
        'upcoming_competitions': upcoming_competitions,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    # Enrich context per type
    if org_type == 'federation':
        context.update(view.get_federation_context(organization))
    elif org_type == 'club':
        context.update(view.get_club_context(organization))
    elif org_type == 'coach':
        context.update(view.get_coach_context(organization))

    # Render with X-Frame-Options: SAMEORIGIN to allow iframe preview
    response = render(request, template, context)
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response

def public_organization_register_view(request, slug: str):
    organization = _get_org_by_slug(slug)
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    request.session['organization_context'] = {
        'id': organization.id,
        'type': OrganizationSiteView().get_organization_type(organization),
        'name': getattr(organization, 'name', '') or getattr(organization, 'nom', ''),
    }
    from django.shortcuts import redirect
    from django.utils.translation import get_language

    # Déterminer la langue
    lang = get_language() or 'fr'
    if lang not in ['fr', 'en', 'es', 'de', 'it', 'pt']:
        lang = 'fr'

    # Rediriger directement vers l'onboarding avec préfixe de langue
    return redirect(f'/{lang}/competitions/onboarding/role/')


def public_organization_referral_view(request, slug: str):
    """Vue publique de parrainage pour une organisation."""
    organization = _get_org_by_slug(slug)
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Récupérer l'ID du parrain depuis les paramètres
    referrer_id = request.GET.get('ref', '')

    # Stocker le contexte de parrainage dans la session
    request.session['organization_context'] = {
        'id': organization.id,
        'type': OrganizationSiteView().get_organization_type(organization),
        'name': getattr(organization, 'name', '') or getattr(organization, 'nom', ''),
        'referrer_id': referrer_id,
    }

    from django.shortcuts import redirect
    from django.utils.translation import get_language

    # Déterminer la langue
    lang = get_language() or 'fr'
    if lang not in ['fr', 'en', 'es', 'de', 'it', 'pt']:
        lang = 'fr'

    # Rediriger vers l'onboarding avec préfixe de langue et paramètre ref
    url = f'/{lang}/competitions/onboarding/role/'
    if referrer_id:
        url = f"{url}?ref={referrer_id}"
    return redirect(url)


def public_organization_qr_code_view(request, slug: str, qr_type: str = 'register'):
    organization = _get_org_by_slug(slug)
    if not organization:
        return JsonResponse({'error': _('Organisation non trouvée')}, status=404)

    cache_key = f"qr_codes_{organization.id}_{qr_type}"
    qr_codes = cache.get(cache_key)
    if not qr_codes:
        try:
            qr_codes = generate_organization_qr_codes_set(organization)
            cache.set(cache_key, qr_codes, 3600)
        except Exception as e:
            logger.error(f"Erreur génération QR codes (fallback) pour {organization}: {e}")
            return JsonResponse({'error': _('Erreur génération QR codes')}, status=500)

    if qr_type not in qr_codes:
        return JsonResponse({'error': _('Type de QR code non trouvé')}, status=404)

    url, file_path = qr_codes[qr_type]
    try:
        file_path_url = f"{settings.MEDIA_URL}{file_path}".replace('\\\\', '/').replace('\\', '/')
    except Exception:
        file_path_url = f"{settings.MEDIA_URL}{file_path}"
    return JsonResponse({
        'qr_url': url,
        'qr_image': file_path_url,
        'organization': {
            'name': getattr(organization, 'name', '') or getattr(organization, 'nom', ''),
            'type': OrganizationSiteView().get_organization_type(organization)
        }
    })

def public_organization_payment_view(request, slug: str):
    """Vue publique de paiement des cotisations pour une organisation."""
    organization = _get_org_by_slug(slug)
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Récupérer les packages d'adhésion de l'organisation
    packages = []
    try:
        from apps.membership.models import MembershipPackage
        packages = list(MembershipPackage.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('sort_order', 'base_price'))
    except Exception as e:
        logger.warning(f"Erreur récupération packages membership pour {organization}: {e}")

    # Tarifs par défaut si pas de packages
    default_pricing = {
        'discovery': 150,
        'standard': 250,
        'competitor': 350,
    }

    # Essayer de récupérer les tarifs personnalisés depuis le modèle Club si pas de packages
    if not packages:
        try:
            from apps.competitions.models import Club
            club = Club.objects.filter(organization=organization).first()
            if club:
                if hasattr(club, 'cotisation_debutant') and club.cotisation_debutant:
                    default_pricing['discovery'] = int(club.cotisation_debutant)
                if hasattr(club, 'cotisation_standard') and club.cotisation_standard:
                    default_pricing['standard'] = int(club.cotisation_standard)
                if hasattr(club, 'cotisation_competiteur') and club.cotisation_competiteur:
                    default_pricing['competitor'] = int(club.cotisation_competiteur)
        except Exception as e:
            logger.warning(f"Erreur récupération tarifs club pour {organization}: {e}")

    context = {
        'organization': organization,
        'packages': packages,
        'pricing': default_pricing,
        'has_packages': len(packages) > 0,
    }

    return render(request, 'organizations/sites/payment_template.html', context)


def public_organization_shop_view(request, slug: str):
    """Vue publique de la boutique pour une organisation."""
    organization = _get_org_by_slug(slug)
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Récupérer les produits de la boutique
    products = []
    categories = []
    try:
        from apps.shop.models import Product, ProductCategory
        products = list(Product.objects.filter(
            organization=organization,
            is_active=True,
            is_visible=True
        ).select_related('category').order_by('category__order', 'order', 'name')[:50])

        # Récupérer les catégories avec produits
        category_ids = set(p.category_id for p in products if p.category_id)
        if category_ids:
            categories = list(ProductCategory.objects.filter(
                id__in=category_ids,
                is_active=True
            ).order_by('order', 'name'))
    except Exception as e:
        logger.debug(f"Module shop non disponible ou erreur: {e}")

    # Produits par défaut si pas de boutique configurée
    default_products = []
    if not products:
        default_products = [
            {
                'name': 'Kimono Club',
                'description': 'Kimono officiel du club avec logo brodé',
                'price': 89.00,
                'category': 'Tenues',
                'image': None,
            },
            {
                'name': 'T-shirt Club',
                'description': 'T-shirt technique avec logo du club',
                'price': 25.00,
                'category': 'Tenues',
                'image': None,
            },
            {
                'name': 'Ceinture',
                'description': 'Ceinture de grade officielle',
                'price': 15.00,
                'category': 'Accessoires',
                'image': None,
            },
            {
                'name': 'Sac de sport',
                'description': 'Sac de sport aux couleurs du club',
                'price': 35.00,
                'category': 'Accessoires',
                'image': None,
            },
        ]

    context = {
        'organization': organization,
        'products': products,
        'categories': categories,
        'default_products': default_products,
        'has_shop': len(products) > 0,
    }

    return render(request, 'organizations/sites/shop_template.html', context)


from django.contrib.auth.decorators import login_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def public_organization_admin_view(request, slug: str):
    """Fallback admin management view without tenant, resolved by slug."""
    organization = _get_org_by_slug(slug)
    if not organization:
        return render(request, 'error.html', {'error': _('Organisation non trouvée')})

    # Permission check if available
    try:
        if hasattr(organization, 'can_user_edit') and not organization.can_user_edit(request.user):
            return render(request, 'error.html', {'error': _('Permissions insuffisantes')})
    except Exception:
        pass

    # Generate QR codes for management page
    try:
        qr_codes = generate_organization_qr_codes_set(organization)
    except Exception as e:
        logger.warning(f"Erreur génération QR codes pour {slug}: {e}")
        qr_codes = {}

    # Calculer les statistiques dynamiquement
    stats = _calculate_organization_stats(organization)

    # Récupérer les images de galerie (max 10)
    gallery_images = []
    try:
        from apps.organizations.models import OrganizationGalleryImage
        gallery_images = list(OrganizationGalleryImage.objects.filter(
            organization=organization
        ).order_by('order', 'created_at')[:10])
    except Exception as e:
        logger.debug(f"Erreur récupération galerie: {e}")

    # Récupérer les vidéos YouTube (max 10)
    video_links = []
    try:
        from apps.organizations.models import OrganizationVideoLink
        video_links = list(OrganizationVideoLink.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('order', '-created_at')[:10])
    except Exception as e:
        logger.debug(f"Erreur récupération vidéos: {e}")

    # Récupérer les actualités (toutes pour l'admin)
    news_articles = []
    try:
        from apps.organizations.models import OrganizationNews
        news_articles = list(OrganizationNews.objects.filter(
            organization=organization
        ).order_by('-is_featured', '-created_at')[:20])
    except Exception as e:
        logger.debug(f"Erreur récupération news: {e}")

    context = {
        'organization': organization,
        'qr_codes': qr_codes,
        'tenant': None,
        'subdomain_url': SubdomainGenerator().get_organization_subdomain_url(organization),
        'MEDIA_URL': settings.MEDIA_URL,
        # Statistiques calculées dynamiquement
        'visit_count': stats.get('visit_count', 0),
        'qr_scan_count': stats.get('qr_scan_count', 0),
        'member_count': stats.get('member_count', 0),
        'conversion_rate': stats.get('conversion_rate', 0),
        'today_visits': stats.get('today_visits', 0),
        'week_qr_scans': stats.get('week_qr_scans', 0),
        'month_registrations': stats.get('month_registrations', 0),
        # Galerie et vidéos
        'gallery_images': gallery_images,
        'video_links': video_links,
        # Actualités
        'news_articles': news_articles,
    }

    return render(request, 'organizations/admin/site_management.html', context)


def _calculate_organization_stats(organization):
    """
    Calcule les statistiques pour une organisation.

    Args:
        organization: Instance de l'organisation

    Returns:
        Dict avec les statistiques calculées
    """
    from django.db.models import Count, Q
    from datetime import timedelta

    stats = {
        'visit_count': 0,
        'qr_scan_count': 0,
        'member_count': 0,
        'conversion_rate': 0,
        'today_visits': 0,
        'week_qr_scans': 0,
        'month_registrations': 0,
    }

    try:
        now = timezone.now()
        month_start = now - timedelta(days=30)

        # Méthode principale: Compter les pratiquants directement liés à l'organisation
        try:
            from apps.competitions.models import Practitioner

            # Le modèle Practitioner a un champ 'organization' qui pointe vers Organization
            practitioner_count = Practitioner.objects.filter(
                organization=organization,
                is_active=True
            ).count()

            if practitioner_count > 0:
                stats['member_count'] = practitioner_count

                # Compter les inscriptions récentes (pratiquants créés ce mois)
                stats['month_registrations'] = Practitioner.objects.filter(
                    organization=organization,
                    created_at__gte=month_start
                ).count()

                logger.debug(f"Stats via Practitioner.organization: {practitioner_count} membres, {stats['month_registrations']} inscriptions récentes")

        except Exception as e:
            logger.debug(f"Erreur comptage pratiquants via organization: {e}")

        # Méthode de secours: Compter les membres OrganizationMember
        if stats['member_count'] == 0:
            if hasattr(organization, 'members'):
                member_count = organization.members.filter(is_active=True).count()
                if member_count > 0:
                    stats['member_count'] = member_count
                    stats['month_registrations'] = organization.members.filter(
                        created_at__gte=month_start
                    ).count()
                    logger.debug(f"Stats via OrganizationMember: {member_count} membres")

        # Méthode de secours 2: Chercher via le Club lié
        if stats['member_count'] == 0:
            try:
                from apps.competitions.models import Club, Practitioner

                # Chercher un club lié à cette organisation
                club = Club.objects.filter(organization=organization).first()

                # Ou via old_club_id
                if not club and hasattr(organization, 'old_club_id') and organization.old_club_id:
                    club = Club.objects.filter(id=organization.old_club_id).first()

                # Ou via le nom similaire (Club.name, pas Club.nom)
                if not club and hasattr(organization, 'name'):
                    club = Club.objects.filter(
                        Q(name__iexact=organization.name) |
                        Q(name__icontains=organization.name)
                    ).first()

                if club:
                    # Compter les pratiquants via l'organisation du club
                    if club.organization:
                        practitioner_count = Practitioner.objects.filter(
                            organization=club.organization,
                            is_active=True
                        ).count()
                        if practitioner_count > stats['member_count']:
                            stats['member_count'] = practitioner_count
                            stats['month_registrations'] = Practitioner.objects.filter(
                                organization=club.organization,
                                created_at__gte=month_start
                            ).count()
                            logger.debug(f"Stats via Club.organization: {practitioner_count} pratiquants")

            except Exception as e:
                logger.debug(f"Erreur recherche via club: {e}")

        # Calculer un taux de conversion estimé (si des inscriptions existent)
        if stats['member_count'] > 0 and stats['month_registrations'] > 0:
            stats['conversion_rate'] = min(round((stats['month_registrations'] / max(stats['member_count'], 1)) * 100, 1), 100)

    except Exception as e:
        logger.warning(f"Erreur calcul stats organisation: {e}")

    return stats


# ============================================
# API Endpoints pour la galerie et bannière
# ============================================

from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
import json


@require_POST
@csrf_protect
def api_upload_gallery_image(request, slug):
    """Upload une image dans la galerie de l'organisation."""
    # Vérifier l'authentification AVANT tout (retourner JSON, pas redirect)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationGalleryImage

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Vérifier la limite de 10 images
        current_count = OrganizationGalleryImage.objects.filter(organization=organization).count()
        if current_count >= 10:
            return JsonResponse({
                'success': False,
                'error': 'Limite de 10 images atteinte. Supprimez une image avant d\'en ajouter une nouvelle.'
            }, status=400)

        # Récupérer les fichiers (supporte 'images' et 'image')
        files = request.FILES.getlist('images')
        if not files:
            files = request.FILES.getlist('image')
        if not files:
            return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'}, status=400)

        # Calculer combien on peut ajouter
        max_to_add = 10 - current_count
        files_to_process = files[:max_to_add]

        created_images = []
        for i, file in enumerate(files_to_process):
            # Vérifier le type de fichier
            if not file.content_type.startswith('image/'):
                continue

            # Vérifier la taille (max 5 Mo)
            if file.size > 5 * 1024 * 1024:
                continue

            # Créer l'image
            gallery_image = OrganizationGalleryImage.objects.create(
                organization=organization,
                image=file,
                order=current_count + i
            )
            created_images.append({
                'id': gallery_image.id,
                'url': gallery_image.image.url,
                'description': gallery_image.description
            })

        return JsonResponse({
            'success': True,
            'images': created_images,
            'total_count': OrganizationGalleryImage.objects.filter(organization=organization).count()
        })

    except Exception as e:
        logger.error(f"Erreur upload galerie: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
@csrf_protect
def api_delete_gallery_image(request, slug, image_id):
    """Supprime une image de la galerie."""
    # Vérifier l'authentification AVANT tout (retourner JSON, pas redirect)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationGalleryImage

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Récupérer et supprimer l'image
        gallery_image = get_object_or_404(
            OrganizationGalleryImage,
            id=image_id,
            organization=organization
        )

        # Supprimer le fichier physique
        if gallery_image.image:
            gallery_image.image.delete(save=False)

        gallery_image.delete()

        return JsonResponse({
            'success': True,
            'total_count': OrganizationGalleryImage.objects.filter(organization=organization).count()
        })

    except Exception as e:
        logger.error(f"Erreur suppression galerie: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_update_gallery_description(request, slug, image_id):
    """Met à jour la description d'une image de galerie."""
    # Vérifier l'authentification AVANT tout (retourner JSON, pas redirect)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationGalleryImage

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Récupérer l'image
        gallery_image = get_object_or_404(
            OrganizationGalleryImage,
            id=image_id,
            organization=organization
        )

        # Mettre à jour la description
        data = json.loads(request.body) if request.body else {}
        description = data.get('description', '')

        gallery_image.description = description[:255]  # Limiter à 255 caractères
        gallery_image.save(update_fields=['description'])

        return JsonResponse({
            'success': True,
            'description': gallery_image.description
        })

    except Exception as e:
        logger.error(f"Erreur mise à jour description galerie: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_upload_banner(request, slug):
    """Upload la bannière de l'organisation."""
    # Vérifier l'authentification AVANT tout (retourner JSON, pas redirect)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Récupérer le fichier
        banner_file = request.FILES.get('banner')
        if not banner_file:
            return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'}, status=400)

        # Vérifier le type de fichier
        if not banner_file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'Le fichier doit être une image'}, status=400)

        # Vérifier la taille (max 5 Mo)
        if banner_file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'La taille maximale est de 5 Mo'}, status=400)

        # Supprimer l'ancienne bannière si elle existe
        if organization.banner:
            organization.banner.delete(save=False)

        # Sauvegarder la nouvelle bannière
        organization.banner = banner_file
        organization.save(update_fields=['banner'])

        return JsonResponse({
            'success': True,
            'banner_url': organization.banner.url
        })

    except Exception as e:
        logger.error(f"Erreur upload bannière: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
@csrf_protect
def api_delete_banner(request, slug):
    """Supprime la bannière de l'organisation."""
    # Vérifier l'authentification AVANT tout (retourner JSON, pas redirect)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Supprimer la bannière
        if organization.banner:
            organization.banner.delete(save=False)
            organization.banner = None
            organization.save(update_fields=['banner'])

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Erreur suppression bannière: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_customize_organization(request, organization_id):
    """
    API pour sauvegarder la personnalisation complète de l'organisation.
    Inclut: description, couleurs, modules activés, logo, bannière.
    """
    # Vérifier l'authentification
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization
        import re

        organization = get_object_or_404(Organization, id=organization_id)

        # Vérifier les permissions
        # Vérifier les permissions : staff, propriétaire du club, ou admin de l'organisation
        from apps.competitions.models import Club
        is_club_owner = Club.objects.filter(organization=organization, owner=request.user).exists()
        if not request.user.is_staff and not is_club_owner:
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Récupérer les données du formulaire
        description = request.POST.get('description', '').strip()
        # Normaliser les couleurs en minuscules pour comparaison cohérente
        primary_color = request.POST.get('primary_color', '#8b5cf6').lower()
        secondary_color = request.POST.get('secondary_color', '#a78bfa').lower()
        accent_color = request.POST.get('accent_color', '#d4af37').lower()

        # Logger les valeurs reçues pour debug
        logger.info(f"[api_customize] Reçu: primary={primary_color}, secondary={secondary_color}, accent={accent_color}")
        logger.info(f"[api_customize] En base: primary={organization.primary_color}, secondary={organization.secondary_color}, accent={organization.accent_color}")

        # Valider les couleurs (format hexadécimal)
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for color_name, color_value in [('primary_color', primary_color),
                                         ('secondary_color', secondary_color),
                                         ('accent_color', accent_color)]:
            if not hex_pattern.match(color_value):
                return JsonResponse({
                    'success': False,
                    'error': f'Format de couleur invalide pour {color_name}: {color_value}'
                }, status=400)

        # Mettre à jour les champs
        update_fields = []

        if description != (organization.description or ''):
            organization.description = description
            update_fields.append('description')

        # TOUJOURS mettre à jour les couleurs si elles sont fournies
        # Les couleurs sont toujours envoyées par le formulaire JS
        logger.info(f"[api_customize] Valeurs en base AVANT: primary={organization.primary_color}, secondary={organization.secondary_color}, accent={organization.accent_color}")

        # Mettre à jour primary_color
        organization.primary_color = primary_color
        update_fields.append('primary_color')

        # Mettre à jour secondary_color
        organization.secondary_color = secondary_color
        update_fields.append('secondary_color')

        # Mettre à jour accent_color
        organization.accent_color = accent_color
        update_fields.append('accent_color')

        logger.info(f"[api_customize] Valeurs APRÈS modification: primary={organization.primary_color}, secondary={organization.secondary_color}, accent={organization.accent_color}")

        # Gérer l'upload du logo
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']
            # Valider le type de fichier
            if not logo_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'Le logo doit être une image'}, status=400)
            # Valider la taille (max 2 Mo)
            if logo_file.size > 2 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'La taille maximale du logo est de 2 Mo'}, status=400)

            # Supprimer l'ancien logo si existant
            if organization.logo:
                organization.logo.delete(save=False)

            organization.logo = logo_file
            update_fields.append('logo')

        # Gérer l'upload de la bannière
        if 'banner' in request.FILES:
            banner_file = request.FILES['banner']
            # Valider le type de fichier
            if not banner_file.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'La bannière doit être une image'}, status=400)
            # Valider la taille (max 5 Mo)
            if banner_file.size > 5 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'La taille maximale de la bannière est de 5 Mo'}, status=400)

            # Supprimer l'ancienne bannière si existante
            if organization.banner:
                organization.banner.delete(save=False)

            organization.banner = banner_file
            update_fields.append('banner')

        # Sauvegarder si des champs ont changé
        if update_fields:
            organization.save(update_fields=update_fields)
            logger.info(f"Organisation {organization.slug} mise à jour: {update_fields}")

        return JsonResponse({
            'success': True,
            'message': 'Personnalisation sauvegardée',
            'updated_fields': update_fields,
            'logo_url': organization.logo.url if organization.logo else None,
            'banner_url': organization.banner.url if organization.banner else None
        })

    except Exception as e:
        logger.error(f"Erreur sauvegarde personnalisation: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def api_update_site_content(request, slug):
    """
    Met à jour le contenu du site (titre, texte de bienvenue, etc.)
    Stocke les données dans organization.metadata['content']
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentification requise'}, status=401)

    try:
        from apps.organizations.models import Organization
        import json

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not request.user.is_staff:
            # Vérifier si l'utilisateur est membre de l'organisation
            has_permission = False
            try:
                from apps.organizations.models import OrganizationMember
                has_permission = OrganizationMember.objects.filter(
                    organization=organization,
                    user=request.user,
                    role__in=['owner', 'admin', 'manager']
                ).exists()
            except Exception:
                pass

            if not has_permission and organization.created_by != request.user:
                return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

        # Récupérer les données
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST.dict()

        welcome_title = data.get('welcome_title', '').strip()
        welcome_text = data.get('welcome_text', '').strip()

        # Initialiser metadata si nécessaire
        if not organization.metadata:
            organization.metadata = {}

        # Mettre à jour le contenu
        if 'content' not in organization.metadata:
            organization.metadata['content'] = {}

        organization.metadata['content']['welcome_title'] = welcome_title
        organization.metadata['content']['welcome_text'] = welcome_text

        organization.save(update_fields=['metadata'])

        logger.info(f"Contenu du site {organization.slug} mis à jour par {request.user}")

        return JsonResponse({
            'success': True,
            'message': 'Contenu sauvegardé avec succès',
            'content': organization.metadata.get('content', {})
        })

    except Exception as e:
        logger.error(f"Erreur mise à jour contenu site: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_add_video_link(request, slug):
    """Ajoute un lien vidéo YouTube à l'organisation."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationVideoLink

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not request.user.is_staff and not hasattr(request.user, 'managed_organizations'):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        # Vérifier la limite de 10 vidéos
        current_count = OrganizationVideoLink.objects.filter(
            organization=organization
        ).count()
        if current_count >= 10:
            return JsonResponse({
                'success': False,
                'error': 'Limite de 10 vidéos atteinte.'
            }, status=400)

        # Récupérer les données
        data = json.loads(request.body) if request.body else {}
        youtube_url = data.get('youtube_url', '').strip()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not youtube_url:
            return JsonResponse({
                'success': False,
                'error': 'URL YouTube requise'
            }, status=400)

        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Titre requis'
            }, status=400)

        # Créer le lien vidéo
        video_link = OrganizationVideoLink(
            organization=organization,
            youtube_url=youtube_url,
            title=title[:255],
            description=description,
            order=current_count
        )
        video_link.save()

        return JsonResponse({
            'success': True,
            'video': {
                'id': video_link.id,
                'youtube_url': video_link.youtube_url,
                'video_id': video_link.video_id,
                'title': video_link.title,
                'description': video_link.description,
                'thumbnail_url': video_link.get_thumbnail_url(),
                'embed_url': video_link.get_embed_url()
            },
            'total_count': current_count + 1
        })

    except Exception as e:
        logger.error(f"Erreur ajout vidéo: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
@csrf_protect
def api_delete_video_link(request, slug, video_id):
    """Supprime un lien vidéo YouTube."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationVideoLink

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not request.user.is_staff and not hasattr(request.user, 'managed_organizations'):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        # Récupérer et supprimer la vidéo
        video_link = get_object_or_404(
            OrganizationVideoLink,
            id=video_id,
            organization=organization
        )
        video_link.delete()

        return JsonResponse({
            'success': True,
            'total_count': OrganizationVideoLink.objects.filter(
                organization=organization
            ).count()
        })

    except Exception as e:
        logger.error(f"Erreur suppression vidéo: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_update_video_link(request, slug, video_id):
    """Met à jour un lien vidéo YouTube (titre, description)."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationVideoLink

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not request.user.is_staff and not hasattr(request.user, 'managed_organizations'):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        # Récupérer la vidéo
        video_link = get_object_or_404(
            OrganizationVideoLink,
            id=video_id,
            organization=organization
        )

        # Mettre à jour les données
        data = json.loads(request.body) if request.body else {}

        if 'title' in data:
            video_link.title = data['title'][:255]
        if 'description' in data:
            video_link.description = data['description']
        if 'youtube_url' in data:
            video_link.youtube_url = data['youtube_url']
            # Recalculer le video_id et thumbnail
            video_link.video_id = video_link.extract_video_id()
            video_link.thumbnail_url = video_link.get_thumbnail_url()

        video_link.save()

        return JsonResponse({
            'success': True,
            'video': {
                'id': video_link.id,
                'youtube_url': video_link.youtube_url,
                'video_id': video_link.video_id,
                'title': video_link.title,
                'description': video_link.description,
                'thumbnail_url': video_link.get_thumbnail_url(),
                'embed_url': video_link.get_embed_url()
            }
        })

    except Exception as e:
        logger.error(f"Erreur mise à jour vidéo: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# API GESTION DES ACTUALITÉS (NEWS)
# ============================================

@require_http_methods(["GET"])
def api_get_news(request, slug, news_id):
    """Récupère une actualité spécifique pour édition."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews

        organization = get_object_or_404(Organization, slug=slug)

        news = get_object_or_404(
            OrganizationNews,
            id=news_id,
            organization=organization
        )

        return JsonResponse({
            'success': True,
            'news': {
                'id': news.id,
                'title': news.title,
                'excerpt': news.excerpt or '',
                'content': news.content,
                'is_published': news.is_published,
                'is_featured': news.is_featured,
                'image_url': news.image.url if news.image else None,
                'created_at': news.created_at.isoformat() if news.created_at else None,
                'published_at': news.published_at.isoformat() if news.published_at else None,
            }
        })

    except Exception as e:
        logger.error(f"Erreur récupération news: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _check_news_permission(request, organization):
    """
    Vérifie si l'utilisateur a les permissions pour gérer les news de l'organisation.
    Retourne True si autorisé, False sinon.
    """
    user = request.user

    logger.info(f"[NEWS_PERM] Checking permissions for user {user.id} ({user.username}) on org {organization.slug} (id={organization.id})")
    logger.info(f"[NEWS_PERM] org.old_federation_id={getattr(organization, 'old_federation_id', None)}, org.created_by_id={getattr(organization, 'created_by_id', None)}")

    # Superuser ou staff toujours autorisé
    if user.is_superuser or user.is_staff:
        logger.info(f"[NEWS_PERM] User {user.id} is superuser/staff - AUTHORIZED")
        return True

    # 1. Vérifier si membre de l'organisation
    try:
        from apps.organizations.models import OrganizationMember
        member = OrganizationMember.objects.filter(
            organization=organization,
            user=user
        ).first()
        if member:
            logger.info(f"[NEWS_PERM] User {user.id} is OrganizationMember with role={member.role}")
            if member.role in ['owner', 'admin', 'manager']:
                logger.info(f"[NEWS_PERM] User {user.id} has admin role - AUTHORIZED")
                return True
        else:
            logger.info(f"[NEWS_PERM] User {user.id} is NOT an OrganizationMember of org {organization.id}")
    except Exception as e:
        logger.error(f"[NEWS_PERM] Error checking OrganizationMember: {e}")

    # 1b. Vérifier si propriétaire du club lié à l'organisation
    try:
        from apps.competitions.models import Club
        if Club.objects.filter(organization=organization, owner=user).exists():
            logger.info(f"[NEWS_PERM] User {user.id} is club owner - AUTHORIZED")
            return True
    except Exception as e:
        logger.error(f"[NEWS_PERM] Error checking club owner: {e}")

    # 2. Vérifier si créateur de l'organisation
    if organization.created_by_id and organization.created_by_id == user.id:
        logger.info(f"[NEWS_PERM] User {user.id} is organization creator - AUTHORIZED")
        return True

    # 3. Vérifier si admin de la fédération liée via old_federation_id
    federation = None
    if organization.old_federation_id:
        try:
            from apps.competitions.models import Federation, FederationAdministrator
            federation = Federation.objects.get(id=organization.old_federation_id)
            logger.info(f"[NEWS_PERM] Found federation via old_federation_id: {federation.id} ({federation.name})")
        except Exception as e:
            logger.error(f"[NEWS_PERM] Error getting federation by old_federation_id: {e}")

    # 3b. Essayer de trouver la fédération via le slug de l'organisation
    if not federation:
        try:
            from apps.competitions.models import Federation, FederationAdministrator
            # Le slug de l'organisation peut correspondre au slug de la fédération
            federation = Federation.objects.filter(slug=organization.slug).first()
            if federation:
                logger.info(f"[NEWS_PERM] Found federation via slug match: {federation.id} ({federation.name})")
            else:
                # Essayer avec le nom
                federation = Federation.objects.filter(name__iexact=organization.name).first()
                if federation:
                    logger.info(f"[NEWS_PERM] Found federation via name match: {federation.id} ({federation.name})")
        except Exception as e:
            logger.error(f"[NEWS_PERM] Error finding federation by slug/name: {e}")

    # 3c. Essayer via organization.federation (relation directe si existe)
    if not federation and hasattr(organization, 'federation'):
        try:
            federation = organization.federation
            if federation:
                logger.info(f"[NEWS_PERM] Found federation via organization.federation: {federation.id}")
        except Exception as e:
            logger.error(f"[NEWS_PERM] Error getting organization.federation: {e}")

    # Vérifier les permissions sur la fédération trouvée
    if federation:
        try:
            from apps.competitions.models import FederationAdministrator

            logger.info(f"[NEWS_PERM] Checking federation permissions: owner_id={getattr(federation, 'owner_id', None)}, created_by_id={getattr(federation, 'created_by_id', None)}")

            # Owner de la fédération
            if hasattr(federation, 'owner_id') and federation.owner_id == user.id:
                logger.info(f"[NEWS_PERM] User {user.id} is federation owner - AUTHORIZED")
                return True

            if hasattr(federation, 'owner') and federation.owner == user:
                logger.info(f"[NEWS_PERM] User {user.id} is federation owner (via object) - AUTHORIZED")
                return True

            # Créateur de la fédération
            if hasattr(federation, 'created_by_id') and federation.created_by_id == user.id:
                logger.info(f"[NEWS_PERM] User {user.id} is federation creator - AUTHORIZED")
                return True

            # FederationAdministrator (comme dans dashboard)
            try:
                fed_admin = FederationAdministrator.objects.filter(
                    federation=federation,
                    user=user
                ).first()
                if fed_admin:
                    logger.info(f"[NEWS_PERM] User {user.id} is FederationAdministrator - AUTHORIZED")
                    return True
                else:
                    logger.info(f"[NEWS_PERM] User {user.id} is NOT a FederationAdministrator")
            except Exception as e:
                logger.error(f"[NEWS_PERM] Error checking FederationAdministrator: {e}")

            # Admin de la fédération via admins M2M
            if hasattr(federation, 'admins'):
                try:
                    if user in federation.admins.all():
                        logger.info(f"[NEWS_PERM] User {user.id} is in federation.admins - AUTHORIZED")
                        return True
                except Exception as e:
                    logger.error(f"[NEWS_PERM] Error checking federation.admins: {e}")

        except Exception as e:
            logger.error(f"[NEWS_PERM] Federation permission check failed: {e}")
    else:
        logger.warning(f"[NEWS_PERM] No federation found for organization {organization.slug}")

    logger.warning(f"[NEWS_PERM] Permission DENIED for user {user.id} on org {organization.slug}")
    return False


@require_POST
@csrf_protect
def api_create_news(request, slug):
    """Crée une nouvelle actualité."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews
        from django.utils import timezone
        from django.utils.text import slugify

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not _check_news_permission(request, organization):
            logger.warning(f"Permission denied for user {request.user.id} on org {organization.slug}")
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        # Récupérer les données du formulaire
        title = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        is_published = request.POST.get('is_published', '').lower() in ('true', '1', 'on')
        is_featured = request.POST.get('is_featured', '').lower() in ('true', '1', 'on')
        image = request.FILES.get('image')

        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Le titre est obligatoire'
            }, status=400)

        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Le contenu est obligatoire'
            }, status=400)

        # Générer le slug
        base_slug = slugify(title)[:200]
        unique_slug = base_slug
        counter = 1
        while OrganizationNews.objects.filter(organization=organization, slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1

        # Créer l'actualité
        news = OrganizationNews(
            organization=organization,
            title=title[:255],
            slug=unique_slug,
            excerpt=excerpt[:500] if excerpt else '',
            content=content,
            is_published=is_published,
            is_featured=is_featured,
            author=request.user,
            published_at=timezone.now() if is_published else None
        )

        if image:
            # Vérifier la taille (max 5 Mo)
            if image.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'Image trop grande (max 5 Mo)'
                }, status=400)
            news.image = image

        news.save()

        return JsonResponse({
            'success': True,
            'news': {
                'id': news.id,
                'title': news.title,
                'slug': news.slug,
                'is_published': news.is_published
            }
        })

    except Exception as e:
        logger.error(f"Erreur création news: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_update_news(request, slug, news_id):
    """Met à jour une actualité existante."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews
        from django.utils import timezone

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not _check_news_permission(request, organization):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        news = get_object_or_404(
            OrganizationNews,
            id=news_id,
            organization=organization
        )

        # Récupérer les données du formulaire
        title = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        is_published = request.POST.get('is_published', '').lower() in ('true', '1', 'on')
        is_featured = request.POST.get('is_featured', '').lower() in ('true', '1', 'on')
        image = request.FILES.get('image')

        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Le titre est obligatoire'
            }, status=400)

        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Le contenu est obligatoire'
            }, status=400)

        # Mettre à jour
        news.title = title[:255]
        news.excerpt = excerpt[:500] if excerpt else ''
        news.content = content
        news.is_featured = is_featured

        # Gérer la publication
        was_published = news.is_published
        news.is_published = is_published
        if is_published and not was_published:
            news.published_at = timezone.now()

        # Supprimer l'image si demandé
        remove_image = request.POST.get('remove_image', '').lower() in ('true', '1')
        if remove_image and news.image:
            news.image.delete(save=False)
            news.image = None

        if image:
            if image.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'Image trop grande (max 5 Mo)'
                }, status=400)
            news.image = image

        news.save()

        return JsonResponse({
            'success': True,
            'news': {
                'id': news.id,
                'title': news.title,
                'is_published': news.is_published
            }
        })

    except Exception as e:
        logger.error(f"Erreur mise à jour news: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
@csrf_protect
def api_delete_news(request, slug, news_id):
    """Supprime une actualité."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not _check_news_permission(request, organization):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        news = get_object_or_404(
            OrganizationNews,
            id=news_id,
            organization=organization
        )

        # Supprimer l'image si elle existe
        if news.image:
            news.image.delete(save=False)

        news.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Erreur suppression news: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_toggle_news_publish(request, slug, news_id):
    """Bascule le statut de publication d'une actualité."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews
        from django.utils import timezone

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not _check_news_permission(request, organization):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        news = get_object_or_404(
            OrganizationNews,
            id=news_id,
            organization=organization
        )

        # Basculer le statut
        news.is_published = not news.is_published
        if news.is_published and not news.published_at:
            news.published_at = timezone.now()
        news.save()

        return JsonResponse({
            'success': True,
            'is_published': news.is_published
        })

    except Exception as e:
        logger.error(f"Erreur toggle publish news: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_protect
def api_generate_competition_article(request, slug):
    """Génère automatiquement un article de résultats de compétition."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentification requise'
        }, status=401)

    try:
        from apps.organizations.models import Organization, OrganizationNews
        from apps.competitions.models import Club, Competition, Practitioner, CompetitionCategory
        from apps.competitions.models.technical_scoring import CompetitionRanking
        from apps.competitions.models.combat import Combat, Equipe, MembreEquipe, Poule
        from django.utils import timezone
        from django.utils.text import slugify
        import json as json_module

        organization = get_object_or_404(Organization, slug=slug)

        # Vérifier les permissions
        if not _check_news_permission(request, organization):
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        # Si c'est une demande de liste de compétitions
        if request.POST.get('list_competitions'):
            club = Club.objects.filter(organization=organization).first()
            if not club:
                return JsonResponse({'competitions': []})

            practitioners = Practitioner.objects.filter(organization=organization)
            competition_ids = CompetitionRanking.objects.filter(
                practitioner__in=practitioners
            ).values_list('competition_id', flat=True).distinct()

            # Aussi inclure les compétitions avec combats
            from django.db.models import Q
            combat_comp_ids = Combat.objects.filter(
                Q(pratiquant_rouge__in=practitioners) |
                Q(pratiquant_blanc__in=practitioners)
            ).values_list('competition_id', flat=True).distinct()

            all_comp_ids = set(list(competition_ids) + list(combat_comp_ids))
            competitions = Competition.objects.filter(
                id__in=all_comp_ids
            ).order_by('-start_date')

            return JsonResponse({
                'competitions': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'date': c.start_date.strftime('%d/%m/%Y') if c.start_date else '',
                    }
                    for c in competitions
                ]
            })

        # Récupérer l'ID de la compétition
        competition_id = request.POST.get('competition_id')
        if not competition_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de compétition requis'
            }, status=400)

        competition = get_object_or_404(Competition, id=competition_id)

        # Récupérer le club et les pratiquants de l'organisation
        club = Club.objects.filter(organization=organization).first()
        if not club:
            return JsonResponse({
                'success': False,
                'error': 'Aucun club associé à cette organisation'
            }, status=404)

        practitioners = Practitioner.objects.filter(organization=organization)

        # Récupérer les classements techniques
        rankings = CompetitionRanking.objects.filter(
            competition_id=competition_id,
            practitioner__in=practitioners
        ).select_related('competition', 'category', 'practitioner').order_by('category__name', 'rank')

        # Récupérer les résultats de combat
        from django.db.models import Q
        combats = Combat.objects.filter(
            competition_id=competition_id,
            status='termine'
        ).filter(
            Q(pratiquant_rouge__in=practitioners) |
            Q(pratiquant_blanc__in=practitioners)
        ).select_related(
            'pratiquant_rouge', 'pratiquant_blanc',
            'equipe_rouge', 'equipe_blanc'
        )

        # Récupérer les combats par équipe du club
        equipes_club = Equipe.objects.filter(
            competition_id=competition_id,
            club=club
        )
        combats_equipe = Combat.objects.filter(
            competition_id=competition_id,
            status='termine'
        ).filter(
            Q(equipe_rouge__in=equipes_club) |
            Q(equipe_blanc__in=equipes_club)
        ).select_related('equipe_rouge', 'equipe_blanc')

        # Calculer les médailles
        gold = rankings.filter(rank=1).count()
        silver = rankings.filter(rank=2).count()
        bronze = rankings.filter(rank=3).count()
        total_participants = rankings.values('practitioner').distinct().count()

        # Calculer les résultats combat individuels
        combat_results = []
        for combat in combats:
            if combat.pratiquant_rouge and combat.pratiquant_rouge in practitioners:
                practitioner = combat.pratiquant_rouge
                if combat.vainqueur == 'rouge':
                    result = 'V'
                elif combat.est_nul:
                    result = 'N'
                else:
                    result = 'D'
                combat_results.append({
                    'name': practitioner.full_name,
                    'result': result,
                })
            if combat.pratiquant_blanc and combat.pratiquant_blanc in practitioners:
                practitioner = combat.pratiquant_blanc
                if combat.vainqueur == 'blanc':
                    result = 'V'
                elif combat.est_nul:
                    result = 'N'
                else:
                    result = 'D'
                combat_results.append({
                    'name': practitioner.full_name,
                    'result': result,
                })

        # Calculer résultats par équipe
        equipe_results = []
        for combat in combats_equipe:
            if combat.equipe_rouge and combat.equipe_rouge in equipes_club:
                equipe = combat.equipe_rouge
                if combat.vainqueur == 'rouge':
                    result = 'V'
                elif combat.est_nul:
                    result = 'N'
                else:
                    result = 'D'
                equipe_results.append({
                    'name': equipe.nom,
                    'result': result,
                })
            if combat.equipe_blanc and combat.equipe_blanc in equipes_club:
                equipe = combat.equipe_blanc
                if combat.vainqueur == 'blanc':
                    result = 'V'
                elif combat.est_nul:
                    result = 'N'
                else:
                    result = 'D'
                equipe_results.append({
                    'name': equipe.nom,
                    'result': result,
                })

        # Texte personnalisé de l'utilisateur
        custom_text = request.POST.get('custom_text', '').strip()

        # Générer le contenu HTML simplifié : médailles uniquement
        date_str = competition.start_date.strftime('%d/%m/%Y') if competition.start_date else ''
        lieu = competition.venue_name or competition.city or ''
        total_medals = gold + silver + bronze

        # Construire la liste des médaillés groupés par catégorie
        medalists_html = ''
        if rankings.filter(rank__lte=3).exists():
            current_cat = None
            seen_teams = set()
            for ranking in rankings.filter(rank__lte=3).order_by('category__name', 'rank'):
                cat_name = ranking.category.name if ranking.category else '-'
                if cat_name != current_cat:
                    if current_cat is not None:
                        medalists_html += '</div>'
                    medalists_html += f'<div style="margin-bottom: 16px;"><h4 style="color: #a78bfa; font-size: 0.95em; margin: 0 0 8px 0;">{cat_name}</h4>'
                    current_cat = cat_name
                    seen_teams = set()
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(ranking.rank, '')
                prat = ranking.practitioner
                name = prat.full_name if prat else '-'

                # Récupérer le grade du pratiquant
                def get_grade_str(p):
                    try:
                        if p and p.grade:
                            g = str(p.grade)
                            # Retirer la partie "(discipline)" si présente
                            if '(' in g:
                                g = g[:g.index('(')].strip()
                            return g
                    except Exception:
                        pass
                    return ''

                # Pour les catégories équipe, afficher tous les membres
                is_team = False
                try:
                    if ranking.category.competition_type and ranking.category.competition_type.team_based:
                        is_team = True
                except Exception:
                    pass

                if is_team:
                    membership = MembreEquipe.objects.filter(
                        equipe__category=ranking.category,
                        equipe__is_active=True,
                        pratiquant=prat,
                    ).select_related('equipe').first()
                    if not membership:
                        membership = MembreEquipe.objects.filter(
                            equipe__category=ranking.category,
                            equipe__is_active=True,
                            equipe__memberships__pratiquant=prat,
                        ).select_related('equipe').first()
                    if membership and membership.equipe.id not in seen_teams:
                        seen_teams.add(membership.equipe.id)
                        team = membership.equipe
                        members = list(team.memberships.filter(est_remplacant=False).select_related('pratiquant', 'pratiquant__grade').order_by('ordre'))
                        members_parts = []
                        for m in members:
                            grade = get_grade_str(m.pratiquant)
                            if grade:
                                members_parts.append(f'{m.pratiquant.full_name} <em style="color:#888; font-size:0.85em;">({grade})</em>')
                            else:
                                members_parts.append(m.pratiquant.full_name)
                        members_str = ', '.join(members_parts)
                        medalists_html += f'<div style="padding: 6px 0; color: #e0e0e0;">{medal} <strong>{team.nom}</strong><br/><span style="color: #a0a0a0; font-size: 0.9em; padding-left: 24px;">{members_str}</span></div>'
                    elif not membership:
                        grade = get_grade_str(prat)
                        grade_html = f' <em style="color:#888; font-size:0.85em;">- {grade}</em>' if grade else ''
                        medalists_html += f'<div style="padding: 4px 0; color: #e0e0e0;">{medal} {name}{grade_html}</div>'
                else:
                    grade = get_grade_str(prat)
                    grade_html = f' <em style="color:#888; font-size:0.85em;">- {grade}</em>' if grade else ''
                    medalists_html += f'<div style="padding: 4px 0; color: #e0e0e0;">{medal} {name}{grade_html}</div>'
            if current_cat is not None:
                medalists_html += '</div>'

        # Résultats combat : classement des poules pour les pratiquants du club
        combat_medalists_html = ''
        combat_cats = CompetitionCategory.objects.filter(
            competition=competition
        ).exclude(competition_type__isnull=True)
        combat_cats = [c for c in combat_cats if 'combat' in (c.competition_type.name.lower() if c.competition_type else '')]

        from collections import defaultdict as dd

        for cat in combat_cats:
            # Calculer le classement global de la catégorie
            poules = Poule.objects.filter(competition=competition, category=cat)
            if not poules.exists():
                continue

            all_stats = dd(lambda: {'v': 0, 'pts_for': 0, 'pts_against': 0, 'nom': '', 'equipe': None, 'prat': None, 'is_individual': False})
            for poule in poules:
                cat_combats = Combat.objects.filter(poule=poule, status='termine').select_related(
                    'equipe_rouge', 'equipe_blanc', 'pratiquant_rouge', 'pratiquant_blanc',
                    'pratiquant_rouge__organization', 'pratiquant_blanc__organization',
                    'pratiquant_rouge__grade', 'pratiquant_blanc__grade'
                )
                for c in cat_combats:
                    # Mode equipe
                    if c.equipe_rouge_id:
                        s = all_stats[f'eq_{c.equipe_rouge_id}']
                        s['nom'] = c.equipe_rouge.nom
                        s['equipe'] = c.equipe_rouge
                        s['pts_for'] += float(c.score_rouge or 0)
                        s['pts_against'] += float(c.score_blanc or 0)
                        if c.vainqueur == 'rouge': s['v'] += 1
                    elif c.pratiquant_rouge_id:
                        # Mode individuel
                        s = all_stats[f'pr_{c.pratiquant_rouge_id}']
                        s['nom'] = c.pratiquant_rouge.full_name
                        s['prat'] = c.pratiquant_rouge
                        s['is_individual'] = True
                        s['pts_for'] += float(c.score_rouge or 0)
                        s['pts_against'] += float(c.score_blanc or 0)
                        if c.vainqueur == 'rouge': s['v'] += 1

                    if c.equipe_blanc_id:
                        s = all_stats[f'eq_{c.equipe_blanc_id}']
                        s['nom'] = c.equipe_blanc.nom
                        s['equipe'] = c.equipe_blanc
                        s['pts_for'] += float(c.score_blanc or 0)
                        s['pts_against'] += float(c.score_rouge or 0)
                        if c.vainqueur == 'blanc': s['v'] += 1
                    elif c.pratiquant_blanc_id:
                        s = all_stats[f'pr_{c.pratiquant_blanc_id}']
                        s['nom'] = c.pratiquant_blanc.full_name
                        s['prat'] = c.pratiquant_blanc
                        s['is_individual'] = True
                        s['pts_for'] += float(c.score_blanc or 0)
                        s['pts_against'] += float(c.score_rouge or 0)
                        if c.vainqueur == 'blanc': s['v'] += 1

            if not all_stats:
                continue

            sorted_stats = sorted(all_stats.items(), key=lambda x: (
                -x[1]['v'], -(x[1]['pts_for'] - x[1]['pts_against']), -x[1]['pts_for']
            ))

            # Trouver les pratiquants/equipes du club dans le classement
            club_entries = []
            for pos, (sid, s) in enumerate(sorted_stats, 1):
                if s['is_individual']:
                    # Combat individuel : verifier si le pratiquant est du club
                    prat = s.get('prat')
                    if prat and prat.organization == organization:
                        grade = get_grade_str(prat)
                        grade_html = f' <em style="color:#888; font-size:0.85em;">- {grade}</em>' if grade else ''
                        club_entries.append({'pos': pos, 'html': f'{s["nom"]}{grade_html}', 'v': s['v'], 'is_team': False})
                else:
                    # Combat equipe
                    equipe = s.get('equipe')
                    if equipe and equipe.club and equipe.club.organization == organization:
                        members = list(equipe.memberships.filter(est_remplacant=False).select_related('pratiquant', 'pratiquant__grade').order_by('ordre'))
                        members_parts = []
                        for m in members:
                            grade = get_grade_str(m.pratiquant)
                            if grade:
                                members_parts.append(f'{m.pratiquant.full_name} <em style="color:#888; font-size:0.85em;">({grade})</em>')
                            else:
                                members_parts.append(m.pratiquant.full_name)
                        members_str = ', '.join(members_parts)
                        club_entries.append({'pos': pos, 'html': f'<strong>{s["nom"]}</strong><br/><span style="color: #666; font-size: 0.9em; padding-left: 24px;">{members_str}</span>', 'v': s['v'], 'is_team': True})

            if club_entries:
                combat_medalists_html += f'<div style="margin-bottom: 16px;"><h4 style="color: #5b21b6; font-size: 0.95em; margin: 0 0 8px 0;">🥊 {cat.name}</h4>'
                for entry in club_entries:
                    medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(entry['pos'], f'{entry["pos"]}.')
                    combat_medalists_html += f'<div style="padding: 6px 0; color: #222;">{medal} {entry["html"]} ({entry["v"]}V)</div>'
                combat_medalists_html += '</div>'

        if combat_medalists_html:
            medalists_html += '<h3 style="color: #222; margin: 24px 0 16px 0; font-size: 1.1em; border-bottom: 2px solid #ef4444; padding-bottom: 8px;">🥊 Resultats Combat</h3>'
            medalists_html += combat_medalists_html

        # Texte personnalisé formaté
        custom_html = ''
        if custom_text:
            paragraphs = custom_text.split('\n')
            custom_html = '<div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 10px; border-left: 3px solid #8b5cf6;">'
            for p in paragraphs:
                p = p.strip()
                if p:
                    custom_html += f'<p style="color: #e0e0e0; margin: 0 0 8px 0; line-height: 1.6;">{p}</p>'
            custom_html += '</div>'

        club_name = organization.name or ''
        html_content = f'''
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:680px; margin:0 auto; font-family:Georgia, 'Times New Roman', serif; color:#222; background:#fff;">
    <tr><td style="background:#1a1a2e; padding:32px 24px; text-align:center;">
        <p style="margin:0 0 4px; font-size:13px; letter-spacing:3px; text-transform:uppercase; color:#a0a0c0;">{club_name}</p>
        <h1 style="margin:0 0 6px; font-size:28px; color:#ffd700; font-weight:700;">COMMUNIQUE OFFICIEL</h1>
        <h2 style="margin:0 0 10px; font-size:20px; color:#fff; font-weight:400;">{competition.title}</h2>
        <p style="margin:0; font-size:14px; color:#8888aa;">{date_str}{f" &mdash; {lieu}" if lieu else ""}</p>
    </td></tr>
    <tr><td style="padding:28px 32px 0;">
        <p style="font-size:15px; line-height:1.7; color:#333; margin:0 0 20px;">
            Notre club a participe au <strong>{competition.title}</strong> et nos pratiquants se sont illustres
            avec un total de <strong>{total_medals} medaille(s)</strong> &mdash;
            <span style="color:#b8860b;">{gold} or</span>,
            <span style="color:#808080;">{silver} argent</span> et
            <span style="color:#a0522d;">{bronze} bronze</span>
            pour {total_participants} participant(s) engages.
        </p>
    </td></tr>
    <tr><td style="padding:0 32px;">
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 auto 24px; text-align:center;">
            <tr>
                <td style="padding:12px; width:33%;">
                    <div style="background:#fffbe6; border:2px solid #ffd700; border-radius:10px; padding:16px 8px;">
                        <div style="font-size:28px;">🥇</div>
                        <div style="font-size:32px; font-weight:bold; color:#b8860b;">{gold}</div>
                        <div style="font-size:12px; color:#666; text-transform:uppercase; letter-spacing:1px;">Or</div>
                    </div>
                </td>
                <td style="padding:12px; width:33%;">
                    <div style="background:#f5f5f5; border:2px solid #c0c0c0; border-radius:10px; padding:16px 8px;">
                        <div style="font-size:28px;">🥈</div>
                        <div style="font-size:32px; font-weight:bold; color:#808080;">{silver}</div>
                        <div style="font-size:12px; color:#666; text-transform:uppercase; letter-spacing:1px;">Argent</div>
                    </div>
                </td>
                <td style="padding:12px; width:33%;">
                    <div style="background:#fdf0e2; border:2px solid #cd7f32; border-radius:10px; padding:16px 8px;">
                        <div style="font-size:28px;">🥉</div>
                        <div style="font-size:32px; font-weight:bold; color:#a0522d;">{bronze}</div>
                        <div style="font-size:12px; color:#666; text-transform:uppercase; letter-spacing:1px;">Bronze</div>
                    </div>
                </td>
            </tr>
        </table>
    </td></tr>
    {f"""<tr><td style="padding:0 32px 20px;">
        <div style="border-left:4px solid #1a1a2e; padding:16px 20px; background:#f8f8fc; margin:0 0 8px;">
            {''.join(f'<p style="margin:0 0 8px; font-size:15px; line-height:1.7; color:#333;">{p.strip()}</p>' for p in custom_text.split(chr(10)) if p.strip())}
        </div>
    </td></tr>""" if custom_text else ""}
    <tr><td style="padding:0 32px 8px;">
        <h3 style="font-size:18px; color:#1a1a2e; margin:0 0 16px; padding-bottom:10px; border-bottom:2px solid #ffd700;">
            🏅 Palmares detaille
        </h3>
    </td></tr>
    <tr><td style="padding:0 32px 24px;">
        {medalists_html}
    </td></tr>
    <tr><td style="background:#1a1a2e; padding:20px 32px; text-align:center;">
        <p style="margin:0 0 4px; font-size:12px; color:#8888aa;">{club_name} &mdash; Saison {date_str[-4:] if len(date_str) >= 4 else ""}</p>
        <p style="margin:0; font-size:11px; color:#555;">Genere par <strong style="color:#8b5cf6;">MartialComp</strong> &mdash; Plateforme de gestion des competitions d&apos;arts martiaux</p>
    </td></tr>
</table>'''

        # Adapter les couleurs des medaillés pour le format newsletter (fond blanc)
        medalists_html_light = medalists_html.replace('color: #e0e0e0;', 'color: #222;').replace('color: #a0a0a0;', 'color: #666;').replace('color: #a78bfa;', 'color: #5b21b6;')
        html_content = html_content.replace(medalists_html, medalists_html_light)

        # Creer l'article
        title = f"Resultats - {competition.title}"
        base_slug = slugify(title)
        article_slug = base_slug
        counter = 1
        while OrganizationNews.objects.filter(organization=organization, slug=article_slug).exists():
            article_slug = f"{base_slug}-{counter}"
            counter += 1

        excerpt = f"{gold} or, {silver} argent, {bronze} bronze - {total_participants} participant(s) au {competition.title}"

        news = OrganizationNews.objects.create(
            organization=organization,
            title=title,
            slug=article_slug,
            excerpt=excerpt,
            content=html_content,
            is_published=True,
            is_featured=True,
            published_at=timezone.now(),
            author=request.user,
        )

        return JsonResponse({
            'success': True,
            'article_id': news.id,
            'article_title': news.title,
            'article_url': f'/org/{slug}/news/{news.slug}/',
        })

    except Competition.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Compétition non trouvée'
        }, status=404)
    except Exception as e:
        logger.error(f"Erreur génération article compétition: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

