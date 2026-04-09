# 🐛 Prompts de Correction - Retours Compétition Zone Nord (6 décembre 2025)

## 📋 Synthèse des Problèmes Remontés

| # | Module | Problème | Priorité | Type |
|---|--------|----------|----------|------|
| 1 | Juges | Drag & Drop ne scroll pas | 🔴 Haute | UX Bug |
| 2 | Notation | Égalité écrase la note au lieu d'ajouter | 🔴 Critique | Bug |
| 3 | Notation | Notes des juges non visibles admin | 🟡 Moyenne | Feature |
| 4 | Notation | Config plage notation non fonctionnelle | 🔴 Haute | Bug |
| 5 | Notation | Nom catégorie caché par photos podium | 🟡 Moyenne | UI Bug |
| 6 | Assaut | Scores non enregistrés fin combat | 🔴 Critique | Bug |
| 7 | Assaut | Pas de podium/résultats | 🔴 Haute | Bug |
| 8 | Assaut | Génération poules non fonctionnelle | 🔴 Haute | Bug |
| 9 | Assaut | Configurer finale après poules | 🟢 Basse | Feature |
| 10 | Assaut | Son gong fin assaut | 🟢 Basse | Feature |
| 11 | Assaut | Couleurs agressives arbitre table | 🟡 Moyenne | UX |

---

## 🎯 SECTION 1 : INSCRIPTION JUGES

### 🐛 Bug #1 : Drag & Drop ne scroll pas avec longue liste

**Contexte du problème :**
Quand la liste des juges est trop longue, l'écran ne défile pas automatiquement lors du drag & drop, rendant impossible l'affectation aux catégories situées en bas de page.

**Fichiers concernés :**
- `templates/competitions/manage/competition_management_pro.html`
- JavaScript Dragula configuration

---

#### PROMPT 1.1 - Investigation

```
Analyse le problème de scroll lors du drag & drop des juges dans MartialComp.

Fichier : templates/competitions/manage/competition_management_pro.html

Le drag & drop utilise la bibliothèque Dragula. Actuellement, quand on glisse un juge vers une catégorie située hors de l'écran visible, la page ne scroll pas automatiquement.

Tâches :
1. Examine la configuration Dragula actuelle dans le template
2. Identifie pourquoi l'auto-scroll ne fonctionne pas
3. Recherche si Dragula supporte nativement l'auto-scroll ou si un plugin est nécessaire
4. Propose une solution technique

Le code actuel utilise :
```javascript
dragulaJudges = dragula(judgeContainers, {
    copy: false,
    revertOnSpill: true,
    accepts: function(el, target, source, sibling) { ... }
});
```

Fournis un diagnostic complet.
```

---

#### PROMPT 1.2 - Correction avec Auto-Scroll

```
Implémente la solution d'auto-scroll pour le drag & drop des juges dans MartialComp.

Solution retenue : Utiliser le plugin `dragula-scroll` ou implémenter un auto-scroll personnalisé.

Option A - Plugin dragula-scroll :
```bash
npm install dom-autoscroller
```

Option B - Auto-scroll personnalisé avec détection de position souris.

Modifie le fichier `competition_management_pro.html` pour :

1. Ajouter la détection de position de la souris pendant le drag
2. Déclencher le scroll quand la souris est à moins de 100px du bord haut/bas
3. Ajuster la vitesse de scroll en fonction de la proximité du bord

Code à implémenter :
```javascript
// Auto-scroll pendant le drag
let scrollInterval = null;

dragulaJudges.on('drag', function(el) {
    document.addEventListener('mousemove', handleDragScroll);
});

dragulaJudges.on('dragend', function() {
    document.removeEventListener('mousemove', handleDragScroll);
    if (scrollInterval) {
        clearInterval(scrollInterval);
        scrollInterval = null;
    }
});

function handleDragScroll(e) {
    const scrollZone = 100; // pixels from edge
    const scrollSpeed = 10;
    const viewportHeight = window.innerHeight;
    
    if (scrollInterval) {
        clearInterval(scrollInterval);
        scrollInterval = null;
    }
    
    if (e.clientY < scrollZone) {
        // Scroll vers le haut
        scrollInterval = setInterval(() => {
            window.scrollBy(0, -scrollSpeed);
        }, 16);
    } else if (e.clientY > viewportHeight - scrollZone) {
        // Scroll vers le bas
        scrollInterval = setInterval(() => {
            window.scrollBy(0, scrollSpeed);
        }, 16);
    }
}
```

Intègre ce code dans la fonction `initDragAndDrop()` existante.
```

---

#### PROMPT 1.3 - Alternative : Affectation par Clic

```
Ajoute une méthode alternative d'affectation des juges par clic (en plus du drag & drop).

Contexte : Le drag & drop peut être difficile sur écran tactile ou avec une longue liste. Ajouter des boutons de sélection/affectation.

Modifications à apporter dans `competition_management_pro.html` :

1. Ajouter un bouton "Affecter" sur chaque juge :
```html
<div class="draggable-item" data-judge-id="{{ judge.id }}">
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <i class="fas fa-user-tie me-2"></i>
            <strong>{{ judge.full_name }}</strong>
        </div>
        <button class="btn btn-sm btn-outline-primary btn-assign-judge" 
                data-judge-id="{{ judge.id }}"
                data-judge-name="{{ judge.full_name }}"
                title="{% trans 'Affecter à une catégorie' %}">
            <i class="fas fa-arrow-right"></i>
        </button>
    </div>
</div>
```

2. Créer un modal de sélection de catégorie :
```html
<div class="modal fade" id="assignJudgeModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>{% trans "Affecter" %} <span id="judgeNameToAssign"></span></h5>
            </div>
            <div class="modal-body">
                <p>{% trans "Sélectionnez la catégorie :" %}</p>
                <div class="list-group" id="categoryListForAssign">
                    {% for category in competition.categories.all %}
                    <button class="list-group-item list-group-item-action" 
                            data-category-id="{{ category.id }}">
                        {{ category.name }}
                        <span class="badge bg-secondary float-end">
                            {{ category.technical_judges.count }} juges
                        </span>
                    </button>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
