import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.urls import reverse  # Ajout nécessaire pour la fonction apply_as_judge

# Modèles
from ..models import (
    Competition, 
    CompetitionCategory, 
    Practitioner, 
    CompetitionRegistration,
    Judge,
    JudgeQualification,
    JudgeCompetitionAssignment,
    JudgeApplication, 
    Discipline,  # Déplacé ici pour éviter le doublon
    Notification  # Déplacé ici pour éviter le doublon
)
from django.contrib.auth.models import User

# Formulaires
from ..forms import (
    JudgeProfileForm, 
    JudgeQualificationForm,
    JudgeApplicationForm  # Ajouté pour apply_as_judge
)
from ..forms.judges import JudgeTechnicalApplicationForm

logger = logging.getLogger(__name__)

# Vue pour le tableau de bord des juges
@login_required
def judge_dashboard(request):
    """
    Tableau de bord principal pour les juges.
    Affiche les compétitions où le juge est inscrit et ses affectations.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès au tableau de bord des juges."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Essayer de récupérer le profil juge
    try:
        judge = Judge.objects.get(practitioner=practitioner)
    except Judge.DoesNotExist:
        judge = None
    
    # Récupérer toutes les inscriptions du pratiquant où il est juge/arbitre
    registrations = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        status='approved'
    ).filter(
        Q(is_technical_judge=True) | Q(is_combat_referee=True)
    ).select_related('competition')
    
    # Récupérer toutes les affectations du juge
    assignments_by_competition = {}
    try:
        assignments = JudgeCompetitionAssignment.objects.filter(
            registration__in=registrations
        ).select_related('registration', 'category')
        
        # Regrouper les affectations par compétition
        for assignment in assignments:
            competition = assignment.registration.competition
            if competition.id not in assignments_by_competition:
                assignments_by_competition[competition.id] = {
                    'competition': competition,
                    'assignments': []
                }
            assignments_by_competition[competition.id]['assignments'].append(assignment)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des affectations: {str(e)}")
        assignments = []
    
    # Récupérer les compétitions à venir où le juge peut s'inscrire
    now = timezone.now().date()
    upcoming_competitions = Competition.objects.filter(
        start_date__gte=now,
        status='published'
    ).exclude(
        id__in=[reg.competition.id for reg in registrations]
    ).order_by('start_date')[:5]
    
    # Statistiques pour le tableau de bord
    stats = {
        'upcoming_assignments': sum(1 for reg in registrations if reg.competition.start_date >= now),
        'completed_assignments': sum(1 for reg in registrations if hasattr(reg.competition, 'end_date') and 
                                   reg.competition.end_date and reg.competition.end_date < now),
        'qualification_level': judge.get_qualification_level_display() if judge and hasattr(judge, 'get_qualification_level_display') else 'N/A',
        'experience_years': judge.years_experience if judge and hasattr(judge, 'years_experience') else 0
    }
    
    context = {
        'practitioner': practitioner,
        'judge': judge,
        'registrations': registrations,
        'assignments_by_competition': assignments_by_competition,
        'upcoming_competitions': upcoming_competitions,
        'stats': stats,
        'today': now
    }
    
    return render(request, 'competitions/judge/dashboard.html', context)

@login_required
def judge_profile(request):
    """
    Affiche et permet de modifier le profil du juge.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès au profil de juge."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Récupérer ou créer le profil juge
    judge, created = Judge.objects.get_or_create(
        practitioner=practitioner,
        defaults={
            'qualification_level': 'novice',
            'years_experience': 0,
            'is_technical_judge': True
        }
    )
    
    # Récupérer les qualifications du juge
    qualifications = JudgeQualification.objects.filter(practitioner=practitioner)
    
    # Récupérer les inscriptions
    registrations = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        status='approved'
    ).filter(
        Q(is_technical_judge=True) | Q(is_combat_referee=True)
    ).select_related('competition')
    
    context = {
        'judge': judge,
        'practitioner': practitioner,
        'qualifications': qualifications,
        'registrations': registrations,
    }
    
    return render(request, 'competitions/judge/profile.html', context)

