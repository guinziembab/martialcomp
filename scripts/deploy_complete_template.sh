#!/bin/bash

# =============================================================================
# Déploiement complet du template professionnel MartialComp
# =============================================================================

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Déploiement du template professionnel complet..."

# Sauvegarder le template actuel
echo "💾 Sauvegarde du template actuel..."
cp competitions/templates/competitions/welcome.html competitions/templates/competitions/welcome.html.backup_$TIMESTAMP

# Créer le template complet en utilisant Python pour éviter les problèmes de heredoc
python3 << 'PYTHON_SCRIPT'
template_content = '''<!DOCTYPE html>
{% load i18n %}
{% load static %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MartialComp - La Plateforme Complète de Gestion des Compétitions d'Arts Martiaux</title>
    
    <!-- Meta descriptions pour SEO -->
    <meta name="description" content="MartialComp est la solution complète pour organiser, gérer et participer aux compétitions d'arts martiaux. Multi-disciplines, multi-langues, avec outils de notation technique et gestion financière intégrée.">
    <meta name="keywords" content="arts martiaux, compétitions, karaté, judo, taekwondo, gestion tournois, notation technique">
    
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
            --google: #4285f4;
            --facebook: #1877f2;
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
        
        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }
        
        .nav-links a {
            color: var(--light);
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
            transition: var(--transition);
        }
        
        .nav-links a:hover {
            background-color: rgba(212, 175, 55, 0.2);
            color: var(--accent);
        }
        
        .auth-section {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: var(--border-radius);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }
        
        .btn-google {
            background: var(--google);
            color: var(--white);
        }
        
        .btn-google:hover {
            background: #3367d6;
            transform: translateY(-2px);
        }
        
        .btn-facebook {
            background: var(--facebook);
            color: var(--white);
        }
        
        .btn-facebook:hover {
            background: #166fe5;
            transform: translateY(-2px);
        }
        
        /* ==== HERO SECTION ==== */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 120px 0 80px;
            background: linear-gradient(135deg, var(--dark) 0%, var(--secondary) 100%);
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
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><defs><radialGradient id="g" cx="50%" cy="50%"><stop offset="0%" stop-color="%23c41e3a" stop-opacity="0.1"/><stop offset="100%" stop-color="%23c41e3a" stop-opacity="0"/></radialGradient></defs><circle cx="200" cy="200" r="150" fill="url(%23g)"/><circle cx="800" cy="300" r="200" fill="url(%23g)"/><circle cx="400" cy="700" r="180" fill="url(%23g)"/></svg>');
            opacity: 0.5;
        }
        
        .hero-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            position: relative;
            z-index: 1;
        }
        
        .hero-content h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            background: linear-gradient(135deg, var(--white) 0%, var(--accent) 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero-content .subtitle {
            font-size: 1.3rem;
            color: var(--light);
            margin-bottom: 2rem;
            opacity: 0.9;
        }
        
        .hero-content .description {
            font-size: 1.1rem;
            color: var(--gray);
            margin-bottom: 3rem;
            line-height: 1.8;
        }
        
        .social-auth-section {
            background: rgba(255, 255, 255, 0.05);
            padding: 2rem;
            border-radius: var(--border-radius);
            border: 1px solid rgba(212, 175, 55, 0.2);
            margin-bottom: 2rem;
        }
        
        .social-auth-title {
            color: var(--accent);
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .social-auth-buttons {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .social-btn-large {
            padding: 1rem 2rem;
            border-radius: var(--border-radius);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            font-size: 1rem;
        }
        
        .hero-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .stat-item {
            text-align: center;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius);
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: var(--gray);
        }
        
        .hero-visual {
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        /* Success Banner */
        .success-banner {
            background: linear-gradient(45deg, var(--success), #20c997);
            color: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .success-banner h3 {
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        
        /* ==== TEST PHASE BANNER ==== */
        .test-phase-banner {
            background: linear-gradient(135deg, var(--warning), var(--accent));
            color: var(--dark);
            text-align: center;
            padding: 1.5rem;
            font-weight: 600;
            position: relative;
            overflow: hidden;
        }
        
        .test-phase-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shine 3s infinite;
        }
        
        @keyframes shine {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        /* ==== FOOTER ==== */
        .footer {
            background: var(--dark);
            padding: 4rem 0 2rem;
            border-top: 2px solid var(--accent);
        }
        
        .footer-links {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .footer-links a {
            color: var(--gray);
            text-decoration: none;
            transition: var(--transition);
            margin: 0 1rem;
        }
        
        .footer-links a:hover {
            color: var(--accent);
        }
        
        .footer-bottom {
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--gray);
        }
        
        /* ==== RESPONSIVE DESIGN ==== */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }
            
            .hero-container {
                grid-template-columns: 1fr;
                gap: 2rem;
                text-align: center;
            }
            
            .hero-content h1 {
                font-size: 2.5rem;
            }
            
            .hero-stats {
                grid-template-columns: 1fr;
            }
            
            .auth-section {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .social-auth-buttons {
                gap: 0.5rem;
            }
        }
        
        /* ==== ANIMATIONS ==== */
        .fade-in {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }
        
        .fade-in.visible {
            opacity: 1;
            transform: translateY(0);
        }
    </style>
</head>

<body>
    <!-- TEST PHASE BANNER -->
    <div class="test-phase-banner">
        <i class="fas fa-flask"></i>
        Phase de test en cours (1er-30 juin 2025) • 
        Lancement officiel: 1er juillet 2025 • 
        <strong>Rejoignez les testeurs !</strong>
    </div>
    
    <!-- HEADER -->
    <header class="header">
        <div class="nav-container">
            <a href="#" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-fist-raised"></i>
                </div>
                Martial<span style="color: var(--accent);">Comp</span>
            </a>
            
            <nav class="nav-links">
                <a href="#social-auth">Connexion</a>
                <a href="#contact">Contact</a>
            </nav>
            
            <div class="auth-section">
                <a href="/accounts/google/login/" class="btn btn-google">
                    <i class="fab fa-google"></i>
                    Google
                </a>
                <a href="/accounts/facebook/login/" class="btn btn-facebook">
                    <i class="fab fa-facebook-f"></i>
                    Facebook
                </a>
            </div>
        </div>
    </header>
    
    <!-- HERO SECTION -->
    <section class="hero">
        <div class="hero-container">
            <div class="hero-content fade-in">
                <h1>La solution complète pour vos compétitions d'arts martiaux</h1>
                <p class="subtitle">
                    Simplicité • Professionnalisme • Innovation
                </p>
                <p class="description">
                    MartialComp révolutionne l'organisation des compétitions d'arts martiaux avec une plateforme tout-en-un qui simplifie la gestion des événements, des inscriptions, de la notation et des résultats pour tous les acteurs du milieu.
                </p>
                
                <div class="success-banner">
                    <h3><i class="fas fa-check-circle"></i> Authentification Sociale Opérationnelle !</h3>
                    <p>Connectez-vous facilement avec Google ou Facebook. Système entièrement déployé et sécurisé.</p>
                </div>
                
                <div class="social-auth-section" id="social-auth">
                    <div class="social-auth-title">
                        <i class="fas fa-shield-alt"></i> Connexion Sécurisée
                    </div>
                    <p style="text-align: center; margin-bottom: 1.5rem; color: var(--gray);">
                        Choisissez votre méthode de connexion préférée :
                    </p>
                    
                    <div class="social-auth-buttons">
                        <a href="/accounts/google/login/" class="social-btn-large btn-google">
                            <i class="fab fa-google"></i>
                            Continuer avec Google
                        </a>
                        <a href="/accounts/facebook/login/" class="social-btn-large btn-facebook">
                            <i class="fab fa-facebook-f"></i>
                            Continuer avec Facebook
                        </a>
                    </div>
                </div>
                
                <div class="hero-stats">
                    <div class="stat-item">
                        <div class="stat-number">50+</div>
                        <div class="stat-label">Compétitions organisées</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">500+</div>
                        <div class="stat-label">Pratiquants actifs</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">16</div>
                        <div class="stat-label">Langues supportées</div>
                    </div>
                </div>
            </div>
            
            <div class="hero-visual fade-in">
                <div style="width: 100%; max-width: 500px; height: 400px; background: linear-gradient(135deg, var(--primary), var(--accent)); border-radius: 20px; display: flex; align-items: center; justify-content: center; color: white; font-size: 4rem; box-shadow: var(--shadow-hover);">
                    <i class="fas fa-trophy"></i>
                </div>
            </div>
        </div>
    </section>
    
    <!-- FOOTER -->
    <footer id="contact" class="footer">
        <div class="footer-links">
            <a href="/privacy/">Politique de confidentialité</a>
            <a href="/terms/">Conditions d'utilisation</a>
            <a href="mailto:support@martialcomp.com">Contact</a>
        </div>
        
        <div class="footer-bottom">
            <p>&copy; 2025 MartialComp. Tous droits réservés.</p>
            <p>Authentification sociale déployée avec succès 🥋</p>
        </div>
    </footer>
    
    <script>
        // Animations au scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.fade-in').forEach(el => {
            observer.observe(el);
        });
        
        // Header sticky behavior
        window.addEventListener('scroll', () => {
            const header = document.querySelector('.header');
            if (window.scrollY > 100) {
                header.style.backgroundColor = 'rgba(26, 26, 26, 0.95)';
            } else {
                header.style.backgroundColor = 'transparent';
            }
        });
    </script>
</body>
</html>'''

