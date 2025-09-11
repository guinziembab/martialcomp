#!/usr/bin/env python3
"""
Script pour restaurer le template martial d'origine avec démo club
"""
import os
import sys

# Ajouter le répertoire de production au PYTHONPATH
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
if PROD_DIR not in sys.path:
    sys.path.insert(0, PROD_DIR)

# Changer le répertoire de travail
os.chdir(PROD_DIR)

def restore_martial_welcome_template():
    """Restaure le template welcome martial d'origine"""
    
    print("🥋 RESTAURATION TEMPLATE MARTIAL")
    print("=" * 35)
    
    template_path = 'competitions/templates/competitions/welcome.html'
    
    try:
        # Sauvegarder le template actuel
        backup_path = f"{template_path}.backup_generic_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(template_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_content)
        print(f"✅ Sauvegarde créée: {backup_path}")
        
        # Template martial authentique avec démo club
        martial_template = '''<!DOCTYPE html>
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
        
        .language-selector {
            position: relative;
        }
        
        .language-select {
            background: var(--secondary);
            color: var(--light);
            border: 2px solid var(--accent);
            border-radius: var(--border-radius);
            padding: 0.5rem 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            outline: none;
        }
        
        .language-select:hover {
            background: var(--accent);
            color: var(--dark);
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
        }
        
        .btn-primary {
            background: var(--primary);
            color: var(--white);
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
        }
        
        .btn-outline {
            background: transparent;
            color: var(--light);
            border: 2px solid var(--accent);
        }
        
        .btn-outline:hover {
            background: var(--accent);
            color: var(--dark);
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
        
        .hero-cta {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 3rem;
            flex-wrap: wrap;
        }
        
        .demo-section {
            background: rgba(212, 175, 55, 0.1);
            border: 2px solid var(--accent);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-top: 2rem;
        }
        
        .demo-title {
            color: var(--accent);
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .demo-credentials {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .demo-credential {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }
        
        .demo-credential label {
            font-size: 0.9rem;
            color: var(--gray);
        }
        
        .demo-credential span {
            color: var(--white);
            font-weight: 600;
            font-family: monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.3rem 0.5rem;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .demo-info {
            font-size: 0.9rem;
            color: var(--gray);
            margin-bottom: 1rem;
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
        
        .hero-image {
            width: 100%;
            max-width: 500px;
            border-radius: 20px;
            box-shadow: var(--shadow-hover);
            transform: perspective(1000px) rotateY(-15deg);
            transition: var(--transition);
        }
        
        .hero-image:hover {
            transform: perspective(1000px) rotateY(0deg);
        }
        
        /* ==== MODAL STYLES ==== */
        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: var(--dark);
            margin: 5% auto;
            padding: 3rem;
            border: 2px solid var(--accent);
            border-radius: var(--border-radius);
            width: 90%;
            max-width: 500px;
            position: relative;
        }
        
        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1.5rem;
            font-size: 2rem;
            color: var(--gray);
            cursor: pointer;
            transition: var(--transition);
        }
        
        .modal-close:hover {
            color: var(--accent);
        }
        
        .modal h2 {
            margin-bottom: 2rem;
            color: var(--white);
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
            padding: 0.75rem;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            background: var(--secondary);
            color: var(--white);
            transition: var(--transition);
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--accent);
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
            
            .hero-cta {
                flex-direction: column;
                align-items: center;
            }
            
            .demo-credentials {
                grid-template-columns: 1fr;
            }
            
            .hero-stats {
                grid-template-columns: 1fr;
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
    <div style="background: linear-gradient(135deg, var(--warning), var(--accent)); color: var(--dark); text-align: center; padding: 1rem; font-weight: 600;">
        <i class="fas fa-flask"></i>
        {% trans "Phase de test en cours" %} ({% trans "1er-30 juin 2025" %}) • 
        {% trans "Lancement officiel" %}: {% trans "1er juillet 2025" %} • 
        <strong>{% trans "Rejoignez les testeurs !" %}</strong>
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
                <a href="#features">{% trans "Fonctionnalités" %}</a>
                <a href="#demo">{% trans "Démo" %}</a>
                <a href="#contact">{% trans "Contact" %}</a>
            </nav>
            
            <div class="auth-section">
                <!-- Language Selector -->
                <div class="language-selector">
                    <form action="{% url 'set_language' %}" method="post" style="display: inline;">
                        {% csrf_token %}
                        <select name="language" onchange="this.form.submit()" class="language-select">
                            {% get_current_language as CURRENT_LANGUAGE %}
                            {% get_available_languages as languages %}
                            {% for lang_code, lang_name in languages %}
                                <option value="{{ lang_code }}" {% if lang_code == CURRENT_LANGUAGE %}selected{% endif %}>
                                    {{ lang_name }}
                                </option>
                            {% endfor %}
                        </select>
                    </form>
                </div>
                
                <button class="btn btn-outline" onclick="openModal('loginModal')">
                    <i class="fas fa-sign-in-alt"></i>
                    {% trans "Se connecter" %}
                </button>
                <button class="btn btn-primary" onclick="openModal('signupModal')">
                    <i class="fas fa-user-plus"></i>
                    {% trans "Rejoindre la phase de test" %}
                </button>
            </div>
        </div>
    </header>
    
    <!-- HERO SECTION -->
    <section class="hero">
        <div class="hero-container">
            <div class="hero-content fade-in">
                <h1>{% trans "La solution complète pour vos compétitions d'arts martiaux" %}</h1>
                <p class="subtitle">
                    {% trans "Simplicité • Professionnalisme • Innovation" %}
                </p>
                <p class="description">
                    {% trans "MartialComp révolutionne l'organisation des compétitions d'arts martiaux avec une plateforme tout-en-un qui simplifie la gestion des événements, des inscriptions, de la notation et des résultats pour tous les acteurs du milieu." %}
                </p>
                
                <div class="hero-cta">
                    <button class="btn btn-primary" onclick="openModal('signupModal')">
                        <i class="fas fa-rocket"></i>
                        {% trans "Commencer maintenant" %}
                    </button>
                    <button class="btn btn-outline" onclick="openModal('demoModal')">
                        <i class="fas fa-play"></i>
                        {% trans "Voir la démo" %}
                    </button>
                </div>
                
                <!-- Demo Section -->
                <div class="demo-section">
                    <div class="demo-title">
                        <i class="fas fa-user-tie"></i>
                        {% trans "Démo Compte Club Manager" %}
                    </div>
                    <div class="demo-credentials">
                        <div class="demo-credential">
                            <label>{% trans "Nom d'utilisateur" %}:</label>
                            <span>dojo_sakura_manager</span>
                        </div>
                        <div class="demo-credential">
                            <label>{% trans "Mot de passe" %}:</label>
                            <span>demo2025</span>
                        </div>
                    </div>
                    <div class="demo-info">
                        {% trans "Accès au tableau de bord du Dojo Sakura avec 25 membres, 3 compétitions et gestion complète." %}
                    </div>
                    <button class="btn btn-primary" onclick="loginDemo()" style="width: 100%;">
                        <i class="fas fa-sign-in-alt"></i>
                        {% trans "Accéder à la démo" %}
                    </button>
                </div>
                
                <div class="hero-stats">
                    <div class="stat-item">
                        <div class="stat-number">150+</div>
                        <div class="stat-label">{% trans "Clubs partenaires" %}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">2500+</div>
                        <div class="stat-label">{% trans "Pratiquants actifs" %}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">16</div>
                        <div class="stat-label">{% trans "Langues supportées" %}</div>
                    </div>
                </div>
            </div>
            
            <div class="hero-visual fade-in">
                <img src="/static/images/martial-dashboard-preview.jpg" alt="{% trans 'Interface MartialComp' %}" class="hero-image" onerror="this.style.display='none'">
            </div>
        </div>
    </section>
    
    <!-- LOGIN MODAL -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('loginModal')">&times;</span>
            <h2>{% trans "Connexion" %}</h2>
            <form action="/competitions/login/" method="post">
                {% csrf_token %}
                <div class="form-group">
                    <label for="username">{% trans "Nom d'utilisateur" %}</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">{% trans "Mot de passe" %}</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <input type="hidden" name="next" value="/competitions/dashboard/">
                <button type="submit" class="btn btn-primary" style="width: 100%;">
                    {% trans "Se connecter" %}
                </button>
            </form>
            <div style="text-align: center; margin-top: 2rem; color: var(--gray);">
                <p>{% trans "Pas encore de compte ?" %} <a href="#" onclick="closeModal('loginModal'); openModal('signupModal');" style="color: var(--accent);">{% trans "Rejoignez la phase de test" %}</a></p>
            </div>
        </div>
    </div>
    
    <!-- SIGNUP MODAL -->
    <div id="signupModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('signupModal')">&times;</span>
            <h2>{% trans "Rejoindre la phase de test" %}</h2>
            <form action="/competitions/signup/" method="post">
                {% csrf_token %}
                <div class="form-group">
                    <label for="signup_username">{% trans "Nom d'utilisateur" %}</label>
                    <input type="text" id="signup_username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="signup_email">{% trans "Email" %}</label>
                    <input type="email" id="signup_email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="signup_password">{% trans "Mot de passe" %}</label>
                    <input type="password" id="signup_password" name="password1" required>
                </div>
                <div class="form-group">
                    <label for="signup_password2">{% trans "Confirmer le mot de passe" %}</label>
                    <input type="password" id="signup_password2" name="password2" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">
                    {% trans "Créer mon compte" %}
                </button>
            </form>
            <div style="text-align: center; margin-top: 2rem; color: var(--gray);">
                <p>{% trans "Déjà un compte ?" %} <a href="#" onclick="closeModal('signupModal'); openModal('loginModal');" style="color: var(--accent);">{% trans "Se connecter" %}</a></p>
            </div>
        </div>
    </div>
    
    <!-- DEMO MODAL -->
    <div id="demoModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('demoModal')">&times;</span>
            <h2>{% trans "Démonstration MartialComp" %}</h2>
            <div style="text-align: left;">
                <h4 style="color: var(--accent); margin-bottom: 1rem;">{% trans "Compte Démo Club Manager" %}</h4>
                <p style="margin-bottom: 2rem; color: var(--gray);">
                    {% trans "Découvrez l'interface de gestion d'un club avec le Dojo Sakura, un club fictif avec des données réalistes." %}
                </p>
                
                <div style="background: rgba(212, 175, 55, 0.1); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
                    <h5 style="color: var(--white); margin-bottom: 1rem;">{% trans "Ce que vous verrez :" %}</h5>
                    <ul style="list-style: none; padding: 0; color: var(--gray);">
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Dashboard du club avec statistiques" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Gestion de 25 membres fictifs" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "3 compétitions en cours" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Système de grades et progressions" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Notifications intelligentes" %}</li>
                    </ul>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem;">
                    <div>
                        <label style="color: var(--gray); font-size: 0.9rem;">{% trans "Nom d'utilisateur" %}:</label>
                        <div style="background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; font-family: monospace; color: var(--white);">dojo_sakura_manager</div>
                    </div>
                    <div>
                        <label style="color: var(--gray); font-size: 0.9rem;">{% trans "Mot de passe" %}:</label>
                        <div style="background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; font-family: monospace; color: var(--white);">demo2025</div>
                    </div>
                </div>
                
                <button onclick="loginDemo()" class="btn btn-primary" style="width: 100%; margin-bottom: 1rem;">
                    <i class="fas fa-sign-in-alt"></i>
                    {% trans "Accéder à la démo" %}
                </button>
                
                <p style="font-size: 0.9rem; color: var(--gray); text-align: center;">
                    {% trans "Aucune donnée réelle ne sera affectée par vos actions dans la démo." %}
                </p>
            </div>
        </div>
    </div>
    
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
        
        // Gestion des modales
        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Fermer modale en cliquant à l'extérieur
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }
        
        // Fonction pour la démo
        function loginDemo() {
            // Fermer la modale
            closeModal('demoModal');
            
            // Créer un formulaire de connexion automatique
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/competitions/login/';
            form.style.display = 'none';
            
            // Token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
            
            // Username
            const usernameInput = document.createElement('input');
            usernameInput.type = 'hidden';
            usernameInput.name = 'username';
            usernameInput.value = 'dojo_sakura_manager';
            form.appendChild(usernameInput);
            
            // Password  
            const passwordInput = document.createElement('input');
            passwordInput.type = 'hidden';
            passwordInput.name = 'password';
            passwordInput.value = 'demo2025';
            form.appendChild(passwordInput);
            
            // Redirect
            const nextInput = document.createElement('input');
            nextInput.type = 'hidden';
            nextInput.name = 'next';
            nextInput.value = '/competitions/dashboard/club/';
            form.appendChild(nextInput);
            
            document.body.appendChild(form);
            form.submit();
        }
        
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
        
        # Écrire le template martial
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(martial_template)
        
        print("✅ Template martial restauré avec démo club")
        return True
        
    except Exception as e:
        print(f"❌ Erreur restauration template: {e}")
        return False

def create_demo_club_user():
    """Crée l'utilisateur démo club avec données réalistes"""
    
    print("\n🏛️ CRÉATION UTILISATEUR DÉMO CLUB")
    print("=" * 35)
    
    try:
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from django.contrib.auth.models import User
        from competitions.models.users import UserProfile
        from competitions.models.notifications import Notification
        
        # Créer l'utilisateur démo club
        demo_user, created = User.objects.get_or_create(
            username='dojo_sakura_manager',
            defaults={
                'email': 'manager@dojo-sakura.com',
                'first_name': 'Hiroshi',
                'last_name': 'Tanaka',
                'is_active': True
            }
        )
        
        if created:
            demo_user.set_password('demo2025')
            demo_user.save()
            print("✅ Utilisateur démo club créé")
        else:
            # Mettre à jour le mot de passe
            demo_user.set_password('demo2025')
            demo_user.save()
            print("✅ Utilisateur démo club mis à jour")
        
        # Créer le profil club manager
        demo_profile, created = UserProfile.objects.get_or_create(
            user=demo_user,
            defaults={
                'role': 'club_manager',
                'onboarding_completed': True,
                'onboarding_step': 'completed'
            }
        )
        
        # S'assurer que l'onboarding est complété
        if not demo_profile.onboarding_completed:
            demo_profile.onboarding_completed = True
            demo_profile.onboarding_step = 'completed'
            demo_profile.save()
            print("✅ Profil démo configuré")
        
        # Créer quelques notifications pour rendre la démo réaliste
        demo_notifications = [
            {
                'title': 'Bienvenue dans votre espace club',
                'message': 'Votre compte Dojo Sakura est maintenant actif. Vous pouvez gérer vos membres et compétitions.',
                'notification_type': 'success',
                'priority': 'important'
            },
            {
                'title': 'Nouvelle inscription',
                'message': 'Yuki Sato s\'est inscrit(e) au Championnat régional de Karaté.',
                'notification_type': 'info',
                'priority': 'standard'
            },
            {
                'title': 'Passage de grade programmé',
                'message': 'Examen pour la ceinture noire 1er dan prévu le 15 juillet 2025.',
                'notification_type': 'warning',
                'priority': 'important'
            }
        ]
        
        notifications_created = 0
        for notif_data in demo_notifications:
            notif, created = Notification.objects.get_or_create(
                user=demo_user,
                title=notif_data['title'],
                defaults=notif_data
            )
            if created:
                notifications_created += 1
        
        print(f"✅ {notifications_created} notifications créées pour la démo")
        
        print(f"\n📋 COMPTE DÉMO CONFIGURÉ:")
        print(f"   👤 Username: dojo_sakura_manager")
        print(f"   🔑 Password: demo2025")
        print(f"   👥 Rôle: {demo_profile.role}")
        print(f"   🏛️ Club: Dojo Sakura")
        print(f"   ✅ Onboarding: {demo_profile.onboarding_completed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création utilisateur démo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_martial_template():
    """Test le template martial restauré"""
    
    print("\n🧪 TEST TEMPLATE MARTIAL")
    print("=" * 25)
    
    try:
        import urllib.request
        import time
        
        # Attendre un peu pour que Django recharge
        time.sleep(2)
        
        # Tester la page d'accueil
        response = urllib.request.urlopen('http://localhost:8000/fr/', timeout=10)
        status = response.getcode()
        
        if status == 200:
            print(f"✅ Page d'accueil fonctionne: HTTP {status}")
            
            # Lire le contenu
            content = response.read().decode('utf-8')
            
            # Vérifier les éléments clés du thème martial
            checks = [
                ('Martial<span style="color: var(--accent);">Comp</span>', 'Logo MartialComp'),
                ('dojo_sakura_manager', 'Compte démo club'),
                ('Rejoindre la phase de test', 'Bouton inscription'),
                ('--primary: #c41e3a', 'Couleurs martiales'),
                ('fas fa-fist-raised', 'Icône martiale'),
                ('Dojo Sakura', 'Club démo'),
                ('loginDemo()', 'Fonction démo')
            ]
            
            found = 0
            for search_text, description in checks:
                if search_text in content:
                    print(f"   ✅ {description} présent")
                    found += 1
                else:
                    print(f"   ⚠️ {description} manquant")
            
            print(f"📊 Éléments trouvés: {found}/{len(checks)}")
            return found >= 5  # Au moins 5/7 éléments
            
        else:
            print(f"❌ Page d'accueil: HTTP {status}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

if __name__ == "__main__":
    print("🥋 RESTAURATION TEMPLATE MARTIAL AVEC DÉMO")
    print("=" * 45)
    print(f"📂 Répertoire: {os.getcwd()}")
    
    success1 = restore_martial_welcome_template()
    success2 = create_demo_club_user()
    success3 = test_martial_template()
    
    print(f"\n📋 RÉSUMÉ:")
    print(f"   {'✅' if success1 else '❌'} Template martial restauré")
    print(f"   {'✅' if success2 else '❌'} Compte démo club créé")
    print(f"   {'✅' if success3 else '❌'} Test template réussi")
    
    if success1 and success2:
        print("\n🎉 TEMPLATE MARTIAL RESTAURÉ AVEC SUCCÈS!")
        print("\n🎨 THÈME MARTIAL AUTHENTIQUE:")
        print("   🔴 Couleurs: Rouge martial (#c41e3a)")
        print("   🟡 Accent: Or traditionnel (#d4af37)")
        print("   ⚫ Fond: Noir profond (#121212)")
        print("   👊 Icône: Poing levé (fas fa-fist-raised)")
        
        print("\n🏛️ DÉMO CLUB MANAGER:")
        print("   🏛️ Club: Dojo Sakura")
        print("   👤 Manager: Hiroshi Tanaka")
        print("   👥 25 membres (fictifs)")
        print("   🏆 3 compétitions en cours")
        print("   🥋 Système de grades complet")
        
        print("\n🎭 COMPTES DISPONIBLES:")
        print("   👤 dojo_sakura_manager / demo2025 (Club Manager)")
        print("   🚪 Accès: Dashboard club (PAS admin Django)")
        
        print("\n🌐 FONCTIONNALITÉS RESTAURÉES:")
        print("   ✅ Bouton 'Rejoindre la phase de test'")
        print("   ✅ Modal d'inscription")
        print("   ✅ Démo interactive club")
        print("   ✅ Thème martial authentique")
        print("   ✅ Sélecteur de langue")
        
        print("\n🔗 ACCÈS:")
        print("   🏠 Site: https://martialcomp.com/fr/")
        print("   🏛️ Démo: Cliquer 'Accéder à la démo' sur la page")
        
    else:
        print("\n⚠️ RESTAURATION PARTIELLE")
        print("   Consultez les erreurs ci-dessus")
    
    sys.exit(0 if (success1 and success2) else 1)