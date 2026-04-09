"""
Taches Celery pour les notifications de grade.
Prompt 2 - Systeme d'Alertes et Notifications Proactives

Ces taches verifient quotidiennement l'eligibilite des pratiquants
et envoient des notifications automatiques.
"""

import logging
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name='competitions.tasks.check_grade_eligibility_daily')
def check_grade_eligibility_daily():
    """
    Tache quotidienne pour verifier l'eligibilite de tous les pratiquants
    et creer les notifications appropriees.

    Execute: Tous les jours a 8h00

    Scenarios:
    - J-30 avant eligibilite
    - J-7 avant eligibilite
    - J-0 eligibilite atteinte
    """
    from apps.competitions.models import Practitioner
    from apps.competitions.models.notifications import Notification, NotificationPreference
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    logger.info("Debut de la verification quotidienne d'eligibilite de grade")

    notifications_created = 0
    errors = 0

    try:
        # Recuperer tous les pratiquants actifs avec un utilisateur associe
        practitioners = Practitioner.objects.filter(
            user__isnull=False,
            user__is_active=True
        ).select_related('user', 'primary_discipline')

        for practitioner in practitioners:
            try:
                # Verifier les preferences de notification
                prefs, _ = NotificationPreference.objects.get_or_create(
                    user=practitioner.user,
                    defaults={'grade_notifications': True}
                )

                if not prefs.grade_notifications:
                    continue

                # Obtenir la discipline principale
                discipline = practitioner.primary_discipline
                if not discipline:
                    # Essayer via les disciplines secondaires
                    if practitioner.disciplines.exists():
                        discipline = practitioner.disciplines.first()
                    else:
                        continue

                # Calculer l'eligibilite
                result = GradeEligibilityService.check_eligibility(practitioner, discipline)

                if result.status == 'no_next_grade':
                    continue

                # Verifier les seuils de notification
                days = result.days_remaining

                # J-30 avant eligibilite
                if days == 30:
                    notification = _create_eligibility_notification(
                        practitioner.user,
                        result,
                        'upcoming',
                        30
                    )
                    if notification:
                        notifications_created += 1

                # J-7 avant eligibilite
                elif days == 7:
                    notification = _create_eligibility_notification(
                        practitioner.user,
                        result,
                        'soon',
                        7
                    )
                    if notification:
                        notifications_created += 1

                # J-0 eligibilite atteinte
                elif days == 0 and result.is_eligible:
                    # Verifier qu'on n'a pas deja notifie aujourd'hui
                    already_notified = Notification.objects.filter(
                        user=practitioner.user,
                        title__icontains=result.next_grade.get('name', ''),
                        created_at__date=timezone.now().date()
                    ).exists()

                    if not already_notified:
                        notification = _create_eligibility_notification(
                            practitioner.user,
                            result,
                            'reached',
                            0
                        )
                        if notification:
                            notifications_created += 1

            except Exception as e:
                logger.error(f"Erreur verification eligibilite pour practitioner {practitioner.id}: {e}")
                errors += 1

        logger.info(
            f"Verification eligibilite terminee: {notifications_created} notifications creees, "
            f"{errors} erreurs"
        )

    except Exception as e:
        logger.error(f"Erreur dans check_grade_eligibility_daily: {e}")
        raise

    return {'notifications_created': notifications_created, 'errors': errors}


