# 📋 Rapport des Erreurs Production - 19 Octobre 2025

## 🔴 Erreurs Identifiées et Corrigées

### 1. ✅ Erreur Logout (500)
**Problème:** La page `/accounts/logout/` retournait une erreur 500  
**Cause:** `ACCOUNT_LOGOUT_ON_GET` était sur `False`, nécessitant un POST  
**Solution:** 
- Modifié `ACCOUNT_LOGOUT_ON_GET = True` dans `config/settings/base.py`
- Créé une vue de logout personnalisée en backup
- **Status:** ✅ CORRIGÉ

### 2. ✅ Erreur Disciplines Fédération  
**Problème:** Les cases à cocher des disciplines ne s'affichaient pas lors de la création d'une fédération  
**Cause:** Le champ `disciplines` n'était pas dans `Meta.fields` de `FederationCreationForm`  
**Solution:**
- Ajouté `'disciplines'` dans la liste `Meta.fields`
- **Status:** ✅ CORRIGÉ

### 3. ⚠️ Erreur Page d'Accueil (500)
**Problème:** La page `https://martialcomp.com/fr/` retourne une erreur 500  
**Causes identifiées:**
1. Module `apps.utils` manquant → ✅ Créé
2. `apps.utils.decorators` manquant → ✅ Créé avec `federation_admin_required`
3. `apps.models` manquant → ✅ Créé fichier temporaire
4. `federation_list` manquant dans `apps.competitions.views.federations`

**Status:** ⚠️ EN COURS - Nécessite investigation supplémentaire

## 📁 Fichiers Créés/Modifiés

### Nouveaux fichiers créés:
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/utils/__init__.py`
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/utils/helpers.py`
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/utils/decorators.py`
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/models.py` (temporaire)
- `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/custom_logout.py`

### Fichiers modifiés:
- `config/settings/base.py` - `ACCOUNT_LOGOUT_ON_GET = True`
- `apps/competitions/forms/onboarding.py` - Ajout de `'disciplines'` dans Meta.fields

## 🚨 Actions Recommandées

### Pour l'erreur de la page d'accueil:
1. **Examiner le fichier federations.py** pour voir si `federation_list` est défini
2. **Vérifier les URLs** pour voir quelle vue est censée gérer la page d'accueil
3. **Consulter les logs complets** pour avoir le traceback complet de l'erreur

### Script de diagnostic suggéré:
```bash
# Sur le serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs
grep -n "def federation_list" apps/competitions/views/federations.py
grep -n "federation_list" config/urls.py apps/competitions/urls/*.py
tail -100 logs/django.log | grep -A20 "Internal Server Error"
```

## 📊 État Global

| Composant | État | Notes |
|-----------|------|--------|
| Logout | ✅ | Fonctionne avec GET |
| Disciplines Fédération | ✅ | Cases à cocher affichées |
| Page d'accueil | ❌ | Erreur d'import |
| Module utils | ✅ | Créé avec succès |

## 🔄 Prochaines Étapes

1. Identifier pourquoi `federation_list` est importé mais n'existe pas
2. Vérifier la configuration des URLs de la page d'accueil
3. Possiblement créer la vue manquante ou corriger l'import

## 📝 Notes

- Le serveur utilise Plesk avec Gunicorn + Apache
- Structure du projet : `/var/www/vhosts/martialcomp.com/httpdocs/`
- Services : `martialcomp.service` et Apache2
- Environnement virtuel : `/var/www/vhosts/martialcomp.com/venv/`