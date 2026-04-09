# RÉCAPITULATIF PHASE 1 : URLs ET DONNÉES MANQUANTES

**Date :** 3 novembre 2025  
**Phase :** Phase 1 - Préparation

---

## ✅ TEMPLATES PARTIELS CRÉÉS

### 1. Templates Dashboard (2 fichiers créés)

#### ✅ `dashboard/partials/competitions_scoring.html`
**Statut :** ✅ **CRÉÉ**  
**Localisation :** `/apps/competitions/templates/competitions/dashboard/partials/competitions_scoring.html`  
**Usage :** Section Scoring pour l'onglet Compétitions du Dashboard Club

**Fonctionnalités :**
- Statistiques globales scoring (performances totales, terminées, en attente, progression)
- Liste des compétitions avec progression scoring par compétition
- Accès rapide aux interfaces de notation
- Liste des performances prioritaires à noter

**Variables nécessaires :**
- `competitions_to_manage` : Liste des compétitions à gérer
- `scoring_stats` : Dictionnaire avec statistiques par compétition
  - `scoring_stats[competition.id].total_performances`
  - `scoring_stats[competition.id].completed_performances`
  - `scoring_stats[competition.id].pending_performances`
  - `scoring_stats[competition.id].progress_percent`
- `pending_performances` : Liste des performances en attente de notation
- `scoring_stats.total_performances` : Total global
- `scoring_stats.completed_performances` : Total terminées
- `scoring_stats.pending_performances` : Total en attente
- `scoring_stats.progress_percent` : Progression globale

#### ✅ `dashboard/partials/competitions_combat.html`
**Statut :** ✅ **CRÉÉ**  
**Localisation :** `/apps/competitions/templates/competitions/dashboard/partials/competitions_combat.html`  
**Usage :** Section Combat pour l'onglet Compétitions du Dashboard Club

**Fonctionnalités :**
- Statistiques globales combat (totaux, en cours, terminés, taux de victoire)
- Liste des combats actifs avec statut et scores
- Combats récents avec résultats
- Accès rapide aux interfaces de combat
- Section interface Taekwondo spécialisée
- Section affichage public plein écran

**Variables nécessaires :**
- `active_combats` : Liste des combats actifs (status='en_cours')
- `recent_combats` : Liste des combats récents
- `combat_stats` : Dictionnaire avec statistiques globales
  - `combat_stats.total_combats`
  - `combat_stats.en_cours`
  - `combat_stats.termines`
  - `combat_stats.win_rate`
- `taekwondo_combats` : Liste des combats Taekwondo (optionnel)

### 2. Templates Hub (2 fichiers créés)

#### ✅ `club/hub/partials/scoring_section.html`
**Statut :** ✅ **CRÉÉ**  
**Localisation :** `/apps/competitions/templates/competitions/club/hub/partials/scoring_section.html`  
**Usage :** Catégorie "Notation & Scoring" dans le Competition Hub

**Fonctionnalités :**
- 6 cartes d'accès aux interfaces de scoring
- Dashboard Scoring Admin
- Interface Admin Scoring
- Scoring Technique
- Scoring Standalone
- Configuration Critères
- Historique Scoring

**Variables nécessaires :**
- `competition` : Compétition actuelle
- `categories` : Liste des catégories (pour la première carte de critères)
- `stats` : Statistiques enrichies
  - `stats.scoring_total_performances`
  - `stats.judges_count`
  - `stats.total_categories`

#### ✅ `club/hub/partials/combat_section.html`
**Statut :** ✅ **CRÉÉ**  
**Localisation :** `/apps/competitions/templates/competitions/club/hub/partials/combat_section.html`  
**Usage :** Catégorie "Combat en Direct" dans le Competition Hub

**Fonctionnalités :**
- 5 cartes d'accès aux interfaces de combat
- Liste des Combats
- Interface Combat Générale
- Interface Taekwondo
- Monitoring Live
- Affichage Public

**Variables nécessaires :**
- `competition` : Compétition actuelle
- `active_combats` : Liste des combats actifs
- `taekwondo_combats` : Liste des combats Taekwondo (optionnel)
- `combat_stats` : Statistiques combat
  - `combat_stats.total_combats`

---

## ⚠️ URLS MANQUANTES À CRÉER/VÉRIFIER

### 1. URLs Standalone Scoring

**Problème identifié :**
- Les vues `standalone_scoring` utilisent le namespace `competitions:standalone_scoring`
- Mais ce namespace n'est pas défini dans `urls/__init__.py`