@shared_task(name='competitions.tasks.check_exam_deadlines_daily')
def check_exam_deadlines_daily():
    """
    Tache quotidienne pour verifier les deadlines d'inscription aux examens.

    Execute: Tous les jours a 9h00

    Scenarios:
    - J-14 avant deadline inscription
    - J-3 avant deadline inscription (urgent)
    """
    from apps.grades.models import GradeExam, GradeExamRegistration
    from apps.competitions.models import Practitioner
    from apps.competitions.models.notifications import Notification, NotificationPreference
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    logger.info("Debut de la verification des deadlines d'examens")

    notifications_created = 0
    errors = 0
    today = timezone.now().date()

    try:
        # Examens avec deadline dans 14 ou 3 jours
        deadlines_14 = today + timedelta(days=14)
        deadlines_3 = today + timedelta(days=3)

        exams = GradeExam.objects.filter(
            Q(registration_deadline=deadlines_14) | Q(registration_deadline=deadlines_3),
            status='scheduled',
            date__gte=today
        ).prefetch_related('available_grades')

        for exam in exams:
            try:
                days_until_deadline = (exam.registration_deadline - today).days
                priority = 'urgent' if days_until_deadline <= 3 else 'high'

                # Trouver les pratiquants eligibles non inscrits
                for grade in exam.available_grades.all():
                    # Trouver les pratiquants avec le grade precedent
                    eligible_practitioners = _get_eligible_practitioners_for_grade(
                        grade, exam.discipline
                    )

                    for practitioner in eligible_practitioners:
                        try:
                            if not practitioner.user:
                                continue

                            # Verifier preferences
                            prefs, _ = NotificationPreference.objects.get_or_create(
                                user=practitioner.user,
                                defaults={'grade_notifications': True}
                            )
                            if not prefs.grade_notifications:
                                continue

                            # Verifier si deja inscrit
                            already_registered = GradeExamRegistration.objects.filter(
                                practitioner=practitioner,
                                exam=exam
                            ).exists()

                            if already_registered:
                                continue

                            # Verifier qu'on n'a pas deja notifie pour cette deadline
                            already_notified = Notification.objects.filter(
                                user=practitioner.user,
                                title__icontains=exam.title,
                                created_at__date=today
                            ).exists()

                            if already_notified:
                                continue

                            # Creer la notification
                            notification = _create_exam_deadline_notification(
                                practitioner.user,
                                exam,
                                grade,
                                days_until_deadline,
                                priority
                            )

                            if notification:
                                notifications_created += 1

                        except Exception as e:
                            logger.error(f"Erreur notification deadline pour {practitioner.id}: {e}")
                            errors += 1

            except Exception as e:
                logger.error(f"Erreur traitement examen {exam.id}: {e}")
                errors += 1

        logger.info(
            f"Verification deadlines terminee: {notifications_created} notifications, "
            f"{errors} erreurs"
        )

    except Exception as e:
        logger.error(f"Erreur dans check_exam_deadlines_daily: {e}")
        raise

    return {'notifications_created': notifications_created, 'errors': errors}


@shared_task(name='competitions.tasks.send_exam_reminders')
def send_exam_reminders():
    """
    Envoie les rappels J-1 aux pratiquants inscrits a un examen.

    Execute: Tous les jours a 18h00
    """
    from apps.grades.models import GradeExam, GradeExamRegistration
    from apps.competitions.models.notifications import Notification, NotificationPreference

    logger.info("Debut de l'envoi des rappels d'examens J-1")

    notifications_created = 0
    errors = 0
    tomorrow = timezone.now().date() + timedelta(days=1)

    try:
        # Examens demain
        exams_tomorrow = GradeExam.objects.filter(
            date=tomorrow,
            status='scheduled'
        )

        for exam in exams_tomorrow:
            # Recuperer les inscrits
            registrations = GradeExamRegistration.objects.filter(
                exam=exam,
                status__in=['confirmed', 'pending']
            ).select_related('practitioner__user')

            for registration in registrations:
                try:
                    user = registration.practitioner.user
                    if not user:
                        continue

                    # Verifier preferences
                    prefs, _ = NotificationPreference.objects.get_or_create(
                        user=user,
                        defaults={'grade_notifications': True}
                    )
                    if not prefs.grade_notifications:
                        continue

                    # Verifier qu'on n'a pas deja envoye ce rappel
                    already_reminded = Notification.objects.filter(
                        user=user,
                        title__icontains="Rappel",
                        created_at__date=timezone.now().date()
                    ).filter(
                        Q(title__icontains=exam.title) | Q(message__icontains=exam.title)
                    ).exists()

                    if already_reminded:
                        continue

                    # Creer la notification de rappel
                    notification = _create_exam_reminder_notification(
                        user,
                        exam,
                        registration
                    )

                    if notification:
                        notifications_created += 1

                except Exception as e:
                    logger.error(f"Erreur rappel pour registration {registration.id}: {e}")
                    errors += 1

        logger.info(
            f"Envoi rappels termine: {notifications_created} rappels envoyes, "
            f"{errors} erreurs"
        )

    except Exception as e:
        logger.error(f"Erreur dans send_exam_reminders: {e}")
        raise

    return {'reminders_sent': notifications_created, 'errors': errors}


