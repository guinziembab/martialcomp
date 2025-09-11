#!/usr/bin/env python3
"""
Script de déploiement des templates et corrections dashboard en production.
Usage: python deploy_templates_production.py [--dry-run] [--backup]
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
import json

def create_backup():
    """Créer une sauvegarde des templates existants."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"templates_backup_{timestamp}"
    
    print(f"📦 Création de la sauvegarde dans: {backup_dir}")
    
    # Templates à sauvegarder
    templates_to_backup = [
        "competitions/templates/registration/",
        "competitions/templates/competitions/dashboard/",
        "competitions/templates/base.html"
    ]
    
    os.makedirs(backup_dir, exist_ok=True)
    
    for template_path in templates_to_backup:
        if os.path.exists(template_path):
            backup_path = os.path.join(backup_dir, template_path.replace('/', '_'))
            if os.path.isdir(template_path):
                shutil.copytree(template_path, backup_path)
            else:
                shutil.copy2(template_path, backup_path)
            print(f"   ✅ Sauvegardé: {template_path}")
    
    return backup_dir

def deploy_profile_templates():
    """Déployer les templates de profil manquants."""
    print("\n🚀 Déploiement des templates de profil...")
    
    # Vérifier que les templates existent
    profile_template = "competitions/templates/registration/profile.html"
    password_template = "competitions/templates/registration/password_change.html"
    profile_forms = "competitions/forms/profile_forms.py"
    
    status = {
        'profile_template': os.path.exists(profile_template),
        'password_template': os.path.exists(password_template),
        'profile_forms': os.path.exists(profile_forms)
    }
    
    print(f"   📄 Template profil: {'✅' if status['profile_template'] else '❌'}")
    print(f"   📄 Template mot de passe: {'✅' if status['password_template'] else '❌'}")
    print(f"   📄 Formulaires profil: {'✅' if status['profile_forms'] else '❌'}")
    
    # Vérifier la navigation dans base.html
    base_template = "competitions/templates/base.html"
    if os.path.exists(base_template):
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
            has_profile_link = "Mon profil" in content and "profile" in content
            print(f"   🔗 Lien profil dans navigation: {'✅' if has_profile_link else '❌'}")
    
    return status

