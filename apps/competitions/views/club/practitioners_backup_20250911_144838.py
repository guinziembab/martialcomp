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
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.core.paginator import Paginator
import json

# Import des modèles
from apps.competitions.models import (
    Practitioner, 
    Club,
    Discipline,
    Competition,
    CompetitionRegistration
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
    logger.warning(f"Les modèles de grades n'ont pas pu être importés: {str(e)}")
    GRADES_MODELS_AVAILABLE = False

# Création du logger
logger = logging.getLogger(__name__)

# Import de la fonction depuis le module utils pour éviter la duplication
# Ou si le module utils n'existe pas, on peut garder la définition locale
try:
    from apps.competitions.views.club.utils import get_user_club
except ImportError:
    # Définition locale de la fonction seulement si l'import échoue
    from apps.grades.models import GradeCategory as GradeSystem, Grade, GradeCategory
    def get_user_club(request):
        """
        Récupère le club associé à l'utilisateur de manière uniforme.
        Essaie différentes méthodes pour trouver le club.
        """
        # Si le club est déjà dans la requête (via le décorateur)
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
        messages.error(request, gettext_func("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit être le propriétaire du club ou un administrateur
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
        # Requête de base
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
def practitioner_form(request, practitioner_id=None):
    """Vue unifiée pour créer/modifier un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit être le propriétaire du club ou un administrateur
    is_authorized = (club.owner == request.user) or \
                   (hasattr(request.user, 'is_staff') and request.user.is_staff)
                   
    # Si l'utilisateur n'est pas autorisé, vérifier s'il est administrateur du club
    if not is_authorized and hasattr(request.user, 'club_admin_roles'):
        is_authorized = request.user.club_admin_roles.filter(club=club).exists()
        
    if not is_authorized:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer les pratiquants."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant si modification
    practitioner = None
    current_grades = {}
    
    if practitioner_id:
        # Vérifier si le club a une organisation associée
        club_organization = club.organization or getattr(club, 'as_organization', None)
        if not club_organization:
            messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
            return redirect('competitions:dashboard')
            
        practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=club_organization)
        # Récupérer tous les grades actuels
        if hasattr(practitioner, 'get_all_current_grades'):
            current_grades = practitioner.get_all_current_grades()
    
    if request.method == 'POST':
        # Créer le formulaire avec les données POST
        if practitioner:
            form = PractitionerForm(request.POST, request.FILES, instance=practitioner, request=request)
        else:
            form = PractitionerForm(request.POST, request.FILES, request=request)
        
        if form.is_valid():
            try:
                # Sauvegarder le pratiquant
                practitioner = form.save(commit=False)
                
                # S'assurer que le pratiquant est associé Ã  l'organisation
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if not club_organization:
                    messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
                    return redirect('competitions:dashboard')
                    
                if not practitioner.organization:
                    practitioner.organization = club_organization
                
                # Sauvegarder le pratiquant
                practitioner.save()
                
                # Sauvegarder les relations M2M (disciplines)
                form.save_m2m()
                
                if practitioner_id:
                    messages.success(request, _("Pratiquant mis Ã  jour avec succès."))
                else:
                    messages.success(request, _("Pratiquant créé avec succès."))
                
                return redirect('competitions:club:practitioners')
                
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {0}").format(str(e)))
                logger.error(f"Erreur lors de la sauvegarde du pratiquant: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Log des erreurs pour debugging
            logger.error(f"Erreurs du formulaire: {form.errors}")
            
    else:
        # Créer le formulaire pour GET
        if practitioner:
            form = PractitionerForm(instance=practitioner, request=request)
        else:
            form = PractitionerForm(request=request)
    
    context = {
        'form': form,
        'practitioner': practitioner,
        'club': club,
        'title': _("Modifier le pratiquant") if practitioner else _("Ajouter un pratiquant"),
        'submit_text': _("Enregistrer"),
        'is_edit': bool(practitioner),
        'current_grades': current_grades,
    }
    
    return render(request, 'competitions/club/practitioner_form.html', context)

@login_required
def practitioner_create(request):
    """Création d'un nouveau pratiquant (alias vers practitioner_form)"""
    return practitioner_form(request)

@login_required
def practitioner_update(request, pk):
    """Modification d'un pratiquant existant (alias vers practitioner_form)"""
    return practitioner_form(request, practitioner_id=pk)

@login_required
def practitioner_detail(request, pk):
    """Affichage des détails d'un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
        
    practitioner = get_object_or_404(Practitioner, pk=pk, organization=club_organization)
    
    # Récupérer les inscriptions aux compétitions de ce pratiquant
    try:
        from apps.competitions.models import CompetitionRegistration
        registrations = CompetitionRegistration.objects.filter(practitioner=practitioner)
    except (ImportError, AttributeError):
        # Si le modèle CompetitionRegistration n'existe pas encore
        logger.warning("Le modèle CompetitionRegistration n'est pas disponible")
        registrations = []
    
    # Récupérer les qualifications du pratiquant
    qualifications = []
    if hasattr(practitioner, 'get_active_qualifications'):
        qualifications = practitioner.get_active_qualifications()
    
    return render(request, 'competitions/club/practitioner_detail.html', {
        'practitioner': practitioner,
        'registrations': registrations,
        'qualifications': qualifications,
        'club': club,
        'active_tab': request.GET.get('tab', 'info'),  # Pour la navigation par onglets
    })

@login_required
def create_user_for_practitioner(request, practitioner_id):
    """Crée un compte utilisateur pour un pratiquant existant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
        
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
    
    # Vérifier si le pratiquant a déjÃ  un utilisateur associé
    if practitioner.user:
        messages.warning(request, _("Ce pratiquant possède déjÃ  un compte utilisateur."))
        return redirect('competitions:club:practitioners')
    
    try:
        # Créer un compte utilisateur pour le pratiquant
        if hasattr(practitioner, 'create_user_account'):
            user, temp_password, created = practitioner.create_user_account()
            
            if created:
                messages.success(
                    request, 
                    _("Compte utilisateur créé avec succès pour {}. Identifiants: "
                    "Nom d'utilisateur: {}, Mot de passe temporaire: {}").format(
                        practitioner.full_name, user.username, temp_password
                    )
                )
            else:
                messages.warning(request, _("Aucun compte n'a été créé."))
        else:
            # Implémentation basique si la méthode n'existe pas sur le modèle
            username = f"{practitioner.first_name.lower()}.{practitioner.last_name.lower()}"
            username = username.replace(' ', '')[:30]
            
            # Vérifier si l'utilisateur existe déjÃ  et ajouter un nombre si nécessaire
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Générer un mot de passe aléatoire
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=practitioner.email,
                password=temp_password,
                first_name=practitioner.first_name,
                last_name=practitioner.last_name
            )
            
            # Associer l'utilisateur au pratiquant
            practitioner.user = user
            practitioner.save()
            
            messages.success(
                request, 
                _("Compte utilisateur créé avec succès pour {}. Identifiants: "
                "Nom d'utilisateur: {}, Mot de passe temporaire: {}").format(
                    practitioner.full_name, username, temp_password
                )
            )
    except Exception as e:
        logger.error(f"Erreur lors de la création du compte utilisateur pour {practitioner_id}: {str(e)}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de la création du compte: {}").format(str(e)))
    
    return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

@login_required
def link_user_to_practitioner(request, practitioner_id):
    """Associe un pratiquant Ã  un utilisateur existant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
        
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
    
    # Vérifier si le pratiquant a déjÃ  un utilisateur associé
    if practitioner.user:
        messages.warning(request, _("Ce pratiquant possède déjÃ  un compte utilisateur."))
        return redirect('competitions:club:practitioners')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                
                # Associer l'utilisateur au pratiquant
                practitioner.user = user
                practitioner.save()
                
                messages.success(
                    request, 
                    _("Le pratiquant {} a été associé Ã  l'utilisateur {}.").format(
                        practitioner.full_name, user.username
                    )
                )
                return redirect('competitions:club:practitioner_detail', pk=practitioner_id)
            except User.DoesNotExist:
                messages.error(request, _("L'utilisateur sélectionné n'existe pas."))
            except Exception as e:
                logger.error(f"Erreur lors de l'association de l'utilisateur au pratiquant: {str(e)}", exc_info=True)
                messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
        else:
            messages.error(request, _("Aucun utilisateur n'a été sélectionné."))
    
    # Récupérer les utilisateurs disponibles pour l'association
    available_users = User.objects.filter(
        Q(profile__role='participant') | 
        Q(profile__role='club_manager', profile__club=club)
    ).order_by('last_name', 'first_name')
    
    return render(request, 'competitions/club/link_user_form.html', {
        'practitioner': practitioner,
        'available_users': available_users,
        'title': _("Associer un utilisateur Ã  {}").format(practitioner.full_name),
        'club': club,
    })

@login_required
@require_POST
def practitioner_delete(request, practitioner_id):
    """Supprime un pratiquant - Version corrigée avec logs détaillés."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, gettext_func("Vous devez être responsable de club pour accéder à cette page."))
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


@login_required
def practitioner_qualifications_add(request, practitioner_id):
    """Ajouter une qualification à un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:practitioners')
    
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
    
    context = {
        'practitioner': practitioner,
        'club': club,
        'page_title': _('Ajouter une qualification'),
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:index'},
            {'name': _('Pratiquants'), 'url': 'competitions:club:practitioners'},
            {'name': practitioner.full_name, 'url': 'competitions:club:practitioner_detail', 'args': [practitioner.id]},
            {'name': _('Ajouter qualification'), 'active': True}
        ]
    }
    
    return render(request, 'competitions/club/practitioners/qualifications_add.html', context)


@login_required
def practitioner_registrations(request, practitioner_id):
    """Afficher les inscriptions d'un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:practitioners')
    
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
    
    # Récupérer les inscriptions du pratiquant (si le module existe)
    registrations = []
    try:
        from apps.competitions.models import Registration
        registrations = Registration.objects.filter(practitioner=practitioner).order_by('-created_at')
    except (ImportError, AttributeError):
        # Le modèle Registration n'existe pas encore
        pass
    
    context = {
        'practitioner': practitioner,
        'club': club,
        'registrations': registrations,
        'page_title': _('Inscriptions du pratiquant'),
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:index'},
            {'name': _('Pratiquants'), 'url': 'competitions:club:practitioners'},
            {'name': practitioner.full_name, 'url': 'competitions:club:practitioner_detail', 'args': [practitioner.id]},
            {'name': _('Inscriptions'), 'active': True}
        ]
    }
    
    return render(request, 'competitions/club/practitioners/registrations.html', context)


