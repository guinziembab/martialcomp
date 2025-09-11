
# 🛠️ GUIDE DE DÉPANNAGE ROSETTA

## Problème: Impossible de sélectionner la langue

### Solution 1: Vérifier les permissions
```bash
# Créer un superuser si nécessaire
python manage.py createsuperuser

# Se connecter avec le superuser sur /admin/
# Puis aller sur /rosetta/
```

### Solution 2: Vérifier la configuration
```python
# Dans settings/base.py, vérifier:
USE_I18N = True
USE_L10N = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('pt', 'Português'),
    ('no', 'Norsk'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('ar', 'العربية'),
]

ROSETTA_LANGUAGES = [
    ('es', 'Español'),
    ('pt', 'Português'), 
    ('no', 'Norsk'),
]
```

### Solution 3: Regénérer les fichiers de traduction
```bash
# Supprimer les anciens fichiers
rm -rf locale/*/LC_MESSAGES/django.mo

# Regénérer
python manage.py makemessages --all
python manage.py compilemessages
```

### Solution 4: Vérifier les fichiers .po
- Les fichiers .po doivent être valides (pas de doublons)
- L'encodage doit être UTF-8
- Les headers doivent être corrects

### Solution 5: Redémarrer le serveur
```bash
# Arrêter le serveur (Ctrl+C)
# Redémarrer
python manage.py runserver
```

## URLs de test
- Rosetta: http://localhost:8000/rosetta/
- Admin: http://localhost:8000/admin/
- Site ES: http://localhost:8000/es/
- Site PT: http://localhost:8000/pt/
- Site NO: http://localhost:8000/no/
