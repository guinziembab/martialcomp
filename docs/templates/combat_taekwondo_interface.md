# DOCUMENTATION : taekwondo/interface_combat.html

**Interface spécialisée Taekwondo pour notation en temps réel**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `taekwondo/interface_combat.html`
- **Localisation :** `apps/competitions/templates/competitions/combat/taekwondo/interface_combat.html`
- **Type :** Interface de combat Taekwondo temps réel
- **Priorité :** 🔴 Haute
- **Usage :** Interface spécialisée pour noter les combats Taekwondo avec système de points spécifique

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/combat/taekwondo/combats/<combat_id>/interface/`

**Vue Django :** `apps/competitions/views/combat_taekwondo.py::interface_combat` (ou similaire)

**Nom de l'URL :** `competitions:combat_taekwondo:interface_combat`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `combat` | `Combat` | Combat Taekwondo |
| `penalties` | `Dict` | Dictionnaire des pénalités par couleur |
| `actions` | `List[ActionCombat]` | Historique des actions |
| `is_judge` | `bool` | Si l'utilisateur est juge |

### Structure de `penalties`

```python
penalties = {
    'rouge': {
        'kyong-go': int,      # Nombre de Kyong-go
        'gam-jeom': int       # Nombre de Gam-jeom
    },
    'blanc': {
        'kyong-go': int,
        'gam-jeom': int
    }
}
```

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. En-tête Taekwondo

```html
<div class="taekwondo-header">
    <div class="taekwondo-logo">
        <i class="fas fa-fist-raised"></i> Taekwondo Combat #{{ combat.id }}
    </div>
</div>
```

### 2. Zones de scores (Rouge/Bleu)

Différence principale avec `interface_combat.html` :
- **Rouge/Blanc** devient **Rouge/Bleu**
- Système de points Taekwondo spécifique
- Pénalités Taekwondo : Kyong-go et Gam-jeom

### 3. Points Taekwondo spécifiques

```html
<!-- Points Rouge -->
<button class="btn btn-punch" data-color="rouge" data-point-type="punch">
    Coup de poing (1pt)
</button>
<button class="btn btn-kick-body" data-color="rouge" data-point-type="kick_body">
    Coup de pied au tronc (2pts)
</button>
<button class="btn btn-kick-head" data-color="rouge" data-point-type="kick_head">
    Coup de pied à la tête (3pts)
</button>
<button class="btn btn-turning-kick-body" data-color="rouge" data-point-type="turning_kick_body">
    Coup de pied retourné au tronc (4pts)
</button>
<button class="btn btn-turning-kick-head" data-color="rouge" data-point-type="turning_kick_head">
    Coup de pied retourné à la tête (5pts)
</button>
```

### 4. Pénalités Taekwondo

```html
<!-- Kyong-go (Avertissement) -->
<button class="btn btn-kyong-go" data-color="rouge" data-penalty-type="kyong-go">
    Kyong-go (Avertissement)
</button>

<!-- Gam-jeom (Déduction -1pt) -->
<button class="btn btn-gam-jeom" data-color="rouge" data-penalty-type="gam-jeom">
    Gam-jeom (Déduction -1pt)
</button>
```

### 5. Affichage des pénalités

```html
<div class="penalties-display">
    <div class="penalty-count">
        <strong>Kyong-go:</strong> 
        <span id="kyong-go-red-count">{{ penalties.rouge.kyong-go }}</span>
        <div id="kyong-go-red-badges">
            {% for i in "x"|ljust:penalties.rouge.kyong-go %}
            <span class="penalty-badge kyong-go-badge">K</span>
            {% endfor %}
        </div>
    </div>
    <div class="penalty-count">
        <strong>Gam-jeom:</strong> 
        <span id="gam-jeom-red-count">{{ penalties.rouge.gam-jeom }}</span>
        <div id="gam-jeom-red-badges">
            {% for i in "x"|ljust:penalties.rouge.gam-jeom %}
            <span class="penalty-badge gam-jeom-badge">G</span>
            {% endfor %}
        </div>
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS UNIQUES TAEKWONDO

### ✅ Système de points Taekwondo

1. **Coup de poing** : 1 point
2. **Coup de pied au tronc** : 2 points
3. **Coup de pied à la tête** : 3 points
4. **Coup de pied retourné au tronc** : 4 points
5. **Coup de pied retourné à la tête** : 5 points

### ✅ Pénalités Taekwondo

1. **Kyong-go** : Avertissement (badge jaune "K")
2. **Gam-jeom** : Déduction de 1 point (badge rouge "G")

### ✅ Rounds Taekwondo

- Affichage du round actuel (1/3)
- Timer par round
- Gestion des rounds multiples

---

## 💻 CODE JAVASCRIPT

### Gestion des actions

```javascript
function addAction(data) {
    fetch('{% url "competitions:combat_taekwondo:ajouter_action" combat.id %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour scores et pénalités
            updateCombatStatus();
        }
    });
}
```

### Mise à jour du statut

```javascript
function updateCombatStatus() {
    fetch('{% url "competitions:combat_taekwondo:api_statut_combat" combat.id %}')
        .then(response => response.json())
        .then(data => {
            // Mettre à jour scores
            // Mettre à jour timer et rounds
            // Mettre à jour pénalités
            // Mettre à jour journal actions
        });
}
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load custom_filters %}` : Filtres personnalisés (pour ljust)

### CSS

- Styles Taekwondo spécifiques (rouge/bleu)
- Badges de pénalités (K et G)
- Classes pour chaque type de point

### JavaScript

- Vanilla JavaScript pour gestion interactive
- API calls pour actions de combat

---

## 📌 NOTES IMPORTANTES

1. **Système Taekwondo** : Points et pénalités spécifiques au Taekwondo
2. **Couleurs** : Rouge/Bleu (pas Rouge/Blanc)
3. **Pénalités** : Kyong-go et Gam-jeom avec badges visuels
4. **Rounds** : Support des rounds multiples

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
