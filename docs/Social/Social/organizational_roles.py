# competitions/models/organizational_roles.py
"""
Modèles pour la gestion des rôles organisationnels dans MartialComp.
Ce module gère les rôles au niveau Club et Fédération.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class OrganizationalRole(models.Model):
    """
    Définition des rôles organisationnels disponibles.
    Extensible par chaque organisation.
    """
    ROLE_CATEGORIES = [
        ('executive', _('Direction')),
        ('administrative', _('Administration')),
        ('financial', _('Finance')),
        ('technical', _('Technique')),
        ('operational', _('Opérationnel')),
    ]
    
    code = models.CharField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Nom"), max_length=100)
    name_en = models.CharField(_("Name (EN)"), max_length=100, blank=True)
    category = models.CharField(_("Catégorie"), max_length=20, choices=ROLE_CATEGORIES)
    description = models.TextField(_("Description"), blank=True)
    
    # Permissions par défaut (JSON)
    default_permissions = models.JSONField(_("Permissions par défaut"), default=dict)
    
    # Hiérarchie (plus bas = plus de pouvoir)
    hierarchy_level = models.PositiveSmallIntegerField(_("Niveau hiérarchique"), default=10)
    
    # Icône pour l'interface
    icon = models.CharField(_("Icône FontAwesome"), max_length=50, default="fa-user")
    color = models.CharField(_("Couleur"), max_length=20, default="#6c757d")
    
    # Actif
    is_active = models.BooleanField(_("Actif"), default=True)
    is_system = models.BooleanField(_("Rôle système"), default=False)  # Non modifiable/supprimable
    
    class Meta:
        verbose_name = _("Rôle organisationnel")
        verbose_name_plural = _("Rôles organisationnels")
        ordering = ['hierarchy_level', 'name']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_default_roles(cls):
        """Retourne les rôles par défaut du système."""
        return cls.objects.filter(is_system=True)
    
    @classmethod
    def get_role_by_code(cls, code):
        """Retourne un rôle par son code."""
        try:
            return cls.objects.get(code=code)
        except cls.DoesNotExist:
            return None


class ClubMember(models.Model):
    """
    Appartenance d'un utilisateur à un club avec rôle(s) organisationnel(s).
    Remplace/étend ClubAdministrator pour une gestion unifiée.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('active', _('Actif')),
        ('suspended', _('Suspendu')),
        ('inactive', _('Inactif')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='club_memberships',
        verbose_name=_("Utilisateur")
    )
    club = models.ForeignKey(
        'Club',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_("Club")
    )
    
    # Rôle principal dans le club
    role = models.ForeignKey(
        OrganizationalRole,
        on_delete=models.SET_NULL,
        null=True,
        related_name='club_members',
        verbose_name=_("Rôle principal")
    )
    
    # Rôles additionnels (un trésorier peut aussi être entraîneur)
    additional_roles = models.ManyToManyField(
        OrganizationalRole,
        blank=True,
        related_name='additional_club_members',
        verbose_name=_("Rôles additionnels")
    )
    
    # Permissions personnalisées (override les permissions du rôle)
    custom_permissions = models.JSONField(
        _("Permissions personnalisées"),
        default=dict,
        blank=True,
        help_text=_("Format: {'grant': ['perm1'], 'revoke': ['perm2']}")
    )
    
    # Statut
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    
    # Dates
    joined_at = models.DateTimeField(_("Membre depuis"), auto_now_add=True)
    role_assigned_at = models.DateTimeField(_("Rôle assigné le"), null=True, blank=True)
    
    # Qui a assigné le rôle
    role_assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made',
        verbose_name=_("Assigné par")
    )
    
    # Notes internes
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Membre de club")
        verbose_name_plural = _("Membres de club")
        unique_together = ('user', 'club')
        ordering = ['-joined_at']
    
    def __str__(self):
        role_name = self.role.name if self.role else _("Membre")
        return f"{self.user.get_full_name() or self.user.username} - {role_name} @ {self.club.name}"
    
    @property
    def all_roles(self):
        """Retourne tous les rôles (principal + additionnels)."""
        roles = []
        if self.role:
            roles.append(self.role)
        roles.extend(list(self.additional_roles.all()))
        return roles
    
    @property
    def effective_permissions(self):
        """
        Calcule les permissions effectives:
        1. Permissions du rôle principal
        2. + Permissions des rôles additionnels
        3. + Permissions personnalisées (override)
        """
        permissions = set()
        
        # Permissions du rôle principal
        if self.role and self.role.default_permissions:
            perms = self.role.default_permissions.get('permissions', [])
            permissions.update(perms)
        
        # Permissions des rôles additionnels
        for role in self.additional_roles.all():
            if role.default_permissions:
                perms = role.default_permissions.get('permissions', [])
                permissions.update(perms)
        
        # Permissions personnalisées
        if self.custom_permissions:
            # Ajouter les permissions accordées
            permissions.update(self.custom_permissions.get('grant', []))
            # Retirer les permissions révoquées
            for perm in self.custom_permissions.get('revoke', []):
                permissions.discard(perm)
        
        return permissions
    
    def has_permission(self, permission):
        """Vérifie si le membre a une permission spécifique."""
        perms = self.effective_permissions
        # Wildcard pour propriétaire
        if '*' in perms:
            return True
        return permission in perms
    
    def has_any_permission(self, *permissions):
        """Vérifie si le membre a au moins une des permissions."""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, *permissions):
        """Vérifie si le membre a toutes les permissions."""
        return all(self.has_permission(p) for p in permissions)
    
    def assign_role(self, role, assigned_by=None):
        """Assigne un nouveau rôle principal."""
        old_role = self.role
        self.role = role
        self.role_assigned_at = timezone.now()
        self.role_assigned_by = assigned_by
        self.save()
        
        # Logger l'action
        MemberRoleHistory.objects.create(
            member=self,
            action='role_assigned',
            role=role,
            old_role=old_role,
            performed_by=assigned_by
        )
    
    def add_additional_role(self, role, assigned_by=None):
        """Ajoute un rôle additionnel."""
        if role not in self.additional_roles.all():
            self.additional_roles.add(role)
            
            MemberRoleHistory.objects.create(
                member=self,
                action='additional_role_added',
                role=role,
                performed_by=assigned_by
            )
    
    def remove_additional_role(self, role, removed_by=None):
        """Retire un rôle additionnel."""
        if role in self.additional_roles.all():
            self.additional_roles.remove(role)
            
            MemberRoleHistory.objects.create(
                member=self,
                action='additional_role_removed',
                role=role,
                performed_by=removed_by
            )
    
    def grant_permission(self, permission, granted_by=None):
        """Accorde une permission personnalisée."""
        if not self.custom_permissions:
            self.custom_permissions = {'grant': [], 'revoke': []}
        
        if permission not in self.custom_permissions.get('grant', []):
            self.custom_permissions.setdefault('grant', []).append(permission)
            # Retirer de revoke si présent
            if permission in self.custom_permissions.get('revoke', []):
                self.custom_permissions['revoke'].remove(permission)
            self.save()
            
            MemberRoleHistory.objects.create(
                member=self,
                action='permissions_modified',
                notes=f"Permission accordée: {permission}",
                performed_by=granted_by
            )
    
    def revoke_permission(self, permission, revoked_by=None):
        """Révoque une permission."""
        if not self.custom_permissions:
            self.custom_permissions = {'grant': [], 'revoke': []}
        
        if permission not in self.custom_permissions.get('revoke', []):
            self.custom_permissions.setdefault('revoke', []).append(permission)
            # Retirer de grant si présent
            if permission in self.custom_permissions.get('grant', []):
                self.custom_permissions['grant'].remove(permission)
            self.save()
            
            MemberRoleHistory.objects.create(
                member=self,
                action='permissions_modified',
                notes=f"Permission révoquée: {permission}",
                performed_by=revoked_by
            )


