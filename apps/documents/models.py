import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

# Vérifie si l'application multi-tenant est installée
try:
    from apps.multitenant.models import TenantAwareModel  # Peut lever SyntaxError si fichier corrompu
    MULTITENANT_ENABLED = True
except Exception:  # ImportError, SyntaxError, etc.
    TenantAwareModel = models.Model
    MULTITENANT_ENABLED = False


def document_upload_path(instance, filename):
    """Définit le chemin d'upload pour les documents en fonction du tenant et de la catégorie"""
    tenant_path = f"tenant_{instance.tenant.id}/" if hasattr(instance, 'tenant') and instance.tenant else ""
    folder_path = f"{instance.folder.path}/" if instance.folder else "uncategorized/"
    # Génère un nom de fichier unique basé sur UUID
    ext = filename.split('.')[-1] if '.' in filename else ''
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('documents', tenant_path, folder_path, new_filename)


class DocumentFolder(TenantAwareModel):
    """Modèle pour la structure de dossiers du système GED"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nom du dossier"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='children', verbose_name=_("Dossier parent"))
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='document_folders_owned', verbose_name=_("Propriétaire"))
    is_public = models.BooleanField(_("Public"), default=False)
    path = models.CharField(_("Chemin"), max_length=1000, blank=True)
    
    # Champs spécifiques pour les rÃ´les
    visible_to_admins = models.BooleanField(_("Visible pour les administrateurs"), default=True)
    visible_to_federations = models.BooleanField(_("Visible pour les fédérations"), default=False)
    visible_to_clubs = models.BooleanField(_("Visible pour les clubs"), default=False)
    visible_to_practitioners = models.BooleanField(_("Visible pour les pratiquants"), default=False)
    visible_to_judges = models.BooleanField(_("Visible pour les juges"), default=False)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Dossier de documents")
        verbose_name_plural = _("Dossiers de documents")
        ordering = ['name']
        unique_together = [['name', 'parent']] if not MULTITENANT_ENABLED else [['tenant', 'name', 'parent']]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Met Ã  jour le chemin du dossier lors de la sauvegarde"""
        if self.parent:
            self.path = f"{self.parent.path}/{self.name}" if self.parent.path else self.name
        else:
            self.path = self.name
        super().save(*args, **kwargs)
        
        # Met Ã  jour le chemin des sous-dossiers
        for child in self.children.all():
            child.save()


