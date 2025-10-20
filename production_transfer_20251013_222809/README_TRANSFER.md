# 📦 Package de Transfert - MartialComp Production

**Date:** 13 Octobre 2025  
**Version:** 1.0  
**Statut:** Prêt pour transfert en production

## 📋 RÉSUMÉ DES MODIFICATIONS

Ce package contient toutes les modifications récentes (2 derniers jours) pour le transfert en production :

### ✅ **Fichiers Inclus**

#### **Apps/Competitions (58 fichiers Python + 19 templates HTML)**
- `admin/qr_code.py` - Gestion des codes QR
- `api.py` - API REST
- `apps.py` - Configuration de l'app
- `consumers.py` - WebSocket consumers
- `forms/` - Formulaires (competitions, competition_types, practitioner)
- `migrations/0009_add_scoring_system_to_competition_type.py` - Migration scoring
- `models/` - Modèles (competitions, competitions_fixed)
- `tests/` - Tests unitaires
- `urls/` - URLs (club, competitions, competition_types)
- `views/` - Vues (categories, etc.)
- `templates/` - Templates HTML (19 fichiers)

#### **Configuration (6 fichiers)**
- `config/asgi.py` - Configuration ASGI
- `config/routing.py` - Routing WebSocket
- `config/settings/base.py` - Configuration de base
- `config/settings/development.py` - Configuration développement
- `config/settings/test.py` - Configuration tests
- `config/urls.py` - URLs principales

#### **Apps/Core (1 fichier)**
- `apps/core/isolation.py` - Module d'isolation

#### **Données JSON (2 fichiers)**
- `disciplines_dev.clean.json` - Disciplines nettoyées
- `grades_dev.clean.json` - Grades nettoyés

## 🚀 INSTRUCTIONS DE DÉPLOIEMENT

### 1. **Sauvegarde de Production**
```bash
# Créer une sauvegarde complète
cd /var/www/vhosts/martialcomp.com/httpdocs
tar -czf backup_before_transfer_$(date +%Y%m%d_%H%M%S).tar.gz .
```

### 2. **Installation des Dépendances Manquantes**
```bash
# Activer l'environnement virtuel
cd /var/www/vhosts/martialcomp.com
source venv/bin/activate

# Installer les dépendances manquantes
pip install --break-system-packages channels python-decouple djangorestframework django-cors-headers pillow qrcode djangorestframework-simplejwt django-allauth django-modeltranslation django-widget-tweaks django-crispy-forms crispy-bootstrap5 django-import-export python-dateutil
```

### 3. **Transfert des Fichiers**
```bash
# Copier les fichiers modifiés
cp -r apps/competitions/* /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/
cp -r config/* /var/www/vhosts/martialcomp.com/httpdocs/config/
cp -r apps/core/* /var/www/vhosts/martialcomp.com/httpdocs/apps/core/

# Copier les fichiers de données
cp disciplines_dev.clean.json grades_dev.clean.json /var/www/vhosts/martialcomp.com/httpdocs/
```

### 4. **Migrations et Compilation**
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source ../venv/bin/activate

# Appliquer les migrations
python3 manage.py migrate --settings=config.settings.production

# Compiler les traductions
python3 manage.py compilemessages

# Collecter les fichiers statiques
python3 manage.py collectstatic --no-input --settings=config.settings.production
```

### 5. **Redémarrage du Service**
```bash
# Redémarrer le service
sudo systemctl restart martialcomp.service

# Vérifier le statut
sudo systemctl status martialcomp.service
```

## ⚠️ POINTS D'ATTENTION

1. **Dépendances** : S'assurer que toutes les dépendances sont installées
2. **Permissions** : Vérifier que les fichiers appartiennent à `www-data:www-data`
3. **Migrations** : Appliquer les migrations avant le redémarrage
4. **Logs** : Surveiller les logs après redémarrage

## 🔍 VÉRIFICATIONS POST-DÉPLOIEMENT

1. **Service** : `sudo systemctl status martialcomp.service`
2. **Site** : `curl -I https://martialcomp.com/`
3. **Logs** : `sudo journalctl -u martialcomp.service -f`
4. **Admin** : Accéder à https://martialcomp.com/admin/

## 📊 STATISTIQUES

- **Fichiers Python** : 65 fichiers
- **Templates HTML** : 19 fichiers
- **Fichiers de configuration** : 6 fichiers
- **Fichiers de données** : 2 fichiers JSON
- **Taille totale** : ~245 KB

---

**Créé par** : Assistant Claude  
**Date** : 13 Octobre 2025  
**Statut** : Prêt pour déploiement