# 📋 GUIDE POUR CLAUDE - DÉBOGAGE INCIDENT MARTIALCOMP

**Date** : 14 Novembre 2025, 21:50 CET  
**Priorité** : 🚨 CRITIQUE  
**Statut** : Site hors ligne depuis 3 heures

---

## 🎯 MISSION

**Remettre le site martialcomp.com en ligne le plus rapidement possible.**

Le site est complètement hors ligne (502 Bad Gateway) suite à des modifications pour corriger un problème d'affichage cosmétique.

---

## 📦 FICHIERS FOURNIS

### 1. RAPPORT_INCIDENT_CRITIQUE_20251114.md
**Contenu** : Rapport complet de l'incident avec :
- Chronologie détaillée (18:44 → 20:45)
- État actuel du serveur
- Fichiers modifiés
- Erreurs rencontrées
- Hypothèses sur la cause
- Diagnostics effectués
- Actions recommandées

**👉 LIRE EN PREMIER**

### 2. COMMANDES_RESTAURATION_URGENCE.sh
**Contenu** : Script bash automatisé pour :
- Sauvegarder les fichiers actuels
- Restaurer depuis les sauvegardes
- Nettoyer le cache
- Redémarrer Gunicorn
- Tester le site

**👉 EXÉCUTER SI RESTAURATION NÉCESSAIRE**

### 3. FICHIERS_ANALYSE_INCIDENT_20251114.tar.gz
**Contenu** : Archive avec :
- `config/urls.py` (version DEV testée)
- `apps/competitions/views/competitions.py` (version DEV testée)
- `apps/competitions/templates/competitions/competition/detail_enhanced.html` (version DEV testée)
- Les 2 fichiers ci-dessus

**👉 EXTRAIRE POUR ANALYSER LES FICHIERS**

---

## 🚀 PLAN D'ACTION RECOMMANDÉ

### Phase 1 : Diagnostic (5-10 min)

1. **Lire le rapport complet**
   ```bash
   cat RAPPORT_INCIDENT_CRITIQUE_20251114.md
   ```

2. **Se connecter au serveur**
   ```bash
   ssh martialcomp-production
   ```

3. **Vérifier l'état actuel**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   
   # Gunicorn
   pgrep -fa gunicorn | wc -l
   
   # Logs récents
   tail -50 logs/gunicorn_error.log
   tail -50 logs/django.log | grep ERROR
   
   # Apache
   systemctl status apache2
   tail -50 /var/log/apache2/error.log
   ```

4. **Tester Gunicorn en mode debug**
   ```bash
   # Arrêter le daemon
   pkill -9 -f gunicorn
   
   # Démarrer en mode debug (SANS --daemon)
   cd /var/www/vhosts/martialcomp.com/httpdocs
   /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
     --workers 1 \
     --bind 127.0.0.1:8000 \
     --log-level debug \
     config.wsgi:application
   
   # Observer les erreurs en direct
   # Ctrl+C pour arrêter
   ```

### Phase 2 : Restauration d'urgence (5-10 min)

**Si le diagnostic ne révèle pas de solution rapide :**

1. **Exécuter le script de restauration**
   ```bash
   # Depuis votre machine locale
   cd /mnt/c/martial_hub_django/martialcomp
   chmod +x COMMANDES_RESTAURATION_URGENCE.sh
   ./COMMANDES_RESTAURATION_URGENCE.sh
   ```

2. **OU restauration manuelle**
   ```bash
   ssh martialcomp-production
   cd /var/www/vhosts/martialcomp.com/httpdocs
   
   # Restaurer les fichiers
   cp config/urls.py.original config/urls.py
   cp apps/competitions/views/competitions.py.backup_20251026_081137 \
      apps/competitions/views/competitions.py
   rm -f apps/competitions/templates/competitions/competition/detail_enhanced.html
   
   # Nettoyer le cache
   find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
   
   # Redémarrer Gunicorn
   pkill -9 -f gunicorn
   sleep 2
   /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
     --workers 3 \
     --bind 127.0.0.1:8000 \
     --access-logfile logs/gunicorn_access.log \
     --error-logfile logs/gunicorn_error.log \
     --log-level info \
     config.wsgi:application \
     --daemon
   
   # Vérifier
   sleep 3
   pgrep -fa gunicorn | wc -l  # Doit afficher 4 ou 5
   ```

3. **Tester le site**
   ```bash
   # Test local
   curl -H "X-Forwarded-Proto: https" -H "Host: martialcomp.com" \
        http://127.0.0.1:8000/competition/4/ | head -50
   
   # Test public (attendre 10 secondes pour Cloudflare)
   curl -I https://martialcomp.com/competition/4/
   ```

### Phase 3 : Vérification (2-5 min)

1. **Vérifier que le site répond**
   - URL : https://martialcomp.com/competition/4/
   - Status attendu : HTTP 200 OK
   - Contenu attendu : Page de détail de compétition (sans onglets)

2. **Vérifier Gunicorn**
   ```bash
   pgrep -fa gunicorn | wc -l  # Doit être 4-5
   ps aux | grep gunicorn      # Tous les workers doivent être actifs
   ```

3. **Vérifier les logs**
   ```bash
   tail -20 logs/gunicorn_error.log  # Pas d'erreur récente
   tail -20 logs/django.log          # Pas d'erreur récente
   ```

---

## 🔍 POINTS D'ATTENTION

### 1. Chemins du venv
⚠️ **ATTENTION** : Le venv est à `/var/www/vhosts/martialcomp.com/venv/`  
❌ **PAS** à `/var/www/vhosts/martialcomp.com/httpdocs/.venv/`

### 2. URL de la compétition
Après restauration, l'URL sera :
- ✅ `https://martialcomp.com/competition/4/` (singulier)
- ❌ `https://martialcomp.com/competitions/4/` (pluriel - ne fonctionnera plus)

