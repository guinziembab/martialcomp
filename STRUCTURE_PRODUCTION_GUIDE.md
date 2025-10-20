# Guide de Structure pour le Déploiement en Production

## 🏗️ Structure Actuelle (Développement)
```
/mnt/c/martial_hub_django/martialcomp/
├── manage.py
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   ├── competitions/
│   ├── finances/
│   ├── organizations/
│   ├── shop/
│   └── ... (autres apps)
├── templates/
├── static/
├── media/
├── locale/
└── logs/
```

## 📦 Structure Attendue en Production

### Option 1: Installation Standard Django
```
/var/www/martialcomp/           # ou /home/user/martialcomp/
├── manage.py
├── requirements.txt
├── config/
├── apps/
├── templates/
├── static/                      # Fichiers statiques de développement
├── staticfiles/                 # Fichiers statiques collectés (collectstatic)
├── media/                       # Uploads utilisateurs
├── locale/
└── logs/
```

### Option 2: Structure avec Séparation Code/Données
```
/opt/martialcomp/                # Code source (lecture seule)
├── manage.py
├── requirements.txt
├── config/
├── apps/
└── templates/

/var/lib/martialcomp/            # Données persistantes
├── media/
├── staticfiles/
└── logs/
```

## ⚙️ Chemins Critiques dans la Configuration

### BASE_DIR
- **Développement**: `/mnt/c/martial_hub_django/martialcomp/`
- **Production**: Variable selon installation (ex: `/var/www/martialcomp/`)
- **Définition**: `Path(__file__).resolve().parent.parent.parent`

### Chemins Relatifs (depuis BASE_DIR)
- **STATIC_ROOT**: `os.path.join(BASE_DIR, 'staticfiles')`
- **MEDIA_ROOT**: `os.path.join(BASE_DIR, 'media')`
- **Logs**: `os.path.join(BASE_DIR, 'logs')`
- **Templates**: `BASE_DIR / 'templates'`
- **Locale**: `BASE_DIR / 'locale'`

## 🔧 Variables d'Environnement Requises

```bash
# Base de données
DB_NAME=martialcomp_prod
DB_USER=martialcomp_user
DB_PASSWORD=xxx
DB_HOST=localhost
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=xxx
ALLOWED_HOSTS=example.com,www.example.com

# Chemins (optionnel, si différent de la structure par défaut)
# STATIC_ROOT=/var/www/martialcomp/static
# MEDIA_ROOT=/var/www/martialcomp/media
```

## ⚠️ Points d'Attention

1. **BASE_DIR Dynamique**: Le code utilise `Path(__file__)` donc s'adapte automatiquement au chemin d'installation

2. **Permissions**: 
   - `staticfiles/`: Écriture pour Django (collectstatic)
   - `media/`: Écriture pour Django (uploads)
   - `logs/`: Écriture pour Django (logs)

3. **Serveur Web (Nginx)**:
   - `/static/` → `staticfiles/`
   - `/media/` → `media/`

4. **Éviter les Chemins Absolus**: Le projet utilise des chemins relatifs à BASE_DIR, donc portable

## 📋 Checklist Pré-Déploiement

- [ ] Définir le répertoire d'installation cible
- [ ] Vérifier les permissions du serveur web
- [ ] Configurer les variables d'environnement
- [ ] S'assurer que l'utilisateur du serveur peut écrire dans media/, logs/, staticfiles/
- [ ] Adapter la configuration Nginx/Apache selon les chemins choisis