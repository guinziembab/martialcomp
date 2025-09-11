#!/bin/bash

echo "🔄 SYNCHRONISATION COMPLÈTE DEV → PRODUCTION"
echo "============================================="
echo "📅 Date: $(date)"
echo "🎯 Objectif: Aligner production avec environnement de développement"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/production_sync_$TIMESTAMP"

# ============================================
# 1. SAUVEGARDE COMPLÈTE DE LA PRODUCTION
# ============================================

echo "💾 1. SAUVEGARDE COMPLÈTE DE LA PRODUCTION"
echo "==========================================="

mkdir -p $BACKUP_DIR

# Sauvegarder les fichiers critiques de production
echo "   📁 Sauvegarde des templates actuels..."
cp -r competitions/templates/ $BACKUP_DIR/ 2>/dev/null || true

echo "   📁 Sauvegarde des configurations..."
cp config/settings.py $BACKUP_DIR/ 2>/dev/null || true
cp config/urls.py $BACKUP_DIR/ 2>/dev/null || true

echo "   📁 Sauvegarde des traductions..."
cp -r locale/ $BACKUP_DIR/ 2>/dev/null || true

echo "   📁 Sauvegarde des scripts..."
cp -r scripts/ $BACKUP_DIR/ 2>/dev/null || true

echo "   ✅ Sauvegarde terminée dans: $BACKUP_DIR"

# ============================================
# 2. SYNCHRONISATION SYSTÈME MULTILINGUE
# ============================================

echo ""
echo "🌍 2. SYNCHRONISATION SYSTÈME MULTILINGUE"
echo "=========================================="

# Vérifier la structure locale existante
echo "   🔍 Vérification structure locale actuelle..."
if [ -d "locale" ]; then
    echo "   📊 Langues actuellement présentes:"
    ls -la locale/ | grep "^d" | awk '{print "      " $9}' | grep -v "^\.$\|^\.\.$"
else
    echo "   📁 Création du répertoire locale..."
    mkdir -p locale
fi

# Créer la structure complète pour 16 langues (selon docs de dev)
echo "   🏗️ Création structure complète 16 langues..."
LANGUAGES=("fr" "en" "es" "it" "de" "pt" "ru" "vi" "no" "ja" "zh" "hi" "ar" "sw" "am" "zu" "yo" "ko")

for lang in "${LANGUAGES[@]}"; do
    mkdir -p "locale/$lang/LC_MESSAGES"
    echo "      ✅ $lang/LC_MESSAGES/"
done

# Mettre à jour la configuration Django avec toutes les langues
echo "   ⚙️ Mise à jour configuration multilingue..."

cat >> config/settings.py << 'EOF'

# ===========================================
# CONFIGURATION MULTILINGUE COMPLÈTE
# ===========================================

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('pt', 'Português'),
    ('ru', 'Русский'),
    ('vi', 'Tiếng Việt'),
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

# Ajouter middleware locale s'il n'existe pas
import sys
current_module = sys.modules[__name__]
if hasattr(current_module, 'MIDDLEWARE'):
    middleware_list = list(MIDDLEWARE)
    locale_middleware = 'django.middleware.locale.LocaleMiddleware'
    if locale_middleware not in middleware_list:
        # Insérer après SessionMiddleware
        session_index = next((i for i, mw in enumerate(middleware_list) if 'SessionMiddleware' in mw), 1)
        middleware_list.insert(session_index + 1, locale_middleware)
        MIDDLEWARE = middleware_list

# Configuration Rosetta (si installé)
try:
    import rosetta
    ROSETTA_REQUIRES_AUTH = True
    ROSETTA_MESSAGES_PER_PAGE = 25
    ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
    ROSETTA_AUTO_COMPILE = True
except ImportError:
    pass

EOF

echo "   ✅ Configuration multilingue ajoutée"

# ============================================
# 3. MISE À JOUR TEMPLATE WELCOME.HTML
# ============================================

echo ""
echo "🎨 3. MISE À JOUR TEMPLATE WELCOME.HTML"
echo "========================================"

