#!/bin/bash

echo "🚀 Déploiement complet de l'authentification sociale (Production PostgreSQL)"
echo "==========================================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du projet Django"
    exit 1
fi

echo "📊 Étape 1: Vérification de la base de données PostgreSQL..."

# Tester la connexion PostgreSQL
python3 manage.py shell -c "
from django.db import connection;
cursor = connection.cursor();
cursor.execute('SELECT current_database(), current_user, version()');
result = cursor.fetchone();
print(f'✅ Base: {result[0]}');
print(f'✅ Utilisateur: {result[1]}');
print(f'✅ Version: {result[2][:50]}...');
"

if [ $? -ne 0 ]; then
    echo "❌ Erreur de connexion PostgreSQL"
    exit 1
fi

echo ""
echo "🗄️  Étape 2: Vérification des migrations allauth..."

# Vérifier que toutes les migrations allauth sont appliquées
python3 manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors des migrations"
    exit 1
fi

echo "✅ Migrations vérifiées"

echo ""
echo "🏗️  Étape 3: Configuration des fournisseurs sociaux..."

# Exécuter le script de configuration des fournisseurs sociaux
python3 setup_social_providers_production.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la configuration des fournisseurs sociaux"
    exit 1
fi

echo ""
echo "👤 Étape 4: Vérification du superutilisateur admin..."

# Vérifier s'il existe déjà un superutilisateur
ADMIN_EXISTS=$(python3 manage.py shell -c "
from django.contrib.auth.models import User;
admins = User.objects.filter(is_superuser=True);
print('YES' if admins.exists() else 'NO')
" 2>/dev/null | tail -1)

if [ "$ADMIN_EXISTS" = "NO" ]; then
    echo "🔐 Création d'un superutilisateur admin..."
    echo "   Veuillez entrer les informations pour l'admin:"
    python3 manage.py createsuperuser
else
    echo "✅ Superutilisateur existant trouvé"
fi

echo ""
echo "🔍 Étape 5: Vérification de la configuration finale..."

# Test des URLs allauth
echo "📡 Test des URLs d'authentification sociale..."

# Vérifier que le serveur Django répond
if ! pgrep -f "manage.py runserver" > /dev/null; then
    echo "🔄 Démarrage du serveur Django..."
    nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
    sleep 5
fi

# Tester les URLs principales
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
echo "📋 Étape 6: Résumé de la configuration..."

# Afficher le résumé des applications sociales créées
python3 manage.py shell -c "
from allauth.socialaccount.models import SocialApp;
from django.contrib.sites.models import Site;

print('📊 RÉSUMÉ DE LA CONFIGURATION:');
print('=' * 40);

try:
    site = Site.objects.get(id=1);
    print(f'🌐 Site: {site.domain} - {site.name}');
except:
    print('❌ Site non configuré');

apps = SocialApp.objects.all();
print(f'📱 Applications sociales: {apps.count()}');
for app in apps:
    configured = '🔐' if not app.client_id.startswith('YOUR_') else '⚠️';
    print(f'   {configured} {app.name} ({app.provider})');
    print(f'      Client ID: {app.client_id[:20]}...');

print('');
print('🔗 URLs de redirection configurées:');
for app in apps:
    provider = app.provider;
    print(f'   {provider}: https://martialcomp.com/accounts/{provider}/login/callback/');
"

echo ""
echo "🎉 Déploiement terminé avec succès !"
echo "==========================================================================="
echo ""
echo "🔄 PROCHAINES ÉTAPES:"
echo ""
echo "1. 📱 Configurer Google OAuth2:"
echo "   - Aller sur https://console.cloud.google.com/"
echo "   - Créer les identifiants OAuth 2.0"
echo "   - URL de redirection: https://martialcomp.com/accounts/google/login/callback/"
echo ""
echo "2. 📘 Configurer Facebook Login:"
echo "   - Aller sur https://developers.facebook.com/"
echo "   - Créer une app Facebook"
echo "   - URL de redirection: https://martialcomp.com/accounts/facebook/login/callback/"
echo ""
echo "3. 🍎 Configurer Apple Sign In:"
echo "   - Aller sur https://developer.apple.com/"
echo "   - Créer un Services ID"
echo "   - URL de redirection: https://martialcomp.com/accounts/apple/login/callback/"
echo ""
echo "4. 🔐 Mettre à jour les clés API:"
echo "   - Éditer update_social_keys_production.py"
echo "   - Remplacer les placeholders par les vraies clés"
echo "   - Exécuter: python3 update_social_keys_production.py"
echo ""
echo "5. 🌐 Tester l'authentification:"
echo "   - Aller sur https://martialcomp.com/accounts/login/"
echo "   - Vérifier que les boutons sociaux apparaissent"
echo ""
echo "6. 🛠️  Administration Django:"
echo "   - Aller sur https://martialcomp.com/admin/"
echo "   - Section 'Social Applications' pour gérer les fournisseurs"
echo ""
echo "📚 Pour le guide détaillé: python3 update_social_keys_production.py --guide"