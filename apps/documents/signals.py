from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

from .models import Document, DocumentAccessLog, DocumentShare, DocumentFolder

User = get_user_model()


@receiver(pre_save, sender=Document)
def update_document_metadata(sender, instance, **kwargs):
    """Met Ã  jour les métadonnées du document avant sauvegarde"""
    # Mise Ã  jour de la taille du fichier si un nouveau fichier est uploadé
    if instance.file and hasattr(instance.file, 'size'):
        instance.file_size = instance.file.size


@receiver(post_save, sender=Document)
def log_document_creation(sender, instance, created, **kwargs):
    """Enregistre la création d'un document dans le journal d'accès"""
    if created and instance.created_by:
        DocumentAccessLog.objects.create(
            document=instance,
            user=instance.created_by,
            action=DocumentAccessLog.ACTION_EDIT,
            details={
                'action_details': str(_("Création du document")),
                'document_title': instance.title,
                'document_type': instance.document_type,
            }
        )


@receiver(post_save, sender=DocumentShare)
def log_document_share(sender, instance, created, **kwargs):
    """Enregistre le partage d'un document dans le journal d'accès"""
    if created and instance.created_by:
        # Déterminer avec qui le document a été partagé
        if instance.user:
            shared_with = f"User: {instance.user.get_full_name() or instance.user.username}"
        elif instance.group_object:
            shared_with = f"Group: {instance.group_content_type.model}: {instance.group_object}"
        else:
            shared_with = str(_("Inconnu"))

        DocumentAccessLog.objects.create(
            document=instance.document,
            user=instance.created_by,
            action=DocumentAccessLog.ACTION_SHARE,
            details={
                'action_details': str(_("Partage du document")),
                'shared_with': shared_with,
                'access_level': str(instance.get_access_level_display()),
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
            }
        )


@receiver(post_delete, sender=Document)
def delete_document_file(sender, instance, **kwargs):
    """Supprime le fichier associé au document lorsque celui-ci est supprimé"""
    if instance.file:
        # Vérifier si le fichier n'est pas utilisé par d'autres versions du document
        if not Document.objects.filter(file=instance.file.name).exclude(pk=instance.pk).exists():
            # Le fichier n'est pas utilisé ailleurs, on peut le supprimer
            default_storage.delete(instance.file.name)


@receiver(post_delete, sender=Document)
def log_document_deletion(sender, instance, **kwargs):
    """Enregistre la suppression d'un document dans le journal d'accès"""
    # Essayer de récupérer l'utilisateur qui a effectué la suppression
    # Note: c'est une approche imparfaite car post_delete ne fournit pas cette info directement
    from django.contrib.admin.models import LogEntry, DELETION
    from django.contrib.contenttypes.models import ContentType
    
    try:
        log_entry = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(sender),
            object_id=str(instance.pk),
            action_flag=DELETION
        ).order_by('-action_time').first()
        
        user = log_entry.user if log_entry else None
    except:
        user = None
    
    DocumentAccessLog.objects.create(
        document=instance,
        user=user,
        action=DocumentAccessLog.ACTION_DELETE,
        details={
            'action_details': str(_("Suppression du document")),
            'document_title': instance.title,
            'document_type': instance.document_type,
        }
    )


@receiver(post_save, sender=DocumentFolder)
def update_children_paths(sender, instance, **kwargs):
    """Met Ã  jour les chemins des sous-dossiers lorsqu'un dossier est modifié"""
    # Cette logique est maintenant dans la méthode save() du modèle DocumentFolder
    pass
