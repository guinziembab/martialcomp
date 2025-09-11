# 🚨 RAPPORT D'ERREURS - MARTIALCOMP.COM

**Date :** 14 Juillet 2025  
**Situation :** Site non accessible après transfert des fichiers de développement vers production

---

## 📋 **CONTEXTE INITIAL**

### **Avant le transfert :**

- ✅ **Site fonctionnel** : martialcomp.com accessible
- ✅ **Django opérationnel** sur production
- ✅ **Base de données PostgreSQL** connectée
- ✅ **Apache proxy** configuré (port 80 → 8080)

### **Action déclenchante :**

- 🔄 **Transfert complet** des fichiers de développement vers production
- 📦 **Remplacement total** du code Django existant
- ⚙️ **Synchronisation** des templates et configurations

---

## 🔍 **ERREURS CHRONOLOGIQUES RENCONTRÉES**

### **1. ERREUR INITIALE - Configuration Django (14h30)**

```
django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1),
port 5432 failed: FATAL: password authentication failed for user "postgres"
```

**Cause :** Après le transfert, Django tentait de se connecter avec l'utilisateur `postgres` au lieu de `martialcomp_user`

**Solution appliquée :**

- ✅ Vérification des variables d'environnement dans `.env`
- ✅ Création de scripts de démarrage avec configuration explicite

---

### **2. ERREUR SSL REDIRECT (16h00)**

```
INFO "GET / HTTP/1.1" 301 0
INFO "HEAD / HTTP/1.1" 301 0
```

**Cause :** `SECURE_SSL_REDIRECT = True` dans production.py forçait HTTPS alors qu'Apache proxy utilise HTTP

**Solution appliquée :**

- ✅ Désactivation de `SECURE_SSL_REDIRECT`
- ✅ Création de script `start_django_simple.py`

---

### **3. ERREUR ALLOWED_HOSTS (18h00)**

```
HTTP/1.1 400 Bad Request
Server: WSGIServer/0.2 CPython/3.9.2
```

**Cause :** L'IP publique `212.227.78.104` n'était pas autorisée dans `ALLOWED_HOSTS`

**Solution tentée :**

- ❌ Ajout de l'IP dans plusieurs scripts
- ❌ Multiples tentatives de configuration

---

### **4. PROBLÈME DE CONNECTIVITÉ EXTERNE (20h30)**

```
Firefox: La connexion a échoué
Chrome: ERR_CONNECTION_REFUSED
```

**Cause :** Malgré Django fonctionnel en local, accès externe bloqué

**Solutions tentées :**

- ✅ Vérification Apache (fonctionne)
- ✅ Vérification pare-feu (autorise port 80)
- ❌ ALLOWED_HOSTS toujours problématique

---

## 📊 **ÉTAT ACTUEL DU SYSTÈME (21h15)**

### **🟢 COMPOSANTS FONCTIONNELS :**

1. **Infrastructure serveur :**

   - ✅ **Serveur** : 212.227.78.104 (Ionos) accessible en SSH
   - ✅ **PostgreSQL** : Service actif, base `martialcomp_db` accessible
   - ✅ **Apache** : Service actif, écoute sur port 80

2. **Configuration réseau :**

   - ✅ **Pare-feu** : Autorise HTTP (port 80)
   - ✅ **DNS** : martialcomp.com pointe vers 212.227.78.104
   - ✅ **Proxy Apache** : Configuration martialcomp-proxy.conf active

3. **Django interne :**
   - ✅ **Port 8080** : Django écoute et répond
   - ✅ **Base de données** : Connexion PostgreSQL fonctionnelle
   - ✅ **Réponse locale** : `curl http://localhost:8080` → HTTP/1.1 302 Found

### **🔴 COMPOSANTS DÉFAILLANTS :**

1. **Accès externe :**

   - ❌ **martialcomp.com** : ERR_CONNECTION_REFUSED
   - ❌ **IP directe** : HTTP/1.1 400 Bad Request
   - ❌ **ALLOWED_HOSTS** : Configuration non appliquée correctement

2. **Configuration Django :**
   - ❌ **Variables d'environnement** : Non chargées par les settings
   - ❌ **Production.py** : Lecture incorrecte des variables DB

---

## 🔧 **PROBLÈMES RACINES IDENTIFIÉS**

### **1. Configuration Django désynchronisée**

- Les nouveaux fichiers de développement utilisent `python-decouple` ou `dotenv`
- L'ancien système de production utilisait des variables d'environnement directes
- **Résultat :** Mismatch entre configuration attendue et réelle

### **2. ALLOWED_HOSTS non persistant**

- Malgré tous les scripts créés, Django continue de rejeter l'IP publique
- **Résultat :** Accès externe impossible