@shared_task(name='competitions.tasks.send_monthly_eligibility_reminders')
def send_monthly_eligibility_reminders():
    """
    Envoie les rappels mensuels aux pratiquants eligibles non inscrits.

    Execute: 1er de chaque mois a 10h00
    """
    from apps.competitions.models import Practitioner
    from apps.grades.models import GradeExamRegistration
    from apps.competitions.models.notifications import Notification, NotificationPreference
    from apps.competitions.services.grade_eligibility import GradeEligibilityService

    logger.info("Debut de l'envoi des rappels mensuels d'eligibilite")

    notifications_created = 0
    errors = 0

    try:
        # Pratiquants actifs
        practitioners = Practitioner.objects.filter(
            user__isnull=False,
            user__is_active=True
        ).select_related('user', 'primary_discipline')

        for practitioner in practitioners:
            try:
                if not practitioner.user:
                    continue

                # Verifier preferences
                prefs, _ = NotificationPreference.objects.get_or_create(
                    user=practitioner.user,
                    defaults={'grade_notifications': True}
                )

                if not prefs.grade_notifications:
                    continue

                # Frequence de rappel
                if prefs.notification_frequency == 'never':
                    continue

                # Obtenir la discipline
                discipline = practitioner.primary_discipline
                if not discipline and practitioner.disciplines.exists():
                    discipline = practitioner.disciplines.first()

                if not discipline:
                    continue

                # Calculer eligibilite
                result = GradeEligibilityService.check_eligibility(practitioner, discipline)

                # Seulement si eligible
                if not result.is_eligible:
                    continue

                # Verifier si inscrit a un examen
                has_upcoming_registration = GradeExamRegistration.objects.filter(
                    practitioner=practitioner,
                    exam__date__gte=timezone.now().date(),
                    status__in=['confirmed', 'pending']
                ).exists()

                if has_upcoming_registration:
                    continue

                # Calculer depuis combien de temps eligible
                days_eligible = 0
                if result.eligibility_date:
                    days_eligible = (timezone.now().date() - result.eligibility_date).days

                # Creer le rappel mensuel
                notification = _create_monthly_reminder_notification(
                    practitioner.user,
                    result,
                    days_eligible
                )

                if notification:
                    notifications_created += 1

            except Exception as e:
                logger.error(f"Erreur rappel mensuel pour {practitioner.id}: {e}")
                errors += 1

        logger.info(
            f"Rappels mensuels termines: {notifications_created} envoyes, "
            f"{errors} erreurs"
        )

    except Exception as e:
        logger.error(f"Erreur dans send_monthly_eligibility_reminders: {e}")
        raise

    return {'reminders_sent': notifications_created, 'errors': errors}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def _create_eligibility_notification(user, result, notification_type, days_remaining):
    """
    Cree une notification d'eligibilite de grade.

    Args:
        user: Instance User
        result: EligibilityResult
        notification_type: 'upcoming' (J-30), 'soon' (J-7), 'reached' (J-0)
        days_remaining: Nombre de jours restants

    Returns:
        Notification ou None
    """
    from apps.competitions.models.notifications import Notification

    try:
        next_grade_name = result.next_grade.get('name', 'grade suivant') if result.next_grade else 'grade suivant'

        if notification_type == 'upcoming':
            title = f"Bientot eligible au grade {next_grade_name}"
            message = (
                f"Dans {days_remaining} jours, vous serez eligible au passage de grade "
                f"{next_grade_name}. Preparez-vous et consultez les exigences."
            )
            priority = 'standard'

        elif notification_type == 'soon':
            title = f"Plus que {days_remaining} jours avant eligibilite"
            message = (
                f"Vous serez eligible au grade {next_grade_name} dans {days_remaining} jours. "
            )
            if result.available_exams:
                exam = result.available_exams[0]
                message += f"Un examen est disponible le {exam.get('date_display', exam.get('date', 'bientot'))}."
            priority = 'important'

        elif notification_type == 'reached':
            title = f"Vous etes eligible au grade {next_grade_name} !"
            message = (
                f"Felicitations ! Vous remplissez toutes les conditions pour passer "
                f"au grade {next_grade_name}. Inscrivez-vous au prochain examen."
            )
            priority = 'important'

        else:
            return None

        # Generer l'URL d'action
        try:
            action_url = reverse('competitions:dashboard:participant')
        except Exception:
            action_url = '/competitions/dashboard/participant/'

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type='info',
            priority=priority,
            action_url=action_url,
            action_text='Voir ma progression'
        )

        logger.debug(f"Notification eligibilite creee pour {user.username}: {notification_type}")
        return notification

    except Exception as e:
        logger.error(f"Erreur creation notification eligibilite: {e}")
        return None


