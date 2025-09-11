from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta

import json
from apps.competitions.models import (
    Competition, 
    CompetitionRegistration
)
from apps.competitions.models.practitioners import Practitioner
from apps.competitions.models.membership import Membership
from apps.competitions.models.scoring_results import CompetitionResult
from apps.grades.models import PractitionerGrade, Grade
from apps.competitions.models import CategoryTemplate
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def dashboard(request):
    """Vue principale du tableau de bord du pratiquant."""
    # Récupérer le pratiquant associé Ã  l'utilisateur connecté
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            # Si aucun pratiquant n'existe, essayons de chercher par l'email ou créer un nouveau profil
            practitioner = Practitioner.objects.filter(email=request.user.email).first()
            if practitioner and not practitioner.user:
                # Associer le pratiquant Ã  l'utilisateur
                practitioner.user = request.user
                practitioner.save()
            elif not practitioner:
                # Créer un nouveau pratiquant si aucun n'existe
                messages.warning(request, _("Création automatique d'un profil pratiquant."))
                practitioner = Practitioner.objects.create(
                    user=request.user,
                    first_name=request.user.first_name or 'Prénom',
                    last_name=request.user.last_name or 'Nom',
                    email=request.user.email,
                    birth_date=timezone.now().date() - timedelta(days=365*25),  # Ã‚ge par défaut 25 ans
                    gender='M',  # Par défaut
                    nationality='FR'  # Par défaut
                )
                messages.success(request, _("Profil pratiquant créé avec succès. Veuillez compléter vos informations."))
    except Exception as e:
        messages.error(request, _(f"Erreur lors de la récupération du profil: {str(e)}"))
        return redirect('welcome')
    
    # Date actuelle pour les calculs
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    
    # Statistiques de base
    # Compétitions cette année
    competitions_this_year = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition__start_date__year=current_year
    ).count()
    
    # EntraÃ®nements ce mois (simulation - Ã  remplacer par de vraies données quand disponibles)
    trainings_this_month = 12  # Valeur simulée pour le moment
    
    # Taux de présence (simulation)
    attendance_rate = 85  # Valeur simulée
    
    stats = {
        'total_competitions': CompetitionRegistration.objects.filter(practitioner=practitioner).count(),
        'upcoming_competitions': CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition__start_date__gte=timezone.now().date(),
            status='confirmed'
        ).count(),
        'podiums': CompetitionResult.objects.filter(
            practitioner=practitioner,
            rank__lte=3
        ).count(),
        'active_memberships': Membership.objects.filter(
            practitioner=practitioner,
            status='active',
            end_date__gte=timezone.now().date()
        ).count(),
        'trainings_this_month': trainings_this_month,
        'competitions_this_year': competitions_this_year,
        'attendance_rate': attendance_rate
    }
    
    # Prochaines compétitions avec statut d'inscription
    upcoming_competitions = []
    for competition in Competition.objects.filter(
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]:
        registration = CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition=competition
        ).first()
        
        # Vérifier si les inscriptions sont ouvertes
        registration_open = True
        if competition.registration_end_date:
            registration_open = competition.registration_end_date >= timezone.now().date()
        
        upcoming_competitions.append({
            'id': competition.id,
            'name': competition.name,
            'start_date': competition.start_date,
            'location': competition.location,
            'registration': registration,
            'registration_open': registration_open
        })
    
    # Derniers résultats
    recent_results = CompetitionResult.objects.filter(
        practitioner=practitioner
    ).select_related('competition', 'category').order_by('-competition__end_date')[:5]
    
    # Ã‰tat des cotisations
    current_membership = Membership.objects.filter(
        practitioner=practitioner,
        status='active'
    ).order_by('-end_date').first()
    
    # Grade actuel (premier grade actuel trouvé)
    current_grade = PractitionerGrade.objects.filter(
        practitioner=practitioner,
        is_current=True
    ).select_related('grade', 'discipline').first()
    
    # Progression vers le prochain grade (simulation)
    grade_progress = 65  # Valeur simulée
    
    # Prochains entraÃ®nements (simulation - Ã  remplacer par de vraies données)
    next_trainings = []  # Ã€ implémenter quand le modèle Training sera disponible
    
    # Programmes actifs (simulation)
    active_programs = []  # Ã€ implémenter quand le modèle Program sera disponible
    
    # Données pour le graphique d'activité (simulation)
    months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin']
    chart_labels = json.dumps(months)
    chart_data = json.dumps([8, 12, 10, 14, 11, 15])  # Activités par mois (simulation)
    
    # Alertes
    alerts = []
    
    # Vérifier le certificat médical
    if practitioner.medical_certificate_date:
        medical_cert_expiry = practitioner.medical_certificate_date + timedelta(days=365)
        if medical_cert_expiry < timezone.now().date() + timedelta(days=30):
            alerts.append({
                'type': 'warning' if medical_cert_expiry >= timezone.now().date() else 'danger',
                'message': _("Votre certificat médical expire le {}").format(
                    medical_cert_expiry.strftime('%d/%m/%Y')
                )
            })
    else:
        alerts.append({
            'type': 'danger',
            'message': _("Aucun certificat médical enregistré")
        })
    
    # Vérifier l'adhésion
    if current_membership:
        if current_membership.end_date < timezone.now().date() + timedelta(days=30):
            alerts.append({
                'type': 'warning' if current_membership.end_date >= timezone.now().date() else 'danger',
                'message': _("Votre adhésion expire le {}").format(
                    current_membership.end_date.strftime('%d/%m/%Y')
                )
            })
    else:
        alerts.append({
            'type': 'danger',
            'message': _("Aucune adhésion active")
        })
    
    # Récupération des documents du pratiquant
    recent_documents = []
    document_stats = {'total': 0, 'certificates': 0, 'medical': 0}
    
    try:
        from apps.documents.models import Document
        from django.contrib.contenttypes.models import ContentType
        
        # Documents associés au pratiquant
        practitioner_documents = Document.objects.filter(
            Q(created_by=request.user) |
            Q(content_type=ContentType.objects.get_for_model(Practitioner), object_id=str(practitioner.id)) |
            Q(shares__user=request.user)
        ).filter(
            document_type__in=['certificate', 'diploma', 'license', 'medical']
        ).distinct()
        
        recent_documents = practitioner_documents.order_by('-created_at')[:3]
        document_stats = {
            'total': practitioner_documents.count(),
            'certificates': practitioner_documents.filter(document_type='certificate').count(),
            'medical': practitioner_documents.filter(document_type='medical').count(),
        }
    except ImportError:
        # Module documents non disponible
        pass
    except Exception as e:
        # Erreur lors de la récupération des documents
        pass

    context = {
        'practitioner': practitioner,
        'stats': stats,
        'upcoming_competitions': upcoming_competitions,
        'recent_results': recent_results,
        'current_membership': current_membership,
        'current_grade': current_grade,
        'grade_progress': grade_progress,
        'next_trainings': next_trainings,
        'active_programs': active_programs,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'alerts': alerts,
        'recent_documents': recent_documents,
        'document_stats': document_stats,
        'active_page': 'dashboard'
    }
    
    return render(request, 'competitions/practitioner/dashboard.html', context)


