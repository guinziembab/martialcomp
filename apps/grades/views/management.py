from django.core.exceptions import PermissionDenied
"""
Module pour la gestion des grades individuels des pratiquants.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
import json

from apps.competitions.models import Practitioner, Discipline, Club
from apps.grades.utils import get_user_club, get_grades_for_discipline
from django.views.decorators.http import require_POST
from apps.competitions.utils.decorators import club_required
from django.contrib.auth import get_user_model
from apps.grades.models import Grade, GradeCategory, PractitionerGrade, GradeActionLog
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
User = get_user_model()


@login_required
def update_practitioner_grade(request, practitioner_id):
    """
    Permet de mettre Ã  jour le grade d'un pratiquant.
    """
    # Import nécessaire
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club  
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
    
    # Récupérer les disciplines du pratiquant
    practitioner_disciplines = practitioner.disciplines.all()
    
    # Récupérer les grades pour chaque discipline
    discipline_grades = {}
    for discipline in practitioner_disciplines:
        grades = get_grades_for_discipline(discipline)
        grades_data = []
        
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'category': grade.category.name if hasattr(grade, 'category') and grade.category else "",
                'level': grade.level
            })
        
        discipline_grades[str(discipline.id)] = grades_data
    
    # Récupérer la liste des responsables de club et de fédération
    try:
        # Essai avec les rÃ´les spécifiques
        club_managers = User.objects.filter(profile__role='club_manager').select_related('profile')
        federation_admins = User.objects.filter(profile__role='federation_admin').select_related('profile')
        
        # Combiner les deux listes
        certifiers = list(club_managers) + list(federation_admins)
        
        # Si aucun certificateur trouvé, utiliser une approche alternative
        if not certifiers:
            # Récupérer tous les utilisateurs avec un profil 
            certifiers = list(User.objects.filter(profile__isnull=False))
    except Exception as e:
        # En cas d'erreur, utiliser tous les utilisateurs comme fallback
        certifiers = list(get_organization_queryset(User, self.request.user))
        print(f"Erreur lors de la récupération des certificateurs: {str(e)}")
    
    # Récupérer le grade actuel correctement
    current_grade = None
    try:
        # Vérifier si des grades sont définis comme actuels pour ce pratiquant
        current_grades = PractitionerGrade.objects.filter(
            practitioner=practitioner,
            is_current=True
        ).select_related('grade', 'discipline').order_by('-date_obtained')
        
        if current_grades.exists():
            current_grade = current_grades.first()
    except Exception as e:
        print(f"Erreur lors de la récupération du grade actuel: {str(e)}")
    
    if request.method == 'POST':
        # Débogage - afficher toutes les valeurs POST pour vérifier ce qui est soumis
        print("Valeurs POST reçues:", request.POST)
        
        grade_id = request.POST.get('grade')
        discipline_id = request.POST.get('discipline')
        date_obtained = request.POST.get('date_obtained')
        awarded_by = request.POST.get('awarded_by', '')
        location = request.POST.get('location', '')
        certificate_number = request.POST.get('certificate_number', '')
        notes = request.POST.get('notes', '')
        is_current = request.POST.get('is_current') == 'on'
        
        print(f"Traitement du formulaire: grade_id={grade_id}, discipline_id={discipline_id}, is_current={is_current}")
        
        try:
            with transaction.atomic():
                # Vérifier que les valeurs essentielles sont bien présentes
                if not grade_id:
                    raise ValueError(_("Aucun grade sélectionné."))
                    
                if not discipline_id:
                    raise ValueError(_("Aucune discipline sélectionnée."))
                
                # Récupérer le grade sélectionné
                grade = get_object_or_404(Grade, id=grade_id)
                
                # Récupérer la discipline
                discipline = get_object_or_404(Discipline, id=discipline_id)
                
                # Mettre Ã  jour le grade principal du pratiquant
                practitioner.grade = grade
                practitioner.save(update_fields=['grade'])
                
                # Créer l'entrée d'historique
                grade_record = PractitionerGrade.objects.create(
                    practitioner=practitioner,
                    grade=grade,
                    discipline=discipline,
                    date_obtained=date_obtained,
                    awarded_by=awarded_by,
                    location=location,
                    certificate_number=certificate_number,
                    notes=notes,
                    is_current=is_current
                )
                
                # Si ce grade est défini comme courant, désactiver les autres grades courants pour cette discipline
                if is_current:
                    PractitionerGrade.objects.filter(
                        practitioner=practitioner,
                        discipline=discipline,
                        is_current=True
                    ).exclude(id=grade_record.id).update(is_current=False)
                
                messages.success(request, _("Le grade de {} a été mis Ã  jour avec succès.").format(practitioner.full_name))
                
                # Redirection explicite
                return redirect('grades:practitioner_history', practitioner_id=practitioner.id)
                
        except Exception as e:
            # Message d'erreur plus explicite
            error_msg = str(e)
            print(f"ERREUR lors de la mise Ã  jour du grade: {error_msg}")
            messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour du grade: {}").format(error_msg))
    # Ajouter la date actuelle pour le formulaire
    today = timezone.now().date()
    
    return render(request, 'grades/update_grade.html', {
        'practitioner': practitioner,
        'club': club,
        'disciplines': practitioner_disciplines,
        'discipline_grades': json.dumps(discipline_grades),
        'current_grade': current_grade,
        'today': today,
        'next': request.GET.get('next', ''),
        'certifiers': certifiers,  # Ajouter les certificateurs au contexte
    })

@login_required
def promote_practitioner(request, practitioner_id):
    """
    Permet de promouvoir un pratiquant au grade suivant dans sa discipline.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club  
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
    
    if request.method == 'POST':
        discipline_id = request.POST.get('discipline')
        notes = request.POST.get('notes', _('Promotion au grade suivant'))
        
        # Valider qu'une discipline est sélectionnée
        if not discipline_id:
            messages.error(request, _("Veuillez sélectionner une discipline."))
            return redirect('grades:update_practitioner_grade', practitioner_id=practitioner.id)
        
        try:
            # Récupérer la discipline
            discipline = get_object_or_404(Discipline, id=discipline_id)
            
            # Récupérer le grade actuel du pratiquant
            current_grade = practitioner.grade
            
            # Récupérer tous les grades de la discipline
            grades = get_grades_for_discipline(discipline).order_by('level')
            
            # Trouver le grade suivant
            next_grade = None
            
            if current_grade:
                found_current = False
                for grade in grades:
                    if found_current:
                        next_grade = grade
                        break
                    if grade.id == current_grade.id:
                        found_current = True
            else:
                # Si pas de grade actuel, prendre le premier
                if grades.exists():
                    next_grade = grades.first()
            
            if next_grade:
                with transaction.atomic():
                    # Mettre Ã  jour le grade principal
                    practitioner.grade = next_grade
                    practitioner.save(update_fields=['grade'])
                    
                    # Créer l'entrée d'historique
                    PractitionerGrade.objects.create(
                        practitioner=practitioner,
                        grade=next_grade,
                        discipline=discipline,
                        date_obtained=timezone.now().date(),  # Changé obtained_date en date_obtained
                        awarded_by=request.user.get_full_name() or request.user.username,  # Changé awarded_by pour stocker une chaÃ®ne
                        notes=notes
                    )
                    
                    messages.success(request, 
                        _("{} a été promu au grade de {}.").format(
                            practitioner.full_name, 
                            next_grade.name
                        )
                    )
            else:
                messages.warning(request, _("Aucun grade supérieur trouvé pour cette discipline."))
            
            return redirect('grades:practitioner_history', practitioner_id=practitioner.id)
            
        except Exception as e:
            messages.error(request, _("Une erreur est survenue lors de la promotion: {}").format(str(e)))
            return redirect('grades:update_practitioner_grade', practitioner_id=practitioner.id)
    
    # Si accès direct en GET, rediriger vers la page de mise Ã  jour
    return redirect('grades:update_practitioner_grade', practitioner_id=practitioner.id)

