from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from competitions.models import Practitioner, Event, EventParticipant
from competitions.models.training import (
    TrainingSession,
    TrainingSlot,
    TrainingReservation,
    Attendance,
    TrainingProgram
)


@login_required
def training_dashboard(request):
    """Tableau de bord d'entraînement du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Prochaines sessions
    upcoming_reservations = TrainingReservation.objects.filter(
        practitioner=practitioner,
        date__gte=timezone.now().date(),
        status='confirmed'
    ).select_related('training_slot__discipline').order_by('date', 'training_slot__start_time')[:5]
    
    # Statistiques du mois
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    month_attendances = Attendance.objects.filter(
        practitioner=practitioner,
        session__date__month=current_month,
        session__date__year=current_year
    )
    
    stats = {
        'total_sessions': month_attendances.count(),
        'present': month_attendances.filter(status='present').count(),
        'absent': month_attendances.filter(status='absent').count(),
        'excused': month_attendances.filter(status='excused').count(),
    }
    
    if stats['total_sessions'] > 0:
        stats['attendance_rate'] = (stats['present'] / stats['total_sessions'] * 100)
    else:
        stats['attendance_rate'] = 0
    
    # Programme actuel
    current_program = getattr(practitioner, 'current_training_program', None)
    program_progress = None
    
    if current_program:
        # Calculer la progression globale
        total_modules = current_program.modules.count()
        completed_modules = 0
        
        for module in current_program.modules.all():
            completed_exercises = module.completed_exercises.filter(
                practitioner=practitioner
            ).count()
            total_exercises = module.exercises.count()
            
            if total_exercises > 0 and completed_exercises == total_exercises:
                completed_modules += 1
        
        program_progress = {
            'percentage': (completed_modules / total_modules * 100) if total_modules > 0 else 0,
            'completed_modules': completed_modules,
            'total_modules': total_modules
        }
    
    # Dernières évaluations
    recent_evaluations = []  # À implémenter avec un modèle Evaluation
    
    context = {
        'practitioner': practitioner,
        'upcoming_reservations': upcoming_reservations,
        'stats': stats,
        'current_program': current_program,
        'program_progress': program_progress,
        'recent_evaluations': recent_evaluations,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/dashboard.html', context)


@login_required
def practitioner_training_schedule(request):
    """Vue du planning d'entraînement du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Semaine sélectionnée
    week_offset = int(request.GET.get('week', 0))
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)
    
    # Créneaux disponibles pour la semaine
    training_slots = TrainingSlot.objects.filter(
        Q(end_date__gte=start_of_week) | Q(end_date__isnull=True),
        club=practitioner.organization,
        is_active=True,
        start_date__lte=end_of_week
    ).select_related('discipline', 'instructor')
    
    # Réservations du pratiquant
    reservations = TrainingReservation.objects.filter(
        practitioner=practitioner,
        training_slot__in=training_slots,
        date__range=[start_of_week, end_of_week]
    )
    
    # Organiser par jour
    week_schedule = {}
    for day in range(7):
        current_date = start_of_week + timedelta(days=day)
        day_slots = []
        
        for slot in training_slots:
            if slot.day_of_week == day:
                # Vérifier si le pratiquant a une réservation
                reservation = reservations.filter(
                    training_slot=slot,
                    date=current_date
                ).first()
                
                # Vérifier la capacité
                current_reservations = TrainingReservation.objects.filter(
                    training_slot=slot,
                    date=current_date,
                    status='confirmed'
                ).count()
                
                day_slots.append({
                    'slot': slot,
                    'reservation': reservation,
                    'available': current_reservations < slot.max_participants,
                    'current_participants': current_reservations,
                    'date': current_date
                })
        
        week_schedule[current_date] = day_slots
    
    # Programmes d'entraînement
    training_programs = TrainingProgram.objects.filter(
        disciplines__in=practitioner.disciplines.all(),
        is_active=True
    ).distinct()
    
    # Programme actuel du pratiquant
    current_program = practitioner.current_training_program if hasattr(practitioner, 'current_training_program') else None
    
    context = {
        'practitioner': practitioner,
        'week_schedule': week_schedule,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'week_offset': week_offset,
        'training_programs': training_programs,
        'current_program': current_program,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/schedule.html', context)


@login_required
def practitioner_reserve_training(request, slot_id):
    """Réserver un créneau d'entraînement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    slot = get_object_or_404(TrainingSlot, id=slot_id, club=practitioner.organization)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        if not date:
            messages.error(request, _("Date requise."))
            return redirect('competitions:practitioner_training_schedule')
        
        date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Vérifier la capacité
        current_reservations = TrainingReservation.objects.filter(
            training_slot=slot,
            date=date,
            status='confirmed'
        ).count()
        
        if current_reservations >= slot.max_participants:
            messages.error(request, _("Ce créneau est complet."))
            return redirect('competitions:practitioner_training_schedule')
        
        # Créer la réservation
        reservation, created = TrainingReservation.objects.get_or_create(
            practitioner=practitioner,
            training_slot=slot,
            date=date,
            defaults={'status': 'confirmed'}
        )
        
        if created:
            messages.success(request, _("Réservation confirmée."))
        else:
            messages.info(request, _("Vous avez déjà une réservation pour ce créneau."))
        
        return redirect('competitions:practitioner_training_schedule')
    
    # Afficher le formulaire de réservation
    date = request.GET.get('date', timezone.now().date())
    
    context = {
        'practitioner': practitioner,
        'slot': slot,
        'date': date,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/reserve.html', context)


@login_required
def practitioner_cancel_reservation(request, reservation_id):
    """Annuler une réservation."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    reservation = get_object_or_404(
        TrainingReservation, 
        id=reservation_id, 
        practitioner=practitioner
    )
    
    # Vérifier si l'annulation est possible (ex: 24h avant)
    if reservation.date <= timezone.now().date() + timedelta(days=1):
        messages.error(request, _("Impossible d'annuler moins de 24h à l'avance."))
        return redirect('competitions:practitioner_training_schedule')
    
    reservation.status = 'cancelled'
    reservation.save()
    
    messages.success(request, _("Réservation annulée."))
    return redirect('competitions:practitioner_training_schedule')


