#!/usr/bin/env python
"""
Script pour restaurer les fonctionnalités de gestion des fédérations
depuis le fichier backup vers le fichier actuel.

Ce script:
1. Sauvegarde le fichier actuel
2. Restaure les fonctions depuis le backup
3. Adapte les chemins des templates
"""

import os
import shutil
from datetime import datetime

# Chemins des fichiers
CURRENT_FILE = "apps/competitions/views/dashboard/federations.py"
BACKUP_FILE = "apps/competitions/views/dashboard/Backup/federations.py.backup"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def create_backup():
    """Créer une sauvegarde du fichier actuel"""
    backup_path = f"{CURRENT_FILE}.backup_{TIMESTAMP}"
    shutil.copy(CURRENT_FILE, backup_path)
    print(f"✅ Sauvegarde créée: {backup_path}")
    return backup_path

def extract_functions_from_backup():
    """Extraire les fonctions depuis le fichier backup"""
    functions = {
        'federation_manage_clubs': None,
        'federation_competitions': None,  # Note: dans backup c'est federation_competitions
        'federation_judges': None,
        'federation_manage_competitions': None,  # sera créé depuis federation_competitions
    }
    
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire chaque fonction
    for func_name in ['federation_manage_clubs', 'federation_competitions', 'federation_judges']:
        start_marker = f"def {func_name}(request, federation_id):"
        if start_marker in content:
            start_idx = content.find(start_marker)
            # Trouver la fin de la fonction (prochain @login_required ou def)
            next_func_idx = content.find('\n@login_required', start_idx + 1)
            if next_func_idx == -1:
                next_func_idx = content.find('\ndef ', start_idx + 1)
            if next_func_idx == -1:
                next_func_idx = len(content)
            
            # Extraire depuis @login_required avant la fonction
            decorator_idx = content.rfind('@login_required', 0, start_idx)
            function_code = content[decorator_idx:next_func_idx].rstrip()
            
            if func_name == 'federation_competitions':
                # Dupliquer pour federation_manage_competitions avec le nouveau nom
                functions['federation_manage_competitions'] = function_code.replace(
                    'def federation_competitions(',
                    'def federation_manage_competitions('
                )
            
            functions[func_name] = function_code
    
    return functions

def update_template_paths(function_code):
    """Mettre à jour les chemins des templates"""
    replacements = {
        "'competitions/federations/manage_clubs.html'": "'competitions/dashboard/federation_clubs.html'",
        "'competitions/federations/competitions.html'": "'competitions/dashboard/federation_competitions.html'",
        "'competitions/federations/judges.html'": "'competitions/dashboard/federation_judges.html'",
    }
    
    for old, new in replacements.items():
        function_code = function_code.replace(old, new)
    
    return function_code

