# Guide de correction des erreurs de traduction dans MartialComp

Ce guide explique comment résoudre l'erreur `ValueError: too many values to unpack (expected 2)` qui se produit lors de l'utilisation de la vue `set_language` pour changer de langue.

## Problème

Cette erreur est généralement causée par des fichiers de traduction (.po/.mo) mal formatés. Le problème spécifique concerne probablement une ligne dans un fichier .po qui ne respecte pas le format attendu par le parseur gettext de Python.

## Solution en 3 étapes

### Étape 1: Nettoyer les fichiers .po

Exécutez le script de nettoyage pour corriger les fichiers .po :

```bash
python fix_po_files.py
```

Ce script va :
- Vérifier tous les fichiers .po existants
- Corriger les formats invalides
- S'assurer que les en-têtes sont conformes
- Créer de nouveaux fichiers .po pour les langues manquantes si nécessaire

### Étape 2: Recompiler les fichiers .mo

Une fois les fichiers .po nettoyés, recompilez-les en fichiers .mo :

```bash
python recompile_translations.py
```

Ce script utilise plusieurs méthodes de compilation pour garantir que les fichiers .mo sont correctement générés, même si vous n'avez pas les outils standard de gettext installés.

### Étape 3: Redémarrer le serveur Django

Après avoir recompilé les fichiers, redémarrez le serveur Django pour prendre en compte les modifications :

```bash
python manage.py runserver
```

## Vérification

Accédez à l'URL `/translation-debug/` pour vérifier que les traductions fonctionnent correctement. Cette page affiche :
- La configuration actuelle des langues
- Les fichiers de traduction détectés
- Des tests de traduction pour vérifier le fonctionnement

## Dépannage supplémentaire

Si le problème persiste après avoir suivi ces étapes, vous pouvez essayer les solutions suivantes :

1. **Recréer manuellement les fichiers .po problématiques**  
   Identifiez le fichier .po problématique (généralement celui de la langue que vous essayez d'activer) et remplacez-le par un nouveau fichier basé sur le modèle fourni dans `en/LC_MESSAGES/django.po`.

2. **Vérifier la structure des répertoires de localisation**  
   Assurez-vous que chaque langue a la structure correcte :
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

3. **Vérifier les paramètres de langue dans settings.py**  
   Assurez-vous que le code de langue dans `LANGUAGE_CODE` correspond exactement aux codes utilisés dans `LANGUAGES` (par exemple, utilisez 'fr' et non 'fr-fr').

## Notes techniques

- L'erreur `too many values to unpack (expected 2)` se produit lorsque le parseur de fichiers .po rencontre une ligne qui ne peut pas être décomposée en exactement 2 valeurs.
- Cela se produit généralement lorsqu'une ligne n'est pas correctement formatée, comme une chaîne multiligne sans guillemets de continuation.
- Les fichiers .po corrects doivent avoir des paires `msgid`/`msgstr` bien formées, avec des guillemets appropriés pour les chaînes multiligne.

## Références

- [Django Translation documentation](https://docs.djangoproject.com/en/5.1/topics/i18n/translation/)
- [GNU gettext utilities](https://www.gnu.org/software/gettext/)