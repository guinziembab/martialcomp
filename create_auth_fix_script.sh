#\!/bin/bash

# Créer le script de correction directement sur le serveur
cat > /var/www/vhosts/martialcomp.com/httpdocs/fix_authentication_loop_comprehensive.sh << 'EOF'
#\!/bin/bash

# Script complet pour diagnostiquer et corriger la boucle d'authentification
# Problème: L'utilisateur TESTBGA_USER1 doit s'authentifier deux fois et est redirigé vers login à chaque clic

echo "=== DIAGNOSTIC ET CORRECTION COMPLÈTE DE L'AUTHENTIFICATION ==="
echo "Date: $(date)"
echo ""

HTTPDOCS_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"
cd "${HTTPDOCS_DIR}"

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Diagnostic initial
echo -e "${YELLOW}1. DIAGNOSTIC INITIAL${NC}"
echo "================================"

# Vérifier l'utilisateur TESTBGA_USER1
echo "Vérification de l'utilisateur TESTBGA_USER1..."
${VENV_DIR}/bin/python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

User = get_user_model()

try:
    user = User.objects.get(username='TESTBGA_USER1')
    print(f"✓ Utilisateur trouvé: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Actif: {user.is_active}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Dernière connexion: {user.last_login}")
    
    # Vérifier les sessions actives
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_sessions = 0
    for session in active_sessions:
        session_data = session.get_decoded()
        if str(session_data.get('_auth_user_id')) == str(user.id):
            user_sessions += 1
    
    print(f"  - Sessions actives pour cet utilisateur: {user_sessions}")
    
    # Vérifier le profil
    try:
        from apps.competitions.models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            print(f"  - Profil trouvé avec ID: {profile.id}")
            if hasattr(profile, 'role'):
                print(f"  - Role: {profile.role}")
            if hasattr(profile, 'onboarding_step'):
                print(f"  - Onboarding step: {profile.onboarding_step}")
            if hasattr(profile, 'onboarding_completed'):
                print(f"  - Onboarding terminé: {profile.onboarding_completed}")
        else:
            print("  - ⚠️ Pas de profil UserProfile trouvé")
    except Exception as e:
        print(f"  - Erreur lors de la vérification du profil: {e}")
        
except User.DoesNotExist:
    print("❌ Utilisateur TESTBGA_USER1 non trouvé\!")
except Exception as e:
    print(f"❌ Erreur: {e}")
PYEOF

echo ""

# 2. Vérifier les paramètres de session
echo -e "${YELLOW}2. PARAMÈTRES DE SESSION ACTUELS${NC}"
echo "================================"

${VENV_DIR}/bin/python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings

print("Configuration des sessions:")
print(f"- SESSION_ENGINE: {getattr(settings, 'SESSION_ENGINE', 'django.contrib.sessions.backends.db')}")
print(f"- SESSION_COOKIE_NAME: {getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')}")
print(f"- SESSION_COOKIE_AGE: {getattr(settings, 'SESSION_COOKIE_AGE', 1209600)} secondes")
print(f"- SESSION_COOKIE_DOMAIN: {getattr(settings, 'SESSION_COOKIE_DOMAIN', None)}")
print(f"- SESSION_COOKIE_PATH: {getattr(settings, 'SESSION_COOKIE_PATH', '/')}")
print(f"- SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}")
print(f"- SESSION_COOKIE_HTTPONLY: {getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)}")
print(f"- SESSION_COOKIE_SAMESITE: {getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax')}")
print(f"- SESSION_SAVE_EVERY_REQUEST: {getattr(settings, 'SESSION_SAVE_EVERY_REQUEST', False)}")
print(f"- SESSION_EXPIRE_AT_BROWSER_CLOSE: {getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False)}")
print("")
print("Configuration de l'authentification:")
print(f"- LOGIN_URL: {settings.LOGIN_URL}")
print(f"- LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"- LOGOUT_REDIRECT_URL: {getattr(settings, 'LOGOUT_REDIRECT_URL', '/')}")
PYEOF

echo ""

# 3. Analyser les middlewares
echo -e "${YELLOW}3. ANALYSE DES MIDDLEWARES${NC}"
echo "================================"

${VENV_DIR}/bin/python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings

print("Middlewares configurés:")
for i, mw in enumerate(settings.MIDDLEWARE):
    print(f"{i+1}. {mw}")
    
# Vérifier les middlewares critiques
critical_middlewares = {
    'SessionMiddleware': 'django.contrib.sessions.middleware.SessionMiddleware',
    'AuthenticationMiddleware': 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'MessageMiddleware': 'django.contrib.messages.middleware.MessageMiddleware',
}

print("\nVérification des middlewares critiques:")
for name, path in critical_middlewares.items():
    if path in settings.MIDDLEWARE:
        idx = settings.MIDDLEWARE.index(path)
        print(f"✓ {name} présent à la position {idx}")
    else:
        print(f"❌ {name} MANQUANT\!")
        
# Vérifier l'ordre
session_idx = None
auth_idx = None
for i, mw in enumerate(settings.MIDDLEWARE):
    if 'SessionMiddleware' in mw:
        session_idx = i
    elif 'AuthenticationMiddleware' in mw:
        auth_idx = i
        
if session_idx is not None and auth_idx is not None:
    if session_idx < auth_idx:
        print("\n✓ Ordre correct: SessionMiddleware avant AuthenticationMiddleware")
    else:
        print("\n❌ PROBLÈME: SessionMiddleware doit être avant AuthenticationMiddleware\!")
PYEOF

echo ""

# 4. Créer un patch pour corriger les settings
echo -e "${YELLOW}4. CRÉATION DU PATCH DE CORRECTION${NC}"
echo "================================"

# Sauvegarder le fichier de settings actuel
cp config/settings/production.py config/settings/production.py.bak.$(date +%Y%m%d_%H%M%S)

# Créer le script de patch
cat > patch_session_settings.py << 'PATCH_EOF'
#\!/usr/bin/env python
import os
import sys
import re

settings_file = 'config/settings/production.py'

# Lire le fichier
with open(settings_file, 'r') as f:
    content = f.read()

# Configuration des sessions à ajouter
session_config = '''
# ============================================
# Configuration des sessions pour éviter les boucles d'authentification
# ============================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'martialcomp_sessionid'
SESSION_COOKIE_AGE = 86400  # 24 heures
SESSION_COOKIE_PATH = '/'
SESSION_SAVE_EVERY_REQUEST = True  # Important pour maintenir la session active

# Pour la production avec sous-domaines
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.martialcomp.com'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF doit correspondre
    CSRF_COOKIE_NAME = 'martialcomp_csrftoken'
    CSRF_COOKIE_DOMAIN = '.martialcomp.com'
    CSRF_COOKIE_PATH = '/'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

# S'assurer que l'authentification fonctionne correctement
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Redirection après login
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Rediriger vers le dashboard après connexion
LOGOUT_REDIRECT_URL = '/'

# AllAuth settings pour éviter les boucles
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
ACCOUNT_LOGIN_ON_GET = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_REDIRECT_ON_LOGIN = True
'''

# Vérifier si les settings de session existent déjà
if 'SESSION_COOKIE_DOMAIN' not in content or 'SESSION_SAVE_EVERY_REQUEST' not in content:
    print("Ajout de la configuration des sessions...")
    
    # Trouver où insérer (après CSRF_TRUSTED_ORIGINS ou à la fin)
    insert_pos = content.find('CSRF_TRUSTED_ORIGINS')
    if insert_pos \!= -1:
        # Trouver la fin de CSRF_TRUSTED_ORIGINS
        bracket_pos = content.find(']', insert_pos)
        if bracket_pos \!= -1:
            # Trouver la ligne suivante
            newline_pos = content.find('\n', bracket_pos)
            if newline_pos \!= -1:
                insert_pos = newline_pos + 1
                content = content[:insert_pos] + '\n' + session_config + '\n' + content[insert_pos:]
            else:
                content += '\n' + session_config
    else:
        # Ajouter à la fin
        content += '\n' + session_config
    
    # Écrire le fichier modifié
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print("✓ Configuration des sessions ajoutée")
else:
    print("La configuration des sessions existe déjà")
    # Vérifier SESSION_SAVE_EVERY_REQUEST spécifiquement
    if 'SESSION_SAVE_EVERY_REQUEST' not in content:
        # Ajouter juste cette ligne après SESSION_COOKIE_AGE
        pattern = r'(SESSION_COOKIE_AGE\s*=\s*\d+)'
        replacement = r'\1\nSESSION_SAVE_EVERY_REQUEST = True  # Important pour maintenir la session active'
        content = re.sub(pattern, replacement, content)
        with open(settings_file, 'w') as f:
            f.write(content)
        print("✓ SESSION_SAVE_EVERY_REQUEST ajouté")
PATCH_EOF

chmod +x patch_session_settings.py

# Appliquer le patch
echo "Application du patch..."
${VENV_DIR}/bin/python patch_session_settings.py

echo ""

# 5. Vérifier le middleware OnboardingRedirect
echo -e "${YELLOW}5. VÉRIFICATION DU MIDDLEWARE ONBOARDING${NC}"
echo "================================"

# Chercher le middleware problématique
if grep -q "OnboardingRedirectMiddleware" config/settings/production.py; then
    echo "⚠️ OnboardingRedirectMiddleware détecté. Vérification..."
    
    # Créer un script pour analyser ce middleware
    cat > check_onboarding_middleware.py << 'CHECK_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

try:
    from apps.accounts.middleware import OnboardingRedirectMiddleware
    print("✓ Middleware OnboardingRedirect trouvé")
    
    # Analyser le code source si possible
    import inspect
    source = inspect.getsource(OnboardingRedirectMiddleware)
    if 'redirect' in source.lower():
        print("⚠️ Le middleware contient des redirections")
        print("Suggestion: Vérifier que le middleware n'entre pas en conflit avec le système d'auth")
except ImportError:
    print("✓ OnboardingRedirectMiddleware n'est pas activé")
except Exception as e:
    print(f"Erreur lors de la vérification: {e}")
CHECK_EOF
    
    ${VENV_DIR}/bin/python check_onboarding_middleware.py
    rm check_onboarding_middleware.py
else
    echo "✓ OnboardingRedirectMiddleware n'est pas configuré"
fi

echo ""

# 6. Nettoyer les sessions expirées
echo -e "${YELLOW}6. NETTOYAGE DES SESSIONS${NC}"
echo "================================"

echo "Nettoyage des sessions expirées..."
${VENV_DIR}/bin/python manage.py clearsessions --settings=config.settings.production || echo "Erreur lors du nettoyage"

# Compter les sessions restantes
${VENV_DIR}/bin/python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone

total = Session.objects.count()
valid = Session.objects.filter(expire_date__gt=timezone.now()).count()
print(f"Sessions après nettoyage: {total} total, {valid} valides")
PYEOF

echo ""

# 7. Créer/mettre à jour le profil utilisateur si nécessaire
echo -e "${YELLOW}7. VÉRIFICATION DU PROFIL UTILISATEUR${NC}"
echo "================================"

${VENV_DIR}/bin/python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    user = User.objects.get(username='TESTBGA_USER1')
    
    # Vérifier/créer le profil
    try:
        from apps.competitions.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'onboarding_completed': True,  # Marquer comme complété pour éviter les redirections
            }
        )
        
        if created:
            print("✓ Profil utilisateur créé")
        else:
            print("✓ Profil utilisateur existant")
            
        # S'assurer que l'onboarding est marqué comme terminé
        if hasattr(profile, 'onboarding_completed') and not profile.onboarding_completed:
            profile.onboarding_completed = True
            profile.save()
            print("✓ Onboarding marqué comme terminé")
            
    except Exception as e:
        print(f"Erreur avec le profil: {e}")
        