@login_required
def profile(request):
    """Vue du profil personnel du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            # Si aucun pratiquant n'existe, essayons de chercher par l'email ou créer un nouveau profil
            practitioner = Practitioner.objects.filter(email=request.user.email).first()
            if practitioner and not practitioner.user:
                # Associer le pratiquant Ã  l'utilisateur
                practitioner.user = request.user
                practitioner.save()
            elif not practitioner:
                # Créer un nouveau pratiquant si aucun n'existe
                messages.warning(request, _("Création automatique d'un profil pratiquant."))
                from datetime import date
                practitioner = Practitioner.objects.create(
                    user=request.user,
                    first_name=request.user.first_name or 'Prénom',
                    last_name=request.user.last_name or 'Nom',
                    email=request.user.email,
                    birth_date=date(2000, 1, 1),  # Date par défaut
                    gender='male',  # Par défaut
                    nationality='FR'  # Par défaut
                )
                messages.success(request, _("Profil pratiquant créé avec succès. Veuillez compléter vos informations."))
    except Exception as e:
        messages.error(request, _(f"Erreur lors de la récupération du profil: {str(e)}"))
        return redirect('welcome')
    
    # Récupérer tous les grades actuels par discipline
    current_grades = PractitionerGrade.objects.filter(
        practitioner=practitioner,
        is_current=True
    ).select_related('grade', 'discipline')
    
    # Récupérer les disciplines pratiquées
    disciplines = practitioner.disciplines.all()
    
    context = {
        'practitioner': practitioner,
        'current_grades': current_grades,
        'disciplines': disciplines,
        'active_page': 'profile'
    }
    
    return render(request, 'competitions/practitioner/profile.html', context)


@login_required
def update_profile(request):
    """Vue pour mettre Ã  jour le profil du pratiquant."""
    if request.method != 'POST':
        messages.error(request, _("Méthode non autorisée."))
        return redirect('competitions:practitioner_profile')
    
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupération des données du formulaire
    try:
        # Mise Ã  jour des informations personnelles
        practitioner.first_name = request.POST.get('first_name', practitioner.first_name)
        practitioner.last_name = request.POST.get('last_name', practitioner.last_name)
        practitioner.email = request.POST.get('email', practitioner.email)
        practitioner.phone = request.POST.get('phone', practitioner.phone)
        practitioner.address = request.POST.get('address', practitioner.address)
        practitioner.postal_code = request.POST.get('postal_code', practitioner.postal_code)
        practitioner.city = request.POST.get('city', practitioner.city)
        practitioner.country = request.POST.get('country', practitioner.country)
        practitioner.gender = request.POST.get('gender', practitioner.gender)
        
        # Mise Ã  jour de la date de naissance si fournie
        birth_date = request.POST.get('birth_date')
        if birth_date:
            practitioner.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        
        # Mise Ã  jour de la nationalité si fournie
        nationality = request.POST.get('nationality')
        if nationality:
            practitioner.nationality = nationality
        
        # Mise Ã  jour du certificat médical si fourni
        medical_certificate_date = request.POST.get('medical_certificate_date')
        if medical_certificate_date:
            practitioner.medical_certificate_date = datetime.strptime(medical_certificate_date, '%Y-%m-%d').date()
        
        # Gestion de l'upload de photo si fournie
        if 'photo' in request.FILES:
            practitioner.photo = request.FILES['photo']
        
        # Sauvegarde des modifications
        practitioner.save()
        
        # Mise Ã  jour éventuelle du nom d'utilisateur
        user = request.user
        user.first_name = practitioner.first_name
        user.last_name = practitioner.last_name
        user.email = practitioner.email
        user.save()
        
        messages.success(request, _("Votre profil a été mis Ã  jour avec succès."))
        
    except ValueError as e:
        messages.error(request, _("Erreur de format de date. Veuillez utiliser le format AAAA-MM-JJ."))
    except Exception as e:
        messages.error(request, _("Erreur lors de la mise Ã  jour du profil: {}").format(str(e)))
    
    return redirect('competitions:practitioner_profile')


@login_required
def activities(request):
    """Vue des activités et entraÃ®nements du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            # Si aucun pratiquant n'existe, essayons de chercher par l'email ou créer un nouveau profil
            practitioner = Practitioner.objects.filter(email=request.user.email).first()
            if practitioner and not practitioner.user:
                # Associer le pratiquant Ã  l'utilisateur
                practitioner.user = request.user
                practitioner.save()
            elif not practitioner:
                # Créer un nouveau pratiquant si aucun n'existe
                messages.warning(request, _("Création automatique d'un profil pratiquant."))
                practitioner = Practitioner.objects.create(
                    user=request.user,
                    first_name=request.user.first_name or 'Prénom',
                    last_name=request.user.last_name or 'Nom',
                    email=request.user.email,
                    birth_date=timezone.now().date() - timedelta(days=365*25),  # Ã‚ge par défaut 25 ans
                    gender='M',  # Par défaut
                    nationality='FR'  # Par défaut
                )
                messages.success(request, _("Profil pratiquant créé avec succès. Veuillez compléter vos informations."))
    except Exception as e:
        messages.error(request, _(f"Erreur lors de la récupération du profil: {str(e)}"))
        return redirect('welcome')
    
    # Récupérer les disciplines pratiquées
    disciplines = practitioner.disciplines.all()
    
    # Ici, on pourrait ajouter plus tard un modèle TrainingSession pour suivre les entraÃ®nements
    # Pour l'instant, on affiche juste les disciplines
    
    context = {
        'practitioner': practitioner,
        'disciplines': disciplines,
        'active_page': 'activities'
    }
    
    return render(request, 'competitions/practitioner/activities.html', context)


