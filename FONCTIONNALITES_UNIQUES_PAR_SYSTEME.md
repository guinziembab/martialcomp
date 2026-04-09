# FONCTIONNALITÉS UNIQUES PAR SYSTÈME DE SCORING

**Date de création :** 3 novembre 2025  
**Objectif :** Identifier toutes les fonctionnalités uniques à préserver lors de la consolidation

---

## 📊 RÉSUMÉ EXÉCUTIF

**Total fonctionnalités identifiées :** 45+  
**Fonctionnalités uniques :** 18  
**Fonctionnalités communes :** 27

---

## 1. STANDALONE SCORING - Fonctionnalités uniques

### 🔴 Système de scoring avancé

#### 1.1 Types de systèmes de scoring multiples
**Fichier :** `models/standalone_scoring.py`  
**Classes :** `StandaloneScoringSystem`

**Fonctionnalités :**
- ✅ **Type STANDARD** : Moyenne pondérée
- ✅ **Type POINT** : Système par points
- ✅ **Type DIRECT_ELIMINATION** : Élimination directe
- ✅ **Type CUSTOM** : Système personnalisable

**Code :**
```python
SYSTEM_TYPES = [
    (STANDARD, _('Standard (Weighted Average)')),
    (POINT, _('Point System')),
    (DIRECT_ELIMINATION, _('Direct Elimination')),
    (CUSTOM, _('Custom')),
]
```

**Importance :** 🔴 Haute - Permet de gérer différents types de compétitions

---

#### 1.2 Système de rounds (preliminary, semifinal, final)
**Fichier :** `models/standalone_scoring.py`  
**Modèle :** `StandalonePerformance`

**Fonctionnalités :**
- ✅ Round PRELIMINARY (préliminaires)
- ✅ Round SEMIFINAL (demi-finales)
- ✅ Round FINAL (finale)
- ✅ Round EXHIBITION (exhibition)
- ✅ Numéro de round (`round_number`)
- ✅ Performance order par round

**Code :**
```python
ROUND_TYPES = [
    (PRELIMINARY, _('Preliminary')),
    (SEMIFINAL, _('Semifinal')),
    (FINAL, _('Final')),
    (EXHIBITION, _('Exhibition')),
]
```

**Importance :** 🔴 Haute - Essentiel pour les compétitions avec phases

---

#### 1.3 Calcul de scores avec ScoreCalculator
**Fichier :** `utils/standalone_scoring.py`  
**Classe :** `StandaloneScoreCalculator`

**Fonctionnalités :**
- ✅ `calculate_weighted_average()` : Moyenne pondérée
- ✅ `calculate_point_score()` : Système par points
- ✅ `generate_rankings()` : Génération de classements
- ✅ `handle_third_place_tie()` : Gestion spéciale des ex-aequos en 3e place
- ✅ Exclusion des scores extrêmes automatique
- ✅ Gestion des Decimal pour précision

**Code :**
```python
class StandaloneScoreCalculator:
    def calculate_weighted_average(self, scores):
        # Calcul avec exclusion extrêmes
        # Pondération par critère
        # Retourne résultat détaillé
    
    def handle_third_place_tie(self, rankings):
        # Gère le cas spécial des multiples 3e places
```

**Importance :** 🔴 Haute - Système de calcul robuste et précis

---

#### 1.4 Snapshots de classements
**Fichier :** `models/standalone_scoring.py`  
**Modèles :** `StandaloneCategoryRankingSnapshot`, `StandaloneRankingSnapshotEntry`

**Fonctionnalités :**
- ✅ Création de snapshots à un moment donné
- ✅ Snapshot final vs draft
- ✅ Publication de snapshot
- ✅ Conservation de l'historique des classements
- ✅ Notes sur les snapshots

**Code :**
```python
class StandaloneCategoryRankingSnapshot(models.Model):
    is_published = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
```

**Importance :** 🟠 Moyenne - Utile pour l'historique et l'audit

---

#### 1.5 Overrides de configuration par catégorie
**Fichier :** `models/standalone_scoring.py`  
**Modèle :** `StandaloneCategoryScoringConfig`

**Fonctionnalités :**
- ✅ `override_min_score` : Override du min par catégorie
- ✅ `override_max_score` : Override du max par catégorie
- ✅ `override_score_step` : Override du pas par catégorie
- ✅ Override pour `exclude_extreme_scores`
- ✅ Override pour `allow_ties`
- ✅ Override pour `real_time_results`
- ✅ Méthodes `get_effective_*()` pour récupérer la valeur effective

