from django.core.exceptions import PermissionDenied
"""
Module pour la gestion des pratiquants d'un club avec correction du problème de suppression.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as gettext_func
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.core.paginator import Paginator

# Import des modèles
from apps.competitions.models import (
    Practitioner, 
    Club,
    Discipline
)

# Import des formulaires
from apps.competitions.forms import (
    PractitionerForm,
)

# Import des décorateurs
from apps.competitions.utils.decorators import club_required, permission_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Import des modèles de grades avec gestion des erreurs
try:
    GRADES_MODELS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Les modèles de grades n'ont pas pu Ãªtre importés: {str(e)}")
    GRADES_MODELS_AVAILABLE = False

# Création du logger
logger = logging.getLogger(__name__)

# Import de la fonction depuis le module utils pour éviter la duplication
# Ou si le module utils n'existe pas, on peut garder la définition locale
try:
    from apps.competitions.views.club.utils import get_user_club
except ImportError:
    # Définition locale de la fonction seulement si l'import échoue
    from apps.grades.models import GradingSystem as GradeSystem, Grade, GradeCategory
    def get_user_club(request):
        """
        Récupère le club associé Ã  l'utilisateur de manière uniforme.
        Essaie différentes méthodes pour trouver le club.
        """
        # Si le club est déjÃ  dans la requÃªte (via le décorateur)
        if hasattr(request, 'club') and request.club:
            return request.club
        
        # Si l'utilisateur a un attribut club
        if hasattr(request.user, 'club') and request.user.club:
            return request.user.club
        
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
def practitioners_list(request):
    """Liste des pratiquants du club - Version améliorée."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, gettext_func("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit Ãªtre le propriétaire du club ou un administrateur
    is_authorized = (club.owner == request.user) or \
                   (hasattr(request.user, 'is_staff') and request.user.is_staff)
                   
    # Si l'utilisateur n'est pas autorisé, vérifier s'il est administrateur du club
    if not is_authorized and hasattr(request.user, 'club_admin_roles'):
        is_authorized = request.user.club_admin_roles.filter(club=club).exists()
        
    if not is_authorized:
        messages.error(request, gettext_func("Vous n'avez pas les permissions nécessaires pour gérer les pratiquants."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, gettext_func("Aucune organisation associée trouvée pour ce club."))
        practitioners = Practitioner.objects.none()
    else:
        # RequÃªte de base
        practitioners = Practitioner.objects.filter(organization=club_organization)
    
    # Récupérer tous les grades distincts des pratiquants du club
    available_grades = practitioners.values_list('grade_text', flat=True).distinct().order_by('grade_text')
    
    # Filtres
    # 1. Recherche textuelle
    search_query = request.GET.get('q')
    if search_query:
        practitioners = practitioners.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )
    
    # 2. Filtre par grade
    grade_filter = request.GET.get('grade')
    if grade_filter:
        practitioners = practitioners.filter(
            Q(grade_text=grade_filter) | Q(grade__name=grade_filter)
        )
    
    # 3. Filtre par groupe d'Ã¢ge
    age_group = request.GET.get('age_group')
    if age_group:
        today = timezone.now().date()
        if age_group == 'children':
            # Enfants (6-11 ans)
            max_birth_date = today.replace(year=today.year - 6)
            min_birth_date = today.replace(year=today.year - 11, day=31, month=12)
            practitioners = practitioners.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
        elif age_group == 'teenagers':
            # Adolescents (12-17 ans)
            max_birth_date = today.replace(year=today.year - 12)
            min_birth_date = today.replace(year=today.year - 17, day=31, month=12)
            practitioners = practitioners.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
        elif age_group == 'adults':
            # Adultes (18-39 ans)
            max_birth_date = today.replace(year=today.year - 18)
            min_birth_date = today.replace(year=today.year - 39, day=31, month=12)
            practitioners = practitioners.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
        elif age_group == 'seniors':
            # Seniors (40+ ans)
            min_birth_date = today.replace(year=today.year - 40)
            practitioners = practitioners.filter(birth_date__lte=min_birth_date)
    
    # 4. Filtre par statut d'utilisateur
    user_status = request.GET.get('user_status')
    if user_status:
        if user_status == 'with_user':
            practitioners = practitioners.filter(user__isnull=False)
        elif user_status == 'without_user':
            practitioners = practitioners.filter(user__isnull=True)
    
    # 5. Filtre par statut d'activité
    status = request.GET.get('status')
    if status:
        practitioners = practitioners.filter(status=status)
    
    # Pagination
    paginator = Paginator(practitioners.order_by('last_name', 'first_name'), 12)  # 12 pratiquants par page
    page = request.GET.get('page')
    practitioners_page = paginator.get_page(page)
    
    # Ajouter une vérification pour chaque pratiquant pour s'assurer que grade_display est disponible
    for practitioner in practitioners_page:
        if not hasattr(practitioner, 'grade_display'):
            # Si la propriété n'existe pas, créer une version de secours
            if hasattr(practitioner, 'grade') and practitioner.grade:
                practitioner.grade_display = str(practitioner.grade)
            elif hasattr(practitioner, 'grade_text') and practitioner.grade_text:
                practitioner.grade_display = practitioner.grade_text
            else:
                practitioner.grade_display = "Non spécifié"
    
    return render(request, 'competitions/club/practitioners_enhanced.html', {
        'practitioners': practitioners_page,
        'available_grades': available_grades,
        'is_paginated': practitioners_page.has_other_pages(),
        'page_obj': practitioners_page,
        'club': club,
        'status_choices': Practitioner.STATUS_CHOICES,
    })