@login_required
# @club_required  # Temporairement désactivé pour test
@require_http_methods(["POST"])
def create_practitioner_registration(request, practitioner_id):
    """
    Créer une nouvelle inscription pour un pratiquant via AJAX.
    """
    try:
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        # club = get_user_club(request)
        
        # Temporairement skip la vérification club pour test
        # if not club or practitioner.club != club:
        #     return JsonResponse({
        #         'success': False,
        #         'error': _("Vous n'avez pas les permissions pour inscrire ce pratiquant.")
        #     }, status=403)
        
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Get competition
        competition_id = data.get('competition')
        if not competition_id:
            return JsonResponse({
                'success': False,
                'error': _("Veuillez sélectionner une compétition.")
            }, status=400)
        
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Check if registration already exists
        if CompetitionRegistration.objects.filter(practitioner=practitioner, competition=competition).exists():
            return JsonResponse({
                'success': False,
                'error': _("Ce pratiquant est déjà inscrit à cette compétition.")
            }, status=400)
        
        # Create registration
        with transaction.atomic():
            # Map frontend status to model status
            frontend_status = data.get('status', 'active')
            model_status = 'approved' if frontend_status == 'active' else 'pending'
            
            registration = CompetitionRegistration.objects.create(
                practitioner=practitioner,
                competition=competition,
                # registration_date is auto_now_add, don't set it manually
                status=model_status,
                notes=data.get('notes', ''),
                # fee is not a field in this model, remove it
            )
            
            return JsonResponse({
                'success': True,
                'message': _("Inscription créée avec succès!"),
                'registration_id': registration.id
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': _("Données invalides.")
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'inscription: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _("Une erreur est survenue lors de la création de l'inscription.")
        }, status=500)


