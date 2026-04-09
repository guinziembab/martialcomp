from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from apps.competitions.models import (
    Competition, CompetitionCategory, Match
)
from apps.competitions.models.schedule import (
    CompetitionSchedule, TatamiSchedule, CategorySchedule,
    MatchTimeSlot, ScheduleChange
)
from apps.competitions.utils.decorators import competition_management_permission_required
from apps.competitions.forms.schedule import (
    CompetitionScheduleForm, TatamiScheduleForm, 
    CategoryScheduleForm, MatchTimeSlotForm,
    BulkCategoryScheduleForm
)
from apps.competitions.utils.schedule import (
    generate_match_schedule, optimize_tatami_usage,
    detect_schedule_conflicts
)


@login_required
@competition_management_permission_required
def schedule_overview(request, competition_id):
    """
    Affiche une vue d'ensemble du planning de la compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer ou créer le planning principal
    schedule, created = CompetitionSchedule.objects.get_or_create(
        competition=competition,
        defaults={
            'start_time': '09:00',
            'end_time': '18:00',
            'tatami_count': 1,
            'updated_by': request.user
        }
    )
    
    # Si le planning vient d'Ãªtre créé, créer un tatami par défaut
    if created:
        TatamiSchedule.objects.create(
            competition_schedule=schedule,
            tatami_number=1,
            name=_("Tatami principal")
        )
        messages.info(request, _("Un planning par défaut a été créé pour cette compétition."))
    
    # Récupérer les tatamis
    tatamis = TatamiSchedule.objects.filter(
        competition_schedule=schedule
    ).order_by('tatami_number')
    
    # Récupérer les plannings par catégorie
    category_schedules = CategorySchedule.objects.filter(
        competition_schedule=schedule
    ).select_related('category', 'tatami').order_by('order', 'estimated_start_time')
    
    # Récupérer les catégories sans planning
    categories_without_schedule = CompetitionCategory.objects.filter(
        competition=competition
    ).exclude(
        id__in=category_schedules.values_list('category_id', flat=True)
    )
    
    # Récupérer les dernières modifications
    recent_changes = ScheduleChange.objects.filter(
        competition_schedule=schedule
    ).select_related('changed_by').order_by('-timestamp')[:10]
    
    # Calculer les heures pour la timeline
    start_hour = schedule.start_time.hour if schedule.start_time else 9
    end_hour = schedule.end_time.hour if schedule.end_time else 18
    hours = list(range(start_hour, end_hour + 1))
    
    # Calculer les positions et largeurs pour la timeline
    total_minutes = (end_hour - start_hour) * 60
    for cat_schedule in category_schedules:
        if cat_schedule.estimated_start_time and cat_schedule.estimated_end_time:
            # Calculer la position de départ (en minutes depuis le début)
            start_minutes = (cat_schedule.estimated_start_time.hour - start_hour) * 60 + cat_schedule.estimated_start_time.minute
            
            # Calculer la durée (en minutes)
            end_minutes = (cat_schedule.estimated_end_time.hour - start_hour) * 60 + cat_schedule.estimated_end_time.minute
            duration_minutes = end_minutes - start_minutes
            
            # Calculer le pourcentage de position (left) et de largeur (width)
            if total_minutes > 0:
                cat_schedule.timeline_left = (start_minutes / total_minutes) * 100
                cat_schedule.timeline_width = (duration_minutes / total_minutes) * 100
            else:
                cat_schedule.timeline_left = 0
                cat_schedule.timeline_width = 0
        elif cat_schedule.estimated_start_time:
            # Fallback: pas de estimated_end_time, estimer une duree par defaut
            participants_count = cat_schedule.category.registrations.count() if cat_schedule.category else 0
            default_duration = max(30, participants_count * (schedule.match_duration or 3))
            start_minutes = (cat_schedule.estimated_start_time.hour - start_hour) * 60 + cat_schedule.estimated_start_time.minute
            if total_minutes > 0:
                cat_schedule.timeline_left = (start_minutes / total_minutes) * 100
                cat_schedule.timeline_width = (default_duration / total_minutes) * 100
            else:
                cat_schedule.timeline_left = 0
                cat_schedule.timeline_width = 0
        else:
            cat_schedule.timeline_left = 0
            cat_schedule.timeline_width = 0
    
    # Calculer les statistiques de progression
    total_categories = CompetitionCategory.objects.filter(competition=competition).count()
    scheduled_categories = category_schedules.count()
    progress_percent = (scheduled_categories / total_categories * 100) if total_categories > 0 else 0
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'tatamis': tatamis,
        'category_schedules': category_schedules,
        'categories_without_schedule': categories_without_schedule,
        'recent_changes': recent_changes,
        'today': competition.start_date or timezone.now().date(),
        'hours': hours,
        'progress_percent': progress_percent,
        'scheduled_categories': scheduled_categories,
        'total_categories': total_categories,
    }
    
    return render(request, 'competitions/management/schedule.html', context)


@login_required
@competition_management_permission_required
def edit_competition_schedule(request, competition_id):
    """
    Modifie les paramètres généraux du planning de la compétition.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        form = CompetitionScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            # Mise Ã  jour du planning
            updated_schedule = form.save(commit=False)
            updated_schedule.updated_by = request.user
            updated_schedule.save()
            
            # Gérer les tatamis si leur nombre a changé
            old_tatami_count = TatamiSchedule.objects.filter(competition_schedule=schedule).count()
            new_tatami_count = updated_schedule.tatami_count
            
            if new_tatami_count > old_tatami_count:
                # Ajouter des tatamis supplémentaires
                for i in range(old_tatami_count + 1, new_tatami_count + 1):
                    TatamiSchedule.objects.create(
                        competition_schedule=schedule,
                        tatami_number=i,
                        name=_("Tatami {}").format(i)
                    )
            elif new_tatami_count < old_tatami_count:
                # Supprimer les tatamis en trop
                # Déplacer d'abord les catégories vers d'autres tatamis
                categories_to_move = CategorySchedule.objects.filter(
                    tatami__competition_schedule=schedule,
                    tatami__tatami_number__gt=new_tatami_count
                )
                
                # Affecter ces catégories au premier tatami
                first_tatami = TatamiSchedule.objects.filter(
                    competition_schedule=schedule,
                    tatami_number=1
                ).first()
                
                if first_tatami and categories_to_move.exists():
                    categories_to_move.update(tatami=first_tatami)
                    messages.warning(request, _("Des catégories ont été réaffectées au tatami 1 suite Ã  la réduction du nombre de tatamis."))
                
                # Supprimer les tatamis en trop
                TatamiSchedule.objects.filter(
                    competition_schedule=schedule,
                    tatami_number__gt=new_tatami_count
                ).delete()
            
            messages.success(request, _("Le planning de la compétition a été mis Ã  jour avec succès."))
            return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    else:
        form = CompetitionScheduleForm(instance=schedule)
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_competition_schedule.html', context)


