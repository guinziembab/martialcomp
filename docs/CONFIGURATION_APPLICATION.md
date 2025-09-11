# 🏗️ CONFIGURATION APPLICATION MARTIALCOMP

## 📋 Vue d'ensemble du Projet

**MartialComp** est une application Django multilingue de gestion des arts martiaux avec architecture multi-tenant.

### 🎯 Informations Générales
- **Framework** : Django 5.1.4
- **Base de données** : PostgreSQL
- **Cache** : Redis
- **Serveur** : Gunicorn + Nginx
- **Déploiement** : IONOS Debian + Plesk
- **Langues supportées** : 16 langues

---

## 🗂️ Structure du Projet

### **Applications Django**
```
martialcomp/
├── competitions/       # Application principale
├── organizations/      # Multi-tenant
├── grades/            # Gestion des grades
├── finances/          # Gestion financière
├── shop/              # E-commerce
├── documents/         # Gestion documentaire
├── family_management/ # Gestion familiale
├── multitenant/       # Infrastructure multi-tenant
├── accounts/          # Authentification
├── api/               # API REST
├── permissions_manager/ # Gestion des permissions
├── payment/           # Paiements
├── api_auth/          # Auth API
└── federations/       # Fédérations
```

### **Configuration Django**
```
config/
├── settings/
│   ├── base.py           # Configuration de base
│   ├── development.py    # Configuration développement
│   ├── production.py     # Configuration production
│   └── staging.py        # Configuration staging
├── urls.py              # URLs principales
└── wsgi.py              # WSGI configuration
```

---

## 🌍 Internationalisation

### **Langues Supportées**
- **Principales** : FR, EN, DE, ES, IT, PT, NO, AR
- **Supplémentaires** : ZH, JA, KO, HI, AM, SW, YO, ZU

### **Fichiers de Traduction**
```
locale/
├── fr/LC_MESSAGES/django.po  # Français (base)
├── en/LC_MESSAGES/django.po  # Anglais
├── de/LC_MESSAGES/django.po  # Allemand
├── es/LC_MESSAGES/django.po  # Espagnol
├── it/LC_MESSAGES/django.po  # Italien
├── pt/LC_MESSAGES/django.po  # Portugais
├── no/LC_MESSAGES/django.po  # Norvégien
├── ar/LC_MESSAGES/django.po  # Arabe
└── ... (autres langues)
```

### **Outils de Traduction**
- **Poedit Pro** : Traduction professionnelle
- **Rosetta** : Interface web Django
- **IA Translation** : Traduction automatique (DeepL, Google, OpenAI)

---

## 🐳 Environnements

### **Développement Local**
```bash
# Démarrage
python manage.py runserver

# URLs
http://localhost:8000/       # Application
http://localhost:8000/admin/ # Admin
http://localhost:8000/rosetta/ # Traductions
```

### **Staging**
```bash
# Docker
docker-compose -f docker-compose.staging.yml up -d

# URL
http://staging.martialcomp.com/
```

### **Production**
```bash
# Service systemd
systemctl start martialcomp

# URLs
https://martialcomp.com/
https://www.martialcomp.com/
https://*.martialcomp.com/  # Sous-domaines
```

---

## 🔧 Configuration Technique

### **Base de Données**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp',
        'USER': 'martialcomp',
        'PASSWORD': 'AQWZSX123ok,',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### **Cache Redis**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### **Gunicorn**
```python
# gunicorn.conf.py
bind = "127.0.0.1:8001"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
```

---

## 📁 Fichiers Importants

### **Configuration**
- `.env` : Variables d'environnement
- `requirements.txt` : Dépendances Python
- `gunicorn.conf.py` : Configuration Gunicorn
- `docker-compose.*.yml` : Configuration Docker

### **Déploiement**
- `deploy-gunicorn.sh` : Script de déploiement
- `martialcomp.service` : Service systemd
- `ionos-*.py` : Configuration IONOS

### **Traductions**
- `complete_i18n_workflow.py` : Workflow complet
- `ai_translation_system.py` : Système IA
- `*.po` : Fichiers de traduction

---

## 🔍 Commandes Utiles

### **Développement**
```bash
# Démarrer le serveur
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Traductions
python manage.py makemessages --all
python manage.py compilemessages

# Collecte des fichiers statiques
python manage.py collectstatic

# Créer un superutilisateur
python manage.py createsuperuser
```

### **Production**
```bash
# Redémarrer l'application
systemctl restart martialcomp

# Voir les logs
journalctl -u martialcomp -f

# Nginx
systemctl reload nginx
nginx -t

# Base de données
pg_dump -U martialcomp -d martialcomp > backup.sql
```

---

## 🌐 URLs Principales

### **Application**
- `/` : Page d'accueil
- `/competitions/` : Compétitions
- `/organizations/` : Organisations
- `/grades/` : Grades
- `/finances/` : Finances
- `/shop/` : Boutique

### **Admin et Outils**
- `/admin/` : Administration Django
- `/rosetta/` : Traductions
- `/api/` : API REST
- `/health/` : Health check

### **Authentification**
- `/accounts/login/` : Connexion
- `/accounts/signup/` : Inscription
- `/accounts/logout/` : Déconnexion

---

## 🔐 Sécurité

### **Variables d'Environnement**
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,*.martialcomp.com
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
```

### **SSL/HTTPS**
- Certificats Let's Encrypt via Plesk
- Redirection HTTP → HTTPS
- Headers de sécurité configurés

---

## 📊 Monitoring

### **Logs**
- Django : `/var/log/django/`
- Gunicorn : `/var/log/gunicorn/`
- Nginx : `/var/log/nginx/`

### **Health Checks**
- Application : `/health/`
- Base de données : Migrations status
- Redis : Connection test

---

## 🚀 Déploiement

### **Workflow**
1. **Développement** → Git push
2. **Staging** → Tests automatiques
3. **Production** → Déploiement manuel

### **Scripts de Déploiement**
- `deploy-gunicorn.sh` : Déploiement Gunicorn
- `ionos-deployment-script.sh` : Déploiement IONOS
- `sync-db-to-dev.sh` : Synchronisation DB

---

## 📞 Support

### **Équipe**
- **Développeur Principal** : Configuration et maintenance
- **Traducteurs** : Poedit Pro + Rosetta
- **DevOps** : IONOS + Plesk

### **Documentation**
- Guides markdown dans `/root/`
- Documentation Django officielle
- Documentation Plesk IONOS

---

## 🔄 Maintenance

### **Quotidienne**
- Vérification des logs
- Monitoring des performances
- Backup automatique

### **Hebdomadaire**
- Mise à jour des traductions
- Nettoyage des logs
- Tests de sécurité

### **Mensuelle**
- Mise à jour des dépendances
- Audit de sécurité
- Optimisation des performances

---

**📝 Dernière mise à jour : 2025-01-18**
**🔧 Version : Django 5.1.4 - Multi-tenant**
**🌍 Langues : 16 langues supportées**