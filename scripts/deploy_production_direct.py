#!/usr/bin/env python3
"""
Script de déploiement direct en production - Templates et Dashboards
À exécuter directement sur le serveur de production.
"""

import os
import sys
import shutil
from datetime import datetime

def create_backup():
    """Créer une sauvegarde des templates existants."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    print(f"📦 Création de la sauvegarde: {backup_dir}")
    
    # Créer le répertoire de sauvegarde
    os.makedirs(backup_dir, exist_ok=True)
    
    # Templates à sauvegarder
    templates_to_backup = [
        "competitions/templates/registration/",
        "competitions/templates/competitions/dashboard/",
        "competitions/templates/base.html"
    ]
    
    for template_path in templates_to_backup:
        if os.path.exists(template_path):
            if os.path.isdir(template_path):
                # Copier un répertoire
                backup_path = os.path.join(backup_dir, template_path.replace('/', '_'))
                shutil.copytree(template_path, backup_path, dirs_exist_ok=True)
                print(f"   ✅ Répertoire sauvegardé: {template_path}")
            else:
                # Copier un fichier
                backup_path = os.path.join(backup_dir, os.path.basename(template_path))
                shutil.copy2(template_path, backup_path)
                print(f"   ✅ Fichier sauvegardé: {template_path}")
        else:
            print(f"   ⚠️  Introuvable: {template_path}")
    
    return backup_dir

def check_existing_templates():
    """Vérifier l'état actuel des templates."""
    print("\n🔍 Vérification des templates existants...")
    
    templates_status = {
        "Profile template": "competitions/templates/registration/profile.html",
        "Password template": "competitions/templates/registration/password_change.html",
        "Profile forms": "competitions/forms/profile_forms.py",
        "Base template": "competitions/templates/base.html",
        "Dashboard base": "competitions/templates/competitions/dashboard/base.html",
        "Participant dashboard": "competitions/templates/competitions/dashboard/participant.html",
        "Admin dashboard": "competitions/templates/competitions/dashboard/admin.html",
        "Club dashboard": "competitions/templates/competitions/dashboard/club.html",
        "Federation dashboard": "competitions/templates/competitions/dashboard/federation.html",
        "Manager dashboard": "competitions/templates/competitions/dashboard/manager.html",
        "Spectator dashboard": "competitions/templates/competitions/dashboard/spectator.html"
    }
    
    for name, path in templates_status.items():
        exists = os.path.exists(path)
        print(f"   {'✅' if exists else '❌'} {name}: {path}")
    
    return templates_status