@login_required
@club_required
def revoke_grade(request, grade_id):
    """Retire un grade attribué Ã  un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le grade
    grade = get_object_or_404(PractitionerGrade, pk=grade_id, practitioner__organization=organization)
    practitioner = grade.practitioner
    discipline = grade.discipline
    
    if request.method == 'POST':
        # Vérifier les informations du formulaire
        revoke_reason = request.POST.get('revoke_reason', '').strip()
        confirm_revoke = request.POST.get('confirm_revoke') == 'on'
        set_previous_grade = request.POST.get('set_previous_grade') == 'on'
        
        if not revoke_reason or not confirm_revoke:
            messages.error(request, _("Veuillez remplir tous les champs obligatoires et confirmer le retrait."))
            return render(request, 'grades/revoke_grade.html', {'grade': grade})
        
        # Trouver le grade précédent pour ce pratiquant dans cette discipline
        previous_grade = None
        if set_previous_grade:
            previous_grade = PractitionerGrade.objects.filter(
                practitioner=practitioner,
                discipline=discipline,
                date_obtained__lt=grade.date_obtained
            ).order_by('-date_obtained').first()
        
        # Effectuer les modifications dans une transaction
        with transaction.atomic():
            # Marquer le grade comme non courant et ajouter la raison du retrait
            grade.is_current = False
            grade.notes = f"{grade.notes}\n\nGrade retiré le {timezone.now().strftime('%d/%m/%Y')}. Raison: {revoke_reason}"
            grade.save()
            
            # Si demandé, activer le grade précédent comme grade courant
            if previous_grade:
                previous_grade.is_current = True
                previous_grade.save()
                
                # Mise Ã  jour du grade actuel du pratiquant
                practitioner.grade = previous_grade.grade.name
                practitioner.save()
            elif grade.is_current:
                # Si c'était le grade actuel, effacer le grade du pratiquant
                practitioner.grade = ""
                practitioner.save()
            
            # Enregistrer l'action dans les logs (facultatif)
            if hasattr(request, 'user') and request.user:
                admin_note = f"Grade retiré par {request.user.get_full_name() or request.user.username}"
                grade.notes += f"\n{admin_note}"
                grade.save()
        
        messages.success(request, _("Le grade a été retiré avec succès."))
        return redirect('grades:practitioner_grades', practitioner_id=practitioner.id)
    
    # Rendu du formulaire pour la méthode GET
    return render(request, 'grades/revoke_grade.html', {'grade': grade})
    
@login_required
def club_management(request):
    """
    Vue principale pour la gestion des grades au niveau du club.
    Permet de visualiser les grades par discipline et de gérer les attributions.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les disciplines du club
    club_disciplines = club.disciplines.all()
    
    # Récupérer tous les pratiquants du club via l'organisation
    practitioners = Practitioner.objects.filter(organization=organization).order_by('last_name', 'first_name')
    
    # Récupérer les catégories de grade pour les disciplines du club
    grade_categories = GradeCategory.objects.filter(discipline__in=club_disciplines).order_by('discipline', 'order')
    
    # Récupérer les grades pour les disciplines du club
    grades = Grade.objects.filter(discipline__in=club_disciplines).order_by('discipline', 'level')
    
    # Récupérer les attributions récentes de grades
    recent_awards = PractitionerGrade.objects.filter(
        practitioner__organization=organization
    ).select_related('practitioner', 'grade', 'discipline').order_by('-date_obtained')[:10]
    
    # Attacher directement les grades Ã  chaque discipline
    for discipline in club_disciplines:
        # Récupérer les grades de cette discipline
        discipline.grades_list = [
            {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level,
                'color_code': grade.color_code,
                'category': grade.category.name if grade.category else None,
                'category_id': grade.category_id if grade.category else None
            } 
            for grade in grades.filter(discipline=discipline)
        ]
        
        # Compter les pratiquants pour cette discipline
        discipline.practitioners_count = practitioners.filter(disciplines=discipline).count()
    
    # Aujourd'hui pour le formulaire d'attribution de grades
    today = timezone.now().date()
    
    context = {
        'club': club,
        'organization': organization,
        'disciplines': club_disciplines,
        'practitioners': practitioners,
        'grade_categories': grade_categories,
        'grades': grades,
        'recent_awards': recent_awards,
        'today': today
    }
    
    return render(request, 'grades/club_management.html', context)
    
