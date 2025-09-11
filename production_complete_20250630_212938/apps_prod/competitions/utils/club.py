# Contenu du nouveau fichier competitions/utils/club.py
from competitions.models import Club

def get_user_club(request):
    """
    Récupère le club associé à l'utilisateur de manière uniforme.
    Essaie différentes méthodes pour trouver le club.
    """
    # Si le club est déjà dans la requête (via le décorateur)
    if hasattr(request, 'club') and request.club:
        return request.club
    
    # Si l'utilisateur a un attribut club
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Si l'utilisateur est propriétaire d'un club
    club = Club.objects.filter(owner=request.user).first()
    if club:
        return club
    
    # Si l'utilisateur est administrateur d'un club
    if hasattr(request.user, 'club_admin_roles'):
        club_admin = request.user.club_admin_roles.first()
        if club_admin:
            return club_admin.club
    
    return None