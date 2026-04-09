# DOCUMENTATION : management/scoring_dashboard.html

**Tableau de bord de notation pour administrateurs**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `management/scoring_dashboard.html`
- **Localisation :** `apps/competitions/templates/competitions/management/scoring_dashboard.html`
- **Type :** Dashboard admin pour scoring
- **Priorité :** 🟠 Moyenne
- **Usage :** Dashboard centralisé pour administrateurs pour gérer le scoring d'une compétition

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/competitions/management/scoring/<competition_id>/`

**Vue Django :** `apps/competitions/views/management/scoring.py::scoring_dashboard`

**Nom de l'URL :** `competitions:management:scoring_dashboard`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competition` | `Competition` | Compétition |
| `categories` | `List[CompetitionCategory]` | Liste des catégories avec statistiques |

### Structure de chaque `category` annotée

- `id` : ID de la catégorie
- `name` : Nom de la catégorie
- `discipline.name` : Nom de la discipline
- `scoring_criteria_count` : Nombre de critères
- `performances_count` : Nombre total de performances
- `completed_performances_count` : Nombre de performances terminées
- `scoring_progress` : Pourcentage de progression (0-100)

### Autres variables

| Variable | Type | Description |
|----------|------|-------------|
| `judges` | `List[JudgeAssignment]` | Liste des juges assignés |
| `recent_performances` | `List[TechnicalPerformance]` | Performances récentes |

---

## 🎨 STRUCTURE DU TEMPLATE

### Informations compétition

```html
<div class="card">
    <div class="card-header bg-primary text-white">
        <h2>{{ competition.title }}</h2>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <p><i class="fas fa-calendar-alt"></i> Dates: {{ competition.start_date|date:"d/m/Y" }}</p>
                <p><i class="fas fa-map-marker-alt"></i> Lieu: {{ competition.location }}</p>
            </div>
            <div class="col-md-6 text-md-end">
                <p><i class="fas fa-user-friends"></i> Catégories: {{ categories|length }}</p>
                <p><i class="fas fa-gavel"></i> Juges techniques: {{ judges|length }}</p>
            </div>
        </div>
    </div>
</div>
```

### Tableau des catégories

```html
<table class="table">
    <thead>
        <tr>
            <th>Catégorie</th>
            <th>Critères</th>
            <th>Performances</th>
            <th>Progression</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for category in categories %}
        <tr>
            <td>
                <strong>{{ category.name }}</strong>
                <div class="small text-muted">{{ category.discipline.name }}</div>
            </td>
            <td>
                <span class="badge bg-info">{{ category.scoring_criteria_count }}</span>
            </td>
            <td>
                {{ category.completed_performances_count }}/{{ category.performances_count }}
            </td>
            <td>
                <div class="progress">
                    <div class="progress-bar bg-success" 
                         style="width: {{ category.scoring_progress }}%">
                    </div>
                </div>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="{% url 'competitions:management:category_scoring_setup' competition.id category.id %}">
                        <i class="fas fa-cog"></i> Configurer
                    </a>
                    <a href="{% url 'competitions:management:manage_performances' competition.id category.id %}">
                        <i class="fas fa-users"></i> Performances
                    </a>
                    <a href="{% url 'competitions:management:category_results' competition.id category.id %}">
                        <i class="fas fa-trophy"></i> Résultats
                    </a>
                </div>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Performances récentes

```html
{% if recent_performances %}
<div class="card">
    <div class="card-header">
        <h3>Performances récentes</h3>
    </div>
    <div class="card-body">
        {% for performance in recent_performances %}
        <div class="performance-item">
            <strong>{{ performance.practitioner.full_name }}</strong>
            <small>{{ performance.category.name }}</small>
            <span class="badge">{{ performance.get_status_display }}</span>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Vue d'ensemble** : Toutes les catégories avec progression
2. **Statistiques** : Nombre de critères, performances, progression
3. **Barres de progression** : Visualisation de la progression par catégorie
4. **Actions rapides** : Liens vers configuration, performances, résultats
5. **Performances récentes** : Liste des dernières performances

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
@login_required
@competition_management_permission_required
def scoring_dashboard(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Annoter chaque catégorie avec statistiques
    for category in categories:
        category.scoring_criteria_count = ScoringCriterion.objects.filter(category=category).count()
        category.performances_count = TechnicalPerformance.objects.filter(category=category).count()
        category.completed_performances_count = TechnicalPerformance.objects.filter(
            category=category, status='completed'
        ).count()
        
        if category.performances_count > 0:
            category.scoring_progress = int(
                (category.completed_performances_count / category.performances_count) * 100
            )
        else:
            category.scoring_progress = 0
    
    # Récupérer juges et performances récentes
    judges = JudgeAssignment.objects.filter(
        category__competition=competition,
        assignment_type__in=['technical_judge', 'chief_judge']
    ).select_related('user', 'category')
    
    recent_performances = TechnicalPerformance.objects.filter(
        category__competition=competition
    ).select_related('practitioner', 'category').order_by('-end_time')[:5]
    
    context = {
        'competition': competition,
        'categories': categories,
        'judges': judges,
        'recent_performances': recent_performances,
    }
    
    return render(request, 'competitions/management/scoring_dashboard.html', context)
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