```

3. JavaScript pour gérer l'affectation par clic :
```javascript
document.querySelectorAll('.btn-assign-judge').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const judgeId = this.dataset.judgeId;
        const judgeName = this.dataset.judgeName;
        document.getElementById('judgeNameToAssign').textContent = judgeName;
        document.getElementById('assignJudgeModal').dataset.judgeId = judgeId;
        new bootstrap.Modal(document.getElementById('assignJudgeModal')).show();
    });
});

document.querySelectorAll('#categoryListForAssign .list-group-item').forEach(item => {
    item.addEventListener('click', function() {
        const judgeId = document.getElementById('assignJudgeModal').dataset.judgeId;
        const categoryId = this.dataset.categoryId;
        assignJudgeToCategory(judgeId, categoryId);
        bootstrap.Modal.getInstance(document.getElementById('assignJudgeModal')).hide();
    });
});
```

Implémente cette solution complète.
```

---

## 🎯 SECTION 2 : NOTATION TECHNIQUE

### 🐛 Bug #2 : Égalité - Nouvelle note écrase au lieu d'ajouter

**Contexte du problème :**
En cas d'égalité nécessitant une nouvelle note (barrage), la note supplémentaire écrase la précédente au lieu de s'ajouter. Cela fausse le résultat final.

**Fichiers concernés :**
- `apps/competitions/models/technical_scoring.py` (modèle TechnicalScore)
- Vue de soumission des scores

---

#### PROMPT 2.1 - Investigation

```
Analyse le bug de notation en cas d'égalité dans le module notation technique de MartialComp.

Problème : Quand il y a égalité et qu'un barrage est nécessaire, la nouvelle note écrase la précédente au lieu de s'ajouter comme note de barrage.

Fichiers à analyser :
1. `apps/competitions/models/technical_scoring.py` - Modèle TechnicalScore
2. La vue qui gère la soumission des scores
3. La logique de calcul du classement

Questions à investiguer :
1. Le modèle TechnicalScore a-t-il un champ pour distinguer les tours de notation ?
2. La contrainte `unique_together = ['performance', 'judge', 'criterion']` empêche-t-elle d'avoir plusieurs notes ?
3. Comment est gérée la logique de barrage/égalité ?

Le modèle actuel :
```python
class TechnicalScore(models.Model):
    performance = models.ForeignKey(TechnicalPerformance, ...)
    judge = models.ForeignKey(User, ...)
    criterion = models.ForeignKey(ScoringCriterion, ...)
    value = models.DecimalField(...)
    # ... pas de champ 'round' ou 'attempt'
    
    class Meta:
        unique_together = ['performance', 'judge', 'criterion']
```

Le problème est probablement que `unique_together` force une seule note par juge/critère/performance.

Fournis une analyse complète et propose une solution.
```

---

#### PROMPT 2.2 - Correction du Modèle

```
Corrige le modèle TechnicalScore pour supporter les notes de barrage en cas d'égalité.

Solution : Ajouter un champ `round_number` pour distinguer les tours de notation.

Modifications dans `apps/competitions/models/technical_scoring.py` :

```python
class TechnicalScore(models.Model):
    """Note technique attribuée par un juge"""
    
    ROUND_TYPES = [
        (1, _('Tour initial')),
        (2, _('Barrage 1')),
        (3, _('Barrage 2')),
        (4, _('Barrage 3')),
    ]
    
    performance = models.ForeignKey(TechnicalPerformance, on_delete=models.CASCADE, 
                                  related_name='scores',
                                  verbose_name=_("Prestation"))
    judge = models.ForeignKey(User, on_delete=models.CASCADE, 
                           related_name='technical_scores',
                           verbose_name=_("Juge"))
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE, 
                                related_name='technical_scores',
                                verbose_name=_("Critère"))
    value = models.DecimalField(_("Note"), max_digits=4, decimal_places=2)
    
    # NOUVEAU : Numéro du tour de notation
    round_number = models.PositiveSmallIntegerField(
        _("Tour de notation"),
        choices=ROUND_TYPES,
        default=1,
        help_text=_("1 = Tour initial, 2+ = Barrages")
    )
    
    submitted_at = models.DateTimeField(_("Soumis le"), auto_now_add=True)
    is_locked = models.BooleanField(_("Verrouillé"), default=False)
    is_training_score = models.BooleanField(_("Note de formation"), default=False)
    
    # NOUVEAU : Flag pour indiquer si c'est la note active pour le classement
    is_active_for_ranking = models.BooleanField(
        _("Active pour le classement"),
        default=True,
        help_text=_("Si False, cette note n'est pas comptée dans le classement final")
    )
    
    class Meta:
        verbose_name = _("Note technique")
        verbose_name_plural = _("Notes techniques")
        # MODIFICATION : Ajouter round_number à unique_together
        unique_together = ['performance', 'judge', 'criterion', 'round_number']
        ordering = ['performance', 'round_number', 'judge']
```

Crée la migration :
```bash
python manage.py makemigrations competitions --name add_round_number_to_technical_score
python manage.py migrate
```

Mets à jour la vue de soumission pour :
1. Détecter si c'est un tour initial ou un barrage
2. Créer une nouvelle note avec `round_number` incrémenté si barrage
3. Ne pas modifier les notes existantes
```

---

#### PROMPT 2.3 - Logique de Barrage

