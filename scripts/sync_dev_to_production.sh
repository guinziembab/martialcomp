#!/bin/bash

echo "🔄 SYNCHRONISATION DEV → PRODUCTION"
echo "===================================="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. Sauvegarder les templates actuels de production
echo "1. Sauvegarde des templates de production..."
mkdir -p backups/templates_production_$TIMESTAMP

# Sauvegarder les templates critiques
cp competitions/templates/competitions/welcome.html backups/templates_production_$TIMESTAMP/
cp -r competitions/templates/competitions/dashboard/ backups/templates_production_$TIMESTAMP/ 2>/dev/null || true
cp competitions/templates/base.html backups/templates_production_$TIMESTAMP/ 2>/dev/null || true

echo "   ✅ Sauvegarde terminée dans backups/templates_production_$TIMESTAMP/"

# 2. Mettre à jour le template welcome.html avec la version de développement
echo ""
echo "2. Mise à jour du template welcome.html..."

# Créer la version complète et moderne du template welcome
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
    <meta name="keywords" content="arts martiaux, compétitions, karaté, judo, taekwondo, gestion tournois, notation technique">
    
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
                
                <div class="d-flex gap-2">
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

echo "   ✅ Template welcome.html mis à jour avec design moderne"

# 3. Synchroniser les fichiers statiques
echo ""
echo "3. Synchronisation des fichiers statiques..."
python manage.py collectstatic --noinput
echo "   ✅ Fichiers statiques collectés"

# 4. Vérifier que Django fonctionne toujours
echo ""
echo "4. Vérification Django..."
python manage.py check --quiet
if [ $? -eq 0 ]; then
    echo "   ✅ Django configuration OK"
else
    echo "   ❌ Problème de configuration Django"
    exit 1
fi

# 5. Redémarrer Django
echo ""
echo "5. Redémarrage Django..."
pkill -f "manage.py runserver"
sleep 2

cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="/var/www/vhosts/martialcomp.com/httpdocs"

nohup python manage.py runserver 127.0.0.1:8080 > /var/www/vhosts/martialcomp.com/logs/django_sync.log 2>&1 &
DJANGO_PID=$!

echo "   ✅ Django redémarré (PID: $DJANGO_PID)"

# 6. Tests finaux
echo ""
echo "6. Tests finaux..."
sleep 3

echo "   Test Django interne:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://127.0.0.1:8080/

echo "   Test Apache proxy:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://localhost/

echo "   Test externe:"
EXTERNAL_IP=$(curl -s ifconfig.me)
curl -s -o /dev/null -w "   Status: %{http_code}\n" http://$EXTERNAL_IP/

echo ""
echo "✅ SYNCHRONISATION TERMINÉE"
echo "=========================="
echo "🌐 URL à tester: http://martialcomp.com"
echo "📊 Django PID: $DJANGO_PID"
echo "💾 Sauvegarde: backups/templates_production_$TIMESTAMP/"
echo ""
echo "🎨 NOUVEAU DESIGN DISPONIBLE:"
echo "   • Page d'accueil modernisée"
echo "   • Design professionnel martial"
echo "   • Navigation améliorée"
echo "   • Section démo mise à jour"
echo "   • 8 fonctionnalités présentées"
echo ""
echo "📝 Si problème, restaurer avec:"
echo "   cp backups/templates_production_$TIMESTAMP/welcome.html competitions/templates/competitions/" 