@login_required
@competition_management_permission_required
def edit_tatami(request, competition_id, tatami_id):
    """
    Modifie les informations d'un tatami.
    """
    # Récupérer la compétition et le tatami
    competition = get_object_or_404(Competition, pk=competition_id)
    tatami = get_object_or_404(TatamiSchedule, pk=tatami_id, competition_schedule__competition=competition)
    
    if request.method == 'POST':
        form = TatamiScheduleForm(request.POST, instance=tatami)
        if form.is_valid():
            form.save()
            messages.success(request, _("Les informations du tatami ont été mises Ã  jour."))
            return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    else:
        form = TatamiScheduleForm(instance=tatami)
    
    context = {
        'competition': competition,
        'tatami': tatami,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_tatami.html', context)


@login_required
@competition_management_permission_required
def add_category_schedule(request, competition_id):
    """
    Ajoute une catégorie au planning.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        form = CategoryScheduleForm(request.POST, schedule=schedule)
        if form.is_valid():
            category_schedule = form.save(commit=False)
            category_schedule.competition_schedule = schedule
            
            # Déterminer l'ordre si non spécifié
            if not category_schedule.order:
                # Prendre le dernier ordre + 1
                last_order = CategorySchedule.objects.filter(
                    competition_schedule=schedule
                ).order_by('-order').values_list('order', flat=True).first() or 0
                category_schedule.order = last_order + 1
            
            # Enregistrer le planning de catégorie
            category_schedule.save()
            
            # Enregistrer le changement dans l'historique
            ScheduleChange.objects.create(
                competition_schedule=schedule,
                category_schedule=category_schedule,
                change_type='category_added',
                changed_by=request.user,
                description=_("Catégorie ajoutée au planning: {}").format(category_schedule.category.name)
            )
            
            messages.success(request, _("La catégorie a été ajoutée au planning."))
            
            # Si demandé, générer automatiquement le planning des matchs
            if 'generate_matches' in request.POST:
                try:
                    # Générer le planning des matchs
                    generate_match_schedule(category_schedule)
                    messages.success(request, _("Le planning des matchs a été généré avec succès."))
                except Exception as e:
                    messages.error(request, _("Erreur lors de la génération du planning des matchs: {}").format(str(e)))
            
            return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    else:
        # Pré-sélectionner la catégorie si fournie en paramètre
        category_id = request.GET.get('category')
        initial = {}
        if category_id:
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                initial['category'] = category
            except CompetitionCategory.DoesNotExist:
                pass
        
        form = CategoryScheduleForm(schedule=schedule, initial=initial)
    
    # Récupérer les tatamis disponibles
    tatamis = TatamiSchedule.objects.filter(competition_schedule=schedule)
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'form': form,
        'tatamis': tatamis,
    }
    
    return render(request, 'competitions/management/add_category_schedule.html', context)


@login_required
@competition_management_permission_required
def edit_category_schedule(request, competition_id, category_schedule_id):
    """
    Modifie le planning d'une catégorie.
    """
    # Récupérer la compétition et le planning de catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category_schedule = get_object_or_404(
        CategorySchedule,
        pk=category_schedule_id,
        competition_schedule__competition=competition
    )
    
    if request.method == 'POST':
        form = CategoryScheduleForm(request.POST, instance=category_schedule, schedule=category_schedule.competition_schedule)
        if form.is_valid():
            # Sauvegarder les anciennes valeurs pour l'historique
            old_tatami = category_schedule.tatami
            old_start_time = category_schedule.estimated_start_time
            
            # Mise Ã  jour du planning
            updated_schedule = form.save()
            
            # Enregistrer les changements dans l'historique
            if old_tatami != updated_schedule.tatami:
                ScheduleChange.objects.create(
                    competition_schedule=category_schedule.competition_schedule,
                    category_schedule=category_schedule,
                    change_type='tatami_change',
                    changed_by=request.user,
                    description=_("Changement de tatami pour {}").format(category_schedule.category.name),
                    old_value=str(old_tatami),
                    new_value=str(updated_schedule.tatami)
                )
            
            if old_start_time != updated_schedule.estimated_start_time:
                ScheduleChange.objects.create(
                    competition_schedule=category_schedule.competition_schedule,
                    category_schedule=category_schedule,
                    change_type='time_change',
                    changed_by=request.user,
                    description=_("Changement d'horaire pour {}").format(category_schedule.category.name),
                    old_value=str(old_start_time),
                    new_value=str(updated_schedule.estimated_start_time)
                )
            
            messages.success(request, _("Le planning de la catégorie a été mis Ã  jour."))
            return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    else:
        form = CategoryScheduleForm(instance=category_schedule, schedule=category_schedule.competition_schedule)
    
    context = {
        'competition': competition,
        'category_schedule': category_schedule,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_category_schedule.html', context)


@login_required
@competition_management_permission_required
@require_POST
def remove_category_schedule(request, competition_id, category_schedule_id):
    """
    Supprime une catégorie du planning.
    """
    # Récupérer la compétition et le planning de catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category_schedule = get_object_or_404(
        CategorySchedule,
        pk=category_schedule_id,
        competition_schedule__competition=competition
    )
    
    # Enregistrer les informations pour l'historique
    schedule = category_schedule.competition_schedule
    category_name = category_schedule.category.name
    
    # Supprimer le planning de catégorie
    category_schedule.delete()
    
    # Enregistrer le changement dans l'historique
    ScheduleChange.objects.create(
        competition_schedule=schedule,
        change_type='category_removed',
        changed_by=request.user,
        description=_("Catégorie supprimée du planning: {}").format(category_name)
    )
    
    messages.success(request, _("La catégorie a été supprimée du planning."))
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
def reorder_categories(request, competition_id):
    """
    Réorganise l'ordre des catégories dans le planning.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        # Récupérer les données JSON
        import json
        try:
            data = json.loads(request.body)
            category_orders = data.get('categoryOrders', [])
            
            with transaction.atomic():
                for item in category_orders:
                    category_id = item.get('id')
                    new_order = item.get('order')
                    
                    if category_id and new_order is not None:
                        CategorySchedule.objects.filter(
                            competition_schedule=schedule,
                            category_id=category_id
                        ).update(order=new_order)
                
                # Enregistrer le changement dans l'historique
                ScheduleChange.objects.create(
                    competition_schedule=schedule,
                    change_type='order_change',
                    changed_by=request.user,
                    description=_("Réorganisation de l'ordre des catégories")
                )
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # Si méthode GET, afficher la page de réorganisation
    category_schedules = CategorySchedule.objects.filter(
        competition_schedule=schedule
    ).select_related('category', 'tatami').order_by('order')
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'category_schedules': category_schedules,
    }
    
    return render(request, 'competitions/management/reorder_categories.html', context)