```
Implémente la logique de gestion des barrages pour la notation technique.

Fichier : `apps/competitions/services/scoring_service.py` (à créer ou modifier)

```python
class ScoringService:
    """Service de gestion de la notation technique"""
    
    @staticmethod
    def get_current_round(category):
        """Détermine le tour de notation actuel pour une catégorie"""
        from competitions.models import TechnicalScore, TechnicalPerformance
        
        performances = TechnicalPerformance.objects.filter(category=category)
        if not performances.exists():
            return 1
        
        # Trouver le plus haut round_number utilisé
        max_round = TechnicalScore.objects.filter(
            performance__category=category
        ).aggregate(max_round=Max('round_number'))['max_round'] or 1
        
        return max_round
    
    @staticmethod
    def check_for_tie(category, round_number=1):
        """
        Vérifie s'il y a égalité nécessitant un barrage.
        Retourne les performances ex-aequo si égalité, None sinon.
        """
        from competitions.models import TechnicalPerformance, TechnicalScore
        
        # Calculer les scores pour ce round
        performances = TechnicalPerformance.objects.filter(
            category=category,
            status='completed'
        ).annotate(
            round_score=Avg(
                'scores__value',
                filter=Q(scores__round_number=round_number, scores__is_active_for_ranking=True)
            )
        ).order_by('-round_score')
        
        if performances.count() < 2:
            return None
        
        # Vérifier égalité pour le podium (1ère, 2ème, 3ème place)
        scores = [p.round_score for p in performances[:4] if p.round_score]
        
        ties = []
        for i, score in enumerate(scores[:-1]):
            if score and scores[i+1] and abs(score - scores[i+1]) < 0.001:
                # Égalité détectée
                tied_performances = performances.filter(round_score=score)
                ties.append({
                    'position': i + 1,
                    'score': score,
                    'performances': tied_performances
                })
        
        return ties if ties else None
    
    @staticmethod
    def initiate_tiebreaker(category, tied_performances, current_round):
        """
        Initialise un barrage pour départager les ex-aequo.
        """
        new_round = current_round + 1
        
        # Marquer les performances comme nécessitant un barrage
        for perf in tied_performances:
            perf.status = 'tiebreaker_pending'
            perf.notes = f"Barrage tour {new_round} requis"
            perf.save()
        
        return {
            'round_number': new_round,
            'performances': tied_performances,
            'message': f"Barrage tour {new_round} initialisé pour {len(tied_performances)} performances"
        }
    
    @staticmethod
    def submit_score(performance, judge, criterion, value, round_number=None):
        """
        Soumet une note en gérant correctement les barrages.
        """
        from competitions.models import TechnicalScore
        
        if round_number is None:
            round_number = ScoringService.get_current_round(performance.category)
        
        # Vérifier si une note existe déjà pour ce round
        existing = TechnicalScore.objects.filter(
            performance=performance,
            judge=judge,
            criterion=criterion,
            round_number=round_number
        ).first()
        
        if existing:
            # Mettre à jour si modification autorisée
            config = performance.category.scoring_configuration
            if config and config.allow_score_modification:
                existing.value = value
                existing.save()
                return existing, 'updated'
            else:
                raise ValueError("Modification des notes non autorisée")
        else:
            # Créer nouvelle note
            score = TechnicalScore.objects.create(
                performance=performance,
                judge=judge,
                criterion=criterion,
                value=value,
                round_number=round_number,
                is_active_for_ranking=True
            )
            return score, 'created'
```

Intègre ce service dans les vues de notation.
```

---

### 🐛 Bug #3 : Notes des juges non visibles dans l'admin

#### PROMPT 3.1 - Ajout Vue Admin Notes Détaillées

```
Ajoute une interface pour voir les notes de chaque juge dans l'admin de compétition.

Fichier à créer/modifier : `templates/competitions/manage/scoring_details.html`

Objectif : Permettre au manager de voir toutes les notes individuelles des juges pour chaque performance.

Template :
```html
{% extends "base.html" %}
{% load i18n %}

{% block content %}
<div class="container-fluid">
    <h2>{% trans "Détail des notes par juge" %} - {{ category.name }}</h2>
    
    <div class="table-responsive">
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th rowspan="2">{% trans "Pratiquant" %}</th>
                    {% for judge in judges %}
                    <th colspan="{{ criteria_count }}" class="text-center">
                        {{ judge.get_full_name }}
                        {% if judge.is_training_judge %}
                        <span class="badge bg-warning">{% trans "Formation" %}</span>
                        {% endif %}
                    </th>
                    {% endfor %}
                    <th rowspan="2" class="text-center">{% trans "Moyenne" %}</th>
                    <th rowspan="2" class="text-center">{% trans "Rang" %}</th>
                </tr>
                <tr>
                    {% for judge in judges %}
                        {% for criterion in criteria %}
                        <th class="small text-center" style="writing-mode: vertical-rl;">
                            {{ criterion.name|truncatechars:15 }}
                        </th>
                        {% endfor %}
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for performance in performances %}
                <tr>
                    <td>
                        <strong>{{ performance.practitioner.full_name }}</strong>
                        <br>
                        <small class="text-muted">{{ performance.practitioner.club.name }}</small>
                    </td>
                    {% for judge in judges %}
                        {% for criterion in criteria %}
                        <td class="text-center {% if score.is_extreme %}bg-warning{% endif %}">
                            {% with score=performance.get_score_for_judge_criterion judge criterion %}
                                {% if score %}
                                    {{ score.value }}
                                {% else %}
                                    <span class="text-muted">-</span>
                                {% endif %}
                            {% endwith %}
                        </td>
                        {% endfor %}
                    {% endfor %}
                    <td class="text-center table-info">
                        <strong>{{ performance.calculated_average|floatformat:2 }}</strong>
                    </td>
                    <td class="text-center">
                        {% if performance.ranking == 1 %}
                            <span class="badge bg-warning text-dark">🥇 1er</span>
                        {% elif performance.ranking == 2 %}
                            <span class="badge bg-secondary">🥈 2e</span>
                        {% elif performance.ranking == 3 %}
                            <span class="badge bg-danger">🥉 3e</span>
                        {% else %}
                            {{ performance.ranking }}e
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Légende -->
    <div class="mt-3">
        <span class="badge bg-warning">{% trans "Note extrême (exclue si configuré)" %}</span>
        <span class="badge bg-info ms-2">{% trans "Note de juge en formation (non comptée)" %}</span>
    </div>
    
    <!-- Export -->
    <div class="mt-4">
        <a href="{% url 'competitions:technical_scoring:export_scores' category.id %}" class="btn btn-success">
            <i class="fas fa-file-excel me-2"></i>{% trans "Exporter en Excel" %}
        </a>
        <a href="{% url 'competitions:technical_scoring:export_scores_pdf' category.id %}" class="btn btn-danger">
            <i class="fas fa-file-pdf me-2"></i>{% trans "Exporter en PDF" %}
        </a>
    </div>
