# 🚀 Guide Déploiement MartialComp - Ionos Plesk (Port Alternatif)

## ⚠️ Problème Identifié

**Le port 80 est déjà utilisé par Ionos et non disponible pour MartialComp.**

## 💡 Solutions Alternatives Disponibles

### **SOLUTION 1 : Django sur Port 8080 (Recommandée)**

L'application sera accessible via `http://martialcomp.com:8080`

### **SOLUTION 2 : Sous-domaine Dédié**

L'application sera accessible via `http://app.martialcomp.com:8080`

### **SOLUTION 3 : Proxy Nginx Interne**

L'application reste accessible via `https://martialcomp.com` (proxy interne)

---

## 🔧 **SOLUTION 1 : Configuration Port 8080**

### Étape 1 : Connexion au Serveur

```bash
ssh root@212.227.78.104
cd /var/www/vhosts/martialcomp.com/httpdocs
```

### Étape 2 : Démarrage Django sur Port 8080

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Arrêter les processus existants
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true

# Créer le répertoire logs
mkdir -p /var/www/vhosts/martialcomp.com/logs/
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/logs/

# Démarrer Django sur port 8080 (accessible depuis l'extérieur)
nohup python manage.py runserver 0.0.0.0:8080 > /var/www/vhosts/martialcomp.com/logs/django_8080.log 2>&1 &
```

### Étape 3 : Ouvrir le Port dans le Firewall

```bash
# Ouvrir port 8080
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# Sauvegarder les règles
iptables-save > /etc/iptables/rules.v4
```

### Étape 4 : Vérification

```bash
# Test local
curl -I http://localhost:8080/

# Test depuis votre machine locale
curl -I http://martialcomp.com:8080/
```

### Étape 5 : Configuration Permanente avec Systemd

```bash
# Créer le service systemd
cat > /etc/systemd/system/martialcomp.service << 'EOF'
[Unit]
Description=MartialComp Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment="PATH=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin/python manage.py runserver 0.0.0.0:8080
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Activer et démarrer le service
systemctl daemon-reload
systemctl enable martialcomp
systemctl start martialcomp
systemctl status martialcomp
```

**✅ URL d'accès : `http://martialcomp.com:8080`**

---

## 🔧 **SOLUTION 2 : Sous-domaine dans Plesk**

### Étape 1 : Créer le Sous-domaine dans Plesk

1. Connexion à Plesk : `https://212.227.78.104:8443`
2. Aller à **"Domaines"** → **"Ajouter un sous-domaine"**
3. Nom du sous-domaine : `app`
4. Domaine parent : `martialcomp.com`
5. Document Root : `/var/www/vhosts/martialcomp.com/app/`

### Étape 2 : Configuration du Proxy dans Plesk

1. Aller dans **"Configuration supplémentaire"** du sous-domaine
2. Section **"Directives nginx supplémentaires"**
3. Ajouter :

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Étape 3 : Démarrer Django (même que Solution 1)

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py runserver 127.0.0.1:8080 > /var/www/vhosts/martialcomp.com/logs/django_app.log 2>&1 &
```

**✅ URL d'accès : `http://app.martialcomp.com` (sans port)**

---

## 🔧 **SOLUTION 3 : Proxy Nginx Interne**

### Étape 1 : Modifier la Configuration Nginx dans Plesk

```bash
# Sauvegarder la configuration actuelle
cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup

# Nouvelle configuration proxy
cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Buffers
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 16 4k;
}

# Fichiers statiques
location /static/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/static/;
    expires 30d;
}

location /media/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/media/;
    expires 7d;
}
EOF
```

### Étape 2 : Recharger Nginx

```bash
nginx -t  # Tester la configuration
systemctl reload nginx
```

### Étape 3 : Démarrer Django sur 127.0.0.1:8080

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py runserver 127.0.0.1:8080 > /var/www/vhosts/martialcomp.com/logs/django_proxy.log 2>&1 &
```

**✅ URL d'accès : `https://martialcomp.com` (URL normale)**

---

## 🛠️ **Scripts Automatisés**

### Script de Démarrage Rapide

```bash
# Télécharger et exécuter le script
cd /var/www/vhosts/martialcomp.com/httpdocs
wget https://raw.githubusercontent.com/scripts/ionos_port_alternative.sh
chmod +x ionos_port_alternative.sh
./ionos_port_alternative.sh
```

### Script de Test

```bash
# Test des ports disponibles
wget https://raw.githubusercontent.com/scripts/test_port_alternative.sh
chmod +x test_port_alternative.sh
./test_port_alternative.sh
```

---

## 🔍 **Diagnostic et Dépannage**

### Vérifier l'État de Django

```bash
# Processus Django actifs
ps aux | grep manage.py

# Ports en écoute
netstat -tlnp | grep 8080

# Logs Django
tail -f /var/www/vhosts/martialcomp.com/logs/django_8080.log
```

### Test de Connectivité

```bash
# Test local (sur le serveur)
curl -I http://localhost:8080/

# Test externe (depuis votre machine)
curl -I http://martialcomp.com:8080/
```

### Résolution des Erreurs Communes

#### ❌ Erreur 502 Bad Gateway

```bash
# Vérifier que Django fonctionne
curl http://127.0.0.1:8080/

# Redémarrer Django
pkill -f "manage.py runserver"
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080 &
```

#### ❌ Port déjà utilisé

```bash
# Trouver le processus qui utilise le port
lsof -i :8080

# Arrêter le processus
fuser -k 8080/tcp
```

#### ❌ Module `rosetta.translate_utils` non trouvé

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
pip install django-rosetta
```

---

## 📋 **Récapitulatif des URLs**

| Solution         | URL d'accès                   | Avantages      | Inconvénients                |
| ---------------- | ----------------------------- | -------------- | ---------------------------- |
| **Port 8080**    | `http://martialcomp.com:8080` | Simple, direct | Port visible dans URL        |
| **Sous-domaine** | `http://app.martialcomp.com`  | URL propre     | Configuration DNS nécessaire |
| **Proxy Nginx**  | `https://martialcomp.com`     | URL normale    | Plus complexe                |

---

## ✅ **Recommandation**

**Commencez par la Solution 1 (Port 8080)** car elle est :

- ✅ La plus simple à implémenter
- ✅ La plus rapide à tester
- ✅ La plus stable
- ✅ Facilement réversible

Une fois que l'application fonctionne correctement, vous pourrez migrer vers la Solution 3 (Proxy) pour avoir une URL propre.

---

## 🚀 **Commandes de Démarrage Rapide**

```bash
# Connexion au serveur
ssh root@212.227.78.104

# Aller dans le projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement
source venv/bin/activate

# Démarrer sur port 8080
python manage.py runserver 0.0.0.0:8080 &

# Ouvrir le firewall
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# Tester
curl -I http://martialcomp.com:8080/
```

**L'application sera accessible via : `http://martialcomp.com:8080`**
