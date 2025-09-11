from django.core.exceptions import PermissionDenied
"""
Module pour la gestion des grades des pratiquants.
Permet aux responsables de club de gérer l'historique des grades
et de mettre Ã  jour les grades des pratiquants.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
import logging
import json

# Import des modèles
from apps.competitions.models import Practitioner, Club, Discipline, CategoryGrade
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
try:
    # Import des nouveaux modèles de grade si disponibles
except ImportError:
    # Créer des classes de remplacement pour les cas oÃ¹ les modèles n'existent pas encore
    class Grade:
        pass
    class GradeSystem:
        pass
    class PractitionerGradeHistory:
        pass

# Création du logger
logger = logging.getLogger(__name__)

# Fonction pour récupérer le club de l'utilisateur
    from apps.grades.models import Grade, GradeCategory as GradeSystem, PractitionerGrade as PractitionerGradeHistory
def get_user_club(request):
    """
    Récupère le club associé Ã  l'utilisateur de manière uniforme.
    """
    # Si le club est déjÃ  dans la requÃªte (via le décorateur)
    if hasattr(request, 'club') and request.club:
        return request.club
    
    # Si l'utilisateur a un attribut club via le profile
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club') and request.user.profile.club:
        return request.user.profile.club
    
    # Si l'utilisateur est propriétaire d'un club
    club = Club.objects.filter(owner=request.user).first()
    if club:
        return club
    
    # Si l'utilisateur est administrateur d'un club
    if hasattr(request.user, 'club_admin_roles'):
        club_admin = request.user.club_admin_roles.first()
        if club_admin:
            return club_admin.club
    
    return None

@login_required
def grades_dashboard(request):
    """
    Tableau de bord principal pour la gestion des grades.
    Affiche une vue d'ensemble des pratiquants et de leurs grades actuels.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer tous les pratiquants du club
    practitioners = Practitioner.objects.filter(club=club)
    
    # Filtrer par discipline si demandé
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        try:
            discipline = Discipline.objects.get(id=discipline_id)
            practitioners = practitioners.filter(disciplines=discipline)
        except Discipline.DoesNotExist:
            pass
    
    # Filtrer par statut si demandé
    grade_status = request.GET.get('grade_status')
    if grade_status:
        if grade_status == 'with_grade':
            practitioners = practitioners.exclude(Q(grade__isnull=True) | Q(grade=''))
        elif grade_status == 'without_grade':
            practitioners = practitioners.filter(Q(grade__isnull=True) | Q(grade=''))
    
    # Filtrer par nom si recherche
    search_query = request.GET.get('q')
    if search_query:
        practitioners = practitioners.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(practitioners.order_by('last_name', 'first_name'), 20)  # 20 pratiquants par page
    page = request.GET.get('page')
    practitioners_page = paginator.get_page(page)
    
    # Récupérer les disciplines du club
    disciplines = Discipline.objects.filter(
        is_active=True
    ).order_by('name')
    
    return render(request, 'competitions/club/grades/dashboard.html', {
        'practitioners': practitioners_page,
        'club': club,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'selected_grade_status': grade_status,
        'search_query': search_query,
    })

