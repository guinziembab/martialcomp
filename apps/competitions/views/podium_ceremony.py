# -*- coding: utf-8 -*-
"""
Vues pour la cérémonie de remise des récompenses (podium).
Affichage cérémoniel avec révélation progressive et animations.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from apps.competitions.models import Competition, CompetitionCategory
from apps.competitions.services.podium_display_service import PodiumDisplayService
from apps.competitions.services.podium_order_service import PodiumOrderService


@login_required
def podium_ceremony(request, competition_id):
    """
    Vue principale de la cérémonie de remise des récompenses.
    Affiche le podium avec navigation entre catégories.

    Args:
        competition_id: ID de la compétition

    Template: competitions/combat/podium_ceremony.html
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Filtre par type de competition (optionnel)
    comp_type_filter = request.GET.get('type', '')

    # Récupérer l'index de la catégorie (0 par défaut)
    category_index = request.GET.get('category', 0)
    try:
        category_index = int(category_index)
    except (ValueError, TypeError):
        category_index = 0

    # Récupérer toutes les categories ordonnees
    ordered_categories = PodiumOrderService.get_all_categories_for_podium(
        competition,
        include_pending=True
    )

    # Filtrer par type si demandé
    if comp_type_filter and ordered_categories:
        filtered = []
        new_idx = 0
        for cat_data in ordered_categories:
            category = cat_data['category']
            comp_type = category.competition_type
            type_name = comp_type.name if comp_type else ''
            if type_name == comp_type_filter:
                filtered.append({**cat_data, 'index': new_idx})
                new_idx += 1
        ordered_categories = filtered

    # Exclure les catégories sans résultats
    if ordered_categories:
        with_results = []
        new_idx = 0
        for cat_data in ordered_categories:
            podium = PodiumDisplayService.get_category_podium_data(cat_data['category'])
            p = podium.get('podium', {})
            if p.get('gold') or p.get('silver') or p.get('bronze'):
                with_results.append({**cat_data, 'index': new_idx})
                new_idx += 1
        ordered_categories = with_results

    if not ordered_categories:
        return render(request, 'competitions/combat/podium_ceremony.html', {
            'competition': competition,
            'no_categories': True,
            'message': _("Aucune catégorie n'est prête pour la cérémonie."),
            'comp_type_filter': comp_type_filter,
        })

    # S'assurer que l'index est valide
    if category_index < 0:
        category_index = 0
    elif category_index >= len(ordered_categories):
        category_index = len(ordered_categories) - 1

    cat_data = ordered_categories[category_index]
    category = cat_data['category']
    podium_data = PodiumDisplayService.get_category_podium_data(category)

    category_data = {
        'index': category_index,
        'total': len(ordered_categories),
        'is_first': category_index == 0,
        'is_last': category_index == len(ordered_categories) - 1,
        'prev_index': category_index - 1 if category_index > 0 else None,
        'next_index': category_index + 1 if category_index < len(ordered_categories) - 1 else None,
        **podium_data,
    }

    # Préparer les étapes de révélation
    reveal_steps = PodiumDisplayService.format_podium_for_reveal(
        category_data['podium']
    )

    # Mode plein écran
    fullscreen = request.GET.get('fullscreen', 'false') == 'true'

    context = {
        'competition': competition,
        'category_data': category_data,
        'reveal_steps': reveal_steps,
        'current_index': category_data['index'],
        'total_categories': category_data['total'],
        'is_first': category_data['is_first'],
        'is_last': category_data['is_last'],
        'prev_index': category_data['prev_index'],
        'next_index': category_data['next_index'],
        'fullscreen': fullscreen,
        'comp_type_filter': comp_type_filter,
    }

    return render(request, 'competitions/combat/podium_ceremony.html', context)


