# Éléments essentiels à transférer en production

## Structure de base Django
- `manage.py`
- `requirements.txt` ou `Pipfile`
- `config/` (tous les fichiers de configuration)
  - `settings/` (notamment production.py)
  - `urls.py`
  - `wsgi.py`
  - `asgi.py`

## Applications Django
- `apps/` (tout le dossier avec le code source)
  - Tous les sous-dossiers d'applications
  - Migrations (dossiers `migrations/`)
  - Fichiers Python (.py)
  - Templates HTML

## Ressources statiques et médias
- `static/` (fichiers CSS, JS, images statiques)
- `media/` (uploads utilisateurs - à vérifier selon besoins)
- `templates/` (templates globaux)

## Configuration et dépendances
- `.env` ou fichiers de variables d'environnement
- `locale/` (si multilinguisme activé)
- Fichiers de configuration serveur (nginx, gunicorn, etc.)

## Fichiers racine importants
- `__init__.py` (tous les fichiers nécessaires)
- Fichiers de configuration Docker (si utilisé)
- Scripts de déploiement personnalisés

## À EXCLURE absolument
- Environnements virtuels (venv, env, .venv)
- Fichiers compilés Python (__pycache__, *.pyc)
- Base de données SQLite de développement
- Logs de développement
- Archives et backups
- Dossier .git (sauf si déploiement via Git)
- Fichiers temporaires et de test
- Documentation de développement (.md temporaires)