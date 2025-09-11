# Guide de Traduction MartialComp

## État Actuel

✅ **Site traduit en anglais** - 98.4% de traduction complète  
✅ **Système IA intégré** - Traduction automatique avec deep-translator  
✅ **Interface multilingue** - Sélecteur de langue dans la navigation  

## Langues Supportées

- 🇫🇷 **Français** (langue principale) - 100%
- 🇺🇸 **Anglais** - 98.4% 
- 🇪🇸 **Espagnol** - Partiellement traduit
- 🇩🇪 **Allemand** - Partiellement traduit  
- 🇮🇹 **Italien** - Partiellement traduit
- 🇸🇦 **Arabe** - Partiellement traduit

## Commandes de Traduction

### Traduction Manuelle (Django)

```bash
# Générer les messages pour une langue
python manage.py makemessages -l en

# Compiler les messages
python manage.py compilemessages -l en

# Notre commande personnalisée (recommandée)
python manage.py translate_site --language en --test
```

### Traduction Automatique (IA)

```bash
# Traduction automatique avec IA
python manage.py auto_translate --target-language en --model all

# Traduction spécifique (pratiquants seulement)
python manage.py auto_translate --target-language en --model practitioner

# Simulation (test)
python manage.py auto_translate --target-language en --dry-run
```

## Interface d'Administration IA

### Accès à l'Interface de Traduction

1. Connectez-vous en tant qu'administrateur
2. Accédez à `/admin/translation-dashboard/`
3. Utilisez l'interface pour :
   - Détecter la langue d'un texte
   - Traduire du contenu instantanément
   - Lancer des traductions en lot
   - Voir les statistiques de traduction

### Fonctionnalités IA Disponibles

- **Détection automatique de langue** avec `langdetect`
- **Traduction intelligente** avec `deep-translator` (Google, Bing, LibreTranslator)
- **Cache intelligent** des traductions (24h)
- **Validation de qualité** automatique
- **Traduction en lot** via interface admin

## Templates Traduits

### Page d'Accueil (welcome.html)
- ✅ Titre principal
- ✅ Navigation  
- ✅ Boutons d'action
- ✅ Bannière de test
- ✅ Sélecteur de langue

### Dashboard Coach
- ✅ Titre et navigation
- ✅ Actions rapides
- ✅ Menus sidebar
- ✅ Boutons d'ajout

### Administration
- ✅ Interface de traduction IA
- ✅ Import/export intelligent
- ✅ Gestion des doublons

## Ajouter une Nouvelle Traduction

### 1. Dans les Templates

```django
<!-- Avant -->
<h1>Tableau de bord</h1>

<!-- Après -->
{% load i18n %}
<h1>{% trans "Tableau de bord" %}</h1>
```

### 2. Dans le Code Python

```python
from django.utils.translation import gettext_lazy as _

# Messages d'interface
messages.success(request, _("Opération réussie"))

# Labels de modèles
class Meta:
    verbose_name = _("Pratiquant")
    verbose_name_plural = _("Pratiquants")
```

### 3. Ajouter la Traduction

```bash
# 1. Générer les nouveaux messages
python manage.py makemessages -l en

# 2. Éditer locale/en/LC_MESSAGES/django.po
msgid "Nouveau texte"
msgstr "New text"

# 3. Compiler
python manage.py translate_site --language en --compile-only
```

## Test des Traductions

### Script de Test

```python
# test_translation.py
python test_translation.py
```

### Test dans l'Interface

1. Changez la langue avec le sélecteur en haut à droite
2. Vérifiez que les textes changent
3. Testez la navigation entre les pages

## Déploiement des Traductions

### Développement

```bash
# Compiler toutes les langues
python manage.py compilemessages

# Redémarrer le serveur
python manage.py runserver
```

### Production

```bash
# Compiler avec optimisation
python manage.py compilemessages --settings=config.settings_production

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer les services
sudo systemctl reload nginx
sudo systemctl restart gunicorn
```

## Architecture Technique

### Fichiers de Traduction

```
locale/
├── en/LC_MESSAGES/
│   ├── django.po     # Messages à traduire
│   └── django.mo     # Messages compilés
├── es/LC_MESSAGES/
├── de/LC_MESSAGES/
└── ...
```

### Configuration Django

```python
# settings.py
LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('de', 'Deutsch'),
    ('it', 'Italiano'),
    ('ar', 'العربية'),
]

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [BASE_DIR / 'locale']
```

### Middleware de Traduction IA

Le système intègre l'IA pour :
- Détecter automatiquement la langue préférée de l'utilisateur
- Proposer des traductions intelligentes
- Optimiser la qualité avec scoring automatique

## Maintenance

### Mise à Jour des Traductions

```bash
# 1. Extraire les nouveaux textes
python manage.py makemessages -a

# 2. Traduire automatiquement les manquants
python manage.py auto_translate --target-language en --force

# 3. Compiler
python manage.py translate_site --language en --test
```

### Statistiques

```bash
# Voir l'état de toutes les traductions
python manage.py translate_site --language en --compile-only --test
```

## Support

- **Traduction manuelle** : Éditez les fichiers `.po`
- **Traduction IA** : Interface d'administration  
- **Documentation** : Ce guide
- **Dépannage** : Vérifiez les logs Django

---

*MartialComp - Plateforme multilingue pour les arts martiaux* 🥋🌍