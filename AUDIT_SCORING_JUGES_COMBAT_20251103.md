# AUDIT APPROFONDI - SCORING DES JUGES TECHNIQUES ET GESTION DES COMBATS

**Date de l'audit :** 3 novembre 2025  
**Domaine d'analyse :** Gestion de compétition - Scoring technique et combat en temps réel  
**Répertoire analysé :** `/apps/competitions`

---

## TABLE DES MATIÈRES

1. [Architecture générale](#1-architecture-générale)
2. [Fonctionnalités de scoring technique](#2-fonctionnalités-de-scoring-technique)
3. [Gestion des combats en temps réel](#3-gestion-des-combats-en-temps-réel)
4. [Templates de notation](#4-templates-de-notation)
5. [Flux d'accès des juges](#5-flux-daccès-des-juges)
6. [Système WebSocket et temps réel](#6-système-websocket-et-temps-réel)
7. [Recommandations](#7-recommandations)

---

## 1. ARCHITECTURE GÉNÉRALE

### 1.1 Modules principaux identifiés

Le système de gestion des compétitions est organisé en plusieurs modules :

#### A. **Scoring Technique** (`technical_scoring`)
- Module dédié à la notation des performances techniques
- Localisation : `apps/competitions/views/technical_scoring.py`
- URLs : `apps/competitions/urls/technical_scoring.py`

#### B. **Standalone Scoring** (`standalone_scoring`)
- Système de scoring indépendant et complet
- Localisation : `apps/competitions/views/standalone_scoring.py`
- URLs : `apps/competitions/urls/standalone_scoring.py`

#### C. **Combat** (`combat`)
- Module pour la gestion des combats (Taekwondo et autres disciplines)
- Localisation : `apps/competitions/views/combat.py`
- URLs : `apps/competitions/urls/combat.py`

#### D. **WebSocket Consumers** (`consumers.py`)
- Gestion des communications en temps réel via WebSocket
- Localisation : `apps/competitions/consumers.py`

---

## 2. FONCTIONNALITÉS DE SCORING TECHNIQUE

### 2.1 Systèmes de scoring disponibles

#### **A. Technical Scoring System**
**Fichier principal :** `apps/competitions/views/technical_scoring.py`

**Fonctionnalités principales :**
- ✅ Configuration des catégories de notation
- ✅ Affectation des juges aux catégories
- ✅ Gestion des performances
- ✅ Interface de notation pour les juges
- ✅ Suivi en temps réel
- ✅ Calcul et publication des résultats

**Modèles de données :**
- `ScoringCriterion` : Critères de notation
- `JudgeSubmissionStatus` : Statut des soumissions des juges
- `JudgeSettings` : Paramètres des juges
- `JudgeApplication` : Candidatures de juges
- `ScoringConfiguration` : Configuration du scoring

#### **B. Standalone Scoring System**
**Fichier principal :** `apps/competitions/views/standalone_scoring.py`

**Fonctionnalités principales :**
- ✅ Système complet et indépendant
- ✅ Gestion des performances
- ✅ Interface dédiée aux juges
- ✅ Système de ranking et snapshots
- ✅ Configuration par catégorie

**Modèles de données :**
- `StandaloneScoringSystem` : Système de notation
- `StandaloneScoringCriterion` : Critères
- `StandaloneCategoryScoringConfig` : Configuration par catégorie
- `StandalonePerformance` : Performances
- `StandaloneScore` : Scores individuels
- `StandaloneJudgeSubmission` : Soumissions des juges
- `StandaloneJudgeSettings` : Paramètres
- `StandaloneCompetitionRanking` : Classements

### 2.2 Interfaces de notation pour les juges

#### **Vue principale :** `judge_dashboard`
**URL :** `/technical-scoring/judge/dashboard/`
**Template :** `apps/competitions/templates/competitions/technical_scoring/judge_dashboard.html`

**Fonctionnalités :**
- Liste des compétitions assignées
- Statistiques (compétitions, matchs en attente, matchs notés)
- Actions rapides
- Historique récent

#### **Interface de notation :** `judge_score_performance`
**URL :** `/technical-scoring/judge/performance/<performance_id>/score/`
**Template :** `apps/competitions/templates/competitions/technical_scoring/judge_score_performance.html`

**Fonctionnalités :**
- Formulaire de notation par critère
- Validation des scores
- Soumission des notes
- Verrouillage après soumission

#### **Interface de notation alternative :** `judge_scoring_interface`
**URL :** Via management dashboard
**Template :** `apps/competitions/templates/competitions/management/judge_scoring_interface.html`

**Fonctionnalités :**
- Performance actuelle
- Liste des performances à venir
- Guide de notation
- Scores par critère avec pondération

### 2.3 Workflow de notation technique

```
1. ADMINISTRATEUR
   ├─ Configure les critères de notation (category_scoring_setup)
   ├─ Assigne les juges aux catégories (assign_judges)
   └─ Gère les performances (manage_performances)

2. JUGE
   ├─ Accède à son dashboard (judge_dashboard)
   ├─ Consulte ses compétitions assignées
   ├─ Sélectionne une performance à noter
   ├─ Remplit la grille de notation (judge_score_performance)
   ├─ Soumet les scores
   └─ Consulte l'historique (scoring_history)

3. SYSTÈME
   ├─ Calcule les résultats agrégés
   ├─ Applique les pondérations
   ├─ Publie les résultats (si real_time_results = True)
   └─ Génère les classements
```

---

## 3. GESTION DES COMBATS EN TEMPS RÉEL

### 3.1 Module de combat

**Fichier principal :** `apps/competitions/views/combat.py`

**Fonctionnalités principales :**
- ✅ Gestion des configurations de combat
- ✅ Création et gestion des équipes
- ✅ Gestion des poules
- ✅ Création et suivi des combats
- ✅ Interface de combat en temps réel
- ✅ Suivi des actions de combat
- ✅ Timer et gestion du temps

### 3.2 Interface de combat en temps réel

#### **A. Interface principale de combat**
**URL :** `/combat/combats/<combat_id>/interface/`
**Template :** `apps/competitions/templates/competitions/combat/interface_combat.html`

**Fonctionnalités :**
- Timer en temps réel
- Affichage des scores (rouge/blanc)
- Contrôles d'actions de combat
- Historique des actions
- Statut du combat (en cours, terminé, annulé)

**Structure de l'interface :**
```
┌─────────────────────────────────────────────────┐
│  En-tête : Nom combat, timer, statut            │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐     ┌──────────────┐         │
│  │ ROUGE        │     │ BLANC        │         │
│  │ Score: 0     │     │ Score: 0     │         │
│  │ Nom combatt. │     │ Nom combatt. │         │
│  └──────────────┘     └──────────────┘         │
│                                                  │
│  [Contrôles d'actions]                          │
│  [Historique des actions]                       │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### **B. Interface Taekwondo spécifique**
**URL :** `/combat/combats/<combat_id>/interface/` (version Taekwondo)
**Template :** `apps/competitions/templates/competitions/combat/taekwondo/interface_combat.html`

**Spécificités Taekwondo :**
- Système de points Taekwondo
- Gestes techniques spécifiques
- Règles de combat adaptées

#### **C. Monitoring du combat**
**URL :** `/combat/combats/<combat_id>/monitor/`
**Template :** `apps/competitions/templates/competitions/combat/monitor_live.html`

**Fonctionnalités :**
- Suivi en temps réel sans modification
- Affichage public
- Synchronisation avec l'interface principale

### 3.3 Modèles de données pour les combats

**Fichier :** `apps/competitions/models/combat.py`

**Modèles principaux :**

1. **CombatConfiguration**
   - Configuration des règles de combat
   - Durée des rounds
   - Système de points

2. **Equipe**
   - Équipes de combattants
   - Membres d'équipe

3. **Poule**
   - Organisation des poules
   - Matchs de poule

4. **Combat**
   - Combat individuel
   - Statut (programmé, en cours, terminé)
   - Scores
   - Équipe rouge/blanche

5. **ActionCombat**
   - Actions enregistrées pendant le combat
   - Points attribués
   - Annulation possible

### 3.4 Actions de combat disponibles

D'après l'analyse du code, les actions typiques incluent :
- Attribution de points
- Pénalités
- Avertissements
- Actions techniques spécifiques à la discipline

---

## 4. TEMPLATES DE NOTATION

### 4.1 Liste complète des templates de scoring technique

#### **A. Templates principaux de scoring technique**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `judge_dashboard.html` | `competitions/technical_scoring/judge_dashboard.html` | Tableau de bord principal des juges |
| `judge_score_performance.html` | `competitions/technical_scoring/judge_score_performance.html` | Formulaire de notation d'une performance |
| `scoring_interface.html` | `competitions/technical_scoring/scoring_interface.html` | Interface de notation générique |
| `judge_category_view.html` | `competitions/technical_scoring/judge_category_view.html` | Vue catégorie pour juge |
| `judge_competition_list.html` | `competitions/technical_scoring/judge_competition_list.html` | Liste des compétitions assignées |
| `scoring_history.html` | `competitions/technical_scoring/scoring_history.html` | Historique des notations |

#### **B. Templates de gestion (Admin/Manager)**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `management_dashboard.html` | `competitions/technical_scoring/management_dashboard.html` | Dashboard de gestion |
| `category_setup.html` | `competitions/technical_scoring/category_setup.html` | Configuration de catégorie |
| `assign_judges.html` | `competitions/technical_scoring/assign_judges.html` | Affectation des juges |
| `manage_performances.html` | `competitions/technical_scoring/manage_performances.html` | Gestion des performances |
| `monitor_performance.html` | `competitions/technical_scoring/monitor_performance.html` | Monitoring d'une performance |
| `performance_results.html` | `competitions/technical_scoring/performance_results.html` | Résultats d'une performance |
| `category_results.html` | `competitions/technical_scoring/category_results.html` | Résultats par catégorie |
| `public_results.html` | `competitions/technical_scoring/public_results.html` | Résultats publics |

#### **C. Templates de management (ancien système)**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `judge_scoring_interface.html` | `competitions/management/judge_scoring_interface.html` | Interface de notation (ancien) |
| `scoring_dashboard.html` | `competitions/management/scoring_dashboard.html` | Dashboard scoring |
| `scoring.html` | `competitions/management/scoring.html` | Page de scoring |
| `scoring_statistics.html` | `competitions/management/scoring_statistics.html` | Statistiques |
| `category_scoring_setup.html` | `competitions/management/category_scoring_setup.html` | Setup catégorie |
| `add_scoring_criterion.html` | `competitions/management/add_scoring_criterion.html` | Ajout critère |
| `edit_scoring_criterion.html` | `competitions/management/edit_scoring_criterion.html` | Édition critère |

#### **D. Templates standalone scoring**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `judge/performance_list.html` | `competitions/standalone_scoring/judge/performance_list.html` | Liste des performances |
| `judge/score_entry.html` | `competitions/standalone_scoring/judge/score_entry.html` | Saisie de score |
| `judge/settings.html` | `competitions/standalone_scoring/judge/settings.html` | Paramètres juge |
| `admin/dashboard.html` | `competitions/standalone_scoring/admin/dashboard.html` | Dashboard admin |
| `admin/performance_list.html` | `competitions/standalone_scoring/admin/performance_list.html` | Liste performances admin |

#### **E. Templates de scoring générique**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `scoring_form.html` | `competitions/scoring/scoring_form.html` | Formulaire de scoring |
| `scoring_criteria.html` | `competitions/scoring/scoring_criteria.html` | Critères de scoring |
| `judge_dashboard.html` | `competitions/scoring/judge_dashboard.html` | Dashboard juge (alternatif) |
| `results_view.html` | `competitions/scoring/results_view.html` | Vue des résultats |

### 4.2 Liste complète des templates de combat

#### **A. Templates principaux de combat**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `interface_combat.html` | `competitions/combat/interface_combat.html` | **Interface principale de notation en temps réel** |
| `detail_combat.html` | `competitions/combat/detail_combat.html` | Détails d'un combat |
| `liste_combats.html` | `competitions/combat/liste_combats.html` | Liste des combats |
| `affichage_combat.html` | `competitions/combat/affichage_combat.html` | Affichage public du combat |
| `monitor_live.html` | `competitions/combat/monitor_live.html` | Monitoring en temps réel |
| `form_combat.html` | `competitions/combat/form_combat.html` | Formulaire création/modification |

#### **B. Templates Taekwondo spécifiques**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `taekwondo/interface_combat.html` | `competitions/combat/taekwondo/interface_combat.html` | **Interface Taekwondo temps réel** |
| `taekwondo/detail_combat.html` | `competitions/combat/taekwondo/detail_combat.html` | Détails combat Taekwondo |
| `taekwondo/liste_combats.html` | `competitions/combat/taekwondo/liste_combats.html` | Liste combats Taekwondo |

#### **C. Templates de gestion de combat**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `liste_configurations.html` | `competitions/combat/liste_configurations.html` | Liste configurations |
| `form_configuration.html` | `competitions/combat/form_configuration.html` | Formulaire configuration |
| `liste_equipes.html` | `competitions/combat/liste_equipes.html` | Liste des équipes |
| `form_equipe.html` | `competitions/combat/form_equipe.html` | Formulaire équipe |
| `detail_equipe.html` | `competitions/combat/detail_equipe.html` | Détails équipe |
| `form_membre_equipe.html` | `competitions/combat/form_membre_equipe.html` | Formulaire membre |
| `liste_poules.html` | `competitions/combat/liste_poules.html` | Liste des poules |
| `form_poule.html` | `competitions/combat/form_poule.html` | Formulaire poule |
| `detail_poule.html` | `competitions/combat/detail_poule.html` | Détails poule |
| `generer_poules.html` | `competitions/combat/generer_poules.html` | Génération automatique |
| `annuler_combat.html` | `competitions/combat/annuler_combat.html` | Annulation combat |

#### **D. Templates de combat (ancien module)**

| Template | Chemin complet | Fonction |
|----------|---------------|----------|
| `interface_combat.html` | `competitions/combat_taekwondo/interface_combat.html` | Interface combat (ancien) |
| `detail_combat.html` | `competitions/combat_taekwondo/detail_combat.html` | Détails (ancien) |
| `liste_combats.html` | `competitions/combat_taekwondo/liste_combats.html` | Liste (ancien) |

### 4.3 Templates résumés par fonctionnalité

#### **Templates permettant de NOTER les pratiquants (Scoring technique) :**
1. ✅ `technical_scoring/judge_score_performance.html` - **PRINCIPAL**
2. ✅ `technical_scoring/scoring_interface.html` - Alternative
3. ✅ `management/judge_scoring_interface.html` - Ancien système
4. ✅ `standalone_scoring/judge/score_entry.html` - Système standalone
5. ✅ `scoring/scoring_form.html` - Générique

#### **Templates permettant de NOTER les combats (Combat en temps réel) :**
1. ✅ `combat/interface_combat.html` - **PRINCIPAL** - Notation temps réel
2. ✅ `combat/taekwondo/interface_combat.html` - **Taekwondo spécifique**
3. ✅ `combat/affichage_combat.html` - Affichage avec possibilité de notation
4. ✅ `combat_taekwondo/interface_combat.html` - Ancien module

---

## 5. FLUX D'ACCÈS DES JUGES

### 5.1 Comment les juges reçoivent leurs templates

#### **A. Accès via dashboard personnel**

**Workflow :**
```
1. Le juge se connecte
2. Accède à : /technical-scoring/judge/dashboard/
3. Voit ses compétitions assignées
4. Clique sur "Noter" pour une compétition
5. Redirection vers : /technical-scoring/scoring/<competition_id>/
6. Template affiché : scoring_interface.html
```

**Code de redirection :**
```html
<!-- Dans judge_dashboard.html -->
<a href="{% url 'competitions:technical_scoring:scoring_interface' competition.id %}">
    <i class="fas fa-clipboard-list"></i>
    {% trans "Noter" %}
</a>
```

#### **B. Accès direct à une performance**

**Workflow :**
```
1. Le juge accède à sa liste de performances
2. URL : /technical-scoring/judge/performances/
3. Sélectionne une performance
4. Redirection vers : /technical-scoring/judge/score/<performance_id>/
5. Template affiché : judge_score_performance.html
```

#### **C. Accès via management (ancien système)**

**Workflow :**
```
1. Administrateur assigne le juge à une catégorie
2. Le juge reçoit notification/accès
3. URL : /competitions/management/judge/scoring/<competition_id>/<category_id>/<judge_id>/
4. Template affiché : judge_scoring_interface.html
```

### 5.2 Système d'assignation des juges

#### **A. Assignation par catégorie**

**Vue :** `assign_judges`
**URL :** `/technical-scoring/manage/<competition_id>/assign-judges/`
**Template :** `technical_scoring/assign_judges.html`

**Processus :**
1. Admin sélectionne une catégorie
2. Liste des juges disponibles
3. Sélection des juges à assigner
4. Type d'assignation (Principal, Suppléant, etc.)
5. Confirmation et notification

#### **B. Assignation bulk**

**Template :** `management/bulk_judge_assignment.html`

**Fonctionnalités :**
- Assignation multiple
- Assignation par critères
- Export/Import des assignations

### 5.3 Notification aux juges

**Mécanismes identifiés :**
- ✅ Notification via dashboard (compétitions assignées visibles)
- ✅ Liste de performances disponibles
- ✅ Email (si configuré dans le système)
- ✅ Notifications in-app

### 5.4 URLs complètes pour les juges

#### **Scoring technique :**

| Fonction | URL Pattern | Template | Accessible via |
|----------|-------------|----------|----------------|
| Dashboard juge | `/technical-scoring/judge/dashboard/` | `judge_dashboard.html` | ✅ Direct |
| Liste compétitions | `/technical-scoring/judge/competitions/` | `judge_competition_list.html` | ✅ Direct |
| Détail compétition | `/technical-scoring/judge/competition/<id>/` | `judge_competition_detail.html` | ✅ Direct |
| Vue catégorie | `/technical-scoring/judge/category/<id>/` | `judge_category_view.html` | ✅ Direct |
| **Notation performance** | `/technical-scoring/performance/<id>/score/` | `judge_score_performance.html` | ✅ **Principal** |
| Interface scoring | `/technical-scoring/scoring/<competition_id>/` | `scoring_interface.html` | ✅ Alternative |
| Historique | `/technical-scoring/history/` | `scoring_history.html` | ✅ Direct |
| Paramètres | `/technical-scoring/judge/settings/` | Settings page | ✅ Direct |
| Aide | `/technical-scoring/judge/help/` | Help page | ✅ Direct |

#### **Combat :**

| Fonction | URL Pattern | Template | Accessible via |
|----------|-------------|----------|----------------|
| **Interface combat** | `/combat/combats/<id>/interface/` | `interface_combat.html` | ✅ **Principal** |
| Détails combat | `/combat/combats/<id>/` | `detail_combat.html` | ✅ Direct |
| Liste combats | `/combat/combats/` | `liste_combats.html` | ✅ Direct |
| Monitoring | `/combat/combats/<id>/monitor/` | `monitor_live.html` | ✅ Direct |
| Affichage public | `/combat/combats/<id>/affichage/` | `affichage_combat.html` | ✅ Public |

#### **Standalone scoring :**

| Fonction | URL Pattern | Template | Accessible via |
|----------|-------------|----------|----------------|
| Liste performances | `/standalone-scoring/judge/performances/` | `judge/performance_list.html` | ✅ Direct |
| **Saisie score** | `/standalone-scoring/judge/score/<id>/` | `judge/score_entry.html` | ✅ **Principal** |
| Soumettre scores | `/standalone-scoring/judge/submit/<id>/` | Submit handler | ✅ Via formulaire |
| Paramètres | `/standalone-scoring/judge/settings/` | `judge/settings.html` | ✅ Direct |

---

## 6. SYSTÈME WEBSOCKET ET TEMPS RÉEL

### 6.1 Consumers WebSocket

**Fichier :** `apps/competitions/consumers.py`

#### **A. TechnicalScoringConsumer**

**Fonctionnalités :**
- Connexion des juges à une compétition
- Réception des scores en temps réel
- Synchronisation entre juges
- Notifications de statut

**Groupes WebSocket :**
- `technical_{competition_id}` : Groupe pour une compétition

**Messages échangés :**
```json
{
  "action": "submit_score",
  "performance_id": 123,
  "score": 8.5,
  "criteria_id": 45
}
```

#### **B. CombatConsumer**

**Fonctionnalités :**
- Mise à jour du score en temps réel
- Synchronisation du timer
- Notifications d'actions
- Statut du combat

**Groupes WebSocket :**
- `combat_{combat_id}` : Groupe pour un combat

**Messages échangés :**
```json
{
  "action": "add_point",
  "combat_id": 123,
  "team": "red",
  "points": 3
}
```

#### **C. DashboardConsumer**

**Fonctionnalités :**
- Mise à jour du dashboard
- Notifications globales
- Statistiques en temps réel

### 6.2 Configuration temps réel

#### **A. Paramètres de modèle**

**Champs identifiés :**
- `real_time_results` (BooleanField) : Active l'affichage en temps réel
- Présent dans :
  - `ScoringSystem`
  - `CategoryScoringConfig`
  - `StandaloneScoringSystem`

#### **B. Activation du temps réel**

**Pour le scoring technique :**
- Configuration par catégorie
- Option dans `CategoryScoringConfig`
- Affichage automatique si activé

**Pour les combats :**
- Activation automatique quand combat démarre
- Timer synchronisé
- Actions propagées instantanément

### 6.3 Synchronisation

**Mécanismes :**
1. WebSocket pour les mises à jour instantanées
2. Polling AJAX pour les cas non-WebSocket
3. Refresh automatique des pages de monitoring

---

## 7. RECOMMANDATIONS

### 7.1 Points forts identifiés

✅ **Modularité** : Système bien organisé en modules distincts  
✅ **Flexibilité** : Plusieurs systèmes de scoring disponibles  
✅ **Temps réel** : Infrastructure WebSocket en place  
✅ **Complétude** : Templates couvrant tous les cas d'usage  

### 7.2 Points d'attention

⚠️ **Duplication** : Plusieurs systèmes de scoring en parallèle (technical_scoring, standalone_scoring, management)
⚠️ **Compatibilité** : Nécessité de maintenir plusieurs systèmes
⚠️ **Documentation** : Certains templates semblent obsolètes

### 7.3 Recommandations spécifiques

#### **A. Consolidation des systèmes de scoring**

**Problème :** Trois systèmes en parallèle créent de la confusion

**Recommandation :**
1. Documenter clairement quel système utiliser selon le contexte
2. Consolider progressivement vers un système unique
3. Créer une interface unifiée pour les juges

#### **B. Amélioration de l'assignation des juges**

**Recommandation :**
1. Système de notifications automatiques lors d'assignation
2. Email de confirmation avec liens directs
3. Dashboard personnalisé avec notifications

#### **C. Documentation des templates**

**Recommandation :**
1. Documenter chaque template avec son usage
2. Identifier les templates obsolètes
3. Créer un guide pour les développeurs

#### **D. Amélioration du temps réel**

**Recommandation :**
1. Gestion d'erreur WebSocket plus robuste
2. Fallback vers polling si WebSocket indisponible
3. Indicateurs visuels de connexion

#### **E. Tests et validation**

**Recommandation :**
1. Tests unitaires pour chaque template de notation
2. Tests d'intégration pour le flux complet
3. Tests de charge pour le temps réel

### 7.4 Plan d'action proposé

1. **Court terme (1-2 semaines)**
   - Documenter les templates actifs vs obsolètes
   - Créer un guide d'utilisation pour les juges
   - Tester le flux complet d'assignation

2. **Moyen terme (1 mois)**
   - Consolider la documentation des URLs
   - Améliorer les notifications aux juges
   - Optimiser les performances WebSocket

3. **Long terme (2-3 mois)**
   - Évaluer la consolidation des systèmes
   - Créer une interface unifiée
   - Implémenter les améliorations recommandées

---

## 8. RÉSUMÉ EXÉCUTIF

### Templates principaux pour la notation

#### **Pratiquants (Scoring technique) :**
1. **PRINCIPAL** : `technical_scoring/judge_score_performance.html`
2. **Alternative** : `technical_scoring/scoring_interface.html`
3. **Standalone** : `standalone_scoring/judge/score_entry.html`

#### **Combats (Temps réel) :**
1. **PRINCIPAL** : `combat/interface_combat.html`
2. **Taekwondo** : `combat/taekwondo/interface_combat.html`

### Flux d'accès des juges

**Scoring technique :**
- Dashboard → Compétitions assignées → Performance → Template de notation

**Combat :**
- Liste combats → Sélection combat → Interface temps réel

### Infrastructure temps réel

- ✅ WebSocket consumers implémentés
- ✅ Synchronisation des scores
- ✅ Timer en temps réel pour combats
- ✅ Notifications multi-juges

---

**Fin de l'audit**
