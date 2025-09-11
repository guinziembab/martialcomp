from django.core.exceptions import PermissionDenied
"""
Vue dashboard pour les coaches - Version simplifiée
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from ...models import UserProfile, Practitioner, CoachProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

# Task Management Integration
try:
    from apps.task_management.dashboard_utils import get_dashboard_task_data, get_coach_dashboard_task_data
    TASK_MANAGEMENT_AVAILABLE = True
except ImportError:
    TASK_MANAGEMENT_AVAILABLE = False
    logger.warning("Task Management module not available")

@login_required
def coach_dashboard(request):
    """
    Tableau de bord pour les coaches.
    Version simplifiée qui redirige vers coach-multidiscipline.
    """
    try:
        # Vérifier l'authentification
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Récupérer le profil utilisateur
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.warning(request, _("Profil utilisateur non trouvé."))
            return redirect('competitions:dashboard:home')
        
        # Vérifier le rôle
        logger.warning(f"DEBUG: Valeur du rôle pour {request.user.username}: '{profile.role}' (après strip/lower: '{profile.role.strip().lower()}')")
        messages.info(request, _(f"DEBUG: Votre rôle détecté est : '{profile.role}' (après strip/lower: '{profile.role.strip().lower()}')"))
        if profile.role.strip().lower() != 'coach':
            messages.warning(request, _("Ce tableau de bord est réservé aux coaches."))
            return redirect('competitions:dashboard:home')
        
        # Récupérer le pratiquant
        try:
            practitioner = Practitioner.objects.get(user=request.user)
        except Practitioner.DoesNotExist:
            messages.error(request, _("Profil coach non trouvé."))
            return redirect('competitions:dashboard:home')
        
        # Récupérer le profil coach
        try:
            coach_profile = CoachProfile.objects.get(practitioner=practitioner)
        except CoachProfile.DoesNotExist:
            # Créer le profil coach si nécessaire
            coach_profile = CoachProfile.objects.create(
                practitioner=practitioner,
                profile_type='multidisciplinary',
                teaching_philosophy=f'Coach - {practitioner.first_name} {practitioner.last_name}',
                years_teaching=5,
                hourly_rate_range='50-80',
                available_for_private_lessons=True,
                available_for_seminars=True,
                available_for_online_coaching=True
            )
        
        # Récupérer les données de gestion de tâches
        task_data = {}
        if TASK_MANAGEMENT_AVAILABLE:
            try:
                # Données générales des tâches de l'utilisateur
                task_data = get_dashboard_task_data(request.user, limit_tasks=5, limit_boards=3)
                
                # Données spécifiques au coach
                coach_task_data = get_coach_dashboard_task_data(request.user)
                task_data.update(coach_task_data)
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données de tâches: {str(e)}")
                task_data = {'has_access': False}
        
        # Récupérer les disciplines pour le badge de la sidebar
        disciplines_count = 0
        try:
            from apps.competitions.models.discipline import Discipline
            disciplines = get_organization_queryset(Discipline, request.user)
            disciplines_count = len(disciplines) if disciplines else 0
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des disciplines: {e}")
            disciplines_count = 0

        # Récupérer les données d'adhésion spécifiques au coach (NOUVEAU - MartialComp v2.0)
        membership_stats = {}
        try:
            from apps.membership.services import MembershipService
            from apps.membership.models import MembershipSubscription, MembershipPackage
            
            # Obtenir l'organisation du coach
            coach_organization = None
            if coach_profile and hasattr(coach_profile, 'primary_teaching_place'):
                coach_organization = getattr(coach_profile.primary_teaching_place, 'organization', None)
            elif practitioner:
                coach_organization = getattr(practitioner, 'organization', None)
            
            if coach_organization:
                # Statistiques spécifiques au coach
                # Élèves du coach (pratiquants de la même organisation)
                from apps.competitions.models import Practitioner as PractitionerModel
                my_students = PractitionerModel.objects.filter(organization=coach_organization)
                
                # Packages créés par le coach ou utilisés par ses élèves
                coach_packages = MembershipPackage.objects.filter(
                    organization=coach_organization
                ).count()
                
                # Souscriptions actives des élèves du coach
                active_subscriptions = MembershipSubscription.objects.filter(
                    package__organization=coach_organization,
                    status='active'
                )
                
                # Revenus générés (estimation basée sur les souscriptions actives)
                monthly_revenue = sum([
                    float(sub.price_paid) for sub in active_subscriptions 
                    if sub.package.package_type == 'monthly'
                ])
                
                # Cours privés (packages incluant des cours privés)
                private_lessons_packages = MembershipPackage.objects.filter(
                    organization=coach_organization,
                    name__icontains='privé'
                ).count()
                
                membership_stats = {
                    'my_students_count': my_students.count(),
                    'my_packages_count': coach_packages,
                    'monthly_revenue': monthly_revenue,
                    'private_lessons_count': private_lessons_packages,
                    'retention_rate': 85,  # Taux fixe pour l'exemple
                    'active_subscriptions': active_subscriptions.count()
                }
                
                logger.info(f"Données d'adhésion coach chargées: {membership_stats}")
                
        except ImportError:
            logger.warning("Module membership non disponible pour le coach")
            membership_stats = {
                'my_students_count': 0,
                'my_packages_count': 0,
                'monthly_revenue': 0,
                'private_lessons_count': 0,
                'retention_rate': 0,
                'active_subscriptions': 0
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données d'adhésion coach: {str(e)}")
            membership_stats = {
                'my_students_count': 0,
                'my_packages_count': 0,
                'monthly_revenue': 0,
                'private_lessons_count': 0,
                'retention_rate': 0,
                'active_subscriptions': 0
            }

        # Contexte pour le template
        context = {
            'user': request.user,
            'practitioner': practitioner,
            'coach_profile': coach_profile,
            'dashboard_type': 'coach',
            'page_title': _('Tableau de bord Coach'),
            'disciplines_count': disciplines_count,
            'membership_stats': membership_stats,  # NOUVEAU - Données d'adhésion MartialComp v2.0
        }
        
        # Ajouter les données de gestion de tâches au contexte si disponibles
        if task_data:
            context.update(task_data)
        
        return render(request, 'competitions/dashboard/coach.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans coach_dashboard: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors du chargement du tableau de bord."))
        return redirect('competitions:dashboard:home') 
