# Module de Gestion de Tâches Kanban - MartialComp

## Vue d'ensemble

Module complet de gestion de tâches avec interface Kanban pour la plateforme MartialComp. Permet la gestion collaborative de projets et tâches avec un système de tableaux flexibles adaptés aux besoins des arts martiaux.

## Fonctionnalités principales

### ✅ Gestion de Tableaux Kanban
- Création de tableaux multi-contextes (Général, Compétition, Entraînement, Fédération, Club)
- Colonnes personnalisables avec limites WIP
- Gestion des permissions par rôle d'organisation
- Archives et templates de tableaux

### ✅ Gestion de Tâches Avancées  
- Drag & drop entre colonnes
- Système de priorités et statuts
- Dates d'échéance avec alertes de retard
- Assignation multiple d'utilisateurs
- Sous-tâches hiérarchiques
- Suivi du temps (estimé/passé)
- Étiquettes et métadonnées personnalisées
- Commentaires collaboratifs

### ✅ API REST Complète
- Endpoints RESTful pour toutes les opérations
- Sérialisation optimisée avec filtres
- Support mobile et applications tierces
- Documentation automatique

### ✅ Système de Permissions
- Intégration avec les rôles d'organisation
- Feature flags basés sur les abonnements
- Limites par tier de souscription
- Contrôle granulaire des accès

### ✅ Interface Utilisateur
- Design responsive et moderne
- Drag & drop intuitif
- Filtres et recherche avancés
- Mode plein écran pour présentations
- Notifications en temps réel

## Architecture technique

```
apps/task_management/
├── models/                 # Modèles de données
│   ├── boards.py          # Tableaux et colonnes
│   ├── tasks.py           # Tâches et commentaires  
│   ├── assignments.py     # Assignations d'utilisateurs
│   └── templates.py       # Templates de tableaux
├── views/                 # Vues Django
│   ├── boards.py          # Gestion des tableaux
│   ├── tasks.py           # Gestion des tâches
│   └── kanban.py          # Interface Kanban
├── templates/             # Templates HTML
│   ├── base/              # Templates de base
│   ├── boards/            # Vues tableaux
│   ├── tasks/             # Vues tâches
│   └── kanban/            # Interface Kanban
├── static/                # Assets statiques
│   ├── css/kanban.css     # Styles Kanban
│   └── js/                # JavaScript drag & drop
├── api.py                 # API REST
├── serializers.py         # Sérialisation API
├── permissions.py         # Système de permissions
├── utils.py               # Fonctions utilitaires
└── admin.py               # Interface d'administration
```

## Installation

### 1. Ajout du module aux settings

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ... autres apps
    'apps.task_management',
    'rest_framework',  # Requis pour l'API
]

# Configuration optionnelle
TASK_MANAGEMENT = {
    'MAX_BOARDS_PER_ORG': {
        'dojo_essentials': 0,
        'master_circle': 3, 
        'grand_champion': 999
    },
    'MAX_TASKS_PER_BOARD': {
        'dojo_essentials': 0,
        'master_circle': 50,
        'grand_champion': 999
    },
    'ENABLE_TIME_TRACKING': True,
    'ENABLE_TEMPLATES': True,
}
```

### 2. URLs

```python
# config/urls.py
urlpatterns = [
    # ... autres URLs
    path('task-management/', include('apps.task_management.urls')),
    path('api/task-management/', include('apps.task_management.api_urls')),
]
```

### 3. Migrations et setup

```bash
# Créer les migrations
python manage.py makemigrations task_management

# Appliquer les migrations  
python manage.py migrate

# Créer les templates système
python manage.py create_system_templates

# Configurer les permissions
python manage.py setup_task_permissions
```

### 4. Collecte des fichiers statiques

```bash
python manage.py collectstatic
```

## Configuration des Feature Flags

### Integration avec le système d'abonnement

Le module s'intègre automatiquement avec le système de tiers d'abonnement existant :

- **Dojo Essentials** : Pas d'accès au module
- **Master's Circle** : 3 tableaux max, 50 tâches par tableau, suivi du temps
- **Grand Champion** : Illimité + templates + API + fonctionnalités avancées

### Templates tags pour les permissions

```html
{% load task_permissions %}