@login_required
def practitioner_grade_history(request, practitioner_id):
    """
    Affiche l'historique des grades d'un pratiquant spécifique.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, club=club)
    
    # Essayer de récupérer l'historique des grades
    try:
        grade_history = PractitionerGradeHistory.objects.filter(
            practitioner=practitioner
        ).order_by('-attribution_date')
    except (ImportError, Exception):
        # Modèle non disponible, créer un historique fictif basé sur le grade actuel
        grade_history = []
        if practitioner.grade:
            grade_history = [{
                'grade': practitioner.grade,
                'attribution_date': practitioner.created_at or timezone.now(),
                'notes': _("Grade initial")
            }]
    
    # Récupérer les disciplines du pratiquant
    practitioner_disciplines = practitioner.disciplines.all()
    
    return render(request, 'competitions/club/grades/history.html', {
        'practitioner': practitioner,
        'grade_history': grade_history,
        'club': club,
        'disciplines': practitioner_disciplines,
    })

@login_required
def update_practitioner_grade(request, practitioner_id):
    """
    Permet de mettre Ã  jour le grade d'un pratiquant.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, club=club)
    
    # Récupérer les disciplines du pratiquant
    practitioner_disciplines = practitioner.disciplines.all()
    
    # Récupérer les grades pour chaque discipline
    discipline_grades = {}
    for discipline in practitioner_disciplines:
        try:
            # Essayer de récupérer avec le nouveau système
            systems = GradeSystem.objects.filter(discipline=discipline)
            default_system = systems.filter(is_default=True).first() or systems.first()
            
            if default_system:
                grades = []
                for category in default_system.categories.all():
                    for grade in category.grades.all():
                        grades.append({
                            'id': grade.id,
                            'name': grade.name,
                            'category': category.name
                        })
                discipline_grades[str(discipline.id)] = grades
            else:
                # Fallback Ã  l'ancien système
                grades = CategoryGrade.objects.filter(
                    discipline=discipline,
                    is_active=True
                ).order_by('order', 'nom')
                
                grade_list = []
                for grade_category in grades:
                    # Générer des grades Ã  partir des min/max
                    if grade_category.grade_min and grade_category.grade_max:
                        grade_list.append({
                            'id': f"cat_{grade_category.id}_{grade_category.grade_min}",
                            'name': grade_category.grade_min,
                            'category': grade_category.nom
                        })
                        if grade_category.grade_min != grade_category.grade_max:
                            grade_list.append({
                                'id': f"cat_{grade_category.id}_{grade_category.grade_max}",
                                'name': grade_category.grade_max,
                                'category': grade_category.nom
                            })
                
                discipline_grades[str(discipline.id)] = grade_list
        except Exception as e:
            # En cas d'erreur, utiliser des grades par défaut
            discipline_grades[str(discipline.id)] = [
                {'id': 'default_white', 'name': _('Ceinture Blanche'), 'category': _('Débutant')},
                {'id': 'default_yellow', 'name': _('Ceinture Jaune'), 'category': _('Débutant')},
                {'id': 'default_orange', 'name': _('Ceinture Orange'), 'category': _('Intermédiaire')},
                {'id': 'default_green', 'name': _('Ceinture Verte'), 'category': _('Intermédiaire')},
                {'id': 'default_blue', 'name': _('Ceinture Bleue'), 'category': _('Avancé')},
                {'id': 'default_brown', 'name': _('Ceinture Marron'), 'category': _('Avancé')},
                {'id': 'default_black', 'name': _('Ceinture Noire'), 'category': _('Expert')}
            ]
            logger.error(f"Erreur lors du chargement des grades pour {discipline}: {e}")
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        discipline_id = request.POST.get('discipline')
        attribution_date = request.POST.get('attribution_date', timezone.now().date().isoformat())
        notes = request.POST.get('notes', '')
        
        try:
            with transaction.atomic():
                # Mise Ã  jour du grade principal
                old_grade = practitioner.grade
                practitioner.grade = grade
                practitioner.save(update_fields=['grade'])
                
                # Essayer d'enregistrer dans l'historique si disponible
                try:
                    discipline = None
                    if discipline_id:
                        discipline = Discipline.objects.get(id=discipline_id)
                    
                    # Créer l'entrée d'historique
                    PractitionerGradeHistory.objects.create(
                        practitioner=practitioner,
                        grade=grade,
                        discipline=discipline,
                        attribution_date=attribution_date,
                        attributed_by=request.user,
                        previous_grade=old_grade,
                        notes=notes
                    )
                except (ImportError, Exception) as e:
                    # Le modèle d'historique n'est pas disponible, ignorer
                    logger.warning(f"Impossible d'enregistrer l'historique du grade: {e}")
                
                messages.success(request, _("Le grade de {} a été mis Ã  jour avec succès.").format(practitioner.full_name))
                
                # Redirection selon le paramètre next ou par défaut vers l'historique
                next_url = request.POST.get('next', request.GET.get('next'))
                if next_url:
                    return redirect(next_url)
                return redirect('competitions:club:practitioner_grade_history', practitioner_id=practitioner.id)
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise Ã  jour du grade: {e}", exc_info=True)
            messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour du grade: {}").format(str(e)))
    
    return render(request, 'competitions/club/grades/update_grade.html', {
        'practitioner': practitioner,
        'club': club,
        'disciplines': practitioner_disciplines,
        'discipline_grades': json.dumps(discipline_grades),
        'current_grade': practitioner.grade,
        'next': request.GET.get('next', ''),
    })

