#!/bin/bash
# SCRIPT DE DÉPLOIEMENT PRODUCTION - MartialComp
# À exécuter sur le serveur de production

echo "🚀 DÉPLOIEMENT DES CORRECTIONS FINALES..."
echo "========================================"

# 1. Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# 2. Sauvegarder l'ancien fichier auth.py
echo "💾 Sauvegarde du fichier auth.py actuel..."
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

# 3. Créer le fichier auth.py corrigé
echo "📝 Création du fichier auth.py corrigé..."
cat > competitions/views/auth.py << 'EOF'
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect
from ..auth_forms import SignUpForm
from ..models import UserProfile
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
# Importer correctement le signal
from ..models.users import create_user_profile

@ensure_csrf_cookie
def login_view(request):
    """Vue de connexion utilisateur."""
    # Rediriger si déjà connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Tentative d'authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Récupérer l'URL de redirection
            next_url = request.POST.get('next')
            
            # Vérifier si next_url est sécurisé (non vide et interne au site)
            if next_url and not next_url.startswith('/'):
                next_url = None
                
            # Si aucune URL next ou URL invalide, rediriger vers le dashboard
            if not next_url:
                # Utiliser le système de nommage d'URL de Django au lieu d'un chemin en dur
                return redirect('dashboard:index')
            
            return redirect(next_url)
        else:
            messages.error(request, _("Identifiants invalides. Veuillez réessayer."))
    
    return render(request, 'registration/login.html')

def logout_view(request):
    """Vue de déconnexion utilisateur."""
    logout(request)
    messages.success(request, _("Vous êtes maintenant déconnecté."))
    return redirect('welcome')

@transaction.atomic
def signup_view(request):
    """Vue d'inscription utilisateur."""
    # Rediriger si déjà connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Créer l'utilisateur avec les données du formulaire
                user = form.save()
                
                # S'assurer que l'utilisateur a un profil
                try:
                    # Vérifier si un profil existe déjà
                    profile = UserProfile.objects.get(user=user)
                    
                    # Si le profil existe, mettre à jour ses attributs
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                except UserProfile.DoesNotExist:
                    # Créer un nouveau profil si nécessaire
                    profile = UserProfile.objects.create(
                        user=user,
                        role='spectator',
                        onboarding_step='role_selection',
                        onboarding_completed=False
                    )
                
                # Connecter l'utilisateur
                login(request, user)
                
                # Message de bienvenue
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # CORRECTION PRINCIPALE: Rediriger vers le dashboard avec un message
                messages.info(request, _("Veuillez compléter votre profil pour accéder à toutes les fonctionnalités."))
                return redirect('dashboard:index')
                    
            except IntegrityError as e:
                # Gérer spécifiquement l'erreur d'intégrité
                messages.error(request, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur d'intégrité lors de la création du compte: {str(e)}")
                
            except Exception as e:
                # Gérer les autres exceptions
                messages.error(request, _("Une erreur inattendue est survenue. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la création du compte: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_view(request):
    """Vue de profil utilisateur avec gestion de la modification."""
    user = request.user
    
    # S'assurer que l'utilisateur a un profil
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user, 
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
    
    # Importer le formulaire de profil
    from ..forms.profile_forms import UserProfileForm
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Votre profil a été mis à jour avec succès !"))
                return redirect('profile')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue lors de la mise à jour de votre profil."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = UserProfileForm(instance=profile, user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'form': form,
    }
    
    return render(request, 'registration/profile.html', context)

@login_required
def password_change_view(request):
    """Vue de changement de mot de passe."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Importante pour maintenir la session utilisateur après changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, _("Votre mot de passe a été mis à jour avec succès!"))
            return redirect('profile')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change.html', {
        'form': form
    })
EOF

# 4. Correction de la base de données (PostgreSQL)
echo "🔧 Correction de la base de données..."
python manage.py shell << 'PYEOF'
from django.db import connection

cursor = connection.cursor()

# Vérifier si la colonne criterion_id existe
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'competitions_technicalscoreresult' 
    AND column_name = 'criterion_id';
""")

if not cursor.fetchone():
    print("📋 Ajout de la colonne criterion_id...")
    cursor.execute("""
        ALTER TABLE competitions_technicalscoreresult 
        ADD COLUMN criterion_id INTEGER REFERENCES competitions_scoringcriterion(id) ON DELETE CASCADE;
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_technicalscoreresult_criterion 
        ON competitions_technicalscoreresult(criterion_id);
    """)
    print("✅ Colonne criterion_id ajoutée")
else:
    print("✅ Colonne criterion_id existe déjà")

print("✅ Base de données corrigée")
PYEOF

# 5. Redémarrer Gunicorn
echo "🔄 Redémarrage de Gunicorn..."
pkill -f gunicorn

# Attendre un peu que les processus se terminent
sleep 2

# Redémarrer Gunicorn
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &

# 6. Vérification
echo "🔍 Vérification du déploiement..."
sleep 3

# Vérifier que Gunicorn fonctionne
if ps aux | grep -q "[g]unicorn"; then
    echo "✅ Gunicorn démarré avec succès"
else
    echo "❌ Erreur: Gunicorn n'a pas démarré"
    echo "📋 Logs de Gunicorn:"
    tail -20 gunicorn.log
    exit 1
fi

# 7. Test final
echo "🌐 Test final..."
curl -s -I http://127.0.0.1:8000/ | head -1

echo ""
echo "========================================"
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "========================================"
echo "✅ Fichier auth.py corrigé"
echo "✅ Base de données corrigée" 
echo "✅ Gunicorn redémarré"
echo "========================================"
echo "🌐 TESTEZ: https://martialcomp.com/signup/"
echo "👉 Le processus d'inscription devrait maintenant fonctionner !"
echo "========================================"
