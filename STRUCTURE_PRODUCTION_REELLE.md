# 📁 Structure Réelle de Production - martialcomp.com
**Date:** 24 Octobre 2025  
**Serveur:** martialcomp-production (vigilant-swartz)

---

## 🏗️ Architecture Découverte

### **Racine de l'application**
```
/var/www/vhosts/martialcomp.com/
├── httpdocs/              # Application Django principale
├── venv/                  # Environnement virtuel Python
├── apps/                  # Applications supplémentaires
├── logs/                  # Logs du serveur
└── conf/                  # Configurations
```

---

## 📂 Détails des Répertoires

### 1. **Application Django** (`httpdocs/`)
```
/var/www/vhosts/martialcomp.com/httpdocs/
├── manage.py              # Script de gestion Django
├── config/                # Configuration Django
│   ├── settings/
│   │   └── production.py
│   └── wsgi.py
├── apps/                  # Applications Django
│   ├── competitions/
│   │   ├── templates/
│   │   │   └── competitions/
│   │   │       ├── club/
│   │   │       │   ├── competition_management.html
│   │   │       │   ├── competition_management_general.html ← NOTRE FICHIER
│   │   │       │   └── competition_management_detail.html
│   │   │       └── dashboard/
│   │   ├── views/
│   │   └── models/
│   ├── core/
│   ├── finances/
│   └── ...
├── static/                # Fichiers statiques
├── media/                 # Fichiers uploadés
├── logs/                  # Logs de l'application
│   ├── gunicorn.log
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── backups/               # Sauvegardes
├── .env.production        # Variables d'environnement
└── start_gunicorn.sh      # Script de démarrage
```

**Propriétaire:** `www-data:www-data`  
**Permissions:** `755` (répertoires), `644` (fichiers)

---

### 2. **Environnement Virtuel** (`venv/`)
```
/var/www/vhosts/martialcomp.com/venv/
├── bin/
│   ├── activate           # Script d'activation
│   ├── python             # Python 3.11.2
│   ├── pip
│   └── gunicorn
├── lib/
│   └── python3.11/
│       └── site-packages/ # Packages Django, etc.
└── pyvenv.cfg
```

**Propriétaire:** `www-data:www-data`

---

### 3. **Répertoire Utilisateur** (`/home/martialcomp/`)
```
/home/martialcomp/
├── martialcomp/           # ⚠️ Ancien répertoire (NE PAS UTILISER)
│   ├── apps/              # Copie partielle
│   └── config/            # Copie partielle
├── backups/               # Sauvegardes diverses
└── fix_*.sh               # Scripts de correction
```

**⚠️ IMPORTANT:** Ce répertoire n'est **PAS** l'application en production !  
C'est probablement un ancien emplacement ou des fichiers de sauvegarde.

---

## ⚙️ Configuration du Service

### **Service systemd:** `martialcomp`

**Fichier:** `/etc/systemd/system/martialcomp.service`

```ini
[Unit]
Description=MartialComp Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/start_gunicorn.sh
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Commandes utiles:**
```bash
sudo systemctl status martialcomp
sudo systemctl restart martialcomp
sudo systemctl stop martialcomp
sudo systemctl start martialcomp
```

---

## 🔧 Script de Démarrage Gunicorn

**Fichier:** `/var/www/vhosts/martialcomp.com/httpdocs/start_gunicorn.sh`

**Configuration:**
- **Workers:** 3
- **Port:** 127.0.0.1:8000
- **Timeout:** 300s
- **Logs:** `/var/www/vhosts/martialcomp.com/httpdocs/logs/`

---

## 🎯 Chemins Importants pour le Déploiement

### **Pour transférer des fichiers:**

| Type de fichier | Destination |
|----------------|-------------|
| Templates Django | `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/` |
| Vues Python | `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/` |
| Modèles Python | `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/models/` |
| Fichiers statiques | `/var/www/vhosts/martialcomp.com/httpdocs/static/` |
| Configuration | `/var/www/vhosts/martialcomp.com/httpdocs/config/` |

### **Après transfert:**

```bash
# 1. Définir les bonnes permissions
sudo chown www-data:www-data /chemin/vers/fichier
sudo chmod 644 /chemin/vers/fichier  # Pour les fichiers
sudo chmod 755 /chemin/vers/dossier  # Pour les dossiers

# 2. Collecter les fichiers statiques (si nécessaire)
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python manage.py collectstatic --noinput

# 3. Redémarrer le service
sudo systemctl restart martialcomp
```

---

## 📊 Utilisateurs et Permissions

| Utilisateur | Rôle | Accès |
|-------------|------|-------|
| `www-data` | Service web | Propriétaire de l'application |
| `bguinziemba` | Administrateur | Accès complet via Plesk |
| `martialcomp` | Utilisateur système | Accès limité |
| `root` | Super admin | Accès complet |

---

## 🚨 Erreurs Communes

### **Erreur 1: Permission denied**
```bash
# Solution
sudo chown www-data:www-data /chemin/vers/fichier
sudo chmod 644 /chemin/vers/fichier
```

### **Erreur 2: Module not found**
```bash
# Vérifier que le venv est activé
source /var/www/vhosts/martialcomp.com/venv/bin/activate
which python  # Doit pointer vers le venv
```

### **Erreur 3: Template not found**
```bash
# Vérifier le chemin complet
ls -la /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/
```

---

## 📝 Notes Importantes

1. **NE JAMAIS** utiliser `/home/martialcomp/martialcomp/` pour le déploiement
2. **TOUJOURS** utiliser `/var/www/vhosts/martialcomp.com/httpdocs/`
3. **TOUJOURS** définir les permissions `www-data:www-data`
4. **TOUJOURS** redémarrer le service après modification
5. **TOUJOURS** faire une sauvegarde avant modification

---

## ✅ Checklist de Déploiement

Avant chaque déploiement:
- [ ] Identifier le bon chemin de destination
- [ ] Faire une sauvegarde du fichier existant
- [ ] Transférer le nouveau fichier
- [ ] Définir les bonnes permissions (www-data:www-data)
- [ ] Tester localement si possible
- [ ] Collecter les fichiers statiques si nécessaire
- [ ] Redémarrer le service
- [ ] Vérifier les logs
- [ ] Tester l'URL en production

---

## 🔍 Commandes de Diagnostic

```bash
# Vérifier la structure
ssh martialcomp-production "ls -la /var/www/vhosts/martialcomp.com/"

# Vérifier le service
ssh martialcomp-production "sudo systemctl status martialcomp"

# Vérifier les logs
ssh martialcomp-production "sudo tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log"

# Vérifier les permissions
ssh martialcomp-production "ls -la /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/"

# Vérifier le venv
ssh martialcomp-production "source /var/www/vhosts/martialcomp.com/venv/bin/activate && python --version"
```

---

**Fin du document**
