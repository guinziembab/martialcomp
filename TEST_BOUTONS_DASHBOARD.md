# Instructions de Test - Boutons Dashboard Club
**Date : 08/11/2025 23:42**

## ✅ Corrections Appliquées

1. **Vue `practitioner_delete`** - Modifiée pour retourner du JSON
2. **Event listeners ajoutés** - Code JavaScript pour gérer les clics sur les boutons
3. **Fonction `showAlert`** - Pour afficher les messages de succès/erreur

## 🔄 Étapes de Test

### 1. Arrêter et redémarrer le serveur Django
```bash
# Arrêter avec Ctrl+C puis :
python manage.py runserver 8888
```

### 2. Vider le cache du navigateur
- **Chrome/Edge** : Ctrl + Shift + R
- **Firefox** : Ctrl + Shift + R  
- **Ou** : Ouvrir en navigation privée/incognito

### 3. Accéder au dashboard
1. Aller sur : http://127.0.0.1:8888/fr/competitions/dashboard/club/
2. Cliquer sur l'onglet **"Pratiquants"**
3. Ouvrir la console du navigateur (F12) pour voir les logs

### 4. Vérifier dans la console
Vous devriez voir :
```
🔧 Initialisation des corrections de boutons...
✓ Bouton Import CSV trouvé
✓ Bouton Inscription en masse trouvé
✅ Event listeners des boutons pratiquants initialisés
```

### 5. Tester chaque bouton

#### 🗑️ Bouton Supprimer (rouge)
1. Cliquer sur le bouton poubelle rouge
2. Une boîte de dialogue devrait demander confirmation
3. Confirmer la suppression
4. Le pratiquant devrait disparaître avec un effet de fondu
5. Un message de succès devrait apparaître en haut de la page

#### ⚡ Bouton Toggle Status (vert/orange)
1. Cliquer sur le bouton toggle
   - Vert (actif) → devient orange (inactif)
   - Orange (inactif) → devient vert (actif)
2. Le badge de statut dans la colonne devrait changer
3. Un message de succès devrait apparaître

#### 📄 Bouton Import CSV
1. Cliquer sur "Import CSV" dans la barre d'outils
2. Devrait rediriger vers `/fr/competitions/club/import-export/`

#### 🏆 Bouton Inscription en masse
1. Cocher la case à côté d'un ou plusieurs pratiquants
2. Le bouton "Inscription en masse" devrait indiquer le nombre sélectionné
3. Cliquer sur le bouton
4. Un modal devrait s'ouvrir pour choisir une compétition

## 🐛 Débogage

### Si les boutons ne fonctionnent toujours pas :

1. **Vérifier la console pour les erreurs JavaScript**
   - Chercher des erreurs comme "getCookie is not defined"
   - Chercher des erreurs 404 ou 500

2. **Vérifier l'onglet Network (Réseau)**
   - Cliquer sur un bouton
   - Voir si une requête est envoyée
   - Vérifier le statut de la réponse

3. **Tester avec une URL directe**
   Dans la console du navigateur, taper :
   ```javascript
   // Tester si getCookie existe
   console.log(typeof getCookie);
   
   // Tester si les boutons sont trouvés
   console.log(document.querySelectorAll('.delete-practitioner-btn').length);
   console.log(document.querySelectorAll('.toggle-status-btn').length);
   ```

4. **Vérifier que les attributs data sont présents**
   Dans la console :
   ```javascript
   // Pour un bouton de suppression
   const delBtn = document.querySelector('.delete-practitioner-btn');
   console.log(delBtn.getAttribute('data-practitioner-id'));
   console.log(delBtn.getAttribute('data-practitioner-name'));
   ```

## 📝 Logs à Vérifier

Dans le terminal Django, vous devriez voir :
- Pour suppression : une requête POST vers `/fr/competitions/club/practitioners/XX/delete/`
- Pour toggle : une requête POST vers `/fr/competitions/club/practitioners/XX/toggle-status/`

## 🔧 En Cas de Problème Persistant

1. **Restaurer la sauvegarde**
   ```bash
   cp apps/competitions/templates/competitions/dashboard/club.html.backup_event_20251108_234105 apps/competitions/templates/competitions/dashboard/club.html
   ```

2. **Vérifier manuellement le template**
   Ouvrir le fichier et chercher :
   - La fonction `getCookie`
   - Les event listeners pour `.delete-practitioner-btn`
   - Les event listeners pour `.toggle-status-btn`

3. **Forcer le rechargement complet**
   - Arrêter Django
   - Supprimer le cache Python : `find . -type d -name __pycache__ -exec rm -rf {} +`
   - Redémarrer Django

---
**Note** : Les sauvegardes de tous les fichiers modifiés ont été créées et peuvent être restaurées si nécessaire.