@login_required
def grades(request):
    """Vue de l'évolution des grades du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer tous les grades actuels par discipline
    current_grades = PractitionerGrade.objects.filter(
        practitioner=practitioner,
        is_current=True
    ).select_related('grade', 'discipline')
    
    # Récupérer l'historique des grades
    grade_history = PractitionerGrade.objects.filter(
        practitioner=practitioner
    ).select_related('grade', 'discipline').order_by('-date_obtained')
    
    # Récupérer les prochains grades possibles par discipline
    next_grades = {}
    for current_grade in current_grades:
        if current_grade.grade:
            next_grade = Grade.objects.filter(
                system=current_grade.grade.system,
                order__gt=current_grade.grade.order
            ).order_by('order').first()
            if next_grade:
                next_grades[current_grade.discipline.id] = next_grade
    
    context = {
        'practitioner': practitioner,
        'current_grades': current_grades,
        'grade_history': grade_history,
        'next_grades': next_grades,
        'active_page': 'grades'
    }
    
    return render(request, 'competitions/practitioner/grades.html', context)


@login_required
def competitions(request):
    """Vue des compétitions du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    discipline_filter = request.GET.get('discipline', 'all')
    
    # RequÃªte de base
    registrations = CompetitionRegistration.objects.filter(practitioner=practitioner)
    
    # Appliquer les filtres
    if status_filter == 'upcoming':
        registrations = registrations.filter(
            competition__start_date__gte=timezone.now().date()
        )
    elif status_filter == 'past':
        registrations = registrations.filter(
            competition__start_date__lt=timezone.now().date()
        )
    
    if discipline_filter != 'all':
        registrations = registrations.filter(
            competition__disciplines__id=discipline_filter
        )
    
    # Tri et sélection des relations
    registrations = registrations.select_related(
        'competition', 'category'
    ).order_by('-competition__start_date')
    
    # Récupérer les résultats pour les compétitions passées
    results = {}
    for registration in registrations:
        if registration.competition.end_date and registration.competition.end_date < timezone.now().date():
            result = CompetitionResult.objects.filter(
                practitioner=practitioner,
                competition=registration.competition,
                category=registration.category
            ).first()
            if result:
                results[registration.id] = result
    
    # Disciplines pour le filtre
    disciplines = practitioner.disciplines.all()
    
    context = {
        'practitioner': practitioner,
        'registrations': registrations,
        'results': results,
        'disciplines': disciplines,
        'status_filter': status_filter,
        'discipline_filter': discipline_filter,
        'active_page': 'competitions'
    }
    
    return render(request, 'competitions/practitioner/competitions.html', context)


