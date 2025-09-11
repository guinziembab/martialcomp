# Guide d'intégration DeepL avec Django-Rosetta

## Vue d'ensemble

Cette intégration permet d'utiliser DeepL pour la traduction automatique dans votre projet Django avec django-rosetta. Elle fournit des suggestions de traduction directement dans l'interface Rosetta et des commandes pour la traduction en lot.

## Installation et Configuration

### 1. Installation des dépendances

Les dépendances suivantes ont été ajoutées à `requirements.txt` :
```
deepl==1.19.0
django-rosetta==0.10.0  # (déjà installé)
```

### 2. Configuration DeepL

Dans `config/settings/base.py`, la configuration DeepL a été ajoutée :

```python
# DeepL Translation Service Configuration
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY', '')
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'  # URL gratuite

# Mapping des langues (Django locale -> DeepL language code)
DEEPL_LANGUAGE_MAPPING = {
    'fr': 'FR',
    'en': 'EN',
    'es': 'ES',
    'it': 'IT',
    'de': 'DE',
    'pt': 'PT',
    'ja': 'JA',
    'zh': 'ZH',
    'ar': 'AR',
    'ko': 'KO',
    'nl': 'NL',
    'pl': 'PL',
    'ru': 'RU',
    'sv': 'SV',
    'no': 'NB',
}
```

### 3. Variable d'environnement

Ajoutez votre clé API DeepL dans votre fichier `.env` :
```bash
DEEPL_API_KEY=votre_cle_api_deepl_ici
```

## Fonctionnalités

### 1. Service de traduction (`config/translation_service.py`)

Le service DeepL offre les fonctionnalités suivantes :
- Traduction de texte unique
- Traduction en lot (plus efficace)
- Gestion des langues supportées
- Informations d'utilisation de l'API
- Mapping automatique des codes de langue

### 2. Interface Web

#### Rosetta avec suggestions DeepL
- Boutons "DeepL" ajoutés à chaque champ de traduction
- Suggestions automatiques en un clic
- Intégration JavaScript native avec Rosetta

#### Interface d'administration
- `/admin/deepl/status/` : Statut du service et utilisation de l'API
- `/admin/deepl/batch/` : Interface pour la traduction en lot

### 3. Commande de gestion Django

```bash
# Traduction automatique des entrées manquantes
python manage.py translate_missing --target-language fr

# Options disponibles :
--target-language fr    # Langue cible (obligatoire)
--source-language en    # Langue source (défaut: en)
--app competitions      # App spécifique (optionnel)
--dry-run              # Aperçu sans modification
--force                # Retraduit les entrées existantes
```

## Utilisation

### 1. Traduction manuelle avec Rosetta

1. Accédez à `/rosetta/`
2. Sélectionnez la langue cible
3. Cliquez sur le bouton "🌍 DeepL" à côté des champs à traduire
4. Acceptez ou modifiez la suggestion
5. Sauvegardez

### 2. Traduction automatique en lot

#### Via l'interface web :
1. Accédez à `/admin/deepl/batch/`
2. Sélectionnez la langue cible
3. Choisissez l'application (optionnel)
4. Cochez "Dry Run" pour un aperçu
5. Lancez la traduction

#### Via la ligne de commande :
```bash
# Exemple : traduire toutes les entrées manquantes en français
python manage.py translate_missing --target-language fr

# Exemple : traduire une app spécifique avec aperçu
python manage.py translate_missing --target-language es --app competitions --dry-run

# Exemple : retradure toutes les entrées existantes
python manage.py translate_missing --target-language de --force
```

### 3. Vérification du statut

Accédez à `/admin/deepl/status/` pour :
- Vérifier la disponibilité du service
- Consulter l'utilisation de l'API
- Voir les langues supportées

## Fichiers créés/modifiés

### Nouveaux fichiers :
- `config/translation_service.py` : Service principal DeepL
- `config/rosetta_views.py` : Vues web pour l'intégration
- `competitions/management/commands/translate_missing.py` : Commande Django
- `templates/admin/deepl_status.html` : Interface de statut
- `templates/admin/batch_translate.html` : Interface de traduction en lot
- `static/admin/js/deepl_integration.js` : Intégration JavaScript
- `docs/DEEPL_INTEGRATION_GUIDE.md` : Ce guide

### Fichiers modifiés :
- `requirements.txt` : Ajout de deepl==1.19.0
- `config/settings/base.py` : Configuration DeepL
- `config/urls.py` : URLs pour les vues DeepL

## Bonnes pratiques

### 1. Gestion des coûts
- Utilisez l'interface de statut pour surveiller l'utilisation
- Commencez par `--dry-run` pour estimer les coûts
- Utilisez des traductions en lot pour réduire les appels API

### 2. Qualité des traductions
- Révisez toujours les traductions automatiques
- Utilisez DeepL comme point de départ, pas comme solution finale
- Testez avec des termes spécifiques aux arts martiaux

### 3. Workflow recommandé
1. Créez vos chaînes de traduction en français (langue source)
2. Utilisez `python manage.py makemessages` pour générer les fichiers .po
3. Utilisez la commande `translate_missing` pour les traductions automatiques
4. Révisez et corrigez dans Rosetta
5. Compilez avec `python manage.py compilemessages`

## Dépannage

### Problèmes courants

1. **Service non disponible**
   - Vérifiez la variable `DEEPL_API_KEY`
   - Vérifiez votre quota DeepL
   - Consultez les logs Django

2. **Traductions de mauvaise qualité**
   - Vérifiez le mapping des langues
   - Ajustez les termes spécifiques dans un glossaire
   - Utilisez des contextes plus spécifiques

3. **Erreurs de commande**
   - Vérifiez que les fichiers .po existent
   - Utilisez `python manage.py makemessages` avant la traduction
   - Vérifiez les permissions sur les fichiers .po

### Logs et debugging

Activez les logs pour le service DeepL :
```python
LOGGING = {
    'loggers': {
        'config.translation_service': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Limites et considérations

### Limites DeepL
- Compte gratuit : 500 000 caractères/mois
- Certaines langues peuvent ne pas être supportées
- API rate limits

### Considérations techniques
- Les traductions sont synchrones (pas de traitement en arrière-plan)
- Les gros volumes peuvent prendre du temps
- Pas de cache de traduction intégré

## Support et contribution

- Documentez les problèmes dans le fichier `docs/DEEPL_INTEGRATION_GUIDE.md`
- Testez les nouvelles fonctionnalités avec `--dry-run`
- Gardez les glossaires de termes spécifiques aux arts martiaux

---

*Cette intégration a été développée spécifiquement pour MartialComp et optimisée pour la terminologie des arts martiaux.*