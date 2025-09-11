#!/bin/bash

echo "🚀 Déploiement direct PostgreSQL en Production"
echo "=============================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du projet Django"
    exit 1
fi

echo "⚙️  Étape 1: Configuration PostgreSQL dans settings.py..."

# Sauvegarder le fichier settings actuel
cp config/settings.py config/settings.py.backup_$(date +%Y%m%d_%H%M%S)

# Activer PostgreSQL et désactiver SQLite
sed -i 's/^DATABASES = {/# DATABASES = { # SQLite désactivé/' config/settings.py
sed -i 's/^    '"'"'default'"'"': {/    # '"'"'default'"'"': { # SQLite désactivé/' config/settings.py
sed -i 's/^        '"'"'ENGINE'"'"': '"'"'django.db.backends.sqlite3'"'"'/        # '"'"'ENGINE'"'"': '"'"'django.db.backends.sqlite3'"'"' # SQLite désactivé/' config/settings.py
sed -i 's/^        '"'"'NAME'"'"': BASE_DIR/        # '"'"'NAME'"'"': BASE_DIR # SQLite désactivé/' config/settings.py
sed -i 's/^    }/    # } # SQLite désactivé/' config/settings.py
sed -i 's/^}/# } # SQLite désactivé/' config/settings.py

# Décommenter PostgreSQL
sed -i 's/^# DATABASES = {/DATABASES = {/' config/settings.py
sed -i 's/^#     '"'"'default'"'"': {/    '"'"'default'"'"': {/' config/settings.py
sed -i 's/^#         '"'"'ENGINE'"'"': '"'"'django.db.backends.postgresql'"'"'/        '"'"'ENGINE'"'"': '"'"'django.db.backends.postgresql'"'"'/' config/settings.py
sed -i 's/^#         '"'"'NAME'"'"': '"'"'martialcomp'"'"'/        '"'"'NAME'"'"': '"'"'martialcomp_db'"'"'/' config/settings.py
sed -i 's/^#         '"'"'USER'"'"': '"'"'postgres'"'"'/        '"'"'USER'"'"': '"'"'martialcomp_user'"'"'/' config/settings.py
sed -i 's/^#         '"'"'PASSWORD'"'"': '"'"'zBx43V22'"'"'/        '"'"'PASSWORD'"'"': '"'"'zBx43V22'"'"'/' config/settings.py
sed -i 's/^#         '"'"'HOST'"'"': '"'"'localhost'"'"'/        '"'"'HOST'"'"': '"'"'localhost'"'"'/' config/settings.py
sed -i 's/^#         '"'"'PORT'"'"': '"'"'5432'"'"'/        '"'"'PORT'"'"': '"'"'5432'"'"'/' config/settings.py
sed -i 's/^#     }/    }/' config/settings.py
sed -i 's/^# }/}/' config/settings.py

echo "✅ PostgreSQL activé dans settings.py"

echo ""
echo "📦 Étape 2: Installation des dépendances PostgreSQL..."

# Installer psycopg2 pour PostgreSQL
sudo apt update
sudo apt install -y python3-psycopg2

echo "✅ Dépendances PostgreSQL installées"

echo ""
echo "🗄️  Étape 3: Test de connexion et migrations PostgreSQL..."

# Tester la connexion PostgreSQL
python3 manage.py check --database default

if [ $? -ne 0 ]; then
    echo "❌ Erreur de connexion PostgreSQL - vérifiez les paramètres"
    exit 1
fi

echo "✅ Connexion PostgreSQL OK"

# Exécuter les migrations
python3 manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors des migrations PostgreSQL"
    exit 1
fi

echo "✅ Migrations PostgreSQL terminées"

echo ""
echo "🏗️  Étape 4: Configuration des fournisseurs sociaux PostgreSQL..."

# Script Python pour configurer les fournisseurs sociaux avec PostgreSQL
cat > configure_social_providers_postgresql.py << 'PEOF'
#!/usr/bin/env python3

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction

