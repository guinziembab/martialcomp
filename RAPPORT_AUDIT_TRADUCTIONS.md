# Rapport d'Audit des Traductions - Templates Competitions

## Date: 2025-11-18

## Résumé Exécutif
Audit complet des traductions dans les templates de `apps/competitions/templates` pour identifier et corriger les textes hardcodés en français qui apparaissaient même en mode anglais.

## Problèmes Identifiés et Corrigés

### ✅ 1. Template `dashboard/club.html`

**Problèmes trouvés:**
- Ligne 1176: `Date non définie` (hardcodé en français)
- Ligne 1177: `default:"Non défini"` (hardcodé en français)
- Ligne 1730: `Date non définie` (hardcodé en français)
- Ligne 1731: `default:"Non défini"` (hardcodé en français)

**Corrections appliquées:**
```django
<!-- Avant -->
{% if competition.start_date %}{{ competition.start_date|date:"d M Y" }}{% else %}Date non définie{% endif %}
{{ competition.location|default:"Non défini" }}

<!-- Après -->
{% if competition.start_date %}{{ competition.start_date|date:"d M Y" }}{% else %}{% trans "Date non définie" %}{% endif %}
{{ competition.location|default:_("Non défini") }}
```

### ✅ 2. Template `competition_management_detail.html`

**Problèmes trouvés:**
- Ligne 399: `default:"À définir"` (hardcodé en français)

**Corrections appliquées:**
```django
<!-- Avant -->
{{ competition.venue_name|default:"À définir" }}

<!-- Après -->
{{ competition.venue_name|default:_("À définir") }}
```

### ✅ 3. Template `combat/interface_combat_v2.html`

**Problèmes trouvés:**
- Ligne 464: `default:"Compétition"` (hardcodé en français)
- Ligne 511: `default:"ROUGE"` (hardcodé en français)
- Ligne 513: `default:"ÉQUIPE ROUGE"` (hardcodé en français)
- Ligne 640: `default:"BLANC"` (hardcodé en français)
- Ligne 642: `default:"ÉQUIPE BLANCHE"` (hardcodé en français)

**Corrections appliquées:**
```django
<!-- Avant -->
{{ combat.competition.name|default:"Compétition" }}
{{ combat.equipe_rouge.nom|default:"ÉQUIPE ROUGE" }}
{{ combat.equipe_blanc.nom|default:"ÉQUIPE BLANCHE" }}

<!-- Après -->
{{ combat.competition.name|default:_("Compétition") }}
{{ combat.equipe_rouge.nom|default:_("ÉQUIPE ROUGE") }}
{{ combat.equipe_blanc.nom|default:_("ÉQUIPE BLANCHE") }}
```

## Méthodologie de Correction

### Règles appliquées:
1. **Pour les textes dans les blocs conditionnels**: Utilisation de `{% trans "..." %}`
2. **Pour les valeurs par défaut dans les filtres**: Utilisation de `default:_("...")`
3. **Vérification que `{% load i18n %}` est présent** dans tous les templates modifiés

### Exemples de patterns corrigés:
- `{% else %}Date non définie{% endif %}` → `{% else %}{% trans "Date non définie" %}{% endif %}`
- `|default:"Non défini"` → `|default:_("Non défini")`
- `|default:"À définir"` → `|default:_("À définir")`

## Fichiers Modifiés

1. ✅ `apps/competitions/templates/competitions/dashboard/club.html`
2. ✅ `apps/competitions/templates/competitions/club/competition_management_detail.html`
3. ✅ `apps/competitions/templates/competitions/combat/interface_combat_v2.html`

## Prochaines Étapes

### À faire:
1. ✅ Vérifier que toutes les traductions sont présentes dans `locale/en/LC_MESSAGES/django.po`
2. ⏳ Exécuter `python manage.py makemessages -l en` pour mettre à jour les fichiers de traduction
3. ⏳ Exécuter `python manage.py compilemessages` pour compiler les traductions
4. ⏳ Tester en production avec la langue anglaise pour vérifier que tous les textes sont traduits

### Fichiers à surveiller (non modifiés car backups ou non utilisés):
- Templates avec `.backup`, `.new`, `_OLD` dans leur nom (non utilisés en production)
- Templates de combat alternatifs (v2_backup, v2_new, etc.)

## Notes Importantes

1. **Fichiers de backup**: Tous les fichiers avec `.backup`, `.new`, `_OLD` dans leur nom ne sont pas utilisés en production et n'ont pas été modifiés.

2. **Templates actifs**: Seuls les templates actifs utilisés en production ont été modifiés.

3. **Traductions manquantes**: Si certaines traductions n'apparaissent pas en anglais, il faudra les ajouter manuellement dans `locale/en/LC_MESSAGES/django.po`.

## Tests Recommandés

1. Tester la page `https://martialcomp.com/en/competitions/dashboard/club/` en anglais
2. Tester la page `https://martialcomp.com/en/competitions/club/competitions/4/manage/` en anglais
3. Vérifier que tous les textes "Non défini", "À définir", "Date non définie" apparaissent en anglais
4. Vérifier que les textes des combats apparaissent en anglais

## Conclusion

Les principaux templates utilisés en production ont été corrigés. Les textes hardcodés en français ont été remplacés par des tags de traduction appropriés. Il reste à mettre à jour les fichiers de traduction et à compiler les messages pour que les traductions prennent effet.
