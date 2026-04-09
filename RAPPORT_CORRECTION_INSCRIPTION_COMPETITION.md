# Rapport de Correction - Inscription aux Compétitions

**Date** : 12 novembre 2025
**Problème** : Le bouton "Suivant" ne fonctionnait pas sur la page d'inscription aux compétitions
**URL concernée** : https://martialcomp.com/en/competitions/club/competition-registration/4/
**Utilisateur affecté** : SN_admin

## Diagnostic

### Problème identifié
L'API endpoint `/competitions/{id}/api/categories/{type_id}/` appelé par le JavaScript n'existait pas, ce qui empêchait le chargement des catégories après la sélection d'un type de compétition.

### Analyse technique
1. Le template `competition_registration_simple.html` tentait d'appeler une API inexistante
2. Sans les catégories chargées, le formulaire ne pouvait pas progresser
3. Le bouton "Suivant" restait désactivé car les conditions de validation n'étaient pas remplies

## Solution appliquée

### 1. Création du fichier API
**Fichier** : `apps/competitions/views/club/registration_api.py`
- Fonction `get_categories_by_type_api` : Retourne les catégories pour un type de compétition
- Fonction `competition_registration_simple` : Gère l'inscription simplifiée via AJAX
- Fonction `unregister_practitioner` : Permet la désinscription d'une catégorie

### 2. Mise à jour des URLs
**Fichier** : `apps/competitions/urls/club.py`
- Import des nouvelles vues API
- Redirection de la route principale vers la vue simplifiée
- Ajout de la route de désinscription

**Fichier** : `apps/competitions/urls/competitions.py`
- Ajout de l'endpoint API : `<int:competition_id>/api/categories/<int:type_id>/`

## Déploiement

### Commandes exécutées
```bash
# Création et exécution du script de déploiement
./deploy_fix_registration_api_v2.sh

# Redémarrage du service
ssh root@martialcomp-production "systemctl restart martialcomp.service"
```

### Fichiers déployés
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/registration_api.py`
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/club.py`
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/competitions.py`

## Résultat

✅ **Déploiement réussi**
- Service MartialComp redémarré avec succès
- Aucune erreur dans les logs Gunicorn
- Les fichiers sont en place avec les bonnes permissions

## Test à effectuer

L'utilisateur SN_admin peut maintenant tester l'inscription :
1. Se connecter avec SN_admin / AQW123ok;
2. Aller sur https://martialcomp.com/en/competitions/club/competition-registration/4/
3. Sélectionner un type de compétition
4. Les catégories devraient maintenant se charger
5. Sélectionner une catégorie et des pratiquants
6. Le bouton "Inscrire" devrait être actif

## Points d'attention

1. L'API retourne maintenant le nombre d'inscrits par catégorie
2. La vue gère l'inscription multiple de pratiquants via AJAX
3. La désinscription est possible via l'onglet "Déjà inscrits"
4. L'âge des pratiquants est calculé automatiquement

## Recommandations

1. Surveiller les logs pour tout problème éventuel
2. Vérifier que tous les types de compétitions ont des catégories associées
3. S'assurer que les pratiquants ont des dates de naissance pour le calcul de l'âge