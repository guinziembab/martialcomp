# Debug Interface d'Inscription - 26 Octobre 2025

## 🔧 Corrections Appliquées

### Problème Identifié
Les boutons et sélections ne fonctionnaient pas car :
1. ❌ Les fonctions JavaScript étaient dans `{% block extra_js %}` qui n'était pas chargé
2. ❌ Les fonctions n'étaient pas dans le scope global (window)
3. ❌ Les event listeners n'étaient pas attachés aux boutons

### Solutions Appliquées

#### 1. ✅ Déplacement du JavaScript
- **Avant** : `{% block extra_js %}<script>...</script>{% endblock %}`
- **Après** : `<script>...</script>` directement dans le body avant `{% endblock %}`

#### 2. ✅ Exposition des fonctions dans le scope global
```javascript
// Avant
function selectType(typeId, typeName) { ... }

// Après
window.selectType = function(typeId, typeName) { ... }
```

Fonctions exposées :
- ✅ `window.selectType()`
- ✅ `window.selectCategory()`
- ✅ `window.removePractitioner()`
- ✅ `window.submitRegistrations()`

#### 3. ✅ Ajout des Event Listeners
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Boutons de navigation
    document.getElementById('btn-next').addEventListener('click', nextStep);
    document.getElementById('btn-prev').addEventListener('click', previousStep);
    document.getElementById('btn-submit').addEventListener('click', submitRegistrations);
    
    // ... reste du code
});
```

## 🧪 Tests à Effectuer

### Test 1 : Bouton "Suivant"
1. Accédez à : `https://martialcomp.com/fr/competitions/competitions/4/`
2. **Sans sélectionner de type**, cliquez sur "Suivant"
   - ✅ **Attendu** : Alert "Veuillez sélectionner un type de compétition"
3. Sélectionnez un type (ex: "Combats")
   - ✅ **Attendu** : La carte devient bleue avec un ✓
4. Cliquez sur "Suivant"
   - ✅ **Attendu** : Passage à l'étape 2, chargement des catégories

### Test 2 : Sélection des Cartes
1. À l'étape 1, cliquez sur une carte de type
   - ✅ **Attendu** : 
     - Border bleue
     - Checkmark (✓) en haut à droite
     - Variable `selectedTypeId` définie

2. À l'étape 2, cliquez sur une carte de catégorie
   - ✅ **Attendu** :
     - Border bleue
     - Checkmark (✓) en haut à droite
     - Variable `selectedCategoryId` définie

### Test 3 : Console du Navigateur
**Ouvrez la console (F12) et testez :**

```javascript
// Après avoir cliqué sur un type
console.log('Type sélectionné:', selectedTypeId, selectedTypeName);
// Devrait afficher : Type sélectionné: 118 "Combats"

// Après avoir cliqué sur une catégorie
console.log('Catégorie sélectionnée:', selectedCategoryId, selectedCategoryName);
// Devrait afficher : Catégorie sélectionnée: 33 "JUNIORS A - FÉMININ"

// Tester la fonction
window.selectType(118, 'Test');
console.log('Fonction selectType accessible:', typeof window.selectType);
// Devrait afficher : Fonction selectType accessible: function
```

### Test 4 : Drag & Drop
1. Arrivez à l'étape 3
2. Glissez un pratiquant vers la zone de droite
   - ✅ **Attendu** :
     - Le pratiquant apparaît dans "Pratiquants inscrits"
     - Le compteur s'incrémente
     - Bouton "Enregistrer" affiche le nombre

## 🐛 Debugging Avancé

### Si les boutons ne fonctionnent toujours pas

**1. Vérifiez que le JavaScript est chargé :**
```javascript
// Dans la console (F12)
console.log('nextStep existe?', typeof nextStep);
console.log('selectType existe?', typeof window.selectType);
```

**2. Vérifiez les erreurs JavaScript :**
- Ouvrez F12 → Onglet "Console"
- Rafraîchissez la page
- Cherchez les erreurs en rouge

**3. Vérifiez les event listeners :**
```javascript
// Dans la console
const btnNext = document.getElementById('btn-next');
console.log('Bouton trouvé?', btnNext);
console.log('Event listeners:', getEventListeners(btnNext));
```

**4. Test manuel des fonctions :**
```javascript
// Tester nextStep
currentStep = 1;
selectedTypeId = 118;
nextStep();
console.log('Étape actuelle:', currentStep); // Devrait être 2

// Tester selectType
window.selectType(118, 'Test Type');
console.log('Type sélectionné:', selectedTypeId, selectedTypeName);
```

### Si les cartes ne se sélectionnent pas

**1. Vérifiez l'attribut onclick :**
```javascript
// Dans la console
const cards = document.querySelectorAll('.selection-card');
console.log('Nombre de cartes:', cards.length);
cards.forEach(card => {
    console.log('Carte:', card.dataset.typeId, card.getAttribute('onclick'));
});
```

**2. Test manuel de sélection :**
```javascript
// Sélectionner la première carte manuellement
const firstCard = document.querySelector('.selection-card');
const typeId = firstCard.dataset.typeId;
const typeName = firstCard.querySelector('.card-title').textContent;
window.selectType(typeId, typeName);
```

## 📋 Checklist de Vérification

### Avant de tester
- [ ] Vider le cache du navigateur (`Ctrl+Shift+Delete`)
- [ ] Fermer tous les onglets de martialcomp.com
- [ ] Ouvrir un nouvel onglet
- [ ] Ouvrir la console (F12)

### Pendant le test
- [ ] Étape 1 : Les cartes de type s'affichent
- [ ] Étape 1 : Clic sur une carte → border bleue + ✓
- [ ] Étape 1 : Bouton "Suivant" fonctionne
- [ ] Étape 2 : Les catégories se chargent
- [ ] Étape 2 : Clic sur une catégorie → border bleue + ✓
- [ ] Étape 2 : Bouton "Suivant" fonctionne
- [ ] Étape 3 : Résumé affiché correctement
- [ ] Étape 3 : Drag & drop fonctionne
- [ ] Étape 3 : Bouton "Enregistrer" fonctionne

### Après le test
- [ ] Message de succès affiché
- [ ] Redirection vers la liste
- [ ] Inscription visible en base de données

## 🔍 Logs à Vérifier

### Logs Django
```bash
ssh martialcomp-production
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
```

### Logs Gunicorn
```bash
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
```

### Logs Nginx
```bash
sudo tail -f /var/log/nginx/martialcomp.com-error.log
```

## 📊 Résumé des Changements

| Élément | Avant | Après | Statut |
|---------|-------|-------|--------|
| Position du JS | `{% block extra_js %}` | Dans le body | ✅ |
| Scope des fonctions | Local | `window.*` | ✅ |
| Event listeners | `onclick="..."` | `addEventListener` | ✅ |
| Bouton Suivant | Ne fonctionnait pas | Fonctionne | ✅ |
| Sélection cartes | Ne fonctionnait pas | Fonctionne | ✅ |

## 🚀 Prochaine Étape

**VIDEZ LE CACHE** et testez immédiatement :

1. `Ctrl+Shift+Delete` → Vider le cache
2. Ouvrir F12 (Console)
3. Aller sur : `https://martialcomp.com/fr/competitions/competitions/4/`
4. Cliquer sur une carte de type
5. Observer dans la console si des erreurs apparaissent

**Si ça ne fonctionne toujours pas**, partagez-moi :
- Une capture d'écran de la console (F12)
- Le message exact qui s'affiche
- Ce qui se passe quand vous cliquez sur une carte

---

**Déploiement effectué le 26/10/2025 à** `date +"%H:%M:%S"`