**Code :**
```python
def get_effective_min_score(self):
    return self.override_min_score if self.override_min_score is not None \
           else self.scoring_system.min_score
```

**Importance :** 🟠 Moyenne - Flexibilité par catégorie

---

#### 1.6 Original value tracking
**Fichier :** `models/standalone_scoring.py`  
**Modèle :** `StandaloneScore`

**Fonctionnalités :**
- ✅ `original_value` : Conserve la valeur originale
- ✅ Permet de suivre les modifications
- ✅ Utile pour l'audit

**Code :**
```python
original_value = models.DecimalField(
    max_digits=5, 
    decimal_places=2, 
    null=True, 
    blank=True
)
```

**Importance :** 🟡 Faible - Utile pour audit mais non essentiel

---

#### 1.7 Système de médailles automatique
**Fichier :** `models/standalone_scoring.py`  
**Modèle :** `StandaloneCompetitionRanking`

**Fonctionnalités :**
- ✅ Attribution automatique des médailles (Gold, Silver, Bronze)
- ✅ Basé sur le rang
- ✅ Gestion des ex-aequos

**Code :**
```python
def save(self, *args, **kwargs):
    if not self.pk and self.medal == self.NONE:
        if self.rank == 1:
            self.medal = self.GOLD
        elif self.rank == 2:
            self.medal = self.SILVER
        elif self.rank == 3:
            self.medal = self.BRONZE
```

**Importance :** 🟠 Moyenne - Améliore l'expérience utilisateur

---

#### 1.8 Isolation organisationnelle intégrée
**Fichier :** `views/standalone_scoring.py`

**Fonctionnalités :**
- ✅ Utilise `get_organization_queryset()` partout
- ✅ Isolation automatique des données par organisation
- ✅ Support des superusers et staff

**Code :**
```python
base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
```

**Importance :** 🔴 Haute - Essentiel pour multi-organisation

---

#### 1.9 Vue complète de saisie de scores pour juges
**Fichier :** `views/standalone_scoring.py`  
**Classe :** `JudgeScoreEntryView`

**Fonctionnalités :**
- ✅ Validation complète des permissions
- ✅ Vérification de l'assignation du juge
- ✅ Gestion des formulaires par critère
- ✅ Sauvegarde AJAX des scores
- ✅ Gestion de l'état des scores (saved/not saved)
- ✅ Vérification avant soumission complète

**Code :**
```python
class JudgeScoreEntryView(LoginRequiredMixin, View):
    def get(self, request, performance_id):
        # Validation complète
        # Création des formulaires par critère
        # Gestion des scores existants
    
    def post(self, request, performance_id):
        # Sauvegarde avec validation
        # Support AJAX
```

**Importance :** 🔴 Haute - Interface complète pour juges

---

#### 1.10 Gestion des paramètres juge avancée
**Fichier :** `models/standalone_scoring.py`, `views/standalone_scoring.py`  
**Modèle :** `StandaloneJudgeSettings`

**Fonctionnalités :**
- ✅ Display mode (COMPACT, DETAILED)
- ✅ Theme (LIGHT, DARK)
- ✅ Notification sounds
- ✅ Auto submit
- ✅ Vue dédiée avec formulaire

**Importance :** 🟠 Moyenne - Personnalisation interface juge

---

### 📋 Récapitulatif Standalone Scoring

**Fonctionnalités uniques identifiées :** 10

1. ✅ Types de systèmes multiples (standard, point, direct, custom)
2. ✅ Système de rounds (preliminary, semifinal, final)
3. ✅ ScoreCalculator avec calculs avancés
4. ✅ Snapshots de classements
5. ✅ Overrides de configuration par catégorie
6. ✅ Original value tracking
7. ✅ Système de médailles automatique
8. ✅ Isolation organisationnelle
9. ✅ Vue complète de saisie de scores
10. ✅ Paramètres juge avancés

---

## 2. MANAGEMENT SCORING - Fonctionnalités uniques

### 🔴 Fonctionnalités admin avancées

#### 2.1 Export CSV des résultats
**Fichier :** `views/management/scoring.py`  
**Fonction :** `export_results()`

