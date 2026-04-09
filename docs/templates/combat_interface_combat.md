# DOCUMENTATION : interface_combat.html

**Interface principale de notation en temps réel pour les combats**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `interface_combat.html`
- **Localisation :** `apps/competitions/templates/competitions/combat/interface_combat.html`
- **Type :** Interface de combat en temps réel
- **Priorité :** 🔴 Haute
- **Usage :** **PRINCIPAL** - Interface pour noter les combats en temps réel avec timer et actions

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/combat/combats/<combat_id>/interface/`

**Vue Django :** `apps/competitions/views/combat.py::interface_combat`

**Nom de l'URL :** `competitions:combat:interface_combat`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `combat` | `Combat` | Combat à noter |

### Structure de `combat`

```python
combat = {
    'id': int,
    'poule': Poule,
    'type_combat': str,  # 'individuel' ou 'equipe'
    'status': str,       # 'programmé', 'en_cours', 'terminé', 'annulé'
    'score_rouge': int,
    'score_blanc': int,
    'pratiquant_rouge': Practitioner (si individuel),
    'equipe_rouge': Equipe (si equipe),
    'pratiquant_blanc': Practitioner (si individuel),
    'equipe_blanc': Equipe (si equipe),
    'configuration': CombatConfiguration,  # Configuration avec valeurs_points, valeurs_penalites
}
```

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. En-tête avec timer

```html
<div class="combat-header">
    <h4>Interface d'arbitrage</h4>
    <div class="small">{{ combat.poule.nom }} - {{ combat.get_type_combat_display }}</div>
    <div class="combat-timer" id="combat-timer">00:00</div>
    <div class="small">
        {% if combat.status == 'en_cours' %}
        <span class="badge bg-success">Combat en cours</span>
        {% else %}
        <span class="badge bg-secondary">{{ combat.get_status_display }}</span>
        {% endif %}
    </div>
</div>
```

### 2. Zone des scores (Rouge/Blanc)

```html
<div class="row">
    <!-- Score Rouge -->
    <div class="col-6">
        <div class="score-container score-red">
            <div class="score-value" id="score-red">{{ combat.score_rouge }}</div>
            <div class="competitor-name">
                {% if combat.type_combat == 'individuel' %}
                {{ combat.pratiquant_rouge.full_name }}
                {% else %}
                {{ combat.equipe_rouge.nom }}
                {% endif %}
            </div>
        </div>
        
        <!-- Boutons d'actions (si combat en cours) -->
        {% if combat.status == 'en_cours' %}
        <div class="row g-2 mb-4">
            <!-- Points -->
            {% for point in combat.configuration.valeurs_points %}
            <div class="col-4">
                <button class="btn btn-outline-danger score-badge" 
                        data-action="point" data-value="{{ point }}" data-color="rouge">
                    +{{ point }}
                </button>
            </div>
            {% endfor %}
            
            <!-- Pénalités -->
            {% for penalite in combat.configuration.valeurs_penalites %}
            <div class="col-4">
                <button class="btn btn-outline-dark score-badge" 
                        data-action="penalite" data-value="{{ penalite }}" data-color="rouge">
                    {{ penalite }}
                </button>
            </div>
            {% endfor %}
        </div>
        
        <!-- Actions spéciales -->
        <button class="btn btn-danger action-btn" data-action="sortie" data-color="rouge">
            <i class="fas fa-sign-out-alt"></i> Sortie de tapis
        </button>
        <button class="btn btn-outline-danger action-btn" data-action="avertissement" data-color="rouge">
            <i class="fas fa-exclamation-triangle"></i> Avertissement
        </button>
        {% endif %}
    </div>
    
    <!-- Score Blanc (identique) -->
    <div class="col-6">
        <!-- Même structure pour le blanc -->
    </div>
</div>
```

### 3. Historique des actions

```html
<div class="action-history">
    <h6>Historique des actions</h6>
    <div id="action-list">
        <!-- Actions affichées dynamiquement via JavaScript -->
    </div>
</div>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Timer en temps réel** : Compteur de temps du combat
2. **Scores Rouge/Blanc** : Affichage des scores en temps réel
3. **Actions de combat** : Boutons pour points, pénalités, sortie, avertissement
4. **Historique** : Liste des actions enregistrées
5. **WebSocket** : Synchronisation temps réel (via consumers.py)
6. **Contrôles** : Démarrage, arrêt, annulation du combat
7. **Affichage public** : Lien vers affichage public synchronisé

### ⚠️ Limitations identifiées

1. **TODO** : Vérifier l'implémentation complète du WebSocket
2. **TODO** : Tester la synchronisation multi-utilisateurs
3. **TODO** : Vérifier l'annulation d'actions

---

## 💻 CODE JAVASCRIPT / WEBSOCKET

### Gestion WebSocket (via consumers.py)

```python
class CombatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        combat_id = self.scope['url_route']['kwargs']['combat_id']
        self.combat_group_name = f'combat_{combat_id}'
        
        await self.channel_layer.group_add(
            self.combat_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'add_point':
            # Ajouter un point
            # Diffuser à tous les clients connectés
            await self.channel_layer.group_send(
                self.combat_group_name,
                {
                    'type': 'score_update',
                    'team': data['team'],
                    'points': data['points']
                }
            )
```

---

## 📝 ACTIONS DE COMBAT DISPONIBLES

### Types d'actions

1. **Points** : `+0.25`, `+0.5`, `+1`, `+1.5`, `+2` (configurables)
2. **Pénalités** : `-0.5`, etc. (configurables)
3. **Sortie de tapis** : Action spéciale
4. **Avertissement** : Action spéciale

### Valeurs par défaut (si pas de configuration)

- Points : `+0.25`, `+0.5`, `+1`, `+1.5`, `+2`
- Pénalités : `-0.5`

---

## 🔗 DÉPENDANCES

### Templates étendus

- `base.html` : Template de base

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load static %}` : Fichiers statiques

### CSS

- `combat.css` : Styles spécifiques au combat
- Styles inline pour timer, scores, etc.

### JavaScript

- WebSocket pour temps réel
- Gestion des actions de combat
- Mise à jour du timer

---

## ✅ TESTS RECOMMANDÉS

1. **Timer** : Vérifier le fonctionnement du timer
2. **Actions** : Tester chaque type d'action
3. **Synchronisation** : Tester avec plusieurs clients
4. **WebSocket** : Tester la connexion et les messages
5. **Annulation** : Tester l'annulation d'actions

---

## 📌 NOTES IMPORTANTES

1. **Temps réel** : Nécessite WebSocket actif
2. **Configuration** : Utilise CombatConfiguration pour valeurs
3. **Types de combat** : Supporte individuel et équipe
4. **Statut** : Contrôles uniquement si combat "en_cours"

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