@login_required
@competition_management_permission_required
def match_schedule(request, competition_id, category_schedule_id):
    """
    Gère le planning des matchs pour une catégorie.
    """
    # Récupérer la compétition et le planning de catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category_schedule = get_object_or_404(
        CategorySchedule,
        pk=category_schedule_id,
        competition_schedule__competition=competition
    )
    
    # Récupérer les time slots
    time_slots = MatchTimeSlot.objects.filter(
        category_schedule=category_schedule
    ).select_related('match').order_by('start_time')
    
    # Récupérer les matchs de la catégorie qui n'ont pas encore de time slot
    unscheduled_matches = Match.objects.filter(
        category=category_schedule.category
    ).exclude(
        id__in=time_slots.exclude(match__isnull=True).values_list('match_id', flat=True)
    )
    
    if request.method == 'POST':
        # Si action de génération automatique
        if 'generate_schedule' in request.POST:
            try:
                # Supprimer les time slots existants
                if 'clear_existing' in request.POST:
                    time_slots.delete()
                
                # Générer le planning des matchs
                generate_match_schedule(category_schedule)
                messages.success(request, _("Le planning des matchs a été généré avec succès."))
                return redirect('competitions:management:match_schedule', 
                               competition_id=competition_id, 
                               category_schedule_id=category_schedule_id)
            except Exception as e:
                messages.error(request, _("Erreur lors de la génération du planning: {}").format(str(e)))
    
    context = {
        'competition': competition,
        'category_schedule': category_schedule,
        'time_slots': time_slots,
        'unscheduled_matches': unscheduled_matches,
    }
    
    return render(request, 'competitions/management/match_schedule.html', context)


