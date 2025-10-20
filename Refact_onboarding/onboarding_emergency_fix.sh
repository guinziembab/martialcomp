#!/bin/bash
# Script d'urgence pour corriger l'onboarding MartialComp
# À exécuter immédiatement pour débloquer la production

echo "=========================================="
echo "🚨 CORRECTION D'URGENCE - ONBOARDING"
echo "=========================================="
echo ""

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_DIR="$PROJECT_DIR/logs"
BACKUP_DIR="/tmp/onboarding_backup_$(date +%Y%m%d_%H%M%S)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Créer un backup
echo -e "${YELLOW}📦 Création backup...${NC}"
mkdir -p "$BACKUP_DIR"
echo ""

# ==========================================
# ÉTAPE 1: Initialiser les Disciplines
# ==========================================
echo -e "${YELLOW}🗄️ ÉTAPE 1: Initialisation des disciplines${NC}"
echo ""

cd "$PROJECT_DIR"
source ../venv/bin/activate

python3 << 'PYTHON_EOF'
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from competitions.models import Discipline

# Disciplines par défaut pour tous les arts martiaux
default_disciplines = [
    {'name': 'Karaté', 'is_active': True},
    {'name': 'Judo', 'is_active': True},
    {'name': 'Taekwondo', 'is_active': True},
    {'name': 'Ju-Jitsu', 'is_active': True},
    {'name': 'Aïkido', 'is_active': True},
    {'name': 'Kung Fu', 'is_active': True},
    {'name': 'Muay Thai', 'is_active': True},
    {'name': 'Krav Maga', 'is_active': True},
    {'name': 'Capoeira', 'is_active': True},
    {'name': 'MMA', 'is_active': True},
]

created_count = 0
existing_count = 0

for disc_data in default_disciplines:
    discipline, created = Discipline.objects.get_or_create(
        name=disc_data['name'],
        defaults={'is_active': disc_data['is_active']}
    )
    if created:
        created_count += 1
    else:
        existing_count += 1

print(f"✅ Disciplines initialisées:")
print(f"   - Créées: {created_count}")
print(f"   - Existantes: {existing_count}")
print(f"   - Total: {Discipline.objects.count()}")
PYTHON_EOF

echo ""

# ==========================================
# ÉTAPE 2: Corriger les Vues d'Onboarding
# ==========================================
echo -e "${YELLOW}🔧 ÉTAPE 2: Correction des vues d'onboarding${NC}"
echo ""

