"""
Vue simplifiée pour la gestion des compétitions v2
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from ..models import Competition


@login_required
def competition_management_v2(request, competition_id):
    """
    Vue principale pour la gestion d'une compétition.
    Template simplifié et fonctionnel.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # TODO: Vérifier les permissions quand created_by sera disponible
    # Pour l'instant, on autorise tous les utilisateurs connectés
    
    context = {
        'competition': competition,
    }
    
    return render(request, 'competitions/club/competition_management_v3.html', context)