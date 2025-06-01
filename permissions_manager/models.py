# permissions_manager/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class Permission(models.Model):
    """Permission individuelle atomique"""
    code = models.CharField(_("Code"), max_length=100, unique=True)
    name = models.CharField(_("Nom"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    category = models.CharField(_("Catégorie"), max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")
        ordering = ['category', 'code']

class Role(models.Model):
    """Ensemble de permissions formant un rôle"""
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True,
        verbose_name=_("Permissions")
    )
    is_system_role = models.BooleanField(_("Rôle système"), default=False,
        help_text=_("Les rôles système ne peuvent pas être modifiés par les utilisateurs"))
    context_type = models.CharField(_("Type de contexte"), max_length=50,
        choices=[
            ('global', _('Global')),
            ('federation', _('Fédération')),
            ('club', _('Club')),
            ('competition', _('Compétition')),
        ],
        default='global'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_context_type_display()})"

    class Meta:
        verbose_name = _("Rôle")
        verbose_name_plural = _("Rôles")
        ordering = ['context_type', 'name']

class UserRoleAssignment(models.Model):
    """Attribution d'un rôle à un utilisateur dans un contexte spécifique"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='assignments')

    # Champs pour le contexte générique
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    context = GenericForeignKey('content_type', 'object_id')

    # Métadonnées
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='permission_assigned_roles',  # Nom modifié
        blank=True
    )
    start_date = models.DateField(_("Date de début"), default=timezone.now)
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        context_name = str(self.context) if self.context else "Global"
        return f"{self.user.username} - {self.role.name} dans {context_name}"

    class Meta:
        verbose_name = _("Attribution de rôle")
        verbose_name_plural = _("Attributions de rôles")
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role', 'content_type', 'object_id'],
                name='unique_user_role_context'
            )
        ]