def restore_functions():
    """Restaurer les fonctions dans le fichier actuel"""
    # Lire le fichier actuel
    with open(CURRENT_FILE, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    # Extraire les fonctions du backup
    functions = extract_functions_from_backup()
    
    # Pour chaque fonction à restaurer
    for func_name, func_code in functions.items():
        if func_code:
            # Mettre à jour les chemins des templates
            func_code = update_template_paths(func_code)
            
            # Trouver et remplacer la fonction stub actuelle
            stub_start = current_content.find(f"def {func_name}(request, federation_id):")
            if stub_start != -1:
                # Trouver le décorateur @login_required avant
                decorator_start = current_content.rfind('@login_required', 0, stub_start)
                
                # Trouver la fin de la fonction stub
                next_func = current_content.find('\n@login_required', stub_start + 1)
                if next_func == -1:
                    next_func = current_content.find('\ndef ', stub_start + 1)
                if next_func == -1:
                    next_func = len(current_content)
                
                # Remplacer
                before = current_content[:decorator_start]
                after = current_content[next_func:]
                current_content = before + func_code + '\n' + after
                
                print(f"✅ Fonction {func_name} restaurée")
    
    # Écrire le fichier mis à jour
    with open(CURRENT_FILE, 'w', encoding='utf-8') as f:
        f.write(current_content)
    
    print("✅ Toutes les fonctions ont été restaurées")

def create_enhanced_templates():
    """Créer des templates améliorés pour les fonctionnalités restaurées"""
    
    templates = {
        'federation_clubs.html': '''{% extends "competitions/dashboard/base_dashboard.html" %}
{% load i18n %}
{% load static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block dashboard_content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
                <h2>
                    <i class="fas fa-dojo"></i> {{ title }}
                </h2>
                <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> {% trans "Retour au dashboard" %}
                </a>
            </div>
        </div>
    </div>
    
    <!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <h3 class="text-primary">{{ affiliated_clubs.count }}</h3>
                    <p class="mb-0">{% trans "Clubs affiliés" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <h3 class="text-success">{{ available_clubs.count }}</h3>
                    <p class="mb-0">{% trans "Clubs disponibles" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <button class="btn btn-primary" data-toggle="modal" data-target="#addClubModal">
                        <i class="fas fa-plus"></i> {% trans "Affilier un club" %}
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Liste des clubs affiliés -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">{% trans "Clubs affiliés" %}</h3>
                </div>
                <div class="card-body">
                    {% if affiliated_clubs %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>{% trans "Nom du club" %}</th>
                                    <th>{% trans "Ville" %}</th>
                                    <th>{% trans "Responsable" %}</th>
                                    <th>{% trans "Pratiquants" %}</th>
                                    <th>{% trans "Actions" %}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for club in affiliated_clubs %}
                                <tr>
                                    <td>
                                        {% if club.logo %}
                                        <img src="{{ club.logo.url }}" alt="{{ club.name }}" style="height: 30px; margin-right: 10px;">
                                        {% endif %}
                                        {{ club.name }}
                                    </td>
                                    <td>{{ club.city|default:"-" }}</td>
                                    <td>{{ club.owner.get_full_name|default:club.owner.username }}</td>
                                    <td>
                                        <span class="badge badge-info">
                                            {{ club.practitioners.count }} {% trans "pratiquants" %}
                                        </span>
                                    </td>
                                    <td>
                                        <a href="#" class="btn btn-sm btn-info" title="{% trans 'Détails' %}">
                                            <i class="fas fa-eye"></i>
                                        </a>
                                        <a href="#" class="btn btn-sm btn-warning" title="{% trans 'Modifier' %}">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <button class="btn btn-sm btn-danger" title="{% trans 'Désaffilier' %}">
                                            <i class="fas fa-unlink"></i>
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> {% trans "Aucun club affilié pour le moment." %}
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal pour affilier un club -->
<div class="modal fade" id="addClubModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{% trans "Affilier un club" %}</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                {% if available_clubs %}
                <form method="post" action="#">
                    {% csrf_token %}
                    <div class="form-group">
                        <label for="club_select">{% trans "Sélectionner un club" %}</label>
                        <select class="form-control" id="club_select" name="club_id">
                            {% for club in available_clubs %}
                            <option value="{{ club.id }}">{{ club.name }} - {{ club.city }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-link"></i> {% trans "Affilier" %}
                    </button>
                </form>
                {% else %}
                <p>{% trans "Aucun club disponible pour l'affiliation." %}</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',

        'federation_competitions.html': '''{% extends "competitions/dashboard/base_dashboard.html" %}
{% load i18n %}
{% load static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block dashboard_content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
                <h2>
                    <i class="fas fa-trophy"></i> {{ title }}
                </h2>
                <div>
                    <button class="btn btn-primary" data-toggle="modal" data-target="#createCompetitionModal">
                        <i class="fas fa-plus"></i> {% trans "Créer une compétition" %}
                    </button>
                    <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filtres -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-body">
                    <form method="get" class="form-inline">
                        <div class="form-group mr-3">
                            <label class="mr-2">{% trans "Statut:" %}</label>
                            <select name="status" class="form-control form-control-sm">
                                <option value="">{% trans "Tous" %}</option>
                                <option value="upcoming">{% trans "À venir" %}</option>
                                <option value="ongoing">{% trans "En cours" %}</option>
                                <option value="completed">{% trans "Terminées" %}</option>
                            </select>
                        </div>
                        <div class="form-group mr-3">
                            <label class="mr-2">{% trans "Discipline:" %}</label>
                            <select name="discipline" class="form-control form-control-sm">
                                <option value="">{% trans "Toutes" %}</option>
                                {% for discipline in federation.disciplines.all %}
                                <option value="{{ discipline.id }}">{{ discipline.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <button type="submit" class="btn btn-sm btn-primary">
                            <i class="fas fa-filter"></i> {% trans "Filtrer" %}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Liste des compétitions -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">{% trans "Compétitions" %}</h3>
                </div>
                <div class="card-body">
                    {% if competitions %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>{% trans "Titre" %}</th>
                                    <th>{% trans "Date" %}</th>
                                    <th>{% trans "Lieu" %}</th>
                                    <th>{% trans "Discipline" %}</th>
                                    <th>{% trans "Inscrits" %}</th>
                                    <th>{% trans "Statut" %}</th>
                                    <th>{% trans "Actions" %}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for competition in competitions %}
                                <tr>
                                    <td>{{ competition.title }}</td>
                                    <td>
                                        {{ competition.start_date|date:"d/m/Y" }}
                                        {% if competition.end_date != competition.start_date %}
                                        - {{ competition.end_date|date:"d/m/Y" }}
                                        {% endif %}
                                    </td>
                                    <td>{{ competition.location }}</td>
                                    <td>
                                        {% for discipline in competition.disciplines.all %}
                                        <span class="badge badge-secondary">{{ discipline.name }}</span>
                                        {% endfor %}
                                    </td>
                                    <td>
                                        <span class="badge badge-info">
                                            {{ competition.registrations.count }} {% trans "inscrits" %}
                                        </span>
                                    </td>
                                    <td>
                                        {% if competition.is_upcoming %}
                                        <span class="badge badge-warning">{% trans "À venir" %}</span>
                                        {% elif competition.is_ongoing %}
                                        <span class="badge badge-success">{% trans "En cours" %}</span>
                                        {% else %}
                                        <span class="badge badge-secondary">{% trans "Terminée" %}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <a href="#" class="btn btn-sm btn-info" title="{% trans 'Détails' %}">
                                            <i class="fas fa-eye"></i>
                                        </a>
                                        <a href="#" class="btn btn-sm btn-warning" title="{% trans 'Modifier' %}">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <a href="#" class="btn btn-sm btn-primary" title="{% trans 'Gérer' %}">
                                            <i class="fas fa-cog"></i>
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> {% trans "Aucune compétition pour le moment." %}
                        <a href="#" class="alert-link" data-toggle="modal" data-target="#createCompetitionModal">
                            {% trans "Créer votre première compétition" %}
                        </a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''
    }
    
    # Créer les templates
    template_dir = "apps/competitions/templates/competitions/dashboard"
    for filename, content in templates.items():
        filepath = os.path.join(template_dir, filename)
        # Sauvegarder l'ancien si existe
        if os.path.exists(filepath):
            backup_path = f"{filepath}.backup_{TIMESTAMP}"
            shutil.copy(filepath, backup_path)
            print(f"✅ Template sauvegardé: {backup_path}")
        
        # Écrire le nouveau template
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Template créé/mis à jour: {filepath}")

def main():
    print("🔧 Restauration des fonctionnalités de gestion des fédérations")
    print("=" * 60)
    
    # Vérifier que les fichiers existent
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Fichier backup introuvable: {BACKUP_FILE}")
        return
    
    if not os.path.exists(CURRENT_FILE):
        print(f"❌ Fichier actuel introuvable: {CURRENT_FILE}")
        return
    
    # 1. Créer une sauvegarde
    backup_path = create_backup()
    
    try:
        # 2. Restaurer les fonctions
        restore_functions()
        
        # 3. Créer/mettre à jour les templates
        create_enhanced_templates()
        
        print("\n✅ Restauration terminée avec succès!")
        print(f"📁 Sauvegarde disponible: {backup_path}")
        print("\n⚠️  N'oubliez pas de:")
        print("   - Vérifier que les imports sont corrects")
        print("   - Tester les fonctionnalités")
        print("   - Adapter les templates si nécessaire")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la restauration: {e}")
        print(f"💾 Restauration depuis la sauvegarde: {backup_path}")
        shutil.copy(backup_path, CURRENT_FILE)
        print("✅ Fichier original restauré")

if __name__ == "__main__":
    main()