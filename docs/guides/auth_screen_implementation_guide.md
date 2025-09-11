# Guide technique d'implémentation de l'écran d'authentification MartialComp

## Introduction

Ce guide détaille l'implémentation technique d'un nouvel écran d'authentification pour MartialComp, inspiré par des interfaces modernes d'authentification. L'objectif est de créer une expérience utilisateur fluide et professionnelle tout en supportant à la fois l'authentification traditionnelle par email et les options d'authentification sociale.

## Table des matières

1. [Maquette et design](#maquette-et-design)
2. [Structure HTML](#structure-html)
3. [Styles CSS](#styles-css)
4. [Configuration Django](#configuration-django)
5. [Intégration de l'authentification sociale](#intégration-de-lauthentification-sociale)
6. [Affichage contextuel des informations de profil](#affichage-contextuel-des-informations-de-profil)
7. [Responsive design](#responsive-design)
8. [Tests et validation](#tests-et-validation)
9. [Déploiement](#déploiement)

## Maquette et design

![Maquette d'écran d'authentification MartialComp](https://example.com/mockup-auth-screen.png)

L'écran d'authentification comprend les éléments suivants :
- **En-tête** : "Sign in to MartialComp" avec le logo MartialComp
- **Informations du profil** : Détails du profil "Responsable de club" avec emplacement et statut
- **Formulaire d'email** : Champ unique pour la saisie de l'email
- **Bouton de continuation** : Pour passer à l'étape suivante
- **Options d'authentification sociale** : Connexion via Google, Apple, LinkedIn et Facebook
- **Pied de page** : Liens vers les conditions d'utilisation et la politique de confidentialité

## Structure HTML

```html
<!-- templates/auth/login.html -->
{% extends "base.html" %}
{% load i18n static %}

{% block content %}
<div class="auth-container">
    <div class="auth-header">
        <img src="{% static 'img/logo-martialcomp.png' %}" alt="MartialComp" class="auth-logo">
        <h1>{% trans "Sign in to MartialComp" %}</h1>
    </div>
    
    {% if profile_info %}
    <div class="profile-info">
        <h2>{{ profile_info.role }}</h2>
        <div class="profile-meta">
            <span class="profile-location">{{ profile_info.location }}</span>
            <span class="profile-badge {{ profile_info.status_class }}">{{ profile_info.status }}</span>
        </div>
        {% if profile_info.valid_dates %}
        <div class="profile-dates">
            <span>{% trans "Available from" %} {{ profile_info.valid_dates.start }} - {{ profile_info.valid_dates.end }}</span>
        </div>
        {% endif %}
    </div>
    {% endif %}
    
    <form method="post" action="{% url 'auth:email_login' %}" class="auth-form">
        {% csrf_token %}
        <div class="form-group">
            <input type="email" name="email" class="form-control" placeholder="{% trans 'Your email...' %}" required>
        </div>
        <button type="submit" class="btn btn-primary btn-block">{% trans 'Continue' %}</button>
    </form>
    
    <div class="separator">{% trans 'or' %}</div>
    
    <div class="social-auth">
        <a href="{% url 'social:begin' 'google-oauth2' %}" class="btn-social btn-google">
            <img src="{% static 'img/icons/google.svg' %}" alt="Google">
            <span>{% trans 'Sign in with Google' %}</span>
        </a>
        <a href="{% url 'social:begin' 'apple-id' %}" class="btn-social btn-apple">
            <img src="{% static 'img/icons/apple.svg' %}" alt="Apple">
            <span>{% trans 'Sign in with Apple' %}</span>
        </a>
        <a href="{% url 'social:begin' 'linkedin-oauth2' %}" class="btn-social btn-linkedin">
            <img src="{% static 'img/icons/linkedin.svg' %}" alt="LinkedIn">
            <span>{% trans 'Sign in with LinkedIn' %}</span>
        </a>
        <a href="{% url 'social:begin' 'facebook' %}" class="btn-social btn-facebook">
            <img src="{% static 'img/icons/facebook.svg' %}" alt="Facebook">
            <span>{% trans 'Sign in with Facebook' %}</span>
        </a>
    </div>
    
    <div class="auth-footer">
        <a href="{% url 'legal:terms' %}">{% trans 'Terms of Use' %}</a> &amp; 
        <a href="{% url 'legal:privacy' %}">{% trans 'Privacy Policy' %}</a>
    </div>
    
    {% if not profile_info %}
    <div class="auth-register-link">
        <p>{% trans 'Not yet registered?' %} <a href="{% url 'auth:register' %}">{% trans 'Create an account' %}</a></p>
    </div>
    {% endif %}
</div>
{% endblock %}
```

## Styles CSS

```css
/* static/css/auth.css */

/* Container principal */
.auth-container {
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    background-color: #fff;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* En-tête avec logo */
.auth-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 1.5rem;
    text-align: center;
}

.auth-logo {
    width: 64px;
    height: 64px;
    margin-bottom: 1rem;
}

.auth-header h1 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #111827;
    margin: 0.5rem 0;
}

/* Informations de profil */
.profile-info {
    background-color: #F9FAFB;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    text-align: center;
}

.profile-info h2 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    margin: 0 0 0.5rem 0;
}

.profile-meta {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.profile-location {
    font-size: 0.875rem;
    color: #4B5563;
}

.profile-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 4px;
    text-transform: uppercase;
    background-color: #6941C6;
    color: white;
}

.profile-badge.active {
    background-color: #10B981;
}

.profile-badge.pending {
    background-color: #F59E0B;
}

.profile-dates {
    font-size: 0.75rem;
    color: #6B7280;
}

/* Formulaire */
.auth-form {
    margin-bottom: 1.5rem;
}

.form-group {
    margin-bottom: 1rem;
}

.form-control {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    font-size: 0.875rem;
    transition: border-color 0.15s ease-in-out;
}

.form-control:focus {
    border-color: #6941C6;
    outline: none;
    box-shadow: 0 0 0 3px rgba(105, 65, 198, 0.1);
}

.btn-primary {
    width: 100%;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    background-color: #F3F4F6;
    color: #374151;
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    transition: background-color 0.15s ease-in-out;
    border: none;
}

.btn-primary:hover {
    background-color: #E5E7EB;
}

/* Séparateur */
.separator {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 1.5rem 0;
    color: #6B7280;
    font-size: 0.875rem;
}

.separator::before,
.separator::after {
    content: "";
    flex: 1;
    border-bottom: 1px solid #E5E7EB;
}

.separator::before {
    margin-right: 0.5rem;
}

.separator::after {
    margin-left: 0.5rem;
}

/* Boutons d'authentification sociale */
.social-auth {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.btn-social {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid #E5E7EB;
    background-color: white;
    color: #111827;
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    transition: background-color 0.15s ease-in-out;
}

.btn-social:hover {
    background-color: #F9FAFB;
}

.btn-social img {
    width: 18px;
    height: 18px;
}

/* Pied de page */
.auth-footer {
    text-align: center;
    font-size: 0.75rem;
    color: #6B7280;
    margin-top: 2rem;
}

.auth-footer a {
    color: #6B7280;
    text-decoration: underline;
}

.auth-register-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.875rem;
}

.auth-register-link a {
    color: #6941C6;
    font-weight: 500;
    text-decoration: none;
}

/* Responsive design */
@media (max-width: 480px) {
    .auth-container {
        margin: 0;
        border-radius: 0;
        padding: 1.5rem;
        max-width: 100%;
        min-height: 100vh;
    }
}
```

## Configuration Django

### Configuration de la vue

```python
# auth/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import gettext as _

def login_view(request):
    """Vue pour l'écran de connexion"""
    
    # Informations de profil (à définir dynamiquement selon votre logique)
    profile_info = None
    
    # Si l'utilisateur se connecte à un club spécifique ou à un rôle prédéfini
    tenant = request.tenant
    role_param = request.GET.get('role')
    
    if tenant and tenant.organization_type == 'CLUB':
        profile_info = {
            'role': _('Responsable de club'),
            'location': f"{tenant.city} - {tenant.country}",
            'status': _('ACTIF') if tenant.is_active else _('INACTIF'),
            'status_class': 'active' if tenant.is_active else 'inactive',
            'valid_dates': {
                'start': tenant.subscription_start.strftime('%d/%m/%Y') if tenant.subscription_start else None,
                'end': tenant.subscription_end.strftime('%d/%m/%Y') if tenant.subscription_end else None
            }
        }
    elif role_param:
        # Afficher les informations basées sur le rôle sélectionné
        role_mappings = {
            'club_manager': {
                'role': _('Responsable de club'),
                'status': _('HYBRIDE'),
                'status_class': 'hybrid'
            },
            'coach': {
                'role': _('Entraîneur'),
                'status': _('PRÉSENTIEL'),
                'status_class': 'onsite'
            },
            'judge': {
                'role': _('Juge/Arbitre'),
                'status': _('OFFICIEL'),
                'status_class': 'official'
            }
        }
        
        if role_param in role_mappings:
            profile_info = role_mappings[role_param]
            profile_info['location'] = _('France - Paris')  # Exemple
    
    if request.method == 'POST':
        email = request.POST.get('email')
        # Logique pour vérifier l'email et rediriger vers l'étape suivante
        # Par exemple, vérifier si l'email existe et rediriger vers la page de mot de passe
        # ou vers la page d'inscription
        
        # Exemple simplifié:
        if email:
            return redirect('auth:password', email=email)
        else:
            messages.error(request, _('Please enter a valid email address'))
    
    return render(request, 'auth/login.html', {
        'profile_info': profile_info
    })
```

### Configuration des URLs

```python
# auth/urls.py
from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/<str:email>/', views.password_view, name='password'),
    path('register/', views.register_view, name='register'),
    # Autres URLs d'authentification...
]
```

## Intégration de l'authentification sociale

### Configuration dans settings.py

```python
# settings.py

INSTALLED_APPS = [
    # Applications Django de base
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    # ...
    
    # Applications d'authentification
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.apple',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.facebook',
    
    # Applications MartialComp
    'competitions',
    'multitenant',
    # ...
]

# Configuration de l'authentification
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Paramètres django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_UNIQUE_EMAIL = True

# Configuration des fournisseurs sociaux
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID'),
            'secret': env('GOOGLE_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
    },
    'apple': {
        'APP': {
            'client_id': env('APPLE_CLIENT_ID'),
            'secret': env('APPLE_SECRET'),
            'key': env('APPLE_KEY'),
        },
        'SCOPE': ['email', 'name'],
    },
    'linkedin_oauth2': {
        'APP': {
            'client_id': env('LINKEDIN_CLIENT_ID'),
            'secret': env('LINKEDIN_SECRET'),
            'key': ''
        },
        'SCOPE': ['r_liteprofile', 'r_emailaddress'],
        'PROFILE_FIELDS': ['id', 'firstName', 'lastName', 'emailAddress'],
    },
    'facebook': {
        'APP': {
            'client_id': env('FACEBOOK_CLIENT_ID'),
            'secret': env('FACEBOOK_SECRET'),
            'key': ''
        },
        'SCOPE': ['email', 'public_profile'],
    },
}

# Redirection après authentification
LOGIN_REDIRECT_URL = '/dashboard/'
```

### Adapation des URLs pour django-allauth

```python
# urls.py principal
from django.urls import path, include

urlpatterns = [
    # URLs d'authentification propres à MartialComp
    path('auth/', include('auth.urls')),
    
    # URLs django-allauth pour l'authentification sociale
    path('accounts/', include('allauth.urls')),
    
    # Autres URLs...
]
```

## Affichage contextuel des informations de profil

Pour afficher les informations de profil de manière contextuelle, nous utilisons les données du tenant dans le système multi-tenant et les paramètres de requête.

```python
# middleware pour enrichir le contexte
class ProfileInfoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Enrichir le request avec les informations de profil si nécessaire
        if hasattr(request, 'tenant') and request.tenant:
            if request.tenant.organization_type == 'CLUB':
                request.profile_context = {
                    'role': 'Responsable de club',
                    'organization_name': request.tenant.name,
                    'location': f"{request.tenant.city}, {request.tenant.country}",
                    'status': 'ACTIF' if request.tenant.is_active else 'INACTIF'
                }
        
        response = self.get_response(request)
        return response
```

## Responsive design

Le design est déjà responsive grâce aux media queries dans le CSS. Pour une expérience optimale sur mobile, assurez-vous que :

1. La largeur de la viewport est correctement définie :
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

2. Les éléments interactifs (boutons, champs) sont suffisamment grands pour être facilement actionnables sur mobile (min. 44px)

3. Les polices sont lisibles sur petit écran (min. 14px)

## Tests et validation

### Tests unitaires

```python
# auth/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from competitions.models import Club

class AuthScreenTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Créer un club de test
        self.club = Club.objects.create(
            name="Club de Test",
            city="Paris",
            country="FR",
            is_active=True
        )
    
    def test_login_screen_basic(self):
        """Test de l'affichage de base de l'écran de connexion"""
        response = self.client.get(reverse('auth:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, "Sign in to MartialComp")
    
    def test_login_screen_with_role(self):
        """Test de l'affichage avec un rôle spécifié"""
        response = self.client.get(reverse('auth:login') + '?role=club_manager')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Responsable de club")
    
    def test_login_submit_valid_email(self):
        """Test de la soumission d'un email valide"""
        response = self.client.post(
            reverse('auth:login'), 
            {'email': 'test@example.com'}
        )
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertRedirects(response, reverse('auth:password', kwargs={'email': 'test@example.com'}))
```

### Tests de compatibilité navigateurs

Testez l'écran d'authentification sur :
- Chrome (dernière version)
- Firefox (dernière version)
- Safari (dernière version)
- Edge (dernière version)
- iOS Safari
- Chrome pour Android

## Déploiement

1. Intégrez les fichiers HTML, CSS et Python dans votre projet Django
2. Configurez les variables d'environnement pour les clés d'API des fournisseurs sociaux
3. Exécutez les migrations nécessaires pour django-allauth
4. Testez en développement avant de déployer en production
5. Déployez en suivant votre procédure de déploiement habituelle

### Script de déploiement

```bash
#!/bin/bash
# deploy_auth_screen.sh

echo "Déploiement de l'écran d'authentification MartialComp"

# Vérifier les dépendances
pip install django-allauth

# Exécuter les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer le serveur
sudo systemctl restart martialcomp

echo "Déploiement terminé."
```

## Conclusion

Ce guide détaille l'implémentation technique d'un nouvel écran d'authentification moderne pour MartialComp, avec support pour l'affichage contextuel des informations de profil et l'authentification sociale. Cette mise à jour améliorera significativement l'expérience utilisateur et la cohérence visuelle de l'application.
