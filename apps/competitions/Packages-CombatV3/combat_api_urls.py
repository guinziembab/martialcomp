"""
URLs configuration pour l'API Combat
MartialComp - Interface de Combat V3
"""

from django.urls import path
from . import combat_api_views as api_views

app_name = 'combat_api'

urlpatterns = [
    # ============================================================================
    # ENDPOINTS PRINCIPAUX
    # ============================================================================
    
    # Mise à jour des scores en temps réel
    path(
        'combat/<int:combat_id>/update/',
        api_views.update_combat_scores,
        name='update_combat_scores'
    ),
    
    # Récupérer l'état actuel d'un combat
    path(
        'combat/<int:combat_id>/status/',
        api_views.get_combat_status,
        name='get_combat_status'
    ),
    
    # Historique des actions
    path(
        'combat/<int:combat_id>/history/',
        api_views.get_combat_history,
        name='get_combat_history'
    ),
    
    # Terminer un combat
    path(
        'combat/<int:combat_id>/end/',
        api_views.end_combat,
        name='end_combat'
    ),
    
    # ============================================================================
    # ENDPOINTS TEMPS RÉEL (Polling)
    # ============================================================================
    
    # Vue générique temps réel (GET et POST)
    path(
        'combat/<int:combat_id>/realtime/',
        api_views.CombatRealtimeView.as_view(),
        name='combat_realtime'
    ),
]

"""
INTÉGRATION DANS LE PROJET PRINCIPAL
=====================================

Dans votre fichier urls.py principal (martialcomp/urls.py), ajoutez :

from django.urls import path, include

urlpatterns = [
    # ... autres URLs ...
    
    # API Combat
    path('api/', include('apps.competitions.combat_api_urls')),
    
    # ... autres URLs ...
]

Cela permettra d'accéder aux endpoints via :
- /api/combat/<id>/update/
- /api/combat/<id>/status/
- etc.
"""

"""
EXEMPLES D'UTILISATION
=======================

# JavaScript (Frontend)
# ---------------------

// 1. Mettre à jour les scores
fetch('/api/combat/123/update/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        score_rouge: 2.5,
        score_blanc: 1.0,
        avert_rouge: 0,
        avert_blanc: 1
    })
})
.then(response => response.json())
.then(data => console.log('Success:', data));

// 2. Récupérer le status actuel
fetch('/api/combat/123/status/')
    .then(response => response.json())
    .then(data => {
        console.log('Score ROUGE:', data.combat.scores.rouge);
        console.log('Score BLANC:', data.combat.scores.blanc);
    });

// 3. Récupérer l'historique
fetch('/api/combat/123/history/?limit=10')
    .then(response => response.json())
    .then(data => {
        data.actions.forEach(action => {
            console.log(action.description, action.points);
        });
    });

// 4. Terminer le combat
fetch('/api/combat/123/end/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    }
})
.then(response => response.json())
.then(data => {
    alert(`Vainqueur: ${data.vainqueur}`);
});


# Python (Tests ou Scripts)
# --------------------------

import requests

# URL de base
BASE_URL = 'http://localhost:8000/api'

# Headers avec authentification
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Token YOUR_AUTH_TOKEN'
}

# 1. Mettre à jour un combat
response = requests.post(
    f'{BASE_URL}/combat/123/update/',
    headers=headers,
    json={
        'score_rouge': 3.0,
        'score_blanc': 2.5
    }
)
print(response.json())

# 2. Récupérer le status
response = requests.get(
    f'{BASE_URL}/combat/123/status/',
    headers=headers
)
combat_data = response.json()
print(f"Score: {combat_data['combat']['scores']}")


# Django Shell
# ------------

from apps.competitions.models import Combat
from apps.competitions.combat_api_views import calculate_combat_statistics

# Récupérer un combat
combat = Combat.objects.get(id=123)

# Calculer les statistiques
stats = calculate_combat_statistics(combat)
print(stats)
"""

"""
SÉCURITÉ ET PERMISSIONS
========================

Tous les endpoints nécessitent une authentification (@login_required).

Niveaux de permissions :
- Staff : Accès complet
- Arbitre du combat : Peut modifier et terminer
- Organisateur de la compétition : Peut modifier et terminer
- Juge du combat : Peut modifier (mais pas terminer)
- Autres utilisateurs authentifiés : Lecture seule

Pour modifier les permissions, éditez la fonction validate_combat_permissions()
dans combat_api_views.py
"""

"""
TESTS UNITAIRES
===============

Pour tester les endpoints, créez un fichier test_combat_api.py :

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.competitions.models import Combat

User = get_user_model()

class CombatAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_update_combat_scores(self):
        # Créer un combat de test
        combat = Combat.objects.create(...)
        
        # Tester la mise à jour
        response = self.client.post(
            f'/api/combat/{combat.id}/update/',
            data={
                'score_rouge': 2.5,
                'score_blanc': 1.0
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
    
    def test_get_combat_status(self):
        combat = Combat.objects.create(...)
        
        response = self.client.get(f'/api/combat/{combat.id}/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('combat', data)
        self.assertIn('scores', data['combat'])

# Lancer les tests :
# python manage.py test apps.competitions.test_combat_api
"""

"""
MONITORING ET LOGS
==================

Les requêtes API sont automatiquement loggées via le middleware APILoggingMiddleware.

Pour activer les logs détaillés, ajoutez dans settings.py :

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/combat_api.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.competitions.combat_api_views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

Puis dans vos vues, utilisez :
logger.info("Message d'information")
logger.error("Message d'erreur")
"""

"""
RATE LIMITING (Optionnel)
==========================

Pour limiter le nombre de requêtes par utilisateur, installez django-ratelimit :

pip install django-ratelimit

Puis dans combat_api_views.py :

from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='POST')
@require_http_methods(["POST"])
@login_required
def update_combat_scores(request, combat_id):
    ...

Cela limitera à 100 requêtes POST par heure par utilisateur.
"""

"""
WEBSOCKETS TEMPS RÉEL (Avancé)
================================

Pour des mises à jour vraiment temps réel, migrez vers Django Channels :

# Installation
pip install channels channels-redis

# Dans settings.py
INSTALLED_APPS = [
    ...
    'channels',
]

ASGI_APPLICATION = 'martialcomp.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Créer consumers.py pour WebSocket
# (Voir documentation Django Channels pour plus de détails)
"""

"""
DOCUMENTATION API (Swagger)
============================

Pour générer une documentation API interactive, installez drf-yasg :

pip install drf-yasg

Dans urls.py principal :

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="MartialComp Combat API",
      default_version='v1',
      description="API pour la gestion des combats en temps réel",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    ...
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0)),
]

Accédez à la doc sur : http://localhost:8000/api/docs/
"""
