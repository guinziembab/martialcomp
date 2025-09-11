# SCRIPT CORRIGÉ SIMPLE

## Supprimer l'ancien fichier et créer le nouveau

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs

# Supprimer l'ancien fichier défectueux
rm -f fix_onboarding_and_db_final.py

# Créer le script corrigé
cat > fix_onboarding_and_db_final.py << 'EOF'
#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def fix_database():
    print("🔧 Correction de la base de données...")
    
    with connection.cursor() as cursor:
        try:
            # Vérifier si la colonne criterion_id existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_technicalscoreresult' 
                AND column_name = 'criterion_id';
            """)
            
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE competitions_technicalscoreresult 
                    ADD COLUMN criterion_id INTEGER REFERENCES competitions_scoringcriterion(id) ON DELETE CASCADE;
                """)
                print("✅ Colonne criterion_id ajoutée")
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_technicalscoreresult_criterion 
                    ON competitions_technicalscoreresult(criterion_id);
                """)
                print("✅ Index créé")
            else:
                print("✅ Colonne criterion_id existe déjà")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
            return False

def fix_auth_file():
    print("📝 Correction du fichier auth.py...")
    
    auth_content = '''from django.shortcuts import render, redirect
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
from ..models.users import create_user_profile

@ensure_csrf_cookie
def login_view(request):
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')
            
            if next_url and not next_url.startswith('/'):
                next_url = None
                
            if not next_url:
                return redirect('dashboard:index')
            
            return redirect(next_url)
        else:
            messages.error(request, _("Identifiants invalides. Veuillez réessayer."))
    
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, _("Vous êtes maintenant déconnecté."))
    return redirect('welcome')

@transaction.atomic
def signup_view(request):
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                try:
                    profile = UserProfile.objects.get(user=user)
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(
                        user=user,
                        role='spectator',
                        onboarding_step='role_selection',
                        onboarding_completed=False
                    )
                
                login(request, user)
                
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                messages.info(request, _("Veuillez compléter votre profil pour accéder à toutes les fonctionnalités."))
                return redirect('dashboard:index')
                    
            except IntegrityError as e:
                messages.error(request, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur intégrité: {str(e)}")
                
            except Exception as e:
                messages.error(request, _("Une erreur inattendue est survenue. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur signup: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_view(request):
  from competitions.forms.profile_forms import UserProfileForm

  user = request.user

  try:
      profile = UserProfile.objects.get(user=user)
  except UserProfile.DoesNotExist:
      profile = UserProfile.objects.create(
          user=user,
          role='spectator',
          onboarding_step='role_selection',
          onboarding_completed=False
      )

  if request.method == 'POST':
      form = UserProfileForm(request.POST, request.FILES, user=request.user)
      if form.is_valid():
          form.save()
          messages.success(request, _("Votre profil a été mis à jour avec succès."))       
          return redirect('profile')
      else:
          messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
  else:
      form = UserProfileForm(user=request.user)

  context = {
      'user': user,
      'profile': profile,
      'form': form,
  }

  return render(request, 'registration/profile.html', context)

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _("Votre mot de passe a été mis à jour avec succès!"))
            return redirect('profile')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change.html', {
        'form': form
    })'''
    
    try:
        with open('/var/www/vhosts/martialcomp.com/httpdocs/competitions/views/auth.py', 'w') as f:
            f.write(auth_content)
        print("✅ Fichier auth.py corrigé")
        return True
    except Exception as e:
        print(f"❌ Erreur fichier: {e}")
        return False

def test_user_creation():
    print("🎯 Test de création d'utilisateur...")
    try:
        from django.contrib.auth.models import User
        import time
        
        test_user = User.objects.create_user(
            username=f'test_{int(time.time())}',
            email='test@test.com',
            password='test123'
        )
        print("✅ Utilisateur créé")
        
        test_user.delete()
        print("✅ Utilisateur supprimé")
        return True
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CORRECTION FINALE...")
    print("="*50)
    
    db_ok = fix_database()
    auth_ok = fix_auth_file()
    test_ok = test_user_creation()
    
    if db_ok and auth_ok and test_ok:
        print("\n🎉 TOUTES LES CORRECTIONS RÉUSSIES !")
        print("="*50)
        print("✅ Base de données corrigée")
        print("✅ Fichier auth.py corrigé")
        print("✅ Tests passés")
        print("="*50)
        print("🔄 REDÉMARREZ GUNICORN:")
        print("pkill -f gunicorn")
        cmd = "nohup gunicorn --bind 127.0.0.1:8000 --workers 3 "
        cmd += "--timeout 120 --chdir /var/www/vhosts/martialcomp.com/httpdocs "
        cmd += "config.wsgi:application > gunicorn.log 2>&1 &"
        print(cmd)
        print("="*50)
        print("🌐 TESTEZ: https://martialcomp.com/signup/")
    else:
        print("❌ Certaines corrections ont échoué")
EOF

# Exécuter le script
python fix_onboarding_and_db_final.py
```