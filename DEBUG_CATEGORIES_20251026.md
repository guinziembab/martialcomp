# Debug - Catégories Non Affichées
**Date:** 26 Octobre 2025 - 19h00

## 🔍 Diagnostic

### Situation
- ✅ L'interface en 3 étapes fonctionne
- ✅ La sélection du type fonctionne
- ✅ Le bouton "Suivant" fonctionne
- ❌ Les catégories ne s'affichent pas à l'étape 2

### Hypothèses
1. **Type sans catégories** : Certains types (Quyen Synchronisé, Song Luyen) n'ont pas de catégories configurées
2. **Erreur API** : L'API ne retourne pas les données correctement
3. **Erreur JavaScript** : Le code ne traite pas la réponse correctement

## 🧪 Tests à Effectuer

### Test 1 : Vérifier la Console

**IMPORTANT : Videz le cache d'abord !**
```
Ctrl+Shift+Delete → Tout effacer → Fermer le navigateur → Rouvrir
```

1. Ouvrez F12 → Console
2. Allez sur la page d'inscription
3. Sélectionnez un type (ex: "Combats")
4. Cliquez sur "Suivant"

**Dans la console, vous devriez voir :**
```
🔍 Chargement des catégories pour le type: 118 "Combats"
📡 URL appelée: /fr/competitions/club/api/competition-types/118/categories/
📥 Réponse reçue: 200
📦 Données reçues: {success: true, categories: [...]}
✅ 18 catégorie(s) trouvée(s)
```

### Test 2 : Identifier le Type Sélectionné

Dans la console, tapez :
```javascript
console.log('Type sélectionné:', selectedTypeId, selectedTypeName);
```

**Résultat attendu :**
```
Type sélectionné: 118 "Combats"
```

### Test 3 : Tester l'API Directement

Dans la console, tapez (remplacez 118 par l'ID de votre type) :
```javascript
fetch('/fr/competitions/club/api/competition-types/118/categories/')
    .then(r => r.json())
    .then(d => console.log('API Response:', d));
```

**Résultat attendu :**
```javascript
API Response: {
    success: true,
    categories: [
        {id: 33, name: "JUNIORS A - FÉMININ", gender: "female", ...},
        {id: 34, name: "JUNIORS A - MASCULIN", gender: "male", ...},
        ...
    ]
}
```

## 📊 Données en Base

### Types avec Catégories
- ✅ **Combats** (ID: 118) → 18 catégories
- ✅ **Quyen Individuel** (ID: 115) → 32 catégories
- ❌ **Quyen Synchronisé** (ID: 116) → 0 catégories
- ❌ **Song Luyen** (ID: 117) → 0 catégories

### Si Vous Avez Sélectionné "Quyen Synchronisé" ou "Song Luyen"

**C'est NORMAL qu'aucune catégorie ne s'affiche !**

Ces types n'ont pas encore de catégories configurées. Vous devriez voir ce message :

```
⚠️ Aucune catégorie disponible

Le type de compétition "Quyen Synchronisé" n'a pas encore de catégories configurées.

[← Retour]
```

**Solution :** Cliquez sur "Retour" et sélectionnez "Combats" ou "Quyen Individuel".

## 🔧 Solutions selon le Problème

### Problème 1 : Aucun Message dans la Console

**Symptôme :** Pas de logs `🔍 Chargement des catégories...`

**Cause :** Le JavaScript ne s'exécute pas ou la fonction n'est pas appelée

**Solution :**
1. Videz le cache complètement
2. Vérifiez que vous voyez les logs initiaux :
   ```
   🚀 Script d'inscription chargé
   ✅ Variables initialisées
   ```
3. Si non, partagez-moi ce que vous voyez dans la console

### Problème 2 : Erreur 404 dans la Console

**Symptôme :** `📥 Réponse reçue: 404`

**Cause :** L'URL de l'API n'existe pas

**Solution :**
```bash
# Vérifier que l'URL est configurée
ssh martialcomp-production
grep -r "api_competition_type_categories" /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/
```

### Problème 3 : Erreur 500 dans la Console

**Symptôme :** `📥 Réponse reçue: 500`

**Cause :** Erreur dans la vue backend

**Solution :**
```bash
# Voir les logs Django
ssh martialcomp-production
tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
```

### Problème 4 : `success: false` dans la Réponse

**Symptôme :** `📦 Données reçues: {success: false, message: "..."}`

**Cause :** Erreur métier (type inexistant, etc.)

**Solution :** Vérifier le message d'erreur retourné

### Problème 5 : Catégories Vides

**Symptôme :** `⚠️ Aucune catégorie trouvée pour ce type`

**Cause :** Le type sélectionné n'a pas de catégories

**Solution :**
1. Cliquez sur "Retour"
2. Sélectionnez "Combats" ou "Quyen Individuel"
3. Ou configurez des catégories pour ce type dans l'admin

## 📸 Informations à Partager

Si le problème persiste, partagez-moi :

### 1. Messages de la Console
```
[Copiez TOUS les messages de la console ici]
```

### 2. Type Sélectionné
```javascript
// Résultat de cette commande :
console.log('Type:', selectedTypeId, selectedTypeName);
```

### 3. Réponse de l'API
```javascript
// Résultat de cette commande :
fetch('/fr/competitions/club/api/competition-types/' + selectedTypeId + '/categories/')
    .then(r => r.json())
    .then(d => console.log('API:', d));
```

### 4. Capture d'Écran
- La page à l'étape 2
- La console (F12)

## 🚀 Actions Immédiates

**MAINTENANT :**

1. ✅ **Videz le cache** (`Ctrl+Shift+Delete`)
2. ✅ **Fermez le navigateur**
3. ✅ **Rouvrez-le**
4. ✅ **Ouvrez F12** (Console)
5. ✅ **Allez sur la page**
6. ✅ **Sélectionnez "Combats"** (pas Quyen Synchronisé ou Song Luyen)
7. ✅ **Cliquez sur "Suivant"**
8. ✅ **Regardez la console**

**Partagez-moi :**
- Le type que vous avez sélectionné
- Les messages dans la console
- Ce que vous voyez à l'écran

---

**Template avec logs détaillés déployé !**  
**Tous les messages de debug s'afficheront dans la console.**

Si vous voyez `✅ X catégorie(s) trouvée(s)` mais qu'elles ne s'affichent pas, c'est un problème d'affichage HTML.  
Si vous voyez `⚠️ Aucune catégorie trouvée`, c'est que le type n'a pas de catégories.  
Si vous ne voyez aucun message, c'est que le JavaScript ne s'exécute pas.

**Dites-moi ce que vous voyez ! 🔍**