@login_required
def practitioner_history(request, practitioner_id):
    """
    Affiche l'historique des grades d'un pratiquant.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club  
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
    
    # Récupérer l'historique des grades
    grade_history = PractitionerGrade.objects.filter(
        practitioner=practitioner
    ).order_by('-date_obtained')
    
    # Regrouper par discipline
    history_by_discipline = {}
    
    for entry in grade_history:
        discipline_id = entry.discipline_id
        if discipline_id not in history_by_discipline:
            history_by_discipline[discipline_id] = {
                'name': entry.discipline.name,
                'entries': []
            }
        
        history_by_discipline[discipline_id]['entries'].append(entry)
    
    return render(request, 'grades/practitioner_history.html', {
        'practitioner': practitioner,
        'history_by_discipline': history_by_discipline,
        'club': club
    })
    
@login_required
@club_required
@require_POST
def set_current_grade(request, grade_id):
    """
    Définit un grade comme grade actuel pour un pratiquant dans une discipline spécifique.
    Cette fonction désactive les autres grades actifs pour la mÃªme discipline.
    """
    # Récupérer le club de l'utilisateur
    club = get_club_for_user(request.user)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour effectuer cette action."))
        return redirect('grades:dashboard')
    
    try:
        # Récupérer le grade
        grade = PractitionerGrade.objects.get(pk=grade_id)
        
        # Récupérer l'organisation associée au club
        organization = club.organization or club.as_organization
        
        # Vérifier que le pratiquant appartient bien Ã  l'organisation de l'utilisateur
        if grade.practitioner.organization != organization:
            messages.error(request, _("Vous n'avez pas l'autorisation de gérer ce pratiquant."))
            return redirect('grades:dashboard')
        
        practitioner = grade.practitioner
        discipline = grade.discipline
        
        # Désactiver tous les autres grades comme grade actuel pour cette discipline
        with transaction.atomic():
            PractitionerGrade.objects.filter(
                practitioner=practitioner,
                discipline=discipline,
                is_current=True
            ).exclude(pk=grade_id).update(is_current=False)
            
            # Définir ce grade comme grade actuel
            grade.is_current = True
            grade.save()
            
            # Mettre Ã  jour le grade principal du pratiquant
            # Si votre modèle Practitioner a un champ 'grade'
            if hasattr(practitioner, 'grade'):
                practitioner.grade = grade.grade.name
                practitioner.save()
                
            # Enregistrer l'action dans l'historique (si applicable)
            log_grade_action(
                practitioner=practitioner,
                user=request.user,
                action_type="set_current",
                grade=grade.grade,
                notes=f"Grade {grade.grade.name} défini comme grade actuel"
            )
        
        messages.success(request, _("Le grade a été défini comme grade actuel avec succès."))
    except PractitionerGrade.DoesNotExist:
        messages.error(request, _("Grade introuvable."))
    except Exception as e:
        messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
    
    # Rediriger vers la page d'historique des grades du pratiquant
    return redirect('grades:practitioner_history', practitioner_id=practitioner.id)

# Ajoutez également cette fonction utilitaire si elle est utilisée et non définie ailleurs
def get_club_for_user(user):
    """
    Récupère le club associé Ã  un utilisateur.
    """
    if hasattr(user, 'club') and user.club:
        return user.club
    
    # Vérifier si l'utilisateur est propriétaire d'un club
    from apps.competitions.models import Club
    return Club.objects.filter(owner=user).first()

# Importez également cette fonction si elle est utilisée dans votre code
def log_grade_action(practitioner, user, action_type, grade, notes=""):
    """
    Enregistre une action sur un grade dans l'historique.
    """
    # Implémentez cette fonction selon vos besoins, ou importez-la si elle existe ailleurs
    # Cette implémentation est juste un exemple
    
    try:
        GradeActionLog.objects.create(
            practitioner=practitioner,
            user=user,
            action_type=action_type,
            grade=grade,
            notes=notes
        )
    except Exception:
        # Gérer silencieusement les erreurs, ou logger selon votre configuration
        pass