**Fonctionnalités :**
- ✅ Export des résultats en CSV
- ✅ Colonnes : Rang, Nom, Prénom, Club, Score final, Ex-aequo
- ✅ Nom de fichier dynamique avec nom de catégorie
- ✅ Headers traduits

**Code :**
```python
def export_results(request, competition_id, category_id):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{category.name}_results.csv"'
    writer = csv.writer(response)
    # Export des données
```

**Importance :** 🟠 Moyenne - Utile pour reporting et archivage

---

#### 2.2 Statistiques détaillées de notation
**Fichier :** `views/management/scoring.py`  
**Fonction :** `scoring_statistics()`

**Fonctionnalités :**
- ✅ Statistiques par juge :
  - Moyenne des scores
  - Nombre de scores attribués
  - Écart-type
- ✅ Statistiques par critère :
  - Moyenne des scores
  - Nombre de scores
  - Écart-type
  - Pondération
- ✅ Vue complète avec tableaux détaillés

**Code :**
```python
def scoring_statistics(request, competition_id, category_id):
    # Calcul moyenne et écart-type par juge
    # Calcul moyenne et écart-type par critère
    # Affichage dans template
```

**Importance :** 🟠 Moyenne - Utile pour analyse et audit

---

#### 2.3 Vue podium pour affichage public
**Fichier :** `views/management/scoring.py`  
**Fonction :** `podium_view()`

**Fonctionnalités :**
- ✅ Affichage des 3 premiers
- ✅ Mode fullscreen
- ✅ Optimisé pour affichage public (écran, projecteur)
- ✅ Design visuel pour podium

**Code :**
```python
def podium_view(request, competition_id, category_id):
    podium = CompetitionRanking.objects.filter(
        competition=competition,
        category=category,
        rank__lte=3
    ).order_by('rank')
    context['is_fullscreen'] = request.GET.get('fullscreen') == '1'
```

**Importance :** 🟡 Faible - Nice to have pour affichage public

---

#### 2.4 Performance scorecard détaillée
**Fichier :** `views/management/scoring.py`  
**Fonction :** `performance_scorecard()`

**Fonctionnalités :**
- ✅ Affichage de tous les scores par juge et critère
- ✅ Matrice juge/critère complète
- ✅ Statistiques par critère (min, max, avg, count)
- ✅ Affichage du rôle de chaque juge
- ✅ Vue complète pour l'administration

**Code :**
```python
def performance_scorecard(request, competition_id, performance_id):
    # Organisation des scores en matrice juge/critère
    # Calcul des statistiques par critère
    # Affichage détaillé
```

**Importance :** 🟠 Moyenne - Utile pour révision et audit

---

#### 2.5 Réorganisation des critères par drag & drop
**Fichier :** `views/management/scoring.py`  
**Fonction :** `reorder_scoring_criteria()`

**Fonctionnalités :**
- ✅ Réorganisation de l'ordre des critères
- ✅ API JSON pour drag & drop
- ✅ Transaction atomique pour sécurité

**Code :**
```python
def reorder_scoring_criteria(request, competition_id, category_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        criteria_orders = data.get('criteriaOrders', [])
        with transaction.atomic():
            # Mise à jour de l'ordre
```

**Importance :** 🟠 Moyenne - UX améliorée pour gestion

---

#### 2.6 Réorganisation des performances
**Fichier :** `views/management/scoring.py`  
**Fonction :** `reorder_performances()`

**Fonctionnalités :**
- ✅ Réorganisation de l'ordre de passage
- ✅ API JSON pour drag & drop
- ✅ Transaction atomique

**Importance :** 🟠 Moyenne - Utile pour planning

---

#### 2.7 Génération de résultats pour toutes les catégories
**Fichier :** `views/management/scoring.py`  
**Fonction :** `generate_all_results()`

**Fonctionnalités :**
- ✅ Calcul en masse pour toutes les catégories
- ✅ Gestion des erreurs par catégorie
- ✅ Compteur de succès/échecs
- ✅ Continuation même en cas d'erreur partielle

**Code :**
```python
def generate_all_results(request, competition_id):
    for category in categories:
        try:
            calculate_results(request._request, competition_id, category.id)
            processed_categories += 1
        except Exception as e:
            # Continue avec les autres catégories
```

**Importance :** 🟠 Moyenne - Gain de temps pour admin

---