@login_required
def podium_display(request, competition_id):
    """
    Écran d'affichage spectateurs (vidéoprojecteur/TV).
    Synchronisé avec l'écran de pilotage via BroadcastChannel.
    Pas de boutons, pas de navigation visible — uniquement le podium.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Banner: competition logo or organization banner
    banner_url = ''
    if competition.logo:
        banner_url = competition.logo.url
    elif competition.organizing_organization and competition.organizing_organization.banner:
        banner_url = competition.organizing_organization.banner.url

    context = {
        'competition': competition,
        'competition_id': competition.id,
        'banner_url': banner_url,
    }

    return render(request, 'competitions/combat/podium_display.html', context)


@login_required
@require_GET
def podium_category_api(request, competition_id, category_index):
    """
    API pour récupérer les données d'une catégorie spécifique (AJAX).

    Args:
        competition_id: ID de la compétition
        category_index: Index de la catégorie

    Returns:
        JsonResponse avec les données du podium
    """
    competition = get_object_or_404(Competition, id=competition_id)
    comp_type_filter = request.GET.get('type', '')

    category_data = PodiumDisplayService.get_category_for_ceremony(
        competition,
        category_index,
        comp_type_filter=comp_type_filter
    )

    if not category_data:
        return JsonResponse({
            'success': False,
            'error': _("Catégorie non trouvée"),
        }, status=404)

    reveal_steps = PodiumDisplayService.format_podium_for_reveal(
        category_data['podium']
    )

    # Convertir les données pour JSON
    response_data = {
        'success': True,
        'category': {
            'id': category_data['category_id'],
            'name': category_data['category_name'],
            'competition_type': category_data['competition_type'],
            'gender': category_data['gender'],
            'gender_display': str(category_data['gender_display']),
            'age_group': category_data['age_group'],
            'is_combat': category_data['is_combat'],
            'combat_mode': category_data['combat_mode'],
        },
        'navigation': {
            'index': category_data['index'],
            'total': category_data['total'],
            'is_first': category_data['is_first'],
            'is_last': category_data['is_last'],
            'prev_index': category_data['prev_index'],
            'next_index': category_data['next_index'],
        },
        'reveal_steps': _serialize_reveal_steps(reveal_steps),
    }

    return JsonResponse(response_data)


@login_required
@require_GET
def podium_all_categories_api(request, competition_id):
    """
    API pour récupérer la liste de toutes les catégories ordonnées.

    Args:
        competition_id: ID de la compétition

    Returns:
        JsonResponse avec la liste des catégories
    """
    competition = get_object_or_404(Competition, id=competition_id)

    ordered_categories = PodiumOrderService.get_all_categories_for_podium(
        competition,
        include_pending=True
    )

    categories_list = []
    for cat_data in ordered_categories:
        categories_list.append({
            'index': cat_data['index'],
            'id': cat_data['category'].id,
            'name': cat_data['category'].name,
            'age_group': cat_data['age_group'],
            'age_group_display': str(cat_data['age_group_display']),
            'gender': cat_data['gender'],
            'gender_display': str(cat_data['gender_display']),
            'is_completed': cat_data['category'].is_completed,
        })

    return JsonResponse({
        'success': True,
        'competition_id': competition.id,
        'competition_title': competition.title,
        'total': len(categories_list),
        'categories': categories_list,
    })


@login_required
def podium_overview(request, competition_id):
    """
    Vue de synthèse montrant tous les podiums de la compétition.
    Utile pour une vue d'ensemble ou pour impression.

    Args:
        competition_id: ID de la compétition

    Template: competitions/combat/podium_overview.html
    """
    competition = get_object_or_404(Competition, id=competition_id)

    ceremony_data = PodiumDisplayService.get_competition_ceremony_data(
        competition,
        include_pending=True
    )

    # Extraire les types de competition distincts
    competition_types = sorted(set(
        cat['competition_type'] for cat in ceremony_data['categories']
        if cat.get('competition_type')
    ))

    # Filtrer par type si demande
    selected_type = request.GET.get('type', '')
    filtered_categories = ceremony_data['categories']
    if selected_type:
        filtered_categories = [
            cat for cat in ceremony_data['categories']
            if cat.get('competition_type') == selected_type
        ]

    context = {
        'competition': competition,
        'ceremony_data': ceremony_data,
        'categories': filtered_categories,
        'total_categories': len(filtered_categories),
        'competition_types': competition_types,
        'selected_type': selected_type,
    }

    return render(request, 'competitions/combat/podium_overview.html', context)


def _serialize_reveal_steps(reveal_steps):
    """
    Sérialise les étapes de révélation pour JSON.

    Args:
        reveal_steps: Liste des étapes

    Returns:
        list: Données sérialisées
    """
    serialized = []
    for step in reveal_steps:
        step_data = {
            'step': step['step'],
            'position': step['position'],
            'medal': step['medal'],
            'medal_emoji': step['medal_emoji'],
            'medal_color': step['medal_color'],
            'announcement': str(step['announcement']),
            'trigger_celebration': step.get('trigger_celebration', False),
            'winners': [],
        }

        for winner in step['winners']:
            winner_data = {
                'entity_id': winner.get('entity_id'),
                'entity_name': winner.get('entity_name', ''),
                'club_name': winner.get('club_name', ''),
                'is_tie': winner.get('is_tie', False),
            }

            # Ajouter les champs optionnels
            if winner.get('photo_url'):
                winner_data['photo_url'] = winner['photo_url']
            if winner.get('country_code'):
                winner_data['country_code'] = winner['country_code']
            if winner.get('logo_url'):
                winner_data['logo_url'] = winner['logo_url']
            if winner.get('grade'):
                winner_data['grade'] = winner['grade']
            if winner.get('type') == 'team' and winner.get('members'):
                winner_data['members'] = winner['members']

            # Stats pour combats
            if 'wins' in winner:
                winner_data['stats'] = {
                    'wins': winner['wins'],
                    'losses': winner['losses'],
                    'draws': winner['draws'],
                    'total_score': winner['total_score'],
                }

            # Score pour techniques
            if 'score' in winner:
                winner_data['score'] = winner['score']

            step_data['winners'].append(winner_data)

        serialized.append(step_data)

    return serialized
