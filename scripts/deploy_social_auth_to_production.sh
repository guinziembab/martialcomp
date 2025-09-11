#!/bin/bash

echo "🚀 Déploiement de l'authentification sociale vers la production"
echo "============================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du projet Django"
    exit 1
fi

echo "📦 Étape 1: Installation de django-allauth sur le serveur de production..."

# Installer django-allauth sur le serveur
sudo apt update && sudo apt install -y python3-django-allauth

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation de django-allauth"
    exit 1
fi

echo "✅ django-allauth installé avec succès"

echo ""
echo "📁 Étape 2: Mise à jour des fichiers de configuration..."

# Sauvegarder les fichiers actuels
sudo cp config/settings.py config/settings.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp config/urls.py config/urls.py.backup_$(date +%Y%m%d_%H%M%S)

echo "✅ Fichiers de configuration sauvegardés"

echo ""
echo "⚙️  Étape 3: Application des modifications..."

# Décommenter les applications allauth dans settings.py
sudo sed -i 's/# *'"'"'allauth'"'"'/'"'"'allauth'"'"'/g' config/settings.py
sudo sed -i 's/# *'"'"'allauth\.account'"'"'/'"'"'allauth.account'"'"'/g' config/settings.py
sudo sed -i 's/# *'"'"'allauth\.socialaccount'"'"'/'"'"'allauth.socialaccount'"'"'/g' config/settings.py
sudo sed -i 's/# *'"'"'allauth\.socialaccount\.providers\.google'"'"'/'"'"'allauth.socialaccount.providers.google'"'"'/g' config/settings.py
sudo sed -i 's/# *'"'"'allauth\.socialaccount\.providers\.facebook'"'"'/'"'"'allauth.socialaccount.providers.facebook'"'"'/g' config/settings.py
sudo sed -i 's/# *'"'"'allauth\.socialaccount\.providers\.apple'"'"'/'"'"'allauth.socialaccount.providers.apple'"'"'/g' config/settings.py

# Ajouter le middleware allauth
if ! grep -q "allauth.account.middleware.AccountMiddleware" config/settings.py; then
    sudo sed -i '/django.contrib.auth.middleware.AuthenticationMiddleware/a\    '"'"'allauth.account.middleware.AccountMiddleware'"'"',  # Middleware allauth requis' config/settings.py
fi

# Décommenter l'authentication backend
sudo sed -i 's/# *'"'"'allauth\.account\.auth_backends\.AuthenticationBackend'"'"'/'"'"'allauth.account.auth_backends.AuthenticationBackend'"'"'/g' config/settings.py

# Décommenter les paramètres allauth
sudo sed -i 's/^# *ACCOUNT_AUTHENTICATION_METHOD/ACCOUNT_AUTHENTICATION_METHOD/g' config/settings.py
sudo sed -i 's/^# *ACCOUNT_EMAIL_REQUIRED/ACCOUNT_EMAIL_REQUIRED/g' config/settings.py
sudo sed -i 's/^# *ACCOUNT_UNIQUE_EMAIL/ACCOUNT_UNIQUE_EMAIL/g' config/settings.py
sudo sed -i 's/^# *ACCOUNT_USERNAME_REQUIRED/ACCOUNT_USERNAME_REQUIRED/g' config/settings.py
sudo sed -i 's/^# *ACCOUNT_EMAIL_VERIFICATION/ACCOUNT_EMAIL_VERIFICATION/g' config/settings.py
sudo sed -i 's/^# *ACCOUNT_ADAPTER/ACCOUNT_ADAPTER/g' config/settings.py
sudo sed -i 's/^# *SOCIALACCOUNT_ADAPTER/SOCIALACCOUNT_ADAPTER/g' config/settings.py

# Remplacer l'URL Django auth par allauth dans urls.py
sudo sed -i "s|path('accounts/', include('django.contrib.auth.urls'))|path('accounts/', include('allauth.urls'))|g" config/urls.py

echo "✅ Modifications appliquées aux fichiers de configuration"

echo ""
echo "🗄️  Étape 4: Exécution des migrations..."

sudo -u www-data python3 manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors des migrations"
    exit 1
fi

echo "✅ Migrations exécutées avec succès"

echo ""
echo "🔍 Étape 5: Vérification de la configuration..."

sudo -u www-data python3 manage.py check

if [ $? -ne 0 ]; then
    echo "❌ Erreur de configuration détectée"
    exit 1
fi

echo "✅ Configuration Django valide"

echo ""
echo "🔄 Étape 6: Redémarrage des services..."

# Redémarrer Gunicorn
sudo systemctl restart gunicorn

# Recharger Nginx  
sudo systemctl reload nginx

echo "✅ Services redémarrés"

echo ""
echo "🎉 Déploiement terminé avec succès !"
echo "============================================================="
echo ""
echo "📋 Résumé du déploiement:"
echo "   ✅ django-allauth installé en production"
echo "   ✅ Fichiers de configuration mis à jour"
echo "   ✅ Migrations exécutées"
echo "   ✅ Services redémarrés"
echo ""
echo "🔍 Vérification:"
echo "   - Testez: https://martialcomp.com/accounts/login/"
echo "   - Testez: https://martialcomp.com/accounts/signup/"
echo ""
echo "📚 Prochaines étapes:"
echo "   1. Configurer les fournisseurs sociaux (Google, Facebook, Apple)"
echo "   2. Ajouter les clés API dans les variables d'environnement"
echo "   3. Tester l'authentification sociale complète"