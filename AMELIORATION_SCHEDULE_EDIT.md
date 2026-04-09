# Amélioration du template de gestion de planning

## Date : 12 novembre 2024

## Objectif

Rendre tous les paramètres du planning configurables et ajustables, notamment :
- Le nombre de tatamis
- Les durées des matchs
- Les temps de pause entre matchs
- Les horaires spéciaux (pause, pesée, briefing, cérémonie)

---

## Problèmes identifiés

### 1. Formulaire incorrect
**Problème** : Le formulaire `CompetitionScheduleForm` utilisait le mauvais modèle (`Competition` au lieu de `CompetitionSchedule`) et ne contenait pas tous les champs configurables.

**Solution** : Correction du formulaire pour utiliser le bon modèle et inclure tous les champs.

### 2. Champs manquants dans le template
**Problème** : Le template n'affichait pas tous les paramètres configurables disponibles dans le modèle.

**Solution** : Ajout de tous les champs configurables dans le template.

### 3. Nom de champ incorrect
**Problème** : Le template utilisait `transition_time` alors que le modèle utilise `break_between_matches`.

**Solution** : Correction du nom du champ dans le template.

---

## Corrections appliquées

### 1. Formulaire `CompetitionScheduleForm` (`apps/competitions/forms/schedule.py`)

**Avant** :
```python
class CompetitionScheduleForm(forms.ModelForm):
    class Meta:
        model = Competition  # ❌ Mauvais modèle
        fields = ['start_date', 'end_date', 'start_time', 'end_time']  # ❌ Champs limités
```

**Après** :
```python
class CompetitionScheduleForm(forms.ModelForm):
    class Meta:
        model = CompetitionSchedule  # ✅ Bon modèle
        fields = [
            'start_time', 'end_time',
            'break_start', 'break_end',
            'weigh_in_start', 'weigh_in_end',
            'briefing_time', 'awards_ceremony_time',
            'tatami_count',
            'match_duration', 'break_between_matches',
            'notes'
        ]  # ✅ Tous les champs configurables
```

**Améliorations** :
- ✅ Utilisation du bon modèle `CompetitionSchedule`
- ✅ Inclusion de tous les champs configurables
- ✅ Widgets appropriés pour chaque type de champ
- ✅ Help text pour guider l'utilisateur
- ✅ Validation avec min/max pour les champs numériques

### 2. Template `edit_competition_schedule.html`

**Ajouts** :
- ✅ Section "Horaires spéciaux" avec tous les champs :
  - Pause (début et fin)
  - Pesée (début et fin)
  - Briefing
  - Cérémonie de remise des prix
- ✅ Correction du nom de champ `transition_time` → `break_between_matches`
- ✅ Organisation claire des champs par sections

**Sections du formulaire** :
1. **Horaires généraux** : Début et fin de la compétition
2. **Configuration des tatamis** : Nombre de tatamis (1-10)
3. **Paramètres des matchs** :
   - Durée par défaut des matchs (minutes)
   - Temps de pause entre les matchs (minutes)
4. **Horaires spéciaux** (NOUVEAU) :
   - Pause déjeuner (début/fin)
   - Pesée (début/fin)
   - Briefing des juges
   - Cérémonie de remise des prix
5. **Notes et commentaires**

---

## Paramètres maintenant configurables

### Paramètres principaux
- ✅ **Nombre de tatamis** : 1 à 10 (configurable)
- ✅ **Heure de début** : Configurable
- ✅ **Heure de fin** : Configurable

### Durées des matchs
- ✅ **Durée par défaut des matchs** : 1 à 60 minutes (configurable)
- ✅ **Temps de pause entre matchs** : 0 à 30 minutes (configurable)

### Horaires spéciaux
- ✅ **Pause déjeuner** : Début et fin (optionnel)
- ✅ **Pesée** : Début et fin avec date/heure (optionnel)
- ✅ **Briefing** : Heure (optionnel)
- ✅ **Cérémonie** : Heure (optionnel)

### Autres
- ✅ **Notes** : Champ texte libre pour les commentaires

---

## Fichiers modifiés

1. **`apps/competitions/forms/schedule.py`**
   - Correction du modèle utilisé
   - Ajout de tous les champs configurables
   - Ajout de help_text et validation

2. **`apps/competitions/templates/competitions/management/edit_competition_schedule.html`**
   - Correction du nom de champ `transition_time` → `break_between_matches`
   - Ajout de la section "Horaires spéciaux"
   - Organisation améliorée des champs

---

## Validation et contraintes

### Nombre de tatamis
- Minimum : 1
- Maximum : 10
- Type : Entier

### Durée des matchs
- Minimum : 1 minute
- Maximum : 60 minutes
- Type : Entier

### Pause entre matchs
- Minimum : 0 minute
- Maximum : 30 minutes
- Type : Entier

### Horaires
- Format : HH:MM pour les heures
- Format : YYYY-MM-DDTHH:MM pour les dates/heures (pesée)

---

## Utilisation

### Accès
```
/fr/competitions/management/schedule/<competition_id>/edit/
```

### Fonctionnalités
1. **Configuration du nombre de tatamis** :
   - Augmentation : Crée automatiquement de nouveaux tatamis
   - Réduction : Déplace les catégories vers le tatami 1

2. **Configuration des durées** :
   - Utilisées pour l'estimation automatique des créneaux horaires
   - Peuvent être ajustées manuellement par catégorie ensuite

3. **Horaires spéciaux** :
   - Tous optionnels
   - Permettent de planifier les événements importants de la compétition

---

## Tests à effectuer

1. ✅ Vérifier que le formulaire s'affiche correctement avec tous les champs
2. ✅ Tester la modification du nombre de tatamis (augmentation et réduction)
3. ✅ Tester la modification des durées des matchs
4. ✅ Tester l'ajout des horaires spéciaux
5. ✅ Vérifier que les données sont bien sauvegardées
6. ✅ Vérifier que les catégories sont correctement réaffectées lors de la réduction du nombre de tatamis

---

## Notes importantes

- **Modification du nombre de tatamis** : Si le nombre est réduit, les catégories planifiées sur les tatamis supprimés sont automatiquement déplacées vers le tatami 1.
- **Durées par défaut** : Ces durées sont utilisées pour l'estimation automatique, mais peuvent être ajustées manuellement pour chaque catégorie.
- **Horaires spéciaux** : Tous les champs sont optionnels et peuvent être laissés vides si non nécessaires.

---

## Résultat

✅ **Tous les paramètres sont maintenant configurables et ajustables** :
- Nombre de tatamis : ✅ Configurable (1-10)
- Durées des matchs : ✅ Configurable (1-60 minutes)
- Pause entre matchs : ✅ Configurable (0-30 minutes)
- Horaires spéciaux : ✅ Tous configurables (optionnels)
- Horaires généraux : ✅ Configurables

Le template permet maintenant une configuration complète et flexible du planning de la compétition.
