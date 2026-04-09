"""
Taches Celery pour le module competitions
Prompt 2 - Systeme d'alertes et notifications de grades
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext as _
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# PROMPT 2: Taches de verification d'eligibilite de grade
# =============================================================================

@shared_task(name='competitions.tasks.check_grade_eligibility_daily')
def check_grade_eligibility_daily():
    """
    Verifie quotidiennement l'eligibilite des pratiquants pour leur prochain grade.
    Envoie des notifications aux jalons J-30, J-7, J-0.

    Cette tache est executee tous les jours a 8h00.
    """
    from apps.competitions.models.practitioners import Practitioner
    from apps.competitions.services.grade_eligibility import GradeEligibilityService
    from apps.grades.models import GradeAlertLog

    logger.info("Debut de la verification quotidienne d'eligibilite de grade")

    notifications_sent = 0
    errors = 0

    try:
        # Recuperer tous les pratiquants actifs avec un utilisateur associe
        practitioners = Practitioner.objects.filter(
            user__isnull=False,
            user__is_active=True,
        ).select_related('user', 'grade', 'primary_discipline')

        for practitioner in practitioners:
            try:
                # Verifier l'eligibilite pour la discipline principale
                result = GradeEligibilityService.check_eligibility(
                    practitioner,
                    practitioner.primary_discipline
                )

                if result.status == 'no_next_grade':
                    # Pas de grade suivant, on passe
                    continue

                # Verifier les jalons de notification
                should_notify, milestone = _check_notification_milestone(
                    result.days_remaining,
                    practitioner,
                    result.next_grade
                )

                if should_notify:
                    _send_grade_eligibility_notification(
                        practitioner,
                        result,
                        milestone
                    )
                    notifications_sent += 1

            except Exception as e:
                logger.error(f"Erreur pour practitioner {practitioner.id}: {e}")
                errors += 1

        logger.info(
            f"Verification eligibilite terminee: {notifications_sent} notifications, "
            f"{errors} erreurs"
        )

    except Exception as e:
        logger.error(f"Erreur globale check_grade_eligibility_daily: {e}")

    return {
        'notifications_sent': notifications_sent,
        'errors': errors,
    }


def _check_notification_milestone(days_remaining, practitioner, next_grade):
    """
    Verifie si le pratiquant doit recevoir une notification pour un jalon.

    Args:
        days_remaining: Jours restants avant eligibilite
        practitioner: Instance de Practitioner
        next_grade: Dict avec les infos du grade suivant

    Returns:
        tuple: (should_notify: bool, milestone: str|None)
    """
    from apps.grades.models import GradeAlertLog

    # Definir les jalons
    milestones = {
        0: 'eligible',    # Devient eligible
        7: 'j-7',         # 7 jours avant
        30: 'j-30',       # 30 jours avant
    }

    # Verifier si le jalon est atteint
    milestone = None
    if days_remaining is not None:
        if days_remaining <= 0:
            milestone = 'eligible'
        elif days_remaining <= 7:
            milestone = 'j-7'
        elif days_remaining <= 30:
            milestone = 'j-30'

    if not milestone:
        return False, None

    # Verifier si la notification a deja ete envoyee
    next_grade_id = next_grade.get('id') if next_grade else None
    if not next_grade_id:
        return False, None

    already_notified = GradeAlertLog.objects.filter(
        practitioner=practitioner,
        target_grade_id=next_grade_id,
        milestone=milestone,
    ).exists()

    if already_notified:
        return False, None

    return True, milestone


def _send_grade_eligibility_notification(practitioner, eligibility_result, milestone):
    """
    Envoie une notification d'eligibilite de grade.

    Args:
        practitioner: Instance de Practitioner
        eligibility_result: Resultat de GradeEligibilityService
        milestone: Type de jalon ('j-30', 'j-7', 'eligible')
    """
    from apps.competitions.models.notifications import Notification
    from apps.grades.models import GradeAlertLog
    from django.urls import reverse

    if not practitioner.user:
        return

    next_grade = eligibility_result.next_grade
    next_grade_name = next_grade.get('name', 'Prochain grade') if next_grade else 'Prochain grade'

    # Construire le message selon le jalon
    if milestone == 'eligible':
        title = _("Vous etes eligible pour passer au grade superieur!")
        message = _(
            "Felicitations! Vous remplissez maintenant toutes les conditions "
            "pour passer au grade %(grade)s. Consultez les prochains examens disponibles."
        ) % {'grade': next_grade_name}
        notification_type = 'success'
        priority = 'important'
    elif milestone == 'j-7':
        title = _("Plus que 7 jours avant eligibilite!")
        message = _(
            "Dans 7 jours, vous serez eligible pour passer au grade %(grade)s. "
            "Preparez-vous et consultez les examens a venir."
        ) % {'grade': next_grade_name}
        notification_type = 'info'
        priority = 'standard'
    else:  # j-30
        title = _("30 jours avant eligibilite de grade")
        message = _(
            "Dans environ 30 jours, vous serez eligible pour passer au grade %(grade)s. "
            "C'est le moment de vous preparer."
        ) % {'grade': next_grade_name}
        notification_type = 'info'
        priority = 'low'

    # Creer la notification
    try:
        action_url = reverse('competitions:dashboard:participant')
    except Exception:
        action_url = None

    notification = Notification.objects.create(
        user=practitioner.user,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url,
        action_text=_("Voir ma progression"),
    )

    # Enregistrer l'alerte dans le log
    GradeAlertLog.objects.create(
        practitioner=practitioner,
        target_grade_id=next_grade.get('id') if next_grade else None,
        milestone=milestone,
        notification=notification,
    )

    logger.info(
        f"Notification grade envoyee: {practitioner.full_name} - "
        f"{milestone} - {next_grade_name}"
    )


@shared_task(name='competitions.tasks.check_exam_deadlines_daily')
def check_exam_deadlines_daily():
    """
    Verifie les deadlines d'inscription aux examens de grade.
    Envoie des alertes aux pratiquants eligibles J-14 et J-3 avant la deadline.

    Cette tache est executee tous les jours a 9h30.
    """
    from apps.grades.models import GradeExam, GradeExamRegistration
    from apps.competitions.models.practitioners import Practitioner
    from apps.competitions.models.notifications import Notification
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    logger.info("Debut de la verification des deadlines d'examen")

    today = timezone.now().date()
    notifications_sent = 0

    # Definir les jalons de deadline
    deadline_milestones = [
        (14, 'deadline-j14', 'standard'),  # J-14
        (3, 'deadline-j3', 'important'),   # J-3
    ]

    try:
        for days_before, milestone, priority in deadline_milestones:
            target_date = today + timedelta(days=days_before)

            # Trouver les examens dont la deadline est dans X jours
            exams = GradeExam.objects.filter(
                registration_deadline=target_date,
                status__in=['scheduled', 'in_progress'],
            ).select_related('discipline')

            for exam in exams:
                # Trouver les pratiquants eligibles qui ne sont pas encore inscrits
                eligible_practitioners = _get_eligible_practitioners_for_exam(exam)

                for practitioner in eligible_practitioners:
                    if not practitioner.user:
                        continue

                    # Verifier si deja notifie pour cet examen et ce jalon
                    from apps.grades.models import GradeAlertLog
                    already_notified = GradeAlertLog.objects.filter(
                        practitioner=practitioner,
                        exam=exam,
                        milestone=milestone,
                    ).exists()

                    if already_notified:
                        continue

                    # Envoyer la notification
                    _send_exam_deadline_notification(
                        practitioner, exam, days_before, milestone, priority
                    )
                    notifications_sent += 1

        logger.info(f"Verification deadlines terminee: {notifications_sent} notifications")

    except Exception as e:
        logger.error(f"Erreur check_exam_deadlines_daily: {e}")

    return {'notifications_sent': notifications_sent}


def _get_eligible_practitioners_for_exam(exam):
    """
    Recupere les pratiquants eligibles pour un examen qui ne sont pas inscrits.
    """
    from apps.competitions.models.practitioners import Practitioner
    from apps.grades.models import GradeExamRegistration
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    # Pratiquants deja inscrits
    registered_ids = GradeExamRegistration.objects.filter(
        exam=exam
    ).values_list('practitioner_id', flat=True)

    # Pratiquants potentiels (meme discipline)
    practitioners = Practitioner.objects.filter(
        primary_discipline=exam.discipline,
        user__isnull=False,
        user__is_active=True,
    ).exclude(id__in=registered_ids)

    eligible = []
    for practitioner in practitioners:
        result = GradeEligibilityService.check_eligibility(practitioner, exam.discipline)
        if result.is_eligible:
            # Verifier si le grade cible de l'examen correspond
            if result.next_grade:
                next_grade_id = result.next_grade.get('id')
                if exam.available_grades.filter(id=next_grade_id).exists():
                    eligible.append(practitioner)

    return eligible


def _send_exam_deadline_notification(practitioner, exam, days_before, milestone, priority):
    """
    Envoie une notification de deadline d'examen.
    """
    from apps.competitions.models.notifications import Notification
    from apps.grades.models import GradeAlertLog
    from django.urls import reverse

    if days_before == 3:
        title = _("Derniere chance: Inscription examen dans 3 jours!")
        message = _(
            "La date limite d'inscription pour l'examen '%(exam)s' est dans 3 jours. "
            "Inscrivez-vous maintenant pour ne pas manquer cette opportunite!"
        ) % {'exam': exam.title}
    else:
        title = _("Rappel: Examen de grade a venir")
        message = _(
            "L'examen '%(exam)s' a lieu le %(date)s. "
            "Vous avez encore 14 jours pour vous inscrire."
        ) % {'exam': exam.title, 'date': exam.date.strftime('%d/%m/%Y')}

    # URL d'inscription
    try:
        action_url = reverse('grades:exam_registration', kwargs={'exam_id': exam.id})
    except Exception:
        action_url = None

    notification = Notification.objects.create(
        user=practitioner.user,
        title=title,
        message=message,
        notification_type='warning' if days_before == 3 else 'info',
        priority=priority,
        action_url=action_url,
        action_text=_("S'inscrire a l'examen"),
    )

    # Log
    GradeAlertLog.objects.create(
        practitioner=practitioner,
        exam=exam,
        milestone=milestone,
        notification=notification,
    )

    logger.info(f"Notification deadline examen: {practitioner.full_name} - {exam.title}")


@shared_task(name='competitions.tasks.send_exam_reminders')
def send_exam_reminders():
    """
    Envoie des rappels J-1 aux pratiquants inscrits a un examen.

    Cette tache est executee tous les jours a 18h00.
    """
    from apps.grades.models import GradeExam, GradeExamRegistration
    from apps.competitions.models.notifications import Notification

    logger.info("Debut de l'envoi des rappels J-1 examens")

    tomorrow = timezone.now().date() + timedelta(days=1)
    notifications_sent = 0

    try:
        # Examens demain
        exams = GradeExam.objects.filter(
            date=tomorrow,
            status='scheduled',
        )

        for exam in exams:
            # Pratiquants inscrits et approuves
            registrations = GradeExamRegistration.objects.filter(
                exam=exam,
                status='approved',
            ).select_related('practitioner', 'practitioner__user')

            for reg in registrations:
                if not reg.practitioner or not reg.practitioner.user:
                    continue

                title = _("Rappel: Votre examen de grade est demain!")
                message = _(
                    "L'examen '%(exam)s' a lieu demain %(date)s a %(location)s. "
                    "Preparez-vous et arrivez a l'heure. Bonne chance!"
                ) % {
                    'exam': exam.title,
                    'date': exam.date.strftime('%d/%m/%Y'),
                    'location': exam.location or 'lieu indique',
                }

                Notification.objects.create(
                    user=reg.practitioner.user,
                    title=title,
                    message=message,
                    notification_type='info',
                    priority='important',
                )

                notifications_sent += 1
                logger.debug(f"Rappel examen envoye: {reg.practitioner.full_name}")

        logger.info(f"Rappels J-1 examens: {notifications_sent} notifications")

    except Exception as e:
        logger.error(f"Erreur send_exam_reminders: {e}")

    return {'notifications_sent': notifications_sent}


@shared_task(name='competitions.tasks.send_monthly_eligibility_reminders')
def send_monthly_eligibility_reminders():
    """
    Envoie des rappels mensuels aux pratiquants eligibles qui ne sont pas inscrits
    a un examen.

    Cette tache est executee le 1er de chaque mois a 10h00.
    """
    from apps.competitions.models.practitioners import Practitioner
    from apps.competitions.models.notifications import Notification
    from apps.competitions.services.grade_eligibility import GradeEligibilityService
    from apps.grades.models import GradeExam, GradeExamRegistration

    logger.info("Debut de l'envoi des rappels mensuels d'eligibilite")

    notifications_sent = 0
    today = timezone.now().date()

    try:
        # Pratiquants actifs avec utilisateur
        practitioners = Practitioner.objects.filter(
            user__isnull=False,
            user__is_active=True,
        ).select_related('user', 'primary_discipline')

        for practitioner in practitioners:
            result = GradeEligibilityService.check_eligibility(
                practitioner,
                practitioner.primary_discipline
            )

            if not result.is_eligible:
                continue

            # Verifier s'il n'est pas deja inscrit a un examen a venir
            next_grade_id = result.next_grade.get('id') if result.next_grade else None
            if not next_grade_id:
                continue

            is_registered = GradeExamRegistration.objects.filter(
                practitioner=practitioner,
                exam__date__gte=today,
                exam__status__in=['scheduled', 'in_progress'],
            ).exists()

            if is_registered:
                continue

            # Verifier si une notification mensuelle a deja ete envoyee ce mois
            from apps.grades.models import GradeAlertLog
            this_month_start = today.replace(day=1)
            already_reminded = GradeAlertLog.objects.filter(
                practitioner=practitioner,
                milestone='monthly-reminder',
                created_at__gte=this_month_start,
            ).exists()

            if already_reminded:
                continue

            # Envoyer la notification
            next_grade_name = result.next_grade.get('name', 'grade superieur')
            title = _("Rappel: Vous etes eligible pour un passage de grade")
            message = _(
                "Vous remplissez les conditions pour passer au grade %(grade)s "
                "mais vous n'etes inscrit a aucun examen. Consultez les examens disponibles!"
            ) % {'grade': next_grade_name}

            notification = Notification.objects.create(
                user=practitioner.user,
                title=title,
                message=message,
                notification_type='info',
                priority='standard',
            )

            GradeAlertLog.objects.create(
                practitioner=practitioner,
                target_grade_id=next_grade_id,
                milestone='monthly-reminder',
                notification=notification,
            )

            notifications_sent += 1

        logger.info(f"Rappels mensuels: {notifications_sent} notifications")

    except Exception as e:
        logger.error(f"Erreur send_monthly_eligibility_reminders: {e}")

    return {'notifications_sent': notifications_sent}


# =============================================================================
# Taches utilitaires
# =============================================================================

@shared_task(name='competitions.tasks.invalidate_grade_cache')
def invalidate_grade_cache(practitioner_id):
    """
    Invalide le cache d'eligibilite pour un pratiquant specifique.
    Appelee apres un changement de grade ou d'exigences.
    """
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    try:
        GradeEligibilityService.invalidate_cache(practitioner_id)
        logger.debug(f"Cache eligibilite invalide pour practitioner {practitioner_id}")
    except Exception as e:
        logger.error(f"Erreur invalidation cache: {e}")


@shared_task(name='competitions.tasks.recalculate_all_eligibility')
def recalculate_all_eligibility():
    """
    Recalcule l'eligibilite pour tous les pratiquants.
    Utilise avec precaution car peut etre couteux.
    """
    from apps.competitions.models.practitioners import Practitioner
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    logger.info("Debut du recalcul global d'eligibilite")

    practitioners = Practitioner.objects.filter(
        user__isnull=False,
    ).select_related('primary_discipline')

    count = 0
    for practitioner in practitioners:
        try:
            # Invalider le cache d'abord
            GradeEligibilityService.invalidate_cache(practitioner.id)
            # Recalculer
            GradeEligibilityService.check_eligibility(
                practitioner,
                practitioner.primary_discipline
            )
            count += 1
        except Exception as e:
            logger.error(f"Erreur recalcul pour {practitioner.id}: {e}")

    logger.info(f"Recalcul eligibilite termine: {count} pratiquants")
    return {'recalculated': count}


# =============================================================================
# Nettoyage automatique des juges ad-hoc
# =============================================================================

@shared_task(name='competitions.tasks.cleanup_adhoc_judges')
def cleanup_adhoc_judges():
    """
    Passe en 'completed' les juges ad-hoc de competitions terminees.
    Executee quotidiennement pour eviter l'accumulation.
    """
    try:
        from apps.competitions.models.adhoc_judges import AdHocJudge
        today = timezone.now().date()
        updated = AdHocJudge.objects.filter(
            status='active',
            competition__end_date__lt=today
        ).update(status='completed')
        if updated:
            logger.info(f"Cleanup adhoc judges: {updated} passes en completed")
        return {'cleaned': updated}
    except ImportError:
        return {'cleaned': 0}
