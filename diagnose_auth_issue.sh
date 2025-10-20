#!/bin/bash

# Script de diagnostic approfondi pour les problèmes d'authentification

echo "=== DIAGNOSTIC APPROFONDI DE L'AUTHENTIFICATION ==="
echo ""

HTTPDOCS_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
cd "${HTTPDOCS_DIR}"

# 1. Tester la connexion avec curl
echo "1. Test de connexion avec curl..."
echo "----------------------------"

# Obtenir le token CSRF
echo "Récupération du token CSRF..."
CSRF_TOKEN=$(curl -s -c cookies.txt https://martialcomp.com/accounts/login/ | grep -oP 'csrfmiddlewaretoken" value="\K[^"]+' | head -1)

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Impossible de récupérer le token CSRF"
else
    echo "✓ Token CSRF récupéré: ${CSRF_TOKEN:0:20}..."
fi

# 2. Vérifier les redirections
echo ""
echo "2. Vérification des redirections..."
echo "Requête vers /dashboard/ sans auth:"
curl -s -I -L --max-redirs 5 https://martialcomp.com/dashboard/ 2>&1 | grep -E "HTTP|Location"

# 3. Vérifier les logs en temps réel
echo ""
echo "3. Dernières erreurs d'authentification dans les logs..."
grep -i "auth\|login\|session" logs/django.log | tail -20

# 4. Vérifier le middleware OnboardingRedirect
echo ""
echo "4. Vérification du middleware OnboardingRedirect..."
/var/www/vhosts/martialcomp.com/venv/bin/python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Vérifier l'utilisateur de test
try:
    user = User.objects.get(username='TESTBGA_USER1')
    print(f"✓ Utilisateur trouvé: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Actif: {user.is_active}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Superuser: {user.is_superuser}")
    
    # Vérifier le profil
    try:
        from apps.competitions.models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            print(f"  - Role: {profile.role if hasattr(profile, 'role') else 'Non défini'}")
            print(f"  - Onboarding step: {getattr(profile, 'onboarding_step', 'Non défini')}")
        else:
            print("  - ⚠️  Pas de profil UserProfile")
    except Exception as e:
        print(f"  - Erreur profil: {e}")
        
except User.DoesNotExist:
    print("❌ Utilisateur TESTBGA_USER1 non trouvé!")
except Exception as e:
    print(f"❌ Erreur: {e}")
EOF

# 5. Analyser les cookies envoyés
echo ""
echo "5. Analyse des headers de réponse..."
curl -s -I -v https://martialcomp.com/accounts/login/ 2>&1 | grep -i "set-cookie\|cookie"

# 6. Vérifier LOGIN_URL et LOGIN_REDIRECT_URL
echo ""
echo "6. Configuration des URLs de login..."
/var/www/vhosts/martialcomp.com/venv/bin/python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings

print(f"LOGIN_URL: {settings.LOGIN_URL}")
print(f"LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"LOGOUT_REDIRECT_URL: {getattr(settings, 'LOGOUT_REDIRECT_URL', 'Non défini')}")
print(f"\nACCOUNT_LOGIN_URL: {getattr(settings, 'ACCOUNT_LOGIN_URL', 'Non défini')}")
print(f"ACCOUNT_LOGOUT_URL: {getattr(settings, 'ACCOUNT_LOGOUT_URL', 'Non défini')}")
print(f"ACCOUNT_LOGIN_REDIRECT_URL: {getattr(settings, 'ACCOUNT_LOGIN_REDIRECT_URL', 'Non défini')}")
EOF

# 7. Nettoyage des fichiers temporaires
rm -f cookies.txt

echo ""
echo "============================================"
echo "ANALYSE TERMINÉE"
echo "============================================"
echo ""
echo "Points à vérifier:"
echo "1. L'utilisateur TESTBGA_USER1 a-t-il un UserProfile avec un role défini?"
echo "2. Le middleware OnboardingRedirect redirige-t-il en boucle?"
echo "3. Les cookies sont-ils correctement définis sur le domaine?"
echo "4. Y a-t-il un conflit entre LOGIN_URL et ACCOUNT_LOGIN_URL?"
echo ""
echo "============================================"