**URLs nécessaires :**
```python
# À ajouter dans urls/__init__.py
path('standalone-scoring/', include('apps.competitions.urls.standalone_scoring', namespace='standalone_scoring')),
```

**Fichier à créer :** `urls/standalone_scoring.py`

**URLs à définir :**
- `judge/performances/` → `JudgePerformanceListView` (name='judge_performances')
- `judge/score/<int:performance_id>/` → `JudgeScoreEntryView` (name='judge_score_entry')
- `judge/submit-scores/<int:performance_id>/` → `JudgeSubmitScoresView` (name='judge_submit_scores')
- `admin/dashboard/` → `StandaloneScoringDashboardView` (name='admin_dashboard')
- `admin/calculate-results/` → `ResultsCalculationView` (name='calculate_results')

**Actions nécessaires :**
1. Créer `urls/standalone_scoring.py`
2. Ajouter le path dans `urls/__init__.py`

### 2. URLs Combat Taekwondo

**Problème identifié :**
- Les vues `combat_taekwondo` existent mais pas de namespace défini
- URL `competitions:combat_taekwondo:interface_combat` utilisée dans les templates

**URLs nécessaires :**
```python
# À ajouter dans urls/__init__.py
path('combat/taekwondo/', include('apps.competitions.urls.combat_taekwondo', namespace='combat_taekwondo')),
```

**Fichier à créer :** `urls/combat_taekwondo.py`

**URLs à définir (basées sur les vues) :**
- `combats/` → `liste_combats_taekwondo` (name='liste_combats')
- `combats/<int:combat_id>/` → `detail_combat_taekwondo` (name='detail_combat')
- `combats/<int:combat_id>/interface/` → `interface_combat_taekwondo` (name='interface_combat')
- `combats/<int:combat_id>/ajouter-action/` → `ajouter_action_taekwondo` (name='ajouter_action')
- `combats/<int:combat_id>/api-statut/` → `api_statut_combat_taekwondo` (name='api_statut_combat')
- `combats/<int:combat_id>/terminer/` → `terminer_combat_taekwondo` (name='terminer_combat')

**Actions nécessaires :**
1. Créer `urls/combat_taekwondo.py`
2. Ajouter le path dans `urls/__init__.py`

### 3. URLs Management Scoring

**Statut :** ✅ **VÉRIFIÉ**  
**Problème :** Les URLs management scoring ne sont pas dans un fichier séparé mais intégrées dans les vues

**URLs nécessaires :**
- `competitions:management:scoring_dashboard` → `scoring_dashboard(competition_id)`
- `competitions:management:judge_scoring_interface` → `judge_scoring_interface(competition_id, category_id, judge_id)`

**Problème identifié :**
- Le namespace `management` n'est pas défini dans les URLs principales
- Les vues sont dans `views/management/scoring.py` mais pas de URLs dédiées

**Actions nécessaires :**
1. Créer `urls/management.py` OU intégrer dans `urls/club.py` OU créer des URLs dans `urls/technical_scoring.py`
2. Vérifier comment accéder aux vues management depuis le hub

**Solution proposée :**
- Option 1 : Ajouter dans `urls/club.py` avec namespace `management`
- Option 2 : Utiliser les URLs existantes de `technical_scoring` avec paramètres

### 4. URLs Scoring Général

**URLs utilisées dans les templates :**
- `competitions:scoring:criteria` → Vue pour configurer les critères

**Problème identifié :**
- Le namespace `scoring` n'existe pas
- Besoin de créer ou utiliser un namespace existant

**Actions nécessaires :**
1. Vérifier si les URLs scoring général existent
2. Créer le namespace si nécessaire ou adapter les templates

---

## 📊 DONNÉES MANQUANTES À ENRICHIR

### 1. Contexte `club_dashboard` (views/dashboard/club.py)

**Données à ajouter :**

#### Scoring Stats (par compétition)

