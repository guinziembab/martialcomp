#!/bin/bash
# Script pour déployer le patch onboarding directement sur le serveur de production
# À exécuter directement sur le serveur de production via SSH

echo "================================================"
echo "🚀 DÉPLOIEMENT DIRECT PATCH ONBOARDING"
echo "================================================"
echo ""

# Variables
PROJECT_DIR="/home/martialc/martialcomp"
BACKUP_DIR="/home/martialc/backups/onboarding_$(date +%Y%m%d_%H%M%S)"

# Créer le répertoire de backup
echo "📁 Création du backup..."
mkdir -p $BACKUP_DIR

# Backup des fichiers existants
if [ -f "$PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py" ]; then
    cp $PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py $BACKUP_DIR/
    echo "✅ Backup de emergency_views.py"
fi
if [ -f "$PROJECT_DIR/apps/competitions/urls/onboarding.py" ]; then
    cp $PROJECT_DIR/apps/competitions/urls/onboarding.py $BACKUP_DIR/
    echo "✅ Backup de onboarding.py"
fi

# Créer les répertoires nécessaires
echo ""
echo "📁 Création des répertoires..."
mkdir -p $PROJECT_DIR/apps/competitions/management/commands
mkdir -p $PROJECT_DIR/apps/competitions/templates/competitions/onboarding

echo ""
echo "📝 Création des fichiers du patch..."

# 1. Créer la commande init_disciplines
cat > $PROJECT_DIR/apps/competitions/management/commands/init_disciplines.py << 'EOF'
"""
Commande Django pour initialiser les disciplines par défaut
Usage: python manage.py init_disciplines
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.competitions.models import Discipline
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialise les disciplines par défaut'

    def handle(self, *args, **options):
        disciplines_data = [
            {'name': 'Karaté', 'description': 'Art martial japonais'},
            {'name': 'Judo', 'description': 'Art martial japonais, sport olympique'},
            {'name': 'Taekwondo', 'description': 'Art martial coréen, sport olympique'},
            {'name': 'Kung Fu', 'description': 'Arts martiaux chinois traditionnels'},
            {'name': 'Aikido', 'description': 'Art martial japonais défensif'},
            {'name': 'Krav Maga', 'description': 'Système de self-défense israélien'},
            {'name': 'MMA', 'description': 'Arts martiaux mixtes'},
            {'name': 'Boxe', 'description': 'Sport de combat avec les poings'},
            {'name': 'Kickboxing', 'description': 'Sport de combat pieds-poings'},
            {'name': 'Muay Thai', 'description': 'Boxe thaïlandaise'},
            {'name': 'Jiu-Jitsu Brésilien', 'description': 'Art martial au sol'},
            {'name': 'Capoeira', 'description': 'Art martial brésilien acrobatique'},
            {'name': 'Sambo', 'description': 'Art martial russe'},
            {'name': 'Hapkido', 'description': 'Art martial coréen défensif'},
            {'name': 'Qwan Ki Do', 'description': 'Art martial vietnamien moderne'},
        ]
        
        created_count = 0
        activated_count = 0
        
        with transaction.atomic():
            for disc_data in disciplines_data:
                discipline, created = Discipline.objects.get_or_create(
                    name=disc_data['name'],
                    defaults={
                        'description': disc_data['description'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ Créée: {disc_data['name']}")
                else:
                    if not discipline.is_active:
                        discipline.is_active = True
                        discipline.save()
                        activated_count += 1
                        self.stdout.write(f"✅ Activée: {disc_data['name']}")
                    else:
                        self.stdout.write(f"✓ Existante: {disc_data['name']}")
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Terminé! {created_count} disciplines créées, '
            f'{activated_count} activées.'
        ))
EOF
echo "✅ Créé: init_disciplines.py"

# 2. Créer les vues d'urgence
cat > $PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py << 'EOF'
"""
Vues d'urgence sécurisées pour l'onboarding
Ces vues incluent une gestion d'erreurs robuste
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils.crypto import get_random_string
import logging
import traceback
from datetime import datetime