def _create_exam_deadline_notification(user, exam, grade, days_until_deadline, priority):
    """
    Cree une notification de deadline d'inscription a un examen.
    """
    from apps.competitions.models.notifications import Notification

    try:
        if days_until_deadline <= 3:
            title = f"URGENT : Inscription examen dans {days_until_deadline} jours"
            message = (
                f"Derniere chance ! L'inscription a l'examen '{exam.title}' du "
                f"{exam.date.strftime('%d/%m/%Y')} ferme dans {days_until_deadline} jours "
                f"({exam.registration_deadline.strftime('%d/%m/%Y')})."
            )
        else:
            title = f"Inscription examen : plus que {days_until_deadline} jours"
            message = (
                f"La date limite d'inscription a l'examen '{exam.title}' du "
                f"{exam.date.strftime('%d/%m/%Y')} approche. "
                f"Inscrivez-vous avant le {exam.registration_deadline.strftime('%d/%m/%Y')}."
            )

        try:
            action_url = reverse('grades:exam_register', kwargs={'exam_id': exam.id})
        except Exception:
            action_url = f'/grades/exams/{exam.id}/register/'

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type='warning' if days_until_deadline <= 3 else 'info',
            priority=priority,
            action_url=action_url,
            action_text="S'inscrire maintenant"
        )

        logger.debug(f"Notification deadline exam creee pour {user.username}")
        return notification

    except Exception as e:
        logger.error(f"Erreur creation notification deadline: {e}")
        return None


def _create_exam_reminder_notification(user, exam, registration):
    """
    Cree une notification de rappel J-1 pour un examen.
    """
    from apps.competitions.models.notifications import Notification

    try:
        grade_name = ''
        if registration.target_grade:
            grade_name = f" au grade {registration.target_grade.name}"

        title = f"Rappel : Examen demain"
        message = (
            f"Votre examen de passage{grade_name} a lieu demain "
            f"a {exam.location or 'voir les details'}. Bonne chance !"
        )

        try:
            action_url = reverse('grades:exam_detail', kwargs={'exam_id': exam.id})
        except Exception:
            action_url = f'/grades/exams/{exam.id}/'

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type='info',
            priority='important',
            action_url=action_url,
            action_text='Voir les details'
        )

        logger.debug(f"Rappel examen J-1 cree pour {user.username}")
        return notification

    except Exception as e:
        logger.error(f"Erreur creation rappel examen: {e}")
        return None


def _create_monthly_reminder_notification(user, result, days_eligible):
    """
    Cree une notification de rappel mensuel pour les eligibles non inscrits.
    """
    from apps.competitions.models.notifications import Notification

    try:
        next_grade_name = result.next_grade.get('name', 'grade suivant') if result.next_grade else 'grade suivant'

        title = f"Rappel : Vous etes eligible au grade {next_grade_name}"
        message = f"Vous etes eligible depuis {days_eligible} jours. "

        if result.available_exams:
            exam = result.available_exams[0]
            message += f"Le prochain examen a lieu le {exam.get('date_display', 'bientot')}. N'attendez plus !"
        else:
            message += "Consultez les examens disponibles."

        try:
            action_url = reverse('grades:exam_list')
        except Exception:
            action_url = '/grades/exams/'

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type='info',
            priority='standard',
            action_url=action_url,
            action_text="Voir les examens"
        )

        logger.debug(f"Rappel mensuel cree pour {user.username}")
        return notification

    except Exception as e:
        logger.error(f"Erreur creation rappel mensuel: {e}")
        return None


def _get_eligible_practitioners_for_grade(grade, discipline):
    """
    Recupere les pratiquants eligibles pour un grade donne.
    """
    from apps.grades.models import PractitionerGrade

    # Trouver le grade precedent
    previous_grade = grade.previous_grade
    if not previous_grade:
        return []

    # Trouver les pratiquants avec ce grade
    practitioner_grades = PractitionerGrade.objects.filter(
        grade=previous_grade,
        is_current=True
    ).select_related('practitioner__user')

    return [pg.practitioner for pg in practitioner_grades if pg.practitioner.user]