@login_required
@require_POST
def practitioner_delete(request, practitioner_id):
    """Supprime un pratiquant - Version corrigée avec logs détaillés."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, gettext_func("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, gettext_func("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Log de débogage
    logger.info(f"Tentative de suppression du pratiquant ID={practitioner_id} par l'utilisateur {request.user.username}")
    
    try:
        # Récupérer le pratiquant Ã  supprimer
        practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
        
        # Stocker le nom pour le message de confirmation
        name = practitioner.full_name
        
        # Log avant la suppression
        logger.info(f"Suppression du pratiquant {practitioner.id} - {name}")
        
        # Suppression avec transaction pour assurer l'intégrité
        with transaction.atomic():
            # Supprimer d'abord les relations qui pourraient bloquer la suppression
            if hasattr(practitioner, 'qr_code'):
                logger.info(f"Suppression du QR code associé au pratiquant {practitioner.id}")
                practitioner.qr_code.delete()
            
            # Supprimer les inscriptions aux compétitions si elles existent
            try:
                from apps.competitions.models import CompetitionRegistration
                registrations = CompetitionRegistration.objects.filter(practitioner=practitioner)
                count = registrations.count()
                if count > 0:
                    logger.info(f"Suppression de {count} inscriptions pour le pratiquant {practitioner.id}")
                    registrations.delete()
            except (ImportError, AttributeError):
                logger.warning("Impossible d'accéder aux inscriptions du pratiquant")
            
            # Supprimer les grades du pratiquant si le module grades est disponible
            try:
                from apps.grades.models import PractitionerGrade
                grades = PractitionerGrade.objects.filter(practitioner=practitioner)
                count = grades.count()
                if count > 0:
                    logger.info(f"Suppression de {count} grades pour le pratiquant {practitioner.id}")
                    grades.delete()
            except (ImportError, AttributeError):
                logger.warning("Impossible d'accéder aux grades du pratiquant")
            
            # Supprimer le pratiquant
            practitioner.delete()
            logger.info(f"Pratiquant {name} supprimé avec succès")
        
        messages.success(request, gettext_func("Le pratiquant {} a été supprimé avec succès.").format(name))
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du pratiquant {practitioner_id}: {str(e)}", exc_info=True)
        messages.error(request, gettext_func("Une erreur est survenue lors de la suppression: {}").format(str(e)))
    
    # Rediriger vers la liste des pratiquants
    return redirect('competitions:club:practitioners')

