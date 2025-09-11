# Guide d'implémentation multilingue pour MartialComp

## Objectif

Améliorer le support multilingue de MartialComp pour atteindre une couverture de traduction proche de 100% et offrir une expérience utilisateur cohérente dans toutes les langues supportées.

## État actuel et problématique

- Seulement 5% des éléments sont actuellement traduits lors du changement de langue
- Expérience utilisateur incohérente et fragmentée
- Manque d'un processus systématique pour la gestion des traductions

## Architecture de la solution

### 1. Configuration du système de traduction Django

#### 1.1 Vérification de la configuration existante

```python
# settings.py
from django.utils.translation import gettext_lazy as _

# Vérifier que ces paramètres sont correctement configurés
MIDDLEWARE = [
    # ... autres middlewares
    'django.middleware.locale.LocaleMiddleware',  # Doit être après SessionMiddleware et avant CommonMiddleware
    # ... autres middlewares
]

LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('Anglais')),
    ('it', _('Italien')),
    ('es', _('Espagnol')),
    ('de', _('Allemand')),
    # Ajouter les autres langues supportées
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Définir la langue par défaut
LANGUAGE_CODE = 'fr'

# Activer la traduction des URL
USE_I18N = True
```

#### 1.2 Activation du sélecteur de langue

```python
# urls.py
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # URLs non traduites (médias, statiques, etc.)
]

# Préfixer toutes les URLs avec la langue
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('competitions.urls')),
    # ... autres URLs
    # Ajouter ce paramètre pour autoriser l'accès sans préfixe de langue à la langue par défaut
    prefix_default_language=False
)
```

### 2. Installation et configuration des outils

#### 2.1 Django-Rosetta pour l'interface de traduction

```bash
pip install django-rosetta
```

```python
# settings.py
INSTALLED_APPS = [
    # ... applications existantes
    'rosetta',
]

# URLs pour accéder à Rosetta
# urls.py
urlpatterns += [
    path('rosetta/', include('rosetta.urls')),
]

# Restreindre l'accès à Rosetta aux superadmins et staff
ROSETTA_REQUIRES_AUTH = True
```

#### 2.2 Django-Modeltranslation pour la traduction des contenus dynamiques

```bash
pip install django-modeltranslation
```

```python
# settings.py
INSTALLED_APPS = [
    # ... applications existantes
    'modeltranslation',
    # Placer modeltranslation avant admin pour intégration
    'django.contrib.admin',
]

# Définir les langues de modeltranslation (généralement identiques à LANGUAGES)
MODELTRANSLATION_LANGUAGES = [lang_code for lang_code, lang_name in LANGUAGES]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'
```

### 3. Marquage des chaînes à traduire

#### 3.1 Dans les fichiers Python

```python
from django.utils.translation import gettext_lazy as _

# Marquer les chaînes de caractères pour traduction
class Competition(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Compétition")
        verbose_name_plural = _("Compétitions")
```

#### 3.2 Dans les templates Django

```html
{% load i18n %}

<!-- Pour les chaînes simples -->
<h1>{% trans "Tableau de bord" %}</h1>

<!-- Pour les blocs contenant des variables -->
{% blocktrans with name=user.full_name %}
  Bienvenue, {{ name }} !
{% endblocktrans %}

<!-- Pour les pluriels -->
{% blocktrans count counter=items_count %}
  Vous avez {{ counter }} notification non lue
{% plural %}
  Vous avez {{ counter }} notifications non lues
{% endblocktrans %}
```

#### 3.3 Dans le JavaScript

```javascript
// Utiliser la fonction gettext exposée par Django
const message = gettext("Bienvenue dans MartialComp");

// Pour les chaînes plurielles
const notification_text = ngettext(
    "Vous avez %(count)s notification",
    "Vous avez %(count)s notifications",
    count
).replace("%(count)s", count);
```

### 4. Extraction et compilation des chaînes

#### 4.1 Extraction des chaînes à traduire

```bash
# Extraire les chaînes de tous les fichiers (Python et templates)
python manage.py makemessages -a

# Pour extraire également les chaînes des fichiers JavaScript
python manage.py makemessages -d djangojs -a
```

#### 4.2 Compilation des fichiers de traduction

```bash
# Après avoir modifié les fichiers .po, compiler en .mo
python manage.py compilemessages
```

### 5. Automatisation des traductions

#### 5.1 Script d'automatisation avec DeepL

Créer un fichier `translate_po.py` dans le dossier `utils`:

