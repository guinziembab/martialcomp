# apps/competitions/views/schedule_api.py
"""
API pour la programmation des catégories par tatami.
Permet de gérer l'ordre de passage des catégories.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext as _
import json

from ..models import Competition, CompetitionCategory


def get_competition_and_check_permission(request, competition_id):
    """Vérifie que l'utilisateur peut gérer la programmation."""
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier les permissions (organisateur ou admin)
    user = request.user
    if not user.is_authenticated:
        return None, JsonResponse({'success': False, 'error': _('Non authentifié')}, status=401)

    # Check if user is organizer or has permission
    is_organizer = False
    if hasattr(competition, 'organizer') and competition.organizer:
        if hasattr(competition.organizer, 'members'):
            is_organizer = competition.organizer.members.filter(user=user).exists()

    if not user.is_staff and not is_organizer:
        return None, JsonResponse({'success': False, 'error': _('Permission refusée')}, status=403)

    return competition, None


@login_required
@require_GET
def get_schedule(request, competition_id):
    """
    Récupère la programmation des catégories par tatami.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    # Récupérer toutes les catégories avec leur programmation
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).select_related('competition_type').order_by('assigned_tatami', 'schedule_order', 'name')

    # Organiser par tatami
    schedule = {}
    unassigned = []

    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': cat.name,
            'competition_type': cat.competition_type.name if cat.competition_type else '',
            'participants_count': cat.registered_count,
            'schedule_order': cat.schedule_order,
            'estimated_start_time': cat.estimated_start_time.strftime('%H:%M') if cat.estimated_start_time else None,
            'estimated_duration': cat.estimated_duration or 30,
            'gender': cat.get_gender_display() if hasattr(cat, 'get_gender_display') else cat.gender,
        }

        if cat.assigned_tatami:
            tatami_key = str(cat.assigned_tatami)
            if tatami_key not in schedule:
                schedule[tatami_key] = []
            schedule[tatami_key].append(cat_data)
        else:
            unassigned.append(cat_data)

    return JsonResponse({
        'success': True,
        'schedule': schedule,
        'unassigned': unassigned,
        'tatamis': list(schedule.keys()),
    })


@login_required
@require_POST
def assign_category_to_tatami(request, competition_id):
    """
    Assigne une catégorie à un tatami.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        tatami = data.get('tatami')

        if not category_id or not tatami:
            return JsonResponse({'success': False, 'error': _('Données manquantes')}, status=400)

        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        with transaction.atomic():
            # Trouver le prochain ordre sur ce tatami
            max_order = CompetitionCategory.objects.filter(
                competition=competition,
                assigned_tatami=tatami
            ).aggregate(Max('schedule_order'))['schedule_order__max'] or 0

            category.assigned_tatami = int(tatami)
            category.schedule_order = max_order + 1
            category.save()

        return JsonResponse({
            'success': True,
            'message': f'Catégorie assignée au tatami {tatami}',
            'schedule_order': category.schedule_order
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def unassign_category(request, competition_id):
    """
    Retire une catégorie de son tatami assigné.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')

        if not category_id:
            return JsonResponse({'success': False, 'error': _('category_id requis')}, status=400)

        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        old_tatami = category.assigned_tatami
        old_order = category.schedule_order

        with transaction.atomic():
            category.assigned_tatami = None
            category.schedule_order = None
            category.estimated_start_time = None
            category.save()

            # Réordonner les catégories restantes sur l'ancien tatami
            if old_tatami and old_order:
                categories_to_reorder = CompetitionCategory.objects.filter(
                    competition=competition,
                    assigned_tatami=old_tatami,
                    schedule_order__gt=old_order
                ).order_by('schedule_order')

                for cat in categories_to_reorder:
                    cat.schedule_order -= 1
                    cat.save()

        return JsonResponse({
            'success': True,
            'message': _('Catégorie retirée du tatami')
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def move_category(request, competition_id):
    """
    Déplace une catégorie vers le haut ou le bas dans l'ordre de passage.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        direction = data.get('direction')  # 'up' ou 'down'

        if not category_id or direction not in ['up', 'down']:
            return JsonResponse({'success': False, 'error': _('Données invalides')}, status=400)

        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        if not category.assigned_tatami or not category.schedule_order:
            return JsonResponse({'success': False, 'error': _('Catégorie non assignée')}, status=400)

        with transaction.atomic():
            current_order = category.schedule_order
            tatami = category.assigned_tatami

            if direction == 'up':
                # Trouver la catégorie au-dessus
                swap_category = CompetitionCategory.objects.filter(
                    competition=competition,
                    assigned_tatami=tatami,
                    schedule_order=current_order - 1
                ).first()

                if swap_category:
                    swap_category.schedule_order = current_order
                    category.schedule_order = current_order - 1
                    swap_category.save()
                    category.save()
                else:
                    return JsonResponse({'success': False, 'error': _('Déjà en première position')})

            else:  # direction == 'down'
                # Trouver la catégorie en-dessous
                swap_category = CompetitionCategory.objects.filter(
                    competition=competition,
                    assigned_tatami=tatami,
                    schedule_order=current_order + 1
                ).first()

                if swap_category:
                    swap_category.schedule_order = current_order
                    category.schedule_order = current_order + 1
                    swap_category.save()
                    category.save()
                else:
                    return JsonResponse({'success': False, 'error': _('Déjà en dernière position')})

        return JsonResponse({
            'success': True,
            'message': f'Catégorie déplacée vers le {"haut" if direction == "up" else "bas"}',
            'new_order': category.schedule_order
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def reorder_categories(request, competition_id):
    """
    Réordonne toutes les catégories d'un tatami (après drag & drop).
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        tatami = data.get('tatami')
        category_ids = data.get('category_ids', [])  # Liste ordonnée des IDs

        if not tatami or not category_ids:
            return JsonResponse({'success': False, 'error': _('Données manquantes')}, status=400)

        with transaction.atomic():
            for order, cat_id in enumerate(category_ids, start=1):
                CompetitionCategory.objects.filter(
                    id=cat_id,
                    competition=competition
                ).update(
                    assigned_tatami=int(tatami),
                    schedule_order=order
                )

        return JsonResponse({
            'success': True,
            'message': f'Ordre mis à jour pour le tatami {tatami}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_category_time(request, competition_id):
    """
    Met à jour l'heure de début estimée d'une catégorie.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        start_time = data.get('start_time')  # Format "HH:MM"
        duration = data.get('duration')  # En minutes

        if not category_id:
            return JsonResponse({'success': False, 'error': _('category_id requis')}, status=400)

        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        from datetime import datetime

        if start_time:
            try:
                category.estimated_start_time = datetime.strptime(start_time, '%H:%M').time()
            except ValueError:
                return JsonResponse({'success': False, 'error': _("Format d'heure invalide (HH:MM)")}, status=400)

        if duration is not None:
            category.estimated_duration = int(duration)

        category.save()

        return JsonResponse({
            'success': True,
            'message': _('Horaire mis à jour')
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def auto_generate_schedule(request, competition_id):
    """
    Génère automatiquement un planning en répartissant les catégories sur les tatamis.
    """
    competition, error = get_competition_and_check_permission(request, competition_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        num_tatamis = data.get('num_tatamis', 3)
        start_time_str = data.get('start_time', '09:00')
        default_duration = data.get('default_duration', 30)

        from datetime import datetime, timedelta

        start_time = datetime.strptime(start_time_str, '%H:%M')

        # Récupérer toutes les catégories non assignées
        categories = list(CompetitionCategory.objects.filter(
            competition=competition
        ).order_by('competition_type', 'name'))

        if not categories:
            return JsonResponse({'success': False, 'error': _('Aucune catégorie à programmer')})

        with transaction.atomic():
            # Répartir les catégories sur les tatamis
            tatami_times = {i: start_time for i in range(1, num_tatamis + 1)}
            tatami_orders = {i: 0 for i in range(1, num_tatamis + 1)}

            for category in categories:
                # Trouver le tatami le moins chargé (celui qui finit le plus tôt)
                min_tatami = min(tatami_times, key=tatami_times.get)

                tatami_orders[min_tatami] += 1
                duration = category.estimated_duration or default_duration

                category.assigned_tatami = min_tatami
                category.schedule_order = tatami_orders[min_tatami]
                category.estimated_start_time = tatami_times[min_tatami].time()
                category.estimated_duration = duration
                category.save()

                # Avancer l'heure pour ce tatami
                tatami_times[min_tatami] += timedelta(minutes=duration)

        return JsonResponse({
            'success': True,
            'message': f'Planning généré avec {num_tatamis} tatamis',
            'categories_count': len(categories)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON invalide')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
