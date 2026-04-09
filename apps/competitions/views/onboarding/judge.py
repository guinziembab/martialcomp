from django.core.exceptions import PermissionDenied
import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...forms.judges import JudgeProfileForm
from ...models import Judge, Practitioner
from apps.competitions.models import Discipline
from apps.grades.models import GradeCategory, Grade
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def handle_judge_profile(request):
    """
    Gestion du profil juge dans le processus d'onboarding.
    Cette vue permet de créer ou modifier un profil de juge pour l'utilisateur connecté.
    """
    # Vérifier si l'utilisateur a le rÃ´le approprié via la propriété profile
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'judge':
        messages.error(request, _("Accès non autorisé. Vous devez Ãªtre juge."))
        return redirect('competitions:onboarding:role_selection')
    
    # Vérifier si le juge n'a pas déjÃ  un profil
    existing_judge = None
    existing_practitioner = None
    
    try:
        # Vérifier si l'utilisateur a déjÃ  un praticien associé
        existing_practitioner = Practitioner.objects.filter(user=request.user).first()
        
        # Vérifier si l'utilisateur a déjÃ  un profil juge
        if existing_practitioner:
            existing_judge = Judge.objects.filter(practitioner=existing_practitioner).first()
        
        if existing_judge:
            messages.warning(request, _("Vous avez déjÃ  un profil de juge."))
            request.session['onboarding_step'] = 'final_setup'
            return redirect('competitions:onboarding:final_setup')
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification du profil juge existant: {str(e)}")
        # Continuer mÃªme si une erreur survient lors de la vérification
    
    if request.method == 'POST':
        # Si un juge existe déjÃ , nous l'utilisons comme instance
        instance = existing_judge if existing_judge else None
        
        # Créer le formulaire avec les données POST et l'utilisateur actuel
        form = JudgeProfileForm(request.POST, instance=instance, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Traitement du grade - récupérer l'objet Grade
                    selected_grade_id = form.cleaned_data.get('selected_grade_id')
                    grade_obj = None
                    
                    if selected_grade_id:
                        try:
                            grade_obj = Grade.objects.get(id=selected_grade_id)
                        except (Grade.DoesNotExist, ValueError):
                            # Récupérer un grade par défaut ou créer un nouveau
                            grade_obj = _get_default_grade()
                    else:
                        # Récupérer un grade par défaut si aucun grade sélectionné
                        grade_obj = _get_default_grade()
                    
                    # Si le pratiquant n'existe pas encore, le créer
                    if not existing_practitioner:
                        # Récupérer un objet Grade valide
                        default_grade = _get_default_grade()
                        
                        existing_practitioner = Practitioner.objects.create(
                            user=request.user,
                            first_name=form.cleaned_data.get('first_name', ''),
                            last_name=form.cleaned_data.get('last_name', ''),
                            birth_date=form.cleaned_data.get('birth_date'),
                            grade=grade_obj or default_grade,  # Utiliser l'objet Grade
                            grade_text=form.cleaned_data.get('grade', '')  # Stocker le texte si fourni
                        )
                    else:
                        # Mettre Ã  jour les données du pratiquant existant
                        existing_practitioner.first_name = form.cleaned_data.get('first_name', existing_practitioner.first_name)
                        existing_practitioner.last_name = form.cleaned_data.get('last_name', existing_practitioner.last_name)
                        existing_practitioner.email = form.cleaned_data.get('email', existing_practitioner.email)
                        if form.cleaned_data.get('birth_date'):
                            existing_practitioner.birth_date = form.cleaned_data.get('birth_date')
                        existing_practitioner.grade = grade_obj  # Utiliser l'objet Grade
                        existing_practitioner.save()
                    
                    # Créer ou mettre Ã  jour le juge
                    judge = form.save(commit=False)
                    judge.practitioner = existing_practitioner
                    judge.save()
                    
                    # Gérer les disciplines
                    if 'disciplines' in form.cleaned_data and form.cleaned_data['disciplines']:
                        # Si des disciplines sont sélectionnées, les associer au praticien
                        if hasattr(existing_practitioner, 'disciplines'):
                            existing_practitioner.disciplines.set(form.cleaned_data['disciplines'])
                        # Si le juge a aussi un champ disciplines, les associer également
                        elif hasattr(judge, 'disciplines'):
                            judge.disciplines.set(form.cleaned_data['disciplines'])
                    
                    # Gérer les autres champs ManyToMany du formulaire
                    form.save_m2m()
                    
                    # Mettre Ã  jour l'étape d'onboarding
                    if hasattr(request.user, 'profile'):
                        request.user.profile.onboarding_completed = True
                        request.user.profile.onboarding_step = 'final_setup'
                        request.user.profile.save()
                    
                    request.session['onboarding_step'] = 'final_setup'
                    
                    messages.success(request, _("Profil de juge créé avec succès!"))
                    return redirect('competitions:onboarding:final_setup')
            except ValueError as ve:
                # Gérer spécifiquement les erreurs de validation
                logger.warning(f"Erreur de validation lors de la création du profil juge: {str(ve)}")
                messages.error(request, str(ve))
            except Exception as e:
                logger.error(f"Erreur lors de la création/mise Ã  jour du profil juge: {str(e)}")
                logger.error(f"Données du formulaire: {form.cleaned_data if form.is_valid() else 'Formulaire invalide'}")
                logger.error(f"Erreurs du formulaire: {form.errors}")
                messages.error(request, _("Une erreur est survenue lors de l'enregistrement de votre profil. Détails: ") + str(e))
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Initialiser le formulaire avec les données existantes ou les données de l'utilisateur
        initial_data = {
            'email': request.user.email,
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or ''
        }
        
        form = JudgeProfileForm(instance=existing_judge, initial=initial_data, user=request.user)
    
    # Récupérer toutes les disciplines actives
    disciplines = Discipline.objects.filter(is_active=True)
    
    # Préparer les données des grades pour JavaScript
    grades_by_discipline = {}
    try:
        # Pour chaque discipline, récupérer ses grades associés
        for discipline in disciplines:
            # Récupérer directement les grades de cette discipline
            grades = Grade.objects.filter(discipline=discipline, is_active=True).order_by('level', 'order')
            discipline_grades = []
            
            for grade in grades:
                discipline_grades.append({
                    'id': grade.id,
                    'name': str(grade.name),
                    'category': str(grade.category.name) if grade.category else str(_('Non catégorisé')),
                    'level': grade.level
                })
            
            if discipline_grades:
                grades_by_discipline[str(discipline.id)] = discipline_grades
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des grades: {str(e)}")
    
    return render(request, 'competitions/onboarding/judge_profile.html', {
        'form': form,
        'step': 'judge_profile',
        'current_step': 'judge_profile',
        'disciplines': disciplines,
        'grades_by_discipline': json.dumps(grades_by_discipline)
    })

def _get_default_grade(discipline=None):
    """
    Fonction utilitaire pour récupérer ou créer un grade par défaut.

    Args:
        discipline: Discipline spécifique à utiliser (optionnel).
                   Si None, on cherche un grade générique existant sans en créer un nouveau
                   avec une discipline par défaut (évite l'assignation automatique d'AIKIDO).
    """
    # Essayer de récupérer un grade générique ou de base
    default_grade = Grade.objects.filter(name__icontains="non spécifié").first()

    if not default_grade:
        # Prendre n'importe quel grade existant avec le niveau le plus bas
        default_grade = Grade.objects.filter(is_active=True).order_by('level').first()

        if not default_grade:
            # Si une discipline est fournie explicitement, créer le grade avec cette discipline
            if discipline:
                try:
                    # Chercher une catégorie existante ou en créer une
                    category = GradeCategory.objects.filter(discipline=discipline).first()
                    if not category:
                        category = GradeCategory.objects.create(
                            name="Catégorie générique",
                            discipline=discipline
                        )

                    # Créer un grade par défaut avec la discipline fournie
                    default_grade = Grade.objects.create(
                        name="Non spécifié",
                        discipline=discipline,
                        category=category,
                        level=0,
                        order=0
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de la création d'un grade par défaut: {str(e)}")
                    return None
            else:
                # IMPORTANT: Ne PAS créer automatiquement un grade avec une discipline par défaut
                # Cela évite l'assignation automatique d'AIKIDO ou autre première discipline
                logger.warning("Aucun grade par défaut trouvé et aucune discipline spécifiée.")
                return None

    return default_grade

@login_required
def view_judge_profile(request):
    """
    Affichage du profil juge de l'utilisateur connecté.
    Cette vue permet Ã  un juge de consulter son profil après l'onboarding.
    """
    # Vérifier si l'utilisateur a le rÃ´le approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'judge':
        messages.error(request, _("Accès non autorisé. Vous devez Ãªtre juge."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé Ã  l'utilisateur
        practitioner = get_object_or_404(Practitioner, user=request.user)
        
        # Récupérer le profil juge associé au praticien
        judge = get_object_or_404(Judge, practitioner=practitioner)
        
        # Récupérer les qualifications du juge (si applicable)
        qualifications = []
        if hasattr(judge, 'qualifications'):
            qualifications = judge.qualifications.all()
        
        context = {
            'judge': judge,
            'practitioner': practitioner,
            'qualifications': qualifications
        }
        return render(request, 'competitions/judges/profile.html', context)
    
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du profil juge: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la récupération de votre profil."))
        return redirect('competitions:dashboard')

@login_required
def edit_judge_profile(request):
    """
    Ã‰dition du profil juge de l'utilisateur connecté.
    Cette vue permet Ã  un juge de modifier son profil après l'onboarding.
    """
    # Vérifier si l'utilisateur a le rÃ´le approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'judge':
        messages.error(request, _("Accès non autorisé. Vous devez Ãªtre juge."))
        return redirect('competitions:dashboard')
    
    try:
        # Récupérer le praticien associé Ã  l'utilisateur
        practitioner = get_object_or_404(Practitioner, user=request.user)
        
        # Récupérer le profil juge associé au praticien
        judge = get_object_or_404(Judge, practitioner=practitioner)
        
        if request.method == 'POST':
            form = JudgeProfileForm(request.POST, instance=judge, user=request.user)
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Traitement du grade
                        grade_value = form.cleaned_data.get('grade', '')
                        
                        # Mettre Ã  jour les informations du praticien
                        practitioner.first_name = form.cleaned_data['first_name']
                        practitioner.last_name = form.cleaned_data['last_name']
                        
                        # S'assurer que birth_date est défini
                        if form.cleaned_data.get('birth_date'):
                            practitioner.birth_date = form.cleaned_data['birth_date']
                        elif not practitioner.birth_date:
                            raise ValueError(_("La date de naissance est requise pour le profil de juge."))
                        
                        # Mettre Ã  jour le grade
                        practitioner.grade = grade_value
                        practitioner.save()
                        
                        # Mettre Ã  jour le juge
                        judge = form.save()
                        
                        # Gérer les disciplines
                        if 'disciplines' in form.cleaned_data:
                            # Si des disciplines sont sélectionnées, les associer au praticien
                            if hasattr(practitioner, 'disciplines'):
                                practitioner.disciplines.set(form.cleaned_data['disciplines'])
                            # Si le juge a aussi un champ disciplines, les associer également
                            elif hasattr(judge, 'disciplines'):
                                judge.disciplines.set(form.cleaned_data['disciplines'])
                        
                        messages.success(request, _("Profil de juge mis Ã  jour avec succès!"))
                        return redirect('competitions:judges:profile')
                except ValueError as ve:
                    messages.error(request, str(ve))
                except Exception as e:
                    logger.error(f"Erreur lors de la mise Ã  jour du profil juge: {str(e)}")
                    messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour de votre profil."))
            else:
                # Afficher les erreurs de validation
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            # Préparer les données initiales
            initial_data = {
                'first_name': practitioner.first_name,
                'last_name': practitioner.last_name,
                'email': request.user.email,
                'birth_date': practitioner.birth_date,
                'grade': practitioner.grade
            }
            
            # Si le praticien a des disciplines
            if hasattr(practitioner, 'disciplines'):
                initial_data['disciplines'] = practitioner.disciplines.all()
            # Sinon, si le juge a des disciplines
            elif hasattr(judge, 'disciplines'):
                initial_data['disciplines'] = judge.disciplines.all()
            
            form = JudgeProfileForm(instance=judge, initial=initial_data, user=request.user)
        
        # Récupérer toutes les disciplines actives
        disciplines = Discipline.objects.filter(is_active=True)
        
        # Préparer les données des grades pour JavaScript
        grades_by_discipline = {}
        try:
            # Pour chaque discipline, récupérer ses grades associés
            for discipline in disciplines:
                # Récupérer directement les grades de cette discipline
                grades = Grade.objects.filter(discipline=discipline, is_active=True).order_by('level', 'order')
                discipline_grades = []
                
                for grade in grades:
                    discipline_grades.append({
                        'id': grade.id,
                        'name': str(grade.name),
                        'category': str(grade.category.name) if grade.category else str(_('Non catégorisé')),
                        'level': grade.level
                    })
                
                if discipline_grades:
                    grades_by_discipline[str(discipline.id)] = discipline_grades
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des grades: {str(e)}")
        
        return render(request, 'competitions/judges/edit_profile.html', {
            'form': form,
            'disciplines': disciplines,
            'grades_by_discipline': json.dumps(grades_by_discipline)
        })
    
    except Exception as e:
        logger.error(f"Erreur lors de l'édition du profil juge: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la récupération de votre profil."))
        return redirect('competitions:dashboard')

