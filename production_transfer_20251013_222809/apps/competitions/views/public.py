# competitions/views/public.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from ..models import Competition, CompetitionRegistration, CompetitionCategory
from ..forms.competitions import CompetitionRegistrationForm


def public_competition_registration(request, competition_id):
    """
    Page publique d'inscription à une compétition.
    Accessible via QR code ou lien direct.
    """
    try:
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Version simplifiée - toujours afficher la page
        context = {
            'competition': competition,
            'categories': [],
            'total_registrations': 0,
            'is_registration_open': True,
        }
        
        return render(request, 'competitions/public/registration.html', context)
    except Exception as e:
        # En cas d'erreur, afficher une page simple
        return render(request, 'competitions/public/registration_closed.html', {
            'competition': {'title': 'Compétition', 'id': competition_id},
            'registration_closed': True,
            'message': f"Erreur: {str(e)}"
        })


def public_competition_detail(request, competition_id):
    """
    Page publique de détails d'une compétition.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si la compétition est publiée
    if competition.status not in ['published', 'registration_open', 'ongoing', 'completed']:
        messages.error(request, _("Cette compétition n'est pas accessible publiquement."))
        return redirect('competitions:list')
    
    # Récupérer les catégories
    categories = CompetitionCategory.objects.filter(competition=competition).order_by('name')
    
    # Statistiques
    total_registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True
    ).count()
    
    # Vérifier si les inscriptions sont ouvertes
    today = timezone.now().date()
    is_registration_open = (
        competition.registration_deadline and 
        competition.registration_deadline >= today and
        competition.status in ['published', 'registration_open']
    )
    
    context = {
        'competition': competition,
        'categories': categories,
        'total_registrations': total_registrations,
        'is_registration_open': is_registration_open,
    }
    
    return render(request, 'competitions/public/detail.html', context)