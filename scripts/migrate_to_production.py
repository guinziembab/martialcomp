#!/usr/bin/env python3
"""
Script de migration vers la production
"""

def create_migration_package():
    """Créer un package de migration pour la production"""
    print("📦 CRÉATION DU PACKAGE DE MIGRATION")
    print("=" * 60)
    
    migration_files = [
        # Templates
        ('competitions/templates/competitions/welcome.html', 'Page d\'accueil multilingue redesignée'),
        
        # Configuration multilingue
        ('locale/', 'Structure locale complète avec 16 langues'),
        ('config/settings.py', 'Configuration multilingue (extrait)'),
        ('config/urls.py', 'URLs avec support multilingue'),
        
        # Apps et utilitaires
        ('competitions/templatetags/translation_helpers.py', 'Template tags pour traductions'),
        ('competitions/views/translation_dashboard.py', 'Dashboard de gestion des traductions'),
        ('competitions/management/commands/translate_messages.py', 'Commande de traduction automatique'),
        ('utils/translate_po.py', 'Script de traduction automatique DeepL'),
        
        # Scripts utilitaires
        ('compile_translations.py', 'Compilation manuelle des traductions'),
        ('setup_multilingual.py', 'Setup automatique du système multilingue'),
    ]
    
    print("📋 FICHIERS À MIGRER:")
    for file_path, description in migration_files:
        print(f"  • {file_path}")
        print(f"    {description}")
        print()
    
    # Créer le guide de migration
    migration_guide = """
# GUIDE DE MIGRATION MULTILINGUE VERS PRODUCTION

## 🎯 OBJECTIF
Migrer le système multilingue complet de MartialComp vers l'environnement de production.

## 📦 CONTENU DE LA MIGRATION

### 1. PAGE D'ACCUEIL REDESIGNÉE
- ✅ Template welcome.html complètement redesigné
- ✅ Design moderne avec CSS responsive
- ✅ Sélecteur de langue intégré
- ✅ Sections : Hero, Value proposition, Target audiences, etc.

### 2. SYSTÈME MULTILINGUE COMPLET
- ✅ 16 langues supportées : fr, en, es, it, de, no, ja, zh, hi, ar, sw, am, zu, yo, pt, ko
- ✅ Structure locale/ avec fichiers PO/MO pour toutes les langues
- ✅ Configuration Django i18n complète
- ✅ Support django-rosetta et django-modeltranslation

### 3. OUTILS DE DÉVELOPPEMENT
- ✅ Interface de gestion des traductions (Rosetta)
- ✅ Dashboard personnalisé pour les statistiques
- ✅ Scripts de traduction automatique avec DeepL
- ✅ Template tags intelligents pour les traductions
- ✅ Commandes de management Django

## 🚀 PROCÉDURE DE MIGRATION

### Phase 1: Backup
```bash
# Backup de l'environnement de production actuel
cp -r /path/to/production /path/to/backup_$(date +%Y%m%d_%H%M%S)
```

### Phase 2: Copie des fichiers
```bash
# Copier les fichiers depuis l'environnement de développement
scp -r locale/ user@production:/path/to/martialcomp/
scp competitions/templates/competitions/welcome.html user@production:/path/to/martialcomp/competitions/templates/competitions/
scp -r competitions/templatetags/ user@production:/path/to/martialcomp/competitions/
# ... autres fichiers
```

### Phase 3: Configuration
```bash
# Installer les packages requis
pip install django-rosetta django-modeltranslation polib deepl

# Ajouter à settings.py de production:
INSTALLED_APPS += [
    'modeltranslation',  # Avant admin
    'rosetta',
]

MIDDLEWARE += [
    'django.middleware.locale.LocaleMiddleware',
]

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('pt', 'Português'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']
MODELTRANSLATION_LANGUAGES = ('fr', 'en', 'es', 'de', 'it')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'
ROSETTA_REQUIRES_AUTH = True
```

### Phase 4: Migrations et compilation
```bash
# Appliquer les migrations modeltranslation
python manage.py makemigrations
python manage.py migrate

# Compiler les traductions
python manage.py compilemessages

# OU utiliser le script personnalisé
python compile_translations.py

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### Phase 5: Test
```bash
# Redémarrer le serveur de production
sudo systemctl restart martialcomp

# Tester les URLs
curl -I https://your-domain.com/
curl -I https://your-domain.com/fr/admin/
curl -I https://your-domain.com/rosetta/
```

## 🔧 URLS DE PRODUCTION À TESTER

- ✅ Page d'accueil : https://your-domain.com/
- ✅ Admin avec langue : https://your-domain.com/fr/admin/
- ✅ Interface Rosetta : https://your-domain.com/rosetta/
- ✅ Sélecteur de langue : https://your-domain.com/set-language/

## 📊 VÉRIFICATIONS POST-MIGRATION

1. **Interface multilingue** : Sélecteur de langue visible et fonctionnel
2. **Rosetta accessible** : Interface de traduction disponible
3. **Traductions chargées** : Vérifier que les fichiers MO sont compilés
4. **Performance** : Pas d'impact sur les temps de réponse
5. **Design responsive** : Page d'accueil s'affiche correctement sur mobile

## 🎯 AVANTAGES DE CETTE MIGRATION

- ✅ **Environnement stable** : Production déjà fonctionnelle
- ✅ **Pas de debug Windows** : Évite les problèmes de développement local
- ✅ **Test immédiat** : Vérification en conditions réelles
- ✅ **Backup facile** : Rollback possible en cas de problème
- ✅ **Utilisateurs finaux** : Test direct avec de vrais utilisateurs

## 🚨 POINTS D'ATTENTION

1. **Backup obligatoire** avant toute migration
2. **Test en staging** si disponible
3. **Migration graduelle** : Par phases si possible
4. **Monitoring** : Surveiller les logs après migration
5. **Rollback plan** : Procédure de retour en arrière préparée

## 📞 SUPPORT POST-MIGRATION

- Interface Rosetta : /rosetta/ (authentification admin requise)
- Dashboard traductions : /admin/translations/dashboard/
- Logs Django : Surveiller les erreurs i18n
- Performance : Vérifier l'impact des middlewares multilingues
"""
    
    with open('MIGRATION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(migration_guide)
    
    print("✅ Guide de migration créé : MIGRATION_GUIDE.md")
    
    # Créer un script de déploiement
    deploy_script = """#!/bin/bash
# Script de déploiement multilingue

echo "🚀 DÉPLOIEMENT MULTILINGUE MARTIALCOMP"
echo "======================================"

# Vérifications préalables
echo "1. Vérifications..."
python --version
pip list | grep -E "(django|rosetta|modeltranslation)"

# Backup
echo "2. Backup..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
cp -r . "../$BACKUP_DIR"
echo "Backup créé: $BACKUP_DIR"

# Installation des dépendances
echo "3. Installation des packages..."
pip install django-rosetta django-modeltranslation polib

# Migrations
echo "4. Migrations..."
python manage.py makemigrations
python manage.py migrate

# Compilation des traductions
echo "5. Compilation des traductions..."
python manage.py compilemessages || python compile_translations.py

# Collecte des fichiers statiques
echo "6. Fichiers statiques..."
python manage.py collectstatic --noinput

# Test de base
echo "7. Tests de base..."
python manage.py check

echo "✅ DÉPLOIEMENT TERMINÉ!"
echo "🔗 Testez: https://your-domain.com/"
echo "🌍 Rosetta: https://your-domain.com/rosetta/"
"""
    
    with open('deploy_multilingual.sh', 'w', encoding='utf-8') as f:
        f.write(deploy_script)
    
    print("✅ Script de déploiement créé : deploy_multilingual.sh")
    print()
    print("🎯 PROCHAINES ÉTAPES:")
    print("1. Consultez MIGRATION_GUIDE.md pour la procédure complète")
    print("2. Transférez les fichiers vers la production") 
    print("3. Exécutez deploy_multilingual.sh sur le serveur de production")
    print("4. Testez les URLs de production")

if __name__ == '__main__':
    create_migration_package()