from apps.competitions.models import (
    Club, Federation, Discipline, UserProfile, Organization
)
from apps.competitions.forms.competitions import (
    ClubCreationForm, FederationCreationForm
)

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET", "POST"])
def safe_club_creation(request):
    """Vue sécurisée pour la création de club avec gestion d'erreurs robuste"""
    try:
        logger.info(f"Club creation accessed by {request.user.username}")
        
        # S'assurer que l'utilisateur a un profil
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            logger.warning(f"Creating missing profile for user {request.user.username}")
            profile = UserProfile.objects.create(
                user=request.user,
                role='club_manager'
            )
        
        # Récupérer les disciplines ou créer par défaut
        try:
            disciplines = Discipline.objects.filter(is_active=True)
            if not disciplines.exists():
                logger.warning("No active disciplines found, creating defaults")
                # Créer quelques disciplines par défaut
                default_disciplines = [
                    ('Karaté', 'Art martial japonais'),
                    ('Judo', 'Art martial japonais'),
                    ('Taekwondo', 'Art martial coréen'),
                ]
                for name, desc in default_disciplines:
                    Discipline.objects.get_or_create(
                        name=name,
                        defaults={'description': desc, 'is_active': True}
                    )
                disciplines = Discipline.objects.filter(is_active=True)
        except Exception as e:
            logger.error(f"Error fetching disciplines: {e}")
            disciplines = Discipline.objects.none()
        
        if request.method == 'POST':
            form = ClubCreationForm(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        club = form.save(commit=False)
                        club.created_by = request.user
                        
                        # Générer un subdomain unique
                        base_subdomain = club.name.lower().replace(' ', '-')
                        club.subdomain = f"{base_subdomain}-{get_random_string(4)}"
                        
                        club.save()
                        
                        # Associer les disciplines sélectionnées
                        if form.cleaned_data.get('disciplines'):
                            club.disciplines.set(form.cleaned_data['disciplines'])
                        
                        # Mettre à jour le profil utilisateur
                        profile.club = club
                        profile.save()
                        
                        logger.info(
                            f"Club created: {club.name} by {request.user.email}"
                        )
                        
                        messages.success(
                            request,
                            _("Votre club a été créé avec succès.")
                        )
                        return redirect('competitions:dashboard:club')
                
                except Exception as e:
                    logger.error(
                        f"Error creating club: {e}",
                        exc_info=True
                    )
                    messages.error(
                        request,
                        _("Erreur lors de la création. Veuillez réessayer.")
                    )
            else:
                logger.warning(f"Form errors: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = ClubCreationForm()
        
        context = {
            'form': form,
            'disciplines': disciplines,
            'step': 'club_creation',
            'progress': 60,
        }
        
        return render(
            request,
            'competitions/onboarding/club_creation.html',
            context
        )
    
    except Exception as e:
        logger.critical(f"Critical error in club creation: {e}", exc_info=True)
        messages.error(
            request,
            _("Erreur technique. Notre équipe a été notifiée.")
        )
        return redirect('onboarding:error')


@login_required
@require_http_methods(["GET", "POST"])
def safe_federation_creation(request):
    """Vue sécurisée pour la création de fédération avec gestion d'erreurs robuste"""
    try:
        logger.info(f"Federation creation accessed by {request.user.username}")
        
        # S'assurer que l'utilisateur a un profil
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            logger.warning(f"Creating missing profile for user {request.user.username}")
            profile = UserProfile.objects.create(
                user=request.user,
                role='federation_admin'
            )
        
        # Récupérer les disciplines
        try:
            disciplines = Discipline.objects.filter(is_active=True)
            if not disciplines.exists():
                logger.warning("No active disciplines found, creating defaults")
                # Créer quelques disciplines par défaut
                default_disciplines = [
                    ('Karaté', 'Art martial japonais'),
                    ('Judo', 'Art martial japonais'),
                    ('Taekwondo', 'Art martial coréen'),
                ]
                for name, desc in default_disciplines:
                    Discipline.objects.get_or_create(
                        name=name,
                        defaults={'description': desc, 'is_active': True}
                    )
                disciplines = Discipline.objects.filter(is_active=True)
        except Exception as e:
            logger.error(f"Error fetching disciplines: {e}")
            disciplines = Discipline.objects.none()
        
        if request.method == 'POST':
            form = FederationCreationForm(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        federation = form.save(commit=False)
                        
                        # Créer l'organisation associée
                        org_name = form.cleaned_data.get('name', 'Federation')
                        organization = Organization.objects.create(
                            name=org_name,
                            type='federation',
                            created_by=request.user
                        )
                        
                        federation.organization = organization
                        federation.created_by = request.user
                        
                        # Générer un subdomain unique
                        base_subdomain = federation.name.lower().replace(' ', '-')
                        federation.subdomain = f"{base_subdomain}-{get_random_string(4)}"
                        
                        federation.save()
                        
                        # Associer au moins une discipline par défaut
                        if disciplines.exists():
                            federation.disciplines.add(disciplines.first())
                        
                        # Mettre à jour le profil utilisateur
                        profile.federation = federation
                        profile.save()
                        
                        logger.info(
                            f"Federation created: {federation.name} "
                            f"by {request.user.email}"
                        )
                        
                        messages.success(
                            request,
                            _("Votre fédération a été créée avec succès.")
                        )
                        return redirect('competitions:dashboard:federations')
                
                except Exception as e:
                    logger.error(
                        f"Error creating federation: {e}",
                        exc_info=True
                    )
                    messages.error(
                        request,
                        _("Erreur lors de la création. Veuillez réessayer.")
                    )
            else:
                logger.warning(f"Form errors: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = FederationCreationForm()
        
        context = {
            'form': form,
            'disciplines': disciplines,
            'step': 'federation_creation',
            'progress': 60,
        }
        
        return render(
            request,
            'competitions/onboarding/federation_creation.html',
            context
        )
    
    except Exception as e:
        logger.critical(f"Critical error in federation creation: {e}", exc_info=True)
        messages.error(
            request,
            _("Erreur technique. Notre équipe a été notifiée.")
        )
        return redirect('onboarding:error')


def onboarding_error(request):
    """Page d'erreur gracieuse pour l'onboarding"""
    error_code = f"ERR-{get_random_string(8).upper()}"
    logger.error(f"Onboarding error page accessed. Code: {error_code}")
    
    context = {
        'error_code': error_code,
        'support_email': 'support@martialcomp.com',
        'timestamp': datetime.now()
    }
    
    return render(request, 'competitions/onboarding/error.html', context)


@login_required
def onboarding_complete(request):
    """Page de finalisation de l'onboarding"""
    logger.info(f"Onboarding completed for user {request.user.username}")
    
    context = {
        'user': request.user,
        'profile': getattr(request.user, 'userprofile', None),
    }
    
    return render(request, 'competitions/onboarding/complete.html', context)
EOF
echo "✅ Créé: emergency_views.py"

# 3. Créer la page d'erreur
cat > $PROJECT_DIR/apps/competitions/templates/competitions/onboarding/error.html << 'EOF'
{% extends "competitions/onboarding/base_onboarding.html" %}
{% load i18n static %}

{% block title %}{% trans "Problème Technique" %} - MartialComp{% endblock %}

{% block extra_css %}
<style>
    .error-container {
        min-height: 60vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .error-box {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 3rem;
        max-width: 600px;
        width: 100%;
        text-align: center;
    }
    
    .error-icon {
        width: 80px;
        height: 80px;
        margin: 0 auto 1.5rem;
        background: #FEE2E2;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .error-icon i {
        font-size: 40px;
        color: #DC2626;
    }
    
    .error-title {
        font-size: 1.875rem;
        font-weight: bold;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    
    .error-message {
        color: #6B7280;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    .error-code {
        font-family: monospace;
        background: #F3F4F6;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 2rem;
        font-size: 0.875rem;
        color: #6B7280;
    }
    
    .error-actions {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .btn-error {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .btn-primary-error {
        background: #2563EB;
        color: white;
    }
    
    .btn-primary-error:hover {
        background: #1D4ED8;
        transform: translateY(-1px);
    }
    
    .btn-secondary-error {
        background: #F3F4F6;
        color: #374151;
    }
    
    .btn-secondary-error:hover {
        background: #E5E7EB;
    }
    
    @media (max-width: 640px) {
        .error-box {
            padding: 2rem;
        }
        
        .error-title {
            font-size: 1.5rem;
        }
        
        .error-actions {
            flex-direction: column;
            width: 100%;
        }
        
        .btn-error {
            width: 100%;
            justify-content: center;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="error-container">
    <div class="error-box">
        <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        
        <h1 class="error-title">{% trans "Oops! Un problème est survenu" %}</h1>
        
        <p class="error-message">
            {% trans "Nous avons rencontré un problème technique lors du traitement de votre demande. Notre équipe a été notifiée et travaille sur une solution." %}
        </p>
        
        {% if error_code %}
        <div class="error-code">
            {% trans "Code d'erreur" %}: {{ error_code }}
        </div>
        {% endif %}
        
        <div class="error-actions">
            <a href="{% url 'competitions:onboarding:role_selection' %}" class="btn-error btn-primary-error">
                <i class="fas fa-redo"></i>
                {% trans "Réessayer" %}
            </a>
            
            <a href="{% url 'competitions:welcome' %}" class="btn-error btn-secondary-error">
                <i class="fas fa-home"></i>
                {% trans "Page d'accueil" %}
            </a>
            
            <a href="mailto:{{ support_email }}?subject=Erreur%20Onboarding%20{{ error_code }}" 
               class="btn-error btn-secondary-error">
                <i class="fas fa-envelope"></i>
                {% trans "Contacter le support" %}
            </a>
        </div>
    </div>
</div>
{% endblock %}
EOF
echo "✅ Créé: error.html"

# 4. Mettre à jour les URLs
echo ""
echo "🔧 Mise à jour des URLs..."

# Sauvegarder l'original s'il existe
if [ -f "$PROJECT_DIR/apps/competitions/urls/onboarding.py" ]; then
    cp $PROJECT_DIR/apps/competitions/urls/onboarding.py $PROJECT_DIR/apps/competitions/urls/onboarding.py.bak
fi

# Ajouter les imports nécessaires aux URLs existantes
python3 << 'PYTHON'
import os

urls_file = "/home/martialc/martialcomp/apps/competitions/urls/onboarding.py"

# Lire le fichier
with open(urls_file, 'r') as f:
    content = f.read()

# Vérifier si les imports sont déjà présents
if 'from apps.competitions.views.onboarding.emergency_views import' not in content:
    # Trouver la fin des imports
    import_section = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('from apps.competitions.views.onboarding'):
            # Ajouter après cette ligne
            lines.insert(i + 1, '''from apps.competitions.views.onboarding.emergency_views import (
    safe_club_creation,
    safe_federation_creation,
    onboarding_error,
    onboarding_complete
)''')
            break
    
    # Remplacer les URLs existantes
    for i, line in enumerate(lines):
        if "path('club/creation/', club.handle_club_creation" in line:
            lines[i] = "    # path('club/creation/', club.handle_club_creation, name='club_creation'),  # ANCIEN"
            lines.insert(i + 1, "    path('club/creation/', safe_club_creation, name='club_creation'),  # NOUVEAU - SÉCURISÉ")
        elif "path('federation/', federations.handle_federation_creation" in line:
            lines[i] = "    # path('federation/', federations.handle_federation_creation, name='federation'),  # ANCIEN"
            lines.insert(i + 1, "    path('federation/', safe_federation_creation, name='federation'),  # NOUVEAU - SÉCURISÉ")
    
    # Ajouter les nouvelles routes si elles n'existent pas
    if 'onboarding_error' not in content:
        # Trouver l'endroit pour ajouter les nouvelles routes
        for i, line in enumerate(lines):
            if "path('final/'," in line:
                lines.insert(i + 1, '''
    # Routes d'urgence (PATCH)
    path('error/', onboarding_error, name='error'),
    path('complete/', onboarding_complete, name='complete'),''')
                break
    
    # Écrire le fichier modifié
    with open(urls_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ URLs mises à jour")
else:
    print("✅ URLs déjà à jour")
PYTHON

# 5. Initialiser les disciplines
echo ""
echo "🔧 Initialisation des disciplines..."
cd $PROJECT_DIR
python manage.py init_disciplines || echo "⚠️  Erreur lors de l'initialisation des disciplines"

# 6. Collecter les fichiers statiques
echo ""
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# 7. Redémarrer les services
echo ""
echo "🔄 Redémarrage des services..."
touch tmp/restart.txt
echo "✅ Passenger redémarré"

echo ""
echo "================================================"
echo "✅ PATCH DÉPLOYÉ AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "📝 Vérifications:"
echo "- Backup créé dans: $BACKUP_DIR"
echo "- Tester: https://app.martialcomp.com/competitions/onboarding/"
echo "- Logs: tail -f /var/log/martialcomp/django.log"
echo ""
echo "🔄 Pour restaurer en cas de problème:"
echo "cp $BACKUP_DIR/* $PROJECT_DIR/apps/competitions/views/onboarding/"
echo "touch $PROJECT_DIR/tmp/restart.txt"
echo ""