@login_required
def memberships(request):
    """Vue des cotisations et paiements du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer toutes les adhésions
    memberships = Membership.objects.filter(
        practitioner=practitioner
    ).order_by('-start_date')
    
    # Adhésion active actuelle
    current_membership = memberships.filter(
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    # Calculer le statut de la cotisation
    membership_status = 'inactive'
    days_remaining = 0
    
    if current_membership:
        days_remaining = (current_membership.end_date - timezone.now().date()).days
        if days_remaining > 60:
            membership_status = 'active'
        elif days_remaining > 0:
            membership_status = 'expiring'
        else:
            membership_status = 'expired'
    
    # Récupérer les paiements associés (si disponibles)
    # Note: Il faudrait intégrer avec le module finances si disponible
    payments = []  # Ã€ implémenter avec le module finances
    
    context = {
        'practitioner': practitioner,
        'memberships': memberships,
        'current_membership': current_membership,
        'membership_status': membership_status,
        'days_remaining': days_remaining,
        'payments': payments,
        'active_page': 'memberships'
    }
    
    return render(request, 'competitions/practitioner/memberships.html', context)


@login_required
def statistics(request):
    """Vue des statistiques personnelles du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Statistiques par année
    current_year = timezone.now().year
    yearly_stats = []
    
    for year in range(current_year - 4, current_year + 1):
        year_registrations = CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition__start_date__year=year
        )
        
        year_results = CompetitionResult.objects.filter(
            practitioner=practitioner,
            competition__start_date__year=year
        )
        
        year_data = {
            'year': year,
            'competitions': year_registrations.count(),
            'podiums': year_results.filter(rank__lte=3).count(),
            'gold': year_results.filter(rank=1).count(),
            'silver': year_results.filter(rank=2).count(),
            'bronze': year_results.filter(rank=3).count(),
        }
        yearly_stats.append(year_data)
    
    # Statistiques par discipline
    discipline_stats = []
    for discipline in practitioner.disciplines.all():
        disc_registrations = CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition__discipline=discipline
        )
        
        disc_results = CompetitionResult.objects.filter(
            practitioner=practitioner,
            competition__discipline=discipline
        )
        
        disc_data = {
            'discipline': discipline,
            'competitions': disc_registrations.count(),
            'podiums': disc_results.filter(rank__lte=3).count(),
            'average_rank': disc_results.aggregate(avg=Avg('rank'))['avg'] or 0
        }
        discipline_stats.append(disc_data)
    
    # Ã‰volution du classement
    rank_evolution = CompetitionResult.objects.filter(
        practitioner=practitioner
    ).select_related('competition', 'category').order_by('competition__start_date')
    
    context = {
        'practitioner': practitioner,
        'yearly_stats': yearly_stats,
        'discipline_stats': discipline_stats,
        'rank_evolution': rank_evolution,
        'active_page': 'statistics'
    }
    
    return render(request, 'competitions/practitioner/statistics.html', context)