```python
#!/usr/bin/env python
import os
import polib
import argparse
import deepl
from django.conf import settings

def translate_po_file(po_file, source_lang, target_lang, api_key):
    """Traduit un fichier PO vers la langue cible."""
    translator = deepl.Translator(api_key)
    po = polib.pofile(po_file)
    
    translated_count = 0
    skipped_count = 0
    
    print(f"Traduction de {po_file} vers {target_lang}...")
    
    for entry in po:
        # Ignorer les entrées déjà traduites ou vides
        if entry.translated() or not entry.msgid:
            skipped_count += 1
            continue
        
        try:
            # Traduire le texte
            result = translator.translate_text(
                entry.msgid,
                source_lang=source_lang.upper(),
                target_lang=target_lang.upper()
            )
            entry.msgstr = result.text
            translated_count += 1
            
            # Attendre un peu pour éviter de surcharger l'API
            if translated_count % 10 == 0:
                print(f"  {translated_count} chaînes traduites...")
                
        except Exception as e:
            print(f"  Erreur lors de la traduction de '{entry.msgid}': {e}")
    
    if translated_count > 0:
        po.save()
        print(f"  Terminé. {translated_count} chaînes traduites, {skipped_count} ignorées.")
    else:
        print(f"  Aucune chaîne à traduire. {skipped_count} déjà traduites.")

def main():
    parser = argparse.ArgumentParser(description='Traduire les fichiers PO avec DeepL')
    parser.add_argument('--api-key', required=True, help='Clé API DeepL')
    parser.add_argument('--source', default='fr', help='Langue source (défaut: fr)')
    parser.add_argument('--target', nargs='+', help='Langue(s) cible(s), ex: en it')
    args = parser.parse_args()
    
    source_lang = args.source
    target_langs = args.target or ['en', 'it', 'es', 'de']
    
    for lang in target_langs:
        if lang == source_lang:
            continue
        
        po_path = f'locale/{lang}/LC_MESSAGES/django.po'
        if os.path.exists(po_path):
            translate_po_file(po_path, source_lang, lang, args.api_key)
        else:
            print(f"Fichier non trouvé: {po_path}")
        
        # Traiter également les fichiers JavaScript
        js_po_path = f'locale/{lang}/LC_MESSAGES/djangojs.po'
        if os.path.exists(js_po_path):
            translate_po_file(js_po_path, source_lang, lang, args.api_key)

if __name__ == '__main__':
    main()
```

#### 5.2 Commande de gestion Django pour l'automatisation

Créer un fichier `management/commands/translate_messages.py`:

```python
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
from ....utils.translate_po import translate_po_file

class Command(BaseCommand):
    help = 'Traduit automatiquement les fichiers de messages avec DeepL'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', required=True, help='Clé API DeepL')
        parser.add_argument('--source', default='fr', help='Langue source (défaut: fr)')
        parser.add_argument('--target', nargs='+', help='Langue(s) cible(s), ex: en it')
        parser.add_argument('--compile', action='store_true', help='Compiler les messages après traduction')

    def handle(self, *args, **options):
        api_key = options['api_key']
        source_lang = options['source']
        target_langs = options['target'] or [lang[0] for lang in settings.LANGUAGES if lang[0] != source_lang]
        
        for lang in target_langs:
            if lang == source_lang:
                continue
            
            self.stdout.write(f"Traduction vers {lang}...")
            
            po_path = os.path.join('locale', lang, 'LC_MESSAGES', 'django.po')
            if os.path.exists(po_path):
                translate_po_file(po_path, source_lang, lang, api_key)
            else:
                self.stdout.write(self.style.WARNING(f"Fichier non trouvé: {po_path}"))
            
            js_po_path = os.path.join('locale', lang, 'LC_MESSAGES', 'djangojs.po')
            if os.path.exists(js_po_path):
                translate_po_file(js_po_path, source_lang, lang, api_key)
        
        if options['compile']:
            self.stdout.write("Compilation des messages...")
            os.system('python manage.py compilemessages')
            self.stdout.write(self.style.SUCCESS("Compilation terminée."))
```

### 6. Configuration de django-modeltranslation

#### 6.1 Définition des modèles à traduire

Créer un fichier `competitions/translation.py`:

```python
from modeltranslation.translator import translator, TranslationOptions
from .models import Competition, Club, Discipline

class CompetitionTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'rules', 'location')

class ClubTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class DisciplineTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

# Enregistrer les modèles pour traduction
translator.register(Competition, CompetitionTranslationOptions)
translator.register(Club, ClubTranslationOptions)
translator.register(Discipline, DisciplineTranslationOptions)
```

#### 6.2 Création des migrations pour les champs de traduction

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Intégration de la détection automatique de langue

#### 7.1 Middleware de détection de langue

Créer un fichier `middleware.py`:

```python
from django.utils import translation
from django.conf import settings

class AutoDetectLanguageMiddleware:
    """Middleware pour détecter automatiquement la langue préférée de l'utilisateur."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Ne pas appliquer si la langue est déjà spécifiée dans l'URL
        if request.path.startswith('/fr/') or request.path.startswith('/en/') or request.path.startswith('/it/'):
            return self.get_response(request)
            
        # Si l'utilisateur a déjà une préférence en session, ne rien faire
        if request.session.get('django_language') or translation.get_language():
            return self.get_response(request)
            
        # Détecter la langue préférée du navigateur
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for lang_code, lang_name in settings.LANGUAGES:
            if lang_code in accept_language:
                request.session['django_language'] = lang_code
                translation.activate(lang_code)
                break
                
        response = self.get_response(request)
        return response
```

Ajouter le middleware à `settings.py`:

```python
MIDDLEWARE = [
    # ... autres middlewares
    'django.middleware.locale.LocaleMiddleware',
    'competitions.middleware.AutoDetectLanguageMiddleware',  # Ajouter après LocaleMiddleware
    # ... autres middlewares
]
```

### 8. Gestion des traductions manquantes

#### 8.1 Middleware pour surveiller les traductions manquantes

```python
class MissingTranslationMiddleware:
    """Middleware pour détecter et journaliser les traductions manquantes en production."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.missing_translations = set()
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Ne vérifier que si nous sommes en production et pas dans le site d'admin
        if settings.DEBUG or request.path.startswith('/admin/'):
            return response
            
        # Vérifier si la réponse contient des marqueurs de traduction manquante
        # Ceci est très simplifié - vous auriez besoin d'une approche plus robuste
        if 'class="translation-missing"' in response.content.decode('utf-8'):
            # Logger les traductions manquantes
            # Implémenter une logique pour extraire et stocker les chaînes manquantes
            pass
            
        return response
```

#### 8.2 Template tag pour gérer les traductions manquantes

Créer un fichier `competitions/templatetags/translation_helpers.py`:

```python
from django import template
from django.utils.translation import get_language
from django.conf import settings

register = template.Library()

@register.simple_tag(takes_context=True)
def smart_trans(context, text):
    """
    Template tag qui tente de traduire le texte,
    et applique un style spécial si la traduction est manquante.
    """
    current_lang = get_language()
    translated = _(text)
    
    # Si nous ne sommes pas dans la langue par défaut et la traduction est identique au texte original
    if current_lang != settings.LANGUAGE_CODE and translated == text:
        return f'<span class="translation-missing" title="Traduction manquante">{text}</span>'
    return translated
```

### 9. Tableau de bord de progression des traductions

#### 9.1 Vue de tableau de bord des traductions

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
import polib
import os
from django.conf import settings

@staff_member_required
def translation_dashboard(request):
    """Affiche un tableau de bord de la progression des traductions."""
    stats = []
    
    source_lang = settings.LANGUAGE_CODE
    
    for lang_code, lang_name in settings.LANGUAGES:
        if lang_code == source_lang:
            continue
        
        po_path = os.path.join('locale', lang_code, 'LC_MESSAGES', 'django.po')
        js_po_path = os.path.join('locale', lang_code, 'LC_MESSAGES', 'djangojs.po')
        
        lang_stats = {
            'code': lang_code,
            'name': lang_name,
            'total': 0,
            'translated': 0,
            'percentage': 0
        }
        
        # Analyser fichier principal
        if os.path.exists(po_path):
            po = polib.pofile(po_path)
            lang_stats['total'] += len(po)
            lang_stats['translated'] += len(po.translated_entries())
        
        # Analyser fichier JavaScript
        if os.path.exists(js_po_path):
            js_po = polib.pofile(js_po_path)
            lang_stats['total'] += len(js_po)
            lang_stats['translated'] += len(js_po.translated_entries())
        
        # Calculer pourcentage
        if lang_stats['total'] > 0:
            lang_stats['percentage'] = round(lang_stats['translated'] / lang_stats['total'] * 100, 1)
        
        stats.append(lang_stats)
    
    return render(request, 'admin/translation_dashboard.html', {
        'stats': stats,
        'source_language': dict(settings.LANGUAGES)[source_lang],
        'title': 'Tableau de bord des traductions'
    })
```

#### 9.2 Template du tableau de bord

Créer un fichier `templates/admin/translation_dashboard.html`:

```html
{% extends "admin/base_site.html" %}
{% load i18n %}

