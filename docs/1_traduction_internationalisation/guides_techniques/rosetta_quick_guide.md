# 🚀 GUIDE RAPIDE ROSETTA - MARTIALCOMP

## Accès à Rosetta

1. **Démarrer le serveur**:
   ```bash
   cd /mnt/c/martial_hub_django/martialcomp
   python manage.py runserver
   ```

2. **Se connecter en admin**:
   - URL: http://localhost:8000/admin/
   - Utilisateur: superuser
   - Créer si nécessaire: `python manage.py createsuperuser`

3. **Accéder à Rosetta**:
   - URL: http://localhost:8000/rosetta/
   - Sélectionner la langue à traduire

## Langues disponibles

| Code | Langue | Statut | Entrées |
|------|--------|--------|---------|
| es   | Español | ✅ 440 | Complet |
| pt   | Português | ✅ 417 | Complet |
| no   | Norsk | ✅ 438 | Complet |
| en   | English | ✅ 276 | Complet |
| it   | Italiano | ✅ 283 | Complet |
| de   | Deutsch | ✅ 249 | Complet |
| ar   | العربية | ✅ 268 | Complet |

## Workflow de traduction

1. **Sélectionner** la langue dans la liste déroulante
2. **Filtrer** par statut: "Untranslated", "Fuzzy", etc.
3. **Traduire** les entrées une par une
4. **Sauvegarder** (Rosetta compile automatiquement)
5. **Tester** sur le site en changeant l'URL (ex: /es/, /pt/)

## Templates par priorité

### 🔥 PRIORITÉ HAUTE (Pages principales)
- `competitions/templates/competitions/welcome.html` (239 traductions)
- `competitions/templates/competitions/dashboard/` (tableaux de bord)
- `competitions/templates/competitions/auth/` (authentification)

### 📋 PRIORITÉ MOYENNE (Gestion)
- `competitions/templates/competitions/management/`
- `finances/templates/finances/`
- `grades/templates/grades/`

### 📊 PRIORITÉ BASSE (Administration)
- `competitions/templates/admin/`
- Templates de configuration

## Commandes utiles

```bash
# Mettre à jour les traductions depuis le code
python manage.py makemessages --all

# Compiler manuellement
python manage.py compilemessages

# Vérifier les traductions
python manage.py check

# Tester les langues
# http://localhost:8000/es/  (Espagnol)
# http://localhost:8000/pt/  (Portugais)
# http://localhost:8000/no/  (Norvégien)
```

## Dépannage

### Problème: Pas de langues dans la liste
```bash
# Vérifier la configuration
python /root/test_rosetta_config.py

# Redémarrer le serveur
python manage.py runserver
```

### Problème: Traductions non visibles
```bash
# Recompiler
python manage.py compilemessages

# Vider le cache
python manage.py collectstatic --clear
```

### Problème: Erreurs de compilation
```bash
# Vérifier les fichiers .po
msgfmt --check locale/es/LC_MESSAGES/django.po
msgfmt --check locale/pt/LC_MESSAGES/django.po
msgfmt --check locale/no/LC_MESSAGES/django.po
```

## Support
- 📖 Doc Rosetta: https://django-rosetta.readthedocs.io/
- 🌐 Django i18n: https://docs.djangoproject.com/en/stable/topics/i18n/