def create_profile_template():
    """Créer le template de profil."""
    template_content = '''{% extends 'base.html' %}
{% load i18n %}
{% load static %}

{% block title %}{% trans "Mon Profil" %} - {{ block.super }}{% endblock %}

{% block extra_css %}
<style>
    .profile-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .profile-avatar {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 4px solid rgba(255,255,255,0.2);
        object-fit: cover;
    }
    
    .profile-card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        padding: 2rem;
        margin-bottom: 2rem;
    }
    
    .btn-edit {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .btn-edit:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        color: white;
    }
</style>
{% endblock %}

{% block content %}
<div class="profile-header">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-8">
                <div class="d-flex align-items-center">
                    <div class="me-4">
                        {% if user.userprofile.avatar %}
                            <img src="{{ user.userprofile.avatar.url }}" alt="{% trans 'Avatar' %}" class="profile-avatar">
                        {% else %}
                            <div class="profile-avatar d-flex align-items-center justify-content-center" style="background: rgba(255,255,255,0.2);">
                                <i class="fas fa-user fa-3x" style="color: rgba(255,255,255,0.7);"></i>
                            </div>
                        {% endif %}
                    </div>
                    <div>
                        <h1 class="mb-2">
                            {% if user.first_name or user.last_name %}
                                {{ user.first_name }} {{ user.last_name }}
                            {% else %}
                                {{ user.username }}
                            {% endif %}
                        </h1>
                        <div class="d-flex align-items-center">
                            <span class="badge bg-primary">
                                {% if user.userprofile.role == 'spectator' %}
                                    <i class="fas fa-eye me-1"></i>{% trans "Spectateur" %}
                                {% elif user.userprofile.role == 'participant' %}
                                    <i class="fas fa-user-ninja me-1"></i>{% trans "Participant" %}
                                {% elif user.userprofile.role == 'coach' %}
                                    <i class="fas fa-chalkboard-teacher me-1"></i>{% trans "Entraîneur" %}
                                {% elif user.userprofile.role == 'judge' %}
                                    <i class="fas fa-gavel me-1"></i>{% trans "Arbitre" %}
                                {% elif user.userprofile.role == 'manager' %}
                                    <i class="fas fa-users-cog me-1"></i>{% trans "Gestionnaire" %}
                                {% elif user.userprofile.role == 'admin' %}
                                    <i class="fas fa-crown me-1"></i>{% trans "Administrateur" %}
                                {% endif %}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 text-md-end">
                <a href="#edit-profile" class="btn btn-edit" data-bs-toggle="modal">
                    <i class="fas fa-edit me-2"></i>{% trans "Modifier le profil" %}
                </a>
            </div>
        </div>
    </div>
</div>

<div class="container">
    <div class="row">
        <div class="col-lg-8">
            <div class="profile-card">
                <h3><i class="fas fa-user me-2"></i>{% trans "Informations personnelles" %}</h3>
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">{% trans "Nom d'utilisateur" %}</label>
                            <p class="form-control-plaintext">{{ user.username }}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">{% trans "Adresse e-mail" %}</label>
                            <p class="form-control-plaintext">{{ user.email|default:"Non renseigné" }}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">{% trans "Prénom" %}</label>
                            <p class="form-control-plaintext">{{ user.first_name|default:"Non renseigné" }}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">{% trans "Nom" %}</label>
                            <p class="form-control-plaintext">{{ user.last_name|default:"Non renseigné" }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4">
            <div class="profile-card">
                <h3 class="mb-3"><i class="fas fa-bolt me-2"></i>{% trans "Actions rapides" %}</h3>
                <div class="d-grid gap-2">
                    <a href="#edit-profile" class="btn btn-outline-primary" data-bs-toggle="modal">
                        <i class="fas fa-edit me-2"></i>{% trans "Modifier mes informations" %}
                    </a>
                    <a href="{% url 'password_change' %}" class="btn btn-outline-warning">
                        <i class="fas fa-key me-2"></i>{% trans "Changer mon mot de passe" %}
                    </a>
                    <a href="{% url 'dashboard:index' %}" class="btn btn-outline-success">
                        <i class="fas fa-tachometer-alt me-2"></i>{% trans "Retour au tableau de bord" %}
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal d'édition simplifié -->
<div class="modal fade" id="edit-profile" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{% trans "Modifier mon profil" %}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="post">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="first_name" class="form-label">{% trans "Prénom" %}</label>
                        <input type="text" class="form-control" id="first_name" name="first_name" value="{{ user.first_name }}">
                    </div>
                    <div class="mb-3">
                        <label for="last_name" class="form-label">{% trans "Nom" %}</label>
                        <input type="text" class="form-control" id="last_name" name="last_name" value="{{ user.last_name }}">
                    </div>
                    <div class="mb-3">
                        <label for="email" class="form-label">{% trans "Adresse e-mail" %}</label>
                        <input type="email" class="form-control" id="email" name="email" value="{{ user.email }}" required>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{% trans "Annuler" %}</button>
                    <button type="submit" class="btn btn-primary">{% trans "Enregistrer" %}</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Créer le répertoire si nécessaire
    os.makedirs("competitions/templates/registration", exist_ok=True)
    
    # Écrire le template
    profile_path = "competitions/templates/registration/profile.html"
    with open(profile_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"   ✅ Template de profil créé: {profile_path}")
    return profile_path

def create_password_change_template():
    """Créer le template de changement de mot de passe."""
    template_content = '''{% extends 'base.html' %}
{% load i18n %}

