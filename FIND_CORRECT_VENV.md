# TROUVER ET UTILISER LE BON ENVIRONNEMENT VIRTUEL

## 1. Localiser le venv
```bash
# Chercher où se trouve le venv
find /var/www/vhosts/martialcomp.com -name "python3" -path "*/bin/*" 2>/dev/null | grep -v httpdocs/venv

# Ou chercher directement Django
find /var/www/vhosts/martialcomp.com -name "django-admin.py" 2>/dev/null

# Vérifier les processus en cours pour voir quel Python est utilisé
ps aux | grep -i python | grep martialcomp
```

## 2. Chemins probables du venv
```bash
# Tester ces chemins courants :
ls -la /var/www/vhosts/martialcomp.com/venv/bin/python3
ls -la /var/www/vhosts/martialcomp.com/env/bin/python3
ls -la /var/www/vhosts/martialcomp.com/.venv/bin/python3
ls -la /var/www/vhosts/martialcomp.com/virtualenv/bin/python3
```

## 3. Une fois le bon venv trouvé
Si par exemple le venv est dans `/var/www/vhosts/martialcomp.com/venv/` :

```bash
# Activer le bon venv
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Ou utiliser directement son Python
/var/www/vhosts/martialcomp.com/venv/bin/python3 manage.py shell --settings=config.settings.production
```

## 4. Alternative : Vérifier comment Apache/WSGI lance l'app
```bash
# Regarder la configuration Apache
cat /etc/apache2/sites-enabled/*martialcomp* | grep -i python

# Ou chercher le fichier wsgi.py
find /var/www/vhosts/martialcomp.com -name "wsgi.py" -o -name "passenger_wsgi.py" | xargs grep -l python
```

## 5. Solution directe une fois le bon Python trouvé
Remplacez `/path/to/correct/venv` par le bon chemin :

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
/path/to/correct/venv/bin/python3 manage.py shell --settings=config.settings.production << 'EOF'
from apps.competitions.models import Discipline

for name in ['Karaté', 'Judo', 'Long Phai', 'Taekwondo']:
    disc, created = Discipline.objects.get_or_create(
        name=name, 
        defaults={'is_active': True}
    )
    print(f"{'✅ Créé' if created else '⚠️  Existe'}: {name}")

print(f"\n📊 Total: {Discipline.objects.count()} disciplines")
EOF
```