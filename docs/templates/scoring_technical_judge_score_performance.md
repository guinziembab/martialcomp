# DOCUMENTATION : judge_score_performance.html

**Template principal pour la notation technique des performances**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge_score_performance.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/judge_score_performance.html`
- **Type :** Template de notation pour juges
- **Priorité :** 🔴 Haute
- **Usage :** Interface principale pour noter une performance technique

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/performance/<performance_id>/score/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::score_performance`

**Nom de l'URL :** `competitions:technical_scoring:score_performance`

**Exemple :**
```python
url('performance/<int:performance_id>/score/', score_performance, name='score_performance')
```

---

## 📦 CONTEXTE REQUIS

Le template attend les variables suivantes dans le contexte :

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `practitioner` | `Practitioner` | Pratiquant à noter |
| `competition` | `Competition` | Compétition |
| `category` | `CompetitionCategory` | Catégorie |
| `forms` | `List[Tuple[ScoringCriterion, Form]]` | Liste des tuples (critère, formulaire) |
| `config` | `ScoringConfiguration` ou dict | Configuration avec min_score, max_score, score_step |

### Variables optionnelles

| Variable | Type | Description |
|----------|------|-------------|
| `messages` | `List[Message]` | Messages Django (succès, erreur, etc.) |

### Structure de `forms`

```python
forms = [
    (criterion1, form1),
    (criterion2, form2),
    ...
]
```

Chaque formulaire doit avoir :
- `form.value` : Champ de saisie du score
- `form.prefix` : Préfixe du formulaire
- `form.errors` : Erreurs de validation
- `form.fields.value.widget.attrs.readonly` : Indique si verrouillé

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. En-tête du participant

Affiche les informations du pratiquant à noter :

```html
<div class="practitioner-info">
    <h1>{{ practitioner.full_name }}</h1>
    <div class="competition-info">
        {{ competition.title }}
        {{ category.name }}
        {{ practitioner.club.name }}
    </div>
</div>
```

### 2. Messages

Affiche les messages Django (succès, erreurs) :

```html
{% if messages %}
    {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">
            {{ message }}
        </div>
    {% endfor %}
{% endif %}
```

### 3. Formulaire de notation

Boucle sur les critères de notation :

```html
{% for criterion, form in forms %}
    <div class="scoring-card">
        <!-- Nom et description du critère -->
        <div class="criterion-name">{{ criterion.name }}</div>
        {% if criterion.description %}
            <div class="criterion-description">{{ criterion.description }}</div>
        {% endif %}
        
        <!-- Contrôles de saisie -->
        <div class="score-input-container">
            <button class="score-btn decrement">-</button>
            <div class="score-display">{{ form.value }}</div>
            <button class="score-btn increment">+</button>
        </div>
        
        <!-- Min/Max -->
        <div class="min-max-label">
            <span>Min: {{ config.min_score }}</span>
            <span>Max: {{ config.max_score }}</span>
        </div>
    </div>
{% endfor %}
```

### 4. Bouton de soumission

