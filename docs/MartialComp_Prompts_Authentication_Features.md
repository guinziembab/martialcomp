# 🔐 MartialComp - Prompts d'Implémentation
## Module Authentification & Gestion des Comptes

**Date:** 19 décembre 2024  
**Version:** 1.0  
**Auteur:** Bertrand / Claude AI  
**Module concerné:** Authentification utilisateur

---

## 📋 Table des matières

1. [Contexte et Analyse de l'Existant](#contexte-et-analyse-de-lexistant)
2. [Prompt 1 - Mot de passe oublié](#prompt-1--fonctionnalité-mot-de-passe-oublié)
3. [Prompt 2 - Email d'activation avec identifiants](#prompt-2--email-dactivation-avec-identifiants)
4. [Prompt 3 - Authentification sociale + classique](#prompt-3--authentification-sociale--classique)
5. [Plan d'Implémentation](#plan-dimplémentation)
6. [Configurations Email](#configurations-email)

---

## Contexte et Analyse de l'Existant

### ✅ Ce qui existe déjà

| Composant | État | Détails |
|-----------|------|---------|
| Django Allauth | ✅ Installé | `allauth`, `allauth.account`, `allauth.socialaccount` |
| URLs Password Reset | ✅ Configurées | `/accounts/password_reset/`, `/accounts/reset/<uidb64>/<token>/` |
| Providers sociaux | ⚠️ Partiellement | Google, Facebook, Apple (config incomplète) |
| Templates login | ✅ Présents | `welcome.html` avec modal login |
| Lien "Mot de passe oublié" | ✅ Présent | Pointe vers `/accounts/password/reset/` |

### ❌ Ce qui manque / À améliorer

| Composant | Priorité | Description |
|-----------|----------|-------------|
| Templates password reset | 🔴 Haute | Templates personnalisés MartialComp |
| Configuration email | 🔴 Haute | SMTP production pour envoi réel |
| Email activation complet | 🔴 Haute | Envoi identifiants à l'activation |
| Auth sociale production | 🟡 Moyenne | Clés API réelles (Google, Facebook) |
| Templates email branded | 🟡 Moyenne | Design MartialComp pour emails |

### 📊 Configuration Actuelle

```python
# settings.py existant
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # ou 'optional'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
LOGOUT_REDIRECT_URL = '/'
```

---

## Prompt 1 – Fonctionnalité Mot de Passe Oublié

### 📝 Description

Implémenter une fonctionnalité complète de réinitialisation de mot de passe avec envoi d'email sécurisé et templates personnalisés MartialComp.

### 🎯 Prompt Complet

```
OBJECTIF: Implémenter la fonctionnalité "Mot de passe oublié" complète pour MartialComp

CONTEXTE EXISTANT:
- Django Allauth installé et configuré
- URLs de base déjà définies:
  - /accounts/password_reset/ (formulaire demande)
  - /accounts/password_reset/done/ (confirmation envoi)
  - /accounts/reset/<uidb64>/<token>/ (lien de reset)
  - /accounts/reset/done/ (confirmation changement)
- Lien "Mot de passe oublié" présent dans welcome.html
- Configuration email basique (console backend en dev)

FONCTIONNALITÉS REQUISES:

1. FLUX UTILISATEUR COMPLET
   
   Étape 1: Demande de réinitialisation
   ┌─────────────────────────────────────────────────────────┐
   │ 🔐 MOT DE PASSE OUBLIÉ                                  │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Entrez votre adresse email pour recevoir un lien       │
   │ de réinitialisation de mot de passe.                   │
   │                                                         │
   │ Email: [_______________________________]               │
   │                                                         │
   │ [Envoyer le lien de réinitialisation]                  │
   │                                                         │
   │ ← Retour à la connexion                                │
   │                                                         │
   └─────────────────────────────────────────────────────────┘

   Étape 2: Confirmation d'envoi
   ┌─────────────────────────────────────────────────────────┐
   │ ✉️ EMAIL ENVOYÉ                                         │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Si un compte existe avec l'adresse fournie,            │
   │ vous recevrez un email avec les instructions           │
   │ pour réinitialiser votre mot de passe.                 │
   │                                                         │
   │ ⚠️ Vérifiez votre dossier spam si vous ne              │
   │    recevez rien dans les prochaines minutes.           │
   │                                                         │
   │ [Retour à l'accueil]                                   │
   │                                                         │
   └─────────────────────────────────────────────────────────┘

   Étape 3: Page de nouveau mot de passe (via lien email)
   ┌─────────────────────────────────────────────────────────┐
   │ 🔑 NOUVEAU MOT DE PASSE                                 │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Nouveau mot de passe:                                   │
   │ [_______________________________] 👁️                   │
   │                                                         │
   │ Confirmer le mot de passe:                              │
   │ [_______________________________] 👁️                   │
   │                                                         │
   │ Exigences:                                              │
   │ ✅ Au moins 8 caractères                                │
   │ ✅ Au moins une majuscule                               │
   │ ✅ Au moins un chiffre                                  │
   │ ⬜ Au moins un caractère spécial                        │
   │                                                         │
   │ [Réinitialiser mon mot de passe]                       │
   │                                                         │
   └─────────────────────────────────────────────────────────┘

   Étape 4: Confirmation finale
   ┌─────────────────────────────────────────────────────────┐
   │ ✅ MOT DE PASSE MODIFIÉ                                 │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ 🎉 Votre mot de passe a été modifié avec succès !      │
   │                                                         │
   │ Vous pouvez maintenant vous connecter avec             │
   │ votre nouveau mot de passe.                            │
   │                                                         │
   │ [Se connecter]                                          │
   │                                                         │
   └─────────────────────────────────────────────────────────┘

2. TEMPLATE EMAIL DE RÉINITIALISATION
   ```
   Subject: [MartialComp] Réinitialisation de votre mot de passe
   
   ┌─────────────────────────────────────────────────────────┐
   │ [LOGO MARTIALCOMP]                                      │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Bonjour {first_name},                                   │
   │                                                         │
   │ Vous avez demandé la réinitialisation de votre mot     │
   │ de passe pour votre compte MartialComp.                │
   │                                                         │
   │ Cliquez sur le bouton ci-dessous pour créer un         │
   │ nouveau mot de passe :                                  │
   │                                                         │
   │        [RÉINITIALISER MON MOT DE PASSE]                │
   │                                                         │
   │ Ce lien expire dans 24 heures.                         │
   │                                                         │
   │ Si vous n'avez pas fait cette demande, ignorez         │
   │ simplement cet email. Votre mot de passe actuel        │
   │ restera inchangé.                                       │
   │                                                         │
   │ ─────────────────────────────────────────────────────  │
   │ Si le bouton ne fonctionne pas, copiez ce lien :       │
   │ {reset_url}                                             │
   │ ─────────────────────────────────────────────────────  │
   │                                                         │
   │ L'équipe MartialComp 🥋                                 │
   │                                                         │
   ├─────────────────────────────────────────────────────────┤
   │ © 2024 MartialComp | Mentions légales | Contact        │
   └─────────────────────────────────────────────────────────┘
   ```

3. SÉCURITÉ
   - Token unique à usage unique
   - Expiration du lien: 24 heures (configurable)
   - Rate limiting: max 3 demandes par heure par email
   - Message identique que l'email existe ou non (éviter énumération)
   - Log des tentatives pour audit
   - Notification email si reset réussi

4. CONFIGURATION EMAIL (settings.py)
   ```python
   # Production (SMTP)
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.ionos.fr'  # ou autre provider
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'noreply@martialcomp.com'
   EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
   DEFAULT_FROM_EMAIL = 'MartialComp <noreply@martialcomp.com>'
   
   # Password reset settings
   PASSWORD_RESET_TIMEOUT = 86400  # 24 heures en secondes
   ```

5. INTERNATIONALISATION
   - Tous les textes avec {% trans %} ou gettext
   - Templates email en FR, EN, ES, IT, DE, PT minimum
   - Détection langue utilisateur pour email

FICHIERS À CRÉER/MODIFIER:

1. templates/account/password_reset.html
   - Formulaire de demande de reset
   - Design MartialComp (cohérent avec welcome.html)

2. templates/account/password_reset_done.html
   - Page de confirmation d'envoi

3. templates/account/password_reset_confirm.html
   - Formulaire de nouveau mot de passe
   - Validation en temps réel (JavaScript)

4. templates/account/password_reset_complete.html
   - Page de confirmation finale

5. templates/account/email/password_reset_key_message.html
   - Template HTML de l'email
   
6. templates/account/email/password_reset_key_message.txt
   - Version texte de l'email

7. templates/account/email/password_reset_key_subject.txt
   - Sujet de l'email

8. config/settings/base.py
   - Configuration EMAIL_*
   - PASSWORD_RESET_TIMEOUT

9. competitions/forms.py (optionnel)
   - CustomPasswordResetForm avec validation

10. static/css/auth.css
    - Styles pour les pages d'authentification

TESTS À IMPLÉMENTER:
- Test envoi email (mock)
- Test token expiration
- Test rate limiting
- Test utilisateur inexistant (même réponse)
- Test changement mot de passe réussi
- Test token invalide/expiré

OUTPUT ATTENDU:
- Templates HTML complets et responsives
- Templates email HTML + TXT
- Configuration settings.py
- CSS cohérent avec le design MartialComp
- Tests unitaires
- Documentation utilisateur
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `templates/account/password_reset.html` | Créer | Formulaire demande |
| `templates/account/password_reset_done.html` | Créer | Confirmation envoi |
| `templates/account/password_reset_confirm.html` | Créer | Nouveau mot de passe |
| `templates/account/password_reset_complete.html` | Créer | Confirmation finale |
| `templates/account/email/password_reset_key_*` | Créer | Templates email |
| `config/settings/base.py` | Modifier | Config EMAIL |

---

## Prompt 2 – Email d'Activation avec Identifiants

### 📝 Description

Lors de l'activation d'un compte par un administrateur ou lors de la validation d'un email, envoyer automatiquement un email contenant les identifiants de connexion de l'utilisateur.

### 🎯 Prompt Complet

```
OBJECTIF: Envoyer un email avec les identifiants lors de l'activation d'un compte

CONTEXTE EXISTANT:
- Système d'inscription via onboarding (onboarding_refactored.py)
- Allauth configuré avec ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
- UserProfile avec champ is_active / onboarding_completed
- Admins peuvent activer des comptes manuellement

SCÉNARIOS D'ACTIVATION:

1. ACTIVATION PAR VÉRIFICATION EMAIL (utilisateur)
   Déclencheur: Clic sur le lien de vérification email
   Action: Envoyer email de bienvenue avec rappel identifiants

2. ACTIVATION MANUELLE PAR ADMIN
   Déclencheur: Admin active un compte depuis le back-office
   Action: Envoyer email d'activation avec identifiants

3. CRÉATION DE COMPTE PAR ADMIN/COACH
   Déclencheur: Admin crée un compte pour un pratiquant
   Action: Envoyer email avec identifiants + lien de première connexion

FONCTIONNALITÉS REQUISES:

1. EMAIL DE BIENVENUE (Post-vérification email)
   ```
   Subject: [MartialComp] 🎉 Bienvenue ! Votre compte est activé
   
   ┌─────────────────────────────────────────────────────────┐
   │ [LOGO MARTIALCOMP]                                      │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ 🎉 Bienvenue sur MartialComp, {first_name} !           │
   │                                                         │
   │ Votre compte a été activé avec succès.                 │
   │ Vous pouvez maintenant accéder à toutes les            │
   │ fonctionnalités de la plateforme.                      │
   │                                                         │
   │ ─────────────────────────────────────────────────────  │
   │ 📧 VOS IDENTIFIANTS DE CONNEXION                       │
   │ ─────────────────────────────────────────────────────  │
   │                                                         │
   │ Email : {email}                                         │
   │ Mot de passe : ******** (celui que vous avez choisi)   │
   │                                                         │
   │ 💡 Conseil : Ajoutez cette page à vos favoris          │
   │    https://www.martialcomp.com/accounts/login/         │
   │                                                         │
   │        [ACCÉDER À MON ESPACE]                          │
   │                                                         │
   │ ─────────────────────────────────────────────────────  │
   │ 🚀 PREMIERS PAS                                         │
   │ ─────────────────────────────────────────────────────  │
   │                                                         │
   │ 1. Complétez votre profil                              │
   │ 2. Rejoignez ou créez votre club                       │
   │ 3. Inscrivez-vous à votre première compétition         │
   │                                                         │
   │ Besoin d'aide ? Consultez notre guide de démarrage     │
   │ ou contactez-nous à support@martialcomp.com            │
   │                                                         │
   │ L'équipe MartialComp 🥋                                 │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

2. EMAIL ACTIVATION PAR ADMIN (avec mot de passe temporaire)
   ```
   Subject: [MartialComp] Votre compte a été créé
   
   ┌─────────────────────────────────────────────────────────┐
   │ [LOGO MARTIALCOMP]                                      │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Bonjour {first_name},                                   │
   │                                                         │
   │ Un compte MartialComp a été créé pour vous par         │
   │ {admin_name} ({organization_name}).                     │
   │                                                         │
   │ ─────────────────────────────────────────────────────  │
   │ 🔐 VOS IDENTIFIANTS DE CONNEXION                       │
   │ ─────────────────────────────────────────────────────  │
   │                                                         │
   │ Email : {email}                                         │
   │ Mot de passe temporaire : {temp_password}              │
   │                                                         │
   │ ⚠️ IMPORTANT : Pour des raisons de sécurité,           │
   │ vous devrez changer ce mot de passe lors de votre      │
   │ première connexion.                                     │
   │                                                         │
   │        [ACTIVER MON COMPTE]                             │
   │                                                         │
   │ Ce lien expire dans 7 jours.                           │
   │                                                         │
   │ Si vous n'avez pas demandé ce compte, veuillez         │
   │ ignorer cet email ou nous contacter.                   │
   │                                                         │
   │ L'équipe MartialComp 🥋                                 │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

3. GÉNÉRATION MOT DE PASSE TEMPORAIRE
   ```python
   import secrets
   import string
   
   def generate_temp_password(length=12):
       """
       Génère un mot de passe temporaire sécurisé.
       Contient: majuscules, minuscules, chiffres, caractères spéciaux
       """
       alphabet = string.ascii_letters + string.digits + "!@#$%&*"
       while True:
           password = ''.join(secrets.choice(alphabet) for _ in range(length))
           # Vérifier qu'il contient au moins 1 de chaque type
           if (any(c.islower() for c in password) and
               any(c.isupper() for c in password) and
               any(c.isdigit() for c in password) and
               any(c in "!@#$%&*" for c in password)):
               return password
   ```

4. SERVICE D'ENVOI D'EMAIL D'ACTIVATION
   ```python
   # competitions/services/account_activation_service.py
   
   class AccountActivationService:
       """Service pour gérer l'activation des comptes et l'envoi d'emails."""
       
       @staticmethod
       def send_welcome_email(user):
           """Envoie l'email de bienvenue après vérification."""
           pass
       
       @staticmethod
       def send_admin_created_account_email(user, temp_password, created_by):
           """Envoie l'email avec identifiants pour compte créé par admin."""
           pass
       
       @staticmethod
       def activate_and_notify(user, activated_by=None):
           """Active un compte et envoie la notification appropriée."""
           pass
       
       @staticmethod
       def force_password_change_on_first_login(user):
           """Marque l'utilisateur pour changement de mot de passe obligatoire."""
           pass
   ```

5. SIGNAL POUR ENVOI AUTOMATIQUE
   ```python
   # competitions/signals/account_signals.py
   
   from allauth.account.signals import email_confirmed
   from django.dispatch import receiver
   
   @receiver(email_confirmed)
   def send_welcome_on_email_confirmed(request, email_address, **kwargs):
       """Envoie l'email de bienvenue quand l'email est confirmé."""
       user = email_address.user
       AccountActivationService.send_welcome_email(user)
   ```

6. FORCER CHANGEMENT MOT DE PASSE (première connexion)
   ```python
   # Ajouter au modèle UserProfile
   class UserProfile(models.Model):
       # ... champs existants
       must_change_password = models.BooleanField(
           default=False,
           verbose_name=_("Doit changer le mot de passe")
       )
       password_changed_at = models.DateTimeField(
           null=True, blank=True,
           verbose_name=_("Mot de passe changé le")
       )
   
   # Middleware pour forcer le changement
   class ForcePasswordChangeMiddleware:
       def __init__(self, get_response):
           self.get_response = get_response
       
       def __call__(self, request):
           if request.user.is_authenticated:
               profile = getattr(request.user, 'profile', None)
               if profile and profile.must_change_password:
                   allowed_urls = [
                       reverse('account_change_password'),
                       reverse('account_logout'),
                   ]
                   if request.path not in allowed_urls:
                       messages.warning(
                           request,
                           _("Veuillez changer votre mot de passe pour continuer.")
                       )
                       return redirect('account_change_password')
           return self.get_response(request)
   ```

7. INTERFACE ADMIN POUR ACTIVATION
   ```python
   # Dans admin.py ou via action custom
   
   @admin.action(description="Activer les comptes sélectionnés et envoyer les identifiants")
   def activate_and_send_credentials(modeladmin, request, queryset):
       for user in queryset:
           if not user.is_active:
               temp_password = generate_temp_password()
               user.set_password(temp_password)
               user.is_active = True
               user.save()
               
               # Marquer pour changement obligatoire
               profile = user.profile
               profile.must_change_password = True
               profile.save()
               
               # Envoyer email
               AccountActivationService.send_admin_created_account_email(
                   user=user,
                   temp_password=temp_password,
                   created_by=request.user
               )
       
       messages.success(request, f"{queryset.count()} compte(s) activé(s).")
   ```

SÉCURITÉ:
- Ne jamais logger les mots de passe temporaires
- Expiration du lien d'activation: 7 jours
- Forcer changement mot de passe à la première connexion
- Rate limiting sur les emails envoyés
- Audit trail des activations

FICHIERS À CRÉER/MODIFIER:

1. competitions/services/account_activation_service.py
   - Service complet d'activation

2. competitions/signals/account_signals.py
   - Signaux pour envoi automatique

3. competitions/middleware/password_change.py
   - Middleware forçage changement mot de passe

4. competitions/models/users.py
   - Ajouter champs must_change_password, password_changed_at

5. templates/account/email/welcome_message.html
   - Email de bienvenue

6. templates/account/email/account_created_message.html
   - Email compte créé par admin

7. competitions/admin.py
   - Action admin pour activation en masse

8. templates/account/password_change.html
   - Page de changement de mot de passe (améliorer)

OUTPUT ATTENDU:
- Service Python complet
- Templates email HTML + TXT
- Middleware de forçage
- Actions admin
- Tests unitaires
- Documentation
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `services/account_activation_service.py` | Créer | Service principal |
| `signals/account_signals.py` | Créer | Signaux auto |
| `middleware/password_change.py` | Créer | Forçage mot de passe |
| `models/users.py` | Modifier | Nouveaux champs |
| `templates/account/email/welcome_*` | Créer | Email bienvenue |
| `templates/account/email/account_created_*` | Créer | Email admin |
| `admin.py` | Modifier | Actions admin |

---

## Prompt 3 – Authentification Sociale + Classique

### 📝 Description

Activer l'authentification via Google, Facebook et Apple tout en conservant l'authentification classique par email/mot de passe. Interface unifiée et gestion des comptes liés.

### 🎯 Prompt Complet

```
OBJECTIF: Activer l'authentification sociale (Google, Facebook, Apple) en parallèle de l'authentification classique

CONTEXTE EXISTANT:
- Django Allauth installé avec providers configurés (mais clés placeholder)
- Guide d'implémentation existant: social-auth-implementation-guide.md
- Templates de login avec boutons sociaux (welcome.html)
- Adapters personnalisés partiellement implémentés

PROVIDERS À ACTIVER:

1. GOOGLE
   - Login via compte Google
   - Récupération: email, nom, prénom, photo
   - Console: https://console.cloud.google.com/

2. FACEBOOK
   - Login via compte Facebook
   - Récupération: email, nom, photo
   - Console: https://developers.facebook.com/

3. APPLE (optionnel mais recommandé)
   - Login via Apple ID
   - Important pour utilisateurs iOS
   - Console: https://developer.apple.com/

FONCTIONNALITÉS REQUISES:

1. PAGE DE CONNEXION UNIFIÉE
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🥋 CONNEXION À MARTIALCOMP                              │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ [G] Continuer avec Google                          │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ [f] Continuer avec Facebook                        │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ [] Continuer avec Apple                           │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ─────────────── ou ───────────────                     │
   │                                                         │
   │ Email:                                                  │
   │ [_______________________________]                      │
   │                                                         │
   │ Mot de passe:                                           │
   │ [_______________________________] 👁️                   │
   │                                                         │
   │ ☐ Se souvenir de moi                                   │
   │                                                         │
   │ [Se connecter]                                          │
   │                                                         │
   │ Mot de passe oublié ? | Créer un compte                │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

2. PAGE D'INSCRIPTION UNIFIÉE
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🥋 CRÉER UN COMPTE MARTIALCOMP                          │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ [G] S'inscrire avec Google                         │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ [f] S'inscrire avec Facebook                       │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ─────────────── ou ───────────────                     │
   │                                                         │
   │ Prénom:              Nom:                               │
   │ [______________]     [______________]                  │
   │                                                         │
   │ Email:                                                  │
   │ [_______________________________]                      │
   │                                                         │
   │ Mot de passe:                                           │
   │ [_______________________________]                      │
   │                                                         │
   │ ☐ J'accepte les CGU et la politique de confidentialité │
   │                                                         │
   │ [Créer mon compte]                                      │
   │                                                         │
   │ Déjà inscrit ? Se connecter                            │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

3. GESTION DES COMPTES LIÉS (Profil utilisateur)
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🔗 COMPTES CONNECTÉS                                    │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ Google                                                  │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ ✅ Connecté: john.doe@gmail.com                    │ │
   │ │                              [Déconnecter]         │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ Facebook                                                │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ ⬜ Non connecté                                     │ │
   │ │                              [Connecter]           │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ Apple                                                   │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ ⬜ Non connecté                                     │ │
   │ │                              [Connecter]           │ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   │ ─────────────────────────────────────────────────────  │
   │                                                         │
   │ Authentification classique                              │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ ✅ Email/Mot de passe activé                       │ │
   │ │    bertrand@example.com                            │ │
   │ │                              [Changer mot de passe]│ │
   │ └─────────────────────────────────────────────────────┘ │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

4. CONFIGURATION SETTINGS.PY COMPLÈTE
   ```python
   # settings.py - Configuration Authentification Sociale
   
   INSTALLED_APPS = [
       # ... apps existantes
       'django.contrib.sites',
       'allauth',
       'allauth.account',
       'allauth.socialaccount',
       'allauth.socialaccount.providers.google',
       'allauth.socialaccount.providers.facebook',
       'allauth.socialaccount.providers.apple',
   ]
   
   SITE_ID = 1
   
   AUTHENTICATION_BACKENDS = [
       'django.contrib.auth.backends.ModelBackend',
       'allauth.account.auth_backends.AuthenticationBackend',
   ]
   
   # Configuration Allauth
   ACCOUNT_AUTHENTICATION_METHOD = 'email'
   ACCOUNT_EMAIL_REQUIRED = True
   ACCOUNT_UNIQUE_EMAIL = True
   ACCOUNT_USERNAME_REQUIRED = False
   ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
   ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
   ACCOUNT_LOGOUT_ON_GET = True
   ACCOUNT_SESSION_REMEMBER = True
   
   # Social Account settings
   SOCIALACCOUNT_AUTO_SIGNUP = True
   SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Emails sociaux déjà vérifiés
   SOCIALACCOUNT_QUERY_EMAIL = True
   SOCIALACCOUNT_STORE_TOKENS = True
   
   # Adapters personnalisés
   ACCOUNT_ADAPTER = 'competitions.adapters.MartialCompAccountAdapter'
   SOCIALACCOUNT_ADAPTER = 'competitions.adapters.MartialCompSocialAccountAdapter'
   
   # Redirections
   LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
   ACCOUNT_LOGOUT_REDIRECT_URL = '/'
   SOCIALACCOUNT_LOGIN_ON_GET = True
   
   # Providers Configuration (via variables d'environnement)
   SOCIALACCOUNT_PROVIDERS = {
       'google': {
           'APP': {
               'client_id': env('GOOGLE_CLIENT_ID'),
               'secret': env('GOOGLE_CLIENT_SECRET'),
               'key': ''
           },
           'SCOPE': ['profile', 'email'],
           'AUTH_PARAMS': {'access_type': 'online'},
           'OAUTH_PKCE_ENABLED': True,
       },
       'facebook': {
           'APP': {
               'client_id': env('FACEBOOK_APP_ID'),
               'secret': env('FACEBOOK_APP_SECRET'),
               'key': ''
           },
           'METHOD': 'oauth2',
           'SCOPE': ['email', 'public_profile'],
           'FIELDS': ['id', 'email', 'name', 'first_name', 'last_name', 'picture'],
           'VERSION': 'v18.0',
       },
       'apple': {
           'APP': {
               'client_id': env('APPLE_CLIENT_ID'),
               'secret': env('APPLE_CLIENT_SECRET'),
               'key': env('APPLE_KEY_ID'),
               'certificate_key': env('APPLE_CERTIFICATE_KEY'),
           },
           'SCOPE': ['email', 'name'],
       },
   }
   ```

5. ADAPTERS PERSONNALISÉS
   ```python
   # competitions/adapters.py
   
   from allauth.account.adapter import DefaultAccountAdapter
   from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
   from django.conf import settings
   from django.shortcuts import redirect
   
   class MartialCompAccountAdapter(DefaultAccountAdapter):
       """Adapter pour personnaliser le comportement des comptes classiques."""
       
       def get_login_redirect_url(self, request):
           """Redirection après login selon le profil."""
           user = request.user
           if hasattr(user, 'profile'):
               if not user.profile.onboarding_completed:
                   return '/competitions/onboarding/role/'
               return user.profile.get_dashboard_url()
           return settings.LOGIN_REDIRECT_URL
       
       def save_user(self, request, user, form, commit=True):
           """Personnalise la création d'utilisateur."""
           user = super().save_user(request, user, form, commit=False)
           # Ajouter des champs personnalisés si nécessaire
           if commit:
               user.save()
           return user
   
   
   class MartialCompSocialAccountAdapter(DefaultSocialAccountAdapter):
       """Adapter pour personnaliser le comportement des comptes sociaux."""
       
       def pre_social_login(self, request, sociallogin):
           """
           Appelé avant le login social.
           Permet de lier un compte social à un compte existant.
           """
           # Si l'utilisateur est déjà connecté, lier le compte social
           if request.user.is_authenticated:
               if sociallogin.is_existing:
                   return
               sociallogin.connect(request, request.user)
               return
           
           # Vérifier si un compte existe avec cet email
           email = sociallogin.account.extra_data.get('email')
           if email:
               try:
                   from django.contrib.auth import get_user_model
                   User = get_user_model()
                   existing_user = User.objects.get(email=email)
                   
                   # Lier automatiquement si l'email correspond
                   sociallogin.connect(request, existing_user)
               except User.DoesNotExist:
                   pass
       
       def save_user(self, request, sociallogin, form=None):
           """Personnalise la création d'utilisateur via social."""
           user = super().save_user(request, sociallogin, form)
           
           # Récupérer les données du provider
           extra_data = sociallogin.account.extra_data
           
           # Mettre à jour le profil avec les données sociales
           if not user.first_name and extra_data.get('first_name'):
               user.first_name = extra_data.get('first_name')
           if not user.last_name and extra_data.get('last_name'):
               user.last_name = extra_data.get('last_name')
           
           user.save()
           
           # Créer le profil si nécessaire
           from competitions.models import UserProfile
           profile, created = UserProfile.objects.get_or_create(user=user)
           
           # Marquer l'email comme vérifié (vient d'un provider social)
           user.emailaddress_set.update(verified=True)
           
           return user
       
       def get_login_redirect_url(self, request):
           """Redirection après login social."""
           return self.get_adapter().get_login_redirect_url(request)
       
       def authentication_error(self, request, provider_id, error=None, 
                                exception=None, extra_context=None):
           """Gère les erreurs d'authentification sociale."""
           from django.contrib import messages
           messages.error(
               request,
               f"Erreur de connexion avec {provider_id}. Veuillez réessayer."
           )
           return redirect('account_login')
   ```

6. TEMPLATES ALLAUTH PERSONNALISÉS

   Structure des fichiers:
   ```
   templates/
   └── account/
       ├── login.html                 # Page de connexion
       ├── signup.html                # Page d'inscription
       ├── logout.html                # Confirmation déconnexion
       ├── email_confirm.html         # Confirmation email
       ├── connections.html           # Gestion comptes liés
       └── socialaccount/
           ├── login_cancelled.html   # Annulation login social
           ├── authentication_error.html
           └── connections.html       # Liste comptes sociaux
   ```

7. URLS CONFIGURATION
   ```python
   # urls.py
   from django.urls import path, include
   
   urlpatterns = [
       # URLs Allauth (inclut login, signup, social, etc.)
       path('accounts/', include('allauth.urls')),
       
       # URL personnalisée pour la gestion des comptes liés
       path('accounts/connections/', 
            SocialConnectionsView.as_view(), 
            name='socialaccount_connections'),
   ]
   ```

8. OBTENTION DES CLÉS API

   GOOGLE:
   1. Aller sur https://console.cloud.google.com/
   2. Créer un projet ou sélectionner existant
   3. APIs & Services > Credentials > Create Credentials > OAuth client ID
   4. Type: Web application
   5. Authorized redirect URIs:
      - https://www.martialcomp.com/accounts/google/login/callback/
      - http://localhost:8000/accounts/google/login/callback/ (dev)
   6. Récupérer Client ID et Client Secret

   FACEBOOK:
   1. Aller sur https://developers.facebook.com/
   2. Mes applications > Créer une application
   3. Type: Consommateur
   4. Ajouter le produit "Connexion Facebook"
   5. Paramètres > Base:
      - URL de redirection OAuth valides:
        https://www.martialcomp.com/accounts/facebook/login/callback/
   6. Récupérer App ID et App Secret

   APPLE:
   1. Aller sur https://developer.apple.com/
   2. Certificates, Identifiers & Profiles
   3. Créer un App ID avec Sign In with Apple
   4. Créer un Services ID
   5. Générer une clé privée
   6. Configuration plus complexe (voir documentation Apple)

9. VARIABLES D'ENVIRONNEMENT (.env)
   ```
   # Google OAuth
   GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
   
   # Facebook OAuth
   FACEBOOK_APP_ID=1234567890
   FACEBOOK_APP_SECRET=abcdef123456789
   
   # Apple OAuth (optionnel)
   APPLE_CLIENT_ID=com.martialcomp.webapp
   APPLE_CLIENT_SECRET=xxxxx
   APPLE_KEY_ID=XXXXXXXXXX
   APPLE_CERTIFICATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
   ```

GESTION DES CAS PARTICULIERS:

1. Email déjà utilisé (autre méthode)
   - Proposer de lier les comptes
   - Message clair à l'utilisateur

2. Compte social sans email
   - Demander l'email manuellement
   - Template spécifique

3. Déconnexion du dernier provider
   - Vérifier qu'un mot de passe existe
   - Sinon, demander d'en créer un

4. Fusion de comptes
   - Interface admin pour fusionner
   - Conservation de l'historique

FICHIERS À CRÉER/MODIFIER:

1. competitions/adapters.py
   - MartialCompAccountAdapter (complet)
   - MartialCompSocialAccountAdapter (complet)

2. config/settings/base.py
   - Configuration SOCIALACCOUNT_PROVIDERS
   - Variables d'environnement

3. templates/account/login.html
   - Page de connexion unifiée

4. templates/account/signup.html
   - Page d'inscription unifiée

5. templates/account/connections.html
   - Gestion des comptes liés

6. templates/socialaccount/*.html
   - Templates pour erreurs/annulations

7. static/css/social-auth.css
   - Styles boutons sociaux

8. .env.example
   - Template des variables

TESTS À IMPLÉMENTER:
- Test login Google (mock)
- Test login Facebook (mock)
- Test liaison compte existant
- Test déconnexion provider
- Test création compte via social
- Test redirection post-login

OUTPUT ATTENDU:
- Configuration complète settings.py
- Adapters fonctionnels
- Templates personnalisés
- Guide obtention clés API
- CSS boutons sociaux
- Tests unitaires
- Documentation déploiement
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `competitions/adapters.py` | Créer/Compléter | Adapters personnalisés |
| `config/settings/base.py` | Modifier | Config SOCIALACCOUNT |
| `templates/account/login.html` | Créer | Login unifié |
| `templates/account/signup.html` | Créer | Signup unifié |
| `templates/account/connections.html` | Créer | Comptes liés |
| `static/css/social-auth.css` | Créer | Styles boutons |
| `.env.example` | Créer | Template variables |

---

## Plan d'Implémentation

### 📅 Planning Recommandé

| Phase | Prompt | Durée | Priorité | Dépendances |
|-------|--------|-------|----------|-------------|
| **1** | Config Email | 1 jour | 🔴 Critique | Aucune |
| **2** | Prompt 1 - Password Reset | 2 jours | 🔴 Critique | Phase 1 |
| **3** | Prompt 2 - Email Activation | 2 jours | 🔴 Haute | Phase 1 |
| **4** | Prompt 3 - Auth Sociale | 3 jours | 🟡 Moyenne | Phases 1-3 |

### 🔗 Ordre d'Exécution

```
┌─────────────────────────────────────────────────────────────┐
│                 PHASE 1: CONFIGURATION EMAIL                │
│     (Prérequis pour toutes les fonctionnalités email)      │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│   PHASE 2: PASSWORD   │   │   PHASE 3: EMAIL      │
│       RESET           │   │   ACTIVATION          │
│   (Templates + Flow)  │   │   (Service + Signals) │
└───────────┬───────────┘   └───────────┬───────────┘
            │                           │
            └─────────────┬─────────────┘
                          ▼
            ┌───────────────────────────┐
            │   PHASE 4: AUTH SOCIALE   │
            │   (Google, Facebook)      │
            │   (Peut être parallélisé) │
            └───────────────────────────┘
```

---

## Configurations Email

### 🔧 Configuration SMTP Production (IONOS)

```python
# config/settings/production.py

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.ionos.fr'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='noreply@martialcomp.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'MartialComp <noreply@martialcomp.com>'
SERVER_EMAIL = 'errors@martialcomp.com'

# Email templates
EMAIL_SUBJECT_PREFIX = '[MartialComp] '
```

### 🔧 Configuration Développement

```python
# config/settings/local.py

# Console backend pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# OU utiliser MailHog/Mailtrap pour tester
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025
```

### 📧 Variables d'Environnement (.env)

```bash
# Email SMTP
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=your-secure-password

# OAuth Providers
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
FACEBOOK_APP_ID=1234567890
FACEBOOK_APP_SECRET=abcdef123456

# Optionnel
APPLE_CLIENT_ID=com.martialcomp.webapp
APPLE_CLIENT_SECRET=xxxxx
```

---

## ✅ Checklist de Validation

### Prompt 1 - Password Reset
- [ ] Templates créés et stylisés
- [ ] Email envoyé correctement
- [ ] Token expire après 24h
- [ ] Rate limiting fonctionnel
- [ ] Traductions FR/EN minimum
- [ ] Tests passants

### Prompt 2 - Email Activation
- [ ] Service créé et fonctionnel
- [ ] Signal email_confirmed connecté
- [ ] Email de bienvenue envoyé
- [ ] Activation admin avec mot de passe temp
- [ ] Forçage changement mot de passe
- [ ] Tests passants

### Prompt 3 - Auth Sociale
- [ ] Google OAuth fonctionnel
- [ ] Facebook OAuth fonctionnel
- [ ] Templates login/signup unifiés
- [ ] Liaison comptes existants
- [ ] Gestion comptes connectés
- [ ] Tests passants

---

## Historique des Versions

| Version | Date | Auteur | Modifications |
|---------|------|--------|---------------|
| 1.0 | 19/12/2024 | Claude AI | Création initiale |

---

*Document généré pour le projet MartialComp*  
*© 2024 - Tous droits réservés*