class FederationMember(models.Model):
    """
    Appartenance d'un utilisateur à une fédération avec rôle(s).
    Structure similaire à ClubMember.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('active', _('Actif')),
        ('suspended', _('Suspendu')),
        ('inactive', _('Inactif')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='federation_memberships',
        verbose_name=_("Utilisateur")
    )
    federation = models.ForeignKey(
        'Federation',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_("Fédération")
    )
    role = models.ForeignKey(
        OrganizationalRole,
        on_delete=models.SET_NULL,
        null=True,
        related_name='federation_members',
        verbose_name=_("Rôle")
    )
    additional_roles = models.ManyToManyField(
        OrganizationalRole,
        blank=True,
        related_name='additional_federation_members'
    )
    custom_permissions = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(auto_now_add=True)
    role_assigned_at = models.DateTimeField(null=True, blank=True)
    role_assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='federation_role_assignments'
    )
    
    class Meta:
        verbose_name = _("Membre de fédération")
        verbose_name_plural = _("Membres de fédération")
        unique_together = ('user', 'federation')
    
    def __str__(self):
        role_name = self.role.name if self.role else _("Membre")
        return f"{self.user.username} - {role_name} @ {self.federation.name}"
    
    @property
    def effective_permissions(self):
        """Calcule les permissions effectives."""
        permissions = set()
        
        if self.role and self.role.default_permissions:
            permissions.update(self.role.default_permissions.get('permissions', []))
        
        for role in self.additional_roles.all():
            if role.default_permissions:
                permissions.update(role.default_permissions.get('permissions', []))
        
        if self.custom_permissions:
            permissions.update(self.custom_permissions.get('grant', []))
            for perm in self.custom_permissions.get('revoke', []):
                permissions.discard(perm)
        
        return permissions
    
    def has_permission(self, permission):
        """Vérifie si le membre a une permission spécifique."""
        perms = self.effective_permissions
        if '*' in perms:
            return True
        return permission in perms


class MemberRoleHistory(models.Model):
    """Historique des changements de rôle."""
    ACTION_CHOICES = [
        ('role_assigned', _('Rôle assigné')),
        ('role_removed', _('Rôle retiré')),
        ('additional_role_added', _('Rôle additionnel ajouté')),
        ('additional_role_removed', _('Rôle additionnel retiré')),
        ('permissions_modified', _('Permissions modifiées')),
        ('status_changed', _('Statut modifié')),
    ]
    
    member = models.ForeignKey(
        ClubMember, 
        on_delete=models.CASCADE, 
        related_name='role_history'
    )
    action = models.CharField(
        _("Action"), 
        max_length=30, 
        choices=ACTION_CHOICES
    )
    role = models.ForeignKey(
        OrganizationalRole, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='+'
    )
    old_role = models.ForeignKey(
        OrganizationalRole, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_("Ancien rôle")
    )
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='role_changes_made'
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Historique de rôle")
        verbose_name_plural = _("Historiques de rôle")
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.member.user.username} - {self.get_action_display()} ({self.performed_at})"
