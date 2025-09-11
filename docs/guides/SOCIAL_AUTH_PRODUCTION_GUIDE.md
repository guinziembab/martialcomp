# Guide de Déploiement - Authentification Sociale (Production)

## État Actuel de l'Implémentation

✅ **Configuration Django complétée:**
- Applications django-allauth ajoutées à `INSTALLED_APPS` (temporairement commentées)
- `AUTHENTICATION_BACKENDS` configuré
- `SITE_ID = 1` défini
- Paramètres django-allauth préparés
- Adaptateurs personnalisés créés dans `competitions/adapters.py`
- Site object configuré dans PostgreSQL (martialcomp.com)

## Installation en Production

### Option 1: Installation Automatique (Recommandée)

```bash
# Rendre le script exécutable et l'exécuter
chmod +x install_social_auth_production.sh
./install_social_auth_production.sh
```

### Option 2: Installation Manuelle

#### 1. Installer django-allauth
```bash
pip install django-allauth
```

#### 2. Décommenter les paramètres dans `config/settings.py`

Décommenter ces lignes dans `INSTALLED_APPS`:
```python
'allauth',
'allauth.account',
'allauth.socialaccount',
'allauth.socialaccount.providers.google',
'allauth.socialaccount.providers.facebook',
'allauth.socialaccount.providers.apple',
```

Décommenter dans `AUTHENTICATION_BACKENDS`:
```python
'allauth.account.auth_backends.AuthenticationBackend',
```

Décommenter tous les paramètres `ACCOUNT_*` et `SOCIALACCOUNT_*`.

#### 3. Ajouter l'URL allauth dans `config/urls.py`
```python
urlpatterns = [
    # ... URLs existantes
    path('accounts/', include('allauth.urls')),
    # ... autres URLs
]
```

#### 4. Exécuter les migrations
```bash
python manage.py migrate
```

## Configuration des Fournisseurs Sociaux

### 1. Google OAuth2

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet ou sélectionner un projet existant
3. Activer l'API Google+ et Google Sign-In
4. Créer des identifiants OAuth 2.0:
   - Type: Application Web
   - Origines JavaScript autorisées: `https://martialcomp.com`
   - URI de redirection autorisés: `https://martialcomp.com/accounts/google/login/callback/`

### 2. Facebook Login

1. Aller sur [Facebook Developers](https://developers.facebook.com/)
2. Créer une nouvelle application
3. Ajouter le produit "Facebook Login"
4. Configurer:
   - URI de redirection OAuth valides: `https://martialcomp.com/accounts/facebook/login/callback/`
   - Domaines d'application: `martialcomp.com`

### 3. Sign in with Apple

1. Aller sur [Apple Developer Portal](https://developer.apple.com/)
2. Créer un App ID avec la capacité "Sign In with Apple"
3. Créer un Services ID pour le web
4. Configurer les domaines et URLs de redirection
5. Générer une clé privée

## Variables d'Environnement

Ajouter ces variables à votre fichier `.env` ou configuration de production:

```bash
# Google OAuth2
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Facebook OAuth2
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret

# Apple Sign In
APPLE_SERVICES_ID=your_apple_services_id
APPLE_PRIVATE_KEY=your_apple_private_key
APPLE_APP_ID=your_apple_app_id
APPLE_CERTIFICATE=your_apple_certificate
```

## Configuration des Applications Sociales en Base

Après avoir obtenu les clés, créer les applications sociales:

```python
# Via Django shell: python manage.py shell
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Google
google_app = SocialApp.objects.create(
    provider='google',
    name='Google',
    client_id='your_google_client_id',
    secret='your_google_client_secret'
)
google_app.sites.add(Site.objects.get(id=1))

# Facebook
facebook_app = SocialApp.objects.create(
    provider='facebook',
    name='Facebook',
    client_id='your_facebook_app_id',
    secret='your_facebook_app_secret'
)
facebook_app.sites.add(Site.objects.get(id=1))

# Apple
apple_app = SocialApp.objects.create(
    provider='apple',
    name='Apple',
    client_id='your_apple_services_id',
    secret='your_apple_private_key'
)
apple_app.sites.add(Site.objects.get(id=1))
```

## URLs Disponibles

Une fois installé, ces URLs seront disponibles:

- `/accounts/login/` - Page de connexion avec options sociales
- `/accounts/signup/` - Page d'inscription avec options sociales
- `/accounts/logout/` - Déconnexion
- `/accounts/password/reset/` - Réinitialisation mot de passe
- `/accounts/google/login/` - Connexion Google
- `/accounts/facebook/login/` - Connexion Facebook
- `/accounts/apple/login/` - Connexion Apple

## Intégration avec l'Onboarding

Les adaptateurs personnalisés dans `competitions/adapters.py` gèrent automatiquement:

1. **Redirection après inscription sociale** → `/onboarding/role/`
2. **Création de profil utilisateur** avec:
   - `role = 'spectator'`
   - `onboarding_step = 'role_selection'`
   - `onboarding_completed = False`
3. **Redirection selon l'état d'onboarding**

## Tests

### 1. Vérifier la configuration
```bash
python manage.py check
```

### 2. Tester les URLs
```bash
curl -I https://martialcomp.com/accounts/login/
curl -I https://martialcomp.com/accounts/google/login/
```

### 3. Vérifier les templates
Les pages de connexion/inscription seront accessibles avec les boutons sociaux intégrés.

## Sécurité

✅ **Paramètres de sécurité activés:**
- `ACCOUNT_EMAIL_VERIFICATION = 'optional'`
- `ACCOUNT_UNIQUE_EMAIL = True`
- `ACCOUNT_EMAIL_REQUIRED = True`
- `ACCOUNT_USERNAME_REQUIRED = False`

✅ **Variables d'environnement pour les secrets**

✅ **HTTPS requis en production**

## Dépannage

### Erreur "allauth module not found"
```bash
pip install django-allauth
python manage.py migrate
```

### Erreur "Social application not found"
Vérifier que les SocialApp sont créées en base avec les bons provider names.

### Erreur de redirection OAuth
Vérifier que les URLs de callback sont correctement configurées dans les consoles développeur.

## Support

- **Documentation complète**: `social-auth-implementation-guide.md`
- **Adaptateurs personnalisés**: `competitions/adapters.py`
- **Configuration**: `config/settings.py` (lignes 111-117, 355, 361-368)

---

## Statut de l'Implémentation

✅ **Installation terminée avec succès** - L'authentification sociale est opérationnelle  
🔄 **Prochaine étape**: Configurer les fournisseurs sociaux (Google, Facebook, Apple)

### Installation Réalisée
- ✅ django-allauth installé (version 0.58.2)
- ✅ Applications allauth ajoutées à INSTALLED_APPS
- ✅ Middleware AccountMiddleware configuré
- ✅ URLs allauth ajoutées (/accounts/)
- ✅ Migrations exécutées (tables créées en PostgreSQL)
- ✅ Site object configuré (martialcomp.com)
- ✅ Adaptateurs personnalisés fonctionnels
- ✅ URLs testées et accessibles