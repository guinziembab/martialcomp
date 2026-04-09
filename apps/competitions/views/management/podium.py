# -*- coding: utf-8 -*-
"""
Vues pour la gestion du podium et l'ajout manuel de participants.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError

from apps.competitions.models import (
    Competition,
    CompetitionCategory,
    Practitioner,
    PodiumEntry,
    CompetitionRegistration,
)
from apps.competitions.utils.decorators import (
    competition_management_permission_required
)


def _enrich_podium_with_teams(podium, category):
    """Enrichit les entrées du podium avec les informations d'équipe."""
    from apps.competitions.models.combat import MembreEquipe
    for position_key in ['gold', 'silver', 'bronze']:
        for entry in podium.get(position_key, []):
            practitioner = entry.get('practitioner')
            if practitioner:
                membership = MembreEquipe.objects.filter(
                    pratiquant=practitioner,
                    equipe__category=category,
                    equipe__is_active=True,
                ).select_related('equipe', 'equipe__club').first()
                if membership:
                    team = membership.equipe
                    entry['is_team'] = True
                    entry['team_name'] = team.nom
                    entry['team_club'] = team.club.name if team.club else ''
                    members = list(
                        team.memberships.filter(est_remplacant=False)
                        .select_related('pratiquant')
                        .order_by('ordre')
                    )
                    entry['team_members'] = members
                else:
                    entry['is_team'] = False
                    entry['team_members'] = []
            else:
                entry['is_team'] = False
                entry['team_members'] = []


@login_required
@competition_management_permission_required
def podium_management(request, competition_id, category_id):
    """
    Vue principale de gestion du podium pour une catégorie.
    Affiche le podium actuel et permet d'ajouter/supprimer des participants.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)

    # Détecter si la catégorie est en mode équipe
    is_team_mode = False
    try:
        if category.competition_type and category.competition_type.team_based:
            is_team_mode = True
    except Exception:
        pass

    # Récupérer le podium complet (calculé + manuel)
    podium = PodiumEntry.get_podium_for_category(category)

    # Enrichir avec les données d'équipe si mode équipe
    if is_team_mode:
        _enrich_podium_with_teams(podium, category)

    # Récupérer les pratiquants inscrits dans la compétition (pour le sélecteur)
    # Inclut tous les inscrits (pas seulement cette catégorie) pour les ajouts honorifiques
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
    ).select_related('practitioner', 'practitioner__organization')

    # Exclure les pratiquants déjà au podium pour cette catégorie
    podium_practitioner_ids = set(PodiumEntry.objects.filter(
        category=category
    ).values_list('practitioner_id', flat=True))

    seen_ids = set()
    available_practitioners = []
    for reg in registrations:
        pid = reg.practitioner_id
        if pid not in podium_practitioner_ids and pid not in seen_ids:
            available_practitioners.append(reg.practitioner)
            seen_ids.add(pid)

    # Entrées manuelles actuelles
    manual_entries = PodiumEntry.objects.filter(
        category=category,
        is_manual=True
    ).select_related('practitioner').order_by('position')

    context = {
        'competition': competition,
        'category': category,
        'podium': podium,
        'manual_entries': manual_entries,
        'available_practitioners': available_practitioners,
        'position_choices': PodiumEntry.POSITION_CHOICES,
        'is_team_mode': is_team_mode,
    }

    return render(request, 'competitions/management/podium_management.html', context)


@login_required
@require_POST
@competition_management_permission_required
def add_podium_entry(request, competition_id, category_id):
    """
    Ajoute un participant au podium manuellement.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)

    practitioner_id = request.POST.get('practitioner_id')
    position = request.POST.get('position')
    honorary_title = request.POST.get('honorary_title', '').strip()
    show_title = request.POST.get('show_title') == 'on'
    internal_note = request.POST.get('internal_note', '').strip()

    if not practitioner_id or not position:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': _("Veuillez sélectionner un pratiquant et une position.")
            })
        messages.error(request, _("Veuillez sélectionner un pratiquant et une position."))
        return redirect('competitions:management:podium_management', competition_id=competition_id, category_id=category_id)

    try:
        practitioner = get_object_or_404(Practitioner, pk=practitioner_id)
        position = int(position)

        if position not in [1, 2, 3]:
            raise ValueError("Position invalide")

        # Créer l'entrée au podium
        entry = PodiumEntry.objects.create(
            category=category,
            practitioner=practitioner,
            position=position,
            is_manual=True,
            honorary_title=honorary_title,
            show_title=show_title,
            internal_note=internal_note,
            added_by=request.user,
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _("%(name)s ajouté(e) au podium en position %(position)s.") % {
                    'name': practitioner.full_name,
                    'position': entry.position_label
                },
                'entry': {
                    'id': entry.id,
                    'practitioner_name': practitioner.full_name,
                    'position': entry.position,
                    'position_label': entry.position_label,
                    'medal_icon': entry.medal_icon,
                }
            })

        messages.success(
            request,
            _("%(name)s ajouté(e) au podium en position %(position)s.") % {
                'name': practitioner.full_name,
                'position': entry.position_label
            }
        )

    except IntegrityError:
        error_msg = _("Ce pratiquant est déjà au podium pour cette catégorie.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)

    except Exception as e:
        error_msg = _("Erreur lors de l'ajout au podium: %(error)s") % {'error': str(e)}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)

    return redirect(
        'competitions:management:podium_management',
        competition_id=competition_id,
        category_id=category_id
    )