</div>
{% endblock %}
```

Vue associée :
```python
@login_required
@competition_manager_required
def scoring_details(request, category_id):
    category = get_object_or_404(CompetitionCategory, id=category_id)
    
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).select_related('practitioner', 'practitioner__club').prefetch_related(
        'scores', 'scores__judge', 'scores__criterion'
    ).order_by('ranking', '-calculated_average')
    
    # Récupérer les juges qui ont noté
    judges = User.objects.filter(
        technical_scores__performance__category=category
    ).distinct()
    
    criteria = ScoringCriterion.objects.filter(category=category, is_active=True)
    
    context = {
        'category': category,
        'performances': performances,
        'judges': judges,
        'criteria': criteria,
        'criteria_count': criteria.count(),
    }
    
    return render(request, 'competitions/manage/scoring_details.html', context)
```

Ajoute l'URL et un lien dans l'interface de gestion.
```

---

### 🐛 Bug #4 : Configuration plage de notation non fonctionnelle

#### PROMPT 4.1 - Investigation Configuration

```
Analyse pourquoi la configuration de la plage de notation (4-7) ne fonctionne pas.

Fichiers à vérifier :
1. `apps/competitions/models/technical_scoring.py` - ScoringConfiguration
2. Template de configuration de catégorie
3. Vue qui sauvegarde la configuration
4. Interface de notation des juges

Le modèle ScoringConfiguration existe :
```python
class ScoringConfiguration(models.Model):
    category = models.OneToOneField(CompetitionCategory, ...)
    min_score = models.DecimalField(default=0.0)
    max_score = models.DecimalField(default=10.0)
    score_step = models.DecimalField(default=0.25)
    # ...
```

Questions à investiguer :
1. La configuration est-elle correctement créée pour chaque catégorie ?
2. Le formulaire de configuration affiche-t-il les bons champs ?
3. L'interface de notation des juges récupère-t-elle et applique-t-elle cette config ?
4. La validation côté serveur utilise-t-elle ces valeurs ?

Vérifie aussi :
- Le template de saisie des notes utilise-t-il min/max dans les inputs ?
- Le JavaScript de validation utilise-t-il ces valeurs ?
```

---

#### PROMPT 4.2 - Correction Interface Configuration

```
Corrige l'interface de configuration de la notation technique.

1. Formulaire de configuration (forms.py) :
```python
class ScoringConfigurationForm(forms.ModelForm):
    class Meta:
        model = ScoringConfiguration
        fields = [
            'min_score', 'max_score', 'score_step',
            'exclude_extreme_scores', 'allow_ties',
            'allow_score_modification', 'real_time_results',
            'training_judges_included'
        ]
        widgets = {
            'min_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'step': '0.5'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'step': '0.5'
            }),
            'score_step': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('0.25', '0.25'),
                ('0.5', '0.5'),
                ('1', '1'),
            ]),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score and max_score and min_score >= max_score:
            raise forms.ValidationError(
                _("La note minimale doit être inférieure à la note maximale.")
            )
        
        return cleaned_data
```

2. Template de configuration :
```html
<div class="card mb-4">
    <div class="card-header bg-primary text-white">
        <h5><i class="fas fa-sliders-h me-2"></i>{% trans "Configuration de la notation" %}</h5>
    </div>
    <div class="card-body">
        <form method="post" action="{% url 'competitions:technical_scoring:save_config' category.id %}">
            {% csrf_token %}
            
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">{% trans "Note minimale" %}</label>
                    <input type="number" name="min_score" class="form-control" 
                           value="{{ config.min_score|default:4 }}" min="0" max="10" step="0.5">
                    <small class="text-muted">{% trans "Ex: 4 pour une plage 4-7" %}</small>
                </div>
                <div class="col-md-4">
                    <label class="form-label">{% trans "Note maximale" %}</label>
                    <input type="number" name="max_score" class="form-control" 
                           value="{{ config.max_score|default:7 }}" min="0" max="10" step="0.5">
                    <small class="text-muted">{% trans "Ex: 7 pour une plage 4-7" %}</small>
                </div>
                <div class="col-md-4">
                    <label class="form-label">{% trans "Pas de notation" %}</label>
                    <select name="score_step" class="form-select">
                        <option value="0.25" {% if config.score_step == 0.25 %}selected{% endif %}>0.25</option>
                        <option value="0.5" {% if config.score_step == 0.5 %}selected{% endif %}>0.5</option>
                        <option value="1" {% if config.score_step == 1 %}selected{% endif %}>1</option>
                    </select>
                </div>
            </div>
            
            <hr>
            
            <h6>{% trans "Critères de notation" %}</h6>
            <div id="criteriaList">
                {% for criterion in config.category.scoring_criteria.all %}
                <div class="criterion-item d-flex align-items-center mb-2">
                    <input type="text" name="criterion_name[]" class="form-control me-2" 
                           value="{{ criterion.name }}" placeholder="{% trans 'Nom du critère' %}">
                    <input type="number" name="criterion_weight[]" class="form-control me-2" 
                           value="{{ criterion.weight }}" step="0.1" min="0" max="5" style="width: 100px;">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-criterion">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                {% empty %}
                <!-- Critères par défaut -->
                <div class="criterion-item d-flex align-items-center mb-2">
                    <input type="text" name="criterion_name[]" class="form-control me-2" value="Forme" placeholder="Nom">
                    <input type="number" name="criterion_weight[]" class="form-control me-2" value="1" step="0.1" style="width: 100px;">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-criterion"><i class="fas fa-times"></i></button>
                </div>
                <div class="criterion-item d-flex align-items-center mb-2">
                    <input type="text" name="criterion_name[]" class="form-control me-2" value="Esprit de combat" placeholder="Nom">
                    <input type="number" name="criterion_weight[]" class="form-control me-2" value="1" step="0.1" style="width: 100px;">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-criterion"><i class="fas fa-times"></i></button>
                </div>
                <div class="criterion-item d-flex align-items-center mb-2">
                    <input type="text" name="criterion_name[]" class="form-control me-2" value="Techniques" placeholder="Nom">
                    <input type="number" name="criterion_weight[]" class="form-control me-2" value="1" step="0.1" style="width: 100px;">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-criterion"><i class="fas fa-times"></i></button>
                </div>
                <div class="criterion-item d-flex align-items-center mb-2">
                    <input type="text" name="criterion_name[]" class="form-control me-2" value="Aspect général" placeholder="Nom">
                    <input type="number" name="criterion_weight[]" class="form-control me-2" value="1" step="0.1" style="width: 100px;">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-criterion"><i class="fas fa-times"></i></button>
                </div>
                {% endfor %}
            </div>
            <button type="button" class="btn btn-outline-secondary btn-sm" id="addCriterion">
                <i class="fas fa-plus me-1"></i>{% trans "Ajouter un critère" %}
            </button>
            
            <hr>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save me-2"></i>{% trans "Enregistrer la configuration" %}
            </button>
        </form>
    </div>
