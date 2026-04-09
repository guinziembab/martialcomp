"""
Tâches Celery pour la gestion des affiliations saisonnières.
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(name='organizations.tasks.check_affiliation_renewals')
def check_affiliation_renewals():
    """
    Tâche quotidienne: vérifie les affiliations qui arrivent à expiration
    et envoie des rappels de renouvellement.

    Vérifie les affiliations dont la saison se termine dans X jours
    (X étant défini par renewal_reminder_days de la saison).
    """
    from apps.organizations.models import AffiliationPeriod, AffiliationPeriodStatus
    from apps.organizations.services import AffiliationSeasonService

    logger.info("Début de la vérification des renouvellements d'affiliation")

    try:
        # Récupérer les affiliations qui expirent bientôt
        expiring_affiliations = AffiliationSeasonService.get_expiring_affiliations()

        sent_count = 0
        for period in expiring_affiliations:
            # Vérifier si un rappel a déjà été envoyé récemment
            if period.last_reminder_sent:
                days_since_reminder = (timezone.now() - period.last_reminder_sent).days
                if days_since_reminder < 7:  # Pas plus d'un rappel par semaine
                    continue

            # Envoyer le rappel
            success = send_renewal_reminder.delay(period.id)
            if success:
                sent_count += 1

        logger.info(f"Rappels de renouvellement envoyés: {sent_count}")
        return f"Rappels envoyés: {sent_count}"

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des renouvellements: {e}")
        raise


@shared_task(name='organizations.tasks.update_expired_affiliations')
def update_expired_affiliations():
    """
    Tâche quotidienne: marque les affiliations expirées.

    Met à jour le statut des périodes d'affiliation dont la saison est terminée.
    """
    from apps.organizations.services import AffiliationSeasonService

    logger.info("Début de la mise à jour des affiliations expirées")

    try:
        updated_count = AffiliationSeasonService.update_expired_affiliations()
        logger.info(f"Affiliations expirées mises à jour: {updated_count}")
        return f"Affiliations expirées: {updated_count}"

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des affiliations expirées: {e}")
        raise


@shared_task(name='organizations.tasks.send_renewal_reminder')
def send_renewal_reminder(affiliation_period_id: int):
    """
    Envoie un rappel de renouvellement pour une période d'affiliation spécifique.

    Args:
        affiliation_period_id: ID de la période d'affiliation
    """
    from apps.organizations.models import AffiliationPeriod

    logger.info(f"Envoi du rappel de renouvellement pour la période {affiliation_period_id}")

    try:
        period = AffiliationPeriod.objects.select_related(
            'affiliation',
            'affiliation__parent_organization',
            'affiliation__child_organization',
            'season'
        ).get(id=affiliation_period_id)

        affiliation = period.affiliation
        club = affiliation.child_organization
        federation = affiliation.parent_organization
        season = period.season

        # Calculer les jours restants
        days_remaining = (season.end_date - timezone.now().date()).days

        # Récupérer les emails des responsables du club
        recipient_emails = []

        # Email du propriétaire de l'organisation club
        if hasattr(club, 'owner') and club.owner and club.owner.email:
            recipient_emails.append(club.owner.email)

        # Emails des membres avec rôle admin du club
        try:
            from apps.organizations.models import OrganizationMember
            admin_members = OrganizationMember.objects.filter(
                organization=club,
                role__in=['admin', 'owner', 'manager']
            ).select_related('user')
            for member in admin_members:
                if member.user and member.user.email:
                    recipient_emails.append(member.user.email)
        except Exception:
            pass

        # Supprimer les doublons
        recipient_emails = list(set(recipient_emails))

        if not recipient_emails:
            logger.warning(f"Aucun destinataire trouvé pour le club {club.name}")
            return False

        # Préparer le contexte du mail
        context = {
            'club_name': club.name,
            'federation_name': federation.name,
            'season_name': season.name,
            'days_remaining': days_remaining,
            'end_date': season.end_date,
            'renewal_url': f"{settings.SITE_URL}/club/affiliations/{affiliation.id}/renew/",
        }

        # Générer le contenu du mail
        subject = f"[{federation.name}] Rappel: Renouvellement d'affiliation - {season.name}"

        # Version texte simple
        message = f"""
Bonjour,

Ceci est un rappel concernant votre affiliation à {federation.name}.

