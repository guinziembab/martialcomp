# 🧪 GUIDE DE TEST - Dashboard Club v2.0.0

## 📋 CHECKLIST DE TEST EN DÉVELOPPEMENT

### 1. Préparation

- [x] Fichiers JavaScript en place (`static/js/dashboard/`)
- [x] Fichier CSS en place (`static/css/dashboard/`)
- [x] Template optimisé en place
- [x] Vues API ajoutées
- [x] URLs configurées
- [x] Aucune erreur système (`python3 manage.py check`)

### 2. Démarrage du serveur

```bash
cd /mnt/c/martial_hub_django/martialcomp
python3 manage.py runserver
```

### 3. Tests d'accès

#### 3.1 Accès au dashboard
- [ ] URL: `http://localhost:8000/dashboard/club/`
- [ ] Vérifier que la page se charge sans erreur 500
- [ ] Vérifier que l'utilisateur est bien connecté et a un club associé

#### 3.2 Vérification de la console navigateur (F12)
- [ ] Aucune erreur JavaScript dans la console
- [ ] Message: `🚀 Initialisation Dashboard Club v2.0.0`
- [ ] Message: `✅ Dashboard Club v2.0.0 initialisé avec succès`
- [ ] Vérifier que les modules sont chargés:
  ```javascript
  console.log(ClubDashboard);  // Doit afficher un objet
  console.log(BulkRegistration);  // Doit afficher un objet
  console.log(CSVImport);  // Doit afficher un objet
  ```

#### 3.3 Vérification des fichiers static
- [ ] Ouvrir l'onglet Network (F12)
- [ ] Recharger la page
- [ ] Vérifier que ces fichiers sont chargés avec statut 200:
  - `static/css/dashboard/club_dashboard.css`
  - `static/js/dashboard/club_dashboard_core.js`
  - `static/js/dashboard/club_dashboard_bulk.js`
  - `static/js/dashboard/club_dashboard_import.js`

### 4. Tests de navigation

#### 4.1 Navigation par onglets
- [ ] Cliquer sur "Vue d'ensemble" → L'onglet s'active
- [ ] Cliquer sur "Pratiquants" → L'onglet s'active
- [ ] Cliquer sur "Compétitions" → L'onglet s'active
- [ ] Cliquer sur "Finances" → L'onglet s'active
- [ ] Cliquer sur "Entraînement" → L'onglet s'active
- [ ] Cliquer sur "Événements" → L'onglet s'active
- [ ] Cliquer sur "Boutique" → L'onglet s'active
- [ ] Cliquer sur "Rôles" → L'onglet s'active

#### 4.2 Persistance de l'onglet
- [ ] Sélectionner un onglet (ex: "Pratiquants")
- [ ] Recharger la page (F5)
- [ ] Vérifier que l'onglet "Pratiquants" reste sélectionné

### 5. Tests fonctionnels - Onglet Pratiquants

#### 5.1 Affichage des pratiquants
- [ ] Vérifier que la liste des pratiquants s'affiche
- [ ] Vérifier que les colonnes sont présentes: Nom, Âge, Grade, Statut, Actions
- [ ] Vérifier que les âges sont calculés automatiquement

#### 5.2 Checkbox "Tout sélectionner"
- [ ] Cocher la checkbox "Tout sélectionner" (en-tête du tableau)
- [ ] Vérifier que toutes les checkboxes des pratiquants sont cochées
- [ ] Décocher "Tout sélectionner"
- [ ] Vérifier que toutes les checkboxes sont décochées

#### 5.3 Sélection individuelle
- [ ] Cocher quelques checkboxes de pratiquants individuellement
- [ ] Vérifier que le compteur de sélection s'affiche correctement

#### 5.4 Bouton "Import CSV"
- [ ] Cliquer sur le bouton "Import CSV" (ID: `import-csv-btn`)
- [ ] Vérifier que le modal s'ouvre
- [ ] Vérifier que le formulaire d'upload est présent
- [ ] Tester l'upload d'un fichier CSV valide
- [ ] Tester l'upload d'un fichier non-CSV (doit être refusé)

#### 5.5 Bouton "Inscription en masse"
- [ ] Sélectionner au moins un pratiquant
- [ ] Cliquer sur le bouton "Inscription en masse" (ID: `bulk-registration-btn`)
- [ ] Vérifier que le modal s'ouvre
- [ ] Vérifier que les pratiquants sélectionnés sont listés
- [ ] Vérifier que la liste des compétitions se charge
- [ ] Sélectionner une compétition
- [ ] Valider l'inscription
- [ ] Vérifier le message de succès

#### 5.6 Actions sur les pratiquants
- [ ] Cliquer sur "Supprimer" pour un pratiquant
- [ ] Vérifier la confirmation
- [ ] Confirmer la suppression
- [ ] Vérifier que le pratiquant est supprimé de la liste