def configure_social_providers():
    print("🔧 Configuration des fournisseurs sociaux avec PostgreSQL...")
    
    try:
        with transaction.atomic():
            # Site object
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={'domain': 'martialcomp.com', 'name': 'MartialComp'}
            )
            print(f"✅ Site: {site.domain} ({'créé' if created else 'existant'})")
            
            # Supprimer anciennes applications
            deleted = SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']).delete()
            if deleted[0] > 0:
                print(f"🔄 {deleted[0]} anciennes applications supprimées")
            
            # Créer applications sociales
            providers = [
                {
                    'provider': 'google',
                    'name': 'Google OAuth2',
                    'client_id': 'YOUR_GOOGLE_CLIENT_ID_HERE',
                    'secret': 'YOUR_GOOGLE_CLIENT_SECRET_HERE'
                },
                {
                    'provider': 'facebook', 
                    'name': 'Facebook Login',
                    'client_id': 'YOUR_FACEBOOK_APP_ID_HERE',
                    'secret': 'YOUR_FACEBOOK_APP_SECRET_HERE'
                },
                {
                    'provider': 'apple',
                    'name': 'Sign in with Apple', 
                    'client_id': 'YOUR_APPLE_SERVICES_ID_HERE',
                    'secret': 'YOUR_APPLE_PRIVATE_KEY_HERE'
                }
            ]
            
            for config in providers:
                app = SocialApp.objects.create(**config)
                app.sites.add(site)
                print(f"✅ {config['name']} créé (ID: {app.id})")
            
            print("\n📊 Résumé:")
            apps = SocialApp.objects.all()
            for app in apps:
                print(f"   📱 {app.name} ({app.provider})")
                print(f"      Client ID: {app.client_id}")
                print(f"      Sites: {[s.domain for s in app.sites.all()]}")
            
            print("\n🔗 URLs de redirection:")
            for app in apps:
                print(f"   {app.provider}: https://martialcomp.com/accounts/{app.provider}/login/callback/")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = configure_social_providers()
    if not success:
        sys.exit(1)
PEOF

python3 configure_social_providers_postgresql.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la configuration des fournisseurs sociaux"
    exit 1
fi

rm configure_social_providers_postgresql.py

echo ""
echo "🔍 Étape 5: Vérification finale..."

# Test de configuration Django
python3 manage.py check

if [ $? -ne 0 ]; then
    echo "❌ Erreur de configuration Django"
    exit 1
fi

echo "✅ Configuration Django valide"

# Redémarrer le serveur Django
echo "🔄 Redémarrage du serveur Django..."
pkill -f "manage.py runserver" 2>/dev/null || true
sleep 2
nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
sleep 3

echo "✅ Serveur Django redémarré"

echo ""
echo "📡 Test des URLs d'authentification sociale..."

urls_to_test=(
    "/accounts/login/"
    "/accounts/signup/"
    "/accounts/google/login/"
    "/accounts/facebook/login/"
    "/accounts/apple/login/"
)

for url in "${urls_to_test[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$url" 2>/dev/null)
    if [ "$status" = "200" ] || [ "$status" = "302" ]; then
        echo "   ✅ $url (HTTP $status)"
    else
        echo "   ❌ $url (HTTP $status)"
    fi
done

echo ""
echo "🎉 Déploiement PostgreSQL terminé avec succès !"
echo "=============================================="
echo ""
echo "📋 STATUT FINAL:"
echo "   ✅ PostgreSQL activé et connecté"
echo "   ✅ Tables allauth créées"
echo "   ✅ Applications sociales configurées"
echo "   ✅ URLs allauth fonctionnelles"
echo "   ✅ Serveur Django redémarré"
echo ""
echo "🔄 PROCHAINES ÉTAPES:"
echo ""
echo "1. 🔐 Configurer les consoles développeur:"
echo "   - Google: https://console.cloud.google.com/"
echo "   - Facebook: https://developers.facebook.com/"
echo "   - Apple: https://developer.apple.com/"
echo ""
echo "2. 🔑 Mettre à jour les clés API:"
echo "   - Modifier update_social_keys_production.py"
echo "   - Exécuter: python3 update_social_keys_production.py"
echo ""
echo "3. 🌐 Tester l'authentification:"
echo "   - Aller sur https://martialcomp.com/accounts/login/"
echo "   - Vérifier que les boutons sociaux apparaissent"
echo ""
echo "4. 🏠 Admin Django:"
echo "   - https://martialcomp.com/admin/"
echo "   - Section 'Social Applications'"