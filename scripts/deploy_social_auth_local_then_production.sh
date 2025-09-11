#!/bin/bash

echo "🚀 Déploiement de l'authentification sociale (Local SQLite puis Production PostgreSQL)"
echo "===================================================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du projet Django"
    exit 1
fi

echo "📊 Étape 1: Configuration locale avec SQLite..."

# Configuration des fournisseurs sociaux en local avec SQLite
python3 setup_social_providers.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la configuration locale"
    exit 1
fi

echo "✅ Configuration locale terminée"

echo ""
echo "📦 Étape 2: Création du package de déploiement pour PostgreSQL..."

# Créer un script spécifique pour la production PostgreSQL
cat > deploy_to_postgresql_production.py << 'EOF'
#!/usr/bin/env python3

import os
import sys
import django
import psycopg2

def deploy_to_postgresql():
    """Script à exécuter sur le serveur de production PostgreSQL."""
    
    print("🚀 Déploiement PostgreSQL en production")
    print("=" * 50)
    
    # Configuration PostgreSQL
    db_config = {
        'host': 'localhost',
        'database': 'martialcomp_db',
        'user': 'martialcomp_user',
        'password': 'zBx43V22'
    }
    
    # Tester la connexion PostgreSQL
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), current_user, version();")
        result = cursor.fetchone()
        print(f"✅ Base: {result[0]}")
        print(f"✅ Utilisateur: {result[1]}")
        print(f"✅ Version: {result[2][:50]}...")
        conn.close()
    except Exception as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    
    # Modifier temporairement Django pour PostgreSQL
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Patch des paramètres Django pour PostgreSQL
    import config.settings as settings
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'martialcomp_db',
            'USER': 'martialcomp_user',
            'PASSWORD': 'zBx43V22',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    
    django.setup()
    
    from django.contrib.sites.models import Site
    from allauth.socialaccount.models import SocialApp
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Configuration du site
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={'domain': 'martialcomp.com', 'name': 'MartialComp'}
            )
            print(f"✅ Site: {site.domain}")
            
            # Supprimer les anciennes applications
            SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']).delete()
            
            # Créer les applications sociales
            providers = [
                ('google', 'Google OAuth2', 'YOUR_GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_SECRET'),
                ('facebook', 'Facebook Login', 'YOUR_FACEBOOK_APP_ID', 'YOUR_FACEBOOK_APP_SECRET'),
                ('apple', 'Sign in with Apple', 'YOUR_APPLE_SERVICES_ID', 'YOUR_APPLE_PRIVATE_KEY')
            ]
            
            for provider, name, client_id, secret in providers:
                app = SocialApp.objects.create(
                    provider=provider,
                    name=name,
                    client_id=client_id,
                    secret=secret
                )
                app.sites.add(site)
                print(f"✅ {name} créé")
            
            print("🎉 Configuration PostgreSQL terminée !")
            return True
            
    except Exception as e:
        print(f"❌ Erreur Django: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    deploy_to_postgresql()
EOF

chmod +x deploy_to_postgresql_production.py

echo "✅ Script PostgreSQL créé"

echo ""
echo "📋 Étape 3: Création du guide de déploiement production..."

cat > PRODUCTION_DEPLOYMENT_GUIDE.md << 'EOF'
# Guide de Déploiement - Authentification Sociale (Production PostgreSQL)

## Étape 1: Sur le serveur de production

### 1.1 Installer les dépendances PostgreSQL
```bash
sudo apt update
sudo apt install -y python3-psycopg2 python3-django-allauth
```

### 1.2 Configurer la base de données PostgreSQL
```bash
# Modifier config/settings.py pour activer PostgreSQL
sed -i 's/# DATABASES = {/DATABASES = {/' config/settings.py
sed -i 's/#     '"'"'default'"'"'/    '"'"'default'"'"'/' config/settings.py
sed -i 's/#         '"'"'ENGINE'"'"'/        '"'"'ENGINE'"'"'/' config/settings.py
sed -i 's/#         '"'"'NAME'"'"'/        '"'"'NAME'"'"'/' config/settings.py
sed -i 's/#         '"'"'USER'"'"'/        '"'"'USER'"'"'/' config/settings.py
sed -i 's/#         '"'"'PASSWORD'"'"'/        '"'"'PASSWORD'"'"'/' config/settings.py
sed -i 's/#         '"'"'HOST'"'"'/        '"'"'HOST'"'"'/' config/settings.py
sed -i 's/#         '"'"'PORT'"'"'/        '"'"'PORT'"'"'/' config/settings.py
sed -i 's/#     }/    }/' config/settings.py
sed -i 's/# }/}/' config/settings.py

# Commenter SQLite
sed -i 's/DATABASES = {/# DATABASES = {/' config/settings.py
sed -i 's/    '"'"'default'"'"'/    # '"'"'default'"'"'/' config/settings.py
sed -i 's/        '"'"'ENGINE'"'"': '"'"'django.db.backends.sqlite3'"'"'/        # '"'"'ENGINE'"'"': '"'"'django.db.backends.sqlite3'"'"'/' config/settings.py
sed -i 's/        '"'"'NAME'"'"': BASE_DIR/        # '"'"'NAME'"'"': BASE_DIR/' config/settings.py
sed -i 's/    }/    # }/' config/settings.py
sed -i 's/}/# }/' config/settings.py
```

### 1.3 Exécuter les migrations
```bash
python3 manage.py migrate
```

### 1.4 Configurer les fournisseurs sociaux
```bash
python3 deploy_to_postgresql_production.py
```

## Étape 2: Configuration des consoles développeur

### 2.1 Google OAuth2
- Console: https://console.cloud.google.com/
- URL de redirection: https://martialcomp.com/accounts/google/login/callback/

### 2.2 Facebook Login  
- Console: https://developers.facebook.com/
- URL de redirection: https://martialcomp.com/accounts/facebook/login/callback/

### 2.3 Apple Sign In
- Console: https://developer.apple.com/
- URL de redirection: https://martialcomp.com/accounts/apple/login/callback/

## Étape 3: Mise à jour des clés API

1. Récupérer les clés des consoles développeur
2. Modifier le script update_social_keys_production.py
3. Exécuter: `python3 update_social_keys_production.py`

## Étape 4: Test

- Aller sur https://martialcomp.com/accounts/login/
- Vérifier que les boutons sociaux apparaissent
EOF

echo "✅ Guide de déploiement créé"

echo ""
echo "🔍 Étape 4: Vérification locale..."

# Test des URLs en local
echo "📡 Test des URLs d'authentification sociale (local)..."

if ! pgrep -f "manage.py runserver" > /dev/null; then
    echo "🔄 Démarrage du serveur Django local..."
    nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
    sleep 5
fi

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
echo "📊 Résumé des applications créées (local SQLite):"
python3 manage.py shell -c "
from allauth.socialaccount.models import SocialApp;
apps = SocialApp.objects.all();
print(f'📱 Applications sociales: {apps.count()}');
for app in apps:
    print(f'   ✅ {app.name} ({app.provider})');
"

echo ""
echo "🎉 Configuration locale terminée avec succès !"
echo "===================================================================================="
echo ""
echo "🔄 PROCHAINES ÉTAPES POUR LA PRODUCTION:"
echo ""
echo "1. 📁 Transférer les fichiers sur le serveur de production:"
echo "   - deploy_to_postgresql_production.py"
echo "   - update_social_keys_production.py"
echo "   - PRODUCTION_DEPLOYMENT_GUIDE.md"
echo ""
echo "2. 📊 Sur le serveur de production:"
echo "   - Suivre le guide PRODUCTION_DEPLOYMENT_GUIDE.md"
echo "   - Activer PostgreSQL dans config/settings.py"
echo "   - Exécuter les migrations et configurations"
echo ""
echo "3. 🔐 Configurer les fournisseurs sociaux:"
echo "   - Google: https://console.cloud.google.com/"
echo "   - Facebook: https://developers.facebook.com/"
echo "   - Apple: https://developer.apple.com/"
echo ""
echo "4. 🌐 Tester sur https://martialcomp.com/accounts/login/"
echo ""
echo "📚 Documentation complète dans PRODUCTION_DEPLOYMENT_GUIDE.md"