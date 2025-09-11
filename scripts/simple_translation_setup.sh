#!/bin/bash

echo "🌍 ACTIVATION SIMPLE DES TRADUCTIONS MARTIALCOMP"
echo "================================================"

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Ce script doit être exécuté depuis le répertoire contenant manage.py"
    exit 1
fi

echo "✅ Répertoire vérifié: $(pwd)"

# 1. Sauvegarder les settings actuels
echo "💾 Sauvegarde des settings..."
cp config/settings.py config/settings.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Settings sauvegardés"

# 2. Ajouter la configuration i18n
echo "⚙️ Configuration i18n..."
cat >> config/settings.py << 'EOF'

# ===========================================
# INTERNATIONALISATION - SYSTÈME MULTILINGUE
# ===========================================

USE_I18N = True
USE_L10N = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('pt', 'Português'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Ajouter rosetta et modeltranslation aux apps
import sys
if 'rosetta' not in INSTALLED_APPS:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['rosetta', 'modeltranslation']

# Ajouter LocaleMiddleware
if 'django.middleware.locale.LocaleMiddleware' not in MIDDLEWARE:
    middleware_list = list(MIDDLEWARE)
    # Insérer après SessionMiddleware
    session_index = next((i for i, mw in enumerate(middleware_list) if 'SessionMiddleware' in mw), 1)
    middleware_list.insert(session_index + 1, 'django.middleware.locale.LocaleMiddleware')
    MIDDLEWARE = middleware_list

EOF

echo "✅ Configuration i18n ajoutée"

# 3. Compiler les traductions
echo "🔨 Compilation des traductions..."
source venv/bin/activate
python manage.py compilemessages
echo "✅ Traductions compilées"

# 4. Collecter les fichiers statiques
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput
echo "✅ Fichiers statiques collectés"

# 5. Redémarrer le serveur Django
echo "🔄 Redémarrage du serveur..."
pkill -f "python.*manage.py.*runserver" 2>/dev/null || true
sleep 2
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &
echo "✅ Serveur redémarré"

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "=================================="
echo "URLs à tester:"
echo "• http://localhost:8000/fr/ (Français)"
echo "• http://localhost:8000/en/ (Anglais)"
echo "• http://localhost:8000/es/ (Espagnol)"
echo "• http://localhost:8000/rosetta/ (Interface traduction)"
echo ""
echo "Pour voir les logs: tail -f /tmp/django.log"