def create_unified_dashboard_base():
    """Créer un template de base unifié pour tous les dashboards."""
    print("\n🎨 Création du template de base unifié pour les dashboards...")
    
    unified_base_content = '''{% extends 'base.html' %}
{% load i18n %}
{% load static %}

{% block title %}{% trans "Tableau de bord" %} - {{ user.get_full_name|default:user.username }} - {{ block.super }}{% endblock %}

{% block extra_css %}
{{ block.super }}
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<style>
    /* Variables CSS unifiées pour tous les dashboards */
    :root {
        --dashboard-primary: #3366ff;
        --dashboard-secondary: #6c757d;
        --dashboard-success: #28a745;
        --dashboard-warning: #ffc107;
        --dashboard-danger: #dc3545;
        --dashboard-info: #17a2b8;
        --dashboard-light: #f8f9fa;
        --dashboard-dark: #343a40;
        
        /* Variables spécifiques aux rôles */
        --club-primary: #3366ff;
        --federation-primary: #dc3545;
        --coach-primary: #28a745;
        --judge-primary: #6f42c1;
        --participant-primary: #17a2b8;
        --manager-primary: #0d6efd;
        --spectator-primary: #3498db;
        --admin-primary: #fd7e14;
        
        /* Layout variables */
        --sidebar-width: 250px;
        --header-height: 60px;
        --border-radius: 8px;
        --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        --transition: all 0.3s ease;
    }

    /* Layout principal unifié */
    .dashboard-container {
        min-height: 100vh;
        background-color: var(--dashboard-light);
    }
    
    .dashboard-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: var(--sidebar-width);
        height: 100vh;
        background: linear-gradient(135deg, var(--role-primary, var(--dashboard-primary)) 0%, #764ba2 100%);
        color: white;
        z-index: 1000;
        overflow-y: auto;
        transition: var(--transition);
    }
    
    .dashboard-main {
        margin-left: var(--sidebar-width);
        padding: 2rem;
        transition: var(--transition);
    }
    
    /* Header unifié */
    .dashboard-header {
        background: white;
        padding: 1rem 2rem;
        margin: -2rem -2rem 2rem -2rem;
        box-shadow: var(--box-shadow);
        border-radius: 0 0 var(--border-radius) var(--border-radius);
    }
    
    .dashboard-title {
        margin: 0;
        color: var(--dashboard-dark);
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .dashboard-subtitle {
        margin: 0;
        color: var(--dashboard-secondary);
        font-size: 0.875rem;
    }
    
    /* Navigation sidebar */
    .sidebar-header {
        padding: 1.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .sidebar-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .sidebar-subtitle {
        margin: 0;
        font-size: 0.875rem;
        opacity: 0.8;
    }
    
    .sidebar-nav {
        padding: 1rem 0;
    }
    
    .nav-item {
        margin: 0.25rem 1rem;
    }
    
    .nav-link {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        color: white;
        text-decoration: none;
        border-radius: var(--border-radius);
        transition: var(--transition);
    }
    
    .nav-link:hover {
        background-color: rgba(255,255,255,0.1);
        color: white;
        text-decoration: none;
    }
    
    .nav-link.active {
        background-color: rgba(255,255,255,0.2);
        font-weight: 600;
    }
    
    .nav-icon {
        margin-right: 0.75rem;
        width: 20px;
        text-align: center;
    }
    
    /* Cards unifiées */
    .dashboard-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--box-shadow);
        transition: var(--transition);
    }
    
    .dashboard-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .card-header {
        display: flex;
        justify-content: between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #eee;
    }
    
    .card-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--dashboard-dark);
    }
    
    /* Stats cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--box-shadow);
        text-align: center;
        transition: var(--transition);
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stat-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: var(--role-primary, var(--dashboard-primary));
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--dashboard-dark);
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: var(--dashboard-secondary);
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Boutons unifiés */
    .btn-dashboard {
        background: linear-gradient(135deg, var(--role-primary, var(--dashboard-primary)) 0%, #764ba2 100%);
        border: none;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: var(--border-radius);
        font-weight: 600;
        transition: var(--transition);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
    }
    
    .btn-dashboard:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        color: white;
        text-decoration: none;
    }
    
    .btn-dashboard i {
        margin-right: 0.5rem;
    }
    
    /* Responsive design unifié */
    @media (max-width: 768px) {
        .dashboard-sidebar {
            transform: translateX(-100%);
        }
        
        .dashboard-sidebar.show {
            transform: translateX(0);
        }
        
        .dashboard-main {
            margin-left: 0;
            padding: 1rem;
        }
        
        .dashboard-header {
            margin: -1rem -1rem 1rem -1rem;
            padding: 1rem;
        }
        
        .stats-grid {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
    }
    
    /* Profile section dans sidebar */
    .sidebar-profile {
        padding: 1rem;
        border-top: 1px solid rgba(255,255,255,0.2);
        margin-top: auto;
    }
    
    .profile-info {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .profile-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 0.75rem;
        background: rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .profile-details h6 {
        margin: 0;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .profile-details small {
        opacity: 0.8;
    }
    
    /* Role-specific color overrides */
    .dashboard-club { --role-primary: var(--club-primary); }
    .dashboard-federation { --role-primary: var(--federation-primary); }
    .dashboard-coach { --role-primary: var(--coach-primary); }
    .dashboard-judge { --role-primary: var(--judge-primary); }
    .dashboard-participant { --role-primary: var(--participant-primary); }
    .dashboard-manager { --role-primary: var(--manager-primary); }
    .dashboard-spectator { --role-primary: var(--spectator-primary); }
    .dashboard-admin { --role-primary: var(--admin-primary); }
</style>
{% endblock %}

{% block content %}
<div class="dashboard-container dashboard-{{ user.userprofile.role|default:'participant' }}">
    <!-- Sidebar -->
    <div class="dashboard-sidebar" id="sidebar">
        <div class="sidebar-header">
            <h5 class="sidebar-title">{% block dashboard_title %}{% trans "Tableau de bord" %}{% endblock %}</h5>
            <p class="sidebar-subtitle">{% block dashboard_subtitle %}{{ user.get_full_name|default:user.username }}{% endblock %}</p>
        </div>
        
        <nav class="sidebar-nav">
            {% block sidebar_nav %}
            <!-- Navigation par défaut -->
            <div class="nav-item">
                <a href="{% url 'dashboard:index' %}" class="nav-link">
                    <i class="fas fa-tachometer-alt nav-icon"></i>
                    {% trans "Accueil" %}
                </a>
            </div>
            <div class="nav-item">
                <a href="{% url 'profile' %}" class="nav-link">
                    <i class="fas fa-user nav-icon"></i>
                    {% trans "Mon profil" %}
                </a>
            </div>
            {% endblock %}
        </nav>
        
        <div class="sidebar-profile">
            <div class="profile-info">
                <div class="profile-avatar">
                    {% if user.userprofile.avatar %}
                        <img src="{{ user.userprofile.avatar.url }}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">
                    {% else %}
                        <i class="fas fa-user"></i>
                    {% endif %}
                </div>
                <div class="profile-details">
                    <h6>{{ user.get_full_name|default:user.username }}</h6>
                    <small>{% block user_role %}{{ user.userprofile.get_role_display|default:"Utilisateur" }}{% endblock %}</small>
                </div>
            </div>
            <a href="{% url 'logout' %}" class="nav-link">
                <i class="fas fa-sign-out-alt nav-icon"></i>
                {% trans "Déconnexion" %}
            </a>
        </div>
    </div>
    
    <!-- Contenu principal -->
    <div class="dashboard-main">
        <div class="dashboard-header">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="dashboard-title">{% block page_title %}{% trans "Tableau de bord" %}{% endblock %}</h1>
                    <p class="dashboard-subtitle">{% block page_subtitle %}{% trans "Bienvenue dans votre espace personnel" %}{% endblock %}</p>
                </div>
                <div class="d-block d-md-none">
                    <button class="btn btn-outline-primary" onclick="toggleSidebar()">
                        <i class="fas fa-bars"></i>
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Messages -->
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}
        
        <!-- Contenu spécifique au dashboard -->
        {% block dashboard_content %}
        <div class="stats-grid">
            {% block dashboard_stats %}
            <!-- Statistiques par défaut -->
            {% endblock %}
        </div>
        
        <div class="row">
            <div class="col-12">
                {% block dashboard_main_content %}
                <div class="dashboard-card">
                    <div class="card-header">
                        <h3 class="card-title">{% trans "Bienvenue" %}</h3>
                    </div>
                    <p>{% trans "Contenu du dashboard à personnaliser selon le rôle." %}</p>
                </div>
                {% endblock %}
            </div>
        </div>
        {% endblock %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Fermer la sidebar en cliquant en dehors (mobile)
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = event.target.closest('button');
    
    if (window.innerWidth <= 768 && 
        !sidebar.contains(event.target) && 
        !toggleBtn) {
        sidebar.classList.remove('show');
    }
});

// Gestion du responsive
window.addEventListener('resize', function() {
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth > 768) {
        sidebar.classList.remove('show');
    }
});
</script>
{% endblock %}'''
    
    # Créer le répertoire si nécessaire
    dashboard_dir = "competitions/templates/competitions/dashboard"
    os.makedirs(dashboard_dir, exist_ok=True)
    
    # Écrire le template unifié
    unified_base_path = os.path.join(dashboard_dir, "unified_base.html")
    with open(unified_base_path, 'w', encoding='utf-8') as f:
        f.write(unified_base_content)
    
    print(f"   ✅ Template de base unifié créé: {unified_base_path}")
    return unified_base_path

