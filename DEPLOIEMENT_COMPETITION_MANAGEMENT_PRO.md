# Déploiement des corrections Competition Management Pro

## Date : 12 novembre 2024

## Résumé des corrections

### 1. Corrections JavaScript - Traductions Django
**Problème** : Erreurs de syntaxe JavaScript causées par l'utilisation directe de `{% trans %}` dans le code JavaScript.

**Solution** :
- Création d'un objet `messages` contenant toutes les traductions
- Utilisation du filtre `escapejs` pour échapper les caractères spéciaux
- Remplacement de toutes les utilisations directes de `{% trans %}` dans le JavaScript par des références à l'objet `messages`
- Ajout de 20+ messages traduits manquants

**Fichiers modifiés** :
- `apps/competitions/templates/competitions/club/competition_management_pro.html`

### 2. Correction du bouton "Ajouter un arbitre"
**Problème** : Le bouton ciblait un modal `#refereeModal` qui n'existait pas.

**Solution** :
- Création du modal `#refereeModal` manquant
- Ajout de la fonction `initRefereeForm()` pour initialiser le formulaire d'arbitre
- Correction de l'utilisation de `Modal.getInstance()` pour gérer les cas où l'instance n'existe pas
- Amélioration de l'accessibilité des modals (attributs `aria-labelledby`, `aria-hidden`)

**Fichiers modifiés** :
- `apps/competitions/templates/competitions/club/competition_management_pro.html`

### 3. Correction des boutons "Actions rapides"
**Problème** : Les boutons "Publier" et "Partager" ne fonctionnaient pas à cause d'URLs incorrectes.

**Solution** :
- Correction des URLs API :
  - `publishCompetition` : `/pro/publish/` → `/publish/`
  - `addType` : `/pro/add-type/` → `/types/`
- Création de la fonction `shareCompetition()` manquante
- Création du modal `#shareModal` pour le partage
- Amélioration de la gestion des erreurs HTTP dans `publishCompetition()`
- Amélioration de `copyShareLink()` avec support mobile

**Fichiers modifiés** :
- `apps/competitions/templates/competitions/club/competition_management_pro.html`

### 4. Ajout de la fonction delete_competition_type
**Problème** : La fonction `deleteType()` dans le template appelait une route qui n'existait pas.

**Solution** :
- Ajout de la fonction `delete_competition_type()` dans `competition_management_pro.py`
- Ajout de la route `/api/competitions/<int:competition_id>/pro/delete-type/<int:type_id>/` dans `urls/club.py`

**Fichiers modifiés** :
- `apps/competitions/views/competition_management_pro.py`
- `apps/competitions/urls/club.py`

## Fichiers à déployer

1. `apps/competitions/templates/competitions/club/competition_management_pro.html`
   - Corrections JavaScript
   - Ajout des modals `refereeModal` et `shareModal`
   - Correction des URLs API
   - Ajout des fonctions manquantes

2. `apps/competitions/views/competition_management_pro.py`
   - Ajout de la fonction `delete_competition_type()`

3. `apps/competitions/urls/club.py`
   - Ajout de la route pour `delete_competition_type`
   - Import de la fonction `delete_competition_type`

## Instructions de déploiement

### Méthode 1 : Script automatique

```bash
cd /mnt/c/martial_hub_django/martialcomp
./deploy_competition_management_pro.sh
```

### Méthode 2 : Déploiement manuel

Si la connexion SSH échoue, exécutez manuellement :

```bash
# 1. Copier les fichiers
scp apps/competitions/templates/competitions/club/competition_management_pro.html \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/

scp apps/competitions/views/competition_management_pro.py \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/

scp apps/competitions/urls/club.py \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/

# 2. Redémarrer Gunicorn
ssh pierrep99@martialcomp.com "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo systemctl reload gunicorn"
```

## Vérifications post-déploiement

1. **Vérifier que la page se charge sans erreurs JavaScript** :
   - Ouvrir la console du navigateur (F12)
   - Aller sur : `https://martialcomp.com/fr/competitions/club/competitions/[ID]/manage/pro/`
   - Vérifier qu'il n'y a pas d'erreurs dans la console

2. **Tester les fonctionnalités** :
   - ✅ Bouton "Ajouter un arbitre" : doit ouvrir le modal `refereeModal`
   - ✅ Bouton "Publier la compétition" : doit publier la compétition
   - ✅ Bouton "Partager" : doit ouvrir le modal `shareModal`
   - ✅ Bouton "Supprimer" sur un type de compétition : doit supprimer le type
   - ✅ Boutons "Editer" et "Supprimer" sur les catégories : doivent fonctionner sans erreur JavaScript

3. **Vider le cache du navigateur** :
   - Appuyer sur `Ctrl+F5` (Windows/Linux) ou `Cmd+Shift+R` (Mac)
   - Ou vider le cache manuellement dans les paramètres du navigateur

## Notes importantes

- **Cache navigateur** : Il est essentiel de vider le cache du navigateur après le déploiement pour charger la nouvelle version du JavaScript.
- **Erreurs JavaScript** : Si des erreurs persistent, vérifier que tous les messages sont bien définis dans l'objet `messages` du template.
- **URLs API** : Toutes les URLs API ont été vérifiées et correspondent aux routes définies dans `urls/club.py`.

## Rollback

En cas de problème, restaurer les fichiers depuis le backup :

```bash
# Sur le serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs
git checkout HEAD -- apps/competitions/templates/competitions/club/competition_management_pro.html
git checkout HEAD -- apps/competitions/views/competition_management_pro.py
git checkout HEAD -- apps/competitions/urls/club.py
sudo systemctl reload gunicorn
```

## Support

En cas de problème, vérifier :
1. Les logs Gunicorn : `sudo journalctl -u gunicorn -n 50`
2. Les logs Django : `tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/*.log`
3. La console du navigateur pour les erreurs JavaScript
