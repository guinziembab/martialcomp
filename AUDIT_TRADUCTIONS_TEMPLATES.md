# Audit des Traductions - Templates Competitions

## Date: 2025-11-18

## Résumé
Audit complet des traductions dans les templates de `apps/competitions/templates` pour identifier et corriger les textes hardcodés en français qui ne sont pas traduits.

## Problèmes identifiés

### 1. Templates principaux corrigés ✅

#### `apps/competitions/templates/competitions/dashboard/club.html`
- **Ligne 1176**: `Date non définie` → Corrigé en `{% trans "Date non définie" %}`
- **Ligne 1177**: `default:"Non défini"` → Corrigé en `default:_("Non défini")`
- **Ligne 1730**: `Date non définie` → Corrigé en `{% trans "Date non définie" %}`
- **Ligne 1731**: `default:"Non défini"` → Corrigé en `default:_("Non défini")`

#### `apps/competitions/templates/competitions/club/competition_management_detail.html`
- **Ligne 399**: `default:"À définir"` → Corrigé en `default:_("À définir")`

### 2. Templates à vérifier/corriger

#### Templates de combat
- `apps/competitions/templates/competitions/combat/interface_combat_v2.html`
- `apps/competitions/templates/competitions/combat/interface_combat.html`
- `apps/competitions/templates/competitions/combat_taekwondo/interface_combat.html`
- `apps/competitions/templates/competitions/combat_taekwondo/detail_combat.html`

**Textes trouvés:**
- `default:"Équipe Rouge"` / `default:"ÉQUIPE ROUGE"`
- `default:"Équipe Bleue"` / `default:"Équipe Blanche"` / `default:"ÉQUIPE BLANCHE"`
- `default:"Compétition"`

#### Templates de gestion
- `apps/competitions/templates/competitions/club/competition_management_pro.html`
- `apps/competitions/templates/competitions/club/competition_management_general.html`

**Textes trouvés:**
- `default:"À définir"`
- `default:"Non défini"`
- `default:"Validé"`

### 3. Fichiers de backup (à ignorer)
Tous les fichiers avec `.backup`, `.new`, `_OLD` dans leur nom ne sont pas utilisés en production et peuvent être ignorés.

## Recommandations

### Corrections appliquées
1. ✅ Utilisation de `{% trans %}` pour les textes dans les blocs conditionnels
2. ✅ Utilisation de `default:_("...")` pour les valeurs par défaut dans les filtres

### À faire
1. Vérifier et corriger les templates de combat actifs
2. Vérifier les templates de gestion de compétition
3. S'assurer que toutes les traductions sont présentes dans `locale/en/LC_MESSAGES/django.po`
4. Exécuter `python manage.py makemessages -l en` pour mettre à jour les fichiers de traduction
5. Exécuter `python manage.py compilemessages` pour compiler les traductions

## Notes
- Les fichiers de backup ne doivent pas être modifiés
- Se concentrer uniquement sur les fichiers actifs utilisés en production
- Tester après chaque correction pour s'assurer que les traductions fonctionnent