@login_required
@competition_management_permission_required
def add_match_time_slot(request, competition_id, category_schedule_id):
    """
    Ajoute un créneau horaire pour un match.
    """
    # Récupérer la compétition et le planning de catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category_schedule = get_object_or_404(
        CategorySchedule,
        pk=category_schedule_id,
        competition_schedule__competition=competition
    )
    
    if request.method == 'POST':
        form = MatchTimeSlotForm(request.POST, category_schedule=category_schedule)
        if form.is_valid():
            time_slot = form.save(commit=False)
            time_slot.category_schedule = category_schedule
            time_slot.save()
            
            messages.success(request, _("Le créneau horaire a été ajouté avec succès."))
            return redirect('competitions:management:match_schedule', 
                           competition_id=competition_id, 
                           category_schedule_id=category_schedule_id)
    else:
        # Préparer les valeurs initiales
        initial = {}
        
        # Utiliser l'heure de début estimée de la catégorie si disponible
        if category_schedule.estimated_start_time:
            from datetime import datetime, timedelta
            start_time = datetime.combine(datetime.today(), category_schedule.estimated_start_time)
            
            # Trouver le dernier créneau existant
            last_slot = MatchTimeSlot.objects.filter(
                category_schedule=category_schedule
            ).order_by('-end_time').first()
            
            if last_slot:
                # Utiliser la fin du dernier créneau comme début du nouveau
                start_time = datetime.combine(datetime.today(), last_slot.end_time)
            
            # Ajouter la durée par défaut des matchs
            match_duration = category_schedule.competition_schedule.match_duration
            end_time = start_time + timedelta(minutes=match_duration)
            
            initial['start_time'] = start_time.time()
            initial['end_time'] = end_time.time()
        
        form = MatchTimeSlotForm(category_schedule=category_schedule, initial=initial)
    
    # Récupérer les matchs disponibles
    unscheduled_matches = Match.objects.filter(
        category=category_schedule.category
    ).exclude(
        time_slot__isnull=False
    )
    
    context = {
        'competition': competition,
        'category_schedule': category_schedule,
        'form': form,
        'unscheduled_matches': unscheduled_matches,
    }
    
    return render(request, 'competitions/management/add_match_time_slot.html', context)


