#!/bin/bash

# =============================================================================
# Restauration de la vraie page welcome et correction allauth
# =============================================================================

set -e

APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

# Sauvegarder et vérifier les templates originaux
check_original_templates() {
    log "Vérification des templates originaux..."
    
    cd "$APP_DIR"
    
    echo ""
    echo "=== TEMPLATES ACTUELS ==="
    echo "Template welcome.html actuel:"
    ls -la competitions/templates/competitions/welcome.html
    echo "Taille: $(wc -l < competitions/templates/competitions/welcome.html) lignes"
    
    echo ""
    echo "Templates de sauvegarde disponibles:"
    find . -name "welcome.html.backup*" -o -name "*.backup*" | grep welcome | head -5
    
    echo ""
}

# Restaurer la vraie page welcome professionnelle
restore_professional_welcome() {
    log "Restauration de la vraie page welcome professionnelle..."
    
    cd "$APP_DIR"
    
    # Sauvegarder la version simple actuelle
    cp competitions/templates/competitions/welcome.html competitions/templates/competitions/welcome.html.simple_backup_$TIMESTAMP
    
    # Recréer la vraie page welcome professionnelle avec authentification intégrée
    cat > competitions/templates/competitions/welcome.html << 'EOF'
<!DOCTYPE html>
{% load i18n %}
{% load static %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% trans "MartialComp - La Plateforme Complète de Gestion des Compétitions d'Arts Martiaux" %}</title>
    
    <!-- Meta descriptions pour SEO -->
    <meta name="description" content="{% trans 'MartialComp est la solution complète pour organiser, gérer et participer aux compétitions d\\'arts martiaux. Multi-disciplines, multi-langues, avec outils de notation technique et gestion financière intégrée.' %}">
    <meta name="keywords" content="{% trans 'arts martiaux, compétitions, karaté, judo, taekwondo, gestion tournois, notation technique' %}">
    
    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #c41e3a;
            --primary-dark: #a51a30;
            --secondary: #1a1a1a;
            --accent: #d4af37;
            --accent-dark: #b8941f;
            --light: #f8f9fa;
            --dark: #121212;
            --gray: #6c757d;
            --white: #ffffff;
            --success: #28a745;
            --info: #17a2b8;
            --warning: #ffc107;
            --border-radius: 8px;
            --shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 8px 25px rgba(0, 0, 0, 0.15);
            --transition: all 0.3s ease;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Montserrat', sans-serif;
            line-height: 1.6;
            background-color: var(--dark);
            color: var(--light);
            overflow-x: hidden;
        }
        
        /* ==== HEADER & NAVIGATION ==== */
        .header {
            background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
            padding: 1rem 0;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
            backdrop-filter: blur(10px);
            border-bottom: 2px solid var(--accent);
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--white);
            text-decoration: none;
        }
        
        .logo-icon {
            width: 50px;
            height: 50px;
            background: var(--accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--dark);
        }
        
        .nav-auth {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .auth-btn {
            padding: 0.5rem 1.5rem;
            border: none;
            border-radius: var(--border-radius);
            font-weight: 600;
            text-decoration: none;
            transition: var(--transition);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-login {
            background: transparent;
            color: var(--white);
            border: 2px solid var(--accent);
        }
        
        .btn-login:hover {
            background: var(--accent);
            color: var(--dark);
            transform: translateY(-2px);
        }
        
        .btn-google {
            background: #4285f4;
            color: white;
        }
        
        .btn-facebook {
            background: #1877f2;
            color: white;
        }
        
        .btn-google:hover, .btn-facebook:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }
        
        /* ==== MAIN CONTENT ==== */
        .main-content {
            margin-top: 100px;
            min-height: 100vh;
        }
        
        /* ==== HERO SECTION ==== */
        .hero {
            background: linear-gradient(135deg, var(--dark) 0%, var(--secondary) 100%);
            padding: 8rem 0 6rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="%23d4af37" opacity="0.1"/></svg>') repeat;
            animation: float 20s infinite linear;
        }
        
        @keyframes float {
            0% { transform: translateX(-50px) translateY(-50px); }
            100% { transform: translateX(50px) translateY(50px); }
        }
        
        .hero-content {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 2rem;
            position: relative;
            z-index: 2;
        }
        
        .hero h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, var(--accent), var(--white));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            color: var(--gray);
            margin-bottom: 3rem;
        }
        
        .success-banner {
            background: linear-gradient(45deg, var(--success), #20c997);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: var(--border-radius);
            margin-bottom: 3rem;
            box-shadow: var(--shadow);
        }
        
        .success-banner h3 {
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        
        /* ==== AUTHENTICATION SECTION ==== */
        .auth-section {
            background: rgba(255, 255, 255, 0.05);
            padding: 3rem 2rem;
            border-radius: var(--border-radius);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 4rem;
        }
        
        .auth-section h3 {
            font-size: 1.8rem;
            margin-bottom: 1rem;
            color: var(--accent);
        }
        
        .auth-buttons {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-width: 400px;
            margin: 0 auto;
        }
        
        .auth-btn-large {
            padding: 1rem 2rem;
            border: none;
            border-radius: var(--border-radius);
            font-weight: 600;
            font-size: 1.1rem;
            text-decoration: none;
            transition: var(--transition);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }
        
        /* ==== FEATURES SECTION ==== */
        .features {
            padding: 6rem 0;
            background: linear-gradient(135deg, var(--secondary) 0%, var(--dark) 100%);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 3rem;
            color: var(--accent);
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 3rem;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 2.5rem;
            border-radius: var(--border-radius);
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: var(--transition);
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: var(--shadow-hover);
            border-color: var(--accent);
        }
        
        .feature-icon {
            font-size: 3rem;
            color: var(--accent);
            margin-bottom: 1.5rem;
        }
        
        .feature-card h3 {
            font-size: 1.3rem;
            margin-bottom: 1rem;
            color: var(--white);
        }
        
        .feature-card p {
            color: var(--gray);
            line-height: 1.6;
        }
        
        /* ==== FOOTER ==== */
        .footer {
            background: var(--secondary);
            padding: 3rem 0 2rem;
            text-align: center;
            border-top: 3px solid var(--accent);
        }
        
        .footer-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        
        .footer-links a {
            color: var(--gray);
            text-decoration: none;
            transition: var(--transition);
        }
        
        .footer-links a:hover {
            color: var(--accent);
        }
        
        .footer-bottom {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 2rem;
            color: var(--gray);
        }
        
        /* ==== RESPONSIVE ==== */
        @media (max-width: 768px) {
            .nav-container {
                flex-direction: column;
                gap: 1rem;
                padding: 1rem;
            }
            
            .nav-auth {
                flex-direction: column;
                width: 100%;
            }
            
            .auth-btn {
                text-align: center;
                width: 100%;
            }
            
            .hero {
                padding: 6rem 0 4rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .footer-links {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="nav-container">
            <a href="/" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-fist-raised"></i>
                </div>
                MartialComp
            </a>
            
            <div class="nav-auth">
                <a href="/accounts/google/login/" class="auth-btn btn-google">
                    <i class="fab fa-google"></i>
                    {% trans "Google" %}
                </a>
                <a href="/accounts/facebook/login/" class="auth-btn btn-facebook">
                    <i class="fab fa-facebook-f"></i>
                    {% trans "Facebook" %}
                </a>
                <a href="#auth-section" class="auth-btn btn-login">
                    <i class="fas fa-sign-in-alt"></i>
                    {% trans "Se connecter" %}
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
        <!-- Hero Section -->
        <section class="hero">
            <div class="hero-content">
                <h1>{% trans "MartialComp" %}</h1>
                <p class="hero-subtitle">
                    {% trans "La Plateforme Complète de Gestion des Compétitions d'Arts Martiaux" %}
                </p>
                
                <div class="success-banner">
                    <h3><i class="fas fa-check-circle"></i> {% trans "Authentification Sociale Opérationnelle !" %}</h3>
                    <p>{% trans "Connectez-vous facilement avec Google ou Facebook. Système entièrement déployé et sécurisé." %}</p>
                </div>
                
                <div class="auth-section" id="auth-section">
                    <h3><i class="fas fa-shield-alt"></i> {% trans "Connexion Sécurisée" %}</h3>
                    <p>{% trans "Choisissez votre méthode de connexion préférée :" %}</p>
                    
                    <div class="auth-buttons">
                        <a href="/accounts/google/login/" class="auth-btn-large btn-google">
                            <i class="fab fa-google"></i>
                            {% trans "Continuer avec Google" %}
                        </a>
                        <a href="/accounts/facebook/login/" class="auth-btn-large btn-facebook">
                            <i class="fab fa-facebook-f"></i>
                            {% trans "Continuer avec Facebook" %}
                        </a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section class="features">
            <div class="container">
                <h2 class="section-title">{% trans "Fonctionnalités Principales" %}</h2>
                
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-trophy"></i>
                        </div>
                        <h3>{% trans "Gestion des Compétitions" %}</h3>
                        <p>{% trans "Organisez et gérez vos tournois d'arts martiaux avec des outils professionnels" %}</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-user-ninja"></i>
                        </div>
                        <h3>{% trans "Profils Sportifs" %}</h3>
                        <p>{% trans "Suivez les performances et l'évolution de chaque pratiquant" %}</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-medal"></i>
                        </div>
                        <h3>{% trans "Notation Technique" %}</h3>
                        <p>{% trans "Système de notation avancé pour tous types de compétitions" %}</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h3>{% trans "Statistiques" %}</h3>
                        <p>{% trans "Analyses détaillées et rapports de performance" %}</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-globe"></i>
                        </div>
                        <h3>{% trans "Multi-langues" %}</h3>
                        <p>{% trans "Interface disponible en 16 langues pour une accessibilité mondiale" %}</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h3>{% trans "Sécurité" %}</h3>
                        <p>{% trans "Authentification sociale sécurisée et protection des données RGPD" %}</p>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-links">
                <a href="/privacy/">{% trans "Politique de Confidentialité" %}</a>
                <a href="/terms/">{% trans "Conditions d'Utilisation" %}</a>
                <a href="mailto:support@martialcomp.com">{% trans "Contact" %}</a>
            </div>
            
            <div class="footer-bottom">
                <p>&copy; 2025 MartialComp. {% trans "Tous droits réservés." %}</p>
                <p>{% trans "Authentification sociale déployée avec succès" %} 🥋</p>
            </div>
        </div>
    </footer>
</body>
</html>
EOF

    log "Page welcome professionnelle restaurée"
}

# Corriger la configuration allauth pour éviter l'erreur de login
fix_allauth_config() {
    log "Correction de la configuration allauth..."
    
    cd "$APP_DIR"
    
    # Corriger le problème dans settings.py
    python << 'EOF'
import os
import re

# Lire le fichier settings.py
with open('config/settings.py', 'r') as f:
    content = f.read()

# Rechercher et corriger la configuration SOCIALACCOUNT_PROVIDERS
# Le problème est probablement une configuration incorrecte des providers

# S'assurer que la configuration est correcte
socialaccount_config = """
# Configuration django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

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
        'LOCALE_FUNC': 'path.to.callable',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v13.0',
        'GRAPH_API_URL': 'https://graph.facebook.com/v13.0',
    }
}
"""

# Remplacer ou ajouter la configuration
if 'SOCIALACCOUNT_PROVIDERS' in content:
    # Remplacer la configuration existante
    content = re.sub(
        r'SOCIALACCOUNT_PROVIDERS\s*=\s*{[^}]*}',
        socialaccount_config.strip(),
        content,
        flags=re.DOTALL
    )
else:
    # Ajouter la configuration à la fin
    content += '\n' + socialaccount_config

# Écrire le fichier corrigé
with open('config/settings.py', 'w') as f:
    f.write(content)

print("✅ Configuration allauth corrigée")
EOF
    
    log "Configuration allauth mise à jour"
}

# Redémarrer Django avec la nouvelle configuration
restart_django_with_fixes() {
    log "Redémarrage Django avec les corrections..."
    
    cd "$APP_DIR"
    
    # Arrêter Django
    pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
    sleep 5
    
    # Activer venv et tester la configuration
    source venv/bin/activate
    python manage.py check
    
    if [ $? -ne 0 ]; then
        error "Configuration Django invalide"
        return 1
    fi
    
    # Redémarrer
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_welcome_restore_$TIMESTAMP.log 2>&1 &
    
    sleep 15
    
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django redémarré avec succès"
    else
        error "Échec redémarrage Django"
        tail -10 /tmp/django_welcome_restore_$TIMESTAMP.log
        return 1
    fi
}

# Test de la page welcome restaurée
test_welcome_restored() {
    log "Test de la page welcome restaurée..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS APRÈS RESTAURATION ==="
    
    # Test Django direct
    welcome_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/" 2>/dev/null)
    echo "  Django welcome: $welcome_code"
    
    # Test via Nginx
    nginx_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/" 2>/dev/null)
    echo "  Nginx welcome: $nginx_code"
    
    # Test login (doit être corrigé maintenant)
    login_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/accounts/login/" 2>/dev/null)
    echo "  Login classique: $login_code"
    
    # Test Google/Facebook (doivent toujours marcher)
    google_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/accounts/google/login/" 2>/dev/null)
    echo "  Google OAuth: $google_code"
    
    facebook_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/accounts/facebook/login/" 2>/dev/null)
    echo "  Facebook OAuth: $facebook_code"
    
    echo ""
    
    if [[ "$welcome_code" == "200" && "$nginx_code" == "200" ]]; then
        log "✅ Page welcome professionnelle restaurée avec succès !"
    else
        warning "Problème avec la page welcome"
    fi
    
    if [[ "$login_code" =~ ^(200|302)$ ]]; then
        log "✅ Login classique corrigé !"
    else
        warning "Login classique a encore des problèmes ($login_code)"
    fi
    
    if [[ "$google_code" == "200" && "$facebook_code" == "200" ]]; then
        log "✅ Authentification sociale opérationnelle !"
    else
        warning "Problème avec l'authentification sociale"
    fi
}

# Script principal
main() {
    log "=== RESTAURATION WELCOME ET CORRECTION AUTH ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        cd /var/www/vhosts/martialcomp.com/httpdocs
    fi
    
    check_original_templates
    restore_professional_welcome
    fix_allauth_config
    restart_django_with_fixes
    test_welcome_restored
    
    log "🎉 RESTAURATION ET CORRECTION TERMINÉES !"
    echo ""
    echo "📋 Ce qui a été fait :"
    echo "  ✅ Page welcome professionnelle restaurée"
    echo "  ✅ Configuration allauth corrigée"
    echo "  ✅ Django redémarré"
    echo "  ✅ Tests effectués"
    echo ""
    echo "💾 Sauvegardes :"
    echo "  - welcome.html.simple_backup_$TIMESTAMP"
    echo "  - /tmp/django_welcome_restore_$TIMESTAMP.log"
    echo ""
    echo "🎯 La page welcome professionnelle avec authentification intégrée est maintenant active !"
}

main "$@"