# DOCUMENTATION : monitor_live.html

**Monitoring en temps réel d'un combat (vue publique)**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `monitor_live.html`
- **Localisation :** `apps/competitions/templates/competitions/combat/monitor_live.html`
- **Type :** Monitoring public en temps réel
- **Priorité :** 🟠 Moyenne
- **Usage :** Affichage public du combat en temps réel avec synchronisation automatique

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/combat/combats/<combat_id>/monitor/`

**Vue Django :** `apps/competitions/views/combat.py::monitor_match`

**Nom de l'URL :** `competitions:combat:monitor_match`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `combat` | `Combat` | Combat à monitorer |
| `actions` | `List[ActionCombat]` | Historique des actions |
| `can_edit` | `bool` | Si l'utilisateur peut modifier |

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Tableau de bord des scores

```html
<div class="score-board">
    <!-- Score Rouge -->
    <div class="team-section team-red">
        <h2>{{ combat.pratiquant_rouge.full_name }}</h2>
        <div id="score-red" class="score score-red">{{ combat.score_rouge }}</div>
    </div>
    
    <!-- Centre : Timer et statut -->
    <div class="center-section">
        <div id="match-time" class="timer">00:00</div>
        <div id="match-status" class="match-status">{{ combat.get_status_display }}</div>
    </div>
    
    <!-- Score Blanc -->
    <div class="team-section team-blue">
        <h2>{{ combat.pratiquant_blanc.full_name }}</h2>
        <div id="score-blue" class="score score-blue">{{ combat.score_blanc }}</div>
    </div>
</div>
```

### 2. Panneau d'actions (si can_edit)

```html
{% if can_edit and combat.status == 'en_cours' %}
<div class="actions-panel">
    <h3>Ajouter une action</h3>
    
    <!-- Points -->
    <h4>Points</h4>
    <div class="button-grid">
        {% for value in combat.configuration.valeurs_points %}
        <button onclick="sendAction('point', 'red', {{ value }})">
            +{{ value }} Rouge
        </button>
        <button onclick="sendAction('point', 'blue', {{ value }})">
            +{{ value }} Blanc
        </button>
        {% endfor %}
    </div>
    
    <!-- Pénalités, Avertissements, Sorties -->
</div>
{% endif %}
```

### 3. Liste des actions récentes

```html
<div class="actions-list">
    <h3>Actions récentes</h3>
    <div id="actions-list">
        {% for action in actions %}
        <div class="action-item">
            <span class="action-time">{{ action.temps|time:"H:i:s" }}</span>
            <span class="action-type">{{ action.get_type_action_display }}</span>
            <span class="action-team">{{ action.get_couleur_display }}</span>
            <span class="action-points">+{{ action.valeur }}</span>
        </div>
        {% endfor %}
    </div>
</div>
```

---

## 💻 CODE JAVASCRIPT / TEMPS RÉEL

### Module de temps réel

```javascript
// Initialisation
combatRealtime.options = {
    refreshInterval: 2000,
    matchStatusUrl: '{% url "competitions:combat:api_statut_combat" combat.id %}',
    csrfToken: '{{ csrf_token }}',
    actionUrl: '{% url "competitions:combat:ajouter_action" combat.id %}'
};

// Démarrer le monitoring
combatRealtime.startMatchMonitoring({{ combat.id }}, updateMatchUI);
```

### Mise à jour de l'interface

```javascript
function updateMatchUI(data) {
    // Mettre à jour les scores
    document.getElementById('score-red').textContent = data.score_rouge;
    document.getElementById('score-blue').textContent = data.score_blanc;
    
    // Mettre à jour le statut
    // Mettre à jour le timer
    // Mettre à jour la liste des actions
}
```

### Envoi d'action

```javascript
function sendAction(actionType, team, points) {
    combatRealtime.sendAction({{ combat.id }}, actionType, team, points, function(data) {
        if (data.success) {
            // Action enregistrée
        }
    });
}
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base

### Fichiers statiques

- `css/combat.css` : Styles de combat
- `js/combat_scoring_realtime.js` : Module temps réel

### JavaScript

- Module `combatRealtime` pour temps réel
- Polling automatique toutes les 2 secondes

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
