# Rapport de Correction - Erreur 500 sur la page d'inscription

**Date** : 12 novembre 2025  
**Problème** : Erreur 500 sur https://martialcomp.com/fr/competitions/club/competition-registration/4/  
**Type d'erreur** : FieldError dans Django  

## Diagnostic

### Erreur identifiée
```
django.core.exceptions.FieldError: Invalid field name(s) given in select_related: 'current_grade'. 
Choices are: user, organization, grade, primary_discipline, family, medical_record, coach_profile, judge, qr_code
```

### Cause
Le modèle `Practitioner` n'a pas de champ `current_grade`. Le champ correct est `grade`.

### Localisation de l'erreur
- **Fichier** : `apps/competitions/views/club/registration_api.py`
- **Ligne** : 111 (dans la requête QuerySet)
- **Template** : `competition_registration_simple.html` (lignes 537, 572)

## Solution appliquée

### 1. Correction dans registration_api.py
```python
# Avant
.select_related('current_grade')

# Après  
.select_related('grade')
```

### 2. Correction dans le template
```html
<!-- Avant -->
{{ practitioner.current_grade }}

<!-- Après -->
{{ practitioner.grade }}
```

## Déploiement

### Fichiers modifiés et déployés
1. `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/registration_api.py`
2. `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_registration_simple.html`

### Résultat
- ✅ Fichiers sauvegardés avec succès
- ✅ Nouveaux fichiers déployés  
- ✅ Permissions ajustées (www-data)
- ✅ Service martialcomp.service redémarré
- ✅ Aucune erreur dans les logs après redémarrage

## Test

La page https://martialcomp.com/fr/competitions/club/competition-registration/4/ devrait maintenant s'afficher correctement sans erreur 500.

## Recommandations

1. Vérifier que le modèle `Practitioner` utilise bien le champ `grade` partout dans l'application
2. Faire une recherche globale pour remplacer toutes les occurrences de `current_grade` par `grade`
3. Ajouter des tests unitaires pour éviter ce type d'erreur à l'avenir