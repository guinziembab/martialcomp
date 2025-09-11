# Guide d'implémentation de l'authentification sociale pour MartialComp

## Objectif

Intégrer l'authentification sociale à MartialComp pour permettre aux utilisateurs de s'inscrire et se connecter via des comptes tiers (Google, Facebook, Apple, etc.), améliorant ainsi l'expérience utilisateur et augmentant le taux de conversion des inscriptions.

## Avantages de l'authentification sociale

- **Simplification du processus d'inscription** : Réduction des frictions lors de l'enregistrement
- **Augmentation du taux de conversion** : +30% d'inscriptions en moyenne selon les études
- **Amélioration de la fiabilité des données** : Informations vérifiées par les fournisseurs sociaux
- **Renforcement de la sécurité** : Délégation de l'authentification à des services éprouvés
- **Accès à des données démographiques** : Informations complémentaires pour personnaliser l'expérience

## Architecture de la solution

### 1. Installation et configuration de django-allauth

Django-allauth est une bibliothèque complète qui gère l'authentification, l'enregistrement et la gestion des comptes sociaux pour Django.

#### 1.1 Installation

```bash
pip install django-allauth
```

Ajouter les dépendances à `requirements.txt` :

```
django-allauth>=0.54.0
```

#### 1.2 Configuration dans settings.py

```python
# settings.py

INSTALLED_APPS = [
    # Django apps existantes
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sites',
    
    # Applications django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Fournisseurs d'authentification sociale
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.apple',
    'allauth.socialaccount.providers.twitter',
    # Ajouter d'autres fournisseurs selon les besoins
    
    # Applications MartialComp existantes
    'competitions',
    # ...
]

MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # ...
]

# Paramètres d'authentification
AUTHENTICATION_BACKENDS = [
    # Nécessaire pour l'authentification par nom d'utilisateur dans Django admin
    'django.contrib.auth.backends.ModelBackend',
    
    # Backend d'authentification spécifique à django-allauth
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Configuration du site
SITE_ID = 1

# Paramètres django-allauth
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Utiliser l'email plutôt que le nom d'utilisateur
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False  # Rendre le nom d'utilisateur optionnel
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 'mandatory', 'optional', ou 'none'
ACCOUNT_ADAPTER = 'competitions.adapters.MartialCompAccountAdapter'  # Adapter personnalisé
SOCIALACCOUNT_ADAPTER = 'competitions.adapters.MartialCompSocialAccountAdapter'  # Adapter personnalisé

# Configuration de la redirection après authentification
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Configuration pour les fournisseurs sociaux
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'your-client-id',
            'secret': 'your-client-secret',
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        'APP': {
            'client_id': 'your-client-id',
            'secret': 'your-client-secret',
            'key': ''
        },
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'picture',
        ],
    },
    'apple': {
        'APP': {
            'client_id': 'your-client-id',
            'secret': 'your-client-secret',
            'key': '',
            'certificate_key': ''
        },
        'SCOPE': ['email', 'name'],
    },
}
```

#### 1.3 Configuration des URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... URLs existantes
    path('accounts/', include('allauth.urls')),
    # ... autres URLs
]
```

### 2. Création des adaptateurs personnalisés

Les adaptateurs permettent de personnaliser le processus d'inscription et de connexion.

#### 2.1 Adapter pour les comptes standard

```python
# competitions/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class MartialCompAccountAdapter(DefaultAccountAdapter):
    """Adapter personnalisé pour gérer le processus d'inscription standard."""
    
    def save_user(self, request, user, form, commit=True):
        """
        Personnalise la création d'un nouvel utilisateur.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Ajouter des champs supplémentaires selon le besoin
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
            
            # Créer un profil utilisateur si nécessaire
            from competitions.models import UserProfile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'spectator',
                    'onboarding_step': 'role_selection',
                    'onboarding_completed': False
                }
            )
        
        return user
    
    def get_signup_redirect_url(self, request):
        """
        Redirige vers le processus d'onboarding après l'inscription.
        """
        return settings.SIGNUP_REDIRECT_URL or '/onboarding/role/'
```

#### 2.2 Adapter pour les comptes sociaux

```python
# competitions/adapters.py (suite)
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

class MartialCompSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter personnalisé pour gérer le processus d'inscription via comptes sociaux."""
    
    def populate_user(self, request, sociallogin, data):
        """
        Personnalise la création d'un utilisateur à partir des données sociales.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Récupérer des informations supplémentaires selon le fournisseur
        if sociallogin.account.provider == 'google':
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
        elif sociallogin.account.provider == 'facebook':
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Personnalise la sauvegarde d'un utilisateur créé via réseau social.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Créer un profil utilisateur si nécessaire
        from competitions.models import UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'spectator',
                'onboarding_step': 'role_selection',
                'onboarding_completed': False
            }
        )
        
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirige vers le processus d'onboarding après la connexion sociale.
        """
        # Vérifier si l'utilisateur a déjà complété l'onboarding
        if hasattr(socialaccount.user, 'profile') and socialaccount.user.profile.onboarding_completed:
            return settings.LOGIN_REDIRECT_URL
        else:
            return settings.SIGNUP_REDIRECT_URL or '/onboarding/role/'
