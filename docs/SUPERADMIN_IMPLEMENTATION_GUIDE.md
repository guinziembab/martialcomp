# 🎛️ Guide d'Implémentation Complet - Interface Super Admin MartialComp

**Version:** 1.0  
**Date:** Janvier 2025  
**Auteur:** MartialComp Development Team

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Architecture Technique](#2-architecture-technique)
3. [Phase 1 : Fondations et Modèles](#3-phase-1--fondations-et-modèles)
4. [Phase 2 : Dashboard Principal](#4-phase-2--dashboard-principal)
5. [Phase 3 : Carte du Monde](#5-phase-3--carte-du-monde)
6. [Phase 4 : Gestion des Memberships](#6-phase-4--gestion-des-memberships)
7. [Phase 5 : Monitoring Système](#7-phase-5--monitoring-système)
8. [Phase 6 : Configuration](#8-phase-6--configuration)
9. [Phase 7 : Logs et Audit](#9-phase-7--logs-et-audit)
10. [Phase 8 : Temps Réel (WebSocket)](#10-phase-8--temps-réel-websocket)
11. [Tests et Validation](#11-tests-et-validation)
12. [Déploiement](#12-déploiement)

---

## 1. Vue d'Ensemble

### 1.1 Objectifs du Projet

L'interface Super Admin MartialComp doit permettre :

| # | Exigence | Priorité | Statut |
|---|----------|----------|--------|
| 1 | État réel de la plateforme en temps réel | 🔴 Critique | ⬜ À faire |
| 2 | Suivi temps réel (adhésions, transformations, compétitions) | 🔴 Critique | ⬜ À faire |
| 3 | Bouton de redémarrage de la plateforme | 🔴 Critique | ⬜ À faire |
| 4 | Carte du monde avec nouvelles adhésions + zoom | 🟡 Haute | ⬜ À faire |
| 5 | Navigation par onglets (pas de scroll) | 🟡 Haute | ⬜ À faire |
| 6 | Statut DB (taille) + stockage total | 🔴 Critique | ⬜ À faire |
| 7 | Gestion des profils membership (membres et non-membres) | 🟡 Haute | ⬜ À faire |

### 1.2 Structure des Onglets

```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 📊      │ │ 🌍      │ │ 📦      │ │ 💾      │ │ ⚙️      │ │ 📜      │
│DASHBOARD│ │ CARTE   │ │MEMBERS  │ │SYSTÈME  │ │ CONFIG  │ │ LOGS    │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 2. Architecture Technique

### 2.1 Structure des Fichiers

```
apps/
└── superadmin/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    ├── forms.py
    ├── views/
    │   ├── __init__.py
    │   ├── dashboard.py
    │   ├── map.py
    │   ├── memberships.py
    │   ├── system.py
    │   ├── config.py
    │   └── logs.py
    ├── api/
    │   ├── __init__.py
    │   ├── serializers.py
    │   ├── viewsets.py
    │   └── urls.py
    ├── services/
    │   ├── __init__.py
    │   ├── system_control.py
    │   ├── metrics.py
    │   ├── geo_stats.py
    │   └── audit.py
    ├── consumers/
    │   ├── __init__.py
    │   └── realtime.py
    ├── tasks.py
    ├── middleware.py
    ├── decorators.py
    └── templates/
        └── superadmin/
            ├── base.html
            ├── dashboard.html
            ├── map.html
            ├── memberships/
            │   ├── list.html
            │   ├── detail.html
            │   └── form.html
            ├── system.html
            ├── config.html
            └── logs.html
```

### 2.2 Dépendances Requises

```txt
# requirements.txt additions
channels>=4.0.0
channels-redis>=4.1.0
psutil>=5.9.0
django-redis>=5.4.0
celery>=5.3.0
```

---

## 3. Phase 1 : Fondations et Modèles

### PROMPT 1.1 : Configuration de l'Application

```
Tu es un développeur Django senior travaillant sur MartialComp, une plateforme SaaS de gestion de compétitions d'arts martiaux.

CONTEXTE :
- Django 5.1+, PostgreSQL 15+, Redis
- Architecture multi-tenant existante
- Apps existantes : competitions, users, organizations, subscriptions

TÂCHE :
Crée l'application Django `superadmin` avec sa configuration de base.

FICHIERS À CRÉER :

1. `apps/superadmin/__init__.py` - Configuration de l'app
2. `apps/superadmin/apps.py` - AppConfig
3. `apps/superadmin/urls.py` - URLs principales avec namespaces

EXIGENCES :
- L'accès doit être restreint aux superusers uniquement
- Namespace URL : 'superadmin'
- Préparer les includes pour les sous-modules (api, views)

STRUCTURE URL ATTENDUE :
/superadmin/ → Dashboard principal
/superadmin/map/ → Carte du monde
/superadmin/memberships/ → Gestion profils
/superadmin/system/ → Monitoring système
/superadmin/config/ → Configuration
/superadmin/logs/ → Logs et audit
/superadmin/api/ → API REST

Génère le code complet et documenté.
```

### PROMPT 1.2 : Modèles de Données - Partie 1 (Membership)

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèles existants : SubscriptionTier, FeatureFlag, Subscription, Organization, Competition
- Besoin de gérer les profils membership pour membres ET non-membres
- Les non-membres peuvent avoir un accès ponctuel lié à une compétition

TÂCHE :
Crée les modèles pour la gestion des profils de membership.

MODÈLES À CRÉER :

1. `MembershipProfile` :
   - name (CharField)
   - slug (SlugField, unique)
   - description (TextField)
   - profile_type : CHOICES ('subscription', 'event', 'hybrid')
   - validity_type : CHOICES ('duration', 'event_bound')
   - validity_duration (IntegerField, nullable) - en jours
   - linked_event (FK Competition, nullable)
   - created_by_organization (FK Organization, nullable)
   - is_global (BooleanField) - créé par super admin
   - base_tier (FK SubscriptionTier, nullable)
   - custom_features (M2M FeatureFlag)
   - feature_overrides (JSONField) - {"feature_code": true/false}
   - pricing_model : CHOICES ('per_member', 'flat', 'free')
   - price (DecimalField)
   - currency (CharField, default='EUR')
   - max_participants (IntegerField, default=0) - 0 = illimité
   - allowed_disciplines (M2M Discipline)
   - requires_approval (BooleanField)
   - is_active (BooleanField)
   - created_at, updated_at (auto)

2. `EventPass` :
   - user (FK User)
   - membership_profile (FK MembershipProfile)
   - competition (FK Competition)
   - organization (FK Organization, nullable) - pour les clubs invités
   - status : CHOICES ('pending', 'approved', 'active', 'expired', 'cancelled')
   - approved_by (FK User, nullable)
   - approved_at (DateTimeField, nullable)
   - payment_status : CHOICES ('pending', 'paid', 'free', 'refunded')
   - payment_reference (CharField, nullable)
   - expires_at (DateTimeField)
   - created_at, updated_at (auto)

3. `MembershipTransformation` :
   - user (FK User)
   - from_profile (FK MembershipProfile, nullable) - null si nouveau
   - to_profile (FK MembershipProfile)
   - transformation_type : CHOICES ('upgrade', 'downgrade', 'conversion', 'new')
   - source_event (FK Competition, nullable) - si conversion depuis event pass
   - discount_applied (DecimalField, nullable)
   - discount_code (CharField, nullable)
   - created_at (auto)

EXIGENCES :
- Utiliser les classes abstraites de base du projet si existantes
- Ajouter les index appropriés pour les requêtes fréquentes
- Méthodes utilitaires : is_valid(), get_features(), can_access()
- Signals pour la gestion automatique des expirations
- Manager personnalisé avec méthodes : active(), for_event(), global_profiles()

Génère le code complet avec docstrings.
```

### PROMPT 1.3 : Modèles de Données - Partie 2 (Monitoring)

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Application superadmin en cours de création
- Besoin de stocker les métriques système et l'historique

TÂCHE :
Crée les modèles pour le monitoring système et l'audit.

MODÈLES À CRÉER :

1. `SystemMetric` :
   - metric_type : CHOICES (
       'db_size', 'db_connections', 'storage_total', 'storage_used',
       'cpu_usage', 'memory_usage', 'active_users', 'requests_per_minute'
     )
   - value (DecimalField)
   - unit (CharField) - 'GB', '%', 'count', 'req/min'
   - recorded_at (DateTimeField, auto_now_add)
   - metadata (JSONField, nullable) - détails supplémentaires

   Meta:
   - index sur (metric_type, recorded_at)
   - ordering = ['-recorded_at']

2. `ServiceStatus` :
   - service_name : CHOICES (
       'web', 'database', 'redis', 'celery', 'celery_beat', 'nginx'
     )
   - status : CHOICES ('ok', 'warning', 'error', 'unknown')
   - response_time_ms (IntegerField, nullable)
   - pid (IntegerField, nullable)
   - cpu_percent (DecimalField, nullable)
   - memory_mb (DecimalField, nullable)
   - last_check (DateTimeField, auto_now)
   - error_message (TextField, nullable)

3. `AdminAction` :
   - admin_user (FK User)
   - action_type : CHOICES (
       'restart_service', 'maintenance_mode', 'emergency_stop',
       'config_change', 'profile_create', 'profile_modify', 'profile_delete',
       'user_action', 'backup_trigger', 'cache_clear'
     )
   - target_service (CharField, nullable)
   - target_object_type (CharField, nullable) - ContentType string
   - target_object_id (IntegerField, nullable)
   - description (TextField)
   - ip_address (GenericIPAddressField)
   - user_agent (TextField)
   - status : CHOICES ('initiated', 'in_progress', 'completed', 'failed')
   - result_message (TextField, nullable)
   - created_at (auto)
   - completed_at (DateTimeField, nullable)

4. `PlatformAlert` :
   - alert_type : CHOICES (
       'disk_space', 'db_connections', 'memory', 'service_down',
       'high_error_rate', 'security', 'performance'
     )
   - severity : CHOICES ('info', 'warning', 'critical')
   - title (CharField)
   - message (TextField)
   - is_resolved (BooleanField, default=False)
   - resolved_by (FK User, nullable)
   - resolved_at (DateTimeField, nullable)
   - auto_resolved (BooleanField, default=False)
   - created_at (auto)

EXIGENCES :
- Créer un Manager pour SystemMetric avec : latest(), history(hours=24), aggregate_by_hour()
- Méthode de classe ServiceStatus.check_all() qui vérifie tous les services
- Signal post_save sur AdminAction pour notifier en temps réel
- Méthode PlatformAlert.create_if_threshold() pour créer des alertes conditionnelles

Génère le code complet.
```

### PROMPT 1.4 : Migrations et Fixtures

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèles MembershipProfile, EventPass, MembershipTransformation créés
- Modèles SystemMetric, ServiceStatus, AdminAction, PlatformAlert créés
- Besoin de données initiales pour les profils globaux

TÂCHE :
Crée les fixtures de données initiales pour l'application superadmin.

FICHIER : `apps/superadmin/fixtures/initial_profiles.json`

DONNÉES À CRÉER :

1. Profils Globaux (Abonnements) - Liés aux SubscriptionTier existants :
   - "Dojo Essentials" (profile_type='subscription', is_global=True)
   - "Master's Circle" (profile_type='subscription', is_global=True)
   - "Grand Champion Suite" (profile_type='subscription', is_global=True)

2. Profils Événement (Templates) :
   - "Pack Compétition Standard" (profile_type='event', is_global=True)
     - pricing_model='per_member', price=15.00
     - Features: inscription, résultats, QR code, portail compétiteur
   
   - "Participant Externe" (profile_type='event', is_global=True)
     - pricing_model='per_member', price=10.00
     - Features: inscription, résultats seulement
   
   - "Délégation Invitée" (profile_type='event', is_global=True)
     - pricing_model='free', requires_approval=True
     - Features: inscription, résultats

ÉGALEMENT :
Crée un script de migration de données (data migration) pour :
- Associer les profils aux SubscriptionTier existants
- Vérifier la cohérence des données

Génère :
1. Le fichier JSON de fixtures
2. Le script de migration de données
3. La commande management pour charger les données : `python manage.py load_superadmin_fixtures`
```

---

## 4. Phase 2 : Dashboard Principal

### PROMPT 2.1 : Service de Métriques

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèles SystemMetric, ServiceStatus créés
- Besoin de collecter et agréger les métriques en temps réel
- Base de données PostgreSQL ~55GB avec 267 tables

TÂCHE :
Crée le service de collecte et d'agrégation des métriques.

FICHIER : `apps/superadmin/services/metrics.py`

CLASSE `MetricsService` avec méthodes :

1. `get_platform_status()` → dict :
   - Statut global (operational, degraded, down)
   - Uptime calculé
   - Timestamp actuel

2. `get_kpis()` → dict :
   - total_memberships (count + delta 24h + delta 7j)
   - total_transformations (count + delta 24h + delta 7j)
   - total_competitions (count + delta 24h + delta 7j)
   - total_organizations (count + delta 24h)
   - total_users (count + delta 24h)
   - monthly_revenue (MTD + delta 24h)

3. `get_memberships_by_profile()` → list[dict] :
   - Pour chaque MembershipProfile actif :
     - name, total, delta_24h, delta_7j
     - transformation_rate (si applicable)

4. `get_evolution_data(days=7)` → dict :
   - Données pour graphique : dates[], memberships[], transformations[], competitions[]

5. `get_database_stats()` → dict :
   - size_gb, tables_count, connections_active, connections_max
   - top_tables : [{name, size_gb, rows_count}]

6. `get_storage_stats()` → dict :
   - total_gb, used_gb, free_gb, percent_used
   - breakdown : {media, static, backups, logs}

7. `get_services_status()` → list[dict] :
   - Pour chaque service : name, status, pid, cpu, memory, response_time

CLASSE `MetricsCollector` (pour tâches Celery) :

1. `collect_all()` - Collecte toutes les métriques et les stocke
2. `cleanup_old_metrics(days=30)` - Supprime les anciennes métriques

EXIGENCES :
- Utiliser des requêtes optimisées avec annotations Django
- Cache Redis pour les métriques fréquentes (TTL=30s pour KPIs)
- Gestion des erreurs robuste (ne pas planter si un service est down)
- Logging des collectes

Génère le code complet avec docstrings.
```

### PROMPT 2.2 : Tâches Celery pour Métriques

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service MetricsService et MetricsCollector créés
- Celery et Redis configurés
- Besoin de collecter les métriques périodiquement

TÂCHE :
Crée les tâches Celery pour la collecte automatique des métriques.

FICHIER : `apps/superadmin/tasks.py`

TÂCHES À CRÉER :

1. `collect_metrics_task` :
   - Fréquence : toutes les 60 secondes
   - Collecte : KPIs, services status
   - Stocke dans SystemMetric

2. `collect_heavy_metrics_task` :
   - Fréquence : toutes les 5 minutes
   - Collecte : DB stats, storage stats
   - Plus coûteux en ressources

3. `cleanup_metrics_task` :
   - Fréquence : quotidien à 3h du matin
   - Supprime les métriques > 30 jours
   - Archive les métriques importantes

4. `check_alerts_task` :
   - Fréquence : toutes les 2 minutes
   - Vérifie les seuils d'alerte :
     - Disk > 80% → warning, > 90% → critical
     - DB connections > 80% → warning
     - Service down → critical
   - Crée PlatformAlert si nécessaire

5. `broadcast_metrics_task` :
   - Fréquence : toutes les 30 secondes
   - Envoie les métriques via WebSocket aux admins connectés

CONFIGURATION CELERY BEAT :
Ajouter les schedules dans le fichier de configuration.

EXIGENCES :
- Utiliser @shared_task avec retry automatique
- Timeout approprié pour chaque tâche
- Logging structuré
- Ne pas bloquer si Redis indisponible

Génère le code complet.
```

### PROMPT 2.3 : Vue Dashboard

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service MetricsService disponible
- Templates Bootstrap 5 utilisés dans le projet
- Navigation par onglets requise (pas de scroll)

TÂCHE :
Crée la vue et le template du dashboard principal.

FICHIERS À CRÉER :

1. `apps/superadmin/views/dashboard.py` :

   - Classe `DashboardView(SuperAdminRequiredMixin, TemplateView)` :
     - template_name = 'superadmin/dashboard.html'
     - get_context_data() retourne toutes les métriques initiales

2. `apps/superadmin/templates/superadmin/base.html` :
   - Layout avec navigation par onglets en haut
   - Pas de scroll vertical sur la page principale
   - Header avec : logo, nom admin, notifications, déconnexion
   - Les onglets : Dashboard, Carte, Memberships, Système, Config, Logs
   - Zone de contenu qui prend 100% de la hauteur restante
   - Auto-refresh indicator (30s par défaut)

3. `apps/superadmin/templates/superadmin/dashboard.html` :
   - Hérite de base.html
   - Section "État Plateforme" :
     - Indicateur principal (🟢 OPÉRATIONNEL / 🟡 DÉGRADÉ / 🔴 HORS LIGNE)
     - Uptime
     - 4 cards services : Web, DB, Redis, Celery
   
   - Section "KPIs Temps Réel" :
     - 6 cards : Adhésions, Transformations, Compétitions, Organisations, Utilisateurs, Revenus
     - Chaque card : valeur principale + deltas (24h, 7j)
   
   - Section "Adhésions par Profil" :
     - Tableau avec : Profil, Total, 24h, 7j, Taux Transformation
     - Séparation visuelle : Profils globaux / Profils événement
   
   - Section "Graphique Évolution" :
     - Chart.js line chart
     - 7 derniers jours
     - 3 séries : Adhésions, Transformations, Compétitions

EXIGENCES :
- Design responsive mais optimisé desktop
- Couleurs cohérentes avec la charte MartialComp
- IDs pour les éléments mis à jour en temps réel
- Data attributes pour les valeurs (data-metric-type, data-value)

Génère le code complet HTML/CSS/JS.
```

### PROMPT 2.4 : API REST Dashboard

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Django REST Framework utilisé
- Service MetricsService disponible
- Besoin d'endpoints pour le refresh AJAX

TÂCHE :
Crée les endpoints API pour le dashboard.

FICHIERS À CRÉER :

1. `apps/superadmin/api/serializers.py` :
   - PlatformStatusSerializer
   - KPISerializer
   - MembershipStatsSerializer
   - ServiceStatusSerializer
   - EvolutionDataSerializer

2. `apps/superadmin/api/viewsets.py` :
   - MetricsViewSet avec actions :
     - @action GET /api/superadmin/metrics/status/
     - @action GET /api/superadmin/metrics/kpis/
     - @action GET /api/superadmin/metrics/memberships/
     - @action GET /api/superadmin/metrics/services/
     - @action GET /api/superadmin/metrics/evolution/?days=7

3. `apps/superadmin/api/urls.py` :
   - Router configuration

EXIGENCES :
- Permission : IsSuperUser
- Throttling : 60 requests/minute
- Cache : 30 secondes pour la plupart des endpoints
- Format JSON standardisé : {"success": bool, "data": {}, "timestamp": ""}

Génère le code complet.
```

---

## 5. Phase 3 : Carte du Monde

### PROMPT 3.1 : Service Géostatistiques

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèle Organization avec champs : country, city, latitude, longitude
- Modèle User avec FK vers Organization
- Besoin d'agréger les adhésions par pays/ville

TÂCHE :
Crée le service de statistiques géographiques.

FICHIER : `apps/superadmin/services/geo_stats.py`

CLASSE `GeoStatsService` :

1. `get_countries_stats(period='24h')` → list[dict] :
   ```python
   [
     {
       "country_code": "BE",
       "country_name": "Belgique",
       "new_memberships": 12,
       "total_organizations": 45,
       "active_competitions": 3,
       "coordinates": {"lat": 50.85, "lng": 4.35}
     },
     ...
   ]
   ```

2. `get_country_detail(country_code)` → dict :
   - Statistiques détaillées pour un pays
   - Liste des dernières inscriptions
   - Top organisations

3. `get_cities_for_country(country_code, period='24h')` → list[dict] :
   - Agrégation par ville pour le zoom

4. `get_recent_signups(limit=10, country_code=None)` → list[dict] :
   - Dernières inscriptions avec localisation
   - Pour les notifications temps réel sur la carte

5. `get_heatmap_data(period='7d')` → list[dict] :
   - Données pour heatmap : lat, lng, intensity

EXIGENCES :
- Utiliser les annotations Django pour les agrégations
- Cache Redis : 5 minutes pour les stats pays
- Gérer les cas où lat/lng manquants
- Utiliser pycountry pour les noms de pays traduits

Génère le code complet.
```

### PROMPT 3.2 : Vue et Template Carte

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service GeoStatsService disponible
- Leaflet.js choisi pour la carte
- Navigation par onglets (l'onglet Carte est le 2ème)

TÂCHE :
Crée la vue et le template de la carte du monde.

FICHIERS À CRÉER :

1. `apps/superadmin/views/map.py` :
   - Classe `MapView(SuperAdminRequiredMixin, TemplateView)`
   - Contexte initial avec stats pays

2. `apps/superadmin/templates/superadmin/map.html` :

LAYOUT (hauteur fixe, pas de scroll) :
```
┌─────────────────────────────────────────────────────────────┐
│ [Période: Dernières 24h ▼]              🔄 Auto-refresh: ON │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    CARTE LEAFLET                            │
│                    (70% hauteur)                            │
│                                                             │
│   [🔍+] [🔍-] [🔄 Reset] [📍 Europe]                        │
├─────────────────────────────────────────────────────────────┤
│ DÉTAIL ZONE SÉLECTIONNÉE          │ TOP PAYS (24h)         │
│ 🇧🇪 BELGIQUE                       │ 🥇 🇧🇪 +12            │
│ Nouvelles adhésions: +12          │ 🥈 🇫🇷 +8             │
│ Organisations: 45                 │ 🥉 🇩🇪 +5             │
│ Compétitions en cours: 3          │                        │
│                                   │                        │
│ Dernières inscriptions:           │                        │
│ • 14:23 - Club Long Phai         │                        │
│ • 13:45 - FFKBDA                 │                        │
└───────────────────────────────────┴────────────────────────┘
```

FONCTIONNALITÉS LEAFLET :
- Markers clusterisés (Leaflet.markercluster)
- Cercles proportionnels au nombre d'adhésions
- Couleurs : vert (peu), jaune (moyen), rouge (beaucoup)
- Popup au hover avec stats rapides
- Click pour sélectionner et afficher détail
- Animation pulse pour nouvelles adhésions (temps réel)

3. `apps/superadmin/static/superadmin/js/map.js` :
   - Initialisation Leaflet
   - Chargement données API
   - Gestion des événements (click, zoom)
   - Mise à jour temps réel via WebSocket

EXIGENCES :
- Carte centrée sur l'Europe par défaut
- Zoom min: 2, Zoom max: 12
- Tiles: OpenStreetMap ou CartoDB (gratuit)
- Responsive : sur mobile, le détail passe en dessous

Génère le code complet.
```

### PROMPT 3.3 : API Carte

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service GeoStatsService disponible
- Besoin d'endpoints pour alimenter la carte Leaflet

TÂCHE :
Crée les endpoints API pour la carte.

FICHIER : `apps/superadmin/api/viewsets.py` (ajouter à l'existant)

ENDPOINTS À CRÉER :

1. GET /api/superadmin/geo/countries/?period=24h
   - Liste tous les pays avec stats
   - Filtrable par période : 24h, 7d, 30d

2. GET /api/superadmin/geo/countries/{code}/
   - Détail d'un pays
   - Inclut dernières inscriptions

3. GET /api/superadmin/geo/countries/{code}/cities/
   - Villes du pays avec stats

4. GET /api/superadmin/geo/recent/?limit=10&country=
   - Dernières inscriptions
   - Optionnel : filtrer par pays

5. GET /api/superadmin/geo/heatmap/?period=7d
   - Données pour heatmap

SERIALIZERS :
- CountryStatsSerializer
- CountryDetailSerializer
- CityStatsSerializer
- RecentSignupSerializer

Génère le code complet.
```

---

## 6. Phase 4 : Gestion des Memberships

### PROMPT 4.1 : Vues CRUD Memberships

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèle MembershipProfile créé avec tous les champs
- Besoin d'interface CRUD complète
- Distinction : profils globaux (lecture seule) vs profils organisation (éditable)

TÂCHE :
Crée les vues pour la gestion des profils de membership.

FICHIER : `apps/superadmin/views/memberships.py`

VUES À CRÉER :

1. `MembershipListView` :
   - Liste tous les profils
   - Filtres : type (subscription/event), statut (actif/inactif), global/local
   - Regroupement : Profils globaux en haut (lecture seule), puis par organisation
   - Stats par profil : total utilisations, revenus générés

2. `MembershipDetailView` :
   - Affichage complet d'un profil
   - Statistiques d'utilisation
   - Historique des modifications
   - Liste des EventPass actifs (pour profils event)

3. `MembershipCreateView` :
   - Formulaire multi-étapes :
     1. Informations générales (nom, type, validité)
     2. Configuration features (basé sur tier ou custom)
     3. Tarification
     4. Contraintes (max participants, disciplines, approbation)
   - Templates disponibles pour pré-remplir

4. `MembershipUpdateView` :
   - Édition avec versioning (garder historique)
   - Confirmation si des EventPass actifs existent

5. `MembershipDeleteView` :
   - Soft delete (is_active=False)
   - Impossible si EventPass actifs

6. `MembershipStatsView` :
   - Graphiques d'utilisation
   - Taux de transformation
   - Revenus par période

FICHIER : `apps/superadmin/forms.py`

FORMS :
- MembershipProfileForm (ModelForm avec widgets personnalisés)
- MembershipFeaturesForm (pour l'étape 2)
- MembershipPricingForm (pour l'étape 3)

Génère le code complet.
```

### PROMPT 4.2 : Templates Memberships

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Vues memberships créées
- Bootstrap 5 + Onglets
- Design cohérent avec le reste de l'admin

TÂCHE :
Crée les templates pour la gestion des memberships.

FICHIERS À CRÉER :

1. `templates/superadmin/memberships/list.html` :

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📦 PROFILS DE MEMBERSHIP                             [+ Nouveau]   │
├─────────────────────────────────────────────────────────────────────┤
│ [Profils Globaux] [Profils Événement] [Statistiques]               │
├─────────────────────────────────────────────────────────────────────┤
│ 🔍 [Rechercher...]  Type: [Tous ▼]  Statut: [Actifs ▼]             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 🌐 PROFILS GLOBAUX (lecture seule)                                 │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ 🥋 Dojo Essentials    │ 📅 Annuel │ 💰 2,99-9,99€ │ 👁️ Voir   ││
│ │ 5,234 actifs · €47,892/mois                                    ││
│ └─────────────────────────────────────────────────────────────────┘│
│ ... autres profils globaux ...                                      │
│                                                                     │
│ 🏢 PROFILS ÉVÉNEMENT                                               │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ 🎫 Pack Compétition   │ 📅 Event │ 💰 15€/pers │ ✏️ 🗑️        ││
│ │ 847 utilisations · €12,705 générés                             ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

2. `templates/superadmin/memberships/detail.html` :
   - Header avec nom, type, statut
   - Section informations générales
   - Section features (liste avec icônes ✓/✗)
   - Section tarification
   - Section contraintes
   - Section statistiques (mini graphiques)
   - Boutons : Modifier, Dupliquer, Désactiver

3. `templates/superadmin/memberships/form.html` :
   - Wizard multi-étapes avec indicateur de progression
   - Étape 1 : Infos générales
   - Étape 2 : Features (checkboxes avec descriptions)
   - Étape 3 : Tarification (preview du prix calculé)
   - Étape 4 : Contraintes + Résumé
   - Navigation : Précédent / Suivant / Enregistrer

4. `templates/superadmin/memberships/stats.html` :
   - Graphique évolution des adhésions
   - Graphique revenus
   - Tableau des transformations
   - Export CSV

EXIGENCES :
- Pas de scroll sur les listes (pagination ou accordéon)
- Modales pour les actions de confirmation
- Transitions fluides entre sous-onglets
- Indicateurs visuels pour les profils les plus utilisés

Génère le code HTML/CSS complet.
```

### PROMPT 4.3 : API Memberships

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèles MembershipProfile, EventPass, MembershipTransformation
- Besoin d'API complète pour CRUD et statistiques

TÂCHE :
Crée les endpoints API pour les memberships.

FICHIERS :

1. `apps/superadmin/api/serializers.py` (ajouter) :

   - MembershipProfileListSerializer (résumé)
   - MembershipProfileDetailSerializer (complet)
   - MembershipProfileCreateSerializer (validation)
   - EventPassSerializer
   - MembershipTransformationSerializer
   - MembershipStatsSerializer

2. `apps/superadmin/api/viewsets.py` (ajouter) :

   MembershipProfileViewSet :
   - list() - GET /api/superadmin/memberships/
   - retrieve() - GET /api/superadmin/memberships/{id}/
   - create() - POST /api/superadmin/memberships/
   - update() - PUT /api/superadmin/memberships/{id}/
   - partial_update() - PATCH /api/superadmin/memberships/{id}/
   - destroy() - DELETE /api/superadmin/memberships/{id}/
   
   Actions personnalisées :
   - @action GET stats/ - Statistiques du profil
   - @action GET event-passes/ - EventPass liés
   - @action POST duplicate/ - Dupliquer le profil
   - @action POST toggle-active/ - Activer/Désactiver

   EventPassViewSet :
   - list() - Filtrable par profil, compétition, statut
   - @action POST approve/ - Approuver un pass
   - @action POST cancel/ - Annuler un pass

   TransformationViewSet (lecture seule) :
   - list() - Historique des transformations
   - @action GET analytics/ - Taux de conversion

EXIGENCES :
- Filtres : DjangoFilterBackend
- Recherche : SearchFilter sur name, description
- Ordering : OrderingFilter
- Pagination : PageNumberPagination (20 par page)
- Permissions : IsSuperUser

Génère le code complet.
```

---

## 7. Phase 5 : Monitoring Système

### PROMPT 5.1 : Service Contrôle Système

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Serveur de production : IONOS avec Plesk
- Stack : Nginx → Apache/Passenger → Gunicorn → Django
- Services : PostgreSQL, Redis, Celery, Celery Beat
- CRITIQUE : Les actions de contrôle doivent être sécurisées

TÂCHE :
Crée le service de contrôle système.

FICHIER : `apps/superadmin/services/system_control.py`

CLASSE `SystemControlService` :

1. `restart_gunicorn()` → dict :
   - Redémarre les workers Gunicorn gracefully
   - Commande : `sudo systemctl reload gunicorn` ou signal HUP
   - Retourne : {"success": bool, "message": str, "pid": int}

2. `enable_maintenance_mode()` → dict :
   - Crée un fichier flag que Nginx détecte
   - Nginx sert une page statique de maintenance
   - Retourne : {"success": bool, "enabled_at": datetime}

3. `disable_maintenance_mode()` → dict :
   - Supprime le fichier flag
   - Retourne : {"success": bool, "disabled_at": datetime}

4. `emergency_stop()` → dict :
   - ⚠️ DANGER : Arrête tous les services
   - Requiert confirmation double
   - Log détaillé obligatoire
   - Retourne : {"success": bool, "services_stopped": list}

5. `get_service_status(service_name)` → dict :
   - Vérifie un service spécifique
   - Utilise psutil pour PID, CPU, RAM
   - Retourne : {"status": str, "pid": int, "cpu": float, "memory_mb": float}

6. `restart_service(service_name)` → dict :
   - Redémarre un service spécifique
   - Services autorisés : ['gunicorn', 'celery', 'celery-beat', 'redis']
   - NE PAS permettre restart de nginx ou postgresql directement

7. `clear_cache()` → dict :
   - Vide le cache Redis de l'application
   - Retourne : {"success": bool, "keys_cleared": int}

8. `trigger_backup()` → dict :
   - Lance un backup DB immédiat
   - Utilise pg_dump
   - Retourne : {"success": bool, "backup_path": str, "size_mb": float}

CLASSE `SystemControlAudit` :
- Décorateur @audit_action pour logger toutes les actions
- Enregistre dans AdminAction

SÉCURITÉ :
- Toutes les méthodes nécessitent un utilisateur superuser
- Rate limiting : max 1 restart par minute
- Les commandes sudo sont pré-configurées dans sudoers (pas de password)
- Timeout sur toutes les commandes (30s max)

Génère le code complet avec gestion d'erreurs robuste.
```

### PROMPT 5.2 : Vue Monitoring Système

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service SystemControlService disponible
- Service MetricsService disponible
- Onglet "Système" dans l'admin

TÂCHE :
Crée la vue et le template du monitoring système.

FICHIERS :

1. `apps/superadmin/views/system.py` :

   - `SystemView(SuperAdminRequiredMixin, TemplateView)`
   - `RestartServiceView(SuperAdminRequiredMixin, View)` - POST
   - `MaintenanceModeView(SuperAdminRequiredMixin, View)` - POST
   - `EmergencyStopView(SuperAdminRequiredMixin, View)` - POST (avec confirmation)
   - `ClearCacheView(SuperAdminRequiredMixin, View)` - POST
   - `TriggerBackupView(SuperAdminRequiredMixin, View)` - POST

2. `templates/superadmin/system.html` :

LAYOUT :
```
┌─────────────────────────────────────────────────────────────────────┐
│ 💾 MONITORING SYSTÈME                              🔄 Refresh: 10s │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─── CONTRÔLE PLATEFORME ───────────────────────────────────────┐  │
│ │ État: 🟢 OPÉRATIONNEL                                         │  │
│ │                                                               │  │
│ │ [🔄 Redémarrer Gunicorn]  [⏸️ Mode Maintenance]  [🔴 ARRÊT]   │  │
│ │                                                               │  │
│ │ Dernière action: 🔄 Redémarrage - 12 Jan 09:45 par admin     │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌─── BASE DE DONNÉES ─────────┐  ┌─── STOCKAGE ─────────────────┐  │
│ │ PostgreSQL 15.4   🟢 OK     │  │ Total: 500 GB                │  │
│ │                             │  │ Utilisé: 127.4 GB (25.5%)    │  │
│ │ 📦 Taille: 55.2 GB         │  │ ████████░░░░░░░░░░░░░░░░░░░░ │  │
│ │ 📊 Tables: 267             │  │                              │  │
│ │ 🔗 Connexions: 45/100      │  │ 📁 media/    68.3 GB         │  │
│ │                             │  │ 📁 backups/  45.2 GB         │  │
│ │ Top tables:                 │  │ 📁 logs/     11.8 GB         │  │
│ │ 1. practitioner  12.4 GB   │  │                              │  │
│ │ 2. registration   8.7 GB   │  │ [🗑️ Nettoyer] [📦 Compresser]│  │
│ │                             │  │                              │  │
│ │ [📊 Analyse] [📥 Backup]   │  └──────────────────────────────┘  │
│ └─────────────────────────────┘                                    │
│                                                                     │
│ ┌─── SERVICES ──────────────────────────────────────────────────┐  │
│ │ Service      PID       CPU    RAM      État      Actions      │  │
│ │ ────────────────────────────────────────────────────────────  │  │
│ │ 🌐 Gunicorn  1827891   12%   2.4 GB   🟢 OK     [🔄] [📊]    │  │
│ │ 🗄️ Postgres  1234      8%    4.2 GB   🟢 OK     [📊]         │  │
│ │ 📦 Redis     5678      2%    512 MB   🟢 OK     [🔄] [📊]    │  │
│ │ 🔄 Celery    9012      5%    1.1 GB   🟢 OK     [🔄] [📊]    │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

MODALES :
- Confirmation restart (simple)
- Confirmation maintenance mode (checkbox "Je comprends")
- Confirmation arrêt d'urgence (double confirmation + raison obligatoire)

EXIGENCES :
- Boutons avec états (loading, disabled pendant action)
- Feedback visuel immédiat
- Auto-refresh des statuts (10s)
- Alertes visuelles si problème détecté

Génère le code complet.
```

### PROMPT 5.3 : API Système

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Service SystemControlService disponible
- Besoin d'API pour les actions système

TÂCHE :
Crée les endpoints API pour le contrôle système.

FICHIER : `apps/superadmin/api/viewsets.py` (ajouter)

ENDPOINTS :

SystemControlViewSet :

1. GET /api/superadmin/system/status/
   - Statut global de tous les services

2. GET /api/superadmin/system/services/
   - Liste des services avec détails

3. GET /api/superadmin/system/database/
   - Stats DB détaillées

4. GET /api/superadmin/system/storage/
   - Stats stockage détaillées

5. POST /api/superadmin/system/restart/
   - Body: {"service": "gunicorn"}
   - Rate limited : 1/minute

6. POST /api/superadmin/system/maintenance/
   - Body: {"enabled": true/false}

7. POST /api/superadmin/system/emergency-stop/
   - Body: {"confirmation": "STOP", "reason": "..."}
   - Double validation

8. POST /api/superadmin/system/clear-cache/

9. POST /api/superadmin/system/backup/
   - Lance backup async, retourne task_id

10. GET /api/superadmin/system/backup/{task_id}/
    - Statut du backup en cours

SÉCURITÉ :
- Permission : IsSuperUser AND IsAuthenticated
- Throttling strict sur les actions POST
- Logging de toutes les requêtes

Génère le code complet.
```

---

## 8. Phase 6 : Configuration

### PROMPT 6.1 : Vue Configuration

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèles existants : SubscriptionTier, FeatureFlag
- Paramètres globaux stockés en DB ou settings
- Besoin de configurer : features, régions/prix, email, sécurité

TÂCHE :
Crée la vue et les templates de configuration.

FICHIERS :

1. `apps/superadmin/views/config.py` :

   - `ConfigView` - Vue principale avec sous-onglets
   - `GeneralConfigView` - Paramètres généraux
   - `FeatureFlagsView` - Gestion des features
   - `RegionPricingView` - Tarification par région
   - `EmailConfigView` - Configuration email
   - `SecurityConfigView` - Paramètres sécurité

2. `templates/superadmin/config.html` :

LAYOUT avec sous-onglets :
```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ CONFIGURATION                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ [Général] [Feature Flags] [Régions/Prix] [Email] [Sécurité] [API]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─── GÉNÉRAL ───────────────────────────────────────────────────┐  │
│ │                                                               │  │
│ │ Nom plateforme:     [MartialComp_________________]           │  │
│ │ URL principale:     [https://www.martialcomp.com__]          │  │
│ │ Email support:      [support@martialcomp.com______]          │  │
│ │                                                               │  │
│ │ Mode maintenance:   ○ Activé  ● Désactivé                    │  │
│ │ Inscriptions:       ● Ouvertes  ○ Fermées                    │  │
│ │                                                               │  │
│ │                                        [💾 Enregistrer]       │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌─── FEATURE FLAGS ─────────────────────────────────────────────┐  │
│ │                                                               │  │
│ │ Feature                    État      Tiers        Actions    │  │
│ │ ──────────────────────────────────────────────────────────── │  │
│ │ 🏆 Création compétitions   [🟢 ON]   Master+      [✏️]       │  │
│ │ 📊 Notation technique      [🟢 ON]   Master+      [✏️]       │  │
│ │ ⚔️ Combat temps réel       [🟢 ON]   Champion     [✏️]       │  │
│ │ 📱 App mobile              [🟡 BETA] Tous         [✏️]       │  │
│ │ 🤖 IA Recommandations      [🔴 OFF]  Champion     [✏️]       │  │
│ │                                                               │  │
│ │ [+ Ajouter Feature]                                          │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

3. Forms pour chaque section

EXIGENCES :
- Validation en temps réel des champs
- Preview avant sauvegarde pour les changements critiques
- Historique des modifications (AdminAction)
- Export/Import de configuration (JSON)

Génère le code complet.
```

---

## 9. Phase 7 : Logs et Audit

### PROMPT 7.1 : Vue Logs

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Modèle AdminAction pour l'audit
- Logs Django standards
- Besoin de visualisation temps réel

TÂCHE :
Crée la vue et le template des logs.

FICHIERS :

1. `apps/superadmin/views/logs.py` :
   - `LogsView` - Vue principale
   - `LogsAPIView` - Endpoint pour le streaming

2. `templates/superadmin/logs.html` :

LAYOUT :
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📜 LOGS & AUDIT                                    [🔄 Live Mode]  │
├─────────────────────────────────────────────────────────────────────┤
│ Type: [Tous ▼] Niveau: [Tous ▼] Période: [24h ▼] [🔍 Rechercher]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─── LOGS APPLICATION ──────────────────────────────────────────┐  │
│ │                                                               │  │
│ │ 14:32:45 │ 🟢 INFO  │ AUTH   │ Login: user@example.com       │  │
│ │ 14:32:43 │ 🟢 INFO  │ COMPET │ Inscription #45892 créée      │  │
│ │ 14:32:41 │ 🟡 WARN  │ PAYMENT│ Timeout Stripe - retry 1/3    │  │
│ │ 14:32:38 │ 🔴 ERROR │ DB     │ Connection timeout            │  │
│ │ ...                                                           │  │
│ │                                                               │  │
│ │ [📥 Exporter] [🗑️ Archiver] [⚙️ Alertes]                     │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌─── AUDIT ACTIONS ADMIN ───────────────────────────────────────┐  │
│ │                                                               │  │
│ │ Date/Heure      Admin              Action                    │  │
│ │ ─────────────────────────────────────────────────────────── │  │
│ │ 14:30:12        admin@mc.com       🔄 Redémarrage Gunicorn   │  │
│ │ 13:45:23        bertrand@mc.com    ✏️ Modif. Feature Flag    │  │
│ │ 12:30:00        admin@mc.com       📦 Backup DB déclenché    │  │
│ │                                                               │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

FONCTIONNALITÉS :
- Mode live : auto-scroll avec nouveaux logs
- Filtrage par type, niveau, période
- Recherche full-text
- Export CSV/JSON
- Coloration syntaxique par niveau

3. `static/superadmin/js/logs.js` :
   - WebSocket pour streaming temps réel
   - Filtrage côté client
   - Virtual scrolling pour performance

Génère le code complet.
```

---

## 10. Phase 8 : Temps Réel (WebSocket)

### PROMPT 8.1 : Configuration Django Channels

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Django Channels à configurer
- Redis disponible
- Besoin de WebSocket pour : métriques, carte, logs

TÂCHE :
Configure Django Channels pour le temps réel.

FICHIERS :

1. `config/asgi.py` :
   - Configuration ASGI avec Channels
   - Routing WebSocket

2. `apps/superadmin/routing.py` :
   - Routes WebSocket pour superadmin

3. `apps/superadmin/consumers/realtime.py` :

   CONSUMERS :
   
   - `MetricsConsumer` :
     - ws://host/ws/superadmin/metrics/
     - Envoie les KPIs toutes les 30s
     - Envoie les alertes immédiatement
   
   - `MapConsumer` :
     - ws://host/ws/superadmin/map/
     - Envoie les nouvelles adhésions en temps réel
     - Broadcast à tous les admins connectés
   
   - `LogsConsumer` :
     - ws://host/ws/superadmin/logs/
     - Stream des logs en temps réel
     - Filtrage côté serveur basé sur les préférences client

4. `apps/superadmin/signals.py` :
   - Signal post_save sur User/Organization pour notifier MapConsumer
   - Signal post_save sur AdminAction pour LogsConsumer

EXIGENCES :
- Authentification WebSocket (token ou session)
- Reconnection automatique côté client
- Heartbeat pour détecter les déconnexions
- Gestion des erreurs gracieuse

Génère le code complet.
```

### PROMPT 8.2 : JavaScript Temps Réel

```
Tu es un développeur JavaScript senior travaillant sur MartialComp.

CONTEXTE :
- WebSocket configuré côté Django
- Besoin de gestion robuste côté client
- Templates utilisent Bootstrap 5

TÂCHE :
Crée le module JavaScript pour la gestion temps réel.

FICHIER : `static/superadmin/js/realtime.js`

CLASSE `RealtimeManager` :

```javascript
class RealtimeManager {
  constructor(options) {
    // Configuration
  }
  
  // Connexion avec reconnection automatique
  connect(endpoint) {}
  
  // Gestion des messages
  onMessage(type, callback) {}
  
  // Envoi de messages
  send(type, data) {}
  
  // Heartbeat
  startHeartbeat() {}
  
  // Déconnexion propre
  disconnect() {}
}
```

CLASSE `DashboardRealtime` :
- Gère les mises à jour du dashboard
- Anime les changements de valeurs
- Met à jour les graphiques

CLASSE `MapRealtime` :
- Ajoute les markers pour nouvelles adhésions
- Animation pulse sur nouveaux markers
- Met à jour les compteurs pays

CLASSE `LogsRealtime` :
- Append les nouveaux logs
- Auto-scroll si activé
- Filtrage temps réel

FICHIER : `static/superadmin/js/animations.js` :
- countUp() - Animation de compteur
- pulseMarker() - Animation marker carte
- flashRow() - Flash sur nouvelle ligne de log

EXIGENCES :
- ES6+ modules
- Gestion des erreurs réseau
- Fallback polling si WebSocket indisponible
- Performance optimisée (requestAnimationFrame)

Génère le code complet.
```

---

## 11. Tests et Validation

### PROMPT 11.1 : Tests Unitaires

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Application superadmin complète
- pytest-django utilisé
- Factory Boy pour les fixtures

TÂCHE :
Crée les tests unitaires pour l'application superadmin.

FICHIERS :

1. `apps/superadmin/tests/test_models.py` :
   - Tests MembershipProfile (création, validation, méthodes)
   - Tests EventPass (cycle de vie, expiration)
   - Tests MembershipTransformation (calculs)
   - Tests SystemMetric (agrégations)
   - Tests AdminAction (audit)

2. `apps/superadmin/tests/test_services.py` :
   - Tests MetricsService (tous les getters)
   - Tests GeoStatsService (agrégations pays)
   - Tests SystemControlService (mock des commandes système)

3. `apps/superadmin/tests/test_views.py` :
   - Tests accès (superuser requis)
   - Tests dashboard (context data)
   - Tests CRUD memberships
   - Tests actions système (avec mock)

4. `apps/superadmin/tests/test_api.py` :
   - Tests endpoints REST
   - Tests permissions
   - Tests throttling

5. `apps/superadmin/tests/factories.py` :
   - MembershipProfileFactory
   - EventPassFactory
   - SystemMetricFactory
   - AdminActionFactory

EXIGENCES :
- Coverage > 80%
- Tests isolation (pas d'effets de bord)
- Mock des services externes (Redis, système)
- Tests des cas limites

Génère le code complet.
```

### PROMPT 11.2 : Tests d'Intégration

```
Tu es un développeur Django senior travaillant sur MartialComp.

CONTEXTE :
- Tests unitaires créés
- Besoin de tester les flux complets

TÂCHE :
Crée les tests d'intégration.

FICHIERS :

1. `apps/superadmin/tests/test_integration.py` :

   Tests de flux complets :
   
   - test_membership_lifecycle :
     - Création profil → Utilisation → Stats → Désactivation
   
   - test_event_pass_workflow :
     - Création → Approbation → Utilisation → Expiration
   
   - test_transformation_tracking :
     - Non-membre → Membre → Upgrade
   
   - test_dashboard_data_consistency :
     - Création données → Vérification KPIs → Vérification graphiques
   
   - test_system_control_safety :
     - Rate limiting → Audit logging → Permissions

2. `apps/superadmin/tests/test_websocket.py` :
   - Tests consumers WebSocket
   - Tests broadcast
   - Tests reconnection

EXIGENCES :
- Utiliser pytest-asyncio pour WebSocket
- Transactions pour isolation
- Cleanup après chaque test

Génère le code complet.
```

---

## 12. Déploiement

### PROMPT 12.1 : Script de Déploiement

```
Tu es un DevOps senior travaillant sur MartialComp.

CONTEXTE :
- Serveur : IONOS avec Plesk
- Stack : Nginx → Gunicorn → Django
- Application superadmin à déployer

TÂCHE :
Crée les scripts de déploiement.

FICHIERS :

1. `scripts/deploy_superadmin.sh` :
   - Backup DB avant migration
   - Pull du code
   - Installation dépendances
   - Migrations
   - Collectstatic
   - Restart services
   - Vérification santé

2. `scripts/rollback_superadmin.sh` :
   - Restauration backup
   - Revert code
   - Restart services

3. `docs/SUPERADMIN_DEPLOYMENT.md` :
   - Prérequis
   - Étapes de déploiement
   - Configuration Nginx pour WebSocket
   - Configuration Redis
   - Vérifications post-déploiement
   - Troubleshooting

4. Configuration Nginx pour WebSocket :
   ```nginx
   location /ws/ {
       proxy_pass http://unix:/run/daphne.sock;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

5. Configuration Supervisor pour Daphne :
   - daphne.conf

EXIGENCES :
- Zero downtime deployment
- Rollback automatique si échec
- Notifications Slack/Email

Génère tous les fichiers.
```

### PROMPT 12.2 : Documentation

```
Tu es un technical writer travaillant sur MartialComp.

CONTEXTE :
- Application superadmin complète
- Besoin de documentation utilisateur et technique

TÂCHE :
Crée la documentation complète.

FICHIERS :

1. `docs/superadmin/USER_GUIDE.md` :
   - Introduction
   - Accès à l'interface
   - Dashboard : lecture des KPIs
   - Carte : navigation et interprétation
   - Memberships : création et gestion
   - Système : monitoring et actions
   - Configuration : paramètres
   - Logs : consultation et export
   - FAQ

2. `docs/superadmin/TECHNICAL_GUIDE.md` :
   - Architecture
   - Modèles de données
   - Services
   - API Reference
   - WebSocket
   - Tests
   - Déploiement
   - Maintenance

3. `docs/superadmin/API_REFERENCE.md` :
   - Authentification
   - Endpoints détaillés
   - Exemples de requêtes
   - Codes d'erreur

4. `docs/superadmin/TROUBLESHOOTING.md` :
   - Problèmes courants
   - Logs à vérifier
   - Solutions

Génère la documentation complète avec exemples.
```

---

## 📊 Matrice de Suivi d'Implémentation

| Phase | Prompt | Statut | Responsable | Date Fin |
|-------|--------|--------|-------------|----------|
| 1 | 1.1 Configuration App | ⬜ | | |
| 1 | 1.2 Modèles Membership | ⬜ | | |
| 1 | 1.3 Modèles Monitoring | ⬜ | | |
| 1 | 1.4 Migrations/Fixtures | ⬜ | | |
| 2 | 2.1 Service Métriques | ⬜ | | |
| 2 | 2.2 Tâches Celery | ⬜ | | |
| 2 | 2.3 Vue Dashboard | ⬜ | | |
| 2 | 2.4 API Dashboard | ⬜ | | |
| 3 | 3.1 Service Géostats | ⬜ | | |
| 3 | 3.2 Vue/Template Carte | ⬜ | | |
| 3 | 3.3 API Carte | ⬜ | | |
| 4 | 4.1 Vues Memberships | ⬜ | | |
| 4 | 4.2 Templates Memberships | ⬜ | | |
| 4 | 4.3 API Memberships | ⬜ | | |
| 5 | 5.1 Service Contrôle | ⬜ | | |
| 5 | 5.2 Vue Système | ⬜ | | |
| 5 | 5.3 API Système | ⬜ | | |
| 6 | 6.1 Vue Configuration | ⬜ | | |
| 7 | 7.1 Vue Logs | ⬜ | | |
| 8 | 8.1 Django Channels | ⬜ | | |
| 8 | 8.2 JS Temps Réel | ⬜ | | |
| 11 | 11.1 Tests Unitaires | ⬜ | | |
| 11 | 11.2 Tests Intégration | ⬜ | | |
| 12 | 12.1 Scripts Déploiement | ⬜ | | |
| 12 | 12.2 Documentation | ⬜ | | |

---

## 🔗 Annexes

### A. Diagramme de Classes

```
┌─────────────────────┐       ┌─────────────────────┐
│  MembershipProfile  │       │    EventPass        │
├─────────────────────┤       ├─────────────────────┤
│ - name              │◄──────│ - membership_profile│
│ - profile_type      │       │ - user              │
│ - validity_type     │       │ - competition       │
│ - pricing_model     │       │ - status            │
│ - is_global         │       │ - expires_at        │
└─────────────────────┘       └─────────────────────┘
         │
         │ FK
         ▼
┌─────────────────────┐
│ SubscriptionTier    │
└─────────────────────┘
```

### B. Flux de Données Temps Réel

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Django  │───►│  Celery  │───►│  Redis   │───►│ Channels │
│  Signal  │    │  Task    │    │  Pub/Sub │    │ Consumer │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
                                                     ▼
                                              ┌──────────┐
                                              │ Browser  │
                                              │ WebSocket│
                                              └──────────┘
```

### C. Checklist Sécurité

- [ ] 2FA obligatoire pour Super Admin
- [ ] Rate limiting sur actions critiques
- [ ] Audit trail complet
- [ ] Confirmation double pour arrêt d'urgence
- [ ] Timeout sur toutes les commandes système
- [ ] Permissions granulaires vérifiées
- [ ] Logs des accès WebSocket
- [ ] Validation des inputs API

---

**Document généré le** : Janvier 2025  
**Version** : 1.0  
**Prochaine révision** : Après Phase 4
