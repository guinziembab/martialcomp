# 📋 RUNBOOK - Correction Erreur Practitioner Production

## 🎯 Problème
- **Erreur** : `DoesNotExist: Discipline matching query does not exist`
- **URL** : `/fr/admin/competitions/practitioner/`
- **Cause** : Table `competitions_discipline` vide en production

## 🚀 Plan de correction

### Étape 1 : Diagnostic (5 min)
```bash
# Se connecter au serveur
ssh user@martialcomp.com

# Aller dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement virtuel
source venv/bin/activate

# Copier le script de diagnostic
# (depuis votre machine locale)
scp check_disciplines_production.py user@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/

# Exécuter le diagnostic
python check_disciplines_production.py
```

### Étape 2 : Correction (10 min)

#### Option A : Si `load_disciplines` existe
```bash
# Appliquer les migrations manquantes
python manage.py migrate --settings=config.settings.production

# Charger les disciplines
python manage.py load_disciplines --settings=config.settings.production

# Vérifier
python manage.py shell --settings=config.settings.production -c \
  "from apps.competitions.models import Discipline; print(f'Disciplines: {Discipline.objects.count()}')"
```

#### Option B : Utiliser le script de correction
```bash
# Copier le script
scp fix_disciplines_production.py user@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/

# Exécuter
python fix_disciplines_production.py
```

#### Option C : Correction manuelle rapide
```bash
python manage.py shell --settings=config.settings.production

>>> from apps.competitions.models import Discipline
>>> 
>>> # Créer les disciplines essentielles
>>> disciplines = [
...     'Karaté', 'Judo', 'Taekwondo', 'Aikido', 
...     'Kung Fu', 'Boxe', 'MMA', 'Long Phai'
... ]
>>> 
>>> for name in disciplines:
...     Discipline.objects.get_or_create(
...         name=name, 
...         defaults={'is_active': True, 'description': f'Art martial {name}'}
...     )
>>> 
>>> print(f"✅ {Discipline.objects.count()} disciplines en base")
>>> exit()
```

### Étape 3 : Test (5 min)

#### 3.1 Test via shell (sûr)
```bash
python manage.py shell --settings=config.settings.production

>>> from apps.competitions.models import Practitioner
>>> from apps.organizations.models import Organization
>>> 
>>> # Test création sans discipline
>>> org = Organization.objects.first()
>>> p = Practitioner.objects.create(
...     first_name="Test",
...     last_name="NoDiscipline",
...     organization=org
... )
>>> print(f"✅ Practitioner créé: {p.id}")
>>> p.delete()  # Nettoyer
>>> exit()
```

#### 3.2 Test de l'URL (avec précaution)
```bash
# Retirer temporairement le blocage
nano config/settings/production.py

# Commenter la ligne du middleware:
# 'apps.core.middleware.block_practitioner.BlockPractitionerMiddleware',

# Sauvegarder et redémarrer
systemctl restart apache2

# Tester l'URL dans le navigateur
# https://martialcomp.com/fr/admin/competitions/practitioner/

# Si OK, garder décommenté
# Si KO, recommenter et redémarrer
```

### Étape 4 : Finalisation

#### Si tout fonctionne
1. Laisser le middleware décommenté
2. Réactiver l'admin practitioner si nécessaire :
   ```python
   # Dans apps/competitions/admin/__init__.py
   from . import practitioner  # Décommenter si commenté
   ```

#### Si l'erreur persiste
1. Recommenter le middleware
2. Investiguer plus en profondeur :
   ```bash
   # Chercher les get() problématiques
   grep -r "Discipline.objects.get" apps/competitions/admin/
   ```

## 🔍 Vérifications post-correction

```bash
# 1. Compter les disciplines
python manage.py shell --settings=config.settings.production -c \
  "from apps.competitions.models import Discipline; \
   print(f'Disciplines actives: {Discipline.objects.filter(is_active=True).count()}')"

# 2. Lister les disciplines
python manage.py shell --settings=config.settings.production -c \
  "from apps.competitions.models import Discipline; \
   [print(f'- {d.name}') for d in Discipline.objects.all()[:10]]"

# 3. Vérifier les logs Apache
tail -f /var/log/apache2/error.log
```

## ⚡ Commande one-liner d'urgence

```bash
# Créer au moins une discipline pour débloquer
python manage.py shell --settings=config.settings.production -c \
  "from apps.competitions.models import Discipline; \
   Discipline.objects.get_or_create(name='Karaté', defaults={'is_active': True}); \
   print(f'OK: {Discipline.objects.count()} discipline(s)')"
```

## 📞 Escalade

Si après toutes ces étapes le problème persiste :
1. Vérifier les filtres de session admin
2. Clear le cache Django : `python manage.py clear_cache`
3. Examiner le traceback complet dans les logs Apache
4. Contacter le support avec :
   - Le nombre de disciplines en base
   - Le traceback complet
   - La version exacte de Django (5.1.6)