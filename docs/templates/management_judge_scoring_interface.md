# DOCUMENTATION : judge_scoring_interface.html

**Interface de notation pour juges (vue administrateur)**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge_scoring_interface.html`
- **Localisation :** `apps/competitions/templates/competitions/management/judge_scoring_interface.html`
- **Type :** Interface de notation pour administrateurs
- **Priorité :** 🔴 Haute
- **Usage :** Interface permettant aux administrateurs de voir et gérer l'interface de notation d'un juge spécifique

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/competitions/management/judge/scoring/<competition_id>/<category_id>/<judge_id>/`

**Vue Django :** `apps/competitions/views/management/scoring.py::judge_scoring_interface`

**Nom de l'URL :** `competitions:management:judge_scoring_interface`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competition` | `Competition` | Compétition |
| `category` | `CompetitionCategory` | Catégorie |
| `judge` | `User` | Juge (User model) |
| `assignment` | `JudgeAssignment` | Assignation du juge à la catégorie |
| `performances` | `List[TechnicalPerformance]` | Liste des performances à noter |
| `criteria` | `List[ScoringCriterion]` | Liste des critères de notation |
| `current_performance` | `TechnicalPerformance` | Performance actuellement à noter (optionnel) |
| `scores` | `Dict[int, float]` | Dictionnaire {criterion_id: score_value} |

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Informations juge et catégorie

```html
<div class="card-header bg-primary text-white">
    <h2>{{ judge.first_name }} {{ judge.last_name }} - {{ category.name }}</h2>
</div>
<div class="card-body">
    <p>Juge : {{ judge.first_name }} {{ judge.last_name }}</p>
    <p>Catégorie : {{ category.name }}</p>
    <p>Discipline : {{ category.discipline.name }}</p>
    <p>Rôle : {{ assignment.get_assignment_type_display }}</p>
    <p>Performances à évaluer : {{ performances|length }}</p>
</div>
```

### 2. Performance actuelle

```html
{% if current_performance %}
<div class="card">
    <div class="card-header bg-warning">
        <h3>
            Performance actuelle
            {% if current_performance.status == 'in_progress' %}
            <span class="badge bg-warning">En cours</span>
            {% endif %}
        </h3>
        <span class="badge bg-primary">{{ current_performance.performance_order }}</span>
    </div>
    <div class="card-body">
        <h4>{{ current_performance.practitioner.full_name }}</h4>
        
        {% if current_performance.practitioner.club %}
        <p><i class="fas fa-building"></i> Club : {{ current_performance.practitioner.club.name }}</p>
        {% endif %}
        
        <form method="post" action="{% url 'competitions:management:save_judge_scores' ... %}">
            {% csrf_token %}
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Critère</th>
                        <th>Description</th>
                        <th>Pondération</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for criterion in criteria %}
                    <tr>
                        <td><strong>{{ criterion.name }}</strong></td>
                        <td>{{ criterion.description|truncatechars:100 }}</td>
                        <td class="text-center">
                            <span class="badge bg-secondary">× {{ criterion.weight }}</span>
                        </td>
                        <td style="width: 160px;">
                            <div class="input-group input-group-sm">
                                <input type="number" 
                                       name="score_{{ criterion.id }}" 
                                       class="form-control" 
                                       step="{{ criterion.step }}" 
                                       min="{{ criterion.min_score }}" 
                                       max="{{ criterion.max_score }}" 
                                       {% if criterion.id in scores %}value="{{ scores|get_item:criterion.id }}"{% endif %}
                                       required>
                                <span class="input-group-text">/{{ criterion.max_score }}</span>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> Enregistrer les scores
            </button>
        </form>
    </div>
</div>
{% endif %}
```

### 3. Liste des performances à venir

