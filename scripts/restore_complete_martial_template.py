#!/usr/bin/env python3
"""
Script pour restaurer le template martial complet avec toutes les fonctionnalités
"""
import os
import sys

# Ajouter le répertoire de production au PYTHONPATH
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
if PROD_DIR not in sys.path:
    sys.path.insert(0, PROD_DIR)

# Changer le répertoire de travail
os.chdir(PROD_DIR)

def restore_complete_martial_template():
    """Restaure le template martial complet avec toutes les fonctionnalités"""
    
    print("🥋 RESTAURATION TEMPLATE MARTIAL COMPLET")
    print("=" * 42)
    
    template_path = 'competitions/templates/competitions/welcome.html'
    
    try:
        # Sauvegarder le template actuel
        backup_path = f"{template_path}.backup_incomplete_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(template_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_content)
        print(f"✅ Sauvegarde créée: {backup_path}")
        
        # Template martial complet avec toutes les fonctionnalités
        complete_martial_template = '''<!DOCTYPE html>
{% load i18n %}
{% load static %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% trans "MartialComp - La Plateforme Complète de Gestion des Arts Martiaux" %}</title>
    
    <!-- Meta descriptions pour SEO -->
    <meta name="description" content="{% trans 'MartialComp est la solution complète pour organiser, gérer et participer aux compétitions d\\'arts martiaux. Gestion de clubs, membres, compétitions, finances et grades.' %}">
    <meta name="keywords" content="{% trans 'arts martiaux, compétitions, karaté, judo, taekwondo, gestion club, membres, finances, grades' %}">
    
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
        
        /* ==== FEATURES SECTION ==== */
        .features {
            padding: 100px 0;
            background: var(--secondary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 5rem;
        }
        
        .section-title {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--white);
        }
        
        .section-subtitle {
            font-size: 1.2rem;
            color: var(--gray);
            max-width: 600px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 3rem;
        }
        
        .feature-card {
            background: var(--dark);
            padding: 3rem;
            border-radius: var(--border-radius);
            text-align: center;
            transition: var(--transition);
            border: 1px solid rgba(212, 175, 55, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: var(--shadow-hover);
            border-color: var(--accent);
        }
        
        .feature-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 2rem;
            font-size: 2rem;
            color: var(--white);
        }
        
        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--white);
        }
        
        .feature-card p {
            color: var(--gray);
            line-height: 1.8;
            margin-bottom: 2rem;
        }
        
        .feature-list {
            list-style: none;
            margin-bottom: 2rem;
            text-align: left;
        }
        
        .feature-list li {
            padding: 0.5rem 0;
            color: var(--light);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .feature-list li::before {
            content: '✓';
            color: var(--accent);
            font-weight: bold;
        }
        
        /* ==== PRIORITY BADGE ==== */
        .priority-badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: var(--primary);
            color: var(--white);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .priority-badge.priority-1 {
            background: var(--primary);
        }
        
        .priority-badge.priority-2 {
            background: var(--accent-dark);
        }
        
        .priority-badge.priority-3 {
            background: var(--info);
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
            
            .features-grid {
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
                <h1>{% trans "La solution complète pour vos arts martiaux" %}</h1>
                <p class="subtitle">
                    {% trans "Gestion • Organisation • Performance" %}
                </p>
                <p class="description">
                    {% trans "MartialComp révolutionne la gestion des arts martiaux : clubs, membres, compétitions, finances, grades et formations. Une plateforme tout-en-un pour tous les acteurs du milieu martial." %}
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
                        {% trans "Accès au tableau de bord du Dojo Sakura avec gestion complète : 25 membres, finances, compétitions et plus." %}
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
    
    <!-- FEATURES SECTION -->
    <section id="features" class="features">
        <div class="container">
            <div class="section-header fade-in">
                <h2 class="section-title">{% trans "Fonctionnalités Complètes MartialComp" %}</h2>
                <p class="section-subtitle">
                    {% trans "Une solution tout-en-un pour tous les besoins des arts martiaux, classée par ordre d'importance" %}
                </p>
            </div>
            
            <div class="features-grid">
                <!-- 1. Gestion des Membres -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-1">{% trans "Priorité 1" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <h3>{% trans "Gestion des Membres" %}</h3>
                    <p>{% trans "Système complet de gestion des membres avec profils détaillés, historiques et suivi personnalisé." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Profils membres détaillés" %}</li>
                        <li>{% trans "Historique des entraînements" %}</li>
                        <li>{% trans "Suivi des progressions" %}</li>
                        <li>{% trans "Gestion des cotisations" %}</li>
                        <li>{% trans "Communications ciblées" %}</li>
                    </ul>
                </div>
                
                <!-- 2. Gestion de Club -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-1">{% trans "Priorité 1" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-building"></i>
                    </div>
                    <h3>{% trans "Gestion de Club" %}</h3>
                    <p>{% trans "Administration complète de votre club : planning, ressources, événements et coordination d'équipe." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Planning des cours" %}</li>
                        <li>{% trans "Gestion des salles" %}</li>
                        <li>{% trans "Événements internes" %}</li>
                        <li>{% trans "Rapports d'activité" %}</li>
                        <li>{% trans "Outils collaboratifs" %}</li>
                    </ul>
                </div>
                
                <!-- 3. Gestion de Fédération -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-1">{% trans "Priorité 1" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-sitemap"></i>
                    </div>
                    <h3>{% trans "Gestion de Fédération" %}</h3>
                    <p>{% trans "Outils avancés pour fédérations : supervision multi-clubs, standardisation et coordination nationale." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Supervision multi-clubs" %}</li>
                        <li>{% trans "Standardisation des processus" %}</li>
                        <li>{% trans "Coordination régionale" %}</li>
                        <li>{% trans "Rapports consolidés" %}</li>
                        <li>{% trans "Certification officielle" %}</li>
                    </ul>
                </div>
                
                <!-- 4. Coach Sportif -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-2">{% trans "Priorité 2" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-chalkboard-teacher"></i>
                    </div>
                    <h3>{% trans "Coach Sportif" %}</h3>
                    <p>{% trans "Outils dédiés aux entraîneurs : programmes personnalisés, suivi technique et développement des athlètes." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Programmes d'entraînement" %}</li>
                        <li>{% trans "Évaluation technique" %}</li>
                        <li>{% trans "Suivi de performance" %}</li>
                        <li>{% trans "Plans de progression" %}</li>
                        <li>{% trans "Analyses vidéo" %}</li>
                    </ul>
                </div>
                
                <!-- 5. Finances -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-2">{% trans "Priorité 2" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3>{% trans "Gestion Financière" %}</h3>
                    <p>{% trans "Comptabilité complète : cotisations, paiements, budgets et reporting financier intégré." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Facturation automatique" %}</li>
                        <li>{% trans "Suivi des paiements" %}</li>
                        <li>{% trans "Budgets et prévisions" %}</li>
                        <li>{% trans "Rapports comptables" %}</li>
                        <li>{% trans "Intégration bancaire" %}</li>
                    </ul>
                </div>
                
                <!-- 6. Boutique -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-2">{% trans "Priorité 2" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-shopping-cart"></i>
                    </div>
                    <h3>{% trans "Boutique Intégrée" %}</h3>
                    <p>{% trans "E-commerce complet : équipements, licences, formations avec gestion automatisée des commandes." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Catalogue équipements" %}</li>
                        <li>{% trans "Vente de licences" %}</li>
                        <li>{% trans "Formations payantes" %}</li>
                        <li>{% trans "Gestion des stocks" %}</li>
                        <li>{% trans "Paiement sécurisé" %}</li>
                    </ul>
                </div>
                
                <!-- 7. Système de Grades -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-3">{% trans "Priorité 3" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-medal"></i>
                    </div>
                    <h3>{% trans "Système de Grades" %}</h3>
                    <p>{% trans "Gestion complète des grades et certifications avec suivi des progressions et passages officiels." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Suivi des progressions" %}</li>
                        <li>{% trans "Passages de grades" %}</li>
                        <li>{% trans "Certifications officielles" %}</li>
                        <li>{% trans "Historique complet" %}</li>
                        <li>{% trans "Diplômes numériques" %}</li>
                    </ul>
                </div>
                
                <!-- 8. Gestionnaire de Compétitions -->
                <div class="feature-card fade-in">
                    <div class="priority-badge priority-3">{% trans "Priorité 3" %}</div>
                    <div class="feature-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <h3>{% trans "Gestionnaire de Compétitions" %}</h3>
                    <p>{% trans "Organisation complète de tournois : inscriptions, brackets, notation et résultats en temps réel." %}</p>
                    <ul class="feature-list">
                        <li>{% trans "Création de tournois" %}</li>
                        <li>{% trans "Gestion des inscriptions" %}</li>
                        <li>{% trans "Système de notation" %}</li>
                        <li>{% trans "Brackets automatiques" %}</li>
                        <li>{% trans "Résultats en temps réel" %}</li>
                    </ul>
                </div>
            </div>
        </div>
    </section>
    
    <!-- LOGIN MODAL -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('loginModal')">&times;</span>
            <h2>{% trans "Connexion" %}</h2>
            <form action="/login/" method="post">
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
            <form action="/accounts/signup/" method="post">
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
                    {% trans "Découvrez l'interface complète de gestion avec le Dojo Sakura, incluant toutes les fonctionnalités prioritaires." %}
                </p>
                
                <div style="background: rgba(212, 175, 55, 0.1); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
                    <h5 style="color: var(--white); margin-bottom: 1rem;">{% trans "Fonctionnalités disponibles dans la démo :" %}</h5>
                    <ul style="list-style: none; padding: 0; color: var(--gray);">
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Gestion de 25 membres actifs" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Administration du club Dojo Sakura" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Outils coach avec 3 programmes" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Comptabilité et finances" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Boutique avec équipements" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Système de grades et certifications" %}</li>
                        <li style="margin-bottom: 0.5rem;"><i class="fas fa-check" style="color: var(--accent); margin-right: 0.5rem;"></i>{% trans "Gestionnaire de compétitions" %}</li>
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
                    {% trans "Accéder à la démo complète" %}
                </button>
                
                <p style="font-size: 0.9rem; color: var(--gray); text-align: center;">
                    {% trans "Toutes les fonctionnalités sont disponibles avec des données réalistes pour tester." %}
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
        
        // Fonction pour la démo - CORRIGÉE avec bonne URL
        function loginDemo() {
            // Fermer la modale
            closeModal('demoModal');
            
            // Créer un formulaire de connexion automatique
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/login/';  // URL CORRIGÉE
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
            
            // Redirect vers dashboard club
            const nextInput = document.createElement('input');
            nextInput.type = 'hidden';
            nextInput.name = 'next';
            nextInput.value = '/competitions/dashboard/';
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
        
        # Écrire le template martial complet
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(complete_martial_template)
        
        print("✅ Template martial complet restauré avec toutes les fonctionnalités")
        return True
        
    except Exception as e:
        print(f"❌ Erreur restauration template: {e}")
        return False

def update_demo_club_user():
    """Met à jour l'utilisateur démo club"""
    
    print("\n🏛️ MISE À JOUR UTILISATEUR DÉMO CLUB")
    print("=" * 38)
    
    try:
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from django.contrib.auth.models import User
        from competitions.models.users import UserProfile
        from competitions.models.notifications import Notification
        
        # Mettre à jour l'utilisateur démo club
        demo_user, created = User.objects.get_or_create(
            username='dojo_sakura_manager',
            defaults={
                'email': 'manager@dojo-sakura.com',
                'first_name': 'Hiroshi',
                'last_name': 'Tanaka',
                'is_active': True
            }
        )
        
        # Toujours mettre à jour le mot de passe
        demo_user.set_password('demo2025')
        demo_user.save()
        print("✅ Utilisateur démo club mis à jour")
        
        # Mettre à jour le profil
        demo_profile, created = UserProfile.objects.get_or_create(
            user=demo_user,
            defaults={
                'role': 'club_manager',
                'onboarding_completed': True,
                'onboarding_step': 'completed'
            }
        )
        
        # S'assurer que l'onboarding est complété
        demo_profile.onboarding_completed = True
        demo_profile.onboarding_step = 'completed'
        demo_profile.save()
        print("✅ Profil démo configuré")
        
        # Créer notifications réalistes pour toutes les fonctionnalités
        demo_notifications = [
            {
                'title': 'Bienvenue dans MartialComp',
                'message': 'Votre compte Dojo Sakura est actif. Toutes les fonctionnalités sont disponibles.',
                'notification_type': 'success',
                'priority': 'important'
            },
            {
                'title': 'Gestion des membres',
                'message': '25 membres actifs dans votre club. 3 nouveaux cette semaine.',
                'notification_type': 'info',
                'priority': 'standard'
            },
            {
                'title': 'Finances du club',
                'message': 'Rapport mensuel disponible. Revenus : 2,500€ ce mois.',
                'notification_type': 'success',
                'priority': 'important'
            },
            {
                'title': 'Passage de grades',
                'message': 'Examen ceinture noire programmé le 15 juillet. 4 candidats inscrits.',
                'notification_type': 'warning',
                'priority': 'important'
            },
            {
                'title': 'Nouvelle commande boutique',
                'message': 'Commande équipements reçue : 3 kimonos et 2 ceintures.',
                'notification_type': 'info',
                'priority': 'standard'
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
        
        print(f"✅ {notifications_created} nouvelles notifications créées")
        
        print(f"\n📋 COMPTE DÉMO COMPLET:")
        print(f"   👤 Username: dojo_sakura_manager")
        print(f"   🔑 Password: demo2025")
        print(f"   👥 Rôle: {demo_profile.role}")
        print(f"   🏛️ Club: Dojo Sakura")
        print(f"   ✅ Onboarding: {demo_profile.onboarding_completed}")
        print(f"   🔔 Notifications: {Notification.objects.filter(user=demo_user).count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour utilisateur démo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🥋 RESTAURATION TEMPLATE MARTIAL COMPLET")
    print("=" * 45)
    print(f"📂 Répertoire: {os.getcwd()}")
    
    success1 = restore_complete_martial_template()
    success2 = update_demo_club_user()
    
    print(f"\n📋 RÉSUMÉ:")
    print(f"   {'✅' if success1 else '❌'} Template martial complet restauré")
    print(f"   {'✅' if success2 else '❌'} Compte démo mis à jour")
    
    if success1 and success2:
        print("\n🎉 TEMPLATE MARTIAL COMPLET RESTAURÉ!")
        print("\n🥋 FONCTIONNALITÉS PAR ORDRE D'IMPORTANCE:")
        print("   1️⃣ PRIORITÉ 1 (Essentielles):")
        print("      • Gestion des Membres")
        print("      • Gestion de Club") 
        print("      • Gestion de Fédération")
        print("   2️⃣ PRIORITÉ 2 (Importantes):")
        print("      • Coach Sportif")
        print("      • Finances")
        print("      • Boutique")
        print("   3️⃣ PRIORITÉ 3 (Complémentaires):")
        print("      • Système de Grades")
        print("      • Gestionnaire de Compétitions")
        
        print("\n🎨 THÈME MARTIAL AUTHENTIQUE:")
        print("   🔴 Rouge martial: #c41e3a")
        print("   🟡 Or traditionnel: #d4af37")
        print("   ⚫ Fond profond: #121212")
        print("   👊 Icône: fas fa-fist-raised")
        
        print("\n🏛️ DÉMO CLUB COMPLÈTE:")
        print("   👤 dojo_sakura_manager / demo2025")
        print("   🚪 Accès: Dashboard club (sécurisé)")
        print("   📊 Toutes fonctionnalités testables")
        
        print("\n🌐 FONCTIONNALITÉS RESTAURÉES:")
        print("   ✅ Bouton 'Rejoindre la phase de test'")
        print("   ✅ URLs de connexion corrigées (/login/)")
        print("   ✅ Modal d'inscription (/accounts/signup/)")
        print("   ✅ Présentation complète des 8 fonctionnalités")
        print("   ✅ Priorités visuelles avec badges")
        print("   ✅ Sélecteur de langues")
        
        print("\n🔗 ACCÈS:")
        print("   🏠 Site: https://martialcomp.com/fr/")
        print("   🏛️ Démo: Bouton 'Accéder à la démo complète'")
        
    else:
        print("\n⚠️ RESTAURATION PARTIELLE")
        print("   Consultez les erreurs ci-dessus")
    
    sys.exit(0 if (success1 and success2) else 1)