</div>
```

3. Vue de sauvegarde de la configuration :
```python
@login_required
@require_POST
def save_scoring_config(request, category_id):
    category = get_object_or_404(CompetitionCategory, id=category_id)
    
    # Créer ou mettre à jour la configuration
    config, created = ScoringConfiguration.objects.get_or_create(category=category)
    
    config.min_score = Decimal(request.POST.get('min_score', '0'))
    config.max_score = Decimal(request.POST.get('max_score', '10'))
    config.score_step = Decimal(request.POST.get('score_step', '0.25'))
    config.save()
    
    # Gérer les critères
    criterion_names = request.POST.getlist('criterion_name[]')
    criterion_weights = request.POST.getlist('criterion_weight[]')
    
    # Supprimer les anciens critères
    ScoringCriterion.objects.filter(category=category).delete()
    
    # Créer les nouveaux
    for i, name in enumerate(criterion_names):
        if name.strip():
            weight = Decimal(criterion_weights[i]) if i < len(criterion_weights) else Decimal('1')
            ScoringCriterion.objects.create(
                category=category,
                name=name.strip(),
                weight=weight,
                min_score=config.min_score,
                max_score=config.max_score,
                step=config.score_step,
                order=i
            )
    
    messages.success(request, _("Configuration enregistrée avec succès."))
    return redirect('competitions:manage:category_detail', category_id=category_id)
```

Implémente cette solution complète.
```

---

### 🐛 Bug #5 : Nom catégorie caché par photos podium

#### PROMPT 5.1 - Correction CSS Podium

```
Corrige l'affichage du podium pour que le nom de la catégorie ne soit pas caché par les photos.

Fichier : Template d'affichage des résultats/podium

Problème : Les photos des médaillés chevauchent ou cachent le titre de la catégorie.

Solution CSS :
```css
/* Conteneur du podium */
.podium-container {
    position: relative;
    padding-top: 80px; /* Espace pour le titre */
}

