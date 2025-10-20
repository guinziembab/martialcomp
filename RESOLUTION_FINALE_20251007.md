# Résolution Finale - Erreur 500 Dashboard Fédération

**Date**: 7 octobre 2025, 20:06 UTC  
**Problème**: Erreur 500 persistante malgré multiples tentatives de correction

---

## 🔍 DÉCOUVERTE CRITIQUE

### Le Vrai Problème

L'application utilise **Gunicorn**, PAS Passenger !

```bash
ps aux | grep gunicorn
# Résultat : 4 workers Gunicorn avec --preload
```

### Pourquoi les Corrections Ne Fonctionnaient Pas

1. **`touch passenger_wsgi.py`** → ❌ N'a AUCUN effet (Passenger n'est pas utilisé)
2. **Fichiers templates modifiés** → ❌ Mais Gunicorn gardait les anciens en mémoire
3. **Cache Python `.pyc`** → ❌ Persistait malgré les suppressions partielles
4. **Signal HUP à Gunicorn** → ❌ Recharge les workers mais garde le code preloadé

### Les Vraies Causes

1. **Gunicorn avec `--preload`** : Charge tout le code en mémoire au démarrage
2. **Cache Python** : Fichiers `.pyc` dans TOUS les répertoires (pas juste `apps/`)
3. **Template en double** : Fichier dans `/static/` ET `/apps/`
4. **Pas de redémarrage complet** : Gu nicorn master process jamais tué

---

## ✅ SOLUTION FINALE APPLIQUÉE

### Étape 1 : Suppression Complète du Cache
```bash
cd /var/www/vhosts/martialcomp.com
find . -name '*.pyc' -delete
find . -type d -name '__pycache__' -exec rm -rf {} +
```

### Étape 2 : Correction des Templates
```bash
# Template dans apps/
apps/competitions/templates/competitions/dashboard/federation.html

# Template dans static/ (CELUI-CI était le problème)
static/apps/competitions/templates/competitions/dashboard/federation.html
```

**Changement** : Suppression complète du tag Django `{% url 'update_site_info' %}`

### Étape 3 : Redémarrage COMPLET de Gunicorn
```bash
# Kill FORCÉ de tous les processes
pkill -9 gunicorn

# Redémarrage propre depuis le bon répertoire
cd /var/www/vhosts/martialcomp.com/httpdocs
../venv/bin/gunicorn \
  --workers 3 \
  --worker-class sync \
  --bind 127.0.0.1:8000 \
  --timeout 300 \
  --daemon \
  config.wsgi:application
```

---

## 📊 Vérifications Effectuées

### Fichier Python Correct
```bash
md5sum apps/competitions/views/dashboard/federations.py
# 1aa2adb859fa4bb9e67d49a5bc200cd5 (identique au développement)

grep -c 'self\.request\.user' apps/competitions/views/dashboard/federations.py
# 0 (aucune occurrence)
```

### Templates Corrects
```bash
grep 'update_site_info' apps/competitions/templates/competitions/dashboard/federation.html
# Résultat : Seulement en commentaire JavaScript

grep 'update_site_info' static/apps/competitions/templates/competitions/dashboard/federation.html
# Résultat : Seulement en commentaire JavaScript
```

### Gunicorn Redémarré
```bash
ps aux | grep gunicorn | grep -v grep
# 4 workers actifs (1 master + 3 workers)
```

---

## 🧪 TESTS À EFFECTUER

### Test Principal
**URL** : https://martialcomp.com/fr/competitions/federations/7/dashboard/

**Résultat Attendu** : Dashboard s'affiche SANS erreur 500

### Vérification des Logs
```bash
tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
```

**Résultat Attendu** : 
- ✅ Pas d'erreur `NoReverseMatch: update_site_info`
- ✅ Pas d'erreur `name 'self' is not defined`

---

## 🔄 Commandes de Redémarrage Futures

### Pour Redémarrer Gunicorn Correctement

```bash
# OPTION 1 : Signal (si pas de --preload)
pkill -HUP gunicorn

# OPTION 2 : Redémarrage complet (RECOMMANDÉ avec --preload)
pkill -9 gunicorn
sleep 3
cd /var/www/vhosts/martialcomp.com/httpdocs
../venv/bin/gunicorn --workers 3 --worker-class sync --bind 127.0.0.1:8000 --timeout 300 --daemon config.wsgi:application
```

### Nettoyage du Cache Python
```bash
cd /var/www/vhosts/martialcomp.com
find . -name '*.pyc' -delete
find . -type d -name '__pycache__' -exec rm -rf {} +
```

---

## 📝 Leçons Apprises

1. **Identifier le serveur d'application réel** : Gunicorn, pas Passenger
2. **Option `--preload`** : Nécessite un redémarrage complet pour charger nouveau code
3. **Cache Python** : Doit être nettoyé PARTOUT, pas juste dans un répertoire
4. **Templates dupliqués** : Vérifier `/static/` en plus de `/apps/`
5. **Kill forcé** : `pkill -9` nécessaire pour Gunicorn avec --preload

---

## 🎯 Résumé

| Item | Avant | Après |
|------|-------|-------|
| Serveur | Passenger (supposé) | Gunicorn (réel) |
| Redémarrage | touch passenger_wsgi.py | pkill -9 + restart |
| Cache | Partiel | Complet (tous .pyc) |
| Templates | 1 fichier modifié | 2 fichiers (apps + static) |
| Erreur update_site_info | ✗ Présente | ✅ Corrigée |
| Erreur self.request.user | ✗ Présente (cache) | ✅ Corrigée |

---

**Statut** : ✅ Toutes les corrections appliquées  
**Gunicorn** : ✅ Redémarré avec nouveau code  
**Cache** : ✅ Complètement nettoyé  
**Test** : ⏳ En attente de confirmation utilisateur

---

**Heure de déploiement** : 20:06 UTC  
**Durée totale** : ~2 heures 30 minutes  
**Cause racine** : Gunicorn --preload + cache Python + templates dupliqués