@login_required  
def grade_progress(request):
    """Vue pour afficher la progression dans les grades du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer tous les grades actuels par discipline
    current_grades = PractitionerGrade.objects.filter(
        practitioner=practitioner,
        is_current=True
    ).select_related('grade', 'discipline')
    
    # Calculer la progression pour chaque discipline
    progressions = []
    for current_grade in current_grades:
        if current_grade.grade:
            # Récupérer le prochain grade dans le système
            next_grade = Grade.objects.filter(
                system=current_grade.grade.system,
                order__gt=current_grade.grade.order
            ).order_by('order').first()
            
            if next_grade:
                # Calculer les points d'expérience ou critères pour le prochain grade
                # Ceci est une estimation basée sur les compétitions et résultats
                total_competitions = CompetitionRegistration.objects.filter(
                    practitioner=practitioner,
                    competition__discipline=current_grade.discipline,
                    competition__end_date__gt=current_grade.date_obtained
                ).count()
                
                total_wins = CompetitionResult.objects.filter(
                    practitioner=practitioner,
                    competition__discipline=current_grade.discipline,
                    rank=1,
                    competition__end_date__gt=current_grade.date_obtained
                ).count()
                
                # Calcul approximatif de la progression
                required_competitions = 10  # Exemple: 10 compétitions pour un grade
                required_wins = 3  # Exemple: 3 victoires pour un grade
                
                competition_progress = min(100, (total_competitions / required_competitions) * 100)
                win_progress = min(100, (total_wins / required_wins) * 100)
                overall_progress = (competition_progress + win_progress) / 2
                
                progressions.append({
                    'discipline': current_grade.discipline,
                    'current_grade': current_grade.grade,
                    'next_grade': next_grade,
                    'date_obtained': current_grade.date_obtained,
                    'competitions': total_competitions,
                    'wins': total_wins,
                    'progress': int(overall_progress),
                    'competition_progress': int(competition_progress),
                    'win_progress': int(win_progress)
                })
            else:
                # Grade maximum atteint
                progressions.append({
                    'discipline': current_grade.discipline,
                    'current_grade': current_grade.grade,
                    'next_grade': None,
                    'date_obtained': current_grade.date_obtained,
                    'is_max_grade': True
                })
    
    # Récupérer l'historique complet des grades
    grade_history = PractitionerGrade.objects.filter(
        practitioner=practitioner
    ).select_related('grade', 'discipline').order_by('-date_obtained')
    
    context = {
        'practitioner': practitioner,
        'progressions': progressions,
        'grade_history': grade_history,
        'active_page': 'grade_progress'
    }
    
    return render(request, 'competitions/practitioner/grade_progress.html', context)


@login_required
def competition_detail(request, competition_id):
    """Vue pour afficher les détails d'une compétition spécifique pour le pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le pratiquant est inscrit Ã  cette compétition
    registration = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition=competition
    ).select_related('category').first()
    
    # Récupérer les résultats si la compétition est terminée
    results = None
    if competition.end_date and competition.end_date < timezone.now().date():
        results = CompetitionResult.objects.filter(
            practitioner=practitioner,
            competition=competition
        ).select_related('category')
    
    # Récupérer les catégories disponibles pour cette compétition
    categories = CategoryTemplate.objects.filter(
        competitions=competition
    ).distinct()
    
    # Vérifier si le pratiquant peut s'inscrire
    can_register = False
    registration_closed_reason = None
    
    if not registration:
        # Vérifier les conditions d'inscription
        if competition.start_date < timezone.now().date():
            registration_closed_reason = _("Les inscriptions sont fermées (compétition déjÃ  commencée)")
        elif competition.registration_end_date and competition.registration_end_date < timezone.now().date():
            registration_closed_reason = _("La date limite d'inscription est dépassée")
        else:
            # Vérifier si le pratiquant a un certificat médical valide
            if not practitioner.medical_certificate_date:
                registration_closed_reason = _("Certificat médical requis")
            else:
                medical_cert_expiry = practitioner.medical_certificate_date + timedelta(days=365)
                if medical_cert_expiry < competition.start_date:
                    registration_closed_reason = _("Certificat médical expiré")
                else:
                    # Vérifier si le pratiquant a une adhésion valide
                    active_membership = Membership.objects.filter(
                        practitioner=practitioner,
                        status='active',
                        end_date__gte=competition.start_date
                    ).exists()
                    
                    if not active_membership:
                        registration_closed_reason = _("Adhésion active requise")
                    else:
                        can_register = True
    
    # Récupérer d'autres participants dans la mÃªme catégorie (si inscrit)
    category_participants = []
    if registration:
        category_participants = CompetitionRegistration.objects.filter(
            competition=competition,
            category=registration.category,
            status='confirmed'
        ).select_related('practitioner').exclude(practitioner=practitioner)[:10]
    
    # Statistiques de la compétition
    total_participants = CompetitionRegistration.objects.filter(
        competition=competition,
        status='confirmed'
    ).count()
    
    context = {
        'practitioner': practitioner,
        'competition': competition,
        'registration': registration,
        'results': results,
        'categories': categories,
        'can_register': can_register,
        'registration_closed_reason': registration_closed_reason,
        'category_participants': category_participants,
        'total_participants': total_participants,
        'active_page': 'competitions'
    }
    
    return render(request, 'competitions/practitioner/competition_detail.html', context)


