# DOCUMENTATION : judge_category_view.html

**Vue d'une catégorie pour juges avec liste des performances**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge_category_view.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/judge_category_view.html`
- **Type :** Vue catégorie pour juges
- **Priorité :** 🟠 Moyenne
- **Usage :** Interface complète pour noter les performances d'une catégorie avec liste de participants et formulaire de notation

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/judge/category/<category_id>/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::judge_category_view`

**Nom de l'URL :** `competitions:technical_scoring:judge_category_view`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competition` | `Competition` | Compétition |
| `category` | `CompetitionCategory` | Catégorie |
| `performances` | `List[Performance]` | Liste des performances à noter |
| `current_performance` | `Performance` | Performance actuellement à noter |
| `scoring_criteria` | `List[ScoringCriterion]` | Liste des critères de notation |
| `min_score` | `float` | Score minimum |
| `max_score` | `float` | Score maximum |
| `is_readonly` | `bool` | Si les notes sont en lecture seule |

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Liste des participants (sidebar gauche)

```html
<div class="col-md-4">
    <div class="card">
        <div class="card-header">
            <h5>Participants</h5>
            <span class="badge bg-primary">{{ performances|length }}</span>
        </div>
        <div class="list-group">
            {% for performance in performances %}
            <a href="?performance={{ performance.id }}" 
               class="list-group-item {% if performance.id == current_performance.id %}active{% endif %}">
                <div class="performance-order">{{ forloop.counter }}</div>
                <div>
                    <h6>{{ performance.participant.full_name }}</h6>
                    <small>{{ performance.participant.club.name }}</small>
                </div>
                <span class="badge status-badge {{ performance.status }}">
                    {{ performance.get_status_display }}
                </span>
            </a>
            {% endfor %}
        </div>
    </div>
    
    <!-- Résumé des notes -->
    <div class="card">
        <div class="card-header">
            <h5>Résumé des notes</h5>
        </div>
        <div class="card-body">
            <div class="score-value" id="final-score">--</div>
            <h6>Notes par critère</h6>
            {% for criteria in scoring_criteria %}
            <div class="criteria-item">
                <div class="criteria-name">{{ criteria.name }}</div>
                <div class="criteria-weight">Poids: {{ criteria.weight }}</div>
                <span class="badge">{{ criteria.score|default:"--" }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

### 2. Formulaire de notation (zone principale)

```html
<div class="col-md-8">
    {% if current_performance %}
    <form id="scoring-form" method="post">
        {% csrf_token %}
        
        <!-- Détails participant -->
        <div class="performance-details">
            <h6>Détails du participant</h6>
            <ul>
                <li><strong>Nom:</strong> {{ current_performance.participant.full_name }}</li>
                <li><strong>Club:</strong> {{ current_performance.participant.club.name }}</li>
                <li><strong>Grade:</strong> {{ current_performance.participant.grade }}</li>
            </ul>
        </div>
        
        <!-- Critères de notation -->
        {% for criteria in scoring_criteria %}
        <div class="criteria-input">
            <label>
                <strong>{{ criteria.name }}</strong>
                <span>(Poids: {{ criteria.weight }})</span>
            </label>
            <div class="input-group">
                <button type="button" class="btn decrement-btn">-</button>
                <input type="number" 
                       id="score-{{ criteria.id }}" 
                       name="criteria-{{ criteria.id }}" 
                       min="{{ min_score }}" 
                       max="{{ max_score }}" 
                       step="0.25"
                       value="{% if criteria.score %}{{ criteria.score }}{% endif %}"
                       {% if is_readonly %}readonly{% endif %}>
                <button type="button" class="btn increment-btn">+</button>
                <button type="button" class="btn" data-bs-toggle="modal" 
                        data-bs-target="#keypadModal" data-criteria-id="{{ criteria.id }}">
                    <i class="fas fa-keyboard"></i>
                </button>
            </div>
            <div class="form-text">{{ criteria.description }}</div>
        </div>
        {% endfor %}
        
        <!-- Notes additionnelles -->
        <textarea id="notes" name="notes">{{ notes }}</textarea>
        
        <!-- Boutons -->
        <button type="button" id="reset-btn">Réinitialiser</button>
        <button type="button" id="save-draft-btn">Enregistrer brouillon</button>
        <button type="submit" id="submit-btn">Soumettre les notes</button>
    </form>
    {% endif %}