@login_required
@competition_management_permission_required
def edit_match_time_slot(request, competition_id, time_slot_id):
    """
    Modifie un créneau horaire pour un match.
    """
    # Récupérer la compétition et le créneau horaire
    competition = get_object_or_404(Competition, pk=competition_id)
    time_slot = get_object_or_404(
        MatchTimeSlot,
        pk=time_slot_id,
        category_schedule__competition_schedule__competition=competition
    )
    category_schedule = time_slot.category_schedule
    
    if request.method == 'POST':
        form = MatchTimeSlotForm(request.POST, instance=time_slot, category_schedule=category_schedule)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le créneau horaire a été mis Ã  jour avec succès."))
            return redirect('competitions:management:match_schedule', 
                           competition_id=competition_id, 
                           category_schedule_id=category_schedule.id)
    else:
        form = MatchTimeSlotForm(instance=time_slot, category_schedule=category_schedule)
    
    context = {
        'competition': competition,
        'category_schedule': category_schedule,
        'time_slot': time_slot,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_match_time_slot.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_match_time_slot(request, competition_id, time_slot_id):
    """
    Supprime un créneau horaire.
    """
    # Récupérer la compétition et le créneau horaire
    competition = get_object_or_404(Competition, pk=competition_id)
    time_slot = get_object_or_404(
        MatchTimeSlot,
        pk=time_slot_id,
        category_schedule__competition_schedule__competition=competition
    )
    category_schedule_id = time_slot.category_schedule.id
    
    # Supprimer le créneau horaire
    time_slot.delete()
    
    messages.success(request, _("Le créneau horaire a été supprimé."))
    return redirect('competitions:management:match_schedule', 
                   competition_id=competition_id, 
                   category_schedule_id=category_schedule_id)


@login_required
@competition_management_permission_required
def bulk_category_scheduling(request, competition_id):
    """
    Permet de planifier plusieurs catégories en une seule opération.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        form = BulkCategoryScheduleForm(request.POST, schedule=schedule)
        if form.is_valid():
            tatami = form.cleaned_data['tatami']  # Now a TatamiSchedule instance
            categories = form.cleaned_data['categories']
            start_time = form.cleaned_data['start_time']
            duration_per_match = form.cleaned_data.get('duration_per_match', 3)
            
            # Planifier les catégories une par une
            from datetime import datetime, timedelta
            current_time = start_time
            for i, category in enumerate(categories):
                # Vérifier si la catégorie a déjÃ  un planning
                existing = CategorySchedule.objects.filter(
                    competition_schedule=schedule,
                    category=category
                ).first()
                
                # Estimer la duree et calculer heure de fin
                participants_count = category.registrations.count()
                est_duration = max(30, participants_count * duration_per_match)
                dt_start = datetime.combine(datetime.today(), current_time)
                dt_end = dt_start + timedelta(minutes=est_duration)
                estimated_end = dt_end.time()

                if existing:
                    existing.tatami = tatami
                    existing.estimated_start_time = current_time
                    existing.estimated_end_time = estimated_end
                    existing.order = i + 1
                    existing.save()
                    
                    # Enregistrer les changements
                    ScheduleChange.objects.create(
                        competition_schedule=schedule,
                        category_schedule=existing,
                        change_type='time_change',
                        changed_by=request.user,
                        description=_("Mise Ã  jour du planning en masse"),
                        new_value=str(current_time)
                    )
                else:
                    # Créer un nouveau planning
                    category_schedule = CategorySchedule.objects.create(
                        competition_schedule=schedule,
                        category=category,
                        tatami=tatami,
                        estimated_start_time=current_time,
                        estimated_end_time=estimated_end,
                        order=i + 1
                    )
                    
                    # Enregistrer le changement
                    ScheduleChange.objects.create(
                        competition_schedule=schedule,
                        category_schedule=category_schedule,
                        change_type='category_added',
                        changed_by=request.user,
                        description=_("Catégorie ajoutée au planning: {}").format(category.name)
                    )
                
                # Avancer au prochain creneau
                current_time = estimated_end
            
            messages.success(request, _("{} catégories ont été planifiées avec succès.").format(len(categories)))
            return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    else:
        form = BulkCategoryScheduleForm(schedule=schedule)
    
    # Récupérer les catégories sans planning
    scheduled_categories = CategorySchedule.objects.filter(
        competition_schedule=schedule
    ).values_list('category_id', flat=True)
    
    unscheduled_categories = CompetitionCategory.objects.filter(
        competition=competition
    ).exclude(
        id__in=scheduled_categories
    )
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'form': form,
        'unscheduled_categories': unscheduled_categories,
    }
    
    return render(request, 'competitions/management/bulk_category_scheduling.html', context)


@login_required
@competition_management_permission_required
def optimize_schedule(request, competition_id):
    """
    Optimise automatiquement le planning de la compétition.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        try:
            # Optimiser l'utilisation des tatamis
            optimize_tatami_usage(schedule)
            
            # Enregistrer le changement
            ScheduleChange.objects.create(
                competition_schedule=schedule,
                change_type='other',
                changed_by=request.user,
                description=_("Optimisation automatique du planning")
            )
            
            messages.success(request, _("Le planning a été optimisé avec succès."))
        except Exception as e:
            messages.error(request, _("Erreur lors de l'optimisation du planning: {}").format(str(e)))
    
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
def check_schedule_conflicts(request, competition_id):
    """
    Vérifie et affiche les conflits dans le planning.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    # Détecter les conflits
    conflicts = detect_schedule_conflicts(schedule)
    
    context = {
        'competition': competition,
        'schedule': schedule,
        'conflicts': conflicts,
    }
    
    return render(request, 'competitions/management/schedule_conflicts.html', context)


@login_required
@competition_management_permission_required
def publish_schedule(request, competition_id):
    """
    Publie le planning de la compétition.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        # Vérifier les conflits avant de publier
        conflicts = detect_schedule_conflicts(schedule)
        
        if conflicts and not request.POST.get('ignore_conflicts'):
            # Afficher les conflits et demander confirmation
            context = {
                'competition': competition,
                'schedule': schedule,
                'conflicts': conflicts,
                'confirm_publish': True,
            }
            return render(request, 'competitions/management/schedule_conflicts.html', context)
        
        # Publier le planning
        schedule.is_published = True
        schedule.updated_by = request.user
        schedule.save()
        
        # Enregistrer le changement
        ScheduleChange.objects.create(
            competition_schedule=schedule,
            change_type='other',
            changed_by=request.user,
            description=_("Planning publié")
        )
        
        messages.success(request, _("Le planning a été publié avec succès."))
    
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
def unpublish_schedule(request, competition_id):
    """
    Dépublie le planning de la compétition.
    """
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    if request.method == 'POST':
        # Dépublier le planning
        schedule.is_published = False
        schedule.updated_by = request.user
        schedule.save()
        
        # Enregistrer le changement
        ScheduleChange.objects.create(
            competition_schedule=schedule,
            change_type='other',
            changed_by=request.user,
            description=_("Planning dépublié")
        )
        
        messages.success(request, _("Le planning a été dépublié."))
    
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
def export_schedule(request, competition_id):
    """
    Exporte le planning de la compétition au format PDF ou Excel.
    """
    from django.http import HttpResponse
    import csv
    
    # Récupérer la compétition et le planning
    competition = get_object_or_404(Competition, pk=competition_id)
    schedule = get_object_or_404(CompetitionSchedule, competition=competition)
    
    # Récupérer les plannings par catégorie
    category_schedules = CategorySchedule.objects.filter(
        competition_schedule=schedule
    ).select_related('category', 'tatami').order_by('estimated_start_time')
    
    # Choisir le format d'export
    export_format = request.GET.get('format', 'csv')
    
    if export_format == 'csv':
        # Créer une réponse CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{competition.title}_schedule.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            _('Catégorie'), _('Tatami'), _('Heure de début'), 
            _('Heure de fin'), _('Participants')
        ])
        
        for cs in category_schedules:
            writer.writerow([
                cs.category.name,
                f"Tatami {cs.tatami.tatami_number}" if cs.tatami else "",
                cs.estimated_start_time.strftime('%H:%M') if cs.estimated_start_time else "",
                cs.estimated_end_time.strftime('%H:%M') if cs.estimated_end_time else "",
                cs.category.registrations.count()
            ])
        
        return response
    
    elif export_format == 'pdf':
        # Pour le PDF, on peut utiliser une bibliothèque comme ReportLab ou WeasyPrint
        # Ici, on renvoie simplement un message indiquant que cette fonctionnalité n'est pas implémentée
        messages.warning(request, _("L'export PDF n'est pas encore disponible."))
        return redirect('competitions:management:schedule_overview', competition_id=competition_id)
    
    else:
        messages.error(request, _("Format d'export non pris en charge."))
        return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
