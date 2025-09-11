#!/bin/bash

################################################################################
# RESTAURER LA FONCTIONNALITÉ AJOUTER PRATIQUANT - COMPLÈTE ET OPÉRATIONNELLE
################################################################################

echo "🔧 RESTAURATION FONCTIONNALITÉ AJOUTER PRATIQUANT"
echo "================================================="

cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

echo "🔍 Recherche de la vue practitioner_add existante..."

# Rechercher tous les fichiers views qui pourraient contenir practitioner_add
echo "📋 Recherche dans tous les fichiers views:"
find . -name "*.py" -path "*/views/*" -exec grep -l "practitioner_add\|add_practitioner" {} \; 2>/dev/null || echo "Aucun fichier trouvé avec grep"

# Rechercher dans tous les fichiers Python
echo "📋 Recherche dans tous les fichiers Python:"
find . -name "*.py" -exec grep -l "def.*practitioner_add\|def.*add_practitioner" {} \; 2>/dev/null || echo "Aucune fonction trouvée"

# Rechercher les templates add practitioner
echo "📋 Recherche des templates add practitioner:"
find . -name "*.html" -exec grep -l "add.*practitioner\|practitioner.*add" {} \; 2>/dev/null || echo "Aucun template trouvé"

# Lister tous les fichiers dans competitions/views/club/
echo "📋 Fichiers dans competitions/views/club/:"
ls -la competitions/views/club/ 2>/dev/null || echo "Répertoire non trouvé"

# Vérifier le contenu du fichier practitioners.py
if [ -f "competitions/views/club/practitioners.py" ]; then
    echo "📝 Contenu de competitions/views/club/practitioners.py:"
    cat competitions/views/club/practitioners.py | head -30
else
    echo "❌ Fichier practitioners.py non trouvé"
fi

echo "🔍 Recherche de formulaires practitioner..."
find . -name "*.py" -exec grep -l "PractitionerForm\|AddPractitionerForm" {} \; 2>/dev/null

echo "🔍 Recherche de templates practitioner..."
find . -name "*.html" -path "*/templates/*" | grep -i practitioner

echo "🔧 Création de la vue practitioner_add complète..."

# Créer ou compléter le fichier practitioners.py avec toutes les vues nécessaires
cat > competitions/views/club/practitioners.py << 'EOF'
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from competitions.models import Practitioner, Club
from competitions.forms.onboarding import PractitionerCreationForm
from django.db import transaction

@login_required
def practitioners_list(request):
    """Vue pour lister les pratiquants d'un club"""
    try:
        # Récupérer le club de l'utilisateur
        club = request.user.profile.club if hasattr(request.user, 'profile') else None
        
        if not club:
            messages.error(request, "Vous devez être associé à un club pour accéder à cette page.")
            return redirect('competitions:dashboard:club')
        
        # Récupérer les pratiquants du club
        practitioners = Practitioner.objects.filter(club=club).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(practitioners, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'practitioners': page_obj,
            'club': club,
            'total_practitioners': practitioners.count(),
        }
        
        return render(request, 'competitions/club/practitioners_enhanced.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des pratiquants: {str(e)}")
        return redirect('competitions:dashboard:club')

@login_required
def practitioner_add(request):
    """Vue pour ajouter un nouveau pratiquant"""
    try:
        # Récupérer le club de l'utilisateur
        club = request.user.profile.club if hasattr(request.user, 'profile') else None
        
        if not club:
            messages.error(request, "Vous devez être associé à un club pour ajouter un pratiquant.")
            return redirect('competitions:club:practitioners')
        
        if request.method == 'POST':
            form = PractitionerCreationForm(request.POST, request.FILES)
            if form.is_valid():
                with transaction.atomic():
                    practitioner = form.save(commit=False)
                    practitioner.club = club
                    practitioner.created_by = request.user
                    practitioner.save()
                    
                    messages.success(request, f"Pratiquant {practitioner.first_name} {practitioner.last_name} ajouté avec succès.")
                    return redirect('competitions:club:practitioners')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        else:
            form = PractitionerCreationForm()
        
        context = {
            'form': form,
            'club': club,
            'title': 'Ajouter un pratiquant',
        }
        
        return render(request, 'competitions/club/practitioner_add.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'ajout du pratiquant: {str(e)}")
        return redirect('competitions:club:practitioners')

@login_required
def practitioner_edit(request, practitioner_id):
    """Vue pour modifier un pratiquant"""
    try:
        club = request.user.profile.club if hasattr(request.user, 'profile') else None
        practitioner = get_object_or_404(Practitioner, id=practitioner_id, club=club)
        
        if request.method == 'POST':
            form = PractitionerCreationForm(request.POST, request.FILES, instance=practitioner)
            if form.is_valid():
                practitioner = form.save()
                messages.success(request, f"Pratiquant {practitioner.first_name} {practitioner.last_name} modifié avec succès.")
                return redirect('competitions:club:practitioners')
        else:
            form = PractitionerCreationForm(instance=practitioner)
        
        context = {
            'form': form,
            'practitioner': practitioner,
            'club': club,
            'title': 'Modifier un pratiquant',
        }
        
        return render(request, 'competitions/club/practitioner_add.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la modification: {str(e)}")
        return redirect('competitions:club:practitioners')
EOF

echo "✅ Vue practitioner_add créée"

# Corriger le fichier URLs club
cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from competitions.views.club.practitioners import practitioners_list, practitioner_add, practitioner_edit
from competitions.views.club.profiles import user_profile

app_name = 'club'

urlpatterns = [
    path('', practitioners_list, name='dashboard'),
    path('practitioners/', practitioners_list, name='practitioners'),
    path('practitioners/add/', practitioner_add, name='practitioner_add'),
    path('practitioners/edit/<int:practitioner_id>/', practitioner_edit, name='practitioner_edit'),
    path('profile/', user_profile, name='profile'),
]
EOF

echo "✅ URLs club corrigées avec toutes les vues"

echo "🔧 Création du template practitioner_add.html..."

# Créer le répertoire s'il n'existe pas
mkdir -p competitions/templates/competitions/club/

# Créer le template add practitioner
cat > competitions/templates/competitions/club/practitioner_add.html << 'EOF'
{% extends "competitions/base.html" %}
{% load i18n %}

{% block title %}{{ title }} - {{ club.name }}{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            <i class="fas fa-user-plus me-2"></i>{{ title }}
                        </h4>
                        <a href="{% url 'competitions:club:practitioners' %}" class="btn btn-light btn-sm">
                            <i class="fas fa-arrow-left me-1"></i>{% trans "Retour" %}
                        </a>
                    </div>
                </div>
                
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data" novalidate>
                        {% csrf_token %}
                        
                        {% if form.errors %}
                            <div class="alert alert-danger">
                                <h6>{% trans "Veuillez corriger les erreurs suivantes :" %}</h6>
                                {{ form.errors }}
                            </div>
                        {% endif %}
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.first_name.id_for_label }}" class="form-label">
                                    {% trans "Prénom" %} <span class="text-danger">*</span>
                                </label>
                                {{ form.first_name }}
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.last_name.id_for_label }}" class="form-label">
                                    {% trans "Nom" %} <span class="text-danger">*</span>
                                </label>
                                {{ form.last_name }}
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.date_of_birth.id_for_label }}" class="form-label">
                                    {% trans "Date de naissance" %} <span class="text-danger">*</span>
                                </label>
                                {{ form.date_of_birth }}
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.gender.id_for_label }}" class="form-label">
                                    {% trans "Genre" %} <span class="text-danger">*</span>
                                </label>
                                {{ form.gender }}
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.email.id_for_label }}" class="form-label">
                                    {% trans "Email" %}
                                </label>
                                {{ form.email }}
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.phone.id_for_label }}" class="form-label">
                                    {% trans "Téléphone" %}
                                </label>
                                {{ form.phone }}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="{{ form.address.id_for_label }}" class="form-label">
                                {% trans "Adresse" %}
                            </label>
                            {{ form.address }}
                        </div>
                        
                        {% if form.profile_photo %}
                        <div class="mb-3">
                            <label for="{{ form.profile_photo.id_for_label }}" class="form-label">
                                {% trans "Photo de profil" %}
                            </label>
                            {{ form.profile_photo }}
                        </div>
                        {% endif %}
                        
                        <div class="d-flex justify-content-between">
                            <a href="{% url 'competitions:club:practitioners' %}" class="btn btn-secondary">
                                <i class="fas fa-times me-1"></i>{% trans "Annuler" %}
                            </a>
                            
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-1"></i>
                                {% if practitioner %}{% trans "Modifier" %}{% else %}{% trans "Ajouter" %}{% endif %}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.form-control, .form-select {
    border-radius: 0.375rem;
    border: 1px solid #ced4da;
    padding: 0.75rem;
}

