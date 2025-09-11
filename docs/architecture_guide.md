# Guide d'Architecture MartialComp

## Vue d'ensemble

MartialComp est une plateforme de gestion des compétitions d'arts martiaux développée avec Django. L'architecture est modulaire et comprend plusieurs composants interagissant ensemble pour fournir une solution complète.

## Architecture technique

```
[Utilisateurs] → [Cloudflare/CDN] → [Nginx] → [Gunicorn] → [Django] → [PostgreSQL]
                                      ↓
                            [Fichiers Statiques]
```

### Composants

1. **Cloudflare/CDN** : Cache et protection contre les attaques DDoS
2. **Nginx** : Serveur web frontal, gestion des fichiers statiques et proxy inverse
3. **Gunicorn** : Serveur WSGI pour exécuter l'application Django
4. **Django** : Framework web pour la logique métier
5. **PostgreSQL** : Base de données relationnelle

## Architecture logicielle

MartialComp est structuré autour des modules suivants :

### Modules principaux (core)

| Module | Description | Dépendances |
|--------|-------------|-------------|
| `competitions` | Module principal de gestion des compétitions | Base |
| `multitenant` | Gestion de l'architecture multi-tenant | Base |
| `permissions_manager` | Gestion des rôles et permissions | Base |

### Modules optionnels

| Module | Description | Dépendances |
|--------|-------------|-------------|
| `grades` | Système de grades d'arts martiaux | `competitions` |
| `finances` | Paiements, factures, transactions | `competitions` |
| `shop` | Boutique en ligne | `competitions`, `finances` |
| `organizations` | Structure organisationnelle | `competitions` |
| `family_management` | Gestion des familles et des relations | `competitions` |

## Structure du projet

```
martialcomp/
├── config/                   # Configuration Django
│   ├── settings/
│   │   ├── base.py           # Paramètres de base
│   │   ├── development.py    # Paramètres de développement
│   │   └── production.py     # Paramètres de production
│   ├── urls.py               # Routage URL principal
│   └── wsgi.py               # Point d'entrée WSGI
├── competitions/             # Module principal
│   ├── models/               # Modèles de données
│   ├── views/                # Vues et logique métier
│   ├── templates/            # Templates HTML
│   ├── static/               # Fichiers statiques
│   ├── migrations/           # Migrations de base de données
│   └── management/           # Commandes personnalisées
├── grades/                   # Module de gestion des grades
├── finances/                 # Module de gestion financière
├── shop/                     # Module de boutique en ligne
├── organizations/            # Module de gestion d'organisations
├── templates/                # Templates globaux
├── static/                   # Fichiers statiques globaux
└── locale/                   # Fichiers de traduction
```

## Architecture de déploiement

### Environnement de production

```
/var/www/vhosts/martialcomp.com/
├── .env                   # Variables d'environnement
├── .venv/                 # Environnement virtuel Python
├── httpdocs/              # Code source
│   ├── manage.py
│   ├── config/
│   ├── competitions/
│   └── ...
├── logs/                  # Logs applicatifs
│   ├── django.log
│   ├── gunicorn-access.log
│   ├── gunicorn-error.log
│   ├── nginx-access.log
│   └── nginx-error.log
├── media/                 # Fichiers uploadés
└── static/                # Fichiers statiques collectés
```

### Services

| Service | Description | Configuration |
|---------|-------------|---------------|
| Nginx | Serveur web frontal | `/etc/nginx/conf.d/martialcomp.com.conf` |
| Gunicorn | Serveur d'application WSGI | `/etc/systemd/system/gunicorn-martialcomp.service` |
| PostgreSQL | Base de données | Base de données `martialcomp` |
| Redis | Cache et files d'attente | Port `6379` |

## Gestion des modules optionnels

MartialComp utilise un système d'imports conditionnels pour gérer les modules optionnels :

1. **Détection des modules** : Vérification de la disponibilité des modules via `try/except`
2. **Fonctionnalités conditionnelles** : Adaptation du comportement selon les modules disponibles
3. **Interface utilisateur adaptative** : Affichage conditionnel des éléments d'interface

Exemple d'import conditionnel :
```python
try:
    from grades.models import Grade
    HAS_GRADES = True
except ImportError:
    HAS_GRADES = False
    Grade = None
```

## Architecture d'internationalisation

MartialComp prend en charge plusieurs langues via le framework d'internationalisation de Django :

1. **URL avec préfixes de langue** : `/fr/`, `/en/`, etc.
2. **Middleware de localisation** : Détection automatique de la langue
3. **Fichiers de traduction** : Messages traduits dans `locale/`
4. **Templates avec tags i18n** : `{% trans "texte" %}`

## Monitoring et performance

L'architecture inclut plusieurs mécanismes pour assurer la fiabilité et les performances :

1. **Logging centralisé** : Tous les logs sont stockés dans `/var/www/vhosts/martialcomp.com/logs/`
2. **Health checks** : Endpoints de vérification d'état de santé
3. **Métriques de performance** : Collecte de métriques via middleware Django
4. **Alertes automatisées** : Notification en cas de problème détecté

## Diagramme de communication

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Interface    │     │ API REST      │     │ Applications │
│ Utilisateur  │────►│ (Django REST) │◄────│ Mobiles      │
└──────────────┘     └───────────────┘     └──────────────┘
       │                     │                    │
       │                     │                    │
       ▼                     ▼                    ▼
┌─────────────────────────────────────────────────────┐
│                 Logique Métier Django                │
├─────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐   │
│ │Compétitions│ │ Grades │ │Finances │ │  Shop    │   │
│ └───────────┘ └────────┘ └─────────┘ └──────────┘   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Base de Données                     │
└─────────────────────────────────────────────────────┘
```

## Conclusion

Cette architecture modulaire permet à MartialComp d'être flexible et adaptable aux différents besoins des utilisateurs tout en maintenant une base solide. La conception favorise la séparation des préoccupations et permet l'activation ou la désactivation de modules selon les besoins spécifiques de chaque installation.
