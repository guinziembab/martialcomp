# Guide d'internationalisation pour MartialComp

Ce guide explique comment gérer les traductions dans l'application MartialComp.

## Langues prises en charge

L'application prend en charge les langues suivantes :

- Français (fr) - Langue par défaut
- Anglais (en)
- Espagnol (es)
- Italien (it)
- Allemand (de)
- Norvégien (no)
- Japonais (ja)
- Chinois (zh)
- Hindi (hi)
- Arabe (ar)
- Swahili (sw)
- Amharic (am)
- Zulu (zu)
- Yoruba (yo)
- Portugais (pt)
- Coréen (ko)

## Structure des fichiers de traduction

Les fichiers de traduction sont organisés comme suit :

```
locale/
  ├── fr/
  │   └── LC_MESSAGES/
  │       └── django.po
  ├── en/
  │   └── LC_MESSAGES/
  │       └── django.po
  └── ...
```

## Marquer les textes pour traduction

### Dans les templates Django

```html
{% load i18n %}

<!-- Traduction simple -->
{% translate "Texte à traduire" %}

<!-- Traduction avec variables -->
{% blocktranslate %}
    Bonjour, {{ username }} !
{% endblocktranslate %}
```

### Dans le code Python

```python
from django.utils.translation import gettext as _

# Traduction simple
message = _("Texte à traduire")

# Traduction avec variables
message = _("Bonjour, {username} !").format(username=user.username)
```

## Mise à jour des traductions

### Utilisation des scripts automatisés

Deux scripts sont disponibles pour faciliter la mise à jour des traductions :

1. `update_translations.py` - Script Python
2. `update_translations.sh` - Script shell

Pour mettre à jour les traductions, exécutez simplement :

```bash
./update_translations.sh
```

Ce script va :
1. Extraire tous les textes à traduire
2. Générer ou mettre à jour les fichiers .po
3. Compiler les fichiers .po en fichiers .mo

### Mise à jour manuelle

Si vous préférez mettre à jour les traductions manuellement, suivez ces étapes :

1. Extraire les messages :
   ```bash
   python manage.py makemessages -l fr  # Pour le français
   python manage.py makemessages -l en  # Pour l'anglais
   # ... etc. pour les autres langues
   ```

2. Modifier les fichiers .po dans `locale/<langue>/LC_MESSAGES/django.po`

3. Compiler les messages :
   ```bash
   python manage.py compilemessages
   ```

## Ajouter une nouvelle langue

Pour ajouter une nouvelle langue :

1. Ajoutez la langue dans `settings.py` :
   ```python
   LANGUAGES = [
       # ... langues existantes ...
       ('xx', 'Nom de la langue'),  # xx est le code ISO de la langue
   ]
   ```

2. Créez le répertoire pour la nouvelle langue :
   ```bash
   mkdir -p locale/xx/LC_MESSAGES
   ```

3. Générez le fichier de traduction initial :
   ```bash
   python manage.py makemessages -l xx
   ```

4. Éditez le fichier `locale/xx/LC_MESSAGES/django.po` pour ajouter les traductions

5. Compilez les messages :
   ```bash
   python manage.py compilemessages
   ```

## Tester les traductions

Pour tester les traductions, changez la langue dans l'interface utilisateur en utilisant le sélecteur de langue dans l'en-tête de l'application.

## Bonnes pratiques

1. **Maintenez la cohérence** : Utilisez les mêmes termes pour les mêmes concepts dans toutes les langues.
2. **Contextualisez les traductions** : Utilisez des commentaires dans les fichiers .po pour expliquer le contexte si nécessaire.
3. **Testez les langues RTL** : Les langues comme l'arabe s'écrivent de droite à gauche, assurez-vous que l'interface s'adapte correctement.
4. **Mettez à jour régulièrement** : Maintenez les traductions à jour lorsque vous ajoutez du nouveau contenu.
5. **Pensez à l'internationalisation dès le début** : Concevez vos templates et votre code en pensant à la traduction.

## Ressources

- [Documentation Django sur la traduction](https://docs.djangoproject.com/fr/5.1/topics/i18n/translation/)
- [Utilitaires GNU gettext](https://www.gnu.org/software/gettext/)