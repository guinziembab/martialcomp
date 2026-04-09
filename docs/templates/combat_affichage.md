# DOCUMENTATION : affichage_combat.html

**Affichage public plein écran d'un combat**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `affichage_combat.html`
- **Localisation :** `apps/competitions/templates/competitions/combat/affichage_combat.html`
- **Type :** Affichage public plein écran
- **Priorité :** 🟡 Faible
- **Usage :** Affichage public sur écran/projecteur avec mode plein écran automatique

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/combat/combats/<combat_id>/affichage/`

**Vue Django :** `apps/competitions/views/combat.py::affichage_combat`

**Nom de l'URL :** `competitions:combat:affichage_combat`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `combat` | `Combat` | Combat à afficher |

---

## 🎨 STRUCTURE DU TEMPLATE

### Mode plein écran

```html
<div class="fullscreen-display" id="combat-display">
    <!-- En-tête -->
    <div class="display-header">
        <h2>{{ combat.competition.title }}</h2>
        <div class="display-timer" id="combat-timer">00:00</div>
        <div>{{ combat.get_status_display }}</div>
    </div>
    
    <!-- Contenu : Scores -->
    <div class="display-content">
        <div class="score-row">
            <!-- Score Rouge (plein écran) -->
            <div class="score-column score-red">
                <div class="score-value" id="score-red">{{ combat.score_rouge }}</div>
                <div class="competitor-name">{{ combat.pratiquant_rouge.full_name }}</div>
                {% if combat.vainqueur == 'rouge' %}
                <div class="winner-mark">✓</div>
                {% endif %}
            </div>
            
            <!-- Séparateur -->
            <div class="score-divider"></div>
            
            <!-- Score Blanc (plein écran) -->
            <div class="score-column score-white">
                <div class="score-value" id="score-white">{{ combat.score_blanc }}</div>
                <div class="competitor-name">{{ combat.pratiquant_blanc.full_name }}</div>
                {% if combat.vainqueur == 'blanc' %}
                <div class="winner-mark">✓</div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Pied de page -->
    <div class="display-footer">
        {{ combat.competition.title }} | {{ combat.get_type_combat_display }}
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Mode plein écran** : Activation automatique au clic
2. **Affichage grand format** : Scores en très grande taille (12rem)
3. **Synchronisation temps réel** : Mise à jour automatique toutes les 2 secondes
4. **Animation flash** : Flash visuel lors de changement de score
5. **Indicateur vainqueur** : Affichage du ✓ pour le vainqueur
6. **Timer automatique** : Timer qui démarre automatiquement
7. **Design optimisé** : Optimisé pour projecteur/écran public

### ⚠️ Limitations identifiées

1. Pas de contrôles d'édition (vue lecture seule)
2. Pas de retour arrière visible
3. Plein écran automatique peut être gênant

---

## 💻 CODE JAVASCRIPT

### Activation plein écran automatique

```javascript
document.addEventListener('click', function() {
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    }
});
```

### Mise à jour des scores

```javascript
function updateScores() {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            // Mettre à jour les scores avec animation flash
            if (oldScoreRed !== newScoreRed) {
                scoreRed.textContent = newScoreRed.toFixed(2);
                redColumn.classList.add('flash-red');
            }
        });
}

// Mise à jour toutes les 2 secondes
setInterval(updateScores, 2000);
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
