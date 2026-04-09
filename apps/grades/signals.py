# -*- coding: utf-8 -*-
"""
Signaux pour l'application grades.
Gère les mises à jour automatiques des grades des pratiquants.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Imports absolus pour éviter les conflits
from apps.competitions.models import Practitioner
from apps.grades.models import PractitionerGrade, Grade, GradeExamRegistration


@receiver(post_save, sender=PractitionerGrade)
def update_practitioner_grade(sender, instance, created, **kwargs):
    """
    Met à jour le grade affiché sur le profil du pratiquant lorsqu'un nouveau grade lui est attribué.
    """
    if instance.is_current:
        # Mettre à jour le champ grade du pratiquant si ce grade est le grade actuel
        practitioner = instance.practitioner
        # Le champ grade du pratitioner est une ForeignKey vers Grade
        practitioner.grade = instance.grade
        practitioner.save(update_fields=['grade'])


@receiver(post_delete, sender=PractitionerGrade)
def handle_deleted_grade(sender, instance, **kwargs):
    """
    Met à jour le grade du pratiquant lorsqu'un grade est supprimé.
    Si le grade supprimé était le grade actuel, on attribue le grade précédent.
    """
    if instance.is_current:
        practitioner = instance.practitioner
        discipline = instance.discipline
        
        # Chercher le grade le plus récent pour cette discipline
        latest_grade = PractitionerGrade.objects.filter(
            practitioner=practitioner,
            discipline=discipline
        ).exclude(pk=instance.pk).order_by('-date_obtained').first()
        
        if latest_grade:
            # Définir ce grade comme le grade actuel
            latest_grade.is_current = True
            latest_grade.save()
            
            # Mettre à jour le grade affiché sur le profil du pratiquant
            practitioner.grade = latest_grade.grade
            practitioner.save(update_fields=['grade'])
        else:
            # Si aucun autre grade n'existe pour cette discipline, effacer le grade affiché
            practitioner.grade = None
            practitioner.save(update_fields=['grade'])


@receiver(post_save, sender=GradeExamRegistration)
def handle_exam_registration_status_change(sender, instance, created, **kwargs):
    """
    Gère les changements de statut d'inscription à un examen.
    Si le statut passe à 'passed', attribue automatiquement le grade au pratiquant.
    """
    if not created and instance.status == 'passed' and not instance.certificate_issued:
        # Vérifier si le grade n'a pas déjà été attribué
        grade_exists = PractitionerGrade.objects.filter(
            practitioner=instance.practitioner,
            grade=instance.target_grade,
            date_obtained=timezone.now().date()
        ).exists()
        
        if not grade_exists:
            # Créer le grade pour le pratiquant
            PractitionerGrade.objects.create(
                practitioner=instance.practitioner,
                grade=instance.target_grade,
                discipline=instance.target_grade.discipline,
                date_obtained=timezone.now().date(),
                awarded_by=instance.exam.examiners,
                location=instance.exam.location,
                certificate_number=instance.certificate_number,
                is_current=True
            )
            
            # Désactiver les autres grades courants pour cette discipline
            PractitionerGrade.objects.filter(
                practitioner=instance.practitioner,
                discipline=instance.target_grade.discipline,
                is_current=True
            ).exclude(grade=instance.target_grade).update(is_current=False)
            
            # Mettre à jour le statut du certificat
            instance.certificate_issued = True
            instance.save(update_fields=['certificate_issued'])


# ===== INVALIDATION DU CACHE D'ELIGIBILITE (Grade Tracking - Prompt 5) =====

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=PractitionerGrade)
def invalidate_eligibility_cache_on_grade_save(sender, instance, created, **kwargs):
    """
    Invalide le cache d'eligibilite lors de l'ajout/modification d'un grade.
    """
    try:
        from apps.competitions.services.grade_eligibility import GradeEligibilityService
        GradeEligibilityService.invalidate_cache(
            practitioner_id=instance.practitioner_id,
            discipline_id=instance.discipline_id
        )
        logger.debug(f"Cache eligibilite invalide pour practitioner {instance.practitioner_id}")
    except ImportError:
        pass  # Service pas encore disponible
    except Exception as e:
        logger.error(f"Erreur invalidation cache eligibilite (save): {e}")


@receiver(post_delete, sender=PractitionerGrade)
def invalidate_eligibility_cache_on_grade_delete(sender, instance, **kwargs):
    """
    Invalide le cache d'eligibilite lors de la suppression d'un grade.
    """
    try:
        from apps.competitions.services.grade_eligibility import GradeEligibilityService
        GradeEligibilityService.invalidate_cache(
            practitioner_id=instance.practitioner_id,
            discipline_id=instance.discipline_id
        )
        logger.debug(f"Cache eligibilite invalide apres suppression pour practitioner {instance.practitioner_id}")
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Erreur invalidation cache eligibilite (delete): {e}")


@receiver(post_save, sender=GradeExamRegistration)
def invalidate_eligibility_cache_on_exam_result(sender, instance, created, **kwargs):
    """
    Invalide le cache lors du resultat d'un examen (reussi ou echoue).
    """
    if not created and instance.status in ['passed', 'failed']:
        try:
            from apps.competitions.services.grade_eligibility import GradeEligibilityService
            GradeEligibilityService.invalidate_cache(
                practitioner_id=instance.practitioner_id,
                discipline_id=instance.target_grade.discipline_id if instance.target_grade else None
            )
            logger.debug(f"Cache eligibilite invalide apres examen pour practitioner {instance.practitioner_id}")
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Erreur invalidation cache eligibilite (exam): {e}")


# ===== NOTIFICATIONS DE GRADE (Prompt 2) =====

from apps.grades.models import GradeExam


@receiver(post_save, sender=GradeExam)
def notify_eligible_practitioners_new_exam(sender, instance, created, **kwargs):
    """
    Notifie les pratiquants eligibles lors de la creation d'un nouvel examen.
    """
    if not created or instance.status != 'scheduled':
        return

    try:
        from apps.competitions.models.notifications import Notification, NotificationPreference
        from apps.competitions.services.grade_eligibility import GradeEligibilityService
        from django.urls import reverse

        notifications_created = 0

        # Pour chaque grade disponible a l'examen
        for grade in instance.available_grades.all():
            # Trouver le grade precedent
            previous_grade = grade.previous_grade
            if not previous_grade:
                continue

            # Trouver les pratiquants avec ce grade
            practitioner_grades = PractitionerGrade.objects.filter(
                grade=previous_grade,
                is_current=True
            ).select_related('practitioner__user')

            for pg in practitioner_grades:
                if not pg.practitioner.user:
                    continue

                # Verifier les preferences
                prefs, _ = NotificationPreference.objects.get_or_create(
                    user=pg.practitioner.user,
                    defaults={'grade_notifications': True}
                )

                if not prefs.grade_notifications:
                    continue

                # Verifier eligibilite
                result = GradeEligibilityService.check_eligibility(
                    pg.practitioner, instance.discipline
                )

                if not result.is_eligible:
                    continue

                # Creer la notification
                try:
                    action_url = reverse('grades:exam_register', kwargs={'exam_id': instance.id})
                except Exception:
                    action_url = f'/grades/exams/{instance.id}/register/'

                Notification.objects.create(
                    user=pg.practitioner.user,
                    title=f"Nouvel examen de grade disponible",
                    message=(
                        f"Un examen pour le grade {grade.name} est programme le "
                        f"{instance.date.strftime('%d/%m/%Y')} a {instance.location or 'voir details'}. "
                        f"Inscriptions ouvertes jusqu'au {instance.registration_deadline.strftime('%d/%m/%Y')}."
                    ),
                    notification_type='info',
                    priority='standard',
                    action_url=action_url,
                    action_text="S'inscrire"
                )
                notifications_created += 1

        if notifications_created > 0:
            logger.info(f"{notifications_created} notifications creees pour nouvel examen {instance.id}")

    except Exception as e:
        logger.error(f"Erreur notification nouvel examen: {e}")


@receiver(post_save, sender=GradeExamRegistration)
def notify_exam_result(sender, instance, created, **kwargs):
    """
    Notifie le pratiquant du resultat de son examen.
    """
    if created:
        return

    # Seulement lors d'un changement vers passed ou failed
    if instance.status not in ['passed', 'failed']:
        return

    try:
        from apps.competitions.models.notifications import Notification, NotificationPreference
        from django.urls import reverse

        user = instance.practitioner.user
        if not user:
            return

        # Verifier preferences
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={'grade_notifications': True}
        )

        if not prefs.grade_notifications:
            return

        grade_name = instance.target_grade.name if instance.target_grade else "grade"

        if instance.status == 'passed':
            title = f"Felicitations ! Grade {grade_name} obtenu"
            message = (
                f"Vous avez reussi votre examen de passage au grade {grade_name}. "
                f"Votre nouveau grade a ete enregistre dans votre profil."
            )
            notification_type = 'success'
            priority = 'important'
            action_text = "Voir mon profil"
            try:
                action_url = reverse('competitions:dashboard:participant')
            except Exception:
                action_url = '/competitions/dashboard/participant/'

        else:  # failed
            title = f"Resultat examen de grade"
            message = (
                f"Vous n'avez pas obtenu le grade {grade_name} cette fois-ci. "
                f"Continuez vos efforts !"
            )
            notification_type = 'info'
            priority = 'standard'
            action_text = "Voir les prochains examens"
            try:
                action_url = reverse('grades:exam_list')
            except Exception:
                action_url = '/grades/exams/'

        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text=action_text
        )

        logger.info(f"Notification resultat examen creee pour {user.username}: {instance.status}")

    except Exception as e:
        logger.error(f"Erreur notification resultat examen: {e}")


@receiver(post_save, sender=PractitionerGrade)
def notify_grade_obtained(sender, instance, created, **kwargs):
    """
    Notification lors de l'obtention d'un nouveau grade.
    """
    if not created:
        return

    try:
        from apps.competitions.models.notifications import Notification, NotificationPreference
        from django.urls import reverse

        user = instance.practitioner.user
        if not user:
            return

        # Verifier preferences
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={'grade_notifications': True}
        )

        if not prefs.grade_notifications:
            return

        grade_name = instance.grade.name

        try:
            action_url = reverse('competitions:dashboard:participant')
        except Exception:
            action_url = '/competitions/dashboard/participant/'

        Notification.objects.create(
            user=user,
            title=f"Nouveau grade enregistre : {grade_name}",
            message=(
                f"Votre grade {grade_name} a ete enregistre dans votre profil. "
                f"Felicitations pour votre progression !"
            ),
            notification_type='success',
            priority='important',
            action_url=action_url,
            action_text="Voir ma progression"
        )

        logger.info(f"Notification nouveau grade creee pour {user.username}: {grade_name}")

    except Exception as e:
        logger.error(f"Erreur notification nouveau grade: {e}")