```python
# À ajouter après récupération de club_competitions
scoring_stats = {}
scoring_stats_global = {
    'total_performances': 0,
    'completed_performances': 0,
    'pending_performances': 0,
    'progress_percent': 0
}

try:
    from ...models.technical_scoring import TechnicalPerformance
    
    total_all = 0
    completed_all = 0
    pending_all = 0
    
    for competition in club_competitions:
        # Récupérer toutes les catégories de la compétition
        categories = CompetitionCategory.objects.filter(competition=competition)
        
        # Récupérer toutes les performances pour ces catégories
        performances = TechnicalPerformance.objects.filter(
            category__in=categories
        )
        
        total = performances.count()
        completed = performances.filter(status='completed').count()
        pending = performances.filter(status__in=['pending', 'in_progress']).count()
        progress = (completed / total * 100) if total > 0 else 0
        
        scoring_stats[competition.id] = {
            'total_performances': total,
            'completed_performances': completed,
            'pending_performances': pending,
            'progress_percent': int(progress)
        }
        
        total_all += total
        completed_all += completed
        pending_all += pending
    
    scoring_stats_global.update({
        'total_performances': total_all,
        'completed_performances': completed_all,
        'pending_performances': pending_all,
        'progress_percent': int((completed_all / total_all * 100) if total_all > 0 else 0)
    })
except Exception as e:
    logger.error(f"Erreur lors de la récupération des stats scoring: {str(e)}")

# Récupérer les performances en attente
pending_performances = []
try:
    categories_all = CompetitionCategory.objects.filter(
        competition__in=club_competitions
    )
    pending_performances = TechnicalPerformance.objects.filter(
        category__in=categories_all,
        status__in=['pending', 'in_progress']
    ).select_related('practitioner', 'category', 'category__competition')[:10]
except Exception as e:
    logger.error(f"Erreur lors de la récupération des performances en attente: {str(e)}")
```

#### Combat Stats (par compétition)

```python
# À enrichir (déjà partiellement présent mais à compléter)
combat_stats_by_competition = {}
combat_stats_global = {
    'total_combats': 0,
    'en_cours': 0,
    'termines': 0,
    'planifies': 0,
    'win_rate': 0
}

try:
    from ...models.combat import Combat
    
    total_combats_all = 0
    en_cours_all = 0
    termines_all = 0
    planifies_all = 0
    victories_all = 0
    
    for competition in club_competitions:
        combats = Combat.objects.filter(competition=competition)
        
        total = combats.count()
        en_cours = combats.filter(status='en_cours').count()
        termines = combats.filter(status='termine').count()
        planifies = combats.filter(status='planifie').count()
        
        # Calculer victoires (approximatif)
        victories = combats.filter(
            status='termine',
            vainqueur__in=['rouge', 'blanc']
        ).count()
        
        combat_stats_by_competition[competition.id] = {
            'total_combats': total,
            'en_cours': en_cours,
            'termines': termines,
            'planifies': planifies,
            'victories': victories
        }
        
        total_combats_all += total
        en_cours_all += en_cours
        termines_all += termines
        planifies_all += planifies
        victories_all += victories
    
    win_rate = (victories_all * 100) // termines_all if termines_all > 0 else 0
    
    combat_stats_global.update({
        'total_combats': total_combats_all,
        'en_cours': en_cours_all,
        'termines': termines_all,
        'planifies': planifies_all,
        'win_rate': win_rate
    })
except Exception as e:
    logger.error(f"Erreur lors de la récupération des stats combat: {str(e)}")

# Récupérer les combats actifs et récents
active_combats = []
recent_combats = []
try:
    active_combats = Combat.objects.filter(
        competition__in=club_competitions,
        status='en_cours'
    ).select_related(
        'competition', 'pratiquant_rouge', 'pratiquant_blanc',
        'equipe_rouge', 'equipe_blanc', 'poule'
    ).order_by('-updated_at')[:10]
    
    recent_combats = Combat.objects.filter(
        competition__in=club_competitions
    ).select_related(
        'competition', 'pratiquant_rouge', 'pratiquant_blanc',
        'equipe_rouge', 'equipe_blanc', 'poule'
    ).order_by('-updated_at')[:10]
except Exception as e:
    logger.error(f"Erreur lors de la récupération des combats: {str(e)}")

# Récupérer les combats Taekwondo
taekwondo_combats = []
try:
    taekwondo_combats = Combat.objects.filter(
        competition__in=club_competitions,
        configuration__system='taekwondo',
        status='en_cours'
    ).select_related(
        'competition', 'pratiquant_rouge', 'pratiquant_blanc',
        'equipe_rouge', 'equipe_blanc', 'poule', 'configuration'
    ).order_by('-updated_at')[:5]
except Exception as e:
    logger.error(f"Erreur lors de la récupération des combats Taekwondo: {str(e)}")
```

#### Contexte enrichi

```python
# Ajouter au contexte club_dashboard
context.update({
    'scoring_stats': scoring_stats,
    'scoring_stats_global': scoring_stats_global,
    'pending_performances': pending_performances,
    'combat_stats': combat_stats_global,  # Utiliser les stats globales
    'combat_stats_by_competition': combat_stats_by_competition,
    'active_combats': active_combats,
    'recent_combats': recent_combats,
    'taekwondo_combats': taekwondo_combats,
})
```