@login_required 
@require_http_methods(["GET"])
# @club_required  # Temporairement désactivé pour test
def get_available_competitions(request, practitioner_id):
    """
    Récupérer la liste des compétitions disponibles pour un pratiquant.
    """
    try:
        logger.info(f"get_available_competitions called for practitioner {practitioner_id}")
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        logger.info(f"Practitioner found: {practitioner.full_name}")
        
        # club = get_user_club(request)
        
        # Temporairement skip la vérification club pour test
        # if not club or practitioner.club != club:
        #     return JsonResponse({
        #         'success': False,
        #         'error': _("Accès non autorisé.")
        #     }, status=403)
        
        # Get competitions that are published and not yet started
        competitions = Competition.objects.filter(
            status='published',
            start_date__gte=timezone.now().date()
        ).exclude(
            # Exclude competitions where practitioner is already registered
            registrations__practitioner=practitioner
        ).order_by('start_date')
        
        competitions_data = [
            {
                'id': comp.id,
                'title': comp.title,
                'start_date': comp.start_date.strftime('%d/%m/%Y'),
                'location': f"{comp.city}" if comp.city else "",
                'discipline': comp.discipline.name if comp.discipline else ""
            }
            for comp in competitions
        ]
        
        return JsonResponse({
            'success': True,
            'competitions': competitions_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des compétitions: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _("Erreur lors du chargement des compétitions.")
        }, status=500)

