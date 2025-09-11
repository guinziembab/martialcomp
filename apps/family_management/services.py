"""
Services pour la gestion familiale centralisée.
Contient la logique métier pour les inscriptions groupées, paiements familiaux, etc.
"""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal
import logging

from .models import Family, FamilyMember, FamilyPaymentGroup, FamilyEvent
from apps.competitions.models import Practitioner, Competition, CompetitionRegistration

# Import de l'intégration financière
try:
    from .finance_integration import FamilyFinanceIntegrationService, FamilyFinanceUtils
    FINANCE_INTEGRATION_AVAILABLE = True
except ImportError:
    FINANCE_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)


class FamilyRegistrationService:
    """Service pour gérer les inscriptions familiales groupées."""
    
    @staticmethod
    def register_family_to_competition(family, competition, selected_members=None, 
                                     registered_by=None, notes=''):
        """
        Inscrit plusieurs membres d'une famille Ã  une compétition.
        
        Args:
            family: Instance de Family
            competition: Instance de Competition
            selected_members: Liste des IDs de FamilyMember Ã  inscrire (None = tous les pratiquants)
            registered_by: Utilisateur qui effectue l'inscription
            notes: Notes pour l'inscription groupée
            
        Returns:
            dict: Résultat avec 'success', 'registrations', 'errors'
        """
        results = {
            'success': False,
            'registrations': [],
            'errors': [],
            'total_cost': Decimal('0.00')
        }
        
        try:
            with transaction.atomic():
                # Récupérer les membres Ã  inscrire
                if selected_members:
                    members = family.members.filter(
                        id__in=selected_members,
                        is_active=True,
                        practitioner__isnull=False
                    )
                else:
                    members = family.members.filter(
                        is_active=True,
                        practitioner__isnull=False
                    )
                
                if not members.exists():
                    results['errors'].append(_("Aucun pratiquant valide trouvé dans la famille"))
                    return results
                
                # Vérifier les permissions
                if registered_by:
                    member_registering = family.members.filter(user=registered_by).first()
                    if not member_registering or not member_registering.has_permission('register_members'):
                        results['errors'].append(_("Permissions insuffisantes pour inscrire les membres"))
                        return results
                
                # Traiter chaque inscription
                successful_registrations = []
                total_cost = Decimal('0.00')
                
                for member in members:
                    practitioner = member.practitioner
                    
                    try:
                        # Vérifier l'éligibilité
                        if not practitioner.is_eligible_for_competition(competition):
                            results['errors'].append(
                                f"{practitioner.full_name}: Non éligible pour cette compétition"
                            )
                            continue
                        
                        # Vérifier si déjÃ  inscrit
                        if CompetitionRegistration.objects.filter(
                            competition=competition,
                            practitioner=practitioner
                        ).exists():
                            results['errors'].append(
                                f"{practitioner.full_name}: DéjÃ  inscrit Ã  cette compétition"
                            )
                            continue
                        
                        # Créer l'inscription
                        registration = CompetitionRegistration.objects.create(
                            competition=competition,
                            practitioner=practitioner,
                            registered_by=registered_by,
                            notes=f"Inscription familiale: {notes}",
                            family_registration=True  # Marqueur pour inscription familiale
                        )
                        
                        successful_registrations.append(registration)
                        
                        # Calculer le coÃ»t (si défini)
                        if hasattr(competition, 'registration_fee'):
                            total_cost += competition.registration_fee or Decimal('0.00')
                        
                        logger.info(f"Inscription familiale réussie: {practitioner.full_name} -> {competition.name}")
                        
                    except Exception as e:
                        results['errors'].append(
                            f"{practitioner.full_name}: Erreur lors de l'inscription - {str(e)}"
                        )
                        logger.error(f"Erreur inscription familiale {practitioner.id}: {e}")
                
                # Créer un groupe de paiement si des inscriptions ont réussi et qu'il y a des frais
                if successful_registrations and total_cost > 0:
                    payment_group = FamilyPaymentGroup.objects.create(
                        family=family,
                        description=f"Inscriptions Ã  {competition.name}",
                        total_amount=total_cost
                    )
                    
                    # Lier les inscriptions au groupe de paiement
                    for registration in successful_registrations:
                        if hasattr(registration, 'payment_group'):
                            registration.payment_group = payment_group
                            registration.save()
                
                results.update({
                    'success': len(successful_registrations) > 0,
                    'registrations': successful_registrations,
                    'total_cost': total_cost,
                    'registered_count': len(successful_registrations)
                })
                
                if successful_registrations:
                    logger.info(f"Inscription familiale terminée: {len(successful_registrations)} inscriptions pour la famille {family.family_name}")
                
        except Exception as e:
            results['errors'].append(f"Erreur générale: {str(e)}")
            logger.error(f"Erreur lors de l'inscription familiale {family.id}: {e}")
        
        return results
    
    @staticmethod
    def get_family_competition_eligibility(family, competition):
        """
        Analyse l'éligibilité de tous les membres d'une famille pour une compétition.
        
        Returns:
            dict: Avec 'eligible', 'ineligible', 'already_registered'
        """
        results = {
            'eligible': [],
            'ineligible': [],
            'already_registered': []
        }
        
        practitioners = [member.practitioner for member in family.get_all_members() 
                        if member.practitioner and member.practitioner.status == 'active']
        
        for practitioner in practitioners:
            # Vérifier si déjÃ  inscrit
            if CompetitionRegistration.objects.filter(
                competition=competition,
                practitioner=practitioner
            ).exists():
                results['already_registered'].append(practitioner)
                continue
            
            # Vérifier l'éligibilité
            if practitioner.is_eligible_for_competition(competition):
                results['eligible'].append(practitioner)
            else:
                results['ineligible'].append(practitioner)
        
        return results