### 2. Contexte `competition_hub` (views/club/competition_hub.py)

**Données à ajouter :**

```python
# Scoring stats par catégorie
try:
    from ...models.technical_scoring import TechnicalPerformance
    
    categories = CompetitionCategory.objects.filter(competition=competition)
    scoring_stats = {}
    
    for category in categories:
        performances = TechnicalPerformance.objects.filter(category=category)
        total = performances.count()
        completed = performances.filter(status='completed').count()
        
        scoring_stats[category.id] = {
            'total_performances': total,
            'completed_performances': completed,
            'pending_performances': total - completed,
            'progress_percent': int((completed / total * 100) if total > 0 else 0)
        }
except Exception as e:
    logger.error(f"Erreur scoring stats: {str(e)}")
    scoring_stats = {}

# Combat stats pour cette compétition
try:
    from ...models.combat import Combat
    
    combats = Combat.objects.filter(competition=competition)
    active_combats = combats.filter(status='en_cours').select_related(
        'pratiquant_rouge', 'pratiquant_blanc', 'equipe_rouge', 'equipe_blanc', 'poule'
    ).order_by('-updated_at')[:10]
    
    taekwondo_combats = combats.filter(
        configuration__system='taekwondo',
        status='en_cours'
    ).select_related(
        'pratiquant_rouge', 'pratiquant_blanc', 'equipe_rouge', 'equipe_blanc', 'poule', 'configuration'
    ).order_by('-updated_at')[:5]
    
    combat_stats = {
        'total_combats': combats.count(),
        'en_cours': combats.filter(status='en_cours').count(),
        'termines': combats.filter(status='termine').count(),
        'planifies': combats.filter(status='planifie').count(),
    }
except Exception as e:
    logger.error(f"Erreur combat stats: {str(e)}")
    active_combats = []
    taekwondo_combats = []
    combat_stats = {}

# Enrichir stats existantes
stats.update({
    'scoring_total_performances': sum(s['total_performances'] for s in scoring_stats.values()),
    'judges_count': JudgeAssignment.objects.filter(
        category__competition=competition
    ).distinct('user').count(),
})

# Ajouter au contexte
context.update({
    'scoring_stats': scoring_stats,
    'combat_stats': combat_stats,
    'active_combats': active_combats,
    'taekwondo_combats': taekwondo_combats,
    'categories': categories,  # Nécessaire pour la carte critères
})
```

---

## 📝 FICHIERS À CRÉER

### 1. URLs Standalone Scoring

**Fichier :** `urls/standalone_scoring.py`

```python
from django.urls import path
from apps.competitions.views.standalone_scoring import (
    JudgePerformanceListView,
    JudgeScoreEntryView,
    JudgeSubmitScoresView,
    StandaloneScoringDashboardView,
    ResultsCalculationView,
    RankingsListView,
)

app_name = 'standalone_scoring'

urlpatterns = [
    # Judge URLs
    path('judge/performances/', JudgePerformanceListView.as_view(), name='judge_performances'),
    path('judge/score/<int:performance_id>/', JudgeScoreEntryView.as_view(), name='judge_score_entry'),
    path('judge/submit-scores/<int:performance_id>/', JudgeSubmitScoresView.as_view(), name='judge_submit_scores'),
    
    # Admin URLs
    path('admin/dashboard/', StandaloneScoringDashboardView.as_view(), name='admin_dashboard'),
    path('admin/calculate-results/', ResultsCalculationView.as_view(), name='calculate_results'),
    path('admin/rankings/', RankingsListView.as_view(), name='rankings'),
]
```

**À ajouter dans `urls/__init__.py` :**
```python
path('standalone-scoring/', include('apps.competitions.urls.standalone_scoring', namespace='standalone_scoring')),
```

### 2. URLs Combat Taekwondo

**Fichier :** `urls/combat_taekwondo.py`

```python
from django.urls import path
from apps.competitions.views import combat_taekwondo

app_name = 'combat_taekwondo'

urlpatterns = [
    path('combats/', combat_taekwondo.liste_combats_taekwondo, name='liste_combats'),
    path('combats/competition/<int:competition_id>/', combat_taekwondo.liste_combats_taekwondo, name='liste_combats_competition'),
    path('combats/<int:combat_id>/', combat_taekwondo.detail_combat_taekwondo, name='detail_combat'),
    path('combats/<int:combat_id>/interface/', combat_taekwondo.interface_combat_taekwondo, name='interface_combat'),
    path('combats/<int:combat_id>/ajouter-action/', combat_taekwondo.ajouter_action_taekwondo, name='ajouter_action'),
    path('combats/<int:combat_id>/api-statut/', combat_taekwondo.api_statut_combat_taekwondo, name='api_statut_combat'),
    path('combats/<int:combat_id>/terminer/', combat_taekwondo.terminer_combat_taekwondo, name='terminer_combat'),
]
```

