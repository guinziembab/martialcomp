from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from ...models import (
    Club, TrainingSession, TrainingSlot, Attendance, Practitioner,
    TrainingProgram, TrainingModule, TrainingExercise, ProgramEnrollment
)
from ...forms.trainings import TrainingProgramForm, TrainingSlotForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def training_sessions(request):
    """
    Vue pour afficher toutes les sessions d'entraÃ®nement du club.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre associé Ã  un club pour voir les sessions d'entraÃ®nement."))
        return redirect('competitions:dashboard:club')
    
    # Récupérer toutes les sessions d'entraÃ®nement du club
    sessions = TrainingSession.objects.filter(
        training_slot__club=club
    ).select_related(
        'training_slot', 
        'training_slot__discipline', 
        'actual_instructor'
    ).order_by('-date')
    
    # Calculer les statistiques pour chaque session
    for session in sessions:
        attendance_data = Attendance.objects.filter(session=session).aggregate(
            total_count=Count('id'),
            presents_count=Count('id', filter=Q(status='present')),
        )
        session.total_count = attendance_data['total_count']
        session.presents_count = attendance_data['presents_count']
        session.attendance_rate = (session.presents_count / session.total_count * 100) if session.total_count > 0 else 0
    
    # Récupérer les créneaux d'entraÃ®nement actifs
    active_slots = TrainingSlot.objects.filter(
        club=club,
        is_active=True
    ).select_related('discipline', 'instructor')
    
    context = {
        'club': club,
        'sessions': sessions,
        'active_slots': active_slots,
        'page_title': _("Sessions d'entraÃ®nement"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/training_sessions.html', context)


@login_required
def attendance_list(request, session_id):
    """
    Vue pour afficher et gérer la liste de présence d'une session d'entraÃ®nement.
    """
    # Récupérer la session d'entraÃ®nement
    session = get_object_or_404(TrainingSession, id=session_id)
    
    # Vérifier que l'utilisateur a accès Ã  cette session
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club or session.training_slot.club != club:
        messages.error(request, _("Vous n'avez pas accès Ã  cette session."))
        return redirect('competitions:dashboard:club')
    
    # Récupérer toutes les présences pour cette session
    attendances = Attendance.objects.filter(
        session=session
    ).select_related('practitioner').order_by('practitioner__last_name', 'practitioner__first_name')
    
    # Si c'est une soumission de formulaire
    if request.method == 'POST':
        # Traiter les mises Ã  jour de présence
        for attendance in attendances:
            status_key = f'status_{attendance.id}'
            if status_key in request.POST:
                new_status = request.POST[status_key]
                if new_status in ['present', 'absent', 'excused', 'late']:
                    attendance.status = new_status
                    attendance.save()
        
        messages.success(request, _("La liste de présence a été mise Ã  jour."))
        return redirect('competitions:club:attendance_list', session_id=session.id)
    
    # Calculer les statistiques
    stats = Attendance.objects.filter(session=session).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        excused=Count('id', filter=Q(status='excused')),
        late=Count('id', filter=Q(status='late'))
    )
    
    context = {
        'session': session,
        'attendances': attendances,
        'stats': stats,
        'club': club,
        'page_title': _("Liste de présence"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/attendance_list.html', context)


@login_required
def create_training_session(request):
    """
    Vue pour créer une nouvelle session d'entraÃ®nement.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre associé Ã  un club pour créer des sessions."))
        return redirect('competitions:dashboard:club')
    
    if request.method == 'POST':
        # Traiter le formulaire
        training_slot_id = request.POST.get('training_slot')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')
        
        if training_slot_id and date:
            try:
                training_slot = TrainingSlot.objects.get(id=training_slot_id, club=club)
                
                # Créer la session
                session = TrainingSession.objects.create(
                    training_slot=training_slot,
                    date=date,
                    notes=notes
                )
                
                # Créer automatiquement les entrées de présence pour tous les pratiquants actifs
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if club_organization:
                    practitioners = Practitioner.objects.filter(
                        organization=club_organization,
                        is_active=True
                    )
                    
                    for practitioner in practitioners:
                        Attendance.objects.create(
                            session=session,
                            practitioner=practitioner,
                            status='absent',  # Par défaut absent
                            recorded_by=request.user
                        )
                
                messages.success(request, _("La session d'entraÃ®nement a été créée."))
                return redirect('competitions:club:attendance_list', session_id=session.id)
                
            except TrainingSlot.DoesNotExist:
                messages.error(request, _("Créneau d'entraÃ®nement invalide."))
        else:
            messages.error(request, _("Veuillez remplir tous les champs requis."))
    
    # Récupérer les créneaux d'entraÃ®nement actifs
    training_slots = TrainingSlot.objects.filter(
        club=club,
        is_active=True
    ).select_related('discipline', 'instructor')
    
    context = {
        'club': club,
        'training_slots': training_slots,
        'today': timezone.now().date(),
        'page_title': _("Créer une session"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/create_training_session.html', context)


@login_required
def training_programs(request):
    """
    Vue pour lister tous les programmes d'entraînement.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez être associé à un club pour voir les programmes d'entraînement."))
        return redirect('competitions:dashboard:club')
    
    # Récupérer tous les programmes d'entraînement actifs
    programs = TrainingProgram.objects.filter(
        is_active=True
    ).select_related().prefetch_related('disciplines', 'modules').order_by('-created_at')
    
    context = {
        'club': club,
        'programs': programs,
        'page_title': _("Programmes d'entraînement"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/training_programs.html', context)


@login_required
def create_training_program(request):
    """
    Vue pour créer un nouveau programme d'entraînement.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez être associé à un club pour créer des programmes."))
        return redirect('competitions:dashboard:club')
    
    if request.method == 'POST':
        form = TrainingProgramForm(request.POST, club=club)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            form.save_m2m()  # Pour sauvegarder les disciplines
            
            messages.success(request, _("Le programme d'entraînement a été créé avec succès."))
            return redirect('competitions:club:training_programs')
    else:
        form = TrainingProgramForm(club=club)
    
    context = {
        'club': club,
        'form': form,
        'page_title': _("Créer un programme"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/create_training_program.html', context)


@login_required
def edit_training_program(request, program_id):
    """
    Vue pour modifier un programme d'entraînement.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez être associé à un club."))
        return redirect('competitions:dashboard:club')
    
    program = get_object_or_404(TrainingProgram, id=program_id)
    
    if request.method == 'POST':
        form = TrainingProgramForm(request.POST, instance=program, club=club)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le programme a été modifié avec succès."))
            return redirect('competitions:club:training_programs')
    else:
        form = TrainingProgramForm(instance=program, club=club)
    
    context = {
        'club': club,
        'form': form,
        'program': program,
        'page_title': _("Modifier le programme"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/edit_training_program.html', context)


@login_required 
def create_training_slot(request):
    """
    Vue pour créer un nouveau créneau d'entraînement.
    """
    # Récupérer le club de l'utilisateur
    club = None
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        club = Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez être associé à un club pour créer des créneaux."))
        return redirect('competitions:dashboard:club')
    
    if request.method == 'POST':
        form = TrainingSlotForm(request.POST, club=club)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.club = club
            slot.save()
            
            messages.success(request, _("Le créneau d'entraînement a été créé avec succès."))
            return redirect('competitions:club:training_sessions')
    else:
        form = TrainingSlotForm(club=club)
    
    context = {
        'club': club,
        'form': form,
        'page_title': _("Créer un créneau"),
        'section': 'training'
    }
    
    return render(request, 'competitions/club/create_training_slot.html', context)
