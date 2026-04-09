# DOCUMENTATION : scoring/scoring_form.html

**Formulaire de notation technique avec pavé numérique mobile**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `scoring_form.html`
- **Localisation :** `apps/competitions/templates/competitions/scoring/scoring_form.html`
- **Type :** Formulaire de notation
- **Priorité :** 🔴 Haute
- **Usage :** Interface complète de notation avec slider, boutons rapides, et pavé numérique mobile

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/competitions/scoring/form/<performance_id>/` ou via management interface

**Vue Django :** `apps/competitions/views/management/scoring.py::judge_scoring_interface` (ou similaire)

**Nom de l'URL :** `competitions:management:judge_scoring_interface`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competition` | `Competition` | Compétition |
| `category` | `CompetitionCategory` | Catégorie |
| `performance` | `TechnicalPerformance` | Performance à noter |
| `judge` | `JudgeAssignment` | Juge assigné |
| `criteria` | `List[ScoringCriterion]` | Liste des critères |

### Variables optionnelles

| Variable | Type | Description |
|----------|------|-------------|
| `scores` | `Dict` | Scores existants (dict[criterion_id] = score) |

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Informations de performance

```html
<div class="performance-info">
    <h5>Participant</h5>
    <p>{{ performance.practitioner.full_name }}</p>
    <p>{{ performance.practitioner.club.name }}</p>
    <p>Ordre de passage: {{ performance.performance_order }}</p>
</div>
```

### 2. Timer avec contrôles

```html
<div class="timer-container">
    <div class="timer" id="timer">00:00</div>
    <div class="timer-controls">
        <button id="startTimer">Démarrer</button>
        <button id="stopTimer">Arrêter</button>
        <button id="resetTimer">Réinitialiser</button>
    </div>
</div>
```

### 3. Formulaire par critère

```html
{% for criterion in criteria %}
<div class="criterion-card">
    <div class="criterion-header">
        <div>
            <div class="criterion-name">{{ criterion.name }}</div>
            <div class="criterion-description">{{ criterion.description }}</div>
        </div>
        <div class="badge bg-primary">Poids: {{ criterion.weight }}</div>
    </div>
    
    <div class="score-input-group">
        <!-- Slider -->
        <input type="range" 
               class="form-range" 
               min="{{ criterion.min_score }}" 
               max="{{ criterion.max_score }}" 
               step="{{ criterion.step }}"
               id="slider_{{ criterion.id }}"
               value="{{ scores|get_item:criterion.id }}">
        
        <!-- Input numérique -->
        <input type="number" 
               class="score-input" 
               id="score_{{ criterion.id }}" 
               name="score_{{ criterion.id }}"
               readonly>
    </div>
    
    <div class="score-feedback" id="feedback_{{ criterion.id }}"></div>
    
    <!-- Boutons rapides (desktop) -->
    <div class="score-buttons">
        <!-- Boutons générés dynamiquement pour chaque valeur possible -->
    </div>
</div>
{% endfor %}
```

### 4. Pavé numérique mobile

```html
<div class="numeric-keypad" id="numericKeypad">
    <div class="keypad-header">
        <h5 id="keypadTitle">Notation</h5>
        <button id="closeKeypad">×</button>
    </div>
    
    <div class="keypad-display" id="keypadDisplay">0.00</div>
    
    <div class="keypad-grid">
        <button data-value="1">1</button>
        <button data-value="2">2</button>
        <!-- ... -->
        <button data-value="reset">
            <i class="fas fa-redo"></i>
        </button>
    </div>
    
    <div class="keypad-actions">
        <button id="cancelKeypad">Annuler</button>
        <button id="confirmKeypad">Valider</button>
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Slider synchronisé** : Slider et input synchronisés
2. **Pavé numérique mobile** : Pavé numérique pour mobile
3. **Boutons rapides** : Boutons pour valeurs courantes (desktop)
4. **Timer intégré** : Timer pour performance
5. **Feedback visuel** : Affichage du score avec animation pulse
6. **Validation** : Vérification complétude avant soumission
7. **Sauvegarde AJAX** : Sauvegarde via AJAX (démarrage/arrêt performance)

---

## 💻 CODE JAVASCRIPT

### Gestion du pavé numérique

```javascript
function openNumericKeypad(inputId, criterionId, criterionName) {
    activeInputId = inputId;
    activeCriterionId = criterionId;
    
    const input = document.getElementById(inputId);
    originalValue = input.value || "0";
    keypadDisplay.textContent = originalValue;
    keypadTitle.textContent = criterionName;
    
    numericKeypad.classList.add('active');
    keypadOverlay.style.display = 'block';
}

// Gestion des boutons du pavé
keypadButtons.forEach(btn => {
    btn.addEventListener('click', function() {
        const value = this.dataset.value;
        
        if (value === 'reset') {
            keypadDisplay.textContent = '0';
        } else {
            // Logique de construction du nombre
            // Gestion des décimales (0.25, 0.5, 0.75)
        }
    });
});
```

### Synchronisation slider/input

```javascript
sliders.forEach(slider => {
    slider.addEventListener('input', function() {
        const criterionId = this.dataset.criterionId;
        const input = document.getElementById(`score_${criterionId}`);
        const feedback = document.getElementById(`feedback_${criterionId}`);
        
        input.value = this.value;
        feedback.textContent = this.value;
        feedback.classList.add('pulse');
    });
});
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