def update_dashboard_templates():
    """Mettre à jour tous les templates de dashboard pour utiliser la base unifiée."""
    print("\n🔄 Mise à jour des templates de dashboard...")
    
    dashboard_templates = {
        "admin.py": "admin",
        "club.py": "club", 
        "federation.py": "federation",
        "coach.py": "coach",
        "judge.py": "judge",
        "participant.py": "participant",
        "manager.py": "manager",
        "spectator.py": "spectator"
    }
    
    updated_templates = []
    
    for template_file, role in dashboard_templates.items():
        template_path = f"competitions/templates/competitions/dashboard/{role}.html"
        
        if os.path.exists(template_path):
            print(f"   🔄 Mise à jour: {template_path}")
            # Ici on pourrait implémenter la mise à jour automatique
            # Pour l'instant, on signale juste qu'il faut le faire manuellement
            updated_templates.append(template_path)
        else:
            print(f"   ⚠️  Template manquant: {template_path}")
    
    return updated_templates

def verify_deployment():
    """Vérifier que le déploiement s'est bien passé."""
    print("\n🔍 Vérification du déploiement...")
    
    checks = {
        "Templates de profil": {
            "registration/profile.html": os.path.exists("competitions/templates/registration/profile.html"),
            "registration/password_change.html": os.path.exists("competitions/templates/registration/password_change.html")
        },
        "Formulaires": {
            "profile_forms.py": os.path.exists("competitions/forms/profile_forms.py")
        },
        "Templates dashboard": {
            "unified_base.html": os.path.exists("competitions/templates/competitions/dashboard/unified_base.html")
        }
    }
    
    all_good = True
    for category, items in checks.items():
        print(f"\n   📂 {category}:")
        for item, status in items.items():
            print(f"      {'✅' if status else '❌'} {item}")
            if not status:
                all_good = False
    
    return all_good

