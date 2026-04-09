# 🥋 MartialComp - Guide d'Implémentation

Ce dossier contient tous les fichiers nécessaires pour implémenter:
1. **Authentification Sociale** (Google, Facebook, Apple)
2. **Système de Rôles Organisationnels** avec switch de contexte

## 📁 Structure des Fichiers

```
martialcomp_implementation/
├── adapters.py                    # Adaptateurs django-allauth personnalisés
├── social_auth_api.py             # Endpoints API pour mobile
├── organizational_roles.py        # Modèles ClubMember, OrganizationalRole
├── permissions_definitions.py     # Définitions des permissions
├── permissions_decorators.py      # Décorateurs @club_permission_required
├── context_middleware.py          # Middleware de contexte organisationnel
├── role_switch_views.py           # Vues de switch de contexte
├── migration_organizational_roles.py  # Migration des rôles par défaut
├── auth_urls.py                   # Configuration des URLs
├── context_switcher.html          # Template du dropdown de switch
├── mobile_socialAuth.js           # Service auth sociale React Native
└── mobile_LoginScreen.js          # Écran de connexion mobile
```

---

## 🚀 Installation Rapide

### 1. Dépendances Python

```bash
pip install django-allauth dj-rest-auth djangorestframework-simplejwt PyJWT requests
```

### 2. Configuration settings.py

```python
INSTALLED_APPS = [
    # ... apps existantes ...
    'django.contrib.sites',
    
    # Django Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.apple',
    
    # REST API
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'rest_framework_simplejwt',
]

MIDDLEWARE = [
    # ... middleware existant ...
    'allauth.account.middleware.AccountMiddleware',
    'competitions.middleware.context.OrganizationalContextMiddleware',  # APRÈS AuthenticationMiddleware
]

SITE_ID = 1

# Allauth
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_ADAPTER = 'competitions.adapters.MartialCompAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'competitions.adapters.MartialCompSocialAccountAdapter'

# Variables d'environnement requises
import os
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
        },
        'SCOPE': ['profile', 'email'],
    },
    'facebook': {
        'APP': {
            'client_id': FACEBOOK_APP_ID,
            'secret': FACEBOOK_APP_SECRET,
        },
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
    },
}
```

### 3. Copier les fichiers

```bash
# Backend
cp adapters.py competitions/
cp organizational_roles.py competitions/models/
cp permissions_definitions.py competitions/permissions/
cp permissions_decorators.py competitions/permissions/
cp context_middleware.py competitions/middleware/
cp role_switch_views.py competitions/views/
cp social_auth_api.py competitions/api/
cp auth_urls.py competitions/api/

# Templates
cp context_switcher.html templates/includes/

# Migration
cp migration_organizational_roles.py competitions/migrations/0XXX_create_organizational_roles.py
# Renommer avec le bon numéro et mettre à jour les dépendances
```

### 4. Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer les applications dans les consoles développeur

| Provider | Console | Callback URL |
|----------|---------|--------------|
| Google | [console.cloud.google.com](https://console.cloud.google.com) | `https://martialcomp.com/accounts/google/login/callback/` |
| Facebook | [developers.facebook.com](https://developers.facebook.com) | `https://martialcomp.com/accounts/facebook/login/callback/` |
| Apple | [developer.apple.com](https://developer.apple.com) | `https://martialcomp.com/accounts/apple/login/callback/` |

---

## 📱 Configuration Mobile (React Native)

### 1. Dépendances npm

```bash
npm install expo-auth-session expo-apple-authentication @react-native-async-storage/async-storage
```

### 2. Variables d'environnement (.env)

```
EXPO_PUBLIC_API_BASE_URL=https://martialcomp.com
EXPO_PUBLIC_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=xxx.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=xxx.apps.googleusercontent.com
EXPO_PUBLIC_FACEBOOK_APP_ID=xxx
```

### 3. Copier les fichiers

```bash
cp mobile_socialAuth.js src/services/socialAuth.js
cp mobile_LoginScreen.js src/screens/auth/LoginScreen.js
```

---

## 🎭 Système de Rôles

### Rôles Disponibles (basés sur l'interface existante)

| Rôle | Code | Hiérarchie | Permissions |
|------|------|------------|-------------|
| Propriétaire | `owner` | 1 | Toutes (`*`) |
| Administrateur | `admin` | 2 | Gestion complète sauf transfert |
| Gestionnaire | `manager` | 3 | Membres + Compétitions |
| Trésorier | `treasurer` | 4 | Finances complètes |
| Comptable | `accountant` | 5 | Finances lecture seule |
| Secrétaire | `secretary` | 5 | Administration + Communication |
| Entraîneur | `coach` | 6 | Cours + Pratiquants |
| Juge | `judge` | 7 | Arbitrage |
| Membre | `member` | 10 | Lecture seule |

### Utilisation des Décorateurs

```python
from competitions.permissions import club_permission_required, Permissions

@login_required
@club_permission_required(Permissions.FINANCE_VIEW)
def treasury_view(request):
    # L'utilisateur a la permission finance.view
    pass

@login_required
@any_permission_required(Permissions.FINANCE_VIEW, Permissions.FINANCE_EDIT)
def finance_dashboard(request):
    # L'utilisateur a au moins une des permissions
    pass
```

### Vérification dans les Templates

```html
{% if 'finance.view' in user_permissions %}
    <a href="{% url 'finances:dashboard' %}">Finances</a>
{% endif %}

{% if '*' in user_permissions or 'roles.assign' in user_permissions %}
    <a href="{% url 'club:roles' %}">Gérer les rôles</a>
{% endif %}
```

---

## 🔄 Intégration du Context Switcher

### Dans base.html

```html
<nav class="navbar">
    <!-- ... autres éléments ... -->
    
    <div class="navbar-nav ms-auto">
        {% include "includes/context_switcher.html" %}
        
        <!-- Menu utilisateur -->
        <div class="dropdown">
            <!-- ... -->
        </div>
    </div>
</nav>
```

### API de Switch

```javascript
// Depuis JavaScript
fetch('/api/contexts/switch/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        type: 'organizational',  // ou 'practitioner', 'judge', 'federation'
        id: membershipId         // ID du ClubMember ou null
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect_url;
    }
});
```

---

## ✅ Checklist de Déploiement

### Authentification Sociale
- [ ] Installer les dépendances Python
- [ ] Configurer INSTALLED_APPS et MIDDLEWARE
- [ ] Créer les apps Google/Facebook/Apple
- [ ] Configurer les variables d'environnement
- [ ] Tester les callbacks OAuth

### Système de Rôles
- [ ] Copier les fichiers de modèles
- [ ] Exécuter les migrations
- [ ] Ajouter le middleware de contexte
- [ ] Intégrer le context_switcher.html
- [ ] Tester les permissions sur les vues
- [ ] Migrer les ClubAdministrator existants

### Mobile
- [ ] Installer les dépendances npm
- [ ] Configurer les variables d'environnement
- [ ] Intégrer le service d'authentification
- [ ] Tester sur iOS et Android

---

## 🆘 Support

En cas de problème:
1. Vérifier les logs Django
2. Tester les endpoints avec curl/Postman
3. Vérifier les permissions dans l'admin Django
4. S'assurer que le middleware est dans le bon ordre

---

*Document généré le 3 février 2026*
