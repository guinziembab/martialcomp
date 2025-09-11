# 🚫 Erreur 404 sur MartialComp : Diagnostic et Résolution

## 1. **Contexte de l'erreur**

Après le transfert du projet Django en production (IONOS/Plesk/Debian), plusieurs utilisateurs ont rencontré des erreurs 404 lors de l'accès à certaines URLs, notamment `/competitions/dashboard/` et `/dashboard/`.

---

## 2. **Symptômes observés**

- Accès à `/competitions/dashboard/` ou `/dashboard/` renvoie une page 404.
- Redirections après login ou certaines actions aboutissent sur une page non trouvée.
- Les autres pages principales (accueil, login, etc.) fonctionnent.

---

## 3. **Diagnostic détaillé**

### a) **Problème de traduction dynamique des URLs**

- Dans `competitions/urls.py`, l'URL du dashboard était définie ainsi :

  ```python
  path(_('dashboard/'), pages.dashboard, name='dashboard'),
  ```

  Cela rendait l'URL dépendante de la langue (ex : `/tableau-de-bord/` en français, `/dashboard/` en anglais), alors que les redirections et liens utilisaient `/dashboard/` en dur.

- Conséquence :
  - En français, `/dashboard/` n'existait pas (URL traduite), d'où l'erreur 404.
  - Les redirections Django (LOGIN_REDIRECT_URL, reverse, etc.) pointaient vers une URL non résolue.

### b) **Problèmes de namespaces et d'inclusion d'URLs**

- Les inclusions d'URLs dans `competitions/urls.py` et `config/urls.py` n'étaient pas toujours cohérentes (manque de namespace, mauvaise imbrication).
- Certaines redirections utilisaient des noms de routes qui n'existaient plus après refonte.

### c) **Absence de handler404 personnalisé**

- Le handler404 Django n'était pas activé ou pointait vers une vue inexistante (`competitions.views.pages.custom_404`).
- Les erreurs 404 affichaient donc la page par défaut Django ou une page blanche.

---

## 4. **Commandes de diagnostic utilisées**

- Recherche des occurrences de `/competitions/dashboard/` dans le code :
  ```bash
  grep -r "/competitions/dashboard/" . --include="*.py"
  ```
- Vérification de la traduction de l'URL :
  ```python
  from django.utils.translation import gettext as _
  print(_("dashboard/"))
  ```
- Test de résolution d'URL :
  ```python
  from django.urls import reverse
  reverse('competitions:dashboard')
  ```

---

## 5. **Solutions appliquées**

### a) **Correction des URLs**

- Suppression de la traduction dynamique dans `competitions/urls.py` :
  ```python
  # AVANT (problématique)
  path(_('dashboard/'), pages.dashboard, name='dashboard'),
  # APRÈS (corrigé)
  path('dashboard/', pages.dashboard, name='dashboard'),
  ```
- Vérification de la cohérence des namespaces et des inclusions d'URLs.

### b) **Redirections et reverse**

- Mise à jour des redirections après login (`LOGIN_REDIRECT_URL`) pour pointer vers la bonne route.
- Utilisation systématique de `reverse('competitions:dashboard')` au lieu de chaînes statiques.

### c) **Handler 404 personnalisé**

- Ajout d'un handler404 dans `config/urls.py` :
  ```python
  handler404 = 'competitions.views.pages.custom_404'
  ```
- Création d'une vue et d'un template personnalisés pour les erreurs 404.

---

## 6. **Résultat**

- Les accès au dashboard et aux autres pages protégées fonctionnent désormais dans toutes les langues.
- Les erreurs 404 affichent une page personnalisée et claire.
- Les redirections après login et actions sensibles sont correctes.

---

## 7. **Conseils pour l'avenir**

- Ne jamais traduire dynamiquement les segments d'URL critiques (dashboard, login, etc.).
- Toujours utiliser les namespaces et `reverse()` pour les redirections.
- Tester la résolution des URLs dans chaque langue après modification.
- Mettre en place des handlers d'erreur personnalisés pour une meilleure UX.
