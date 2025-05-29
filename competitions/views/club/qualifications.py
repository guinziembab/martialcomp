"""
Module pour la gestion des qualifications des pratiquants.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from competitions.models import Practitioner, Club, JudgeQualification
from competitions.forms.qualification import PractitionerGradeForm
from .practitioners import get_user_club
from competitions.utils.permission_helpers import manual_permission_check

import logging
logger = logging.getLogger(__name__)

@login_required
@manual_permission_check('club.manage_practitioners')
def qualification_form(request, practitioner_id, qualification_id=None):
    """Ajoute/modifie une qualification pour un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=club_organization)
    
    # Récupérer la qualification si elle existe
    qualification = None
    if qualification_id:
        qualification = get_object_or_404(JudgeQualification, pk=qualification_id, practitioner=practitioner)
    
    if request.method == 'POST':
        try:
            # Si le modèle JudgeQualification existe dans l'application
            form = PractitionerGradeForm(request.POST, instance=qualification)
            if form.is_valid():
                qual = form.save(commit=False)
                qual.practitioner = practitioner
                
                # Ajouter des champs supplémentaires si nécessaire
                if not hasattr(qual, 'is_active'):
                    qual.is_active = True
                
                qual.save()
                
                messages.success(request, _("Qualification enregistrée avec succès."))
                return redirect('competitions:club:practitioner_detail', pk=practitioner.id)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la qualification: {str(e)}", exc_info=True)
            messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
            return redirect('competitions:club:practitioners')
    else:
        try:
            form = PractitionerGradeForm(instance=qualification)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du formulaire: {str(e)}", exc_info=True)
            messages.warning(request, _("Le module de qualifications n'est pas disponible dans cette version."))
            return redirect('competitions:club:practitioners')
    
    return render(request, 'competitions/club/qualification_form.html', {
        'form': form,
        'practitioner': practitioner,
        'qualification': qualification,
        'is_edit': qualification is not None,
        'title': _("Modifier la qualification") if qualification else _("Ajouter une qualification"),
        'submit_text': _("Enregistrer") if qualification else _("Ajouter"),
        'club': club,
    })

@login_required
def judges_list(request):
    """Liste des juges et arbitres du club."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Vérifier si nous avons le modèle JudgeQualification
    judges = []
    
    try:
        # Tenter d'utiliser le modèle JudgeQualification
        has_qualification_model = 'JudgeQualification' in globals() or hasattr(Practitioner, 'qualifications')
        
        if has_qualification_model:
            # Méthode préférée: utiliser le modèle de qualification
            judges = Practitioner.objects.filter(
                club=club,
                qualifications__isnull=False
            ).distinct().prefetch_related('qualifications')
            
            # Filtres
            qualification_type = request.GET.get('qualification_type')
            level = request.GET.get('level')
            
            # Appliquer les filtres si spécifiés
            if qualification_type:
                judges = judges.filter(qualifications__qualification_type=qualification_type).distinct()
            
            if level:
                judges = judges.filter(qualifications__level=level).distinct()
        else:
            # Méthode alternative si JudgeQualification n'existe pas
            raise AttributeError("JudgeQualification model not found")
            
    except (ImportError, AttributeError) as e:
        logger.warning(f"Module de qualification non disponible: {str(e)}")
        # Si le modèle JudgeQualification n'existe pas, chercher des indices dans les champs existants
        judges = Practitioner.objects.filter(
            club=club
        ).filter(
            Q(grade__icontains='juge') | 
            Q(grade__icontains='arbitre') |
            Q(grade__icontains='referee') |
            Q(notes__icontains='juge') |
            Q(notes__icontains='arbitre') |
            Q(grade__icontains='Ceinture noire')  # Les ceintures noires sont souvent juges
        ).distinct()
        
        messages.warning(
            request, 
            _("Le module de qualification des juges n'est pas disponible. "
             "Affichage des pratiquants qui semblent être des juges ou arbitres selon leur grade.")
        )
    except Exception as e:
        # Erreur générique
        logger.error(f"Erreur lors de la récupération des juges: {str(e)}", exc_info=True)
        judges = []
        messages.error(
            request,
            _("Une erreur est survenue lors de la récupération des juges: {}").format(str(e))
        )
    
    # Si nous n'avons trouvé aucun juge mais que nous avons des pratiquants
    if not judges:
        # Message d'aide
        messages.info(
            request,
            _("Aucun juge ou arbitre n'a été trouvé dans votre club. "
              "Vous pouvez ajouter des qualifications à vos pratiquants depuis leur profil.")
        )
    
    # Rendre le template avec le contexte
    qualification_types = []
    levels = []
    
    try:
        # Vérifier si le club a une organisation associée
        club_organization = club.organization or getattr(club, 'as_organization', None)
        
        if not club_organization:
            qualification_types = []
            levels = []
        else:
            qualification_types = JudgeQualification.objects.filter(
                practitioner__organization=club_organization
            ).values_list('qualification_type', flat=True).distinct()
            
            levels = JudgeQualification.objects.filter(
                practitioner__organization=club_organization
            ).values_list('level', flat=True).distinct()
    except:
        pass
    
    return render(request, 'competitions/club/judges_list.html', {
        'club': club,
        'judges': judges,
        'page_title': _("Juges et arbitres"),
        'qualification_types': qualification_types,
        'levels': levels,
        'selected_type': request.GET.get('qualification_type'),
        'selected_level': request.GET.get('level'),
    })

@login_required
@manual_permission_check('club.manage_practitioners')
def delete_qualification(request, qualification_id):
    """Supprime une qualification."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    try:
        # Vérifier si le club a une organisation associée
        club_organization = club.organization or getattr(club, 'as_organization', None)
        
        if not club_organization:
            messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
            return redirect('competitions:dashboard')
            
        # Vérifier que la qualification appartient bien à un pratiquant du club
        qualification = get_object_or_404(
            JudgeQualification, 
            id=qualification_id,
            practitioner__organization=club_organization
        )
        
        practitioner_id = qualification.practitioner.id
        qualification_name = str(qualification)
        
        qualification.delete()
        
        messages.success(request, _("La qualification {} a été supprimée.").format(qualification_name))
        return redirect('competitions:club:practitioner_detail', pk=practitioner_id)
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la qualification {qualification_id}: {str(e)}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de la suppression: {}").format(str(e)))
        return redirect('competitions:club:practitioners')