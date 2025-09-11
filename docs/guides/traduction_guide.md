# Guide de traduction de MartialComp

Ce document fournit des instructions détaillées pour traduire l'application MartialComp du français vers l'anglais et les 16 autres langues supportées.

## Table des matières

1. [Préparation du code pour la traduction](#1-préparation-du-code-pour-la-traduction)
2. [Configuration du projet](#2-configuration-du-projet)
3. [Génération des fichiers de traduction](#3-génération-des-fichiers-de-traduction)
4. [Traduction des fichiers](#4-traduction-des-fichiers)
5. [Compilation et déploiement](#5-compilation-et-déploiement)
6. [Maintenance et mise à jour](#6-maintenance-et-mise-à-jour)
7. [Bonnes pratiques](#7-bonnes-pratiques)
8. [Résolution des problèmes courants](#8-résolution-des-problèmes-courants)

## 1. Préparation du code pour la traduction

Tous les textes visibles doivent être marqués pour traduction.

### Dans les templates Django (.html)

```html
{% load i18n %}

<!-- Pour un texte simple -->
<h1>{% trans "Tableau de bord" %}</h1>

<!-- Pour un texte avec variables -->
{% blocktrans with name=user.name %}
    Bienvenue, {{ name }}
{% endblocktrans %}

<!-- Pour un texte avec pluralisation -->
{% blocktrans count counter=items|length %}
    {{ counter }} compétiteur inscrit.
{% plural %}
    {{ counter }} compétiteurs inscrits.
{% endblocktrans %}
```

### Dans les fichiers Python (.py)

```python
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

# Texte simple
title = _("Compétitions")

# Texte avec pluralisation
message = ngettext(
    '%(count)d compétiteur trouvé',
    '%(count)d compétiteurs trouvés',
    count
) % {'count': count}
```

### Dans les fichiers JavaScript (.js)

Assurez-vous d'avoir configuré la bibliothèque JavaScript de Django pour la traduction :

```javascript
// Texte simple
var message = gettext("Confirmation");

// Texte avec pluralisation
var message = interpolate(
    ngettext("%(count)s compétiteur sélectionné", "%(count)s compétiteurs sélectionnés", count),
    { count: count },
    true
);
```

## 2. Configuration du projet

Assurez-vous que votre fichier `settings.py` contient les paramètres suivants :

```python
# Activation de l'internationalisation
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Langue par défaut (français dans notre cas)
LANGUAGE_CODE = 'fr'

# Middleware pour la détection de la langue
MIDDLEWARE = [
    # ...
    'django.middleware.locale.LocaleMiddleware',
    # ...
]

# Langues supportées
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('pt', 'Português'),
    ('nl', 'Nederlands'),
    ('pl', 'Polski'),
    ('ru', 'Русский'),
    ('ja', '日本語'),
    ('zh-hans', '简体中文'),
    ('zh-hant', '繁體中文'),
    ('ar', 'العربية'),
    ('ko', '한국어'),
    ('tr', 'Türkçe'),
    ('vi', 'Tiếng Việt'),
]

# Chemin des fichiers de traduction
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
```

Configurez Rosetta dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    # ...
    'rosetta',
    # ...
]
```

Ajoutez l'URL de Rosetta dans votre fichier `urls.py` principal :

```python
urlpatterns = [
    # ...
    path('rosetta/', include('rosetta.urls')),
    # ...
]
```

## 3. Génération des fichiers de traduction

### Création des fichiers PO pour toutes les langues

```bash
# Créer/mettre à jour les fichiers PO pour l'anglais (prioritaire)
python manage.py makemessages -l en

# Pour les fichiers JavaScript
python manage.py makemessages -l en -d djangojs

# Pour toutes les langues configurées
python manage.py makemessages --all

# Pour les fichiers JavaScript de toutes les langues
python manage.py makemessages --all -d djangojs
```

### Structure des fichiers générés

```
locale/
├── en/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── djangojs.po
├── fr/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── djangojs.po
└── [autres langues]/
    └── LC_MESSAGES/
        ├── django.po
        └── djangojs.po
```

## 4. Traduction des fichiers

### Méthode 1 : Utilisation de PoEdit (recommandé pour l'effort initial)

1. Installez PoEdit sur votre poste de travail
2. Ouvrez les fichiers `.po` avec PoEdit
3. Traduisez les chaînes de caractères
4. Utilisez les fonctionnalités de mémoire de traduction pour accélérer le processus
5. Enregistrez régulièrement

#### Avantages de PoEdit

- Interface professionnelle dédiée à la traduction
- Mémoire de traduction pour réutiliser les traductions précédentes
- Suggestions automatiques
- Vérification orthographique
- Travail hors ligne possible
- Meilleure productivité pour les grands volumes

### Méthode 2 : Utilisation de Rosetta (pour la maintenance continue)

1. Accédez à l'interface de Rosetta via votre site (`/rosetta/`)
2. Sélectionnez la langue cible
3. Filtrez par "NON-TRADUITS UNIQUEMENT" pour voir les textes à traduire
4. Complétez les traductions
5. Enregistrez

#### Avantages de Rosetta

- Intégré directement à votre application Django
- Accessible via navigateur pour tous les collaborateurs
- Compilation automatique possible
- Contexte des chaînes visible
- Pas d'installation requise pour les traducteurs

### Fichier PO : comprendre sa structure

```
#: path/to/template.html:10
msgid "Texte original en français"
msgstr "Translated text in English"
```

- `#:` indique l'emplacement du texte dans le code
- `msgid` contient le texte original (français)
- `msgstr` contient la traduction (à compléter)

## 5. Compilation et déploiement

### Compilation des fichiers PO en fichiers MO

Après avoir traduit les fichiers PO, compilez-les en fichiers MO :

```bash
python manage.py compilemessages
```

### Vérification des traductions

1. Lancez votre serveur de développement
2. Changez la langue via l'interface ou en ajoutant `?lang=en` à l'URL
3. Parcourez toutes les pages pour vérifier que les textes sont correctement traduits
4. Notez les textes non traduits

### Déploiement

1. Assurez-vous que tous les fichiers `.po` et `.mo` sont inclus dans votre dépôt
2. Vérifiez que le serveur de production a les bonnes permissions pour lire ces fichiers
3. Si vous utilisez un système de cache, videz-le après le déploiement

## 6. Maintenance et mise à jour

### Workflow continu

1. Marquez tous les nouveaux textes pour traduction
2. Exécutez régulièrement `makemessages` pour mettre à jour les fichiers PO
3. Traduisez les nouvelles chaînes
4. Compilez et déployez

### Automatisation

Vous pouvez intégrer ces étapes dans votre pipeline CI/CD :

```bash
# Exemple de script pour un pipeline CI/CD
python manage.py makemessages --all
# Si vous utilisez des services de traduction automatique, vous pourriez les intégrer ici
python manage.py compilemessages
```

### Collaboration avec des traducteurs externes

1. Exportez les fichiers PO pour les envoyer aux traducteurs
2. Demandez-leur d'utiliser PoEdit pour maintenir la cohérence
3. Réintégrez les fichiers traduits
4. Compilez et vérifiez

## 7. Bonnes pratiques

### Cohérence terminologique

- Créez un glossaire des termes spécifiques aux arts martiaux
- Assurez-vous que la terminologie est cohérente dans toutes les langues
- Utilisez les mémoires de traduction de PoEdit pour maintenir cette cohérence

### Chaînes formatées

Soyez attentif aux chaînes contenant des variables :

```python
# Original
_("Vous avez %(count)d messages")

# Traduction
# "You have %(count)d messages"
```

Les variables doivent être conservées avec la même syntaxe.

### Pluralisation

Chaque langue a ses propres règles de pluralisation. Assurez-vous d'utiliser correctement `ngettext` et `{% blocktrans count %}`.

### Textes contextuels

Si un même texte a des significations différentes selon le contexte, utilisez `pgettext` :

```python
from django.utils.translation import pgettext

# "Tableau" peut signifier "dashboard" ou "table"
pgettext("dashboard", "Tableau")
pgettext("furniture", "Tableau")
```

### Textes longs

Pour les textes longs, utilisez des blocs de traduction :

```html
{% blocktrans trimmed %}
Ce texte est très long et contient plusieurs phrases.
Il peut s'étendre sur plusieurs lignes.
{% endblocktrans %}
```

## 8. Résolution des problèmes courants

### Textes non marqués pour traduction

**Problème :** Certains textes restent en français après la traduction.

**Solution :** Localisez ces textes dans le code et marquez-les pour traduction.

### Chaînes non extraites

**Problème :** Certaines chaînes marquées pour traduction n'apparaissent pas dans les fichiers PO.

**Solutions :**
- Vérifiez l'extension des fichiers (par défaut, seuls .html et .py sont analysés)
- Utilisez l'option `-e` pour spécifier d'autres extensions :
  ```bash
  python manage.py makemessages -l en -e html,txt,py,js
  ```

### Traductions non appliquées

**Problème :** Les traductions existent mais ne sont pas visibles sur le site.

**Solutions :**
- Vérifiez que les fichiers MO sont bien compilés
- Redémarrez le serveur
- Videz le cache
- Vérifiez que le middleware `LocaleMiddleware` est correctement configuré

### Erreurs de formatage

**Problème :** Erreurs liées aux variables dans les chaînes formatées.

**Solution :** Assurez-vous que les variables dans `msgstr` correspondent exactement à celles dans `msgid`.

### Textes tronqués

**Problème :** Certaines traductions sont plus longues que les textes originaux et sont tronquées dans l'interface.

**Solution :** Adaptez votre CSS pour gérer des textes de longueurs variables.

---

## Ressources utiles

- [Documentation officielle Django sur la traduction](https://docs.djangoproject.com/fr/5.0/topics/i18n/translation/)
- [Documentation de django-rosetta](https://django-rosetta.readthedocs.io/)
- [Site officiel de PoEdit](https://poedit.net/)
- [Guide des bonnes pratiques de traduction](https://www.gnu.org/software/gettext/manual/html_node/Preparing-Strings.html)

---

Document préparé par l'équipe de développement de MartialComp - Dernière mise à jour : Juin 2025