{% if user|has_task_management %}
    <a href="{% url 'task_management:board_list' %}">Mes Tableaux</a>
{% endif %}

{% if user|can_edit_board:board %}
    <button>Modifier le tableau</button>
{% endif %}

{% show_feature_limit_warning user 'boards' current_board_count organization %}
```

## Utilisation

### Création d'un tableau

```python
from apps.task_management.models import Board, Column
from apps.organizations.models import Organization

# Créer un tableau
board = Board.objects.create(
    name="Mon Tableau de Compétition",
    organization=organization,
    created_by=user,
    board_type='competition',
    is_public=True
)
```

### API REST

```javascript
// Créer une tâche via API
fetch('/api/task-management/tasks/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        title: 'Nouvelle tâche',
        board: boardId,
        column: columnId,
        priority: 'high',
        assignee_ids: [userId1, userId2]
    })
});

// Déplacer une tâche
fetch(`/api/task-management/tasks/${taskId}/move/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        column_id: newColumnId,
        position: newPosition
    })
});
```

## Tests

```bash
# Lancer les tests du module
python manage.py test apps.task_management

# Avec couverture
coverage run --source='.' manage.py test apps.task_management
coverage report -m
```

## Personnalisation

### Templates personnalisés

Les templates peuvent être surchargés en créant des fichiers dans :
```
templates/task_management/
├── boards/
├── tasks/ 
└── kanban/
```

### Styles personnalisés

```css
/* Surcharger les couleurs du thème */
.kanban-card.priority-urgent {
    border-left-color: #dc3545 !important;
}

.kanban-column {
    background: #f8f9fc !important;
}
```

### Extensions JavaScript

```javascript
// Étendre les fonctionnalités drag & drop
document.addEventListener('DOMContentLoaded', function() {
    const kanbanBoard = document.getElementById('kanban-board');
    if (kanbanBoard) {
        // Ajouter des gestionnaires personnalisés
        kanbanBoard.addEventListener('taskMoved', function(e) {
            console.log('Tâche déplacée:', e.detail);
            // Actions personnalisées
        });
    }
});
```

## Performance et optimisation

### Cache Redis (recommandé)

```python
# settings.py
CACHES['task_boards'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'TIMEOUT': 300,
}
```

### Index base de données

Les modèles incluent déjà les index optimaux, mais pour de gros volumes :

```sql
-- Index supplémentaires pour performance
CREATE INDEX CONCURRENTLY idx_task_board_status 
ON task_management_task (board_id, status);

CREATE INDEX CONCURRENTLY idx_task_due_date_status 
ON task_management_task (due_date, status) 
WHERE due_date IS NOT NULL;
```

## Dépannage

### Problèmes courants

**1. Erreur de permissions**
```
PermissionDenied: Accès au module de gestion de tâches requis
```
→ Vérifier que l'utilisateur a un abonnement avec accès au module

**2. Drag & drop ne fonctionne pas**
→ Vérifier que les fichiers JS sont correctement chargés et que l'utilisateur a les permissions d'édition

**3. Limites WIP**
```
Limite WIP atteinte pour cette colonne
```
→ Normal, augmenter la limite ou passer à un tier supérieur

### Logs utiles

```python
import logging
logger = logging.getLogger('apps.task_management')

# Activer le debug
LOGGING = {
    'loggers': {
        'apps.task_management': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

## Feuille de route

### Version actuelle (v1.0)
- ✅ Interface Kanban complète
- ✅ Gestion de tâches avancée  
- ✅ API REST
- ✅ Système de permissions
- ✅ Templates et archives

### Prochaines versions
- 🔄 Notifications push en temps réel
- 🔄 Rapports et analytics avancés
- 🔄 Intégration calendrier
- 🔄 App mobile native
- 🔄 Import/export avancé (MS Project, etc.)
- 🔄 Workflows automatisés

## Support

Pour toute question ou problème :

1. Vérifier cette documentation
2. Consulter les logs de l'application
3. Tester avec un compte admin/superuser
4. Vérifier les permissions d'organisation

## Licence

Ce module fait partie de la plateforme MartialComp et suit la même licence que le projet principal.