**À ajouter dans `urls/__init__.py` :**
```python
path('combat/taekwondo/', include('apps.competitions.urls.combat_taekwondo', namespace='combat_taekwondo')),
```

### 3. URLs Management (Option)

**Fichier :** `urls/management.py` (SI nécessaire)

```python
from django.urls import path
from apps.competitions.views.management import scoring

app_name = 'management'

urlpatterns = [
    path('scoring/<int:competition_id>/', scoring.scoring_dashboard, name='scoring_dashboard'),
    path('scoring/<int:competition_id>/category/<int:category_id>/judge/<int:judge_id>/', 
         scoring.judge_scoring_interface, name='judge_scoring_interface'),
]
```

**À ajouter dans `urls/__init__.py` :**
```python
path('management/', include('apps.competitions.urls.management', namespace='management')),
```

**Alternative :** Utiliser les URLs existantes dans `urls/technical_scoring.py` ou `urls/club.py`

---

## 🔧 CORRECTIONS NÉCESSAIRES

### 1. Filtre `get_item` amélioration

**Statut :** ✅ **EXISTANT**  
**Fichier :** `templatetags/custom_filters.py` ligne 17-46

**Problème identifié :**
- Le filtre retourne un dictionnaire vide `{}` au lieu d'une valeur par défaut
- Dans les templates, on utilise `scoring_stats|get_item:competition.id|default:{}` mais cela peut poser problème

**Correction suggérée :**
```python
@register.filter
def get_item(dictionary, key, default=None):
    """
    Récupère un élément d'un dictionnaire par sa clé
    Retourne default si la clé n'existe pas ou si le dictionnaire est None
    """
    if dictionary is None:
        return default or {}
    
    # ... code existant ...
    
    return dictionary.get(key_value, default or {})
```

**OU** utiliser `get_item` avec valeur par défaut dans le template :
```django
{% with stats=scoring_stats|get_item:competition.id %}
  {% if stats %}
    {{ stats.total_performances }}
  {% else %}
    0
  {% endif %}
{% endwith %}
```

### 2. URLs Combat manquantes

**Problème :** Certaines URLs utilisées dans les templates partiels n'existent pas encore

**URLs à vérifier :**
- `competitions:combat:liste_combats_competition` → Existe dans `urls/combat.py` ligne 29
- `competitions:combat_taekwondo:interface_combat` → À créer dans `urls/combat_taekwondo.py`
- `competitions:combat_taekwondo:*` → Toutes les URLs Taekwondo à créer

---

## ✅ RÉSUMÉ PHASE 1

### Templates créés (4/4) ✅

1. ✅ `dashboard/partials/competitions_scoring.html`
2. ✅ `dashboard/partials/competitions_combat.html`
3. ✅ `club/hub/partials/scoring_section.html`
4. ✅ `club/hub/partials/combat_section.html`

### URLs à créer (2 fichiers)

1. ⚠️ `urls/standalone_scoring.py` - **À CRÉER**
2. ⚠️ `urls/combat_taekwondo.py` - **À CRÉER**

### URLs à vérifier/corriger

1. ⚠️ `competitions:management:scoring_dashboard` - **À VÉRIFIER**
2. ⚠️ `competitions:management:judge_scoring_interface` - **À VÉRIFIER**
3. ⚠️ `competitions:scoring:criteria` - **À VÉRIFIER**

### Données à enrichir (2 vues)

1. ⚠️ `views/dashboard/club.py` - **À ENRICHIR**
2. ⚠️ `views/club/competition_hub.py` - **À ENRICHIR**

---

## 🎯 PROCHAINES ÉTAPES

### Phase 1 suite (à compléter)

1. ✅ Créer templates partiels (TERMINÉ)
2. ⚠️ Créer `urls/standalone_scoring.py`
3. ⚠️ Créer `urls/combat_taekwondo.py`
4. ⚠️ Vérifier/corriger URLs management
5. ⚠️ Vérifier/corriger URLs scoring général
6. ⚠️ Enrichir contexte `club_dashboard`
7. ⚠️ Enrichir contexte `competition_hub`

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ⏳ En cours (4/7 tâches terminées)
