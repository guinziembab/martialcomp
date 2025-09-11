from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from competitions.models import Practitioner
from .models import PractitionerGrade, Grade, GradeExamRegistration


@receiver(post_save, sender=PractitionerGrade)
def update_practitioner_grade(sender, instance, created, **kwargs):
    """Met à jour le grade affiché sur le profil du pratiquant lorsqu'un nouveau grade lui est attribué."""
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
            latest_grade.is_current = bool(True)
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
        from django.utils import timezone
        
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
                is_current=bool(True)
            )
            
            # Désactiver les autres grades courants pour cette discipline
            PractitionerGrade.objects.filter(
                practitioner=instance.practitioner,
                discipline=instance.target_grade.discipline,
                is_current=bool(True)
            ).exclude(grade=instance.target_grade).update(is_current=bool(False))
            
            # Mettre à jour le statut du certificat
            instance.certificate_issued = bool(True)
            instance.save(update_fields=['certificate_issued'])