@login_required
def practitioner_attendance_history(request):
    """Historique de présence aux entraînements."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Filtres
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    discipline_id = request.GET.get('discipline')
    
    # Récupérer les présences
    attendances = Attendance.objects.filter(
        practitioner=practitioner,
        session__date__month=month,
        session__date__year=year
    ).select_related('session__training_slot__discipline')
    
    if discipline_id:
        attendances = attendances.filter(
            session__training_slot__discipline_id=discipline_id
        )
    
    # Statistiques
    stats = {
        'total_sessions': attendances.count(),
        'present': attendances.filter(status='present').count(),
        'absent': attendances.filter(status='absent').count(),
        'excused': attendances.filter(status='excused').count(),
    }
    
    if stats['total_sessions'] > 0:
        stats['attendance_rate'] = (stats['present'] / stats['total_sessions'] * 100)
    else:
        stats['attendance_rate'] = 0
    
    # Disciplines pour le filtre
    disciplines = practitioner.disciplines.all()
    
    # Graphique mensuel
    monthly_data = []
    for day in range(1, 32):
        try:
            date = datetime(year, month, day).date()
            day_attendances = attendances.filter(session__date=date)
            if day_attendances.exists():
                monthly_data.append({
                    'day': day,
                    'present': day_attendances.filter(status='present').count(),
                    'total': day_attendances.count()
                })
        except ValueError:
            # Jour invalide pour ce mois
            pass
    
    context = {
        'practitioner': practitioner,
        'attendances': attendances.order_by('-session__date'),
        'stats': stats,
        'month': month,
        'year': year,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'monthly_data': monthly_data,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/attendance.html', context)


@login_required
def practitioner_training_progress(request):
    """Suivi de la progression dans les programmes d'entraînement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Programme actuel
    current_program = getattr(practitioner, 'current_training_program', None)
    
    # Progression
    progress_data = {}
    if current_program:
        # Calculer la progression pour chaque module
        for module in current_program.modules.all():
            completed_exercises = module.completed_exercises.filter(
                practitioner=practitioner
            ).count()
            total_exercises = module.exercises.count()
            
            progress_data[module.id] = {
                'module': module,
                'completed': completed_exercises,
                'total': total_exercises,
                'percentage': (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
            }
    
    # Historique des programmes
    program_history = []  # À implémenter avec un modèle ProgramEnrollment
    
    # Objectifs personnels
    personal_goals = []  # À implémenter avec un modèle PersonalGoal
    
    # Statistiques de progression
    stats = {
        'total_training_hours': 0,  # À calculer depuis les présences
        'modules_completed': sum(1 for p in progress_data.values() if p['percentage'] == 100),
        'current_streak': 0,  # À calculer depuis les présences
        'best_streak': 0,  # À calculer depuis l'historique
    }
    
    context = {
        'practitioner': practitioner,
        'current_program': current_program,
        'progress_data': progress_data,
        'program_history': program_history,
        'personal_goals': personal_goals,
        'stats': stats,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/progress.html', context)


@login_required
def practitioner_training_programs(request):
    """Liste des programmes d'entraînement disponibles."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Programmes disponibles pour les disciplines du pratiquant
    available_programs = TrainingProgram.objects.filter(
        disciplines__in=practitioner.disciplines.all(),
        is_active=True
    ).distinct()
    
    # Filtres
    discipline_filter = request.GET.get('discipline')
    level_filter = request.GET.get('level')
    
    if discipline_filter:
        available_programs = available_programs.filter(disciplines__id=discipline_filter)
    if level_filter:
        available_programs = available_programs.filter(level=level_filter)
    
    # Programme actuel
    current_program = getattr(practitioner, 'current_training_program', None)
    
    context = {
        'practitioner': practitioner,
        'available_programs': available_programs,
        'current_program': current_program,
        'disciplines': practitioner.disciplines.all(),
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/programs.html', context)


@login_required
def program_detail(request, program_id):
    """Détails d'un programme d'entraînement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    program = get_object_or_404(TrainingProgram, id=program_id, is_active=True)
    
    # Vérifier si le pratiquant est inscrit
    is_enrolled = practitioner.current_training_program == program if hasattr(practitioner, 'current_training_program') else False
    
    # Vérifier si le programme est disponible pour le pratiquant
    is_available = program.disciplines.filter(id__in=practitioner.disciplines.all()).exists()
    
    # Modules du programme
    modules = program.modules.all().order_by('order')
    
    # Si inscrit, calculer la progression
    module_progress = {}
    if is_enrolled:
        for module in modules:
            completed_exercises = module.completed_exercises.filter(
                practitioner=practitioner
            ).count()
            total_exercises = module.exercises.count()
            
            module_progress[module.id] = {
                'completed': completed_exercises,
                'total': total_exercises,
                'percentage': (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
            }
    
    # Avis et évaluations
    program_reviews = []  # À implémenter avec un modèle ProgramReview
    average_rating = 0  # À calculer depuis les avis
    
    # Instructeurs du programme
    instructors = program.instructors.all() if hasattr(program, 'instructors') else []
    
    context = {
        'practitioner': practitioner,
        'program': program,
        'is_enrolled': is_enrolled,
        'is_available': is_available,
        'modules': modules,
        'module_progress': module_progress,
        'program_reviews': program_reviews,
        'average_rating': average_rating,
        'instructors': instructors,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/program_detail.html', context)


@login_required
def practitioner_enroll_program(request, program_id):
    """S'inscrire à un programme d'entraînement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    program = get_object_or_404(TrainingProgram, id=program_id, is_active=True)
    
    # Vérifier que le pratiquant pratique au moins une des disciplines du programme
    if not program.disciplines.filter(id__in=practitioner.disciplines.all()).exists():
        messages.error(request, _("Ce programme n'est pas disponible pour vos disciplines."))
        return redirect('competitions:practitioner_training_programs')
    
    if request.method == 'POST':
        # S'inscrire au programme
        # À implémenter avec un modèle ProgramEnrollment
        practitioner.current_training_program = program
        practitioner.save()
        
        messages.success(request, _("Inscription au programme confirmée."))
        return redirect('competitions:practitioner_training_progress')
    
    context = {
        'practitioner': practitioner,
        'program': program,
        'active_page': 'training'
    }
    
    return render(request, 'competitions/practitioner/training/enroll_program.html', context)


@login_required
def practitioner_training_calendar_api(request):
    """API pour le calendrier d'entraînement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            return JsonResponse({'error': 'No practitioner profile'}, status=404)
    except:
        return JsonResponse({'error': 'Error retrieving profile'}, status=500)
    
    # Récupérer les dates de début et fin
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    if not start or not end:
        return JsonResponse({'error': 'Missing start or end date'}, status=400)
    
    try:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    events = []
    
    # Réservations d'entraînement
    reservations = TrainingReservation.objects.filter(
        practitioner=practitioner,
        date__range=[start_date, end_date],
        status='confirmed'
    ).select_related('training_slot__discipline')
    
    for reservation in reservations:
        slot = reservation.training_slot
        events.append({
            'id': f'training_{reservation.id}',
            'title': f"{slot.discipline.name} - {slot.level}",
            'start': f"{reservation.date}T{slot.start_time}",
            'end': f"{reservation.date}T{slot.end_time}",
            'color': '#28a745',
            'url': f'/competitions/practitioner/training/reservation/{reservation.id}/'
        })
    
    # Sessions d'entraînement confirmées (présence)
    attendances = Attendance.objects.filter(
        practitioner=practitioner,
        session__date__range=[start_date, end_date]
    ).select_related('session__training_slot__discipline')
    
    for attendance in attendances:
        session = attendance.session
        slot = session.training_slot
        
        color = '#28a745' if attendance.status == 'present' else '#dc3545'
        
        events.append({
            'id': f'attendance_{attendance.id}',
            'title': f"{slot.discipline.name} - {attendance.get_status_display()}",
            'start': f"{session.date}T{slot.start_time}",
            'end': f"{session.date}T{slot.end_time}",
            'color': color,
            'classNames': ['attendance', attendance.status]
        })
    
    return JsonResponse(events, safe=False)


# Alias pour correspondre aux noms des URLs
training_schedule = practitioner_training_schedule
make_reservation = practitioner_reserve_training
cancel_reservation = practitioner_cancel_reservation
attendance_history = practitioner_attendance_history
program_list = practitioner_training_programs
program_enroll = practitioner_enroll_program
training_progress = practitioner_training_progress