### 3. Gunicorn
Le nombre de processus attendu est **4 ou 5** :
- 1 master
- 3 workers (configuré avec `--workers 3`)

Si vous voyez seulement **1 processus**, Gunicorn n'a pas démarré correctement.

### 4. Cache Cloudflare
Après toute modification, attendre **10-15 secondes** avant de tester via le domaine public, car Cloudflare met en cache les réponses.

---

## 🐛 ERREURS CONNUES

### Si vous voyez : "No such file or directory: .venv/bin/gunicorn"
**Solution** : Utiliser le bon chemin `/var/www/vhosts/martialcomp.com/venv/bin/gunicorn`

### Si vous voyez : "TemplateDoesNotExist: detail_enhanced.html"
**Solution** : Le template a été supprimé, c'est normal après restauration. La vue doit utiliser `detail.html`

### Si vous voyez : "KeyError: 'auth'"
**Solution** : Restaurer `config/urls.py.original`

### Si vous voyez : "TypeError: got an unexpected keyword argument"
**Solution** : Vérifier la cohérence entre la route URL et la signature de fonction

---

## 📊 MÉTRIQUES DE SUCCÈS

### ✅ Restauration réussie si :
1. **Gunicorn** : 4-5 processus actifs
2. **Site public** : HTTP 200 OK sur https://martialcomp.com/competition/4/
3. **Logs** : Aucune erreur récente dans gunicorn_error.log et django.log
4. **Test local** : `curl http://127.0.0.1:8000/competition/4/` retourne du HTML valide

### ❌ Restauration échouée si :
1. **Gunicorn** : 0-1 processus seulement
2. **Site public** : HTTP 502, 503, ou 500
3. **Logs** : Erreurs Python ou Django
4. **Test local** : Aucune réponse ou erreur 500

---

## 🆘 SI LA RESTAURATION ÉCHOUE

### Option 1 : Contacter l'hébergeur
```
Hébergeur : Plesk
Serveur : vigilant-swartz.217-154-24-122.plesk.page
Action : Restaurer depuis snapshot avant 18:44 CET le 14/11/2025
```

### Option 2 : Analyser les logs Apache
```bash
tail -100 /var/log/apache2/error.log
# Chercher des erreurs de proxy ou de communication avec Gunicorn
```

### Option 3 : Vérifier la configuration Apache
```bash
cat /etc/apache2/sites-enabled/martialcomp.com.conf
# Vérifier le ProxyPass vers 127.0.0.1:8000
```

### Option 4 : Redémarrer Apache
```bash
systemctl restart apache2
sleep 5
systemctl status apache2
```

---

## 📞 INFORMATIONS SERVEUR

```
SSH : martialcomp-production (217.154.24.122)
Utilisateur : root
Application : /var/www/vhosts/martialcomp.com/httpdocs
Venv : /var/www/vhosts/martialcomp.com/venv
Logs : /var/www/vhosts/martialcomp.com/httpdocs/logs
Python : /var/www/vhosts/martialcomp.com/venv/bin/python3
Gunicorn : /var/www/vhosts/martialcomp.com/venv/bin/gunicorn
```

---

## 🎯 OBJECTIF FINAL

**Une fois le site restauré et stable :**

1. ✅ Confirmer que le site est en ligne
2. 📝 Documenter ce qui a causé le problème
3. 🧪 Tester les modifications en environnement de staging avant tout nouveau déploiement
4. 📦 Créer un vrai système de backup automatisé
5. 🔄 Implémenter un processus de déploiement progressif (blue-green deployment)

---

## ⏰ URGENCE

**Le site est hors ligne depuis 3 heures.**  
**Chaque minute compte pour les utilisateurs.**

**Priorité absolue : REMETTRE LE SITE EN LIGNE**  
**Ensuite : Analyser et améliorer**

---

**Bonne chance Claude ! 🚀**

*Généré le 14 Novembre 2025 à 21:50 CET*
