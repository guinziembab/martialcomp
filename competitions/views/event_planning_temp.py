# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

@login_required
def poll_list_temp(request):
    """
    Vue temporaire pour la liste des sondages, en attendant que la migration
    pour créer la table competitions_eventpoll soit appliquée.
    """
    context = {
        'created_polls': [],
        'responded_polls': [],
        'organization_polls': [],
        'event_polls': [],
        'maintenance_mode': True,
        'message': _("Le module de sondages est en cours de maintenance. Veuillez réessayer plus tard.")
    }
    
    return render(request, 'competitions/event_planning/poll_list_temp.html', context)

@login_required
def create_poll_temp(request, event_id=None):
    """
    Vue temporaire pour la création de sondages, en attendant que la migration
    pour créer la table competitions_eventpoll soit appliquée.
    """
    context = {
        'maintenance_mode': True,
        'message': _("Le module de création de sondages est en cours de maintenance. Veuillez réessayer plus tard.")
    }
    
    return render(request, 'competitions/event_planning/poll_list_temp.html', context)