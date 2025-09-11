# Guide de Traduction Internationale - Gestion des Tâches

## Vue d'ensemble

Le module de gestion des tâches Kanban a été entièrement préparé pour la traduction internationale depuis le 1er août 2025. Tous les templates, messages d'erreur, et chaînes de caractères de l'interface utilisateur utilisent le système de traduction Django `i18n`.

## Structure des Traductions

### Templates préparés pour i18n

Tous les templates utilisent les balises de traduction Django appropriées :

- `{% load i18n %}` - Charge les fonctions de traduction
- `{% trans "texte" %}` - Traduit une chaîne simple
- `{% blocktrans %}...{% endblocktrans %}` - Traduit des blocs avec variables
- `{{ variable|filter }}` - Utilise des filtres personnalisés pour les traductions

### Fichiers concernés

#### Templates principaux
- `base/kanban_base.html` - Template de base avec traductions JavaScript
- `boards/board_list.html` - Liste des tableaux
- `kanban/kanban_board.html` - Vue principale Kanban  
- `kanban/kanban_card.html` - Cartes de tâches
- `tasks/task_detail.html` - Détails des tâches
- `modals/confirm_delete.html` - Modal de confirmation
- `modals/task_quick_edit.html` - Édition rapide
- `widgets/dashboard_*_widget.html` - Widgets du tableau de bord

#### Template tags personnalisés
- `task_permissions.py` - Permissions et badges d'abonnement traduits
- `task_i18n.py` - Template tags spécialisés pour les traductions

#### Fichiers JavaScript
- Toutes les chaînes JavaScript sont traduites via le template tag `{% js_translations %}`
- Configuration centralisée des traductions dans `kanban_base.html`

## Template Tags Personnalisés

### `task_i18n.py`

Ce fichier contient des template tags spécialisés :

```python
{% load task_i18n %}

# Choix traduits pour JavaScript
{% task_status_choices %}
{% task_priority_choices %} 
{% board_type_choices %}

# Filtres de formatage
{{ hours|task_time_display }}
{{ days_diff|relative_time_display }}

# Traductions JavaScript complètes
{% js_translations %}
```

### `task_permissions.py`

Template tags pour les permissions avec traductions :

```python
{% load task_permissions %}

# Badges d'abonnement traduits
{% show_subscription_badge user %}

# Avertissements de limites traduits
{% show_feature_limit_warning user 'boards' current_count %}
```

## Génération des Fichiers de Traduction

### Commande de gestion Django

Utilisez la commande personnalisée pour générer les fichiers de traduction :

```bash
# Générer un fichier JSON en anglais
python manage.py generate_task_translations --lang en --format json

# Générer un fichier PO en espagnol  
python manage.py generate_task_translations --lang es --format po
```

### Commandes Django standard

Après avoir préparé vos traductions, utilisez les commandes Django standard :

```bash
# Extraire toutes les chaînes à traduire
python manage.py makemessages -l en
python manage.py makemessages -l es
python manage.py makemessages -l de

# Compiler les traductions
python manage.py compilemessages
```

## Chaînes de Traduction Principales

### Interface Utilisateur de Base
- Navigation : "Accueil", "Tableau de bord", "Gestion de Tâches"
- Actions : "Nouveau Tableau", "Modifier", "Supprimer", "Enregistrer"
- États : "Chargement...", "Erreur", "Succès"

### Statuts et Priorités des Tâches
- Statuts : "À faire", "En cours", "En révision", "Terminé", "Bloqué"
- Priorités : "Basse", "Moyenne", "Haute", "Urgente"

### Types de Tableaux
- "Général", "Club", "Entraînement", "Compétition", "Fédération", "Événement"

### Messages de Confirmation
- "Êtes-vous sûr de vouloir supprimer cette tâche ?"
- "Cette action est irréversible."

### Messages de Réussite/Erreur
- "Tâche créée avec succès"
- "Erreur lors de la sauvegarde"
- "Permission refusée"

### Temps et Dates
- Temps relatif : "Aujourd'hui", "Demain", "Hier"
- Formatage du temps : "1 heure", "X heures"
- États temporels : "En retard", "X jours de retard"

### Abonnements et Limites
- Niveaux : "Dojo Essentials", "Master's Circle", "Grand Champion"
- Messages de limite : "Limite atteinte", "Mettre à niveau"

## Configuration JavaScript

Toutes les traductions JavaScript sont centralisées via le template tag `{% js_translations %}` qui génère automatiquement un objet JSON contenant toutes les chaînes nécessaires :

```javascript
window.taskManagementConfig = {
    csrfToken: '{{ csrf_token }}',
    currentUser: { /* ... */ },
    urls: { /* ... */ },
    i18n: {% js_translations %}  // Toutes les traductions ici
};
```

## Bonnes Pratiques Implémentées

### 1. Séparation du Contenu et de la Logique
- Toutes les chaînes sont externalisées des fichiers Python et JavaScript
- Utilisation systématique des template tags Django

### 2. Gestion Contextuelle
- `{% blocktrans %}` pour les chaînes avec variables
- Filtres personnalisés pour le formatage spécialisé
- Template tags pour les listes de choix

### 3. Cohérence Terminologique
- Utilisation d'un dictionnaire de traduction centralisé
- Réutilisation des termes standards dans toute l'application

### 4. Fallbacks et Robustesse
- Gestion des cas où les traductions ne sont pas disponibles
- Messages d'erreur traduits pour une meilleure expérience utilisateur

## Langues Supportées

Le système est prêt pour supporter toutes les langues Django standards :

- **Français (fr)** - Langue par défaut
- **Anglais (en)** - Traduction complète fournie
- **Espagnol (es)** - Structure prête
- **Allemand (de)** - Structure prête
- **Italien (it)** - Structure prête
- **Portugais (pt)** - Structure prête

## Tests de Traduction

Pour tester les traductions :

1. Modifier la langue dans `settings.py`
2. Utiliser le middleware `LocaleMiddleware`
3. Tester avec différentes valeurs `LANGUAGE_CODE`

```python
# settings.py
LANGUAGE_CODE = 'en'  # ou 'es', 'de', etc.
USE_I18N = True
USE_L10N = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('de', 'Deutsch'),
]
```

## Conclusion

Le module de gestion des tâches est entièrement préparé pour la traduction internationale avec :

✅ **100% des templates** utilisent les balises de traduction Django  
✅ **JavaScript traduit** via template tags centralisés  
✅ **Template tags personnalisés** pour les cas spécialisés  
✅ **Commande de génération** automatique des fichiers de traduction  
✅ **Documentation complète** pour les traducteurs  
✅ **Structure extensible** pour ajouter de nouvelles langues

Le système respecte toutes les bonnes pratiques Django pour l'internationalisation et est prêt pour la production multilingue.