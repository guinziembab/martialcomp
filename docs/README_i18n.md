# Guide d'internationalisation (i18n) de MartialComp

Ce document explique comment l'internationalisation a été mise en place dans l'application MartialComp et comment la maintenir.

## Configuration générale

L'internationalisation est basée sur le framework standard de Django pour les traductions (i18n), qui utilise GNU gettext.

### Fichiers clés

1. **settings.py**
   - `LANGUAGE_CODE = 'fr'` : Langue par défaut de l'application
   - `USE_I18N = True` : Active l'internationalisation
   - `LANGUAGES` : Liste des langues supportées
   - `LOCALE_PATHS` : Chemin vers les fichiers de traduction

2. **urls.py**
   - Utilise `i18n_patterns` pour les URLs avec préfixe de langue
   - Route `/set-language/` pour changer de langue
   - Option `prefix_default_language=False` pour éviter de préfixer la langue par défaut

3. **Fichiers de traduction**
   - Situés dans le dossier `/locale/[code_langue]/LC_MESSAGES/`
   - Fichiers source `.po` à éditer manuellement
   - Fichiers compilés `.mo` générés automatiquement

## Comment fonctionne le changement de langue

1. Le sélecteur de langue est présent en haut de chaque page (dans `base.html` et `welcome.html`)
2. Lorsque l'utilisateur sélectionne une langue, une requête POST est envoyée à `/set-language/`
3. Django stocke la préférence de langue dans les cookies
4. Les pages sont alors traduites selon cette préférence

## Tags de traduction dans les templates

Pour marquer du texte comme traduisible, utilisez les tags suivants :

1. **Pour les textes simples :**
   ```html
   {% trans "Texte à traduire" %}
   ```

2. **Pour les blocs de texte :**
   ```html
   {% blocktrans %}
   Texte sur plusieurs lignes
   à traduire entièrement.
   {% endblocktrans %}
   ```

3. **Avec des variables :**
   ```html
   {% blocktrans with name=user.name %}
   Bonjour {{ name }}
   {% endblocktrans %}
   ```

4. **Dans les attributs JavaScript :**
   ```html
   <button onclick="alert('{% trans "Message" %}')">Cliquez</button>
   ```

5. **Filtre personnalisé :**
   ```html
   {{ "Texte à traduire"|trans }}
   ```

## Comment ajouter une nouvelle traduction

1. **Extraire les textes à traduire :**
   ```bash
   python manage.py makemessages -l [code_langue]
   ```
   Par exemple : `python manage.py makemessages -l de` pour l'allemand

2. **Éditer les fichiers .po :**
   - Localisez le fichier `locale/[code_langue]/LC_MESSAGES/django.po`
   - Remplissez les chaînes `msgstr` pour chaque `msgid`

3. **Compiler les traductions :**
   ```bash
   python3 recompile_translations.py
   ```

4. **Redémarrer le serveur :**
   ```bash
   ./restart_django.sh
   ```

## Maintenance et débogage

### Fichiers utiles

1. **debug_translations.py** - Script de diagnostic pour vérifier la configuration i18n
2. **recompile_translations.py** - Script pour recompiler les fichiers .mo
3. **restart_django.sh** - Script pour redémarrer le serveur et recompiler les traductions

### Conseils de débogage

1. **Page de test** - Accédez à `/translations-test/` pour vérifier si les traductions fonctionnent
2. **Diagnostic** - Exécutez `python3 debug_translations.py` pour vérifier les fichiers
3. **Vérification de la langue** - Accédez à `/language-debug/` pour voir la langue active
4. **Les traductions ne fonctionnent pas ?**
   - Vérifiez que les fichiers .mo sont à jour
   - Vérifiez que le middleware est correctement configuré
   - Vérifiez que les templates utilisent correctement les tags `{% trans %}`
   - Redémarrez le serveur

## Bonnes pratiques

1. Utilisez **toujours** `{% trans %}` et jamais `{% translate %}`
2. Utilisez **toujours** `{% blocktrans %}` et jamais `{% blocktranslate %}`
3. Conservez tous les textes destinés aux utilisateurs dans des tags de traduction
4. Utilisez des phrases complètes pour la traduction, pas des fragments
5. Évitez de construire des phrases en concaténant plusieurs traductions
6. Utilisez le contexte si nécessaire pour différencier les termes ambigus
7. Pour les nouvelles fonctionnalités, mettez à jour tous les fichiers de traduction