#### 2.8 Interface de notation pour administrateurs
**Fichier :** `views/management/scoring.py`  
**Fonction :** `judge_scoring_interface()`, `save_judge_scores()`

**Fonctionnalités :**
- ✅ Interface de notation accessible aux admins
- ✅ Permet aux admins de noter à la place d'un juge
- ✅ Vue des performances en cours et à venir
- ✅ Guide de notation intégré
- ✅ Sauvegarde des scores

**Code :**
```python
def judge_scoring_interface(request, competition_id, category_id, judge_id):
    # Récupération juge et assignation
    # Liste des performances
    # Performance actuelle
    # Critères et scores existants

def save_judge_scores(request, competition_id, category_id, judge_id, performance_id):
    # Validation complète
    # Sauvegarde transactionnelle
```

**Importance :** 🟠 Moyenne - Utile pour assistance technique

---

#### 2.9 Gestion complète des performances (start/end)
**Fichier :** `views/management/scoring.py`  
**Fonctions :** `start_performance()`, `end_performance()`

**Fonctionnalités :**
- ✅ Démarrage manuel de performance
- ✅ Arrêt manuel de performance
- ✅ Redirection selon paramètre `next`
- ✅ Gestion du statut (pending → in_progress → completed)

**Importance :** 🟠 Moyenne - Contrôle du timing

---

### 📋 Récapitulatif Management Scoring

**Fonctionnalités uniques identifiées :** 9

1. ✅ Export CSV des résultats
2. ✅ Statistiques détaillées de notation
3. ✅ Vue podium pour affichage public
4. ✅ Performance scorecard détaillée
5. ✅ Réorganisation des critères (drag & drop)
6. ✅ Réorganisation des performances (drag & drop)
7. ✅ Génération de résultats en masse
8. ✅ Interface de notation pour administrateurs
9. ✅ Gestion complète start/end performances

---

## 3. TECHNICAL SCORING - Fonctionnalités uniques

### 🔴 Interface juge simplifiée

#### 3.1 Dashboard juge dédié
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `judge_dashboard()`

**Fonctionnalités :**
- ✅ Vue d'ensemble pour les juges
- ✅ Liste des compétitions assignées
- ✅ Statistiques personnelles (compétitions, matchs, temps moyen)
- ✅ Actions rapides
- ✅ Historique récent
- ✅ Interface simple et claire

**Template :** `judge_dashboard.html`

**Importance :** 🔴 Haute - Point d'entrée principal pour juges

---

#### 3.2 Liste des compétitions assignées
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `judge_competition_list()`

**Fonctionnalités :**
- ✅ Vue liste des compétitions assignées au juge
- ✅ Filtrées et organisées
- ✅ Liens directs vers notation

**Template :** `judge_competition_list.html`

**Importance :** 🟠 Moyenne - Navigation facilitée

---

#### 3.3 Vue détaillée compétition pour juge
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `judge_competition_detail()`

**Fonctionnalités :**
- ✅ Détails d'une compétition spécifique
- ✅ Informations pour le juge
- ✅ Accès aux catégories assignées

**Template :** `judge_competition_detail.html`

**Importance :** 🟡 Faible - Complément au dashboard

---

#### 3.4 Vue catégorie pour juge
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `judge_category_view()`

**Fonctionnalités :**
- ✅ Vue d'une catégorie spécifique
- ✅ Liste des performances
- ✅ Accès direct à la notation

**Template :** `judge_category_view.html`

**Importance :** 🟠 Moyenne - Navigation par catégorie

---

#### 3.5 Historique des notations
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `scoring_history()`

**Fonctionnalités :**
- ✅ Historique des notations effectuées
- ✅ Filtrable par compétition
- ✅ Consultation des scores passés

**Template :** `scoring_history.html`

**Importance :** 🟡 Faible - Utile pour référence

---

#### 3.6 Aide pour les juges
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `judge_help()`

**Fonctionnalités :**
- ✅ Page d'aide dédiée aux juges
- ✅ Documentation sur l'utilisation du système

**Template :** `judge_help.html`

**Importance :** 🟡 Faible - Support utilisateur

---

#### 3.7 Gestion des catégories de notation
**Fichier :** `views/technical_scoring.py`  
**Fonction :** `scoring_categories()`

**Fonctionnalités :**
- ✅ Liste des catégories disponibles
- ✅ Accès rapide aux catégories

**Template :** `categories.html`