def api_category_info(request, competition_id):
    """
    API endpoint pour récupérer les informations d'une catégorie.
    Retourne les informations en JSON : discipline, type, nombre de participants, tranche d'âge.
    """
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'success': False, 'error': _("ID de catégorie manquant")}, status=400)
    
    try:
        # Récupérer la catégorie avec les relations nécessaires
        category = CompetitionCategory.objects.select_related(
            'competition_type',
            'competition_type__discipline'
        ).get(
            id=category_id,
            competition_id=competition_id
        )
        
        # Compter les participants inscrits dans cette catégorie
        from apps.competitions.models import CompetitionRegistration
        participants_count = CompetitionRegistration.objects.filter(
            competition_id=competition_id,
            categories=category
        ).count()
        
        # Récupérer les informations
        data = {
            'success': True,
            'discipline': str(category.competition_type.discipline) if category.competition_type and category.competition_type.discipline else '-',
            'type': str(category.competition_type) if category.competition_type else '-',
            'participants_count': participants_count,
            'min_age': category.min_age,
            'max_age': category.max_age,
        }
        
        return JsonResponse(data)

    except CompetitionCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': _("Catégorie non trouvée")}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@competition_management_permission_required
def api_quick_add_category(request, competition_id):
    """
    API endpoint pour ajouter rapidement une catégorie au planning via drag & drop.
    Méthode POST avec JSON body: {category_id, tatami_id, start_time (HH:MM)}
    """
    import json
    from datetime import datetime

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _("Méthode non autorisée")}, status=405)

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        tatami_id = data.get('tatami_id')
        start_time_str = data.get('start_time', '09:00')
        duration_minutes = data.get('duration', 30)

        if not category_id or not tatami_id:
            return JsonResponse({'success': False, 'error': _("Données manquantes")}, status=400)

        # Récupérer la compétition et le planning
        competition = get_object_or_404(Competition, pk=competition_id)
        schedule = get_object_or_404(CompetitionSchedule, competition=competition)

        # Récupérer la catégorie et le tatami
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        tatami = get_object_or_404(TatamiSchedule, id=tatami_id, competition_schedule=schedule)

        # Vérifier que la catégorie n'est pas déjà planifiée
        if CategorySchedule.objects.filter(competition_schedule=schedule, category=category).exists():
            return JsonResponse({
                'success': False,
                'error': _("Cette catégorie est déjà planifiée")
            }, status=400)

        # Parser l'heure de début
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            start_time = schedule.start_time or datetime.strptime('09:00', '%H:%M').time()

        # Calculer l'heure de fin
        from datetime import timedelta
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()

        # Déterminer l'ordre (prochain ordre disponible)
        last_order = CategorySchedule.objects.filter(
            competition_schedule=schedule
        ).order_by('-order').values_list('order', flat=True).first() or 0

        # Créer le planning de catégorie
        with transaction.atomic():
            category_schedule = CategorySchedule.objects.create(
                competition_schedule=schedule,
                category=category,
                tatami=tatami,
                estimated_start_time=start_time,
                estimated_end_time=end_time,
                order=last_order + 1,
                priority='normal'
            )

            # Enregistrer le changement dans l'historique
            ScheduleChange.objects.create(
                competition_schedule=schedule,
                category_schedule=category_schedule,
                change_type='category_added',
                changed_by=request.user,
                description=_("Catégorie ajoutée au planning: {}").format(category.name)
            )

        return JsonResponse({
            'success': True,
            'message': _("Catégorie ajoutée au planning"),
            'data': {
                'category_schedule_id': category_schedule.id,
                'category_name': category.name,
                'tatami_name': tatami.name,
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _("Données JSON invalides")}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@competition_management_permission_required
def api_get_next_available_time(request, competition_id):
    """
    API endpoint pour obtenir la prochaine heure disponible sur un tatami.
    GET avec paramètre tatami_id
    """
    tatami_id = request.GET.get('tatami_id')

    if not tatami_id:
        return JsonResponse({'success': False, 'error': _("ID tatami manquant")}, status=400)

    try:
        competition = get_object_or_404(Competition, pk=competition_id)
        schedule = get_object_or_404(CompetitionSchedule, competition=competition)
        tatami = get_object_or_404(TatamiSchedule, id=tatami_id, competition_schedule=schedule)

        # Trouver la dernière catégorie planifiée sur ce tatami
        last_category = CategorySchedule.objects.filter(
            competition_schedule=schedule,
            tatami=tatami
        ).order_by('-estimated_end_time').first()

        if last_category and last_category.estimated_end_time:
            next_time = last_category.estimated_end_time
        else:
            # Utiliser l'heure de début du planning
            next_time = schedule.start_time or '09:00'

        # Formater l'heure
        if hasattr(next_time, 'strftime'):
            next_time_str = next_time.strftime('%H:%M')
        else:
            next_time_str = str(next_time)[:5]

        return JsonResponse({
            'success': True,
            'next_time': next_time_str,
            'tatami_name': tatami.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
