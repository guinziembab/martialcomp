# Rapport de Correction - Template Manage Categories

## Date: 2025-11-18

## Page concernée
`https://martialcomp.com/en/competitions/competitions/4/manage-categories/`

## Template
`apps/competitions/templates/competitions/club/competition_management_simple.html`

## Corrections appliquées

### ✅ Ligne 247: Description par défaut
**Avant:**
```django
<p>{{ type.description|default:"Aucune description" }}</p>
```

**Après:**
```django
<p>{{ type.description|default:_("Aucune description") }}</p>
```

### ✅ Lignes 301-303: Texte "ans" hardcodé
**Avant:**
```django
{% if category.min_age %}{{ category.min_age }} ans{% endif %}
{% if category.min_age and category.max_age %} - {% endif %}
{% if category.max_age %}{{ category.max_age }} ans{% endif %}
```

**Après:**
```django
{% if category.min_age %}{{ category.min_age }} {% trans "ans" %}{% endif %}
{% if category.min_age and category.max_age %} - {% endif %}
{% if category.max_age %}{{ category.max_age }} {% trans "ans" %}{% endif %}
```

### ✅ Ligne 330: Texte "ans" déjà traduit
Le texte "ans" à la ligne 330 était déjà correctement traduit avec `{% trans "ans" %}`.

### ✅ Ligne 332: Valeur par défaut "-"
**Avant:**
```django
{% else %}
    -
{% endif %}
```

**Après:**
```django
{% else %}
    {% trans "-" %}
{% endif %}
```

## Vérification

### Textes déjà correctement traduits ✅
Le template utilise déjà `{% trans %}` pour la plupart des textes :
- Tous les titres et labels
- Tous les messages d'alerte
- Tous les boutons
- Tous les messages JavaScript

### Textes corrigés ✅
- `default:"Aucune description"` → `default:_("Aucune description")`
- `ans` (hardcodé) → `{% trans "ans" %}`
- `-` (hardcodé) → `{% trans "-" %}`

## Résumé

Tous les textes français dans le template `competition_management_simple.html` sont maintenant correctement balisés avec les tags de traduction appropriés :
- `{% trans "..." %}` pour les textes dans les blocs
- `default:_("...")` pour les valeurs par défaut dans les filtres

## Prochaines étapes

1. Mettre à jour les traductions :
   ```bash
   python manage.py makemessages -l en
   python manage.py compilemessages
   ```

2. Tester en production :
   - Vérifier que tous les textes apparaissent en anglais sur `https://martialcomp.com/en/competitions/competitions/4/manage-categories/`
   - Vérifier que les valeurs par défaut ("Aucune description", "ans", "-") sont traduites
