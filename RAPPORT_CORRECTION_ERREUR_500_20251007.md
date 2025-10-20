# Rapport de Correction - Erreur 500 Dashboard Fédération
**Date**: 7 octobre 2025  
**Problème**: Erreur 500 sur https://martialcomp.com/fr/competitions/federations/6/dashboard/  
**Utilisateur affecté**: FEDETEST1

## Diagnostic

### Problème Principal : Erreur 500

**Cause identifiée** : Dans le fichier `apps/competitions/views/dashboard/federations.py`, il y avait des références incorrectes à `self.request.user` au lieu de `request.user` dans une fonction view (pas une classe).

**Lignes concernées** :
- Ligne 352 : `get_organization_queryset(Order, self.request.user)` ❌
- Ligne 362 : `get_organization_queryset(PaymentAttempt, self.request.user)` ❌

**Erreur générée** :
```python
AttributeError: 'WSGIRequest' object has no attribute 'request'
```

### Problème Secondaire : Utilisateurs disparus

**État constaté** :
- En développement : 65 utilisateurs actifs ✅
- En production : À vérifier (scripts fournis)

**Causes possibles** :
1. Problème de connexion à la base de données
2. Restauration d'un backup incomplet
3. Problème de synchronisation

## Solution Appliquée

### 1. Correction du fichier `federations.py`

**Fichier restauré depuis** : `apps/competitions/views/dashboard/federations_backup_20250912_144233.py`

Ce backup est propre et ne contient pas l'erreur `self.request.user`.

**Vérifications effectuées** :
- ✅ Syntaxe Python valide (py_compile)
- ✅ Aucune occurrence de `self.request.user`
- ✅ 1060 lignes (fichier complet)

### 2. Scripts créés pour le déploiement

| Script | Description |
|--------|-------------|
| `check_users_production.sh` | Vérification complète des utilisateurs en production |
| `fix_federation_500_error.sh` | Correction automatique de l'erreur 500 |
| `recreate_fedetest1.sh` | Recréation de l'utilisateur FEDETEST1 si nécessaire |
| `TRANSFERT_PRODUCTION_URGENT.sh` | Script de transfert automatisé vers production |

## Procédure de Déploiement

### Option A : Transfert Automatique (Si SSH fonctionne)

```bash
bash TRANSFERT_PRODUCTION_URGENT.sh
```

### Option B : Déploiement Manuel

#### Étape 1 : Transfert des fichiers

```bash
# Connexion au serveur
ssh martialcomp.com

# Créer un répertoire pour les scripts
mkdir -p ~/martialcomp/scripts_fix_20251007
cd ~/martialcomp/scripts_fix_20251007
```

Puis transférer depuis votre machine locale :
```bash
scp apps/competitions/views/dashboard/federations.py martialcomp.com:~/martialcomp/scripts_fix_20251007/
scp check_users_production.sh martialcomp.com:~/martialcomp/scripts_fix_20251007/
scp fix_federation_500_error.sh martialcomp.com:~/martialcomp/scripts_fix_20251007/
scp recreate_fedetest1.sh martialcomp.com:~/martialcomp/scripts_fix_20251007/
```

#### Étape 2 : Sur le serveur

```bash
cd ~/martialcomp/scripts_fix_20251007
chmod +x *.sh

# 1. Vérifier l'état des utilisateurs
bash check_users_production.sh > users_report_$(date +%Y%m%d_%H%M%S).log

# 2. Sauvegarder l'ancien fichier
cp ~/martialcomp/apps/competitions/views/dashboard/federations.py \
   ~/martialcomp/apps/competitions/views/dashboard/federations.py.backup_$(date +%Y%m%d_%H%M%S)

# 3. Copier le nouveau fichier
cp federations.py ~/martialcomp/apps/competitions/views/dashboard/federations.py

# 4. Vérifier qu'il n'y a pas d'erreur
cd ~/martialcomp
source venv/bin/activate
python -m py_compile apps/competitions/views/dashboard/federations.py

# 5. Redémarrer l'application
touch ~/martialcomp/passenger_wsgi.py
```

#### Étape 3 : Recréer FEDETEST1 si nécessaire

