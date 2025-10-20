# API Auth Module pour MartialComp

Ce module fournit une authentification JWT complète pour l'application MartialComp, spécialement conçue pour sécuriser les API mobiles et permettre l'intégration multi-tenant.

## Fonctionnalités

- Authentification par nom d'utilisateur/mot de passe
- Gestion des sessions avec tokens de rafraîchissement
- Prise en charge PKCE pour les applications mobiles
- Enregistrement et gestion des appareils 
- Révocation de tokens (globale ou par appareil)
- Journalisation des accès à des fins d'audit
- Support complet du multi-tenant
- Middleware pour la validation des tokens et extraction du contexte tenant
- Gestion des erreurs d'API uniforme

## Installation

1. Ajouter l'application dans `INSTALLED_APPS` de votre fichier `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'oauth2_provider',
    'api_auth',
]
```

2. Ajouter les middlewares dans `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ...
    'api_auth.middleware.JWTTenantMiddleware',  # JWT Tenant middleware
    'api_auth.middleware.APIErrorHandlingMiddleware',  # API Error middleware
    'api_auth.middleware.APILoggingMiddleware',  # API Logging middleware
    # ...
]
```

3. Configurer REST Framework et JWT dans `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    # Autres paramètres...
}

# Configuration des tokens de rafraîchissement
REFRESH_TOKEN_LIFETIME_DAYS = 30
```

4. Inclure les URLs dans votre fichier `urls.py` principal:

```python
urlpatterns = [
    # ...
    path('api/v1/auth/', include('api_auth.urls', namespace='api_auth')),
]
```

5. Exécuter les migrations:

```bash
python manage.py makemigrations api_auth
python manage.py migrate api_auth
```

## Documentation

La documentation complète de l'API est disponible dans le répertoire `docs/api_auth/`.

Des exemples d'implémentation client pour iOS (Swift) et Android (Kotlin) sont fournis dans `docs/api_examples/`.

## Modules et composants

### Modèles

- `RefreshToken`: Stocke les tokens de rafraîchissement pour les sessions longues
- `AccessTokenLog`: Journal des tokens d'accès pour audit et sécurité
- `DeviceRegistration`: Enregistrement des appareils pour les notifications push
- `PKCESession`: Gestion du flux d'authentification PKCE pour les applications mobiles

### Middlewares

- `JWTTenantMiddleware`: Extraction du contexte tenant depuis les tokens JWT
- `APIErrorHandlingMiddleware`: Gestion uniforme des erreurs d'API
- `APILoggingMiddleware`: Journalisation des requêtes et réponses API

### Permissions

- `IsTenantUser`: Vérifie que l'utilisateur appartient au tenant actuel
- `IsTokenOwner`: Vérifie que l'utilisateur est le propriétaire du token
- `IsDeviceOwner`: Vérifie que l'utilisateur est le propriétaire de l'appareil
- `HasRolePermission`: Permission basée sur le rôle de l'utilisateur
- `HasFederationPermission`: Vérifie les droits d'un utilisateur dans une fédération
- `HasClubPermission`: Vérifie les droits d'un utilisateur dans un club

### Vues API

- `LoginView`: Authentification des utilisateurs
- `RegisterView`: Inscription de nouveaux utilisateurs
- `RefreshTokenView`: Rafraîchissement des tokens d'accès
- `LogoutView`: Déconnexion et révocation des tokens
- `UserView`: Information sur l'utilisateur courant
- `DeviceRegistrationView`: Gestion des appareils
- `RevokeTokenView`: Révocation des tokens par appareil
- `PKCEInitView`, `PKCEAuthorizationView`, `PKCECompleteView`: Flux PKCE

## Flux d'authentification

### Flux standard

1. L'utilisateur s'authentifie avec son nom d'utilisateur et mot de passe
2. L'API renvoie un token d'accès (courte durée) et un token de rafraîchissement (longue durée)
3. L'application utilise le token d'accès pour les requêtes API
4. Quand le token d'accès expire, l'application utilise le token de rafraîchissement pour obtenir un nouveau token d'accès

### Flux PKCE (pour applications mobiles)

1. L'application génère un code_verifier et son code_challenge correspondant
2. L'application initie le flux PKCE avec le code_challenge
3. L'utilisateur s'authentifie
4. L'application complète le flux PKCE avec le code_verifier
5. L'API vérifie que le code_verifier correspond au code_challenge et renvoie les tokens