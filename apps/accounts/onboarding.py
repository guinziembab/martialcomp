from .models import OrganisateurNonMembre
from apps.organizations.models import Organization
from django.contrib.auth.models import User

def onboard_organisateur_non_membre(user_data, org_data):
    # Création de l'utilisateur
    user = User.objects.create_user(**user_data)
    # Création de l'organisation
    org = Organization.objects.create(**org_data)
    # Création du profil organisateur non-membre
    profil = OrganisateurNonMembre.objects.create(user=user, organization=org)
    return profil 