### **3. Différence dev/production**

- Le code de développement n'est pas 100% compatible avec l'environnement de production
- **Résultat :** Instabilité générale

---

## 🎯 **SOLUTIONS RECOMMANDÉES**

### **SOLUTION IMMÉDIATE (30 minutes)**

1. **Revenir à l'état fonctionnel :**

   - Restaurer la sauvegarde de production d'avant transfert
   - Redémarrer Apache et Django
   - Vérifier l'accès externe

2. **Analyse post-mortem :**
   - Identifier les différences critiques dev/prod
   - Préparer un plan de migration progressive

### **SOLUTION À LONG TERME (2-4 heures)**

1. **Migration progressive :**

   - Synchroniser d'abord les templates seulement
   - Tester l'accès externe
   - Migrer ensuite les applications une par une

2. **Configuration unifiée :**
   - Créer un settings/production.py compatible
   - Unifier la gestion des variables d'environnement
   - Tester chaque composant individuellement

---

## 📈 **MÉTRIQUES D'IMPACT**

- **Temps d'arrêt** : ~7 heures (14h30 → 21h30)
- **Tentatives de résolution** : 15+ scripts créés
- **Composants affectés** : Django, Configuration, Accès externe
- **Utilisateurs impactés** : Tous (site inaccessible)

---

## ⚠️ **LEÇONS APPRISES**

1. **Toujours tester** les transferts complets sur un environnement de staging
2. **Documenter** précisément les différences entre dev et production
3. **Conserver** des sauvegardes fonctionnelles avant modifications majeures
4. **Valider** l'accès externe après chaque modification critique

---

## 🔄 **PROCHAINES ÉTAPES RECOMMANDÉES**

### **Étape 1 - URGENCE (maintenant)**

```bash
# Restaurer la dernière sauvegarde fonctionnelle
cd /var/www/vhosts/martialcomp.com/
cp -r production_complete_backup_YYYYMMDD/* httpdocs/
systemctl restart apache2
```

### **Étape 2 - DIAGNOSTIC (dans 1h)**

```bash
# Vérifier l'accès externe
curl -I http://martialcomp.com
curl -I http://212.227.78.104
```

### **Étape 3 - MIGRATION PROGRESSIVE (demain)**

- Synchroniser templates par application
- Tester après chaque synchronisation
- Documenter les incompatibilités

---

**Status final :** 🔴 **CRITIQUE** - Site inaccessible, nécessite intervention immédiate

**Date :** 14 Juillet 2025  
**Situation :** Site non accessible après transfert des fichiers de développement vers production

---

## 📋 **CONTEXTE INITIAL**

### **Avant le transfert :**

- ✅ **Site fonctionnel** : martialcomp.com accessible
- ✅ **Django opérationnel** sur production
- ✅ **Base de données PostgreSQL** connectée
- ✅ **Apache proxy** configuré (port 80 → 8080)

### **Action déclenchante :**

- 🔄 **Transfert complet** des fichiers de développement vers production
- 📦 **Remplacement total** du code Django existant
- ⚙️ **Synchronisation** des templates et configurations

---

## 🔍 **ERREURS CHRONOLOGIQUES RENCONTRÉES**

### **1. ERREUR INITIALE - Configuration Django (14h30)**

```
django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1),
port 5432 failed: FATAL: password authentication failed for user "postgres"
```

**Cause :** Après le transfert, Django tentait de se connecter avec l'utilisateur `postgres` au lieu de `martialcomp_user`

**Solution appliquée :**

- ✅ Vérification des variables d'environnement dans `.env`
- ✅ Création de scripts de démarrage avec configuration explicite

---

### **2. ERREUR SSL REDIRECT (16h00)**

```
INFO "GET / HTTP/1.1" 301 0
INFO "HEAD / HTTP/1.1" 301 0
```

**Cause :** `SECURE_SSL_REDIRECT = True` dans production.py forçait HTTPS alors qu'Apache proxy utilise HTTP

**Solution appliquée :**

- ✅ Désactivation de `SECURE_SSL_REDIRECT`
- ✅ Création de script `start_django_simple.py`

---

### **3. ERREUR ALLOWED_HOSTS (18h00)**

```
HTTP/1.1 400 Bad Request
Server: WSGIServer/0.2 CPython/3.9.2
```

**Cause :** L'IP publique `212.227.78.104` n'était pas autorisée dans `ALLOWED_HOSTS`

**Solution tentée :**

- ❌ Ajout de l'IP dans plusieurs scripts
- ❌ Multiples tentatives de configuration

---

### **4. PROBLÈME DE CONNECTIVITÉ EXTERNE (20h30)**

```
Firefox: La connexion a échoué
Chrome: ERR_CONNECTION_REFUSED
```

