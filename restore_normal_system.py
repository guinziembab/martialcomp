# -*- coding: utf-8 -*-
"""
Script pour restaurer le système en état normal après les tests d'urgence
"""

import os
import shutil
from datetime import datetime

def restore_normal_system():
    """Restaurer le système en configuration normale"""
    
    print("RESTAURATION SYSTÈME NORMAL")
    print("=" * 30)
    
    changes_made = []
    
    # 1. RÉACTIVER LE CSRF MIDDLEWARE
    print("1. Réactivation du middleware CSRF...")
    
    base_settings = "config/settings/base.py"
    if os.path.exists(base_settings):
        # Créer une sauvegarde
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = f"{base_settings}.backup_restore_{timestamp}"
        shutil.copy2(base_settings, backup)
        
        with open(base_settings, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Réactiver le CSRF
        old_line = "    # 'django.middleware.csrf.CsrfViewMiddleware',  # DÉSACTIVÉ TEMPORAIREMENT POUR DEBUG"
        new_line = "    'django.middleware.csrf.CsrfViewMiddleware',"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            with open(base_settings, 'w', encoding='utf-8') as f:
                f.write(content)
            
            changes_made.append("✅ Middleware CSRF réactivé")
            print("   ✅ Middleware CSRF réactivé")
        else:
            print("   ⚠️ Middleware CSRF déjà actif ou pattern non trouvé")
    
    # 2. RESTAURER LA VUE COACH NORMALE
    print("\n2. Restauration vue coach normale...")
    
    dashboard_urls = "apps/competitions/urls/dashboard.py"
    if os.path.exists(dashboard_urls):
        with open(dashboard_urls, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer la vue d'urgence par la vue normale
        old_line = "    path('coach/', coach_emergency.coach_dashboard_emergency, name='coach'),"
        new_line = "    path('coach/', coach.coach_dashboard, name='coach'),"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            with open(dashboard_urls, 'w', encoding='utf-8') as f:
                f.write(content)
            
            changes_made.append("✅ Vue coach normale restaurée")
            print("   ✅ Vue coach normale restaurée")
        else:
            print("   ⚠️ Vue coach déjà normale ou pattern non trouvé")
    
    # 3. SUPPRIMER LES ROUTES D'URGENCE (optionnel)
    print("\n3. Options de nettoyage des routes d'urgence...")
    print("   Les routes d'urgence peuvent être conservées pour debug futur")
    print("   ou supprimées si plus nécessaires.")
    
    # 4. RÉSUMÉ
    print(f"\n" + "=" * 30)
    print("RESTAURATION TERMINÉE")
    print("=" * 30)
    
    if changes_made:
        print("Changements appliqués:")
        for change in changes_made:
            print(f"  {change}")
    else:
        print("Aucun changement nécessaire - système déjà normal")
    
    print(f"\nÉTAPES SUIVANTES:")
    print("1. Redémarrez Django: python manage.py runserver")
    print("2. Testez la connexion normale sur /accounts/login/")
    print("3. Vérifiez que les coaches vont vers le bon dashboard")
    print("4. Si problèmes CSRF persistent, vérifiez la configuration CSRF")
    
    print(f"\nFICHIERS DE SAUVEGARDE CRÉÉS:")
    if os.path.exists(base_settings + f".backup_restore_{timestamp}"):
        print(f"  • {base_settings}.backup_restore_{timestamp}")

def create_coach_template_fix():
    """Créer un template coach minimal pour éviter les erreurs"""
    
    print(f"\n4. Création template coach minimal...")
    
    coach_template_dir = "apps/competitions/templates/competitions/dashboard"
    coach_template = f"{coach_template_dir}/coach.html"
    
    if not os.path.exists(coach_template_dir):
        os.makedirs(coach_template_dir, exist_ok=True)
    
    if not os.path.exists(coach_template):
        minimal_template = '''{% extends "competitions/base_dashboard.html" %}
{% load i18n %}

{% block title %}{% trans "Dashboard Coach" %}{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">{% trans "Dashboard Coach" %}</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <h4>🎉 Bienvenue {{ user.username }} !</h4>
                        <p>Vous êtes maintenant sur votre dashboard coach.</p>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5>{% trans "Mes étudiants" %}</h5>
                                    <p>{% trans "Gérez vos étudiants ici" %}</p>
                                    <!-- Liens vers gestion étudiants -->
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5>{% trans "Mes cours" %}</h5>
                                    <p>{% trans "Planifiez et gérez vos cours" %}</p>
                                    <!-- Liens vers gestion cours -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        with open(coach_template, 'w', encoding='utf-8') as f:
            f.write(minimal_template)
        
        print(f"   ✅ Template coach minimal créé: {coach_template}")
        return True
    else:
        print(f"   ℹ️ Template coach existe déjà: {coach_template}")
        return False

if __name__ == "__main__":
    print("SCRIPT DE RESTAURATION SYSTÈME NORMAL")
    print("=" * 40)
    
    restore_normal_system()
    create_coach_template_fix()
    
    print("=" * 40)

# Exécuter automatiquement
restore_normal_system()
create_coach_template_fix()