</div>
```

### 3. Pavé numérique (modal)

```html
<div class="modal fade" id="keypadModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-body">
                <input type="number" id="keypad-input" 
                       min="{{ min_score }}" max="{{ max_score }}" step="0.25">
                
                <!-- Pavé numérique -->
                <div class="numeric-keypad">
                    <!-- Boutons 0-9, C, backspace, +0.25, -0.25 -->
                </div>
            </div>
            <div class="modal-footer">
                <button data-bs-dismiss="modal">Annuler</button>
                <button id="apply-score-btn">Appliquer</button>
            </div>
        </div>
    </div>
</div>
```

### 4. Modal de confirmation

```html
<div class="modal fade" id="confirmSubmitModal">
    <div class="modal-body">
        <div class="alert alert-warning">
            Attention : Une fois soumises, les notes ne pourront plus être modifiées.
        </div>
        <h6>Résumé des notes</h6>
        <div id="notes-summary">
            <!-- Résumé injecté dynamiquement -->
        </div>
    </div>
    <div class="modal-footer">
        <button data-bs-dismiss="modal">Annuler</button>
        <button id="confirm-submit-btn">Confirmer et soumettre</button>
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Liste des participants** : Sidebar avec tous les participants
2. **Sélection performance** : Clic pour sélectionner une performance
3. **Formulaire complet** : Tous les critères avec min/max
4. **Boutons +/-** : Incrément/décrément rapide
5. **Pavé numérique** : Modal avec pavé numérique pour saisie précise
6. **Timer** : Timer pour performance en cours
7. **Calcul automatique** : Score final calculé en temps réel
8. **Résumé des notes** : Affichage des notes par critère
9. **Confirmation** : Modal de confirmation avant soumission
10. **Sauvegarde brouillon** : Bouton pour sauvegarder sans soumettre
11. **Validation** : Vérification que tous les critères sont remplis

---

## 💻 CODE JAVASCRIPT

### Calcul du score final

```javascript
function calculateFinalScore() {
    let totalWeightedScore = 0;
    let totalWeight = 0;
    let allCriteriaScored = true;
    
    {% for criteria in scoring_criteria %}
        const criteriaInput = document.getElementById('score-{{ criteria.id }}');
        if (criteriaInput && criteriaInput.value) {
            const criteriaScore = parseFloat(criteriaInput.value);
            const criteriaWeight = {{ criteria.weight }};
            
            totalWeightedScore += criteriaScore * criteriaWeight;
            totalWeight += criteriaWeight;
        } else {
            allCriteriaScored = false;
        }
    {% endfor %}
    
    if (allCriteriaScored && totalWeight > 0) {
        return (totalWeightedScore / totalWeight).toFixed(2);
    }
    
    return null;
}

function updateFinalScore() {
    const finalScoreDisplay = document.getElementById('final-score');
    const finalScore = calculateFinalScore();
    
    if (finalScore !== null) {
        finalScoreDisplay.textContent = finalScore;
    } else {
        finalScoreDisplay.textContent = '--';
    }
}
```

### Pavé numérique

```javascript
// Gestion du pavé numérique
keypadBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        const value = this.getAttribute('data-value');
        
        if (value === 'clear') {
            keypadInput.value = '';
        } else if (value === 'backspace') {
            keypadInput.value = keypadInput.value.slice(0, -1);
        } else if (value === '+0.25') {
            let currentValue = parseFloat(keypadInput.value) || 0;
            currentValue += 0.25;
            if (currentValue <= {{ max_score }}) {
                keypadInput.value = currentValue.toFixed(2);
            }
        } else if (value === '-0.25') {
            let currentValue = parseFloat(keypadInput.value) || 0;
            currentValue -= 0.25;
            if (currentValue >= {{ min_score }}) {
                keypadInput.value = currentValue.toFixed(2);
            }
        } else {
            keypadInput.value += value;
        }
    });
});
```

### Soumission avec confirmation

```javascript
scoringForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Vérifier complétude
    // Remplir résumé
    // Afficher modal confirmation
    const confirmModal = new bootstrap.Modal(document.getElementById('confirmSubmitModal'));
    confirmModal.show();
});
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load static %}` : Fichiers statiques

### CSS

- Bootstrap 5
- Styles personnalisés pour performance-card, score-input-group, numeric-keypad

### JavaScript

- Vanilla JavaScript
- Bootstrap Modal pour pavé numérique et confirmation

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