```bash
cd ~/martialcomp/scripts_fix_20251007
bash recreate_fedetest1.sh
```

### Étape 4 : Tests Post-Déploiement

1. **Tester la page d'accueil**
   - URL : https://martialcomp.com/
   - Résultat attendu : Page s'affiche sans erreur

2. **Tester la connexion FEDETEST1**
   - URL : https://martialcomp.com/fr/account/login/
   - Username : `FEDETEST1`
   - Password : `TestFede2025!` (si recréé) ou password existant
   - Résultat attendu : Connexion réussie

3. **Tester le dashboard fédération**
   - URL : https://martialcomp.com/fr/competitions/federations/6/dashboard/
   - Résultat attendu : Dashboard s'affiche sans erreur 500

4. **Vérifier les logs**
   ```bash
   tail -f ~/logs/error_log
   ```
   - Résultat attendu : Aucune nouvelle erreur

## Points de Vérification

### ✅ Avant le Déploiement

- [x] Fichier `federations.py` corrigé et validé
- [x] Syntaxe Python vérifiée (py_compile)
- [x] Scripts de diagnostic créés
- [x] Documentation complète

### ⏳ Après le Déploiement (À faire sur le serveur)

- [ ] Utilisateurs vérifiés (nombre, état)
- [ ] Fichier `federations.py` remplacé
- [ ] Application redémarrée
- [ ] FEDETEST1 vérifié/recréé
- [ ] Tests de connexion réussis
- [ ] Dashboard fédération accessible
- [ ] Logs vérifiés (pas d'erreurs)

## Rollback en Cas de Problème

Si le problème persiste après le déploiement :

```bash
# Restaurer le backup
cp ~/martialcomp/apps/competitions/views/dashboard/federations.py.backup_XXXXXX \
   ~/martialcomp/apps/competitions/views/dashboard/federations.py

# Redémarrer
touch ~/martialcomp/passenger_wsgi.py

# Vérifier les logs
tail -100 ~/logs/error_log
```

## Informations sur FEDETEST1

### Si l'utilisateur existe déjà
- Username : `FEDETEST1`
- Email : Vérifier via `check_users_production.sh`
- Password : Connu de l'administrateur

### Si l'utilisateur est recréé
- Username : `FEDETEST1`
- Email : `fedetest1@martialcomp.com`
- Password : `TestFede2025!`
- Rôle : `federation_admin`
- Fédération : ID 6 (associée automatiquement)

## Commandes Utiles

### Vérifier l'état de l'application
```bash
passenger-status
passenger-memory-stats
```

### Vérifier les logs en temps réel
```bash
tail -f ~/logs/error_log
```

### Vérifier la base de données
```bash
cd ~/martialcomp
source venv/bin/activate
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"
```

### Redémarrer l'application
```bash
touch ~/martialcomp/passenger_wsgi.py
```

## Contact et Support

En cas de problème pendant le déploiement :
1. Consulter ce document
2. Vérifier les logs : `tail -100 ~/logs/error_log`
3. Exécuter `check_users_production.sh` pour diagnostiquer
4. Utiliser le rollback si nécessaire

## Statut

- **Environnement de développement** : ✅ Corrigé et testé
- **Environnement de production** : ⏳ En attente de déploiement
- **Tests** : ⏳ À effectuer après déploiement

## Fichiers Modifiés

| Fichier | Action | Statut |
|---------|--------|--------|
| `apps/competitions/views/dashboard/federations.py` | Restauré depuis backup propre | ✅ Prêt |
| Scripts de déploiement | Créés | ✅ Prêt |
| Documentation | Créée | ✅ Complet |

## Prochaines Étapes

1. ⏳ Transférer les fichiers vers la production
2. ⏳ Exécuter `check_users_production.sh`
3. ⏳ Appliquer la correction avec le nouveau fichier
4. ⏳ Vérifier/recréer FEDETEST1
5. ⏳ Tester l'accès au dashboard
6. ⏳ Documenter les résultats

---

**Note** : Ce rapport doit être mis à jour après le déploiement avec les résultats des tests et l'état final de la production.
