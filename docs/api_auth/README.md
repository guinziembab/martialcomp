# Documentation de l'API d'Authentification JWT pour MartialComp

Cette documentation décrit l'API d'authentification JWT utilisée par l'application MartialComp pour l'authentification des applications mobiles et des services externes.

## Table des matières

1. [Introduction](#introduction)
2. [Configuration](#configuration)
3. [Endpoints d'API](#endpoints-dapi)
   - [Login](#login)
   - [Register](#register)
   - [Refresh Token](#refresh-token)
   - [Logout](#logout)
   - [User Info](#user-info)
   - [Device Registration](#device-registration)
   - [Revoke Tokens](#revoke-tokens)
   - [PKCE Authentication Flow](#pkce-authentication-flow)
4. [Modèles de Données](#modèles-de-données)
5. [Sécurité](#sécurité)
6. [Exemples de Code](#exemples-de-code)
7. [Annexes](#annexes)

## Introduction

L'API d'authentification JWT de MartialComp utilise le standard JSON Web Token (JWT) pour fournir une authentification sécurisée aux clients mobiles et services tiers. Cette API prend en charge :

- Authentification par nom d'utilisateur/mot de passe
- Gestion des sessions via tokens de rafraîchissement
- Protection PKCE pour les applications mobiles
- Enregistrement et gestion des appareils
- Support multi-tenant

## Configuration

### Dépendances requises

```
djangorestframework
djangorestframework-simplejwt
django-oauth-toolkit
cryptography
```

### Configuration dans settings.py

```python
# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
}

# Configuration JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Configuration des tokens de rafraîchissement
REFRESH_TOKEN_LIFETIME_DAYS = 30
```

## Endpoints d'API

Tous les endpoints sont disponibles sous le préfixe `/api/v1/auth/`.

### Login

**Endpoint**: `POST /api/v1/auth/login/`

**Description**: Authentifie un utilisateur et renvoie des tokens d'accès et de rafraîchissement.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| username | string | Oui | Nom d'utilisateur |
| password | string | Oui | Mot de passe |
| device_id | string | Non | Identifiant unique de l'appareil |
| device_name | string | Non | Nom convivial de l'appareil |
| device_model | string | Non | Modèle de l'appareil |
| os_version | string | Non | Version du système d'exploitation |
| app_version | string | Non | Version de l'application |
| code_challenge | string | Non | Code challenge pour PKCE |
| code_challenge_method | string | Non | Méthode du code challenge (S256 ou plain) |

**Exemple de requête**:

```json
{
  "username": "user123",
  "password": "securepassword",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "iPhone de Jean",
  "device_model": "iPhone 13",
  "os_version": "16.2",
  "app_version": "1.2.0"
}
```

**Exemple de réponse réussie** (200 OK):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "username": "user123",
    "email": "user@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_joined": "2025-01-15T14:30:45Z",
    "is_active": true
  },
  "expires_in": 3600
}
```

### Register

**Endpoint**: `POST /api/v1/auth/register/`

**Description**: Enregistre un nouvel utilisateur et renvoie des tokens d'accès et de rafraîchissement.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| username | string | Oui | Nom d'utilisateur souhaité |
| password | string | Oui | Mot de passe (min 8 caractères) |
| password_confirm | string | Oui | Confirmation du mot de passe |
| email | string | Oui | Adresse email |
| first_name | string | Non | Prénom |
| last_name | string | Non | Nom de famille |
| device_id | string | Non | Identifiant unique de l'appareil |
| device_name | string | Non | Nom convivial de l'appareil |
| device_model | string | Non | Modèle de l'appareil |
| os_version | string | Non | Version du système d'exploitation |
| app_version | string | Non | Version de l'application |

**Exemple de requête**:

```json
{
  "username": "nouveauuser",
  "password": "motdepasse123",
  "password_confirm": "motdepasse123",
  "email": "nouveauuser@example.com",
  "first_name": "Marie",
  "last_name": "Martin",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "Samsung Galaxy de Marie",
  "device_model": "Galaxy S22",
  "os_version": "13",
  "app_version": "1.2.0"
}
```

**Exemple de réponse réussie** (201 Created):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 124,
    "username": "nouveauuser",
    "email": "nouveauuser@example.com",
    "first_name": "Marie",
    "last_name": "Martin",
    "date_joined": "2025-05-20T10:15:30Z",
    "is_active": true
  },
  "expires_in": 3600
}
```

### Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh/`

**Description**: Rafraîchit un token d'accès en utilisant un token de rafraîchissement.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| refresh | string | Oui | Token de rafraîchissement |
| code_verifier | string | Non | Code verifier pour PKCE (si PKCE est utilisé) |

**Exemple de requête**:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Exemple de réponse réussie** (200 OK):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "username": "user123",
    "email": "user@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_joined": "2025-01-15T14:30:45Z",
    "is_active": true
  },
  "expires_in": 3600
}
```

### Logout

**Endpoint**: `POST /api/v1/auth/logout/`

**Description**: Révoque le token de rafraîchissement et invalide la session.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| refresh | string | Oui | Token de rafraîchissement à révoquer |

**Exemple de requête**:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Exemple de réponse réussie** (204 No Content):

(Pas de contenu dans la réponse)

### User Info

**Endpoint**: `GET /api/v1/auth/user/`

**Description**: Récupère les informations de l'utilisateur courant.

**Headers**:
- `Authorization: Bearer <access_token>`

**Exemple de réponse réussie** (200 OK):

```json
{
  "id": 123,
  "username": "user123",
  "email": "user@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "date_joined": "2025-01-15T14:30:45Z",
  "is_active": true
}
```

### Device Registration

**Endpoint**: `POST /api/v1/auth/devices/`

**Description**: Enregistre un nouvel appareil pour l'utilisateur actuel.

**Headers**:
- `Authorization: Bearer <access_token>`

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| device_id | string | Oui | Identifiant unique de l'appareil |
| device_name | string | Non | Nom convivial de l'appareil |
| device_model | string | Non | Modèle de l'appareil |
| os_version | string | Non | Version du système d'exploitation |
| app_version | string | Non | Version de l'application |
| push_token | string | Non | Token pour les notifications push |

**Exemple de requête**:

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "iPad de Jean",
  "device_model": "iPad Pro",
  "os_version": "16.0",
  "app_version": "1.2.0",
  "push_token": "fcm:AbCdEfG123456..."
}
```

**Exemple de réponse réussie** (201 Created):

```json
{
  "id": "9f8e7d6c-5b4a-3210-1234-567890abcdef",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "iPad de Jean",
  "device_model": "iPad Pro",
  "os_version": "16.0",
  "app_version": "1.2.0",
  "push_token": "fcm:AbCdEfG123456...",
  "is_active": true
}
```

### Revoke Tokens

**Endpoint**: `POST /api/v1/auth/devices/revoke/`

**Description**: Révoque tous les tokens pour un appareil ou tous les appareils.

**Headers**:
- `Authorization: Bearer <access_token>`

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| device_id | string | Non | Identifiant de l'appareil (si omis, voir all_devices) |
| all_devices | boolean | Non | Si true, révoque les tokens pour tous les appareils |

**Exemple de requête**:

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

ou

```json
{
  "all_devices": true
}
```

**Exemple de réponse réussie** (200 OK):

```json
{
  "message": "Tokens révoqués pour l'appareil spécifié."
}
```

ou

```json
{
  "message": "Tous les tokens ont été révoqués."
}
```

### PKCE Authentication Flow

PKCE (Proof Key for Code Exchange) est une extension d'OAuth 2.0 qui protège contre les attaques par interception de code d'autorisation. Le flux comprend trois étapes :

#### 1. Initialiser PKCE

**Endpoint**: `POST /api/v1/auth/pkce/init/`

**Description**: Initialise le flux PKCE et retourne un code d'autorisation.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| code_challenge | string | Oui | Code challenge généré par le client |
| code_challenge_method | string | Oui | Méthode (S256 ou plain) |
| state | string | Non | État à conserver entre les requêtes |
| redirect_uri | string | Non | URI de redirection |
| scope | string | Non | Portée des permissions demandées |
| client_id | string | Oui | Identifiant client |

**Exemple de requête**:

```json
{
  "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  "code_challenge_method": "S256",
  "state": "random_state_string",
  "client_id": "mobile_app_client"
}
```

**Exemple de réponse réussie** (201 Created):

```json
{
  "auth_code": "aBcDeFgH1234567890",
  "expires_in": 600
}
```

#### 2. Autoriser PKCE

**Endpoint**: `POST /api/v1/auth/pkce/authorize/`

**Description**: Associe un utilisateur authentifié à une session PKCE.

**Headers**:
- `Authorization: Bearer <access_token>`

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| auth_code | string | Oui | Code d'autorisation obtenu à l'étape 1 |

**Exemple de requête**:

```json
{
  "auth_code": "aBcDeFgH1234567890"
}
```

**Exemple de réponse réussie** (200 OK):

```json
{
  "success": true,
  "message": "Autorisation accordée avec succès."
}
```

#### 3. Compléter PKCE

**Endpoint**: `POST /api/v1/auth/pkce/complete/`

**Description**: Échange un code d'autorisation et un code verifier contre des tokens.

**Paramètres de la requête**:

| Paramètre | Type | Requis | Description |
| --- | --- | --- | --- |
| auth_code | string | Oui | Code d'autorisation |
| code_verifier | string | Oui | Code verifier correspondant au code challenge |
| client_id | string | Oui | Identifiant client |

**Exemple de requête**:

```json
{
  "auth_code": "aBcDeFgH1234567890",
  "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
  "client_id": "mobile_app_client"
}
```

**Exemple de réponse réussie** (200 OK):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "username": "user123",
    "email": "user@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_joined": "2025-01-15T14:30:45Z",
    "is_active": true
  },
  "expires_in": 3600
}
```

## Modèles de Données

### RefreshToken

Stocke les tokens de rafraîchissement pour les sessions longues.

| Champ | Type | Description |
| --- | --- | --- |
| id | UUID | Identifiant unique |
| user | ForeignKey | Utilisateur associé |
| token | CharField | Token de rafraîchissement |
| expires_at | DateTimeField | Date d'expiration |
| issued_at | DateTimeField | Date d'émission |
| revoked | BooleanField | Indique si le token est révoqué |
| device_id | CharField | Identifiant de l'appareil (optionnel) |
| user_agent | TextField | User agent (optionnel) |
| ip_address | GenericIPAddressField | Adresse IP (optionnelle) |
| tenant | ForeignKey | Tenant associé (optionnel) |
| code_challenge | CharField | Code challenge PKCE (optionnel) |
| code_challenge_method | CharField | Méthode du code challenge (optionnel) |

### AccessTokenLog

Journal des tokens d'accès pour audit et sécurité.

| Champ | Type | Description |
| --- | --- | --- |
| id | UUID | Identifiant unique |
| user | ForeignKey | Utilisateur associé |
| issued_at | DateTimeField | Date d'émission |
| expires_at | DateTimeField | Date d'expiration |
| jti | CharField | JWT ID |
| device_id | CharField | Identifiant de l'appareil (optionnel) |
| user_agent | TextField | User agent (optionnel) |
| ip_address | GenericIPAddressField | Adresse IP (optionnelle) |
| revoked | BooleanField | Indique si le token est révoqué |
| revoked_at | DateTimeField | Date de révocation (optionnelle) |
| tenant | ForeignKey | Tenant associé (optionnel) |

### DeviceRegistration

Enregistrement des appareils pour les notifications push et la gestion de sécurité.

| Champ | Type | Description |
| --- | --- | --- |
| id | UUID | Identifiant unique |
| user | ForeignKey | Utilisateur associé |
| device_id | CharField | Identifiant unique de l'appareil |
| device_name | CharField | Nom convivial de l'appareil (optionnel) |
| device_model | CharField | Modèle de l'appareil (optionnel) |
| os_version | CharField | Version du système d'exploitation (optionnel) |
| app_version | CharField | Version de l'application (optionnel) |
| push_token | CharField | Token de notification push (optionnel) |
| is_active | BooleanField | Indique si l'appareil est actif |
| registered_at | DateTimeField | Date d'enregistrement |
| last_used_at | DateTimeField | Date de dernière utilisation |
| tenant | ForeignKey | Tenant associé (optionnel) |

### PKCESession

Session PKCE (Proof Key for Code Exchange) pour l'authentification mobile.

| Champ | Type | Description |
| --- | --- | --- |
| id | UUID | Identifiant unique |
| user | ForeignKey | Utilisateur associé (optionnel avant autorisation) |
| code_challenge | CharField | Code challenge PKCE |
| code_challenge_method | CharField | Méthode du code challenge |
| code_verifier | CharField | Code verifier (optionnel) |
| auth_code | CharField | Code d'autorisation |
| state | CharField | État (optionnel) |
| redirect_uri | URLField | URI de redirection (optionnel) |
| scope | CharField | Portée des permissions (optionnel) |
| client_id | CharField | Identifiant client |
| created_at | DateTimeField | Date de création |
| expires_at | DateTimeField | Date d'expiration |
| used | BooleanField | Indique si la session a été utilisée |
| tenant | ForeignKey | Tenant associé (optionnel) |

## Sécurité

### Multi-tenant

L'API prend en charge les déploiements multi-tenant. Le tenant peut être déterminé de plusieurs façons :

1. Par le domaine de la requête (via middleware)
2. Par un en-tête HTTP personnalisé (`X-Tenant-ID`)
3. Via le token JWT qui contient des claims tenant_id et tenant_name

### Gestion des tokens 

- **Rotation des tokens**: Les tokens d'accès expirent après 60 minutes par défaut
- **Révocation des tokens**: Support complet pour la révocation centralisée des tokens
- **Audit**: Journalisation complète de l'émission et de l'utilisation des tokens
- **Multi-appareils**: Un utilisateur peut avoir plusieurs sessions sur différents appareils
- **Révocation sélective**: Possibilité de révoquer les tokens pour un appareil spécifique

### PKCE

Pour les applications mobiles, l'API prend en charge le PKCE (Proof Key for Code Exchange) qui protège contre les attaques par interception de code d'autorisation :

1. L'application génère un code_verifier aléatoire et calcule le code_challenge
2. Le code_challenge est envoyé au serveur lors de l'initialisation
3. Après authentification, l'application envoie le code_verifier original
4. Le serveur valide que le code_verifier correspond au code_challenge

## Exemples de Code

### iOS (Swift)

Consultez le fichier exemple [iOS JWT Auth Example](/docs/api_examples/ios_jwt_auth_exemple.swift).

### Android (Kotlin)

Consultez le fichier exemple [Android JWT Auth Example](/docs/api_examples/android_jwt_auth_example.kt).

## Annexes

### Format des Tokens JWT

#### Access Token Claims

```json
{
  "token_type": "access",
  "exp": 1716403200,
  "iat": 1716399600,
  "jti": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "user_id": 123,
  "tenant_id": "ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj",
  "tenant_name": "demo"
}
```

#### Refresh Token Claims

```json
{
  "token_type": "refresh",
  "exp": 1718995200,
  "iat": 1716399600,
  "jti": "kkkkkkkk-llll-mmmm-nnnn-oooooooooooo",
  "user_id": 123
}
```

### Codes d'erreur

| Code HTTP | Erreur | Description |
| --- | --- | --- |
| 400 | Invalid request | Requête invalide (paramètres manquants ou incorrects) |
| 401 | Authentication failed | Échec de l'authentification (identifiants invalides) |
| 401 | Token expired | Le token a expiré |
| 401 | Token revoked | Le token a été révoqué |
| 403 | Insufficient permissions | Permissions insuffisantes |
| 404 | Not found | Ressource non trouvée |
| 500 | Server error | Erreur serveur |