from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
# Essayez l'une de ces importations selon votre structure
from competitions.models.users import User  # Si vous avez un fichier users.py
# OU
from django.contrib.auth import get_user_model
User = get_user_model()  # Cette approche est plus sûre et universelle
from competitions.forms.auth import UserRegistrationForm  # Ajustez cette importation selon vos formulaires
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.urls import reverse

@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Vue pour l'inscription d'un nouvel utilisateur.
    Permet la création d'un compte utilisateur et redirige vers
    l'étape d'onboarding après l'inscription.
    """
    # Rediriger si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        messages.info(request, _("Vous êtes déjà connecté."))
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Créer l'utilisateur mais ne pas l'enregistrer tout de suite
            user = form.save(commit=False)
            
            # Définir le mot de passe hasché
            password = form.cleaned_data.get('password1')
            user.set_password(password)
            
            # Enregistrer l'utilisateur
            user.save()
            
            # Connexion automatique après l'inscription
            user = authenticate(username=user.username, password=password)
            if user is not None:
                login(request, user)
                
                # Message de succès
                messages.success(request, _("Votre compte a été créé avec succès ! Bienvenue !"))
                
                # Rediriger vers l'onboarding
                return redirect(reverse('onboarding:start'))
            else:
                messages.error(request, _("Une erreur est survenue lors de la connexion. Veuillez vous connecter manuellement."))
                return redirect('login')
    else:
        form = UserRegistrationForm()
    
    # Contexte pour le template
    context = {
        'form': form,
        'title': _("Inscription"),
        'submit_text': _("Créer un compte"),
    }
    
    return render(request, 'registration/signup.html', context)