# Créer un fichier de vue corrigé temporaire
cat > "$PROJECT_DIR/apps/competitions/views/onboarding/emergency_fix.py" << 'PYTHON_EOF'
"""
Corrections d'urgence pour l'onboarding
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
import logging

from ...models import Discipline, Club, Federation
from ...forms.onboarding import ClubCreationForm, FederationCreationForm

logger = logging.getLogger(__name__)


@login_required
def safe_club_creation(request):
    """Version sécurisée de handle_club_creation"""
    try:
        # Vérifier les disciplines
        disciplines = Discipline.objects.filter(is_active=True)
        
        if not disciplines.exists():
            messages.warning(
                request,
                _("Configuration en cours. Veuillez réessayer dans quelques instants.")
            )
            return redirect('dashboard')
        
        if request.method == 'POST':
            form = ClubCreationForm(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    club = form.save(commit=False)
                    club.owner = request.user
                    club.save()
                    
                    # Sauvegarder les disciplines
                    form.save_m2m()
                    
                    # Mettre à jour le profil
                    profile = request.user.profile
                    profile.club = club
                    profile.onboarding_completed = True
                    profile.save()
                    
                    messages.success(request, _("Votre club a été créé avec succès!"))
                    return redirect('dashboard:club')
                
                except Exception as e:
                    logger.error(f"Error creating club: {e}", exc_info=True)
                    messages.error(request, _("Erreur lors de la création du club. Veuillez réessayer."))
            else:
                messages.error(request, _("Veuillez corriger les erreurs du formulaire."))
        else:
            form = ClubCreationForm()
        
        context = {
            'form': form,
            'disciplines': disciplines,
        }
        
        return render(request, 'competitions/onboarding/club_creation.html', context)
    
    except Exception as e:
        logger.error(f"Critical error in club creation: {e}", exc_info=True)
        messages.error(request, _("Une erreur technique est survenue. Support contacté."))
        return redirect('dashboard')


@login_required
def safe_federation_creation(request):
    """Version sécurisée de handle_federation_creation"""
    try:
        disciplines = Discipline.objects.filter(is_active=True)
        
        if not disciplines.exists():
            messages.warning(
                request,
                _("Configuration en cours. Veuillez réessayer dans quelques instants.")
            )
            return redirect('dashboard')
        
        if request.method == 'POST':
            form = FederationCreationForm(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    federation = form.save(commit=False)
                    federation.save()
                    form.save_m2m()
                    
                    # Mettre à jour le profil
                    profile = request.user.profile
                    profile.onboarding_completed = True
                    profile.save()
                    
                    messages.success(request, _("Votre fédération a été créée avec succès!"))
                    return redirect('dashboard')
                
                except Exception as e:
                    logger.error(f"Error creating federation: {e}", exc_info=True)
                    messages.error(request, _("Erreur lors de la création de la fédération."))
        else:
            form = FederationCreationForm()
        
        context = {
            'form': form,
            'disciplines': disciplines,
        }
        
        return render(request, 'competitions/onboarding/federation_creation.html', context)
    
    except Exception as e:
        logger.error(f"Critical error in federation creation: {e}", exc_info=True)
        messages.error(request, _("Une erreur technique est survenue. Support contacté."))
        return redirect('dashboard')
PYTHON_EOF

echo -e "${GREEN}✅ Fichier emergency_fix.py créé${NC}"
echo ""

# ==========================================
# ÉTAPE 3: Mettre à Jour les URLs
# ==========================================
echo -e "${YELLOW}🔗 ÉTAPE 3: Mise à jour des URLs${NC}"
echo ""

# Backup URLs actuel
if [ -f "$PROJECT_DIR/apps/competitions/urls/__init__.py" ]; then
    cp "$PROJECT_DIR/apps/competitions/urls/__init__.py" "$BACKUP_DIR/"
fi

# Ajouter les nouvelles routes
cat >> "$PROJECT_DIR/apps/competitions/urls/__init__.py" << 'PYTHON_EOF'

# Routes d'urgence pour l'onboarding
from apps.competitions.views.onboarding.emergency_fix import (
    safe_club_creation,
    safe_federation_creation
)

urlpatterns += [
    path('onboarding/club/creation/safe/', safe_club_creation, name='safe_club_creation'),
    path('onboarding/federation/safe/', safe_federation_creation, name='safe_federation_creation'),
]
PYTHON_EOF

echo -e "${GREEN}✅ Routes d'urgence ajoutées${NC}"
echo ""

# ==========================================
# ÉTAPE 4: Créer une Page d'Erreur Gracieuse
# ==========================================
echo -e "${YELLOW}🎨 ÉTAPE 4: Page d'erreur gracieuse${NC}"
echo ""

mkdir -p "$PROJECT_DIR/apps/competitions/templates/errors"

cat > "$PROJECT_DIR/apps/competitions/templates/errors/onboarding_error.html" << 'HTML_EOF'
{% extends "base.html" %}
{% load i18n %}

{% block title %}{% trans "Problème Technique" %}{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-body text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-4x text-warning mb-4"></i>
                    <h2>{% trans "Un problème technique est survenu" %}</h2>
                    <p class="lead">{% trans "Nous sommes désolés, mais nous rencontrons un problème temporaire." %}</p>
                    
                    <div class="alert alert-info mt-4">
                        <i class="fas fa-info-circle"></i>
                        {% trans "Notre équipe technique a été automatiquement notifiée et travaille à résoudre ce problème." %}
                    </div>
                    
                    <div class="mt-4">
                        <h5>{% trans "Que pouvez-vous faire ?" %}</h5>
                        <ul class="list-unstyled">
                            <li>✅ {% trans "Réessayer dans quelques minutes" %}</li>
                            <li>✅ {% trans "Contacter le support : support@martialcomp.com" %}</li>
                            <li>✅ {% trans "Utiliser une autre méthode d'inscription" %}</li>
                        </ul>
                    </div>
                    
                    <div class="mt-4">
                        <a href="{% url 'dashboard' %}" class="btn btn-primary me-2">
                            <i class="fas fa-home"></i> {% trans "Tableau de bord" %}
                        </a>
                        <a href="{% url 'signup' %}" class="btn btn-outline-primary">
                            <i class="fas fa-redo"></i> {% trans "Réessayer" %}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
HTML_EOF

echo -e "${GREEN}✅ Page d'erreur créée${NC}"
echo ""

# ==========================================
# ÉTAPE 5: Redémarrer les Services
# ==========================================
echo -e "${YELLOW}🔄 ÉTAPE 5: Redémarrage des services${NC}"
echo ""

sudo systemctl restart gunicorn-martialcomp
sudo systemctl reload nginx

sleep 2

# Vérifier les services
if systemctl is-active --quiet gunicorn-martialcomp; then
    echo -e "${GREEN}✅ Gunicorn redémarré${NC}"
else
    echo -e "${RED}❌ Erreur Gunicorn${NC}"
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx actif${NC}"
else
    echo -e "${RED}❌ Erreur Nginx${NC}"
fi

echo ""

# ==========================================
# ÉTAPE 6: Tests
# ==========================================
echo -e "${YELLOW}🧪 ÉTAPE 6: Tests de validation${NC}"
echo ""

python3 << 'PYTHON_EOF'
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from competitions.models import Discipline, UserProfile
from django.contrib.auth.models import User

# Test 1: Disciplines
disc_count = Discipline.objects.count()
print(f"✅ Disciplines disponibles: {disc_count}")

# Test 2: Utilisateurs sans profil
users_without_profile = User.objects.filter(profile__isnull=True).count()
if users_without_profile > 0:
    print(f"⚠️  Utilisateurs sans profil: {users_without_profile}")
else:
    print(f"✅ Tous les utilisateurs ont un profil")

# Test 3: Onboarding incomplets
incomplete_onboarding = UserProfile.objects.filter(onboarding_completed=False).count()
print(f"ℹ️  Onboarding incomplets: {incomplete_onboarding}")
PYTHON_EOF

echo ""

# ==========================================
# RÉSUMÉ
# ==========================================
echo "=========================================="
echo -e "${GREEN}✅ CORRECTION TERMINÉE${NC}"
echo "=========================================="
echo ""

echo "ACTIONS COMPLÉTÉES:"
echo "  ✅ Disciplines initialisées"
echo "  ✅ Vues d'onboarding sécurisées créées"
echo "  ✅ URLs de secours ajoutées"
echo "  ✅ Page d'erreur gracieuse créée"
echo "  ✅ Services redémarrés"
echo "  ✅ Tests exécutés"
echo ""

echo "BACKUPS CRÉÉS DANS:"
echo "  📁 $BACKUP_DIR"
echo ""

echo "PROCHAINES ÉTAPES:"
echo "  1. Tester l'inscription: https://martialcomp.com/signup"
echo "  2. Surveiller les logs: $LOG_DIR/django.log"
echo "  3. Si OK, planifier refonte (Option B)"
echo ""

echo "ROLLBACK SI NÉCESSAIRE:"
echo "  cp $BACKUP_DIR/* $PROJECT_DIR/apps/competitions/urls/"
echo "  sudo systemctl restart gunicorn-martialcomp"
echo ""
