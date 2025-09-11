# SUITE DES CORRECTIONS - ENVIRONNEMENT ACTIVÉ

## ✅ Environnement virtuel activé avec succès!
- Python: Version compatible
- Django: 4.2.21 ✅
- PostgreSQL: Connecté avec psycopg2 ✅

## 🚀 ÉTAPES SUIVANTES

### 1. Correction de la base de données

```bash
# Dans l'environnement virtuel activé
python manage.py shell
```

**Dans le shell Django, exécuter:**
```python
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
    print("Ajout de la colonne criterion_id...")
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

# Test de création/suppression d'utilisateur
from django.contrib.auth.models import User
import time

test_user = User.objects.create_user(
    username=f'test_final_{int(time.time())}',
    email='test@test.com',
    password='test123'
)
print("✅ Utilisateur créé")

test_user.delete()
print("✅ Utilisateur supprimé")

print("🎉 Base de données OK!")
exit()
```

### 2. Correction du fichier auth.py

```bash
# Sauvegarder l'ancien fichier
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

# Créer le fichier corrigé
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
from ..models.users import create_user_profile

@ensure_csrf_cookie
def login_view(request):
    """Vue de connexion utilisateur."""
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
    """Vue de déconnexion utilisateur."""
    logout(request)
    messages.success(request, _("Vous êtes maintenant déconnecté."))
    return redirect('welcome')

@transaction.atomic
def signup_view(request):
    """Vue d'inscription utilisateur."""
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
                logger.error(f"Erreur d'intégrité lors de la création du compte: {str(e)}")
                
            except Exception as e:
                messages.error(request, _("Une erreur inattendue est survenue. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la création du compte: {str(e)}")
        else:
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
    
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user, 
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
    
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
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
        else:
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

echo "✅ Fichier auth.py corrigé"
```

### 3. Redémarrage de Gunicorn

```bash
# Arrêter Gunicorn
pkill -f gunicorn

# Attendre un peu
sleep 2

# Redémarrer avec l'environnement virtuel
nohup python -m gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &
```

### 4. Vérification finale

```bash
# Vérifier que Gunicorn fonctionne
ps aux | grep gunicorn

# Tester l'application
curl -I http://127.0.0.1:8000/

# Vérifier les logs
tail -10 gunicorn.log
```

## 📋 COMMANDES COMPLÈTES EN SÉQUENCE

```bash
# 1. Base de données (copier-coller le code Python dans le shell)
python manage.py shell

# 2. Fichier auth.py (après exit du shell)
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s) && cat > competitions/views/auth.py << 'EOF'
[contenu du fichier]
EOF

# 3. Redémarrage
pkill -f gunicorn && sleep 2 && nohup python -m gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &

# 4. Test
curl -I https://martialcomp.com/signup/
```

---

**🎉 Avec l'environnement activé, toutes les corrections peuvent maintenant être appliquées !**