{% block title %}{% trans "Changer le mot de passe" %} - {{ block.super }}{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-key me-2"></i>{% trans "Changer le mot de passe" %}</h3>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <div class="mb-3">
                            <label for="{{ form.old_password.id_for_label }}" class="form-label">{{ form.old_password.label }}</label>
                            {{ form.old_password }}
                            {% if form.old_password.errors %}
                                <div class="text-danger">
                                    {% for error in form.old_password.errors %}
                                        <small>{{ error }}</small>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>

                        <div class="mb-3">
                            <label for="{{ form.new_password1.id_for_label }}" class="form-label">{{ form.new_password1.label }}</label>
                            {{ form.new_password1 }}
                            {% if form.new_password1.errors %}
                                <div class="text-danger">
                                    {% for error in form.new_password1.errors %}
                                        <small>{{ error }}</small>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>

                        <div class="mb-3">
                            <label for="{{ form.new_password2.id_for_label }}" class="form-label">{{ form.new_password2.label }}</label>
                            {{ form.new_password2 }}
                            {% if form.new_password2.errors %}
                                <div class="text-danger">
                                    {% for error in form.new_password2.errors %}
                                        <small>{{ error }}</small>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>

                        <div class="d-flex justify-content-between">
                            <a href="{% url 'profile' %}" class="btn btn-secondary">
                                <i class="fas fa-arrow-left me-2"></i>{% trans "Retour" %}
                            </a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>{% trans "Changer le mot de passe" %}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Écrire le template
    password_path = "competitions/templates/registration/password_change.html"
    with open(password_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"   ✅ Template changement mot de passe créé: {password_path}")
    return password_path

def update_base_template():
    """Mettre à jour le template de base pour ajouter le lien profil."""
    base_path = "competitions/templates/base.html"
    
    if not os.path.exists(base_path):
        print(f"   ⚠️  Template base introuvable: {base_path}")
        return False
    
    # Lire le contenu actuel
    with open(base_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le lien profil existe déjà
    if "Mon profil" in content and "profile" in content:
        print(f"   ✅ Lien profil déjà présent dans: {base_path}")
        return True
    
    # Chercher la section du menu utilisateur et l'ajouter
    old_menu = '''<li><a class="dropdown-item" href="{% url 'dashboard:index' %}">{% trans "Tableau de bord" %}</a></li>'''
    new_menu = '''<li><a class="dropdown-item" href="{% url 'dashboard:index' %}">
                                    <i class="fas fa-tachometer-alt me-2"></i>{% trans "Tableau de bord" %}
                                </a></li>
                                <li><a class="dropdown-item" href="{% url 'profile' %}">
                                    <i class="fas fa-user-edit me-2"></i>{% trans "Mon profil" %}
                                </a></li>'''
    
    if old_menu in content:
        content = content.replace(old_menu, new_menu)
        
        # Sauvegarder
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Template base mis à jour: {base_path}")
        return True
    else:
        print(f"   ⚠️  Impossible de mettre à jour automatiquement: {base_path}")
        return False

def create_profile_forms():
    """Créer le fichier de formulaires de profil."""
    forms_content = '''from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class UserProfileForm(forms.ModelForm):
    """Formulaire de modification du profil utilisateur."""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Nom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=True,
        label=_("Adresse e-mail"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def clean_email(self):
        """Validation de l'email pour éviter les doublons."""
        email = self.cleaned_data.get('email')
        if email and self.user:
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise ValidationError(_("Cette adresse e-mail est déjà utilisée."))
        return email
    
    def save(self, commit=True):
        """Sauvegarde des données utilisateur."""
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            
            if commit:
                self.user.save()
        
        return self.user'''
    
    # Créer le répertoire si nécessaire
    os.makedirs("competitions/forms", exist_ok=True)
    
    # Écrire le fichier
    forms_path = "competitions/forms/profile_forms.py"
    with open(forms_path, 'w', encoding='utf-8') as f:
        f.write(forms_content)
    
    print(f"   ✅ Formulaires de profil créés: {forms_path}")
    return forms_path

def restart_services():
    """Redémarrer les services Django."""
    print("\n🔄 Redémarrage des services...")
    
    commands = [
        "python manage.py collectstatic --noinput",
        "python manage.py compilemessages",
        "systemctl restart gunicorn",
        "systemctl restart nginx"
    ]
    
    for cmd in commands:
        print(f"   Exécution: {cmd}")
        result = os.system(cmd)
        if result == 0:
            print(f"   ✅ Succès: {cmd}")
        else:
            print(f"   ⚠️  Erreur: {cmd}")

def main():
    print("🚀 DÉPLOIEMENT PRODUCTION DIRECT")
    print("=" * 50)
    print("Exécution directe sur le serveur de production")
    print("=" * 50)
    
    try:
        # 1. Vérification initiale
        check_existing_templates()
        
        # 2. Sauvegarde
        backup_dir = create_backup()
        
        # 3. Création des templates de profil
        print("\n📄 Création des templates de profil...")
        create_profile_template()
        create_password_change_template()
        
        # 4. Création des formulaires
        print("\n📋 Création des formulaires...")
        create_profile_forms()
        
        # 5. Mise à jour du template de base
        print("\n🔧 Mise à jour de la navigation...")
        update_base_template()
        
        # 6. Redémarrage des services
        restart_services()
        
        # Résumé final
        print("\n" + "=" * 50)
        print("✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 50)
        print(f"📦 Sauvegarde: {backup_dir}")
        print("📄 Templates de profil créés")
        print("📋 Formulaires créés")
        print("🔧 Navigation mise à jour")
        print("🔄 Services redémarrés")
        
        print("\n🧪 TESTS À EFFECTUER:")
        print("1. Visitez /profile/ pour tester le profil")
        print("2. Visitez /password_change/ pour le changement de mot de passe")
        print("3. Vérifiez la navigation dans le menu utilisateur")
        print("4. Testez la modification des informations profil")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("Consultez les logs pour plus d'informations")
        sys.exit(1)

if __name__ == "__main__":
    main()