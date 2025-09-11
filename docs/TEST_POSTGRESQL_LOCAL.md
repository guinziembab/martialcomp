# Test de la correction PostgreSQL en local

## Prérequis

1. **Installer PostgreSQL localement**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Télécharger depuis https://www.postgresql.org/download/windows/
```

2. **Créer une base de données de test**
```bash
sudo -u postgres createdb martialcomp_test
sudo -u postgres psql -c "CREATE USER martialcomp WITH PASSWORD 'testpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE martialcomp_test TO martialcomp;"
```

## Configuration

1. **Créer un fichier de settings pour PostgreSQL**
```python
# config/settings_postgresql_test.py
from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_test',
        'USER': 'martialcomp',
        'PASSWORD': 'testpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Désactiver les logs pour les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}
```

## Tests étape par étape

### Étape 1: Migration initiale
```bash
# Utiliser les settings PostgreSQL
export DJANGO_SETTINGS_MODULE=config.settings_postgresql_test

# Créer les tables
python manage.py migrate

# Vérifier la structure
python check_postgresql_column.py
```

### Étape 2: Simuler le problème
```bash
# Se connecter à PostgreSQL
psql -h localhost -U martialcomp -d martialcomp_test

# Supprimer la colonne pour simuler le problème
ALTER TABLE competitions_technicalscoreresult DROP COLUMN IF EXISTS is_training_score;

# Vérifier que la colonne n'existe plus
\d competitions_technicalscoreresult
```

### Étape 3: Tester la correction
```bash
# Appliquer la migration de correction
python manage.py migrate competitions 0007

# Vérifier que la correction fonctionne
python check_postgresql_column.py

# Tester l'accès au modèle
python manage.py shell -c "
from competitions.models.scoring_results import TechnicalScoreResult
print('Test réussi:', TechnicalScoreResult.objects.filter(is_training_score=False).count())
"
```

### Étape 4: Test de régression
```bash
# Revenir en arrière
python manage.py migrate competitions 0006

# Appliquer à nouveau
python manage.py migrate competitions 0007

# Vérifier que tout fonctionne toujours
python check_postgresql_column.py
```

## Vérifications finales

1. **Test de l'interface admin**
```bash
python manage.py createsuperuser
python manage.py runserver

# Accéder à http://localhost:8000/admin/auth/user/
# Vérifier qu'aucune erreur ne s'affiche
```

2. **Test des requêtes**
```python
# Dans le shell Django
from competitions.models.scoring_results import TechnicalScoreResult
from django.contrib.auth.models import User

# Test des relations
user = User.objects.first()
scores = user.technical_score_results.all()
print(f"Relations OK: {scores.count()} scores")

# Test des filtres
training_scores = TechnicalScoreResult.objects.filter(is_training_score=True)
regular_scores = TechnicalScoreResult.objects.filter(is_training_score=False)
print(f"Filtres OK: {training_scores.count()} formation, {regular_scores.count()} réguliers")
```

## Nettoyage

```bash
# Supprimer la base de test
sudo -u postgres dropdb martialcomp_test
sudo -u postgres dropuser martialcomp
```