@login_required
@require_POST
def batch_update_grades(request):
    """
    Permet de mettre Ã  jour les grades de plusieurs pratiquants en une seule opération.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    try:
        practitioners_ids = request.POST.getlist('practitioners')
        grade = request.POST.get('grade')
        discipline_id = request.POST.get('discipline')
        attribution_date = request.POST.get('attribution_date', timezone.now().date().isoformat())
        notes = request.POST.get('notes', _('Mise Ã  jour groupée'))
        
        # Vérifier que nous avons des IDs et un grade
        if not practitioners_ids or not grade:
            messages.error(request, _("Veuillez sélectionner des pratiquants et un grade."))
            return redirect('competitions:club:grades_dashboard')
        
        discipline = None
        if discipline_id:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
            except Discipline.DoesNotExist:
                messages.warning(request, _("La discipline sélectionnée n'existe pas."))
        
        with transaction.atomic():
            updated_count = 0
            for practitioner_id in practitioners_ids:
                try:
                    practitioner = Practitioner.objects.get(id=practitioner_id, club=club)
                    
                    # Sauvegarder l'ancien grade pour l'historique
                    old_grade = practitioner.grade
                    
                    # Mettre Ã  jour le grade
                    practitioner.grade = grade
                    practitioner.save(update_fields=['grade'])
                    
                    # Créer une entrée dans l'historique si disponible
                    try:
                        PractitionerGradeHistory.objects.create(
                            practitioner=practitioner,
                            grade=grade,
                            discipline=discipline,
                            attribution_date=attribution_date,
                            attributed_by=request.user,
                            previous_grade=old_grade,
                            notes=notes
                        )
                    except (ImportError, Exception) as e:
                        # Le modèle d'historique n'est pas disponible, ignorer
                        logger.warning(f"Impossible d'enregistrer l'historique du grade: {e}")
                    
                    updated_count += 1
                except Practitioner.DoesNotExist:
                    # Pratiquant non trouvé ou n'appartenant pas au club, ignorer
                    continue
            
            messages.success(
                request, 
                _("{} pratiquant(s) ont été mis Ã  jour avec le grade '{}'.").format(updated_count, grade)
            )
    except Exception as e:
        logger.error(f"Erreur lors de la mise Ã  jour groupée des grades: {e}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour des grades: {}").format(str(e)))
    
    return redirect('competitions:club:grades_dashboard')

@login_required
def grade_systems_management(request):
    """
    Interface de gestion des systèmes de grades.
    Permet de créer et modifier les systèmes de grades pour les différentes disciplines.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si les modèles de grades avancés sont disponibles
    try:
        # Récupérer tous les systèmes de grades
        grade_systems = get_organization_queryset(GradeSystem, self.request.user).order_by('discipline__name', 'name')
        
        # Récupérer les disciplines
        disciplines = Discipline.objects.filter(is_active=True).order_by('name')
        
        return render(request, 'competitions/club/grades/systems.html', {
            'club': club,
            'grade_systems': grade_systems,
            'disciplines': disciplines,
            'advanced_grades_available': True
        })
    except (ImportError, Exception):
        # Les modèles avancés ne sont pas disponibles
        # Récupérer les anciennes catégories de grades
        try:
            grade_categories = get_organization_queryset(CategoryGrade, self.request.user).order_by('discipline__name', 'order', 'nom')
            
            # Récupérer les disciplines
            disciplines = Discipline.objects.filter(is_active=True).order_by('name')
            
            return render(request, 'competitions/club/grades/systems.html', {
                'club': club,
                'grade_categories': grade_categories,
                'disciplines': disciplines,
                'advanced_grades_available': False
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'accès aux catégories de grades: {e}", exc_info=True)
            messages.error(request, _("Une erreur est survenue lors de l'accès aux systèmes de grades."))
            return redirect('competitions:club:grades_dashboard')

@login_required
def api_get_discipline_grades(request, discipline_id):
    """
    API pour récupérer les grades d'une discipline spécifique.
    """
    try:
        discipline = Discipline.objects.get(id=discipline_id)
        
        # Essayer d'abord avec le nouveau système
        try:
            systems = GradeSystem.objects.filter(discipline=discipline)
            default_system = systems.filter(is_default=True).first() or systems.first()
            
            if default_system:
                grades = []
                for category in default_system.categories.all():
                    for grade in category.grades.all():
                        grades.append({
                            'id': grade.id,
                            'name': grade.name,
                            'category': category.name
                        })
                return JsonResponse({'grades': grades})
        except (ImportError, Exception):
            pass
        
        # Fallback aux anciennes catégories
        try:
            categories = CategoryGrade.objects.filter(
                discipline=discipline,
                is_active=True
            ).order_by('order', 'nom')
            
            grades = []
            for category in categories:
                # Si nous avons des grades min et max dans la catégorie
                if category.grade_min and category.grade_max:
                    grades.append({
                        'id': f"cat_{category.id}_{category.grade_min}",
                        'name': category.grade_min,
                        'category': category.nom
                    })
                    if category.grade_min != category.grade_max:
                        grades.append({
                            'id': f"cat_{category.id}_{category.grade_max}",
                            'name': category.grade_max,
                            'category': category.nom
                        })
            
            return JsonResponse({'grades': grades})
        except Exception:
            pass
        
        # Si aucun système n'est trouvé, retourner des grades par défaut
        default_grades = [
            {'id': 'default_white', 'name': _('Ceinture Blanche'), 'category': _('Débutant')},
            {'id': 'default_yellow', 'name': _('Ceinture Jaune'), 'category': _('Débutant')},
            {'id': 'default_orange', 'name': _('Ceinture Orange'), 'category': _('Intermédiaire')},
            {'id': 'default_green', 'name': _('Ceinture Verte'), 'category': _('Intermédiaire')},
            {'id': 'default_blue', 'name': _('Ceinture Bleue'), 'category': _('Avancé')},
            {'id': 'default_brown', 'name': _('Ceinture Marron'), 'category': _('Avancé')},
            {'id': 'default_black', 'name': _('Ceinture Noire'), 'category': _('Expert')}
        ]
        return JsonResponse({'grades': default_grades})
        
    except Discipline.DoesNotExist:
        return JsonResponse({'error': _('Discipline non trouvée'), 'grades': []}, status=404)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des grades: {e}", exc_info=True)
        return JsonResponse({'error': str(e), 'grades': []}, status=500)