class FamilyPaymentService:
    """Service pour gérer les paiements familiaux groupés."""
    
    @staticmethod
    def create_family_payment_group(family, description, items=None, created_by=None):
        """
        Crée un nouveau groupe de paiement familial.
        
        Args:
            family: Instance de Family
            description: Description du groupe de paiement
            items: Liste des éléments Ã  payer avec montants
            created_by: Utilisateur qui crée le groupe
            
        Returns:
            FamilyPaymentGroup instance
        """
        total_amount = Decimal('0.00')
        
        if items:
            for item in items:
                amount = Decimal(str(item.get('amount', 0)))
                total_amount += amount
        
        payment_group = FamilyPaymentGroup.objects.create(
            family=family,
            description=description,
            total_amount=total_amount
        )
        
        logger.info(f"Groupe de paiement familial créé: {payment_group.id} pour {family.family_name}")
        
        return payment_group
    
    @staticmethod
    def process_family_payment(payment_group, payment_method_id, payment_data=None):
        """
        Traite un paiement pour un groupe familial en utilisant le module finances.
        
        Args:
            payment_group: Instance de FamilyPaymentGroup
            payment_method_id: ID de la méthode de paiement du module finances
            payment_data: Données de paiement supplémentaires
            
        Returns:
            dict: Résultat du paiement
        """
        if not FINANCE_INTEGRATION_AVAILABLE:
            logger.warning("Module finances non disponible, utilisation du système simplifié")
            return FamilyPaymentService._process_family_payment_simple(payment_group)
        
        try:
            # Utiliser le service d'intégration financière
            result = FamilyFinanceIntegrationService.process_family_payment(
                payment_group=payment_group,
                payment_method_id=payment_method_id,
                additional_data=payment_data or {}
            )
            
            if result['success']:
                logger.info(f"Paiement familial réussi: {payment_group.id} - {payment_group.total_amount}â‚¬")
            else:
                logger.error(f"Ã‰chec paiement familial: {payment_group.id} - {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du paiement familial {payment_group.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'payment_group': payment_group
            }
    
    @staticmethod
    def _process_family_payment_simple(payment_group):
        """
        Version simplifiée du traitement de paiement sans module finances.
        """
        try:
            with transaction.atomic():
                payment_group.is_paid = True
                payment_group.save()
                
                # Tentative d'enregistrement dans le module finances si disponible
                try:
                    from apps.finances.models import Transaction
                    Transaction.objects.create(
                        amount=payment_group.total_amount,
                        description=f"Paiement familial: {payment_group.description}",
                        transaction_type='income',
                        family_payment_group=payment_group,
                        organization=payment_group.family.organization
                    )
                except ImportError:
                    logger.warning("Module finances non disponible pour enregistrer la transaction")
                
                logger.info(f"Paiement familial traité: {payment_group.id}")
                
                return {
                    'success': True,
                    'payment_group': payment_group,
                    'message': _("Paiement traité avec succès")
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paiement familial {payment_group.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': _("Erreur lors du traitement du paiement")
            }
    
    @staticmethod
    def get_family_financial_summary(family, period_months=12):
        """
        Génère un résumé financier pour une famille.
        
        Returns:
            dict: Résumé avec totaux, paiements en attente, etc.
        """
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        payment_groups = family.payment_groups.filter(created_at__gte=start_date)
        
        summary = {
            'total_paid': payment_groups.filter(is_paid=True).aggregate(
                total=models.Sum('total_amount')
            )['total'] or Decimal('0.00'),
            'total_pending': payment_groups.filter(is_paid=False).aggregate(
                total=models.Sum('total_amount')
            )['total'] or Decimal('0.00'),
            'payment_count': payment_groups.count(),
            'pending_count': payment_groups.filter(is_paid=False).count(),
            'period_start': start_date,
            'period_end': end_date
        }
        
        return summary


class FamilyEventService:
    """Service pour gérer les événements familiaux."""
    
    @staticmethod
    def create_family_event(family, title, start_date, end_date=None, 
                          description='', location='', created_by=None,
                          concerned_members=None):
        """
        Crée un nouvel événement familial.
        
        Returns:
            FamilyEvent instance
        """
        event = FamilyEvent.objects.create(
            family=family,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            location=location,
            created_by=created_by or family.primary_responsible
        )
        
        if concerned_members:
            event.concerned_members.set(concerned_members)
        
        logger.info(f"Ã‰vénement familial créé: {event.title} pour {family.family_name}")
        
        return event
    
    @staticmethod
    def get_family_calendar_events(family, start_date, end_date):
        """
        Récupère tous les événements du calendrier familial sur une période.
        
        Returns:
            dict: Ã‰vénements organisés par type
        """
        events = {
            'family_events': [],
            'competition_events': [],
            'training_events': []
        }
        
        # Ã‰vénements familiaux
        family_events = FamilyEvent.objects.filter(
            family=family,
            start_date__gte=start_date,
            start_date__lte=end_date
        )
        
        events['family_events'] = list(family_events)
        
        # TODO: Ajouter les événements de compétitions et d'entraÃ®nements
        # des membres de la famille
        
        return events
    
    @staticmethod
    def notify_family_members(family, event, notification_type='event_created'):
        """
        Notifie les membres de la famille d'un événement.
        
        Args:
            family: Instance de Family
            event: Instance de FamilyEvent
            notification_type: Type de notification
        """
        try:
            # TODO: Intégrer avec le système de notifications de MartialComp
            
            members_to_notify = family.members.filter(
                is_active=True,
                receive_family_notifications=True
            )
            
            for member in members_to_notify:
                # Créer une notification
                # Notification.objects.create(...)
                pass
            
            logger.info(f"Notifications envoyées pour l'événement {event.title}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des notifications: {e}")


class FamilyManagementService:
    """Service principal pour la gestion familiale."""
    
    @staticmethod
    def create_family_from_practitioner(practitioner, family_name=None):
        """
        Crée une famille Ã  partir d'un pratiquant existant.
        
        Returns:
            Family instance ou None si erreur
        """
        if not practitioner.user:
            raise ValueError("Le pratiquant doit avoir un compte utilisateur")
        
        if practitioner.family:
            return practitioner.family
        
        family_name = family_name or f"Famille {practitioner.last_name}"
        
        try:
            with transaction.atomic():
                family = Family.objects.create(
                    family_name=family_name,
                    primary_responsible=practitioner.user,
                    organization=practitioner.organization
                )
                
                # Ajouter le pratiquant Ã  la famille
                practitioner.family = family
                practitioner.family_role = 'parent'
                practitioner.save()
                
                logger.info(f"Famille créée Ã  partir du pratiquant {practitioner.full_name}: {family.family_name}")
                
                return family
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de famille pour {practitioner.id}: {e}")
            raise
    
    @staticmethod
    def add_practitioner_to_family(family, practitioner, role='child', can_manage=False):
        """
        Ajoute un pratiquant existant Ã  une famille.
        
        Returns:
            FamilyMember instance
        """
        if practitioner.family and practitioner.family != family:
            raise ValueError("Le pratiquant appartient déjÃ  Ã  une autre famille")
        
        try:
            with transaction.atomic():
                # Mettre Ã  jour le pratiquant
                practitioner.family = family
                practitioner.family_role = role
                practitioner.save()
                
                # Créer ou mettre Ã  jour le membre de famille
                member, created = FamilyMember.objects.get_or_create(
                    family=family,
                    practitioner=practitioner,
                    defaults={
                        'user': practitioner.user,
                        'role': role,
                        'can_manage_others': can_manage,
                        'is_active': True
                    }
                )
                
                if not created:
                    member.role = role
                    member.can_manage_others = can_manage
                    member.save()
                
                logger.info(f"Pratiquant ajouté Ã  la famille: {practitioner.full_name} -> {family.family_name}")
                
                return member
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du pratiquant {practitioner.id} Ã  la famille {family.id}: {e}")
            raise
    
    @staticmethod
    def get_family_statistics(family):
        """
        Génère des statistiques complètes pour une famille.
        
        Args:
            family: Instance de Family
            
        Returns:
            dict: Statistiques détaillées de la famille
        """
        from django.db.models import Count, Sum, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            # Statistiques de base
            active_members = family.get_active_members()
            total_practitioners = family.get_total_practitioners()
            
            stats = {
                'basic': {
                    'total_members': active_members.count(),
                    'total_practitioners': total_practitioners,
                    'family_created': family.created_at,
                    'family_age_days': (timezone.now() - family.created_at).days
                },
                'members': {
                    'by_role': {},
                    'active_count': active_members.count(),
                    'can_manage_count': active_members.filter(can_manage_others=True).count()
                },
                'payments': {
                    'total_groups': family.payment_groups.count(),
                    'paid_groups': family.payment_groups.filter(is_paid=True).count(),
                    'pending_groups': family.payment_groups.filter(is_paid=False).count(),
                    'total_paid_amount': Decimal('0.00'),
                    'total_pending_amount': Decimal('0.00')
                },
                'events': {
                    'total_events': family.family_events.count(),
                    'upcoming_events': family.family_events.filter(
                        start_date__gte=timezone.now()
                    ).count(),
                    'past_events': family.family_events.filter(
                        start_date__lt=timezone.now()
                    ).count()
                },
                'activity': {
                    'last_30_days': {
                        'payment_groups': 0,
                        'events_created': 0,
                        'members_added': 0
                    }
                }
            }
            
            # Statistiques par rÃ´le
            role_counts = active_members.values('role').annotate(count=Count('id'))
            for role_data in role_counts:
                stats['members']['by_role'][role_data['role']] = role_data['count']
            
            # Statistiques de paiement
            paid_amount = family.payment_groups.filter(is_paid=True).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            pending_amount = family.payment_groups.filter(is_paid=False).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            stats['payments']['total_paid_amount'] = paid_amount
            stats['payments']['total_pending_amount'] = pending_amount
            
            # Activité des 30 derniers jours
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            stats['activity']['last_30_days']['payment_groups'] = family.payment_groups.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            stats['activity']['last_30_days']['events_created'] = family.family_events.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            stats['activity']['last_30_days']['members_added'] = active_members.filter(
                joined_at__gte=thirty_days_ago
            ).count()
            
            # Intégration financière si disponible
            if FINANCE_INTEGRATION_AVAILABLE:
                try:
                    finance_summary = FamilyFinanceIntegrationService.get_family_financial_summary(family)
                    stats['finance_integration'] = finance_summary
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération des données financières: {e}")
                    stats['finance_integration'] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des statistiques pour la famille {family.id}: {e}")
            return {
                'error': str(e),
                'basic': {
                    'total_members': 0,
                    'total_practitioners': 0
                }
            }
    
    @staticmethod
    def get_family_financial_dashboard(family):
        """
        Génère un tableau de bord financier spécifique pour une famille.
        
        Args:
            family: Instance de Family
            
        Returns:
            dict: Données du tableau de bord financier
        """
        if not FINANCE_INTEGRATION_AVAILABLE:
            return {
                'error': 'Module finances non disponible',
                'available_payment_methods': [],
                'pending_payments': family.payment_groups.filter(is_paid=False),
                'recent_payments': family.payment_groups.filter(is_paid=True).order_by('-created_at')[:5]
            }
        
        try:
            # Méthodes de paiement disponibles
            payment_methods = FamilyFinanceUtils.get_available_payment_methods(family.organization)
            
            # Résumé financier
            financial_summary = FamilyFinanceIntegrationService.get_family_financial_summary(family)
            
            # Calcul des remises familiales potentielles
            sample_amount = Decimal('100.00')  # Montant d'exemple pour calculer les remises
            discount_info = FamilyFinanceUtils.calculate_family_discount(family, sample_amount)
            
            return {
                'available_payment_methods': payment_methods,
                'financial_summary': financial_summary,
                'discount_eligibility': discount_info,
                'pending_payment_groups': family.payment_groups.filter(is_paid=False).order_by('-created_at'),
                'recent_transactions': financial_summary.get('recent_payments', []),
                'outstanding_invoices': financial_summary.get('recent_invoices', []).filter(status='pending') if hasattr(financial_summary.get('recent_invoices', []), 'filter') else []
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tableau de bord financier: {e}")
            return {
                'error': str(e),
                'available_payment_methods': [],
                'financial_summary': {}
            }