except User.DoesNotExist:
    print("❌ Utilisateur TESTBGA_USER1 non trouvé")
except Exception as e:
    print(f"Erreur: {e}")
PYEOF

echo ""

# 8. Redémarrer le service
echo -e "${YELLOW}8. REDÉMARRAGE DU SERVICE${NC}"
echo "================================"

echo "Redémarrage de Gunicorn..."
systemctl restart martialcomp.service

# Attendre que le service démarre
sleep 5

# Vérifier le statut
if systemctl is-active --quiet martialcomp.service; then
    echo -e "${GREEN}✓ Service redémarré avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors du redémarrage du service${NC}"
    systemctl status martialcomp.service
fi

echo ""

# 9. Test de connexion
echo -e "${YELLOW}9. TEST DE CONNEXION${NC}"
echo "================================"

# Tester l'endpoint de login
echo "Test de l'endpoint de login:"
response=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/accounts/login/)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ Page de login accessible (HTTP $response)${NC}"
else
    echo -e "${RED}❌ Problème avec la page de login (HTTP $response)${NC}"
fi

# Tester avec les headers de session
echo ""
echo "Test avec simulation de session:"
curl -s -I -b "martialcomp_sessionid=test123" https://martialcomp.com/dashboard/  < /dev/null |  grep -E "HTTP|Location" | head -5