@login_required
@require_POST
@competition_management_permission_required
def remove_podium_entry(request, competition_id, category_id, entry_id):
    """
    Supprime une entrée manuelle du podium.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    entry = get_object_or_404(PodiumEntry, pk=entry_id, category=category, is_manual=True)

    practitioner_name = entry.practitioner.full_name
    entry.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': _("%(name)s retiré(e) du podium.") % {'name': practitioner_name}
        })

    messages.success(
        request,
        _("%(name)s retiré(e) du podium.") % {'name': practitioner_name}
    )
    return redirect(
        'competitions:management:podium_management',
        competition_id=competition_id,
        category_id=category_id
    )


@login_required
@require_POST
@competition_management_permission_required
def update_podium_entry(request, competition_id, category_id, entry_id):
    """
    Met à jour une entrée du podium (position, titre, etc.).
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    entry = get_object_or_404(PodiumEntry, pk=entry_id, category=category)

    position = request.POST.get('position')
    honorary_title = request.POST.get('honorary_title', '').strip()
    show_title = request.POST.get('show_title') == 'on'
    internal_note = request.POST.get('internal_note', '').strip()

    try:
        if position:
            position = int(position)
            if position in [1, 2, 3]:
                entry.position = position

        entry.honorary_title = honorary_title
        entry.show_title = show_title
        entry.internal_note = internal_note
        entry.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _("Entrée mise à jour."),
                'entry': {
                    'id': entry.id,
                    'position': entry.position,
                    'position_label': entry.position_label,
                    'medal_icon': entry.medal_icon,
                }
            })

        messages.success(request, _("Entrée mise à jour."))

    except Exception as e:
        error_msg = _("Erreur lors de la mise à jour: %(error)s") % {'error': str(e)}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)

    return redirect(
        'competitions:management:podium_management',
        competition_id=competition_id,
        category_id=category_id
    )


@login_required
@require_GET
def podium_display(request, competition_id, category_id):
    """
    Affichage public du podium pour une catégorie.
    Le 1er est au centre, 2ème à gauche, 3ème à droite.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)

    # Détecter mode équipe
    is_team_mode = False
    try:
        if category.competition_type and category.competition_type.team_based:
            is_team_mode = True
    except Exception:
        pass

    # Récupérer le podium complet
    podium = PodiumEntry.get_podium_for_category(category)

    # Enrichir avec les données d'équipe si mode équipe
    if is_team_mode:
        _enrich_podium_with_teams(podium, category)

    context = {
        'competition': competition,
        'category': category,
        'podium': podium,
        'gold': podium['gold'],
        'silver': podium['silver'],
        'bronze': podium['bronze'],
        'is_team_mode': is_team_mode,
    }

    return render(request, 'competitions/podium/podium_display.html', context)


@login_required
@require_GET
def podium_ceremony(request, competition_id, category_id):
    """
    Vue cérémonie du podium (plein écran pour affichage sur écran).
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)

    # Détecter mode équipe
    is_team_mode = False
    try:
        if category.competition_type and category.competition_type.team_based:
            is_team_mode = True
    except Exception:
        pass

    podium = PodiumEntry.get_podium_for_category(category)

    # Enrichir avec les données d'équipe si mode équipe
    if is_team_mode:
        _enrich_podium_with_teams(podium, category)

    context = {
        'competition': competition,
        'category': category,
        'podium': podium,
        'gold': podium['gold'],
        'silver': podium['silver'],
        'bronze': podium['bronze'],
        'fullscreen': True,
        'is_team_mode': is_team_mode,
    }

    return render(request, 'competitions/podium/podium_ceremony.html', context)


@login_required
@require_GET
@competition_management_permission_required
def get_available_practitioners(request, competition_id, category_id):
    """
    API: Retourne les pratiquants disponibles pour ajout au podium.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)

    # Récupérer les inscriptions (toute la compétition pour ajouts honorifiques)
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
    ).select_related('practitioner', 'practitioner__organization')

    # Exclure ceux déjà au podium
    podium_ids = set(PodiumEntry.objects.filter(category=category).values_list('practitioner_id', flat=True))

    seen_ids = set()
    practitioners = []
    for reg in registrations:
        pid = reg.practitioner_id
        if pid not in podium_ids and pid not in seen_ids:
            practitioners.append({
                'id': reg.practitioner.id,
                'name': reg.practitioner.full_name,
                'club': reg.practitioner.organization.name if reg.practitioner.organization else '',
            })
            seen_ids.add(pid)

    return JsonResponse({'practitioners': practitioners})
