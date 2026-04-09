from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count

from ...models import Club, Competition

@login_required
def competition_management_pro_view(request):
    """
    Vue professionnelle NOUVELLE pour la gestion des compétitions.
    Interface moderne avec statistiques.
    """
    user = request.user
    
    # Récupérer l'organisation de l'utilisateur
    user_org = None
    club = getattr(request, 'club', None)
    
    if not club:
        club = Club.objects.filter(owner=user).first()
    
    if club and club.organization:
        user_org = club.organization
    elif hasattr(user, 'userprofile') and hasattr(user.userprofile, 'organization'):
        user_org = user.userprofile.organization
    elif hasattr(request, 'organization'):
        user_org = request.organization
    
    # Filtrer les compétitions selon les permissions
    if user_org:
        competitions = Competition.objects.filter(
            Q(organizing_organization=user_org) |
            Q(organizing_organization__isnull=True) |
            Q(status='published')
        ).distinct().order_by('-created_at')
    else:
        if user.is_superuser or user.is_staff:
            competitions = Competition.objects.all().order_by('-created_at')
        else:
            competitions = Competition.objects.filter(
                Q(organizing_organization__isnull=True) |
                Q(status='published')
            ).order_by('-created_at')
    
    # Annoter avec les compteurs
    competitions = competitions.annotate(
        registrations_count=Count('registrations', distinct=True),
        categories_count=Count('categories', distinct=True),
        types_count=Count('competition_types', distinct=True)
    )
    
    # Statistiques
    now = timezone.now()
    stats = {
        'total': competitions.count(),
        'draft': competitions.filter(status='draft').count(),
        'published': competitions.filter(status='published').count(),
        'completed': competitions.filter(status='completed').count(),
        'open_registrations': competitions.filter(
            registration_deadline__gte=now,
            status='published'
        ).count() if competitions.exists() else 0,
    }
    
    context = {
        'club': club,
        'competitions': competitions,
        'stats': stats,
        'user_org': user_org,
        'page_title': 'Gestion Professionnelle des Compétitions',
    }
    
    return render(request, 'competitions/club/competition_management_pro_new.html', context)
