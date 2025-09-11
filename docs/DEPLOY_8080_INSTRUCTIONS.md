# 🚀 DÉPLOIEMENT IMMÉDIAT - MartialComp Port 8080

## ⚡ Déploiement en 2 Minutes

### **Étape 1 : Connexion au Serveur**

```bash
ssh root@212.227.78.104
```

### **Étape 2 : Script de Déploiement Automatique**

```bash
# Copier et coller TOUT ce bloc d'un coup :
cd /var/www/vhosts/martialcomp.com/httpdocs

cat > deploy_8080.sh << 'EOF'
#!/bin/bash
set -e
echo "🚀 DÉPLOIEMENT MARTIALCOMP - PORT 8080"
PROJECT="/var/www/vhosts/martialcomp.com/httpdocs"
LOGS="/var/www/vhosts/martialcomp.com/logs"
mkdir -p "$LOGS" && chown -R www-data:www-data "$LOGS"
cd "$PROJECT"
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true
fuser -k 8080/tcp || true
sleep 3
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT"
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
python manage.py collectstatic --noinput --clear
nohup python manage.py runserver 0.0.0.0:8080 > "$LOGS/django_8080.log" 2>&1 &
PID=$!
sleep 8
if curl -s http://localhost:8080/ >/dev/null; then
    echo "✅ SUCCESS - Django démarré sur port 8080"
    echo "🌐 URL: http://martialcomp.com:8080"
    echo "📋 PID: $PID"
    echo "📄 Logs: $LOGS/django_8080.log"
    echo "🔍 Test externe: curl -I http://martialcomp.com:8080/"
else
    echo "❌ ERREUR - Django ne répond pas"
    echo "Logs:"
    tail -20 "$LOGS/django_8080.log"
    exit 1
fi
EOF

chmod +x deploy_8080.sh
./deploy_8080.sh
```

### **Étape 3 : Vérification**

```bash
# Test depuis le serveur
curl -I http://localhost:8080/

# Voir les processus Django
ps aux | grep manage.py
```

### **Étape 4 : Test depuis votre Machine Locale**

```bash
# Exécuter depuis votre ordinateur (Windows)
curl -I http://martialcomp.com:8080/
```

---

## ⚡ **Alternative : Commandes Manuelles Étape par Étape**

Si le script automatique ne fonctionne pas, voici les commandes une par une :

```bash
# 1. Aller dans le projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# 2. Créer répertoire logs
mkdir -p /var/www/vhosts/martialcomp.com/logs/
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/logs/

# 3. Arrêter processus existants
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true
fuser -k 8080/tcp || true
sleep 3

# 4. Activer environnement virtuel
source venv/bin/activate

# 5. Variables Django
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="/var/www/vhosts/martialcomp.com/httpdocs"

# 6. Ouvrir firewall
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# 7. Collecte fichiers statiques
python manage.py collectstatic --noinput --clear

# 8. Démarrer Django
nohup python manage.py runserver 0.0.0.0:8080 > /var/www/vhosts/martialcomp.com/logs/django_8080.log 2>&1 &

# 9. Attendre et tester
sleep 10
curl -I http://localhost:8080/
```

---

## 🔍 **Vérifications de Succès**

### ✅ **Django fonctionne si :**

```bash
# Processus Django visible
ps aux | grep manage.py | grep 8080

# Port 8080 en écoute
netstat -tlnp | grep :8080

# Réponse HTTP
curl -I http://localhost:8080/
# Doit retourner: HTTP/1.1 200 OK
```

### ✅ **Application accessible depuis l'extérieur si :**

```bash
# Depuis votre machine Windows
curl -I http://martialcomp.com:8080/
# Doit retourner: HTTP/1.1 200 OK
```

---

## 🚨 **Dépannage Express**

### ❌ **Si Django ne démarre pas :**

```bash
# Voir les erreurs
tail -50 /var/www/vhosts/martialcomp.com/logs/django_8080.log

# Tester la configuration
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py check
```

### ❌ **Si port 8080 occupé :**

```bash
# Voir qui utilise le port
lsof -i :8080

# Forcer l'arrêt
fuser -k 8080/tcp
```

### ❌ **Si erreur module rosetta :**

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
pip install django-rosetta
```

---

## 📱 **URLs Finales d'Accès**

Une fois déployé, l'application sera accessible via :

- **Principal** : `http://martialcomp.com:8080`
- **IP directe** : `http://212.227.78.104:8080`
- **Local** : `http://localhost:8080` (depuis le serveur)

---

## 🔄 **Commandes de Gestion**

### **Arrêter l'application :**

```bash
pkill -f "manage.py runserver"
```

### **Redémarrer l'application :**

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8080 > /var/www/vhosts/martialcomp.com/logs/django_8080.log 2>&1 &
```

### **Voir les logs en temps réel :**

```bash
tail -f /var/www/vhosts/martialcomp.com/logs/django_8080.log
```

---

## ⏰ **Temps Estimé**

- **Déploiement** : 2-3 minutes
- **Test** : 1 minute
- **Total** : 5 minutes maximum

**🎯 L'application devrait être accessible sur `http://martialcomp.com:8080` dans moins de 5 minutes !**
