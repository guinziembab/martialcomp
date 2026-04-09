# DOCUMENTATION : standalone_scoring/judge/score_entry.html

**Interface de saisie de scores pour juges (système standalone)**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge/score_entry.html`
- **Localisation :** `apps/competitions/templates/competitions/standalone_scoring/judge/score_entry.html`
- **Type :** Interface de saisie de scores standalone
- **Priorité :** 🔴 Haute
- **Usage :** Interface complète pour noter une performance avec système standalone

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/standalone-scoring/judge/score/<performance_id>/`

**Vue Django :** `apps/competitions/views/standalone_scoring.py::JudgeScoreEntryView`

**Nom de l'URL :** `competitions:standalone_scoring:judge_score_entry`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `performance` | `StandalonePerformance` | Performance à noter |
| `criterion_forms` | `List[Form]` | Liste de formulaires (un par critère) |
| `scoring_system` | `StandaloneScoringSystem` | Système de scoring |
| `category_config` | `StandaloneCategoryScoringConfig` | Configuration de catégorie |
| `judge_settings` | `StandaloneJudgeSettings` | Paramètres du juge |
| `practitioner_name` | `str` | Nom du pratiquant |
| `category_name` | `str` | Nom de la catégorie |
| `competition_name` | `str` | Nom de la compétition |
| `all_scores_entered` | `bool` | Si tous les scores sont saisis |

### Structure de `criterion_forms`

Chaque formulaire doit avoir :
- `criterion` : `StandaloneScoringCriterion`
- `initial.score` : Score initial (optionnel)
- `initial.notes` : Notes initiales (optionnel)
- `is_saved` : Si le score est déjà sauvegardé
- `fields.score.widget.attrs.min` : Score minimum
- `fields.score.widget.attrs.max` : Score maximum
- `fields.score.widget.attrs.step` : Pas de notation

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Informations de la performance

```html
<div class="performance-info">
    <h2>{{ practitioner_name }}</h2>
    <div class="row">
        <div class="col-md-4">
            <p><strong>Competition:</strong> {{ competition_name }}</p>
        </div>
        <div class="col-md-4">
            <p><strong>Category:</strong> {{ category_name }}</p>
        </div>
        <div class="col-md-4">
            <p><strong>Round:</strong> {{ performance.get_round_type_display }} {{ performance.round_number }}</p>
        </div>
    </div>
</div>
```

### 2. Formulaire par critère

```html
{% for form in criterion_forms %}
<div class="criterion-card">
    <div class="criterion-header">
        <h3>{{ form.criterion.name }}</h3>
        <span class="criterion-weight">Weight: {{ form.criterion.weight }}</span>
    </div>
    <div class="criterion-body">
        <!-- Contrôles de score -->
        <div class="score-controls">
            <button type="button" class="score-btn decrease-score">-</button>
            <div class="score-display">{{ form.initial.score|default:"0.0" }}</div>
            <button type="button" class="score-btn increase-score">+</button>
        </div>
        
        <!-- Slider -->
        <input type="range" class="score-slider" 
               min="{{ form.fields.score.widget.attrs.min }}" 
               max="{{ form.fields.score.widget.attrs.max }}" 
               step="{{ form.fields.score.widget.attrs.step }}"
               value="{{ form.initial.score|default:'0.0' }}">
        
        <!-- Notes -->
        <textarea name="notes">{{ form.initial.notes|default:"" }}</textarea>
        
        <!-- Indicateur de sauvegarde -->
        <span class="saving-indicator" id="saving-{{ form.criterion.id }}">Saving...</span>
        {% if form.is_saved %}
        <span class="saved-indicator" id="saved-{{ form.criterion.id }}">Saved</span>
        {% endif %}
        
        <!-- Bouton sauvegarder -->
        <button type="button" class="btn btn-primary save-score-btn" 
                data-criterion="{{ form.criterion.id }}">
            Save
        </button>
    </div>
</div>
{% endfor %}
```

### 3. Soumission finale

```html
{% if all_scores_entered %}
<form method="post" action="{% url 'competitions:standalone_scoring:judge_submit_scores' performance.id %}">
    {% csrf_token %}
    <button type="submit" class="judge-btn-submit">Submit All Scores</button>
</form>
{% else %}
<button type="button" class="judge-btn-submit" disabled>Submit All Scores</button>
<p>Please save scores for all criteria before submitting.</p>
{% endif %}
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Saisie par slider** : Slider pour ajuster le score
2. **Boutons +/-** : Incrément/décrément rapide
3. **Sauvegarde individuelle** : Sauvegarde par critère (AJAX)
4. **Indicateurs visuels** : "Saving..." et "Saved"
5. **Notes par critère** : Zone de notes pour chaque critère
6. **Validation complète** : Vérification avant soumission
7. **Affichage pondération** : Poids de chaque critère affiché
8. **Support rounds** : Affichage du round (preliminary, semifinal, final)

### ⚠️ Limitations identifiées

1. Pas de prévisualisation du score total
2. Pas de validation temps réel côté client
3. Pas de navigation entre performances

---

## 💻 CODE JAVASCRIPT

### Gestion du slider

```javascript
slider.addEventListener('input', function() {
    displayElement.textContent = parseFloat(this.value).toFixed(1);
});
```

### Sauvegarde AJAX

```javascript
button.addEventListener('click', function() {
    const criterionId = this.dataset.criterion;
    const slider = document.getElementById(`score-${criterionId}`);
    const notes = document.getElementById(`notes-${criterionId}`).value;
    
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('criterion_id', criterionId);
    formData.append('score', slider.value);
    formData.append('notes', notes);
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            savedIndicator.style.display = 'inline';
            checkAllScoresEntered();
        }
    });
});
```

### Vérification complétude

```javascript
function checkAllScoresEntered() {
    const savedIndicators = document.querySelectorAll('.saved-indicator');
    let allSaved = true;
    
    savedIndicators.forEach(function(indicator) {
        if (indicator.style.display === 'none') {
            allSaved = false;
        }
    });
    
    const submitButton = document.querySelector('.judge-btn-submit');
    if (submitButton) {
        submitButton.disabled = !allSaved;
    }
}
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `competitions/standalone_scoring/judge/base.html` : Base juge standalone

### Tags Django requis

- `{% load i18n %}` : Internationalisation

### CSS

- Variables CSS personnalisées (`--judge-primary`, `--judge-border`, etc.)
- Styles pour `.criterion-card`, `.score-controls`, `.score-display`

### JavaScript

- Vanilla JavaScript pour interactions
- AJAX pour sauvegarde individuelle

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