@login_required
def edit_judge_profile(request):
    """
    Permet de modifier le profil du juge.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès au profil de juge."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Récupérer le profil juge
    try:
        judge = Judge.objects.get(practitioner=practitioner)
    except Judge.DoesNotExist:
        judge = None
        messages.error(request, _("Vous n'avez pas encore de profil de juge."))
        return redirect('competitions:judge:profile')
    
    if request.method == 'POST':
        form = JudgeProfileForm(request.POST, request.FILES, instance=judge)
        if form.is_valid():
            try:
                # Ne pas modifier les niveaux de qualification qui doivent être validés par les administrateurs
                judge_updated = form.save(commit=False)
                
                # Ces champs ne doivent pas être modifiables par l'utilisateur
                if hasattr(judge, 'qualification_level') and hasattr(judge_updated, 'qualification_level'):
                    judge_updated.qualification_level = judge.qualification_level
                
                # D'autres champs qui ne devraient pas être modifiés par l'utilisateur
                for field in ['technical_judge_level', 'combat_referee_level', 'certification_number']:
                    if hasattr(judge, field) and hasattr(judge_updated, field):
                        setattr(judge_updated, field, getattr(judge, field))
                
                judge_updated.save()
                
                # Sauvegarder les relations ManyToMany
                form.save_m2m()
                
                messages.success(request, _("Votre profil de juge a été mis à jour avec succès."))
                return redirect('competitions:judge:profile')
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du profil de juge: {str(e)}")
                messages.error(request, _("Une erreur est survenue lors de la mise à jour de votre profil: {}").format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = JudgeProfileForm(instance=judge)
    
    context = {
        'form': form,
        'judge': judge,
        'practitioner': practitioner,
        'title': _("Modifier mon profil de juge"),
        'submit_text': _("Enregistrer les modifications")
    }
    
    return render(request, 'competitions/judge/edit_profile.html', context)

@login_required
def add_qualification(request):
    """
    Permet d'ajouter une qualification au profil du juge.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès à cette fonctionnalité."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    if request.method == 'POST':
        form = JudgeQualificationForm(request.POST)
        if form.is_valid():
            try:
                qualification = form.save(commit=False)
                qualification.practitioner = practitioner
                qualification.save()
                messages.success(request, _("Qualification ajoutée avec succès."))
                return redirect('competitions:judge:profile')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue : {}").format(str(e)))
    else:
        form = JudgeQualificationForm()
    
    return render(request, 'competitions/judge/add_qualification.html', {
        'form': form,
        'practitioner': practitioner,
    })


@login_required
def upcoming_competitions(request):
    """
    Affiche les compétitions à venir pour lesquelles le juge peut s'inscrire.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès à cette fonctionnalité."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Récupérer les compétitions à venir
    now = timezone.now().date()
    upcoming_competitions = Competition.objects.filter(
        start_date__gte=now,
        status='published'
    ).order_by('start_date')
    
    # Récupérer les compétitions où le juge est déjà inscrit
    registered_competitions = Competition.objects.filter(
        registrations__practitioner=practitioner,
        registrations__status__in=['pending', 'approved']
    )
    
    registered_ids = [comp.id for comp in registered_competitions]
    
    context = {
        'upcoming_competitions': upcoming_competitions,
        'registered_ids': registered_ids,
        'practitioner': practitioner,
        'now': now,
    }
    
    return render(request, 'competitions/judge/upcoming_competitions.html', context)

@login_required
def competition_detail(request, competition_id):
    """
    Affiche les détails d'une compétition pour un juge.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès à cette fonctionnalité."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
        
        # Vérifier si le juge est inscrit à cette compétition
        registration = CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition=competition
        ).first()
    except Practitioner.DoesNotExist:
        practitioner = None
        registration = None
    
    # Récupérer les catégories de la compétition
    categories = CompetitionCategory.objects.filter(competition=competition).order_by('name')
    
    context = {
        'competition': competition,
        'categories': categories,
        'practitioner': practitioner,
        'registration': registration,
        'is_registered': registration is not None,
        'is_past': competition.end_date < timezone.now().date()
    }
    
    return render(request, 'competitions/judge/competition_detail.html', context)