.podium-category-title {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    text-align: center;
    font-size: 1.5rem;
    font-weight: bold;
    border-radius: 10px 10px 0 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Photos du podium */
.podium-photos {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 20px;
    margin-top: 20px;
}

.podium-photo {
    position: relative;
    z-index: 50; /* Sous le titre */
}

.podium-photo img {
    border-radius: 50%;
    border: 4px solid;
    object-fit: cover;
}

.podium-photo.gold img {
    border-color: #FFD700;
    width: 120px;
    height: 120px;
}

.podium-photo.silver img {
    border-color: #C0C0C0;
    width: 100px;
    height: 100px;
}

.podium-photo.bronze img {
    border-color: #CD7F32;
    width: 100px;
    height: 100px;
}

/* Nom sous la photo */
.podium-name {
    text-align: center;
    margin-top: 10px;
    font-weight: 600;
}
```

Template HTML corrigé :
```html
<div class="podium-container">
    <!-- Titre TOUJOURS visible -->
    <div class="podium-category-title">
        <i class="fas fa-trophy me-2"></i>
        {{ category.name }}
    </div>
    
    <!-- Photos en dessous -->
    <div class="podium-photos">
        <!-- 2ème place (gauche) -->
        <div class="podium-photo silver">
            {% if second_place %}
            <img src="{{ second_place.practitioner.photo.url|default:'/static/img/default-avatar.png' }}" 
                 alt="{{ second_place.practitioner.full_name }}">
            <div class="podium-name">
                🥈 {{ second_place.practitioner.full_name }}
            </div>
            {% endif %}
        </div>
        
        <!-- 1ère place (centre, plus grand) -->
        <div class="podium-photo gold">
            {% if first_place %}
            <img src="{{ first_place.practitioner.photo.url|default:'/static/img/default-avatar.png' }}" 
                 alt="{{ first_place.practitioner.full_name }}">
            <div class="podium-name">
                🥇 {{ first_place.practitioner.full_name }}
            </div>
            {% endif %}
        </div>
        
        <!-- 3ème place (droite) -->
        <div class="podium-photo bronze">
            {% if third_place %}
            <img src="{{ third_place.practitioner.photo.url|default:'/static/img/default-avatar.png' }}" 
                 alt="{{ third_place.practitioner.full_name }}">
            <div class="podium-name">
                🥉 {{ third_place.practitioner.full_name }}
            </div>
            {% endif %}
        </div>
    </div>
</div>
```

Applique ces modifications au template de résultats.
```

---

## 🎯 SECTION 3 : MODULE ASSAUT / COMBAT

### 🐛 Bug #6 : Scores non enregistrés à la fin du combat

#### PROMPT 6.1 - Investigation

```
Analyse pourquoi les scores des assauts ne sont pas enregistrés à la fin du combat.

Fichiers à vérifier :
1. `apps/competitions/models/combat.py` - Modèle Combat/Match
2. Vue de fin de combat
3. JavaScript qui gère la fin du timer
4. API d'enregistrement des scores

Questions clés :
1. Quel événement déclenche l'enregistrement du score ?
2. La requête AJAX de fin de combat est-elle envoyée ?
3. La vue reçoit-elle et traite-t-elle correctement les données ?
4. Y a-t-il des erreurs JavaScript dans la console ?

Vérifie le flux :
1. Timer arrive à 0 → événement 'combat_end' déclenché ?
2. Scores collectés depuis l'interface → valeurs correctes ?
3. Requête POST envoyée → status HTTP ?
4. Vue Django → sauvegarde en base ?

Fournis un diagnostic avec les points de défaillance identifiés.
```

---

#### PROMPT 6.2 - Correction Enregistrement Scores

```
Corrige le système d'enregistrement des scores de combat/assaut.

1. Modèle Combat (vérifier les champs) :
```python
class Combat(models.Model):
    # ... champs existants ...
    
    # Scores
    score_rouge = models.PositiveIntegerField(_("Score Rouge"), default=0)
    score_blanc = models.PositiveIntegerField(_("Score Blanc"), default=0)
    
    # Résultat
    RESULT_CHOICES = [
        ('rouge', _('Victoire Rouge')),
        ('blanc', _('Victoire Blanc')),
        ('egalite', _('Égalité')),
        ('abandon_rouge', _('Abandon Rouge')),
        ('abandon_blanc', _('Abandon Blanc')),
        ('disqualification_rouge', _('Disqualification Rouge')),
        ('disqualification_blanc', _('Disqualification Blanc')),
    ]
    resultat = models.CharField(_("Résultat"), max_length=30, choices=RESULT_CHOICES, 
                                null=True, blank=True)
    vainqueur = models.ForeignKey('Equipe', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='combats_gagnes')
    
    # Timestamps
    debut = models.DateTimeField(_("Début"), null=True, blank=True)
    fin = models.DateTimeField(_("Fin"), null=True, blank=True)
    
    def terminer_combat(self, score_rouge, score_blanc):
        """Enregistre les scores et détermine le vainqueur."""
        self.score_rouge = score_rouge
        self.score_blanc = score_blanc
        self.fin = timezone.now()
        
        if score_rouge > score_blanc:
            self.resultat = 'rouge'
            self.vainqueur = self.equipe_rouge
        elif score_blanc > score_rouge:
            self.resultat = 'blanc'
            self.vainqueur = self.equipe_blanche
        else:
            self.resultat = 'egalite'
            self.vainqueur = None
        
        self.statut = 'termine'
        self.save()
        
        return self
```

2. Vue API pour terminer le combat :
```python
@login_required
@require_POST
def terminer_combat_api(request, combat_id):
    """API pour enregistrer la fin d'un combat avec les scores."""
    try:
        combat = get_object_or_404(Combat, id=combat_id)
        
        data = json.loads(request.body)
        score_rouge = int(data.get('score_rouge', 0))
        score_blanc = int(data.get('score_blanc', 0))
        
        combat.terminer_combat(score_rouge, score_blanc)
        
        return JsonResponse({
            'success': True,
            'message': _('Combat terminé et scores enregistrés'),
            'combat': {
                'id': combat.id,
                'score_rouge': combat.score_rouge,
                'score_blanc': combat.score_blanc,
                'resultat': combat.resultat,
                'vainqueur': combat.vainqueur.nom if combat.vainqueur else None,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

3. JavaScript pour envoyer les scores à la fin du timer :
```javascript
// Quand le timer atteint 0
function onTimerEnd() {
    // Collecter les scores actuels
    const scoreRouge = parseInt(document.getElementById('scoreRouge').textContent) || 0;
    const scoreBlanc = parseInt(document.getElementById('scoreBlanc').textContent) || 0;
    
    // Jouer le son de gong (voir Bug #10)
    playGongSound();
    
    // Envoyer les scores au serveur
    fetch(`/api/combat/${combatId}/terminer/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            score_rouge: scoreRouge,
            score_blanc: scoreBlanc,
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Afficher le résultat
            showCombatResult(data.combat);
            // Passer au combat suivant ou afficher le podium
        } else {
            console.error('Erreur:', data.error);
            alert('Erreur lors de l\'enregistrement des scores: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erreur réseau:', error);
        // Sauvegarder localement pour retry
        savePendingScore(combatId, scoreRouge, scoreBlanc);
    });
}

// Sauvegarde locale en cas d'échec réseau
function savePendingScore(combatId, scoreRouge, scoreBlanc) {
    const pending = JSON.parse(localStorage.getItem('pendingScores') || '[]');
    pending.push({ combatId, scoreRouge, scoreBlanc, timestamp: Date.now() });
    localStorage.setItem('pendingScores', JSON.stringify(pending));
}
```

Implémente cette solution et ajoute des logs pour le debugging.
```

---

### 🐛 Bug #8 : Génération automatique des poules non fonctionnelle

#### PROMPT 8.1 - Correction Génération Poules

```
Corrige la génération automatique des poules pour les combats.

Fichier : `apps/competitions/services/pool_generator.py`

```python
class PoolGenerator:
    """Générateur de poules pour les compétitions de combat."""
    
    @staticmethod
    def generate_pools(category, pool_size=4, seed_by='random'):
        """
        Génère automatiquement les poules pour une catégorie de combat.
        
        Args:
            category: CompetitionCategory
            pool_size: Nombre de combattants par poule (3-5)
            seed_by: Méthode de répartition ('random', 'grade', 'club')
        
        Returns:
            Liste des poules créées
        """
        from competitions.models import Poule, Combat, CompetitionRegistration
        
        # Récupérer les inscrits dans cette catégorie
        registrations = CompetitionRegistration.objects.filter(
            competition=category.competition,
            categories=category,
            status='approved',
            is_competitor=True
        ).select_related('practitioner', 'practitioner__club')
        
        participants = list(registrations)
        
        if len(participants) < 2:
            raise ValueError(_("Il faut au moins 2 participants pour créer des poules."))
        
        # Mélanger ou trier selon la méthode
        if seed_by == 'random':
            import random
            random.shuffle(participants)
        elif seed_by == 'grade':
            participants.sort(key=lambda r: r.practitioner.current_grade_level or 0, reverse=True)
        elif seed_by == 'club':
            # Séparer les membres du même club
            participants = PoolGenerator._separate_clubs(participants)
        
        # Calculer le nombre de poules
        num_participants = len(participants)
        num_pools = max(1, (num_participants + pool_size - 1) // pool_size)
        
        # Ajuster la taille des poules si nécessaire
        actual_pool_size = (num_participants + num_pools - 1) // num_pools
        
        pools = []
        
        with transaction.atomic():
            # Supprimer les anciennes poules de cette catégorie
            Poule.objects.filter(category=category).delete()
            
            # Créer les nouvelles poules
            for i in range(num_pools):
                pool = Poule.objects.create(
                    category=category,
                    nom=f"Poule {chr(65 + i)}",  # A, B, C, ...
                    numero=i + 1
                )
                
                # Assigner les participants à cette poule
                start_idx = i * actual_pool_size
                end_idx = min(start_idx + actual_pool_size, num_participants)
                pool_participants = participants[start_idx:end_idx]
                
                for reg in pool_participants:
                    pool.participants.add(reg.practitioner)
                
                # Générer les combats de la poule (round-robin)
                combats = PoolGenerator._generate_round_robin_matches(pool, pool_participants)
                pool.combats.set(combats)
                
                pools.append(pool)
        
        return pools
    
    @staticmethod
    def _separate_clubs(participants):
        """Réorganise pour éviter les membres du même club dans la même poule."""
        from collections import defaultdict
        
        by_club = defaultdict(list)
        for p in participants:
            club_id = p.practitioner.club_id or 0
            by_club[club_id].append(p)
        
        # Distribuer en alternant les clubs
        result = []
        club_lists = list(by_club.values())
        max_len = max(len(lst) for lst in club_lists)
        
        for i in range(max_len):
            for club_list in club_lists:
                if i < len(club_list):
                    result.append(club_list[i])
        
        return result
    
    @staticmethod
    def _generate_round_robin_matches(pool, participants):
        """Génère tous les combats d'une poule (chacun contre chacun)."""
        from competitions.models import Combat
        
        combats = []
        practitioners = [r.practitioner for r in participants]
        
        for i in range(len(practitioners)):
            for j in range(i + 1, len(practitioners)):
                combat = Combat.objects.create(
                    poule=pool,
                    category=pool.category,
                    equipe_rouge=practitioners[i],
                    equipe_blanche=practitioners[j],
                    ordre=len(combats) + 1,
                    statut='programme'
                )
                combats.append(combat)
        
        return combats
```

Vue pour déclencher la génération :
```python
@login_required
@require_POST
def generate_pools_api(request, category_id):
    category = get_object_or_404(CompetitionCategory, id=category_id)
    
    pool_size = int(request.POST.get('pool_size', 4))
    seed_by = request.POST.get('seed_by', 'random')
    
    try:
        pools = PoolGenerator.generate_pools(category, pool_size, seed_by)
        
        return JsonResponse({
            'success': True,
            'message': _("{} poules générées avec succès.").format(len(pools)),
            'pools': [{
                'id': p.id,
                'nom': p.nom,
                'participants_count': p.participants.count(),
                'combats_count': p.combats.count()
            } for p in pools]
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

Implémente cette solution et teste avec différents nombres de participants.
```

---

### 🆕 Feature #9 : Configurer finale après poules

#### PROMPT 9.1 - Ajout Phase Finale

```
Ajoute la possibilité de configurer une phase finale après les poules.

1. Modèle pour la configuration de phase finale :
```python
class PhaseFinale(models.Model):
    """Configuration de la phase finale après les poules."""
    
    FORMAT_CHOICES = [
        ('direct_elimination', _('Élimination directe')),
        ('double_elimination', _('Double élimination')),
        ('best_of_pools', _('Meilleurs des poules')),
    ]
    
    category = models.OneToOneField(CompetitionCategory, on_delete=models.CASCADE,
                                    related_name='phase_finale')
    format = models.CharField(_("Format"), max_length=30, choices=FORMAT_CHOICES,
                             default='direct_elimination')
    qualifies_per_pool = models.PositiveSmallIntegerField(
        _("Qualifiés par poule"),
        default=2,
        help_text=_("Nombre de combattants qualifiés par poule pour la finale")
    )
    repechage = models.BooleanField(_("Repêchage pour 3e place"), default=True)
    is_active = models.BooleanField(_("Activée"), default=False)
    
    def generate_bracket(self):
        """Génère le tableau de la phase finale."""
        from competitions.models import Poule, Combat
        
        # Récupérer les qualifiés de chaque poule
        qualifies = []
        for poule in Poule.objects.filter(category=self.category):
            classement = poule.get_classement()[:self.qualifies_per_pool]
            qualifies.extend(classement)
        
        # Créer le bracket selon le format
        if self.format == 'direct_elimination':
            return self._create_elimination_bracket(qualifies)
        # ... autres formats
    
    def _create_elimination_bracket(self, qualifies):
        """Crée un tableau d'élimination directe."""
        # Mélanger pour éviter que les 1ers de poule se rencontrent tôt
        # Logique de seeding...
        pass
```

2. Interface de configuration :
```html
<div class="card mt-4">
    <div class="card-header bg-warning text-dark">
        <h5><i class="fas fa-trophy me-2"></i>{% trans "Phase Finale" %}</h5>
    </div>
    <div class="card-body">
        <form method="post" action="{% url 'competitions:combat:configure_finale' category.id %}">
            {% csrf_token %}
            
            <div class="form-check form-switch mb-3">
                <input class="form-check-input" type="checkbox" name="is_active" 
                       id="finaleActive" {% if phase_finale.is_active %}checked{% endif %}>
                <label class="form-check-label" for="finaleActive">
                    {% trans "Activer la phase finale après les poules" %}
                </label>
            </div>
            
            <div class="row" id="finaleOptions" {% if not phase_finale.is_active %}style="display:none"{% endif %}>
                <div class="col-md-6">
                    <label class="form-label">{% trans "Format" %}</label>
                    <select name="format" class="form-select">
                        <option value="direct_elimination">{% trans "Élimination directe" %}</option>
                        <option value="double_elimination">{% trans "Double élimination" %}</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label class="form-label">{% trans "Qualifiés par poule" %}</label>
                    <select name="qualifies_per_pool" class="form-select">
                        <option value="1">1</option>
                        <option value="2" selected>2</option>
                        <option value="3">3</option>
                    </select>
                </div>
                <div class="col-12 mt-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="repechage" 
                               id="repechage" checked>
                        <label class="form-check-label" for="repechage">
                            {% trans "Match de repêchage pour la 3ème place" %}
                        </label>
                    </div>
                </div>
            </div>
            
            <button type="submit" class="btn btn-warning mt-3">
                <i class="fas fa-save me-2"></i>{% trans "Enregistrer" %}
            </button>
        </form>
    </div>
</div>
```

Implémente cette fonctionnalité complète.
```

---

### 🆕 Feature #10 : Son gong fin d'assaut

#### PROMPT 10.1 - Ajout Son Gong

```
Ajoute un son de gong à la fin du temps d'assaut.

1. Fichier audio :
- Placer un fichier `gong.mp3` dans `static/sounds/`
- Durée recommandée : 2-3 secondes

2. JavaScript pour le timer :
```javascript
// Précharger le son
const gongSound = new Audio('/static/sounds/gong.mp3');
gongSound.preload = 'auto';

// Fonction pour jouer le gong
function playGongSound() {
    gongSound.currentTime = 0;
    gongSound.play().catch(e => {
        console.warn('Impossible de jouer le son:', e);
        // Fallback: vibration sur mobile
        if (navigator.vibrate) {
            navigator.vibrate([500, 200, 500]);
        }
    });
}

// Dans la fonction du timer
function updateTimer() {
    if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        playGongSound();
        onTimerEnd();
    } else if (timeRemaining <= 10) {
        // Bip d'avertissement dans les 10 dernières secondes
        playWarningBeep();
    }
    // ... reste du code
}

// Configuration du son (optionnel)
function setSoundVolume(volume) {
    gongSound.volume = volume; // 0.0 à 1.0
}
```

3. Option dans les paramètres de combat :
```html
<div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" id="soundEnabled" checked>
    <label class="form-check-label" for="soundEnabled">
        <i class="fas fa-volume-up me-2"></i>{% trans "Son de gong activé" %}
    </label>
</div>
<div class="mt-2">
    <label class="form-label">{% trans "Volume" %}</label>
    <input type="range" class="form-range" min="0" max="100" value="80" 
           id="soundVolume" onchange="setSoundVolume(this.value/100)">
</div>
```

Implémente cette fonctionnalité avec gestion des erreurs audio.
```

---

### 🐛 Bug #11 : Couleurs agressives pour l'arbitre de table

#### PROMPT 11.1 - Palette de Couleurs Apaisante

```
Modifie la palette de couleurs de l'interface arbitre de table pour la rendre moins agressive.

Fichier CSS : Interface de combat/arbitrage

Ancienne palette (agressive) :
- Rouge vif : #FF0000
- Bleu vif : #0000FF

Nouvelle palette (apaisante, lisible) :
```css
:root {
    /* Couleurs principales - Plus douces */
    --combat-red: #C0392B;      /* Rouge bordeaux, moins agressif */
    --combat-red-light: #E74C3C;
    --combat-red-bg: #FADBD8;
    
    --combat-blue: #2980B9;     /* Bleu océan, apaisant */
    --combat-blue-light: #3498DB;
    --combat-blue-bg: #D4E6F1;
    
    /* Fond et texte */
    --combat-bg: #2C3E50;       /* Fond sombre mais pas noir */
    --combat-text: #ECF0F1;     /* Texte clair */
    
    /* Accents */
    --combat-success: #27AE60;
    --combat-warning: #F39C12;
    --combat-neutral: #95A5A6;
}

/* Zone rouge */
.combat-zone-red {
    background: var(--combat-red-bg);
    border: 3px solid var(--combat-red);
}

.combat-zone-red .score {
    color: var(--combat-red);
    font-size: 4rem;
    font-weight: bold;
}

/* Zone bleue */
.combat-zone-blue {
    background: var(--combat-blue-bg);
    border: 3px solid var(--combat-blue);
}

.combat-zone-blue .score {
    color: var(--combat-blue);
    font-size: 4rem;
    font-weight: bold;
}

/* Boutons de score */
.btn-score-red {
    background: var(--combat-red);
    color: white;
    border: none;
    padding: 20px 30px;
    font-size: 1.5rem;
    border-radius: 10px;
    transition: all 0.2s;
}

.btn-score-red:hover, .btn-score-red:active {
    background: var(--combat-red-light);
    transform: scale(1.05);
}

.btn-score-blue {
    background: var(--combat-blue);
    color: white;
    border: none;
    padding: 20px 30px;
    font-size: 1.5rem;
    border-radius: 10px;
    transition: all 0.2s;
}

.btn-score-blue:hover, .btn-score-blue:active {
    background: var(--combat-blue-light);
    transform: scale(1.05);
}

/* Timer central */
.combat-timer {
    background: var(--combat-bg);
    color: var(--combat-text);
    font-size: 5rem;
    font-family: 'Roboto Mono', monospace;
    padding: 20px 40px;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

/* Mode nuit (encore plus doux) */
.night-mode {
    --combat-red: #922B21;
    --combat-blue: #1A5276;
    --combat-bg: #1C2833;
}
```

Applique cette palette et ajoute un toggle "Mode nuit" pour les arbitres.
```

---

## 📋 Checklist de Correction

| # | Bug/Feature | Prompt | Priorité | Assigné | Status |
|---|-------------|--------|----------|---------|--------|
| 1 | Drag&Drop scroll | 1.2, 1.3 | 🔴 | - | ⬜ |
| 2 | Égalité écrase note | 2.2, 2.3 | 🔴 | - | ⬜ |
| 3 | Notes juges admin | 3.1 | 🟡 | - | ⬜ |
| 4 | Config notation | 4.2 | 🔴 | - | ⬜ |
| 5 | Titre podium | 5.1 | 🟡 | - | ⬜ |
| 6 | Scores combat | 6.2 | 🔴 | - | ⬜ |
| 7 | Podium combat | Dépend #6 | 🔴 | - | ⬜ |
| 8 | Génération poules | 8.1 | 🔴 | - | ⬜ |
| 9 | Phase finale | 9.1 | 🟢 | - | ⬜ |
| 10 | Son gong | 10.1 | 🟢 | - | ⬜ |
| 11 | Couleurs arbitre | 11.1 | 🟡 | - | ⬜ |

---

## 🚀 Ordre de Traitement Recommandé

### Sprint 1 (Urgences - Cette semaine)
1. Bug #6 - Scores non enregistrés (bloque tout le module combat)
2. Bug #8 - Génération poules
3. Bug #2 - Égalité écrase note
4. Bug #4 - Config notation

### Sprint 2 (Améliorations UX)
5. Bug #1 - Drag&Drop scroll + alternative clic
6. Bug #5 - Titre podium
7. Bug #11 - Couleurs arbitre

### Sprint 3 (Nouvelles Features)
8. Bug #3 - Notes juges admin
9. Feature #9 - Phase finale
10. Feature #10 - Son gong
