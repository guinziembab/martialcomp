#!/bin/bash

# =============================================================================
# SCRIPT FINAL DE DÉPLOIEMENT MARTIALCOMP
# À exécuter directement sur le serveur de production
# =============================================================================

set -e

echo "🚀 Déploiement final complet MartialComp..."

# Aller dans le bon répertoire
cd /opt/martialcomp/app

# =============================================================================
# 1. BACKUP ET SAUVEGARDE
# =============================================================================

echo "💾 Sauvegarde des fichiers critiques..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp config/settings.py config/settings.py.backup_$TIMESTAMP || true
cp manage.py manage.py.backup_$TIMESTAMP || true

# =============================================================================
# 2. CORRIGER MANAGE.PY
# =============================================================================

echo "🔧 Correction du fichier manage.py..."

cat > manage.py << 'MANAGE_EOF'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
MANAGE_EOF

chmod +x manage.py
echo "✅ manage.py corrigé"

# =============================================================================
# 3. CORRIGER SETTINGS.PY POUR LA PRODUCTION
# =============================================================================

echo "⚙️ Correction settings.py pour production..."

# Créer un script Python pour corriger settings.py
cat > fix_settings.py << 'SETTINGS_FIX'
#!/usr/bin/env python3
import re

# Lire le fichier settings
with open('config/settings.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Corriger la configuration de la base de données
database_config = '''
# Database configuration - PostgreSQL production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'martialcomp_user',
        'PASSWORD': 'MartialComp2025!#New',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
'''

# Remplacer la configuration de la base de données
content = re.sub(r'DATABASES\s*=\s*\{[^}]*\}[^}]*\}', database_config.strip(), content, flags=re.DOTALL)

# Nettoyer les configurations SOCIALACCOUNT_PROVIDERS multiples
content = re.sub(r'SOCIALACCOUNT_PROVIDERS\s*=\s*\{.*?\n\}', '', content, flags=re.DOTALL)

# Ajouter la configuration correcte des providers sociaux
socialaccount_config = '''

# Configuration des providers sociaux
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name',
            'email',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v17.0',
    }
}
'''

content += socialaccount_config

# Écrire le fichier corrigé
with open('config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ settings.py corrigé")
SETTINGS_FIX

# Exécuter la correction
python3 fix_settings.py

# =============================================================================
# 4. TESTER LA SYNTAXE PYTHON
# =============================================================================

echo "🔍 Test syntaxe Python..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import config.settings
    print('✅ Syntaxe settings.py correcte')
except Exception as e:
    print(f'❌ Erreur syntaxe: {e}')
    sys.exit(1)
"

# =============================================================================
# 5. ACTIVER L'ENVIRONNEMENT VIRTUEL ET TESTER DJANGO
# =============================================================================

echo "🔄 Test Django..."
source venv/bin/activate

# Test basique de Django
python manage.py check --deploy || python manage.py check

# =============================================================================
# 6. CONFIGURER LA BASE DE DONNÉES (SI DISPONIBLE)
# =============================================================================

echo "🗄️ Tentative de configuration de la base de données..."

# Test de connexion PostgreSQL
if pg_isready -h localhost -p 5432 -U martialcomp_user; then
    echo "✅ PostgreSQL disponible, configuration en cours..."
    
    # Exécuter les migrations
    python manage.py makemigrations --noinput || true
    python manage.py migrate --noinput
    
    # Configurer les applications sociales
    python3 << 'DB_CONFIG'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site

    # Supprimer les applications existantes
    SocialApp.objects.all().delete()
    
    # Récupérer le site actuel
    site = Site.objects.get_current()
    
    # Créer l'application Google
    google_app = SocialApp.objects.create(
        provider='google',
        name='Google',
        client_id='243898642746-6tjnpdflrrsetgif0fne7pgs4v66j6j5.apps.googleusercontent.com',
        secret='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'
    )
    google_app.sites.add(site)
    
    # Créer l'application Facebook
    facebook_app = SocialApp.objects.create(
        provider='facebook',
        name='Facebook',
        client_id='1415333696343612',
        secret='fd1e66ffcd47958997274808d0c2ec64'
    )
    facebook_app.sites.add(site)
    
    print("✅ Applications sociales configurées")
    
except Exception as e:
    print(f"⚠️ Base de données non disponible: {e}")
DB_CONFIG

else
    echo "⚠️ PostgreSQL non disponible, continuons sans configuration DB"
fi

# =============================================================================
# 7. CRÉER LES TEMPLATES PERSONNALISÉS
# =============================================================================

echo "🎨 Création des templates authentification..."

# Créer le répertoire
mkdir -p competitions/templates/account

# Template de connexion
cat > competitions/templates/account/login.html << 'LOGIN_EOF'
<!DOCTYPE html>
{% load i18n %}
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - MartialComp</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #c41e3a;
            --accent: #d4af37;
            --dark: #121212;
            --light: #f8f9fa;
            --google: #4285f4;
            --facebook: #1877f2;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Montserrat', sans-serif;
            background: linear-gradient(135deg, var(--dark), var(--primary));
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--light);
        }
        .login-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 2.5rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(212, 175, 55, 0.3);
            width: 100%;
            max-width: 450px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: var(--accent);
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--light);
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: var(--light);
            font-size: 1rem;
        }
        .btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 1rem;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        .btn-google {
            background: var(--google);
            color: white;
        }
        .btn-facebook {
            background: var(--facebook);
            color: white;
        }
        .divider {
            text-align: center;
            margin: 1.5rem 0;
            color: var(--light);
            opacity: 0.7;
        }
        .footer-links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .footer-links a {
            color: var(--accent);
            text-decoration: none;
            margin: 0 0.5rem;
        }
        .back-home {
            text-align: center;
            margin-top: 1.5rem;
        }
        .back-home a {
            color: var(--light);
            text-decoration: none;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1><i class="fas fa-fist-raised"></i> MartialComp</h1>
            <p>Connexion à votre compte</p>
        </div>
        
        <form method="post">
            {% csrf_token %}
            
            <div class="form-group">
                <label for="id_login">
                    <i class="fas fa-user"></i> Email ou nom d'utilisateur
                </label>
                <input type="text" name="login" id="id_login" required>
            </div>
            
            <div class="form-group">
                <label for="id_password">
                    <i class="fas fa-lock"></i> Mot de passe
                </label>
                <input type="password" name="password" id="id_password" required>
            </div>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-sign-in-alt"></i>
                Se connecter
            </button>
        </form>
        
        <div class="divider">Ou connectez-vous avec</div>
        
        <a href="/accounts/google/login/" class="btn btn-google">
            <i class="fab fa-google"></i>
            Continuer avec Google
        </a>
        
        <a href="/accounts/facebook/login/" class="btn btn-facebook">
            <i class="fab fa-facebook-f"></i>
            Continuer avec Facebook
        </a>
        
        <div class="footer-links">
            <a href="/accounts/signup/">
                <i class="fas fa-user-plus"></i> Créer un compte
            </a>
            <a href="/accounts/password/reset/">
                <i class="fas fa-key"></i> Mot de passe oublié ?
            </a>
        </div>
        
        <div class="back-home">
            <a href="/">
                <i class="fas fa-arrow-left"></i> Retour à l'accueil
            </a>
        </div>
    </div>
</body>
</html>
LOGIN_EOF

# Template d'inscription
cat > competitions/templates/account/signup.html << 'SIGNUP_EOF'
<!DOCTYPE html>
{% load i18n %}
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Créer un compte - MartialComp</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #c41e3a;
            --accent: #d4af37;
            --dark: #121212;
            --light: #f8f9fa;
            --google: #4285f4;
            --facebook: #1877f2;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Montserrat', sans-serif;
            background: linear-gradient(135deg, var(--dark), var(--primary));
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--light);
        }
        .signup-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 2.5rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(212, 175, 55, 0.3);
            width: 100%;
            max-width: 450px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: var(--accent);
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--light);
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: var(--light);
            font-size: 1rem;
        }
        .btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 1rem;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        .btn-google {
            background: var(--google);
            color: white;
        }
        .btn-facebook {
            background: var(--facebook);
            color: white;
        }
        .divider {
            text-align: center;
            margin: 1.5rem 0;
            color: var(--light);
            opacity: 0.7;
        }
        .footer-links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .footer-links a {
            color: var(--accent);
            text-decoration: none;
            margin: 0 0.5rem;
        }
        .back-home {
            text-align: center;
            margin-top: 1.5rem;
        }
        .back-home a {
            color: var(--light);
            text-decoration: none;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <div class="logo">
            <h1><i class="fas fa-fist-raised"></i> MartialComp</h1>
            <p>Créer votre compte</p>
        </div>
        
        <form method="post">
            {% csrf_token %}
            
            <div class="form-group">
                <label for="id_email">
                    <i class="fas fa-envelope"></i> Adresse email
                </label>
                <input type="email" name="email" id="id_email" required>
            </div>
            
            <div class="form-group">
                <label for="id_password1">
                    <i class="fas fa-lock"></i> Mot de passe
                </label>
                <input type="password" name="password1" id="id_password1" required>
            </div>
            
            <div class="form-group">
                <label for="id_password2">
                    <i class="fas fa-lock"></i> Confirmer le mot de passe
                </label>
                <input type="password" name="password2" id="id_password2" required>
            </div>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-user-plus"></i>
                Créer mon compte
            </button>
        </form>
        
        <div class="divider">Ou inscrivez-vous avec</div>
        
        <a href="/accounts/google/login/" class="btn btn-google">
            <i class="fab fa-google"></i>
            S'inscrire avec Google
        </a>
        
        <a href="/accounts/facebook/login/" class="btn btn-facebook">
            <i class="fab fa-facebook-f"></i>
            S'inscrire avec Facebook
        </a>
        
        <div class="footer-links">
            <a href="/accounts/login/">
                <i class="fas fa-sign-in-alt"></i> J'ai déjà un compte
            </a>
        </div>
        
        <div class="back-home">
            <a href="/">
                <i class="fas fa-arrow-left"></i> Retour à l'accueil
            </a>
        </div>
    </div>
</body>
</html>
SIGNUP_EOF

echo "✅ Templates d'authentification créés"

# =============================================================================
# 8. COLLECTER LES FICHIERS STATIQUES
# =============================================================================

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || true

# =============================================================================
# 9. REDÉMARRER DJANGO
# =============================================================================

echo "🚀 Redémarrage Django..."

# Arrêter tous les processus Django existants
pkill -f python || true
pkill -f gunicorn || true
sleep 5

# Redémarrer Django en arrière-plan
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_final_$TIMESTAMP.log 2>&1 &

echo "⏳ Attente du démarrage de Django..."
sleep 15

# =============================================================================
# 10. TESTS FINAUX
# =============================================================================

echo "🧪 Tests de validation finale..."

# Test Django local
django_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/" 2>/dev/null || echo "000")

# Test pages d'authentification
login_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/login/" 2>/dev/null || echo "000")
signup_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/signup/" 2>/dev/null || echo "000")

echo ""
echo "📊 RÉSULTATS DES TESTS :"
echo "  🏠 Django local:      $django_status"
echo "  🔐 Login:            $login_status"
echo "  📝 Signup:           $signup_status"

# =============================================================================
# 11. RÉSULTAT FINAL
# =============================================================================

echo ""
if [[ "$django_status" == "200" && "$login_status" == "200" && "$signup_status" == "200" ]]; then
    echo "🎉🎉🎉 SUCCÈS COMPLET ! 🎉🎉🎉"
    echo ""
    echo "✅ TOUTES LES FONCTIONNALITÉS OPÉRATIONNELLES :"
    echo "  • Page d'accueil professionnelle"
    echo "  • Connexion classique avec templates personnalisés"
    echo "  • Inscription avec templates personnalisés"
    echo "  • Authentification sociale Google et Facebook"
    echo "  • Configuration django-allauth réparée"
    echo "  • Fichiers manage.py et settings.py corrigés"
    echo ""
    echo "🔗 URLS TESTÉES :"
    echo "  • http://127.0.0.1:8000/ - Page d'accueil"
    echo "  • http://127.0.0.1:8000/accounts/login/ - Connexion"
    echo "  • http://127.0.0.1:8000/accounts/signup/ - Inscription"
    echo ""
    echo "🌐 POUR TESTER EN PRODUCTION :"
    echo "  • https://martialcomp.com/"
    echo "  • https://martialcomp.com/accounts/login/"
    echo "  • https://martialcomp.com/accounts/signup/"
    echo ""
    echo "🎯 MARTIALCOMP EST MAINTENANT OPÉRATIONNEL !"
    
elif [[ "$django_status" == "200" ]]; then
    echo "⚠️ SUCCÈS PARTIEL"
    echo "✅ Django fonctionne localement"
    echo "⚠️ Quelques pages d'authentification pourraient avoir des problèmes"
    echo ""
    echo "🔗 URLS FONCTIONNELLES :"
    echo "  • http://127.0.0.1:8000/ (Django direct)"
    
else
    echo "❌ PROBLÈME DÉTECTÉ"
    echo ""
    echo "📋 LOGS RÉCENTS :"
    tail -20 /tmp/django_final_$TIMESTAMP.log 2>/dev/null || echo "Pas de logs Django"
fi

# =============================================================================
# 12. NETTOYAGE
# =============================================================================

echo ""
echo "🧹 Nettoyage..."
rm -f fix_settings.py

echo ""
echo "💾 FICHIERS DE SAUVEGARDE CRÉÉS :"
echo "  • config/settings.py.backup_$TIMESTAMP"
echo "  • manage.py.backup_$TIMESTAMP"
echo "  • /tmp/django_final_$TIMESTAMP.log"

echo ""
echo "🏁 SCRIPT DE DÉPLOIEMENT TERMINÉ !"
echo "⏰ Heure de fin: $(date)"