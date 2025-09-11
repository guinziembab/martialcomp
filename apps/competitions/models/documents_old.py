from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid
import os


class DocumentCategory(models.Model):
    """Catégorie de documents."""
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='document_categories',
        verbose_name=_("Organisation")
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_("Catégorie parente")
    )
    
    icon = models.CharField(_("IcÃ´ne"), max_length=50, default='fa-folder')
    color = models.CharField(_("Couleur"), max_length=7, default='#007bff')
    
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Catégorie de documents")
        verbose_name_plural = _("Catégories de documents")
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Document(models.Model):
    """Document partagé."""
    
    VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('members', _('Membres uniquement')),
        ('staff', _('Staff uniquement')),
        ('private', _('Privé')),
    ]
    
    FILE_TYPE_CHOICES = [
        ('document', _('Document')),
        ('form', _('Formulaire')),
        ('regulation', _('Règlement')),
        ('guide', _('Guide')),
        ('template', _('Modèle')),
        ('other', _('Autre')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_("Catégorie")
    )
    
    file_type = models.CharField(_("Type"), max_length=20, choices=FILE_TYPE_CHOICES, default='document')
    
    # Fichier
    file = models.FileField(
        _("Fichier"),
        upload_to='documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'txt', 'odt', 'ods', 'odp', 'jpg', 'jpeg', 'png', 'gif'
        ])]
    )
    
    file_size = models.PositiveIntegerField(_("Taille (octets)"), editable=False)
    file_extension = models.CharField(_("Extension"), max_length=10, editable=False)
    mime_type = models.CharField(_("Type MIME"), max_length=100, blank=True)
    
    # Métadonnées
    visibility = models.CharField(_("Visibilité"), max_length=20, choices=VISIBILITY_CHOICES, default='members')
    
    # Organisation ou utilisateur propriétaire
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_("Organisation")
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_documents',
        verbose_name=_("Propriétaire")
    )
    
    # Permissions
    can_download = models.BooleanField(_("Téléchargement autorisé"), default=True)
    requires_acceptance = models.BooleanField(_("Acceptation requise"), default=False)
    
    # Tags
    tags = models.CharField(_("Tags"), max_length=200, blank=True, help_text=_("Séparés par des virgules"))
    
    # Versioning
    version = models.CharField(_("Version"), max_length=20, default='1.0')
    is_latest = models.BooleanField(_("Dernière version"), default=True)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        verbose_name=_("Version précédente")
    )
    
    # Statistiques
    download_count = models.PositiveIntegerField(_("Nombre de téléchargements"), default=0)
    view_count = models.PositiveIntegerField(_("Nombre de vues"), default=0)
    
    # Dates
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name=_("Uploadé par")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        # Calculer la taille et l'extension
        if self.file:
            self.file_size = self.file.size
            self.file_extension = os.path.splitext(self.file.name)[1][1:].lower()
        
        super().save(*args, **kwargs)
    
    @property
    def file_size_human(self):
        """Retourne la taille du fichier dans un format lisible."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def can_access(self, user):
        """Vérifie si un utilisateur peut accéder au document."""
        if self.visibility == 'public':
            return True
        elif self.visibility == 'members' and user.is_authenticated:
            # Vérifier si l'utilisateur est membre de l'organisation
            if self.organization:
                return user.practitioners.filter(organization=self.organization).exists()
            return True
        elif self.visibility == 'staff':
            return user.is_staff
        elif self.visibility == 'private':
            return user == self.owner
        return False


class DocumentAccess(models.Model):
    """Suivi des accès aux documents."""
    
    ACTION_CHOICES = [
        ('view', _('Vue')),
        ('download', _('Téléchargement')),
        ('share', _('Partage')),
    ]
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name=_("Document")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Utilisateur")
    )
    
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    
    ip_address = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    accessed_at = models.DateTimeField(_("Accédé le"), auto_now_add=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Accès au document")
        verbose_name_plural = _("Accès aux documents")
        ordering = ['-accessed_at']


class DocumentShare(models.Model):
    """Partage d'un document avec des utilisateurs spécifiques."""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_("Document")
    )
    
    shared_with = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_documents',
        verbose_name=_("Partagé avec")
    )
    
    shared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_shared',
        verbose_name=_("Partagé par")
    )
    
    can_download = models.BooleanField(_("Peut télécharger"), default=True)
    can_share = models.BooleanField(_("Peut partager"), default=False)
    
    expires_at = models.DateTimeField(_("Expire le"), null=True, blank=True)
    
    message = models.TextField(_("Message"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Partage de document")
        verbose_name_plural = _("Partages de documents")
        unique_together = [['document', 'shared_with']]
    
    @property
    def is_expired(self):
        """Vérifie si le partage a expiré."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DocumentAcceptance(models.Model):
    """Acceptation des documents (pour les règlements, etc.)."""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='acceptances',
        verbose_name=_("Document")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accepted_documents',
        verbose_name=_("Utilisateur")
    )
    
    accepted_at = models.DateTimeField(_("Accepté le"), auto_now_add=True)
    
    ip_address = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    # Signature électronique
    signature = models.TextField(_("Signature"), blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Acceptation de document")
        verbose_name_plural = _("Acceptations de documents")
        unique_together = [['document', 'user']]
        ordering = ['-accepted_at']