```html
<div class="card">
    <div class="card-header bg-light">
        <h3>Performances à venir</h3>
    </div>
    <div class="card-body p-0">
        <div class="list-group list-group-flush">
            {% for performance in performances %}
            <a href="{% url 'competitions:management:judge_scoring_interface' ... %}?performance={{ performance.id }}" 
               class="list-group-item list-group-item-action 
                      {% if current_performance and current_performance.id == performance.id %}active{% endif %}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>{{ performance.performance_order }}. {{ performance.practitioner.full_name }}</strong>
                        {% if performance.practitioner.club %}
                        <div class="small">{{ performance.practitioner.club.name }}</div>
                        {% endif %}
                    </div>
                    <span class="badge {% if performance.status == 'in_progress' %}bg-warning{% else %}bg-secondary{% endif %}">
                        {{ performance.get_status_display }}
                    </span>
                </div>
            </a>
            {% empty %}
            <div class="list-group-item text-center py-3">
                <p class="mb-0 text-muted">Aucune performance planifiée.</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

### 4. Guide de notation

```html
<div class="card">
    <div class="card-header bg-light">
        <h3>Guide de notation</h3>
    </div>
    <div class="card-body">
        <ul class="list-group list-group-flush">
            {% for criterion in criteria %}
            <li class="list-group-item">
                <strong>{{ criterion.name }}</strong>
                <div class="small text-muted">{{ criterion.min_score }} - {{ criterion.max_score }} (× {{ criterion.weight }})</div>
                {% if criterion.description %}
                <div class="small">{{ criterion.description }}</div>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            Entrez les scores pour chaque critère selon la performance observée. 
            Le pas de notation est de 0.25 par défaut.
        </div>
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Vue administrateur** : Permet aux admins de voir l'interface d'un juge
2. **Performance actuelle** : Affiche la performance en cours de notation
3. **Liste performances** : Liste toutes les performances à venir
4. **Formulaire de notation** : Formulaire avec tous les critères
5. **Guide intégré** : Guide de notation avec critères et pondérations
6. **Navigation** : Navigation entre performances
7. **Statuts visuels** : Badges pour statuts des performances

### ⚠️ Limitations identifiées

1. Utilise un template filter custom `get_item` pour récupérer valeurs dans dict
2. Pas de validation JavaScript côté client
3. Pas de sauvegarde automatique (auto-save)

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
@login_required
@competition_management_permission_required
def judge_scoring_interface(request, competition_id, category_id, judge_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    judge = get_object_or_404(User, pk=judge_id)
    
    # Vérifier assignation
    assignment = get_object_or_404(
        JudgeAssignment,
        category=category,
        user=judge,
        assignment_type__in=['technical_judge', 'chief_judge']
    )
    
    # Récupérer performances
    performances = TechnicalPerformance.objects.filter(
        category=category,
        status__in=['pending', 'in_progress']
    ).select_related('practitioner').order_by('performance_order')
    
    # Performance actuelle
    current_performance = performances.filter(status='in_progress').first()
    if not current_performance and performances.exists():
        current_performance = performances.first()
    
    # Critères
    criteria = ScoringCriterion.objects.filter(category=category).order_by('order')
    
    # Scores existants
    scores = {}
    if current_performance:
        existing_scores = TechnicalScore.objects.filter(
            performance=current_performance,
            judge=judge
        )
        for score in existing_scores:
            scores[score.criterion.id] = score.value
    
    context = {
        'competition': competition,
        'category': category,
        'judge': judge,
        'assignment': assignment,
        'performances': performances,
        'current_performance': current_performance,
        'criteria': criteria,
        'scores': scores,
    }
    
    return render(request, 'competitions/management/judge_scoring_interface.html', context)
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load widget_tweaks %}` : Widget tweaks (optionnel)

### CSS

- Bootstrap 5
- Styles personnalisés pour `.list-group-item.active`

### JavaScript

```javascript
// Template filter custom pour récupérer une valeur dans un dictionnaire
if (!window.django) window.django = {};
if (!window.django.template) window.django.template = {};
if (!window.django.template.filters) window.django.template.filters = {};

window.django.template.filters.get_item = function(dict, key) {
    return dict[key];
};
```

---

## ✅ TESTS RECOMMANDÉS

1. **Rendu** : Vérifier l'affichage correct
2. **Formulaire** : Tester la soumission des scores
3. **Navigation** : Tester le changement de performance
4. **Validation** : Tester les validations min/max

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
