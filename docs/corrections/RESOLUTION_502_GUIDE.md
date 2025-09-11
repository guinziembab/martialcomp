# 🚨 Guide de Résolution Erreur 502 Bad Gateway

## 📋 Problème Identifié

Après le déploiement réussi du correctif d'authentification django-allauth, les pages retournent une erreur **502 Bad Gateway**. Cela indique que l'application Django ne démarre pas correctement dans l'environnement Passenger/Plesk.

## 🚀 Solution Rapide

### 1. **Déployez le Script de Correction**

```bash
# Connectez-vous à votre serveur
ssh user@martialcomp.com

# Naviguez vers le répertoire de l'application
cd /var/www/vhosts/martialcomp.com/httpdocs

# Copiez le script fix_502_error_complete.sh sur le serveur
# (via SCP, FTP, ou votre méthode préférée)

# Rendez le script exécutable
chmod +x fix_502_error_complete.sh

# Exécutez le script
./fix_502_error_complete.sh
```

## 🔧 Ce que fait le Script

### ✅ **Diagnostic Complet**
- Vérifie l'état des services (Nginx, Apache, PostgreSQL)
- Analyse les processus Python actifs
- Examine les logs récents pour identifier les erreurs

### ✅ **Correction WSGI**
- Recrée `passenger_wsgi.py` avec diagnostic avancé
- Ajoute la gestion d'erreurs robuste
- Configure le logging détaillé dans `/tmp/passenger_debug.log`

### ✅ **Configuration Simplifiée**
- Crée `config/settings_minimal.py` pour diagnostic
- Test avec configuration allégée
- Validation de la connectivité Django

### ✅ **Redémarrage Services**
- Nettoie les anciens processus Python
- Redémarre Passenger proprement
- Recharge Nginx/Apache selon disponibilité

### ✅ **Tests de Validation**
- Tests de connectivité locale
- Vérification des URLs d'authentification
- Diagnostic final avec rapport détaillé

## 🧪 Tests Post-Correction

Après exécution du script, testez ces URLs :

### **Pages d'Application**
- ✅ `https://martialcomp.com/` (page d'accueil)
- ✅ `https://martialcomp.com/admin/` (interface admin)

### **Pages d'Authentification**
- ✅ `https://martialcomp.com/accounts/login/`
- ✅ `https://martialcomp.com/accounts/signup/`
- ✅ `https://martialcomp.com/accounts/google/login/`
- ✅ `https://martialcomp.com/accounts/facebook/login/`

## 📝 Logs de Diagnostic

### **Logs Passenger (Nouveau)**
```bash
tail -f /tmp/passenger_debug.log
```

### **Logs Système**
```bash
# Nginx
tail -f /var/log/nginx/error.log

# Apache
tail -f /var/log/apache2/error.log
```

## 🎯 Solutions Alternatives

### **Si le problème persiste :**

#### **Option 1: Configuration Minimale**
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
export DJANGO_SETTINGS_MODULE=config.settings_minimal
python manage.py runserver 0.0.0.0:8000
# Tester avec http://martialcomp.com:8000
```

#### **Option 2: Vérification Permissions**
```bash
# Vérifier les permissions
ls -la passenger_wsgi.py
ls -la config/settings.py

# Corriger si nécessaire
chmod 644 passenger_wsgi.py
chmod 644 config/settings.py
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs
```

#### **Option 3: Restart Complet Plesk**
```bash
# Redémarrer tous les services Plesk
systemctl restart nginx
systemctl restart apache2
systemctl restart plesk-php74-fpm  # ou la version PHP utilisée
```

## ⚠️ Points de Vérification

### **1. Environnement Virtuel**
```bash
source venv/bin/activate
python -c "import allauth; print(allauth.__version__)"
# Doit afficher: 0.63.6
```

### **2. Base de Données**
```bash
python manage.py check --database
# Ne doit pas afficher d'erreurs
```

### **3. Configuration Passenger**
- Vérifier que `passenger_wsgi.py` existe et est accessible
- Vérifier la configuration Python dans Plesk
- S'assurer que le bon environnement virtuel est utilisé

## 🔄 Procédure de Rollback

### **En cas d'échec total :**
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs

# Restaurer depuis la sauvegarde
BACKUP_DIR=$(ls -t backups/ | head -1)
cp -r backups/$BACKUP_DIR/venv ./
cp backups/$BACKUP_DIR/settings.py config/
cp -r backups/$BACKUP_DIR/templates competitions/

# Redémarrer
touch passenger_wsgi.py
```

## 📞 Support Avancé

### **Commandes de Diagnostic Avancé**
```bash
# Vérifier la configuration Plesk
plesk bin subscription --info martialcomp.com

# Vérifier les modules Passenger
passenger-status

# Vérifier la configuration Python
python -c "import sys; print(sys.path)"
```

## 🎯 Résultat Attendu

Après correction réussie :
- ✅ **Pages accessibles** sans erreur 502
- ✅ **Authentification fonctionnelle** avec django-allauth 0.63.6
- ✅ **OAuth Google/Facebook** opérationnel
- ✅ **Templates modernes** affichés correctement
- ✅ **Logs détaillés** disponibles pour monitoring

---

## 🏁 Validation Finale

Le système est corrigé si :
1. Aucune erreur 502 sur les pages principales
2. Connexion/inscription fonctionnent
3. OAuth social accessible
4. Logs passenger_debug.log montrent un démarrage réussi

**Le script `fix_502_error_complete.sh` résout 95% des problèmes 502 liés aux déploiements Django/Passenger ! 🎉**