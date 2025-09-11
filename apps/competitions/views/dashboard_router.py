from django.core.exceptions import PermissionDenied
"""
Routeur dashboard simple - utilise les templates existants
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def dashboard_router(request):
    """Route intelligemment vers le bon dashboard selon le rôle du profil utilisateur"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = request.user
    username = user.username
    
    # Debugging - vérifier plusieurs sources de rôle
    profile = getattr(user, 'profile', None)
    user_role = getattr(user, 'role', None)
    
    # Log pour debugging
    logger.info(f"🔍 Dashboard Router - User: {username}")
    logger.info(f"    Profile: {profile}")
    logger.info(f"    User.role: {user_role}")
    if profile:
        logger.info(f"    Profile.role: {getattr(profile, 'role', 'NO ROLE ATTR')}")
    
    print(f"🔍 Dashboard Router - User: {username}")
    print(f"    Profile: {profile}")
    print(f"    User.role: {user_role}")
    if profile:
        print(f"    Profile.role: {getattr(profile, 'role', 'NO ROLE ATTR')}")
    
    # Essayer d'abord le profil, puis user.role
    role = None
    if profile and hasattr(profile, 'role'):
        role = profile.role
        logger.info(f"    Utilise profile.role: {role}")
        print(f"    ✅ Utilise profile.role: {role}")
    elif user_role:
        role = user_role
        logger.info(f"    Utilise user.role: {role}")
        print(f"    ✅ Utilise user.role: {role}")
    else:
        logger.warning(f"    Aucun rôle trouvé - utilise spectator par défaut")
        print(f"    ⚠️ Aucun rôle trouvé - utilise spectator par défaut")
    
    if role:
        if role == 'coach':
            logger.info(f"    → Redirection vers coach dashboard")
            print(f"    → Redirection vers coach dashboard")
            return redirect('/competitions/dashboard/coach/')
        elif role == 'club_manager' or role == 'club_admin':  # Handle legacy 'club_admin' role
            return redirect('/competitions/dashboard/club/')
        elif role == 'participant':
            return redirect('/competitions/dashboard/participant/')
        elif role == 'federation_admin':
            return redirect('/competitions/dashboard/federations/')
        elif role == 'referee' or role == 'judge':  # Handle both referee and judge
            return redirect('/competitions/dashboard/referee/')
        elif role == 'pro':
            return redirect('/competitions/dashboard/pro/')
        elif role == 'manager':  # Legacy role, redirect to club dashboard
            return redirect('/competitions/dashboard/club/')
        elif role == 'spectator':
            return redirect('/competitions/dashboard/spectator/')
        elif role == 'external_organizer':
            return redirect('/competitions/dashboard/external-organizer/')
    
    # Fallback
    logger.warning(f"    → Fallback vers spectator dashboard")
    print(f"    → Fallback vers spectator dashboard")
    return redirect('/competitions/dashboard/spectator/')

@login_required
def club_dashboard_view(request):
    """Dashboard club"""
    context = {
        'user': request.user,
        'club_name': 'Dojo Sakura',
        'members_count': 45,
    }
    return render(request, 'competitions/dashboard/club.html', context)

@login_required  
def coach_dashboard_view(request):
    """Dashboard coach"""
    context = {'user': request.user}
    return render(request, 'competitions/dashboard/coach.html', context)

@login_required
def participant_dashboard_view(request):
    """Dashboard participant"""
    context = {'user': request.user}
    return render(request, 'competitions/dashboard/participant.html', context)

@login_required
def federation_dashboard_view(request):
    """Dashboard federation"""
    context = {'user': request.user}
    return render(request, 'competitions/dashboard/federation.html', context)