# Écrire le template dans le fichier
with open('competitions/templates/competitions/welcome.html', 'w', encoding='utf-8') as f:
    f.write(template_content)

print("✅ Template professionnel complet créé avec succès")
PYTHON_SCRIPT

echo "🔄 Redémarrage de Django..."

# Arrêter Django
pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
sleep 5

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la configuration Django
echo "🔍 Vérification de la configuration Django..."
python manage.py check

# Redémarrer Django
echo "🚀 Redémarrage de Django..."
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_template_complete_$TIMESTAMP.log 2>&1 &

sleep 15

# Test de validation
echo ""
echo "🧪 Test de validation..."
django_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/")
echo "Test Django local: $django_code"

nginx_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/")
echo "Test Nginx public: $nginx_code"

echo ""
if [[ "$django_code" == "200" && "$nginx_code" == "200" ]]; then
    echo "🎉🎉🎉 SUCCÈS TOTAL ! 🎉🎉🎉"
    echo ""
    echo "✅ Template professionnel déployé avec succès"
    echo "✅ Django redémarré"
    echo "✅ Page accessible en local et via Nginx"
    echo ""
    echo "🎨 NOUVEAU DESIGN APPLIQUÉ :"
    echo "  • Header professionnel avec logo MartialComp"
    echo "  • Boutons Google/Facebook dans le header"
    echo "  • Section hero avec authentification intégrée"
    echo "  • Bannière de phase de test animée"
    echo "  • Statistiques et design moderne"
    echo "  • Footer avec liens légaux"
    echo ""
    echo "🔗 URLs à tester :"
    echo "  • https://martialcomp.com/"
    echo "  • https://martialcomp.com/accounts/google/login/"
    echo "  • https://martialcomp.com/accounts/facebook/login/"
else
    echo "❌ Problème détecté"
    echo "Codes de réponse: Django=$django_code, Nginx=$nginx_code"
    echo ""
    echo "📋 Logs Django récents :"
    tail -10 /tmp/django_template_complete_$TIMESTAMP.log
fi

echo ""
echo "💾 Fichiers de sauvegarde :"
echo "  • welcome.html.backup_$TIMESTAMP"
echo "  • /tmp/django_template_complete_$TIMESTAMP.log"
echo ""
echo "🏁 Déploiement terminé !"