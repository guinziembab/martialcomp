import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class RefreshToken(models.Model):
    """
    Refresh token pour l'authentification mobile.
    Permet la prolongation des sessions et la rotation automatique des tokens d'accès.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='refresh_tokens',
        verbose_name=_("Utilisateur")
    )
    token = models.CharField(_("Token"), max_length=255, unique=True)
    expires_at = models.DateTimeField(_("Date d'expiration"))
    issued_at = models.DateTimeField(_("Date d'émission"), auto_now_add=True)
    revoked = models.BooleanField(_("Révoqué"), default=False)
    device_id = models.CharField(_("ID de l'appareil"), max_length=255, blank=True, null=True)
    user_agent = models.TextField(_("User Agent"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("Adresse IP"), blank=True, null=True)
    
    # Multi-tenant information
    tenant = models.ForeignKey(
        "multitenant.Tenant", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Tenant"),
        help_text=_("Le tenant auquel ce token est associé")
    )
    
    # Champs PKCE (Proof Key for Code Exchange)
    code_challenge = models.CharField(_("Code Challenge"), max_length=128, blank=True, null=True)
    code_challenge_method = models.CharField(_("Méthode Code Challenge"), max_length=10, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Token de rafraîchissement")
        verbose_name_plural = _("Tokens de rafraîchissement")
        ordering = ['-issued_at']
        
    def __str__(self):
        return f"Token pour {self.user.username} ({self.id})"
    
    @property
    def is_expired(self):
        """Vérifie si le token est expiré"""
        return self.expires_at < timezone.now()
    
    @property
    def is_valid(self):
        """Vérifie si le token est valide (non expiré et non révoqué)"""
        return not self.revoked and not self.is_expired


class AccessTokenLog(models.Model):
    """
    Journal des tokens d'accès émis pour audit et sécurité.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='access_token_logs',
        verbose_name=_("Utilisateur")
    )
    issued_at = models.DateTimeField(_("Date d'émission"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Date d'expiration"))
    jti = models.CharField(_("JWT ID"), max_length=255, unique=True)
    device_id = models.CharField(_("ID de l'appareil"), max_length=255, blank=True, null=True)
    user_agent = models.TextField(_("User Agent"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("Adresse IP"), blank=True, null=True)
    revoked = models.BooleanField(_("Révoqué"), default=False)
    revoked_at = models.DateTimeField(_("Date de révocation"), null=True, blank=True)
    
    # Multi-tenant information
    tenant = models.ForeignKey(
        "multitenant.Tenant", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Tenant"),
        help_text=_("Le tenant auquel ce token est associé")
    )
    
    class Meta:
        verbose_name = _("Journal de token d'accès")
        verbose_name_plural = _("Journal des tokens d'accès")
        ordering = ['-issued_at']
        
    def __str__(self):
        return f"Access token pour {self.user.username} ({self.jti})"
    
    @property
    def is_expired(self):
        """Vérifie si le token est expiré"""
        return self.expires_at < timezone.now()
    
    def revoke(self):
        """Révoque le token"""
        self.revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=['revoked', 'revoked_at'])

    
class DeviceRegistration(models.Model):
    """
    Enregistrement des appareils mobiles pour les notifications push et
    la gestion de la sécurité.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='registered_devices',
        verbose_name=_("Utilisateur")
    )
    device_id = models.CharField(_("ID de l'appareil"), max_length=255)
    device_name = models.CharField(_("Nom de l'appareil"), max_length=255, blank=True, null=True)
    device_model = models.CharField(_("Modèle de l'appareil"), max_length=255, blank=True, null=True)
    os_version = models.CharField(_("Version OS"), max_length=50, blank=True, null=True)
    app_version = models.CharField(_("Version de l'app"), max_length=50, blank=True, null=True)
    push_token = models.CharField(_("Token de notification"), max_length=255, blank=True, null=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    registered_at = models.DateTimeField(_("Date d'enregistrement"), auto_now_add=True)
    last_used_at = models.DateTimeField(_("Dernière utilisation"), auto_now=True)
    
    # Multi-tenant information
    tenant = models.ForeignKey(
        "multitenant.Tenant", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Tenant"),
        help_text=_("Le tenant auquel cet appareil est associé")
    )
    
    class Meta:
        verbose_name = _("Appareil enregistré")
        verbose_name_plural = _("Appareils enregistrés")
        unique_together = ('user', 'device_id')
        ordering = ['-last_used_at']
        
    def __str__(self):
        device_name = self.device_name or self.device_model or self.device_id
        return f"{device_name} ({self.user.username})"


class PKCESession(models.Model):
    """
    Session PKCE (Proof Key for Code Exchange) pour l'authentification mobile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='pkce_sessions',
        verbose_name=_("Utilisateur"),
        null=True,  # Null lors de la phase initiale
    )
    code_challenge = models.CharField(_("Code Challenge"), max_length=128)
    code_challenge_method = models.CharField(_("Méthode Code Challenge"), max_length=10, default="S256")
    code_verifier = models.CharField(_("Code Verifier"), max_length=128, blank=True, null=True)
    auth_code = models.CharField(_("Code d'autorisation"), max_length=128, unique=True, null=True, blank=True)
    state = models.CharField(_("État"), max_length=128, blank=True, null=True)
    redirect_uri = models.URLField(_("URI de redirection"), blank=True, null=True)
    scope = models.CharField(_("Portée"), max_length=255, blank=True, null=True)
    client_id = models.CharField(_("Client ID"), max_length=255)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Date d'expiration"))
    used = models.BooleanField(_("Utilisé"), default=False)
    
    # Multi-tenant information
    tenant = models.ForeignKey(
        "multitenant.Tenant", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Tenant"),
        help_text=_("Le tenant auquel cette session est associée")
    )
    
    class Meta:
        verbose_name = _("Session PKCE")
        verbose_name_plural = _("Sessions PKCE")
        ordering = ['-created_at']
        
    def __str__(self):
        if self.user:
            return f"Session PKCE pour {self.user.username} ({self.id})"
        return f"Session PKCE non authentifiée ({self.id})"
    
    @property
    def is_expired(self):
        """Vérifie si la session est expirée"""
        return self.expires_at < timezone.now()
    
    @property
    def is_valid(self):
        """Vérifie si la session est valide (non expirée et non utilisée)"""
        return not self.used and not self.is_expired