**Importance :** 🟡 Faible - Navigation

---

### 📋 Récapitulatif Technical Scoring

**Fonctionnalités uniques identifiées :** 7

1. ✅ Dashboard juge dédié
2. ✅ Liste des compétitions assignées
3. ✅ Vue détaillée compétition pour juge
4. ✅ Vue catégorie pour juge
5. ✅ Historique des notations
6. ✅ Aide pour les juges
7. ✅ Gestion des catégories de notation

---

## 4. MATRICE DE PRIORISATION DES FONCTIONNALITÉS

### 🔴 Haute priorité (À préserver absolument)

| Fonctionnalité | Système | Importance | Complexité migration |
|----------------|---------|------------|---------------------|
| Types de systèmes multiples | Standalone | 🔴 Critique | Moyenne |
| Système de rounds | Standalone | 🔴 Critique | Moyenne |
| ScoreCalculator avancé | Standalone | 🔴 Critique | Faible |
| Isolation organisationnelle | Standalone | 🔴 Critique | Faible |
| Dashboard juge | Technical | 🔴 Critique | Faible |
| Vue complète saisie scores | Standalone | 🔴 Critique | Moyenne |

### 🟠 Moyenne priorité (À préserver si possible)

| Fonctionnalité | Système | Importance | Complexité migration |
|----------------|---------|------------|---------------------|
| Snapshots de classements | Standalone | 🟠 Important | Moyenne |
| Export CSV | Management | 🟠 Important | Faible |
| Statistiques détaillées | Management | 🟠 Important | Moyenne |
| Réorganisation (drag & drop) | Management | 🟠 Important | Moyenne |
| Performance scorecard | Management | 🟠 Important | Faible |
| Overrides configuration | Standalone | 🟠 Important | Faible |
| Génération résultats en masse | Management | 🟠 Important | Faible |
| Interface notation admin | Management | 🟠 Important | Faible |
| Gestion start/end performances | Management | 🟠 Important | Faible |

### 🟡 Faible priorité (Nice to have)

| Fonctionnalité | Système | Importance | Complexité migration |
|----------------|---------|------------|---------------------|
| Vue podium | Management | 🟡 Nice | Faible |
| Original value tracking | Standalone | 🟡 Nice | Faible |
| Système médailles auto | Standalone | 🟡 Nice | Faible |
| Historique notations | Technical | 🟡 Nice | Faible |
| Aide juges | Technical | 🟡 Nice | Faible |
| Paramètres juge avancés | Standalone | 🟡 Nice | Faible |

---

## 5. PLAN DE PRÉSERVATION DES FONCTIONNALITÉS

### Phase 1 : Fonctionnalités critiques
1. ✅ Intégrer ScoreCalculator de Standalone
2. ✅ Ajouter types de systèmes multiples
3. ✅ Ajouter système de rounds
4. ✅ Intégrer isolation organisationnelle
5. ✅ Intégrer dashboard juge de Technical
6. ✅ Intégrer vue complète saisie de Standalone

### Phase 2 : Fonctionnalités importantes
1. ✅ Ajouter snapshots de classements
2. ✅ Ajouter export CSV de Management
3. ✅ Ajouter statistiques détaillées
4. ✅ Ajouter réorganisation drag & drop
5. ✅ Ajouter performance scorecard
6. ✅ Ajouter overrides configuration

### Phase 3 : Fonctionnalités nice to have
1. ⏳ Ajouter vue podium
2. ⏳ Ajouter original value tracking
3. ⏳ Ajouter système médailles auto
4. ⏳ Ajouter historique notations
5. ⏳ Ajouter aide juges

---

## 6. DÉPENDANCES ENTRE FONCTIONNALITÉS

### Graphique de dépendances

```
ScoreCalculator
    ├─→ Types de systèmes multiples
    ├─→ Calcul weighted average
    ├─→ Calcul point score
    └─→ Gestion ex-aequos

Système de rounds
    ├─→ StandalonePerformance
    └─→ Rankings par round

Snapshots
    ├─→ Rankings
    └─→ Historique

Isolation organisationnelle
    ├─→ Toutes les vues
    └─→ Tous les modèles

Dashboard juge
    ├─→ Liste compétitions assignées
    └─→ Historique notations
```

---

**Prochaines étapes :** Créer le système unifié qui intègre toutes ces fonctionnalités