```html
<button type="submit" name="submit_scores">
    Soumettre les notes
</button>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Affichage des critères** : Liste tous les critères de notation
2. **Saisie de scores** : Champ input pour chaque critère
3. **Boutons +/-** : Incrément/décrément avec respect du pas
4. **Validation** : Affichage des erreurs de formulaire
5. **Verrouillage** : Indication visuelle si note verrouillée
6. **Confirmation** : Popup de confirmation avant soumission
7. **Responsive** : Design adapté mobile (< 768px)

### ⚠️ Limitations identifiées

1. Pas de validation JavaScript avancée
2. Pas de sauvegarde automatique (auto-save)
3. Pas d'indication de progression (X/Y critères remplis)
4. Pas de navigation entre performances
5. Pas de prévisualisation du score total

---

## 💻 CODE JAVASCRIPT

### Gestion des boutons +/-

```javascript
function updateValue(input, increment) {
    const step = parseFloat(input.dataset.step || 0.25);
    const minValue = parseFloat(input.min || 0);
    const maxValue = parseFloat(input.max || 10);
    
    let currentValue = parseFloat(input.value) || 0;
    let newValue = increment ? currentValue + step : currentValue - step;
    
    // Arrondir à la précision du pas
    newValue = Math.round(newValue / step) * step;
    
    // Limiter dans la plage autorisée
    newValue = Math.max(minValue, Math.min(newValue, maxValue));
    
    // Mettre à jour l'input et l'affichage
    input.value = newValue.toFixed(2);
    displayElement.textContent = newValue.toFixed(2);
}
```

### Confirmation avant soumission

```javascript
document.querySelector('form').addEventListener('submit', function(e) {
    if (!confirm("Êtes-vous sûr de vouloir soumettre vos notes ?")) {
        e.preventDefault();
    }
});
```

---

## 🎨 STYLES CSS

### Classes principales

- `.scoring-container` : Conteneur principal (max-width: 900px)
- `.practitioner-info` : En-tête avec infos participant
- `.scoring-card` : Carte pour chaque critère
- `.score-input-container` : Conteneur des contrôles de score
- `.score-display` : Affichage du score (grande taille)
- `.score-btn` : Boutons +/- (cercle)
- `.locked-score` : Classe pour scores verrouillés
- `.min-max-label` : Labels min/max

### Responsive

```css
@media (max-width: 768px) {
    .scoring-card { padding: 1rem; }
    .score-display { font-size: 2rem; }
    .score-btn { width: 36px; height: 36px; }
}
```

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
from apps.competitions.views.technical_scoring import score_performance
from django.shortcuts import render

def score_performance(request, performance_id):
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    practitioner = performance.practitioner
    competition = performance.competition
    category = performance.category
    
    # Récupérer les critères
    criteria = ScoringCriterion.objects.filter(category=category)
    
    # Créer les formulaires
    forms = []
    for criterion in criteria:
        form = ScoreForm(criterion=criterion, prefix=f'criterion_{criterion.id}')
        forms.append((criterion, form))
    
    # Configuration
    config = {
        'min_score': 0.0,
        'max_score': 10.0,
        'score_step': 0.25
    }
    
    context = {
        'practitioner': practitioner,
        'competition': competition,
        'category': category,
        'forms': forms,
        'config': config,
    }
    
    return render(request, 'competitions/technical_scoring/judge_score_performance.html', context)
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base Django

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load static %}` : Fichiers statiques

### CSS

- Bootstrap 5 (classes utilisées : `container`, `btn`, `alert`, etc.)
- Font Awesome (icônes : `fas fa-arrow-left`, `fas fa-minus`, `fas fa-plus`, `fas fa-lock`, `fas fa-paper-plane`)

### JavaScript

- Vanilla JavaScript (pas de dépendances externes)
- Compatible avec tous les navigateurs modernes

---

## ✅ TESTS RECOMMANDÉS

### Tests unitaires

1. **Rendu du template** : Vérifier que tous les critères s'affichent
2. **Affichage des scores** : Vérifier l'affichage correct des valeurs
3. **Boutons +/-** : Tester l'incrément/décrément
4. **Validation** : Tester l'affichage des erreurs
5. **Verrouillage** : Tester l'état verrouillé

### Tests d'intégration

1. **Soumission** : Tester la soumission complète du formulaire
2. **Validation côté serveur** : Vérifier les validations Django
3. **Messages** : Tester l'affichage des messages de succès/erreur

---

## 📌 NOTES IMPORTANTES

1. **Pas de modification après soumission** : Les notes sont verrouillées après soumission (selon la configuration)

2. **Pas de notation** : Le pas est défini dans `config.score_step` (défaut: 0.25)

3. **Limites min/max** : Les scores sont limités par `config.min_score` et `config.max_score`

4. **Responsive** : Le template est adapté pour mobile mais peut être amélioré

5. **Accessibilité** : Le template pourrait bénéficier de meilleurs attributs ARIA

---

## 🔄 AMÉLIORATIONS POSSIBLES

1. **Auto-save** : Sauvegarder automatiquement les scores en cours
2. **Indicateur de progression** : Afficher "X/Y critères remplis"
3. **Navigation** : Boutons "Performance précédente/suivante"
4. **Prévisualisation** : Afficher le score total calculé en temps réel
5. **Validation temps réel** : Valider les scores sans attendre la soumission
6. **Undo/Redo** : Permettre d'annuler/rétablir les modifications
7. **Commentaires** : Ajouter un champ de commentaires par critère

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
