from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def poll_list_simple(request):
    """
    Vue simplifiée pour la liste des sondages, qui fonctionne mÃªme sans les modèles complets.
    """
    try:
        # Essayer d'importer et d'utiliser les modèles d'événements
        from apps.competitions.models.event_planning import EventPoll
        from apps.organizations.models import Organization, OrganizationMember
        
        # Sondages créés par l'utilisateur
        created_polls = EventPoll.objects.filter(
            created_by=request.user
        ).select_related('organization', 'event').order_by('-created_at')[:10]
        
        # Sondages actifs de ses organisations (clubs, fédérations)
        try:
            user_organizations = Organization.objects.filter(
                members__user=request.user
            ).values_list('id', flat=True)
            
            organization_polls = EventPoll.objects.filter(
                organization_id__in=user_organizations,
                status='active',
            ).select_related('organization', 'event').order_by('-created_at')[:10]
        except:
            organization_polls = []
        
        # Si tout fonctionne, utiliser les vraies données
        context = {
            'created_polls': created_polls,
            'responded_polls': [],
            'organization_polls': organization_polls,
            'event_polls': [],
            'polls_available': True,
            'total_polls': created_polls.count() + len(organization_polls),
        }
        
    except Exception as e:
        # Si les modèles n'existent pas encore, afficher une interface de démo
        messages.info(request, _("Les modèles de sondages seront bientÃ´t disponibles. Voici un aperçu de l'interface."))
        
        # Données de démonstration
        context = {
            'created_polls': [],
            'responded_polls': [],
            'organization_polls': [],
            'event_polls': [],
            'polls_available': False,
            'total_polls': 0,
            'demo_mode': True,
            'demo_polls': [
                {
                    'title': _('Sondage pour le tournoi de printemps'),
                    'description': _('Déterminer la meilleure date pour le tournoi'),
                    'status': 'active',
                    'options_count': 3,
                    'responses_count': 12,
                    'created_at': '2025-01-15',
                },
                {
                    'title': _('Disponibilités pour la formation arbitres'),
                    'description': _('Planifier la formation des nouveaux arbitres'),
                    'status': 'active', 
                    'options_count': 4,
                    'responses_count': 8,
                    'created_at': '2025-01-10',
                },
                {
                    'title': _('Choix du lieu pour la compétition régionale'),
                    'description': _('Sélectionner le meilleur lieu pour la compétition'),
                    'status': 'closed',
                    'options_count': 2,
                    'responses_count': 25,
                    'created_at': '2025-01-05',
                },
            ]
        }
    
    return render(request, 'competitions/event_planning/poll_list_simple.html', context)

@login_required  
def create_poll_simple(request):
    """
    Vue simplifiée pour la création de sondages.
    """
    try:
        # Essayer d'utiliser la vraie vue de création
        from apps.competitions.views.event_planning import create_poll
        return create_poll(request)
    except Exception as e:
        # Si les modèles n'existent pas, afficher un formulaire de démo
        messages.info(request, _("La création de sondages sera bientÃ´t disponible."))
        
        context = {
            'demo_mode': True,
            'form_fields': [
                {'name': 'title', 'label': _('Titre du sondage'), 'type': 'text', 'required': True},
                {'name': 'description', 'label': _('Description'), 'type': 'textarea', 'required': False},
                {'name': 'response_type', 'label': _('Type de réponse'), 'type': 'select', 'required': True},
                {'name': 'deadline', 'label': _('Date limite'), 'type': 'date', 'required': False},
            ],
            'response_types': [
                ('yes_no', _('Oui/Non')),
                ('yes_maybe_no', _('Oui/Peut-Ãªtre/Non')),
                ('availability', _('Disponibilité détaillée')),
            ]
        }
        
        return render(request, 'competitions/event_planning/create_poll_simple.html', context)