{% block content %}
<div class="module">
    <h2>{% trans "État des traductions" %}</h2>
    <p>{% blocktrans with source=source_language %}Langue source: {{ source }}{% endblocktrans %}</p>
    
    <table>
        <thead>
            <tr>
                <th>{% trans "Langue" %}</th>
                <th>{% trans "Progression" %}</th>
                <th>{% trans "Traduit" %}</th>
                <th>{% trans "Total" %}</th>
                <th>{% trans "Actions" %}</th>
            </tr>
        </thead>
        <tbody>
            {% for lang in stats %}
            <tr>
                <td>{{ lang.name }} ({{ lang.code }})</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar 
                            {% if lang.percentage < 30 %}bg-danger
                            {% elif lang.percentage < 70 %}bg-warning
                            {% else %}bg-success{% endif %}"
                            style="width: {{ lang.percentage }}%">
                            {{ lang.percentage }}%
                        </div>
                    </div>
                </td>
                <td>{{ lang.translated }}</td>
                <td>{{ lang.total }}</td>
                <td>
                    <a href="{% url 'rosetta-language-selection' %}?lang={{ lang.code }}" class="button">
                        {% trans "Éditer" %}
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="module">
    <h2>{% trans "Actions globales" %}</h2>
    <p>
        <a href="{% url 'admin:index' %}translate_messages/" class="button">
            {% trans "Lancer la traduction automatique" %}
        </a>
        <a href="{% url 'admin:index' %}makemessages/" class="button">
            {% trans "Extraire les nouvelles chaînes" %}
        </a>
        <a href="{% url 'admin:index' %}compilemessages/" class="button">
            {% trans "Compiler les traductions" %}
        </a>
    </p>
</div>
{% endblock %}
```

### 10. Plan d'implémentation recommandé

1. **Phase 1 : Configuration de base**
   - Installer django-rosetta et django-modeltranslation
   - Vérifier et corriger la configuration i18n dans settings.py
   - Configurer correctement le middleware LocaleMiddleware

2. **Phase 2 : Marquage des chaînes**
   - Auditer les templates et fichiers Python pour identifier les textes non marqués
   - Marquer systématiquement toutes les chaînes visibles par l'utilisateur
   - Lancer `makemessages` pour générer les fichiers .po initiaux

3. **Phase 3 : Traduction du contenu statique**
   - Configurer l'API DeepL pour la traduction automatique
   - Exécuter le script de traduction automatique
   - Réviser manuellement les traductions critiques

4. **Phase 4 : Traduction du contenu dynamique**
   - Configurer django-modeltranslation pour les modèles principaux
   - Migrer la base de données pour ajouter les champs de traduction
   - Développer une interface pour que les administrateurs puissent modifier les traductions

5. **Phase 5 : Optimisation et contrôle qualité**
   - Mettre en place le tableau de bord de traduction
   - Déployer le système de détection des traductions manquantes
   - Tester l'interface dans toutes les langues supportées

### 11. Bonnes pratiques à suivre

1. **Éviter les chaînes concaténées**
   ```python
   # À éviter
   message = _("Bonjour") + " " + user.name
   
   # Préférer
   message = _("Bonjour %(name)s") % {'name': user.name}
   ```

2. **Contextualiser les traductions ambiguës**
   ```python
   from django.utils.translation import pgettext
   
   # "Réservation" peut être un nom ou un verbe
   reservation_title = pgettext("noun", "Réservation")
   reservation_action = pgettext("verb", "Réservation")
   ```

3. **Utiliser des slugs et identifiants non traduits**
   ```python
   # Ne pas traduire les slugs d'URL
   path(_('competitions'), ...) # MAUVAIS
   path('competitions', ...) # BON
   ```

4. **Ne pas traduire les noms de variables**
   ```html
   <!-- Ne pas traduire les noms de variables -->
   {% blocktrans with name=user.full_name %}
     Bienvenue, {{ name }} !
   {% endblocktrans %}
   ```

5. **Compiler les messages avant déploiement**
   - Toujours s'assurer que les fichiers .mo sont à jour avant le déploiement
   - Intégrer la compilation dans le script de déploiement

6. **Utiliser des linters et contrôles automatiques**
   - Intégrer des vérifications dans le CI/CD pour détecter les chaînes non marquées
   - Utiliser des outils comme django-i18n-lint

## Conclusion

Cette implémentation permettra à MartialComp d'offrir une expérience utilisateur complètement multilingue, avec un processus efficace de gestion des traductions. En combinant traduction automatique et révision manuelle, la plateforme pourra maintenir un haut niveau de qualité de traduction tout en minimisant l'effort requis.

---

## Ressources utiles

- [Documentation Django sur l'internationalisation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Django-rosetta](https://django-rosetta.readthedocs.io/)
- [Django-modeltranslation](https://django-modeltranslation.readthedocs.io/)
- [API DeepL](https://www.deepl.com/docs-api)
- [Guide des bonnes pratiques i18n](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#localization-how-to-create-language-files)