**Cause :** Malgré Django fonctionnel en local, accès externe bloqué

**Solutions tentées :**

- ✅ Vérification Apache (fonctionne)
- ✅ Vérification pare-feu (autorise port 80)
- ❌ ALLOWED_HOSTS toujours problématique

---

## 📊 **ÉTAT ACTUEL DU SYSTÈME (21h15)**

### **🟢 COMPOSANTS FONCTIONNELS :**

1. **Infrastructure serveur :**

   - ✅ **Serveur** : 212.227.78.104 (Ionos) accessible en SSH
   - ✅ **PostgreSQL** : Service actif, base `martialcomp_db` accessible
   - ✅ **Apache** : Service actif, écoute sur port 80

2. **Configuration réseau :**

   - ✅ **Pare-feu** : Autorise HTTP (port 80)
   - ✅ **DNS** : martialcomp.com pointe vers 212.227.78.104
   - ✅ **Proxy Apache** : Configuration martialcomp-proxy.conf active

3. **Django interne :**
   - ✅ **Port 8080** : Django écoute et répond
   - ✅ **Base de données** : Connexion PostgreSQL fonctionnelle
   - ✅ **Réponse locale** : `curl http://localhost:8080` → HTTP/1.1 302 Found

### **🔴 COMPOSANTS DÉFAILLANTS :**

1. **Accès externe :**

   - ❌ **martialcomp.com** : ERR_CONNECTION_REFUSED
   - ❌ **IP directe** : HTTP/1.1 400 Bad Request
   - ❌ **ALLOWED_HOSTS** : Configuration non appliquée correctement

2. **Configuration Django :**
   - ❌ **Variables d'environnement** : Non chargées par les settings
   - ❌ **Production.py** : Lecture incorrecte des variables DB

---

## 🔧 **PROBLÈMES RACINES IDENTIFIÉS**

### **1. Configuration Django désynchronisée**

- Les nouveaux fichiers de développement utilisent `python-decouple` ou `dotenv`
- L'ancien système de production utilisait des variables d'environnement directes
- **Résultat :** Mismatch entre configuration attendue et réelle

### **2. ALLOWED_HOSTS non persistant**

- Malgré tous les scripts créés, Django continue de rejeter l'IP publique
- **Résultat :** Accès externe impossible

### **3. Différence dev/production**

- Le code de développement n'est pas 100% compatible avec l'environnement de production
- **Résultat :** Instabilité générale

---

## 🎯 **SOLUTIONS RECOMMANDÉES**

### **SOLUTION IMMÉDIATE (30 minutes)**

1. **Revenir à l'état fonctionnel :**

   - Restaurer la sauvegarde de production d'avant transfert
   - Redémarrer Apache et Django
   - Vérifier l'accès externe

2. **Analyse post-mortem :**
   - Identifier les différences critiques dev/prod
   - Préparer un plan de migration progressive

### **SOLUTION À LONG TERME (2-4 heures)**

1. **Migration progressive :**

   - Synchroniser d'abord les templates seulement
   - Tester l'accès externe
   - Migrer ensuite les applications une par une

2. **Configuration unifiée :**
   - Créer un settings/production.py compatible
   - Unifier la gestion des variables d'environnement
   - Tester chaque composant individuellement

---

## 📈 **MÉTRIQUES D'IMPACT**

- **Temps d'arrêt** : ~7 heures (14h30 → 21h30)
- **Tentatives de résolution** : 15+ scripts créés
- **Composants affectés** : Django, Configuration, Accès externe
- **Utilisateurs impactés** : Tous (site inaccessible)

---

## ⚠️ **LEÇONS APPRISES**

1. **Toujours tester** les transferts complets sur un environnement de staging
2. **Documenter** précisément les différences entre dev et production
3. **Conserver** des sauvegardes fonctionnelles avant modifications majeures
4. **Valider** l'accès externe après chaque modification critique

---

## 🔄 **PROCHAINES ÉTAPES RECOMMANDÉES**

### **Étape 1 - URGENCE (maintenant)**

```bash
# Restaurer la dernière sauvegarde fonctionnelle
cd /var/www/vhosts/martialcomp.com/
cp -r production_complete_backup_YYYYMMDD/* httpdocs/
systemctl restart apache2
```

### **Étape 2 - DIAGNOSTIC (dans 1h)**

```bash
# Vérifier l'accès externe
curl -I http://martialcomp.com
curl -I http://212.227.78.104
```

### **Étape 3 - MIGRATION PROGRESSIVE (demain)**

- Synchroniser templates par application
- Tester après chaque synchronisation
- Documenter les incompatibilités

---

**Status final :** 🔴 **CRITIQUE** - Site inaccessible, nécessite intervention immédiate