@login_required
def competition_assignments(request, competition_id):
    """
    Affiche les affectations du juge pour une compétition spécifique.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès à cette fonctionnalité."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé à l'utilisateur
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le juge est inscrit à cette compétition
    registration = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition=competition,
        status='approved'
    ).filter(
        Q(is_technical_judge=True) | Q(is_combat_referee=True)
    ).first()
    
    if not registration:
        messages.error(request, _("Vous n'êtes pas inscrit comme juge pour cette compétition."))
        return redirect('technical_scoring:judge_dashboard')
    
    # Récupérer les affectations du juge pour cette compétition
    try:
        assignments = JudgeAssignment.objects.filter(
            registration=registration
        ).select_related('category')
    except:
        assignments = []
    
    context = {
        'competition': competition,
        'assignments': assignments,
        'registration': registration,
        'practitioner': practitioner,
    }
    
    return render(request, 'competitions/judge/competition_assignments.html', context)

@login_required
def register_for_competition(request, competition_id):
    """
    Permet à un juge de s'inscrire pour officier lors d'une compétition.
    """
    # Vérifier si l'utilisateur a le rôle de juge
    if not hasattr(request.user, 'role') or request.user.role != 'judge':
        messages.error(request, _("Vous n'avez pas accès à cette fonctionnalité."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Vérifier si la compétition accepte les inscriptions
    if competition.status not in ['published', 'open']:
        messages.error(request, _("Les inscriptions ne sont pas ouvertes pour cette compétition."))
        return redirect('technical_scoring:judge_dashboard')
    
    # Récupérer le praticien associé à l'utilisateur
    try:
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'êtes pas enregistré comme pratiquant."))
        return redirect('competitions:dashboard')
    
    # Vérifier si le juge est déjà inscrit à cette compétition
    existing_registration = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition=competition
    ).first()
    
    if request.method == 'POST':
        # Recueillir les informations sur les types de rôles de juge/arbitre
        is_technical_judge = 'is_technical_judge' in request.POST
        is_combat_referee = 'is_combat_referee' in request.POST
        
        # Au moins un type doit être sélectionné
        if not is_technical_judge and not is_combat_referee:
            messages.error(request, _("Vous devez sélectionner au moins un type de rôle (juge technique ou arbitre de combat)."))
            return render(request, 'competitions/judge/register_for_competition.html', {
                'competition': competition,
                'existing_registration': existing_registration,
                'title': _("Inscription à la compétition")
            })
        
        try:
            with transaction.atomic():
                if existing_registration:
                    # Mettre à jour l'inscription existante
                    existing_registration.is_technical_judge = is_technical_judge
                    existing_registration.is_combat_referee = is_combat_referee
                    
                    # Définir les niveaux de qualification à "pending" s'ils ne sont pas déjà définis
                    if is_technical_judge and hasattr(existing_registration, 'technical_judge_level'):
                        if not existing_registration.technical_judge_level or existing_registration.technical_judge_level == '':
                            existing_registration.technical_judge_level = 'pending'
                    
                    if is_combat_referee and hasattr(existing_registration, 'combat_referee_level'):
                        if not existing_registration.combat_referee_level or existing_registration.combat_referee_level == '':
                            existing_registration.combat_referee_level = 'pending'
                    
                    existing_registration.save()
                    messages.success(request, _("Votre inscription a été mise à jour avec succès."))
                else:
                    # Créer une nouvelle inscription
                    registration = CompetitionRegistration(
                        practitioner=practitioner,
                        competition=competition,
                        status='pending',
                        registration_date=timezone.now(),
                        is_technical_judge=is_technical_judge,
                        is_combat_referee=is_combat_referee
                    )
                    
                    # Définir les niveaux de qualification à "pending"
                    if is_technical_judge and hasattr(registration, 'technical_judge_level'):
                        registration.technical_judge_level = 'pending'
                    
                    if is_combat_referee and hasattr(registration, 'combat_referee_level'):
                        registration.combat_referee_level = 'pending'
                    
                    registration.save()
                    messages.success(request, _("Votre inscription a été enregistrée avec succès."))
                    messages.info(request, _("Votre niveau de qualification sera validé par les administrateurs."))
                
                # Notifier les organisateurs de la compétition
                try:
                    organizers = User.objects.filter(
                        Q(is_staff=True) | 
                        Q(role='admin') | 
                        Q(id=competition.owner_id) if hasattr(competition, 'owner_id') else Q()
                    ).distinct()
                    
                    registration_obj = existing_registration if existing_registration else registration
                    roles = []
                    if registration_obj.is_technical_judge:
                        roles.append(_("juge technique"))
                    if registration_obj.is_combat_referee:
                        roles.append(_("arbitre de combat"))
                    
                    roles_text = " et ".join(roles)
                    
                    for organizer in organizers:
                        Notification.objects.create(
                            user=organizer,
                            title=_("Nouvelle inscription de juge"),
                            message=_("{} s'est inscrit(e) en tant que {} pour la compétition {}").format(
                                practitioner.full_name,
                                roles_text,
                                competition.title
                            ),
                            link=reverse('admin:competitions_competitionregistration_changelist')
                        )
                except Exception as notification_error:
                    logger.error(f"Impossible d'envoyer les notifications: {str(notification_error)}")
                
                return redirect('technical_scoring:judge_dashboard')
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription à la compétition: {str(e)}")
            messages.error(request, _("Une erreur est survenue lors de l'inscription: {}").format(str(e)))
    
    context = {
        'competition': competition,
        'existing_registration': existing_registration,
        'title': _("Inscription à la compétition"),
        'practitioner': practitioner,
        # Afficher un message informatif concernant la qualification
        'qualification_message': _("Votre niveau de qualification sera validé par les administrateurs.")
    }
    
    return render(request, 'competitions/judge/register_for_competition.html', context)


@login_required
def apply_as_judge(request):
    """
    Permet à un utilisateur de poser sa candidature pour devenir juge technique.
    """
    # Vérifier si l'utilisateur a déjà le statut de juge
    if hasattr(request.user, 'role') and request.user.role == 'judge':
        try:
            practitioner = Practitioner.objects.get(user=request.user)
            judge = Judge.objects.get(practitioner=practitioner)
            messages.info(request, _("Vous êtes déjà enregistré comme juge."))
            # Utiliser un chemin absolu au lieu d'une URL nommée
            return redirect('competitions:technical_scoring:judge_dashboard')
        except (Practitioner.DoesNotExist, Judge.DoesNotExist):
            pass
    
    # Récupérer toutes les disciplines actives
    try:
        disciplines = Discipline.objects.filter(is_active=True)
        logger.info(f"Nombre de disciplines trouvées: {disciplines.count()}")
        
        # Si aucune discipline n'est trouvée, essayer sans le filtre is_active
        if disciplines.count() == 0:
            disciplines = Discipline.objects.all()
            logger.info(f"Nombre total de disciplines (sans filtre is_active): {disciplines.count()}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des disciplines: {str(e)}")
        disciplines = []
    
    # Initialiser les disciplines sélectionnées
    selected_disciplines = []
    
    if request.method == 'POST':
        form = JudgeApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Créer une candidature en attente
                    application = form.save(commit=False)
                    application.user = request.user
                    application.status = 'pending'
                    application.submission_date = timezone.now()
                    
                    # Les niveaux de qualification seront définis par les administrateurs
                    # On ne laisse donc pas l'utilisateur les définir lui-même
                    for field_name in ['qualification_level', 'technical_judge_level', 'combat_referee_level']:
                        if hasattr(application, field_name):
                            setattr(application, field_name, 'pending')
                    
                    application.save()
                    
                    # Sauvegarder les relations ManyToMany si présentes
                    if hasattr(form, 'save_m2m'):
                        form.save_m2m()
                    
                    # Récupérer les disciplines sélectionnées
                    if 'disciplines' in request.POST:
                        selected_disciplines = [int(d) for d in request.POST.getlist('disciplines') if d.isdigit()]
                    
                    # Notifier les administrateurs
                    try:
                        admin_users = User.objects.filter(is_staff=True)
                        for admin in admin_users:
                            Notification.objects.create(
                                user=admin,
                                title=_("Nouvelle candidature de juge"),
                                message=_("{} a posé sa candidature pour devenir juge.").format(
                                    request.user.get_full_name() or request.user.username
                                ),
                                link=reverse('admin:competitions_judgeapplication_change', args=[application.id])
                            )
                    except Exception as notification_error:
                        logger.error(f"Impossible d'envoyer les notifications: {str(notification_error)}")
                    
                    messages.success(request, _("Votre candidature a été soumise avec succès. Vous serez notifié de la décision."))
                    # Utiliser un chemin absolu au lieu d'une URL nommée
                    return redirect('/competitions/technical-scoring/judge/applications/status/')
            except Exception as e:
                logger.error(f"Erreur lors de la candidature de juge: {str(e)}")
                messages.error(request, _("Une erreur est survenue lors de la soumission de votre candidature: {}").format(str(e)))
        else:
            # Récupérer les disciplines sélectionnées en cas d'erreur de validation
            if 'disciplines' in request.POST:
                try:
                    selected_disciplines = [int(d) for d in request.POST.getlist('disciplines') if d.isdigit()]
                except (ValueError, TypeError) as e:
                    logger.error(f"Erreur lors de la conversion des IDs de disciplines: {str(e)}")
            
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Pré-remplir avec les informations de l'utilisateur si possible
        initial_data = {}
        try:
            if hasattr(request.user, 'practitioner'):
                practitioner = request.user.practitioner
                
                # Pré-remplir les informations de base
                for field in ['first_name', 'last_name', 'email', 'phone']:
                    if hasattr(practitioner, field) and getattr(practitioner, field):
                        initial_data[field] = getattr(practitioner, field)
                
                # Pré-remplir les disciplines si disponibles
                if hasattr(practitioner, 'disciplines'):
                    try:
                        selected_disciplines = list(practitioner.disciplines.values_list('id', flat=True))
                    except Exception as e:
                        logger.error(f"Erreur lors de la récupération des disciplines du pratiquant: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de l'utilisateur: {str(e)}")
        
        form = JudgeApplicationForm(initial=initial_data)
    
    context = {
        'form': form,
        'disciplines': disciplines,
        'selected_disciplines': selected_disciplines,
        'title': _("Candidature pour devenir juge"),
        'submit_text': _("Soumettre ma candidature")
    }
    
    return render(request, 'competitions/judge/apply_as_judge.html', context)

@login_required
def judge_applications_status(request):
    """Affiche le statut des candidatures de juge pour l'utilisateur connecté."""
    try:
        applications = JudgeApplication.objects.filter(user=request.user).order_by('-submission_date')
        
        # Récupérer également la dernière candidature approuvée
        approved_application = JudgeApplication.objects.filter(
            user=request.user,
            status='approved'
        ).order_by('-review_date').first()  # <-- CORRECTION
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des candidatures: {str(e)}")
        applications = []
        approved_application = None
        messages.error(request, _("Une erreur est survenue lors de la récupération de vos candidatures."))
    
    context = {
        'applications': applications,
        'approved_application': approved_application,
        'title': _("Statut de mes candidatures")
    }
    
    return render(request, 'competitions/judge/applications_status.html', context)