Votre affiliation pour la saison {season.name} expire dans {days_remaining} jours (le {season.end_date.strftime('%d/%m/%Y')}).

Pour continuer à bénéficier de votre affiliation, nous vous invitons à procéder au renouvellement.

Vous pouvez renouveler votre affiliation en vous connectant à votre espace club :
{context['renewal_url']}

Si vous avez des questions, n'hésitez pas à contacter {federation.name}.

Cordialement,
L'équipe MartialComp
"""

        # Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )

        # Mettre à jour la date du dernier rappel
        period.last_reminder_sent = timezone.now()
        period.save(update_fields=['last_reminder_sent', 'updated_at'])

        logger.info(f"Rappel envoyé avec succès pour {club.name} -> {federation.name}")
        return True

    except AffiliationPeriod.DoesNotExist:
        logger.error(f"Période d'affiliation {affiliation_period_id} non trouvée")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du rappel: {e}")
        raise


@shared_task(name='organizations.tasks.send_expiration_notice')
def send_expiration_notice(affiliation_period_id: int):
    """
    Envoie une notification d'expiration pour une affiliation.

    Args:
        affiliation_period_id: ID de la période d'affiliation expirée
    """
    from apps.organizations.models import AffiliationPeriod

    logger.info(f"Envoi de la notification d'expiration pour la période {affiliation_period_id}")

    try:
        period = AffiliationPeriod.objects.select_related(
            'affiliation',
            'affiliation__parent_organization',
            'affiliation__child_organization',
            'season'
        ).get(id=affiliation_period_id)

        affiliation = period.affiliation
        club = affiliation.child_organization
        federation = affiliation.parent_organization
        season = period.season

        # Récupérer les emails des responsables du club
        recipient_emails = []

        if hasattr(club, 'owner') and club.owner and club.owner.email:
            recipient_emails.append(club.owner.email)

        try:
            from apps.organizations.models import OrganizationMember
            admin_members = OrganizationMember.objects.filter(
                organization=club,
                role__in=['admin', 'owner', 'manager']
            ).select_related('user')
            for member in admin_members:
                if member.user and member.user.email:
                    recipient_emails.append(member.user.email)
        except Exception:
            pass

        recipient_emails = list(set(recipient_emails))

        if not recipient_emails:
            logger.warning(f"Aucun destinataire trouvé pour le club {club.name}")
            return False

        subject = f"[{federation.name}] Affiliation expirée - {season.name}"

        message = f"""
Bonjour,

Nous vous informons que votre affiliation à {federation.name} pour la saison {season.name} a expiré.

Pour renouveler votre affiliation et continuer à bénéficier des avantages de membre, veuillez vous connecter à votre espace club.

Si vous avez des questions, n'hésitez pas à contacter {federation.name}.

Cordialement,
L'équipe MartialComp
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )

        logger.info(f"Notification d'expiration envoyée pour {club.name}")
        return True

    except AffiliationPeriod.DoesNotExist:
        logger.error(f"Période d'affiliation {affiliation_period_id} non trouvée")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification: {e}")
        raise


@shared_task(name='organizations.tasks.generate_season_invoices')
def generate_season_invoices(season_id: int):
    """
    Génère les factures pour toutes les affiliations actives d'une saison.

    Args:
        season_id: ID de la saison
    """
    from apps.organizations.models import (
        SportSeason, AffiliationPeriod, AffiliationPeriodStatus
    )
    from apps.organizations.services import AffiliationInvoiceService

    logger.info(f"Génération des factures pour la saison {season_id}")

    try:
        season = SportSeason.objects.get(id=season_id)

        # Récupérer les périodes en attente de paiement sans facture
        periods_without_invoice = AffiliationPeriod.objects.filter(
            season=season,
            status=AffiliationPeriodStatus.PENDING_PAYMENT,
            invoice__isnull=True
        ).select_related('affiliation')

        generated_count = 0
        for period in periods_without_invoice:
            try:
                AffiliationInvoiceService.generate_invoice(period)
                generated_count += 1
            except Exception as e:
                logger.error(f"Erreur génération facture pour période {period.id}: {e}")

        logger.info(f"Factures générées: {generated_count}")
        return f"Factures générées: {generated_count}"

    except SportSeason.DoesNotExist:
        logger.error(f"Saison {season_id} non trouvée")
        return "Saison non trouvée"
    except Exception as e:
        logger.error(f"Erreur lors de la génération des factures: {e}")
        raise