- [ ] Cliquer sur "Activer/Désactiver" pour un pratiquant
- [ ] Vérifier que le statut change
- [ ] Vérifier que l'icône change (actif/inactif)

### 6. Tests fonctionnels - Onglet Compétitions

#### 6.1 Affichage des compétitions
- [ ] Vérifier que la liste des compétitions s'affiche
- [ ] Vérifier les colonnes: Nom, Date, Lieu, Inscrits, Statut, Actions
- [ ] Vérifier que les compétitions utilisent `title` (pas `name`)
- [ ] Vérifier que le lieu utilise `venue_name` ou `city`

#### 6.2 Actions sur les compétitions
- [ ] Cliquer sur "Voir" (icône œil)
- [ ] Vérifier que la page de détail s'ouvre
- [ ] Retourner au dashboard
- [ ] Cliquer sur "Modifier" (icône crayon)
- [ ] Vérifier que la page d'édition s'ouvre

### 7. Tests fonctionnels - Onglet Vue d'ensemble

#### 7.1 Statistiques
- [ ] Vérifier que les cartes statistiques s'affichent:
  - Nombre de pratiquants
  - Compétitions organisées
  - Inscriptions actives
  - Juges/Arbitres

#### 7.2 Compétitions à venir
- [ ] Vérifier que les compétitions à venir s'affichent
- [ ] Vérifier que le bouton "S'inscrire" est présent
- [ ] Cliquer sur "S'inscrire"
- [ ] Vérifier que le formulaire d'inscription s'ouvre

### 8. Tests API

#### 8.1 API Compétitions disponibles
- [ ] Ouvrir la console navigateur (F12)
- [ ] Exécuter:
  ```javascript
  fetch('/club/available-competitions/api/', {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    },
    credentials: 'include'
  })
  .then(r => r.json())
  .then(console.log);
  ```
- [ ] Vérifier que la réponse JSON contient `success: true` et un tableau `competitions`

#### 8.2 API Inscription en masse
- [ ] Sélectionner des pratiquants
- [ ] Ouvrir le modal d'inscription en masse
- [ ] Sélectionner une compétition
- [ ] Valider
- [ ] Vérifier dans la console Network que la requête POST est envoyée à `/club/bulk-registration/process/`
- [ ] Vérifier que la réponse JSON contient `success: true`

### 9. Tests de responsive

#### 9.1 Mobile
- [ ] Ouvrir les outils de développement (F12)
- [ ] Activer le mode responsive (Ctrl+Shift+M)
- [ ] Tester sur différentes tailles d'écran (320px, 768px, 1024px)
- [ ] Vérifier que les onglets restent accessibles
- [ ] Vérifier que les tableaux sont scrollables horizontalement

### 10. Tests d'encodage

#### 10.1 Caractères spéciaux
- [ ] Vérifier qu'il n'y a pas de caractères bizarres (Ã©, Ã , etc.)
- [ ] Vérifier que les accents s'affichent correctement (é, è, à, etc.)

### 11. Tests de performance

#### 11.1 Temps de chargement
- [ ] Ouvrir l'onglet Network (F12)
- [ ] Recharger la page
- [ ] Vérifier que le temps de chargement total est < 2 secondes
- [ ] Vérifier que les fichiers JavaScript/CSS sont mis en cache

---

## 🐛 DÉPANNAGE

### Problème: Erreur 404 sur les fichiers JS/CSS

**Solution:**
```bash
cd /mnt/c/martial_hub_django/martialcomp
python3 manage.py collectstatic --noinput
```

### Problème: Erreur JavaScript "ClubDashboard is not defined"

**Vérifications:**
1. Ouvrir l'onglet Network et vérifier que `club_dashboard_core.js` est chargé
2. Vérifier la console pour les erreurs de syntaxe
3. Vérifier que le script est chargé avant l'initialisation

### Problème: Les boutons ne répondent pas

**Vérifications:**
1. Vérifier que les IDs sont corrects:
   - `import-csv-btn` (avec tirets, pas camelCase)
   - `bulk-registration-btn` (avec tirets)
2. Vérifier la console pour les erreurs JavaScript
3. Vérifier que Bootstrap 5 est chargé

### Problème: Modal ne s'ouvre pas

**Vérifications:**
1. Vérifier que Bootstrap 5 est chargé
2. Vérifier que les attributs `data-bs-toggle` et `data-bs-target` sont présents
3. Vérifier la console pour les erreurs JavaScript

---

## ✅ VALIDATION FINALE

Une fois tous les tests passés:

- [ ] Tous les tests fonctionnels passent
- [ ] Aucune erreur dans la console
- [ ] Performance acceptable
- [ ] Responsive fonctionne
- [ ] Encodage correct

**Le dashboard est prêt pour le déploiement en production ! 🚀**