class DocumentTag(TenantAwareModel):
    """Modèle pour les tags/étiquettes des documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nom du tag"), max_length=100)
    color = models.CharField(_("Couleur"), max_length=7, default="#cccccc", 
                           help_text=_("Code couleur hexadécimal (ex: #FF5733)"))
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Tag de document")
        verbose_name_plural = _("Tags de documents")
        ordering = ['name']
        unique_together = [['name']] if not MULTITENANT_ENABLED else [['tenant', 'name']]
    
    def __str__(self):
        return self.name


class Document(TenantAwareModel):
    """Modèle principal pour les documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("Titre"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    file = models.FileField(_("Fichier"), upload_to=document_upload_path, 
                          validators=[FileExtensionValidator(
                              allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 
                                                 'ppt', 'pptx', 'txt', 'csv', 'jpg', 
                                                 'jpeg', 'png', 'gif', 'mp4', 'zip', 'rar']
                          )])
    file_size = models.PositiveIntegerField(_("Taille du fichier (octets)"), default=0)
    mime_type = models.CharField(_("Type MIME"), max_length=255, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                 related_name='documents_created', verbose_name=_("Créé par"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, related_name='documents_modified', 
                                  verbose_name=_("Modifié par"))
    
    # Organisation
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='documents', verbose_name=_("Dossier"))
    tags = models.ManyToManyField(DocumentTag, blank=True, related_name='documents', 
                                verbose_name=_("Tags"))
    
    # Versionnement
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='versions', verbose_name=_("Version précédente"))
    version = models.PositiveIntegerField(_("Version"), default=1)
    is_latest_version = models.BooleanField(_("Version la plus récente"), default=True)
    
    # ContrÃ´le d'accès
    is_public = models.BooleanField(_("Public"), default=False)
    is_template = models.BooleanField(_("Modèle"), default=False)
    expiry_date = models.DateTimeField(_("Date d'expiration"), null=True, blank=True)
    
    # Liaison générique pour associer un document Ã  n'importe quel modèle
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, 
                                   null=True, blank=True, 
                                   verbose_name=_("Type de contenu associé"))
    object_id = models.CharField(_("ID de l'objet associé"), max_length=255, blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Métadonnées additionnelles (JSON)
    metadata = models.JSONField(_("Métadonnées"), default=dict, blank=True)
    
    # Spécifique aux arts martiaux
    document_type = models.CharField(_("Type de document"), max_length=50, blank=True, choices=[
        ('certificate', _("Certificat")),
        ('diploma', _("DiplÃ´me")),
        ('license', _("Licence")),
        ('medical', _("Certificat médical")),
        ('competition', _("Document de compétition")),
        ('training', _("Document d'entraÃ®nement")),
        ('technical', _("Document technique")),
        ('administrative', _("Document administratif")),
        ('other', _("Autre")),
    ])
    
    # Statistiques
    view_count = models.PositiveIntegerField(_("Nombre de vues"), default=0)
    download_count = models.PositiveIntegerField(_("Nombre de téléchargements"), default=0)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-created_at']
        permissions = [
            ("can_view_document", _("Peut voir le document")),
            ("can_download_document", _("Peut télécharger le document")),
            ("can_share_document", _("Peut partager le document")),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        """Mise Ã  jour automatique des métadonnées lors de la sauvegarde"""
        # Si c'est un nouveau document
        if self._state.adding:
            # Si le fichier existe déjÃ , récupérer sa taille
            if self.file:
                self.file_size = self.file.size
                
                # Déterminer le type MIME basé sur l'extension
                filename = self.file.name
                extension = filename.split('.')[-1].lower() if '.' in filename else ''
                mime_map = {
                    'pdf': 'application/pdf',
                    'doc': 'application/msword',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'xls': 'application/vnd.ms-excel',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'ppt': 'application/vnd.ms-powerpoint',
                    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'txt': 'text/plain',
                    'csv': 'text/csv',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'mp4': 'video/mp4',
                    'zip': 'application/zip',
                    'rar': 'application/x-rar-compressed',
                }
                self.mime_type = mime_map.get(extension, 'application/octet-stream')
        
        # Si c'est une nouvelle version d'un document existant
        if self.parent:
            # Marquer l'ancienne version comme n'étant plus la plus récente
            if self.parent.is_latest_version:
                self.parent.is_latest_version = False
                self.parent.save(update_fields=['is_latest_version'])
            
            # Incrémenter le numéro de version
            self.version = self.parent.version + 1
        
        super().save(*args, **kwargs)


class DocumentShare(TenantAwareModel):
    """Modèle pour le partage de documents entre utilisateurs et groupes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, 
                               related_name='shares', verbose_name=_("Document"))
    
    # Partagé avec un utilisateur spécifique
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           null=True, blank=True, related_name='document_shares_received', 
                           verbose_name=_("Utilisateur"))
    
    # Ou avec un groupe d'utilisateurs via un ContentType générique
    # Cela permet de partager avec des clubs, fédérations, etc.
    group_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                         null=True, blank=True, 
                                         related_name='document_shares', 
                                         verbose_name=_("Type de groupe"))
    group_object_id = models.CharField(_("ID du groupe"), max_length=255, null=True, blank=True)
    group_object = GenericForeignKey('group_content_type', 'group_object_id')
    
    # Niveau d'accès
    ACCESS_READ = 'R'
    ACCESS_WRITE = 'W'
    ACCESS_FULL = 'F'
    
    ACCESS_CHOICES = [
        (ACCESS_READ, _("Lecture")),
        (ACCESS_WRITE, _("Ã‰criture")),
        (ACCESS_FULL, _("ContrÃ´le total")),
    ]
    
    access_level = models.CharField(_("Niveau d'accès"), max_length=1, 
                                  choices=ACCESS_CHOICES, default=ACCESS_READ)
    
    # Période de validité
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expire le"), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                 related_name='document_shares_created', verbose_name=_("Créé par"))
    
    # Notification
    notify_on_access = models.BooleanField(_("Notifier lors de l'accès"), default=False)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Partage de document")
        verbose_name_plural = _("Partages de documents")
        ordering = ['-created_at']
        constraints = [
            # Assurer qu'un document est partagé soit avec un utilisateur, soit avec un groupe
            models.CheckConstraint(
                check=models.Q(user__isnull=False, group_object_id__isnull=True) | 
                      models.Q(user__isnull=True, group_object_id__isnull=False),
                name='share_user_or_group_not_both'
            )
        ]
    
    def __str__(self):
        if self.user:
            shared_with = self.user.get_full_name() or self.user.username
        elif self.group_object:
            shared_with = str(self.group_object)
        else:
            shared_with = _("Inconnu")
        
        return f"{self.document.title} â†’ {shared_with} ({self.get_access_level_display()})"


class DocumentAccessLog(TenantAwareModel):
    """Journal d'accès aux documents pour l'audit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, 
                               related_name='access_logs', verbose_name=_("Document"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                           null=True, related_name='documents_access_logs', 
                           verbose_name=_("Utilisateur"))
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)
    
    # Type d'action
    ACTION_VIEW = 'view'
    ACTION_DOWNLOAD = 'download'
    ACTION_EDIT = 'edit'
    ACTION_SHARE = 'share'
    ACTION_DELETE = 'delete'
    
    ACTION_CHOICES = [
        (ACTION_VIEW, _("Consultation")),
        (ACTION_DOWNLOAD, _("Téléchargement")),
        (ACTION_EDIT, _("Modification")),
        (ACTION_SHARE, _("Partage")),
        (ACTION_DELETE, _("Suppression")),
    ]
    
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    
    # Informations supplémentaires
    ip_address = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    details = models.JSONField(_("Détails"), default=dict, blank=True)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Journal d'accès aux documents")
        verbose_name_plural = _("Journal d'accès aux documents")
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.get_full_name() if self.user else _("Utilisateur supprimé")
        return f"{user_str} - {self.get_action_display()} - {self.document.title} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"


class DocumentComment(TenantAwareModel):
    """Commentaires sur les documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, 
                               related_name='comments', verbose_name=_("Document"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                             related_name='documents_comments', verbose_name=_("Auteur"))
    content = models.TextField(_("Contenu"))
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    
    # Pour les fils de discussion
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='replies', verbose_name=_("Commentaire parent"))
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.get_full_name()} sur {self.document.title}"


# Modèles spécifiques aux arts martiaux pour la GED

class TechnicalDocumentMetadata(models.Model):
    """Métadonnées spécifiques pour les documents techniques des arts martiaux"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, 
                                  related_name='technical_metadata', 
                                  verbose_name=_("Document"))
    
    # Discipline associée
    discipline = models.ForeignKey('competitions.Discipline', on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='technical_documents', 
                                 verbose_name=_("Discipline"))
    
    # Niveau technique
    LEVEL_CHOICES = [
        ('beginner', _("Débutant")),
        ('intermediate', _("Intermédiaire")),
        ('advanced', _("Avancé")),
        ('expert', _("Expert")),
        ('master', _("MaÃ®tre")),
    ]
    level = models.CharField(_("Niveau"), max_length=20, choices=LEVEL_CHOICES, blank=True)
    
    # Type de contenu technique
    CONTENT_TYPE_CHOICES = [
        ('kata', _("Kata/Forme")),
        ('technique', _("Technique")),
        ('drill', _("Exercice")),
        ('theory', _("Théorie")),
        ('exam', _("Examen")),
        ('syllabus', _("Programme technique")),
    ]
    content_type = models.CharField(_("Type de contenu"), max_length=20, 
                                  choices=CONTENT_TYPE_CHOICES, blank=True)
    
    # Métadonnées spécifiques
    requirements = models.TextField(_("Prérequis"), blank=True)
    keywords = models.CharField(_("Mots-clés"), max_length=500, blank=True, 
                              help_text=_("Mots-clés séparés par des virgules"))
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Métadonnées de document technique")
        verbose_name_plural = _("Métadonnées de documents techniques")
    
    def __str__(self):
        return f"Métadonnées techniques pour {self.document.title}"