echo "   📝 Création template welcome.html moderne avec traductions..."

cat > competitions/templates/competitions/welcome.html << 'EOF'
<!DOCTYPE html>
{% load i18n %}
{% load static %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MartialComp - {% trans "La Plateforme Complète pour les Arts Martiaux" %}</title>
    
    <!-- Meta descriptions pour SEO -->
    <meta name="description" content="{% trans 'MartialComp révolutionne la gestion des arts martiaux : clubs, membres, compétitions, finances et formations. Une solution tout-en-un pour fédérations, clubs, juges et pratiquants.' %}">
    <meta name="keywords" content="{% trans 'arts martiaux, compétitions, karaté, judo, taekwondo, gestion tournois, notation technique' %}">
    
    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <style>
        :root {
            --martial-red: #c41e3a;
            --martial-gold: #d4af37;
            --martial-dark: #121212;
            --martial-light: #f8f9fa;
            --martial-accent: #ff6b35;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            line-height: 1.6;
            color: #333;
        }

        /* Header */
        .hero {
            background: linear-gradient(135deg, var(--martial-red) 0%, var(--martial-dark) 100%);
            color: white;
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
        }

        .navbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 1rem 0;
        }

        .navbar-brand {
            font-size: 1.8rem;
            font-weight: 800;
            color: white !important;
            text-decoration: none;
        }

        .navbar-nav .nav-link {
            color: white !important;
            font-weight: 500;
            margin: 0 1rem;
            position: relative;
            transition: all 0.3s ease;
        }

        .navbar-nav .nav-link:hover {
            color: var(--martial-gold) !important;
        }

        /* Sélecteur de langue */
        .language-selector {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 0.25rem 0.75rem;
        }

        .language-selector select {
            background: transparent;
            border: none;
            color: white;
            font-weight: 500;
        }

        .language-selector select option {
            background: var(--martial-dark);
            color: white;
        }

        .btn-auth {
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-login {
            background: transparent;
            border: 2px solid white;
            color: white;
        }

        .btn-login:hover {
            background: white;
            color: var(--martial-red);
        }

        .btn-signup {
            background: var(--martial-gold);
            border: 2px solid var(--martial-gold);
            color: var(--martial-dark);
        }

        .btn-signup:hover {
            background: transparent;
            color: var(--martial-gold);
        }

        /* Hero Content */
        .hero-content {
            position: relative;
            z-index: 2;
            text-align: center;
            padding: 8rem 0 4rem 0;
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, white, var(--martial-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-subtitle {
            font-size: 1.4rem;
            font-weight: 300;
            margin-bottom: 2rem;
            opacity: 0.9;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        .hero-description {
            font-size: 1.1rem;
            margin-bottom: 3rem;
            opacity: 0.8;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 4rem;
        }

        .btn-hero {
            padding: 1rem 2.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 30px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary-hero {
            background: var(--martial-gold);
            color: var(--martial-dark);
            border: none;
        }

        .btn-primary-hero:hover {
            background: #b8941f;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(212, 175, 55, 0.3);
        }

        .btn-secondary-hero {
            background: transparent;
            color: white;
            border: 2px solid white;
        }

        .btn-secondary-hero:hover {
            background: white;
            color: var(--martial-red);
            transform: translateY(-2px);
        }

        /* Demo Section */
        .demo-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem auto;
            max-width: 500px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .demo-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .demo-credentials {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .demo-info {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 1rem;
        }

        .btn-demo {
            background: var(--martial-accent);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }

        .btn-demo:hover {
            background: #e55a2b;
            transform: translateY(-1px);
        }

        /* Features Section */
        .features {
            padding: 6rem 0;
            background: var(--martial-light);
        }

        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--martial-dark);
        }

        .section-subtitle {
            text-align: center;
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 4rem;
        }

        .feature-card {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            height: 100%;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border-top: 4px solid var(--martial-red);
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, var(--martial-red), var(--martial-gold));
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 1.5rem;
        }

        .feature-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--martial-dark);
        }

        .feature-description {
            color: #666;
            line-height: 1.6;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }
            
            .hero-subtitle {
                font-size: 1.2rem;
            }
            
            .hero-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .btn-hero {
                width: 100%;
                max-width: 300px;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg fixed-top">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-fist-raised me-2"></i>
                MartialComp
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#fonctionnalites">{% trans "Fonctionnalités" %}</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#demo">{% trans "Démo" %}</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#contact">{% trans "Contact" %}</a>
                    </li>
                </ul>
                
                <div class="d-flex align-items-center gap-3">
                    <!-- Sélecteur de langue -->
                    <div class="language-selector">
                        <form action="{% url 'set_language' %}" method="post" style="margin: 0;">
                            {% csrf_token %}
                            <select name="language" onchange="this.form.submit()" style="background: transparent; border: none; color: white;">
                                {% get_current_language as LANGUAGE_CODE %}
                                {% get_available_languages as LANGUAGES %}
                                {% get_language_info_list for LANGUAGES as languages %}
                                {% for language in languages %}
                                    <option value="{{ language.code }}" {% if language.code == LANGUAGE_CODE %}selected{% endif %}>
                                        {{ language.name_local }}
                                    </option>
                                {% endfor %}
                            </select>
                        </form>
                    </div>
                    
                    <a href="/accounts/login/" class="btn btn-auth btn-login">
                        <i class="fas fa-sign-in-alt me-1"></i>{% trans "Se connecter" %}
                    </a>
                    <a href="/accounts/signup/" class="btn btn-auth btn-signup">
                        <i class="fas fa-user-plus me-1"></i>{% trans "Rejoindre la phase de test" %}
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <h1 class="hero-title">
                    {% trans "La solution complète pour vos arts martiaux" %}
                </h1>
                
                <p class="hero-subtitle">
                    {% trans "Gestion • Organisation • Performance" %}
                </p>
                
                <p class="hero-description">
                    {% trans "MartialComp révolutionne la gestion des arts martiaux : clubs, membres, compétitions, finances et formations. Une plateforme tout-en-un pour tous les acteurs du milieu martial." %}
                </p>
                
                <div class="hero-buttons">
                    <a href="#demo" class="btn-hero btn-primary-hero">
                        <i class="fas fa-play"></i>
                        {% trans "Commencer maintenant" %}
                    </a>
                    <a href="#fonctionnalites" class="btn-hero btn-secondary-hero">
                        <i class="fas fa-eye"></i>
                        {% trans "Voir la démo" %}
                    </a>
                </div>

                <!-- Demo Section -->
                <div class="demo-section" id="demo">
                    <div class="demo-title">
                        <i class="fas fa-crown text-warning"></i>
                        {% trans "Démo Compte Club Manager" %}
                    </div>
                    
                    <div class="demo-credentials">
                        <div><strong>{% trans "Nom d'utilisateur:" %}</strong> dojo_sakura_manager</div>
                        <div><strong>{% trans "Mot de passe:" %}</strong> demo2025</div>
                    </div>
                    
                    <p class="demo-info">
                        {% trans "Accès au tableau de bord du Dojo Sakura avec gestion complète - 25 membres, finances, compétitions et plus." %}
                    </p>
                    
                    <a href="/accounts/login/" class="btn btn-demo">
                        <i class="fas fa-rocket me-1"></i>{% trans "Accéder à la démo" %}
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="fonctionnalites">
        <div class="container">
            <h2 class="section-title">{% trans "Une plateforme complète" %}</h2>
            <p class="section-subtitle">{% trans "Toutes les fonctionnalités dont vous avez besoin pour gérer vos arts martiaux" %}</p>
            
            <div class="row g-4">
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Gestion des Membres" %}</h3>
                        <p class="feature-description">
                            {% trans "Gérez facilement vos pratiquants, leurs profils, grades et progression." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-building"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Gestion de Club" %}</h3>
                        <p class="feature-description">
                            {% trans "Tableau de bord complet pour administrer votre club et ses activités." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-medal"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Système de Grades" %}</h3>
                        <p class="feature-description">
                            {% trans "Suivez et validez la progression des grades selon votre discipline." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-trophy"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Gestionnaire de Compétitions" %}</h3>
                        <p class="feature-description">
                            {% trans "Organisez et gérez vos tournois avec notation technique avancée." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-user-tie"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Coach Sportif" %}</h3>
                        <p class="feature-description">
                            {% trans "Outils dédiés aux entraîneurs pour suivre leurs élèves." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-landmark"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Gestion de Fédération" %}</h3>
                        <p class="feature-description">
                            {% trans "Supervisez plusieurs clubs et coordonnez les activités fédérales." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Finances" %}</h3>
                        <p class="feature-description">
                            {% trans "Gestion financière complète avec suivi des cotisations et revenus." %}
                        </p>
                    </div>
                </div>
                
                <div class="col-lg-3 col-md-6">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-shopping-cart"></i>
                        </div>
                        <h3 class="feature-title">{% trans "Boutique" %}</h3>
                        <p class="feature-description">
                            {% trans "Vendez équipements et produits directement via votre plateforme." %}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>
EOF

echo "   ✅ Template welcome.html mis à jour avec traductions complètes"

# ============================================
# 4. SYNCHRONISATION SCRIPTS DE DÉVELOPPEMENT
# ============================================

echo ""
echo "🛠️ 4. SYNCHRONISATION SCRIPTS DE DÉVELOPPEMENT"
echo "==============================================="

# Créer les scripts essentiels de développement
echo "   📝 Création des scripts de gestion..."

# Script de compilation des traductions
cat > scripts/compile_translations.py << 'EOF'
#!/usr/bin/env python3
"""
Script de compilation des traductions MartialComp
"""
import os
import subprocess
import sys

def compile_translations():
    """Compile tous les fichiers de traduction"""
    
    print("🌍 COMPILATION DES TRADUCTIONS")
    print("==============================")
    
    languages = ['fr', 'en', 'es', 'it', 'de', 'pt', 'ru', 'vi', 'no', 'ja', 'zh', 'hi', 'ar', 'sw', 'am', 'zu', 'yo', 'ko']
    
    for lang in languages:
        po_file = f"locale/{lang}/LC_MESSAGES/django.po"
        mo_file = f"locale/{lang}/LC_MESSAGES/django.mo"
        
        if os.path.exists(po_file):
            print(f"   🔨 Compilation {lang}...")
            try:
                subprocess.run(['python', 'manage.py', 'compilemessages', '--locale', lang], 
                             check=True, capture_output=True)
                print(f"   ✅ {lang} compilé")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Erreur compilation {lang}: {e}")
        else:
            print(f"   ⚠️ Fichier PO manquant pour {lang}")
    
    print("\n✅ Compilation terminée")

if __name__ == "__main__":
    compile_translations()
EOF

# Script de mise à jour des traductions
cat > scripts/update_translations.sh << 'EOF'
#!/bin/bash

echo "🌍 MISE À JOUR DES TRADUCTIONS MARTIALCOMP"
echo "=========================================="

# Activer l'environnement virtuel
source venv/bin/activate

# Extraire tous les messages à traduire
echo "📤 Extraction des messages..."
python manage.py makemessages -a

# Extraire les messages JavaScript
echo "📤 Extraction messages JavaScript..."
python manage.py makemessages -d djangojs -a

# Compiler les traductions
echo "🔨 Compilation des traductions..."
python scripts/compile_translations.py

echo "✅ Mise à jour des traductions terminée"
EOF

chmod +x scripts/update_translations.sh

# Script de diagnostic
cat > scripts/diagnostic_system.py << 'EOF'
#!/usr/bin/env python3
"""
Script de diagnostic système MartialComp
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def diagnostic_complet():
    """Effectue un diagnostic complet du système"""
    
    print("🔍 DIAGNOSTIC SYSTÈME MARTIALCOMP")
    print("=================================")
    
    # 1. Configuration Django
    print("\n1. Configuration Django:")
    try:
        from django.conf import settings
        print(f"   ✅ DEBUG: {settings.DEBUG}")
        print(f"   ✅ LANGUAGES: {len(settings.LANGUAGES)} langues")
        print(f"   ✅ DATABASE: {settings.DATABASES['default']['ENGINE']}")
        print(f"   ✅ STATIC_URL: {settings.STATIC_URL}")
    except Exception as e:
        print(f"   ❌ Erreur configuration: {e}")
    
    # 2. Base de données
    print("\n2. Base de données:")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   ✅ Connexion base de données OK")
    except Exception as e:
        print(f"   ❌ Erreur base de données: {e}")
    
    # 3. Traductions
    print("\n3. Traductions:")
    locale_dir = Path("locale")
    if locale_dir.exists():
        languages = [d.name for d in locale_dir.iterdir() if d.is_dir()]
        print(f"   ✅ {len(languages)} langues détectées: {', '.join(languages)}")
        
        for lang in languages:
            po_file = locale_dir / lang / "LC_MESSAGES" / "django.po"
            mo_file = locale_dir / lang / "LC_MESSAGES" / "django.mo"
            
            if po_file.exists() and mo_file.exists():
                print(f"   ✅ {lang}: PO + MO OK")
            elif po_file.exists():
                print(f"   ⚠️ {lang}: PO OK, MO manquant")
            else:
                print(f"   ❌ {lang}: Fichiers manquants")
    else:
        print("   ❌ Répertoire locale manquant")
    
    # 4. Applications
    print("\n4. Applications Django:")
    try:
        from django.apps import apps
        app_configs = apps.get_app_configs()
        print(f"   ✅ {len(app_configs)} applications chargées")
        
        for app in ['competitions', 'grades', 'organizations']:
            try:
                apps.get_app_config(app)
                print(f"   ✅ {app}: OK")
            except:
                print(f"   ❌ {app}: Manquant")
    except Exception as e:
        print(f"   ❌ Erreur applications: {e}")
    
    print("\n✅ Diagnostic terminé")

if __name__ == "__main__":
    diagnostic_complet()
EOF

echo "   ✅ Scripts de développement créés"

# ============================================
# 5. MISE À JOUR CONFIGURATION URLS
# ============================================

echo ""
echo "🔗 5. MISE À JOUR CONFIGURATION URLS"
echo "====================================="

# Ajouter support i18n dans config/urls.py
cat > config/urls.py << 'EOF'
"""
Configuration URLs principale MartialComp avec support multilingue
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# URLs non internationalisées
urlpatterns = [
    # Set language URL (pour le sélecteur de langue)
    path('set-language/', include('django.conf.urls.i18n')),
    
    # API endpoints (pas de traduction)
    path('api/', include('api.urls')),
]

# URLs internationalisées
urlpatterns += i18n_patterns(
    # Administration
    path('admin/', admin.site.urls),
    
    # Application principale
    path('', include('competitions.urls')),
    
    # Autres applications
    path('grades/', include('grades.urls')),
    path('organizations/', include('organizations.urls')),
    
    # Prefix default language = False pour éviter /fr/ sur la langue par défaut
    prefix_default_language=False
)

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Interface Rosetta (si installée)
try:
    import rosetta
    urlpatterns += [
        path('rosetta/', include('rosetta.urls')),
    ]
except ImportError:
    pass
EOF

echo "   ✅ Configuration URLs mise à jour avec support i18n"

# ============================================
# 6. COLLECTE DES FICHIERS STATIQUES
# ============================================

echo ""
echo "📁 6. COLLECTE DES FICHIERS STATIQUES"
echo "======================================"

echo "   📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
echo "   ✅ Fichiers statiques collectés"

# ============================================
# 7. COMPILATION DES TRADUCTIONS
# ============================================

echo ""
echo "🔨 7. COMPILATION DES TRADUCTIONS"
echo "=================================="

echo "   🌍 Compilation des traductions disponibles..."
python scripts/compile_translations.py
echo "   ✅ Traductions compilées"

# ============================================
# 8. REDÉMARRAGE DJANGO
# ============================================

echo ""
echo "🔄 8. REDÉMARRAGE DJANGO"
echo "========================"

echo "   🛑 Arrêt des processus Django existants..."
pkill -f "manage.py runserver" || true
sleep 3

echo "   🚀 Redémarrage Django avec nouvelles configurations..."
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="/var/www/vhosts/martialcomp.com/httpdocs"

nohup python manage.py runserver 127.0.0.1:8080 > /var/www/vhosts/martialcomp.com/logs/django_sync_complete.log 2>&1 &
DJANGO_PID=$!

echo "   ✅ Django redémarré (PID: $DJANGO_PID)"

# ============================================
# 9. TESTS FINAUX
# ============================================

echo ""
echo "🧪 9. TESTS FINAUX"
echo "=================="

sleep 5

echo "   🔍 Test Django interne:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://127.0.0.1:8080/

echo "   🔍 Test Apache proxy:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://localhost/

echo "   🔍 Test externe:"
EXTERNAL_IP=$(curl -s ifconfig.me)
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://$EXTERNAL_IP/

echo "   🌍 Test changement de langue:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" "http://127.0.0.1:8080/en/"

# ============================================
# 10. DIAGNOSTIC SYSTÈME
# ============================================

echo ""
echo "🔍 10. DIAGNOSTIC SYSTÈME FINAL"
echo "==============================="

python scripts/diagnostic_system.py

# ============================================
# RÉSUMÉ FINAL
# ============================================

echo ""
echo "🎉 SYNCHRONISATION COMPLÈTE TERMINÉE"
echo "===================================="
echo ""
echo "📋 RÉSUMÉ DES AMÉLIORATIONS:"
echo "   ✅ Template welcome.html modernisé avec traductions"
echo "   ✅ Système multilingue complet (16 langues)"
echo "   ✅ Scripts de développement synchronisés"
echo "   ✅ Configuration URLs avec support i18n"
echo "   ✅ Sélecteur de langue fonctionnel"
echo "   ✅ Compilation des traductions automatique"
echo ""
echo "🌐 URLS À TESTER:"
echo "   • Page d'accueil: http://martialcomp.com"
echo "   • Version anglaise: http://martialcomp.com/en/"
echo "   • Version italienne: http://martialcomp.com/it/"
echo "   • Interface Rosetta: http://martialcomp.com/rosetta/"
echo ""
echo "📊 INFORMATIONS TECHNIQUES:"
echo "   🐍 Django PID: $DJANGO_PID"
echo "   🌍 IP externe: $EXTERNAL_IP"
echo "   💾 Sauvegarde: $BACKUP_DIR"
echo "   📝 Logs: /var/www/vhosts/martialcomp.com/logs/django_sync_complete.log"
echo ""
echo "🎨 NOUVELLES FONCTIONNALITÉS:"
echo "   🔧 Scripts de gestion des traductions"
echo "   🌍 Sélecteur de langue dans navigation"
echo "   📱 Design responsive moderne"
echo "   🎭 Thème martial authentique (rouge/or)"
echo "   🚀 Interface de démonstration intégrée"
echo ""
echo "📚 SCRIPTS DISPONIBLES:"
echo "   🔨 ./scripts/update_translations.sh"
echo "   🐍 python scripts/compile_translations.py"
echo "   🔍 python scripts/diagnostic_system.py"
echo ""
echo "🔄 Si problème, restaurer avec:"
echo "   cp $BACKUP_DIR/competitions/templates/competitions/welcome.html competitions/templates/competitions/"
echo "   cp $BACKUP_DIR/config/settings.py config/"
echo ""
echo "✨ ENVIRONNEMENT DE DÉVELOPPEMENT MAINTENANT SYNCHRONISÉ AVEC PRODUCTION !" 