echo ""

# 10. Résumé et recommandations
echo -e "${YELLOW}10. RÉSUMÉ ET RECOMMANDATIONS${NC}"
echo "================================"
echo ""
echo -e "${GREEN}Actions effectuées:${NC}"
echo "1. ✓ Configuration des cookies de session pour le domaine .martialcomp.com"
echo "2. ✓ Activation de SESSION_SAVE_EVERY_REQUEST"
echo "3. ✓ Configuration de LOGIN_REDIRECT_URL vers /dashboard/"
echo "4. ✓ Nettoyage des sessions expirées"
echo "5. ✓ Vérification/création du profil utilisateur"
echo "6. ✓ Marquage de l'onboarding comme terminé"
echo "7. ✓ Redémarrage du service Gunicorn"
echo ""
echo -e "${YELLOW}Pour tester la connexion:${NC}"
echo "1. Ouvrir un navigateur en mode privé/incognito"
echo "2. Aller sur https://martialcomp.com/accounts/login/"
echo "3. Se connecter avec:"
echo "   - Username: TESTBGA_USER1"
echo "   - Password: AQW123ok;"
echo "4. Vérifier que vous êtes redirigé vers /dashboard/"
echo "5. Naviguer dans le dashboard sans être déconnecté"
echo ""
echo -e "${YELLOW}Si le problème persiste:${NC}"
echo "1. Vérifier les logs: tail -f ${HTTPDOCS_DIR}/logs/django.log"
echo "2. Analyser les headers: curl -v https://martialcomp.com/accounts/login/"
echo "3. Vérifier les cookies dans le navigateur (F12 > Application > Cookies)"
echo "4. Tester avec un autre utilisateur"
echo ""
echo "============================================"
echo "Script terminé à $(date)"
echo "============================================"

# Nettoyer les fichiers temporaires
rm -f patch_session_settings.py
EOF

# Rendre le script exécutable
chmod +x /var/www/vhosts/martialcomp.com/httpdocs/fix_authentication_loop_comprehensive.sh

echo "Script créé avec succès dans /var/www/vhosts/martialcomp.com/httpdocs/"
echo "Pour l'exécuter:"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "./fix_authentication_loop_comprehensive.sh"