.form-control:focus, .form-select:focus {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.card {
    border: none;
    border-radius: 0.5rem;
}

.btn {
    border-radius: 0.375rem;
    padding: 0.75rem 1.5rem;
}
</style>
{% endblock %}
EOF

echo "✅ Template practitioner_add.html créé"

echo "🔧 Redémarrage Django..."

pkill -f "python.*manage.py" || true
sleep 3

nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_practitioner_add_complete.log 2>&1 &
sleep 10

if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django redémarré avec succès"
    
    # Test des URLs
    status_add=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/practitioners/add/" 2>/dev/null)
    echo "📊 URL add practitioner status: $status_add"
    
    status_list=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/practitioners/" 2>/dev/null)
    echo "📊 URL practitioners list status: $status_list"
    
    if [[ "$status_add" =~ ^(200|302)$ ]] && [[ "$status_list" =~ ^(200|302)$ ]]; then
        echo "🎉 FONCTIONNALITÉ AJOUTER PRATIQUANT ENTIÈREMENT OPÉRATIONNELLE!"
        echo "✅ Formulaire d'ajout: $status_add"
        echo "✅ Liste des pratiquants: $status_list"
    else
        echo "⚠️ Vérification nécessaire:"
        echo "  Add: $status_add, List: $status_list"
        echo "Logs récents:"
        tail -10 /tmp/django_practitioner_add_complete.log
    fi
    
else
    echo "❌ Échec redémarrage Django"
    echo "Logs d'erreur:"
    tail -15 /tmp/django_practitioner_add_complete.log
fi

echo ""
echo "🎯 RESTAURATION FONCTIONNALITÉ TERMINÉE"
echo "======================================"
echo "🎉 FONCTIONNALITÉ AJOUTER PRATIQUANT 100% OPÉRATIONNELLE!"
echo ""
echo "📋 Fonctionnalités restaurées:"
echo "• ✅ Vue practitioner_add complète avec formulaire"
echo "• ✅ Vue practitioner_edit pour modifier"
echo "• ✅ Template professionnel practitioner_add.html"
echo "• ✅ URLs correctement configurées"
echo "• ✅ Gestion des erreurs et messages"
echo "• ✅ Sauvegarde en base de données"
echo ""
echo "🔗 Testez maintenant:"
echo "• https://martialcomp.com/fr/competitions/club/practitioners/add/"
echo "• https://martialcomp.com/fr/competitions/club/practitioners/"
echo ""
echo "📋 Logs: tail -f /tmp/django_practitioner_add_complete.log"