class GradeDocumentMetadata(models.Model):
    """Métadonnées spécifiques pour les documents liés aux grades"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, 
                                  related_name='grade_metadata', 
                                  verbose_name=_("Document"))
    
    # Grade associé
    grade = models.ForeignKey('grades.Grade', on_delete=models.SET_NULL, 
                            null=True, blank=True, related_name='documents', 
                            verbose_name=_("Grade"))
    
    # Type de document de grade
    TYPE_CHOICES = [
        ('certificate', _("Certificat de grade")),
        ('requirements', _("Exigences de passage")),
        ('exam_form', _("Formulaire d'examen")),
        ('theory', _("Support théorique")),
        ('jury_guidelines', _("Guide pour le jury")),
    ]
    document_type = models.CharField(_("Type de document de grade"), max_length=20, 
                                   choices=TYPE_CHOICES)
    
    # Date de validité pour les certificats
    valid_from = models.DateField(_("Valide Ã  partir du"), null=True, blank=True)
    valid_until = models.DateField(_("Valide jusqu'au"), null=True, blank=True)
    
    # Autorité de délivrance
    issuing_authority = models.CharField(_("Autorité de délivrance"), max_length=255, blank=True)
    authorized_by = models.CharField(_("Autorisé par"), max_length=255, blank=True)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Métadonnées de document de grade")
        verbose_name_plural = _("Métadonnées de documents de grade")
    
    def __str__(self):
        return f"Métadonnées de grade pour {self.document.title}"


class CompetitionDocumentMetadata(models.Model):
    """Métadonnées spécifiques pour les documents liés aux compétitions"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, 
                                  related_name='competition_metadata', 
                                  verbose_name=_("Document"))
    
    # Compétition associée
    competition = models.ForeignKey('competitions.Competition', on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='documents', 
                                  verbose_name=_("Compétition"))
    
    # Type de document de compétition
    TYPE_CHOICES = [
        ('rules', _("Règlement")),
        ('schedule', _("Planning")),
        ('registration', _("Inscription")),
        ('drawing', _("Tirage au sort")),
        ('results', _("Résultats")),
        ('report', _("Rapport")),
        ('certificate', _("Certificat/DiplÃ´me")),
    ]
    document_type = models.CharField(_("Type de document de compétition"), max_length=20, 
                                   choices=TYPE_CHOICES)
    
    # Catégorie associée
    category = models.ForeignKey('competitions.CompetitionCategory', on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='documents', 
                               verbose_name=_("Catégorie"))
    
    # Date de l'événement
    event_date = models.DateField(_("Date de l'événement"), null=True, blank=True)
    
    class Meta:
        app_label = 'documents'
        verbose_name = _("Métadonnées de document de compétition")
        verbose_name_plural = _("Métadonnées de documents de compétition")
    
    def __str__(self):
        return f"Métadonnées de compétition pour {self.document.title}"


class GoogleDriveToken(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='gdrive_token')
    token_json = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Google Drive Token for {self.user}"


