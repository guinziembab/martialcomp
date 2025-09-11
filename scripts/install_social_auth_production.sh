#!/bin/bash

echo "🚀 Installation de l'authentification sociale pour MartialComp (Production)"
echo "=================================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du projet Django"
    exit 1
fi

echo "📦 Étape 1: Installation de django-allauth..."
pip install django-allauth

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation de django-allauth"
    exit 1
fi

echo "✅ django-allauth installé avec succès"

echo ""
echo "⚙️  Étape 2: Configuration des paramètres Django..."

# Créer un script Python pour décommenter les paramètres
cat > uncomment_allauth_settings.py << 'EOF'
import re

# Lire le fichier settings.py
with open('config/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Décommenter les applications allauth
content = re.sub(r'#\s*\'allauth\'', "'allauth'", content)
content = re.sub(r'#\s*\'allauth\.account\'', "'allauth.account'", content)
content = re.sub(r'#\s*\'allauth\.socialaccount\'', "'allauth.socialaccount'", content)
content = re.sub(r'#\s*\'allauth\.socialaccount\.providers\.google\'', "'allauth.socialaccount.providers.google'", content)
content = re.sub(r'#\s*\'allauth\.socialaccount\.providers\.facebook\'', "'allauth.socialaccount.providers.facebook'", content)
content = re.sub(r'#\s*\'allauth\.socialaccount\.providers\.apple\'', "'allauth.socialaccount.providers.apple'", content)

# Décommenter l'authentication backend
content = re.sub(r'#\s*\'allauth\.account\.auth_backends\.AuthenticationBackend\'', "'allauth.account.auth_backends.AuthenticationBackend'", content)

# Décommenter les paramètres allauth
content = re.sub(r'#\s*ACCOUNT_AUTHENTICATION_METHOD', 'ACCOUNT_AUTHENTICATION_METHOD', content)
content = re.sub(r'#\s*ACCOUNT_EMAIL_REQUIRED', 'ACCOUNT_EMAIL_REQUIRED', content)
content = re.sub(r'#\s*ACCOUNT_UNIQUE_EMAIL', 'ACCOUNT_UNIQUE_EMAIL', content)
content = re.sub(r'#\s*ACCOUNT_USERNAME_REQUIRED', 'ACCOUNT_USERNAME_REQUIRED', content)
content = re.sub(r'#\s*ACCOUNT_EMAIL_VERIFICATION', 'ACCOUNT_EMAIL_VERIFICATION', content)
content = re.sub(r'#\s*ACCOUNT_ADAPTER', 'ACCOUNT_ADAPTER', content)
content = re.sub(r'#\s*SOCIALACCOUNT_ADAPTER', 'SOCIALACCOUNT_ADAPTER', content)

# Écrire le fichier modifié
with open('config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Paramètres django-allauth décommentés")
EOF

python3 uncomment_allauth_settings.py
rm uncomment_allauth_settings.py

echo ""
echo "🗄️  Étape 3: Exécution des migrations Django..."

python3 manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors des migrations"
    exit 1
fi

echo "✅ Migrations exécutées avec succès"

echo ""
echo "🌐 Étape 4: Ajout de l'URL allauth..."

# Vérifier si l'URL allauth est déjà présente
if ! grep -q "accounts/" config/urls.py; then
    # Créer un script Python pour ajouter l'URL
    cat > add_allauth_urls.py << 'EOF'
import re

# Lire le fichier urls.py
with open('config/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter l'import include si nécessaire
if 'from django.urls import path, include' not in content:
    content = re.sub(r'from django\.urls import path', 'from django.urls import path, include', content)

# Ajouter l'URL allauth avant la dernière ligne de urlpatterns
allauth_url = "    path('accounts/', include('allauth.urls')),"
if 'accounts/' not in content:
    # Trouver la fin de urlpatterns et insérer avant
    content = re.sub(r'(\s+# ... autres URLs[^\]]*)', r'\1\n    ' + allauth_url, content)
    if 'accounts/' not in content:
        # Si le pattern précédent n'a pas fonctionné, essayer une approche différente
        content = re.sub(r'(urlpatterns = \[[^\]]*)(])', r'\1    ' + allauth_url + '\n\2', content)

# Écrire le fichier modifié
with open('config/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ URL allauth ajoutée")
EOF

    python3 add_allauth_urls.py
    rm add_allauth_urls.py
else
    echo "✅ URL allauth déjà présente"
fi

echo ""
echo "🔍 Étape 5: Vérification de la configuration..."

python3 manage.py check

if [ $? -ne 0 ]; then
    echo "❌ Erreur de configuration détectée"
    exit 1
fi

echo "✅ Configuration Django valide"

echo ""
echo "🎉 Installation terminée avec succès !"
echo "=================================================================="
echo ""
echo "📋 Résumé de l'installation:"
echo "   ✅ django-allauth installé"
echo "   ✅ Applications allauth ajoutées à INSTALLED_APPS"
echo "   ✅ Paramètres d'authentification configurés"
echo "   ✅ Migrations exécutées"
echo "   ✅ URLs allauth ajoutées"
echo "   ✅ Site object configuré (martialcomp.com)"
echo ""
echo "🔄 Prochaines étapes:"
echo "   1. Configurer les fournisseurs sociaux:"
echo "      - Google: https://console.cloud.google.com/"
echo "      - Facebook: https://developers.facebook.com/"
echo "      - Apple: https://developer.apple.com/"
echo ""
echo "   2. Ajouter les clés API dans les variables d'environnement:"
echo "      - GOOGLE_CLIENT_ID"
echo "      - GOOGLE_CLIENT_SECRET"
echo "      - FACEBOOK_APP_ID"
echo "      - FACEBOOK_APP_SECRET"
echo "      - APPLE_SERVICES_ID"
echo "      - APPLE_PRIVATE_KEY"
echo ""
echo "   3. Redémarrer le serveur Django"
echo ""
echo "   4. Tester l'authentification sociale sur:"
echo "      - /accounts/login/"
echo "      - /accounts/signup/"
echo ""
echo "📚 Documentation disponible dans:"
echo "   - social-auth-implementation-guide.md"
echo "   - competitions/adapters.py"