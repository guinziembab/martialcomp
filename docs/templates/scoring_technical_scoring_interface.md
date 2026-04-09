# DOCUMENTATION : scoring_interface.html

**Interface alternative de notation technique pour juges**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `scoring_interface.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/scoring_interface.html`
- **Type :** Interface de notation générique
- **Priorité :** 🔴 Haute
- **Usage :** Interface alternative de notation avec sélection de critères prédéfinis

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/scoring/<competition_id>/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::scoring_interface`

**Nom de l'URL :** `competitions:technical_scoring:scoring_interface`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competition_id` | `int` | ID de la compétition |
| `participants` | `List[Practitioner]` | Liste des participants à noter |
| `scoring_criteria` | `List[Dict]` | Liste des critères de notation |

### Variables optionnelles

| Variable | Type | Description |
|----------|------|-------------|
| `category_id` | `int` | ID de la catégorie (si spécifiée) |

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Grille de notation par critères

Critères prédéfinis :
- **Technique** : Qualité d'exécution des mouvements (0-10)
- **Puissance** : Force et impact des techniques (0-10)
- **Précision** : Exactitude des cibles atteintes (0-10)
- **Style** : Fluidité et esthétique (0-10)

### 2. Boutons de score

```html
<div class="score-buttons">
    {% for i in "0123456789"|make_list %}
    <button type="button" class="btn btn-outline-primary score-btn" 
            data-criteria="technique" data-score="{{ forloop.counter0 }}">
        {{ forloop.counter0 }}
    </button>
    {% endfor %}
</div>
```

### 3. Calcul du score total

```html
<div class="total-score" id="totalScore">0</div>
<small class="text-muted">sur 40 points</small>
```

### 4. Commentaires

```html
<textarea class="form-control" id="comments" name="comments" rows="3"
          placeholder="Ajoutez vos observations..."></textarea>
```

---

## 💻 CODE JAVASCRIPT

### Gestion des boutons de score

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const scoreButtons = document.querySelectorAll('.score-btn');
    const totalScoreElement = document.getElementById('totalScore');
    
    scoreButtons.forEach(button => {
        button.addEventListener('click', function() {
            const criteria = this.dataset.criteria;
            const score = this.dataset.score;
            
            // Déselectionner les autres boutons du même critère
            const criteriaButtons = document.querySelectorAll(`[data-criteria="${criteria}"]`);
            criteriaButtons.forEach(btn => btn.classList.remove('selected'));
            
            // Sélectionner ce bouton
            this.classList.add('selected');
            
            // Mettre à jour le champ caché
            document.getElementById(`${criteria}_score`).value = score;
            
            // Recalculer le total
            updateTotalScore();
        });
    });
    
    function updateTotalScore() {
        let total = 0;
        const scoreInputs = document.querySelectorAll('input[name$="_score"]');
        
        scoreInputs.forEach(input => {
            if (input.value) {
                total += parseInt(input.value);
            }
        });
        
        totalScoreElement.textContent = total;
    }
});
```

### Réinitialisation

```javascript
function resetScores() {
    document.querySelectorAll('.score-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelectorAll('input[name$="_score"]').forEach(input => input.value = '');
    document.getElementById('comments').value = '';
    document.getElementById('totalScore').textContent = '0';
}
```

### Soumission

```javascript
document.getElementById('scoringForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Vérifier que tous les scores sont remplis
    const scoreInputs = document.querySelectorAll('input[name$="_score"]');
    let allScored = true;
    
    scoreInputs.forEach(input => {
        if (!input.value) {
            allScored = false;
        }
    });
    
    if (!allScored) {
        alert("Veuillez renseigner tous les critères de notation.");
        return;
    }
    
    // TODO: Soumettre le formulaire
});
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Sélection par boutons** : Interface tactile avec boutons 0-10
2. **Calcul automatique** : Score total calculé en temps réel
3. **Commentaires** : Zone de texte pour observations
4. **Validation** : Vérification que tous les critères sont remplis
5. **Réinitialisation** : Bouton pour réinitialiser tous les scores
6. **Sauvegarde brouillon** : Bouton de sauvegarde en brouillon (TODO)

### ⚠️ Limitations identifiées

1. **TODO** : Soumission du formulaire non implémentée
2. **TODO** : Sauvegarde en brouillon non implémentée
3. Critères fixes (Technique, Puissance, Précision, Style) - pas dynamiques
4. Pas de sélection de participant
5. Pas de gestion de plusieurs performances

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
@login_required
def scoring_interface(request, competition_id, category_id=None):
    if request.method == 'POST':
        # Traitement des scores soumis
        # TODO: Implémenter la sauvegarde des scores
        messages.success(request, _("Scores enregistrés avec succès."))
        return JsonResponse({'status': 'success'})
    
    context = {
        'competition_id': competition_id,
        'category_id': category_id,
        'participants': [],  # Liste des participants à noter
        'scoring_criteria': [],  # Critères de notation
    }
    
    return render(request, 'competitions/technical_scoring/scoring_interface.html', context)
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `competitions/dashboard/unified_base.html` : Template de base unifié

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load static %}` : Fichiers statiques

### CSS

- Bootstrap 5
- Styles personnalisés pour `.scoring-criteria`, `.criteria-item`, `.score-btn`, `.total-score`

### JavaScript

- Vanilla JavaScript pour gestion interactive

---

## ✅ TESTS RECOMMANDÉS

1. **Sélection boutons** : Vérifier la sélection/désélection
2. **Calcul total** : Vérifier le calcul correct
3. **Validation** : Tester avec scores manquants
4. **Réinitialisation** : Tester le reset

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