```

### 3. Personnalisation des templates d'authentification

#### 3.1 Template de connexion

Créer le fichier `templates/account/login.html` :

```html
{% extends "base.html" %}
{% load i18n %}
{% load account socialaccount %}
{% load static %}

{% block title %}{% trans "Connexion" %} | MartialComp{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow">
                <div class="card-body p-4">
                    <h2 class="card-title text-center mb-4">{% trans "Connexion" %}</h2>
                    
                    {% if messages %}
                    <div class="messages mb-4">
                        {% for message in messages %}
                        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}

                    <div class="social-login mb-4">
                        <p class="text-center mb-3">{% trans "Se connecter avec" %}</p>
                        <div class="d-flex justify-content-center gap-3 mb-3">
                            {% get_providers as socialaccount_providers %}
                            {% for provider in socialaccount_providers %}
                                {% if provider.id == "google" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-danger">
                                    <i class="fab fa-google me-2"></i>Google
                                </a>
                                {% elif provider.id == "facebook" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-primary">
                                    <i class="fab fa-facebook-f me-2"></i>Facebook
                                </a>
                                {% elif provider.id == "apple" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-dark">
                                    <i class="fab fa-apple me-2"></i>Apple
                                </a>
                                {% endif %}
                            {% endfor %}
                        </div>
                    </div>

                    <div class="separator my-4">
                        <div class="line"></div>
                        <div class="or-text">{% trans "ou" %}</div>
                        <div class="line"></div>
                    </div>

                    <form class="login" method="POST" action="{% url 'account_login' %}">
                        {% csrf_token %}
                        
                        <div class="mb-3">
                            <label for="id_login" class="form-label">{% trans "E-mail" %}</label>
                            <input type="email" name="login" placeholder="{% trans 'E-mail' %}" autocomplete="email" required id="id_login" class="form-control">
                        </div>
                        
                        <div class="mb-3">
                            <label for="id_password" class="form-label">{% trans "Mot de passe" %}</label>
                            <input type="password" name="password" placeholder="{% trans 'Mot de passe' %}" autocomplete="current-password" required id="id_password" class="form-control">
                        </div>
                        
                        <div class="mb-3 form-check">
                            <input type="checkbox" name="remember" id="id_remember" class="form-check-input">
                            <label for="id_remember" class="form-check-label">{% trans "Se souvenir de moi" %}</label>
                        </div>
                        
                        {% if redirect_field_value %}
                        <input type="hidden" name="{{ redirect_field_name }}" value="{{ redirect_field_value }}" />
                        {% endif %}
                        
                        <div class="d-grid">
                            <button class="btn btn-primary" type="submit">{% trans "Se connecter" %}</button>
                        </div>
                    </form>

                    <div class="text-center mt-3">
                        <p class="mb-1">
                            <a href="{% url 'account_reset_password' %}" class="text-decoration-none">
                                {% trans "Mot de passe oublié ?" %}
                            </a>
                        </p>
                        <p class="mb-0">
                            {% trans "Pas encore inscrit ?" %}
                            <a href="{% url 'account_signup' %}" class="text-decoration-none">
                                {% trans "Créer un compte" %}
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .separator {
        display: flex;
        align-items: center;
    }
    
    .separator .line {
        flex: 1;
        height: 1px;
        background-color: #dee2e6;
    }
    
    .separator .or-text {
        padding: 0 1rem;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
{% endblock %}
```

#### 3.2 Template d'inscription

Créer le fichier `templates/account/signup.html` :

```html
{% extends "base.html" %}
{% load i18n %}
{% load account socialaccount %}
{% load static %}

{% block title %}{% trans "Inscription" %} | MartialComp{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow">
                <div class="card-body p-4">
                    <h2 class="card-title text-center mb-4">{% trans "Créer un compte" %}</h2>
                    
                    {% if messages %}
                    <div class="messages mb-4">
                        {% for message in messages %}
                        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}

                    <div class="social-signup mb-4">
                        <p class="text-center mb-3">{% trans "S'inscrire avec" %}</p>
                        <div class="d-flex justify-content-center gap-3 mb-3">
                            {% get_providers as socialaccount_providers %}
                            {% for provider in socialaccount_providers %}
                                {% if provider.id == "google" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-danger">
                                    <i class="fab fa-google me-2"></i>Google
                                </a>
                                {% elif provider.id == "facebook" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-primary">
                                    <i class="fab fa-facebook-f me-2"></i>Facebook
                                </a>
                                {% elif provider.id == "apple" %}
                                <a href="{% provider_login_url provider.id process='login' %}" class="btn btn-outline-dark">
                                    <i class="fab fa-apple me-2"></i>Apple
                                </a>
                                {% endif %}
                            {% endfor %}
                        </div>
                    </div>

                    <div class="separator my-4">
                        <div class="line"></div>
                        <div class="or-text">{% trans "ou" %}</div>
                        <div class="line"></div>
                    </div>

                    <form class="signup" id="signup_form" method="post" action="{% url 'account_signup' %}">
                        {% csrf_token %}
                        
                        <div class="row mb-3">
                            <div class="col">
                                <label for="id_first_name" class="form-label">{% trans "Prénom" %}</label>
                                <input type="text" name="first_name" placeholder="{% trans 'Prénom' %}" required id="id_first_name" class="form-control">
                            </div>
                            <div class="col">
                                <label for="id_last_name" class="form-label">{% trans "Nom" %}</label>
                                <input type="text" name="last_name" placeholder="{% trans 'Nom' %}" required id="id_last_name" class="form-control">
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="id_email" class="form-label">{% trans "E-mail" %}</label>
                            <input type="email" name="email" placeholder="{% trans 'E-mail' %}" autocomplete="email" required id="id_email" class="form-control">
                        </div>
                        
                        <div class="mb-3">
                            <label for="id_password1" class="form-label">{% trans "Mot de passe" %}</label>
                            <input type="password" name="password1" placeholder="{% trans 'Mot de passe' %}" autocomplete="new-password" required id="id_password1" class="form-control">
                        </div>
                        
                        <div class="mb-3">
                            <label for="id_password2" class="form-label">{% trans "Confirmer le mot de passe" %}</label>
                            <input type="password" name="password2" placeholder="{% trans 'Confirmer le mot de passe' %}" autocomplete="new-password" required id="id_password2" class="form-control">
                        </div>
                        
                        <div class="mb-3 form-check">
                            <input type="checkbox" name="terms" id="id_terms" class="form-check-input" required>
                            <label for="id_terms" class="form-check-label">
                                {% blocktrans %}J'accepte les <a href="/terms/" target="_blank">conditions d'utilisation</a> et la <a href="/privacy/" target="_blank">politique de confidentialité</a>{% endblocktrans %}
                            </label>
                        </div>
                        
                        {% if redirect_field_value %}
                        <input type="hidden" name="{{ redirect_field_name }}" value="{{ redirect_field_value }}" />
                        {% endif %}
                        
                        <div class="d-grid">
                            <button class="btn btn-primary" type="submit">{% trans "S'inscrire" %}</button>
                        </div>
                    </form>

                    <div class="text-center mt-3">
                        <p class="mb-0">
                            {% trans "Déjà inscrit ?" %}
                            <a href="{% url 'account_login' %}" class="text-decoration-none">
                                {% trans "Se connecter" %}
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .separator {
        display: flex;
        align-items: center;
    }
    
    .separator .line {
        flex: 1;
        height: 1px;
        background-color: #dee2e6;
    }
    
    .separator .or-text {
        padding: 0 1rem;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
{% endblock %}
```

### 4. Configuration des fournisseurs d'authentification sociale

#### 4.1 Configuration Google OAuth2

1. Accéder à la [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Aller dans "APIs & Services" > "Credentials"
4. Cliquer sur "Create Credentials" > "OAuth client ID"
5. Sélectionner "Web application" comme type d'application
6. Configurer les "Authorized JavaScript origins" avec votre domaine (ex: https://martialcomp.com)
7. Configurer les "Authorized redirect URIs" avec l'URL de callback (ex: https://martialcomp.com/accounts/google/login/callback/)
8. Copier le Client ID et le Client Secret générés
9. Ajouter ces identifiants dans le fichier `settings.py` :

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'votre-client-id',
            'secret': 'votre-client-secret',
            'key': ''
        },
        # ...
    },
    # ...
}
```

#### 4.2 Configuration Facebook OAuth2

1. Accéder au [Facebook Developer Portal](https://developers.facebook.com/)
2. Créer une nouvelle application ou sélectionner une application existante
3. Aller dans "Settings" > "Basic"
4. Noter l'App ID et l'App Secret
5. Aller dans "Facebook Login" > "Settings"
6. Ajouter l'URL de redirection OAuth (ex: https://martialcomp.com/accounts/facebook/login/callback/)
7. Ajouter les domaines valides dans "Valid OAuth Redirect URIs"
8. Ajouter ces identifiants dans le fichier `settings.py` :

```python
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'APP': {
            'client_id': 'votre-app-id',
            'secret': 'votre-app-secret',
            'key': ''
        },
        # ...
    },
    # ...
}
```

#### 4.3 Configuration Apple Sign In

1. Accéder à l'[Apple Developer Portal](https://developer.apple.com/)
2. Aller dans "Certificates, Identifiers & Profiles"
3. Créer un nouvel "App ID" avec la capacité "Sign In with Apple"
4. Créer un "Services ID" pour le web et configurer les domaines et URLs de redirection
5. Générer une clé privée pour "Sign in with Apple"
6. Ajouter ces identifiants dans le fichier `settings.py` :

```python
SOCIALACCOUNT_PROVIDERS = {
    'apple': {
        'APP': {
            'client_id': 'votre-services-id',
            'secret': 'votre-clé-privée',
            'key': 'votre-app-id',
            'certificate_key': 'votre-certificat'
        },
        # ...
    },
    # ...
}
```

### 5. Intégration avec le processus d'onboarding existant

Pour assurer une intégration fluide avec le processus d'onboarding existant de MartialComp, il faut adapter le flux de redirection après l'authentification sociale.

#### 5.1 Middleware pour la gestion du flux d'onboarding

```python
# competitions/middleware.py

class OnboardingRedirectMiddleware:
    """
    Middleware pour rediriger les utilisateurs vers le processus d'onboarding
    après une connexion réussie si nécessaire.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Exclure certaines URLs du processus de redirection
            excluded_paths = [
                '/onboarding/',
                '/accounts/logout/',
                '/admin/',
                '/static/',
                '/media/',
                '/api/',
            ]
            
            current_path = request.path
            
            # Vérifier si le chemin actuel est exclu
            if not any(current_path.startswith(path) for path in excluded_paths):
                # Vérifier si l'utilisateur a complété l'onboarding
                if hasattr(request.user, 'profile') and not request.user.profile.onboarding_completed:
                    # Rediriger vers l'étape d'onboarding appropriée
                    onboarding_step = request.user.profile.onboarding_step or 'role_selection'
                    redirect_url = f'/onboarding/{onboarding_step}/'
                    
                    if current_path != redirect_url:
                        from django.shortcuts import redirect
                        return redirect(redirect_url)
        
        return response
```

Ajouter ce middleware à la configuration dans `settings.py` :

```python
MIDDLEWARE = [
    # ...
    'competitions.middleware.OnboardingRedirectMiddleware',
    # ...
]
```

#### 5.2 Formulaire personnalisé pour l'onboarding social

Pour collecter des informations supplémentaires après une inscription sociale, créer un formulaire spécifique :

```python
# competitions/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _

class SocialSignupForm(forms.Form):
    """
    Formulaire pour collecter des informations supplémentaires
    lors de l'inscription via réseaux sociaux.
    """
    
    birth_date = forms.DateField(
        label=_("Date de naissance"),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        help_text=_("Nécessaire pour déterminer les catégories d'âge pour les compétitions.")
    )
    
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=20,
        required=False,
        help_text=_("Facultatif. Utilisé uniquement pour les communications importantes.")
    )
    
    def __init__(self, *args, **kwargs):
        self.sociallogin = kwargs.pop('sociallogin', None)
        super().__init__(*args, **kwargs)
```

#### 5.3 Vue personnalisée pour compléter le profil social

```python
# competitions/views/social.py

from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from competitions.forms import SocialSignupForm
from competitions.models import UserProfile

class SocialProfileCompleteView(LoginRequiredMixin, FormView):
    """
    Vue pour compléter le profil utilisateur après une inscription sociale.
    """
    
    template_name = 'competitions/social_profile_complete.html'
    form_class = SocialSignupForm
    success_url = reverse_lazy('competitions:onboarding:role_selection')
    
    def form_valid(self, form):
        user = self.request.user
        
        # Mettre à jour le profil utilisateur avec les informations supplémentaires
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Enregistrer la date de naissance
        profile.birth_date = form.cleaned_data['birth_date']
        
        # Enregistrer le numéro de téléphone s'il est fourni
        phone_number = form.cleaned_data.get('phone_number')
        if phone_number:
            profile.phone_number = phone_number
        
        # Mettre à jour l'étape d'onboarding
        profile.onboarding_step = 'role_selection'
        profile.save()
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Compléter votre profil")
        context['social_account'] = self.request.user.socialaccount_set.first()
        return context
```

Ajouter cette vue aux URLs :

```python
# competitions/urls.py

from competitions.views.social import SocialProfileCompleteView

urlpatterns = [
    # ...
    path('social/complete-profile/', SocialProfileCompleteView.as_view(), name='social_complete_profile'),
    # ...
]
```

### 6. Sécurité et protection des données

#### 6.1 HTTPS et HSTS

Assurer que toute l'application est servie sur HTTPS pour protéger les données d'authentification :

```python
# settings.py

# Forcer HTTPS
SECURE_SSL_REDIRECT = True

# Paramètres HSTS
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies sécurisés
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 6.2 Protection des identifiants sociaux

Stocker les identifiants de manière sécurisée en utilisant les variables d'environnement :

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        # ...
    },
    'facebook': {
        'APP': {
            'client_id': os.environ.get('FACEBOOK_APP_ID'),
            'secret': os.environ.get('FACEBOOK_APP_SECRET'),
            'key': ''
        },
        # ...
    },
    'apple': {
        'APP': {
            'client_id': os.environ.get('APPLE_SERVICES_ID'),
            'secret': os.environ.get('APPLE_PRIVATE_KEY'),
            'key': os.environ.get('APPLE_APP_ID'),
            'certificate_key': os.environ.get('APPLE_CERTIFICATE')
        },
        # ...
    },
}
```

#### 6.3 Protection contre les attaques CSRF

Django-allauth intègre déjà une protection CSRF, mais il est important de la maintenir activée :

```python
# settings.py

# Protection CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True
```

### 7. Création des records dans la base de données

Pour finaliser la configuration, il faut créer les enregistrements dans la base de données Django.

#### 7.1 Configuration du site

```python
# Script à exécuter une fois
from django.contrib.sites.models import Site

# Mettre à jour le site par défaut
site = Site.objects.get(id=1)
site.domain = 'martialcomp.com'
site.name = 'MartialComp'
site.save()
```

#### 7.2 Configuration des applications sociales

Pour Google :

```python
# Script à exécuter une fois pour chaque fournisseur
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Créer l'application Google
google_app = SocialApp.objects.create(
    provider='google',
    name='Google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    secret=os.environ.get('GOOGLE_CLIENT_SECRET')
)
google_app.sites.add(Site.objects.get(id=1))
google_app.save()
```

Répéter pour Facebook, Apple et autres fournisseurs.

### 8. Tests et validation

#### 8.1 Tests unitaires

Créer des tests pour valider le fonctionnement de l'authentification sociale :

```python
# competitions/tests/test_social_auth.py

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.sites.models import Site

User = get_user_model()

@override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True)
class SocialAuthTest(TestCase):
    def setUp(self):
        # Créer un site pour les tests
        self.site = Site.objects.create(domain='testserver', name='testserver')
        
        # Créer une application sociale pour les tests
        self.google_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-client-secret'
        )
        self.google_app.sites.add(self.site)
    
    def test_social_login_redirect(self):
        """Tester la redirection vers le fournisseur OAuth."""
        response = self.client.get(reverse('socialaccount_login', kwargs={'provider': 'google'}))
        self.assertEqual(response.status_code, 302)  # Doit rediriger
    
    # Autres tests...
```

#### 8.2 Tests fonctionnels

Créer des tests fonctionnels avec Selenium pour tester le flux d'authentification complet :

```python
# competitions/tests/test_functional_social_auth.py

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SocialAuthFunctionalTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Chrome()
        cls.selenium.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def test_social_login_buttons_exist(self):
        """Vérifier que les boutons de connexion sociale sont présents."""
        self.selenium.get(f'{self.live_server_url}/accounts/login/')
        
        # Vérifier que les boutons existent
        google_button = self.selenium.find_element(By.XPATH, "//a[contains(@href, '/accounts/google/login/')]")
        facebook_button = self.selenium.find_element(By.XPATH, "//a[contains(@href, '/accounts/facebook/login/')]")
        
        self.assertIsNotNone(google_button)
        self.assertIsNotNone(facebook_button)
    
    # Autres tests...
```

### 9. Plan d'implémentation

#### Phase 1 : Configuration et intégration de base

1. Installer django-allauth et configurer les paramètres de base
2. Créer les adaptateurs personnalisés pour MartialComp
3. Personnaliser les templates de connexion et d'inscription
4. Créer les applications sociales dans les consoles développeur (Google, Facebook, Apple)
5. Configurer les identifiants des fournisseurs sociaux dans l'application

#### Phase 2 : Intégration avec l'onboarding

1. Créer le middleware de redirection d'onboarding
2. Développer le formulaire et la vue pour compléter le profil après inscription sociale
3. Intégrer le flux social avec le processus d'onboarding existant
4. Tester les différents chemins d'onboarding (inscription directe, sociale, connexion sociale existante)

#### Phase 3 : Tests et déploiement

1. Écrire des tests unitaires et fonctionnels
2. Tester l'ensemble du processus sur l'environnement de staging
3. Corriger les éventuels problèmes identifiés
4. Déployer sur l'environnement de production
5. Surveiller les métriques d'inscription et de conversion

### 10. Bonnes pratiques

1. **Minimiser les informations demandées** : Ne demander que les informations essentielles lors de l'inscription sociale
2. **Transparence** : Informer clairement les utilisateurs des données récupérées via les réseaux sociaux
3. **Respect de la vie privée** : Ne pas publier sur les réseaux sociaux sans consentement explicite
4. **Cohérence visuelle** : Maintenir la cohérence avec la charte graphique de MartialComp
5. **Optimisation mobile** : S'assurer que le processus fonctionne parfaitement sur les appareils mobiles
6. **Feedback utilisateur** : Fournir des retours clairs en cas d'erreur ou de succès
7. **Mesure de performance** : Suivre les taux de conversion pour chaque fournisseur social

## Ressources utiles

- [Documentation django-allauth](https://django-allauth.readthedocs.io/)
- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login/)
- [Sign in with Apple Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Customizing django-allauth](https://django-allauth.readthedocs.io/en/latest/advanced.html)

## Conclusion

L'intégration de l'authentification sociale dans MartialComp permettra d'améliorer significativement l'expérience d'inscription et de connexion des utilisateurs. En suivant ce guide d'implémentation, vous pourrez offrir une expérience fluide et sécurisée, tout en maintenant la cohérence avec le processus d'onboarding existant.

Cette approche permettra également de collecter des informations de profil plus précises et vérifiées, tout en réduisant les frictions lors de l'inscription, ce qui devrait se traduire par une augmentation significative du taux de conversion.