def create_production_deployment_script():
    """Créer un script de déploiement pour la production."""
    script_content = '''#!/bin/bash
# Script de déploiement en production - Templates et Dashboard

echo "🚀 Déploiement des templates et dashboard en production"
echo "=================================================="

# Variables
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
TEMPLATES_DIR="competitions/templates"
STATIC_DIR="competitions/static"

# Créer la sauvegarde
echo "📦 Création de la sauvegarde..."
mkdir -p $BACKUP_DIR
cp -r $TEMPLATES_DIR $BACKUP_DIR/ 2>/dev/null || true
cp -r $STATIC_DIR $BACKUP_DIR/ 2>/dev/null || true

# Redémarrer le serveur Django si en production
if [ "$DJANGO_ENV" = "production" ]; then
    echo "🔄 Redémarrage du serveur Django..."
    systemctl restart gunicorn || service gunicorn restart || echo "⚠️ Impossible de redémarrer gunicorn"
fi

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Compiler les traductions
echo "🌍 Compilation des traductions..."
python manage.py compilemessages

echo "✅ Déploiement terminé!"
echo "📦 Sauvegarde disponible dans: $BACKUP_DIR"
'''
    
    script_path = "deploy_production.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Rendre le script exécutable
    os.chmod(script_path, 0o755)
    
    print(f"   ✅ Script de déploiement créé: {script_path}")
    return script_path

def main():
    parser = argparse.ArgumentParser(description='Déploiement des templates en production')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Mode test - affiche les actions sans les exécuter')
    parser.add_argument('--backup', action='store_true', default=True,
                       help='Créer une sauvegarde avant déploiement')
    
    args = parser.parse_args()
    
    print("🚀 DÉPLOIEMENT TEMPLATES ET DASHBOARD EN PRODUCTION")
    print("=" * 60)
    
    if args.dry_run:
        print("🧪 MODE TEST - Aucune modification ne sera appliquée")
        print("-" * 60)
    
    try:
        # Sauvegarde
        if args.backup and not args.dry_run:
            backup_dir = create_backup()
        
        # Déploiement des templates de profil
        profile_status = deploy_profile_templates()
        
        # Création du template de base unifié
        if not args.dry_run:
            unified_base = create_unified_dashboard_base()
        
        # Mise à jour des templates de dashboard
        updated_templates = update_dashboard_templates()
        
        # Création du script de déploiement
        if not args.dry_run:
            deployment_script = create_production_deployment_script()
        
        # Vérification
        if not args.dry_run:
            success = verify_deployment()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DU DÉPLOIEMENT")
        print("=" * 60)
        
        if not args.dry_run:
            print(f"📦 Sauvegarde créée: {backup_dir if args.backup else 'Aucune'}")
            print(f"📄 Templates de profil: {'✅' if all(profile_status.values()) else '⚠️'}")
            print(f"🎨 Base unifiée dashboard: ✅")
            print(f"🔄 Templates dashboard à mettre à jour: {len(updated_templates)}")
            print(f"📜 Script de déploiement: ✅")
            print(f"🔍 Vérification: {'✅' if success else '⚠️'}")
        else:
            print("🧪 Mode test - Aucune modification appliquée")
        
        print("\n📌 PROCHAINES ÉTAPES:")
        print("1. Mettre à jour manuellement les templates de dashboard")
        print("2. Tester en local avant déploiement production")
        print("3. Exécuter le script deploy_production.sh en production")
        print("4. Vérifier l'alignement des dashboards")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()