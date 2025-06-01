"""
Module pour les opérations en masse sur les grades des pratiquants.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST
import logging

from competitions.models import Practitioner, Discipline
from grades.models import Grade, PractitionerGrade
from grades.utils import get_user_club

# Création du logger
logger = logging.getLogger(__name__)

@login_required
def bulk_grade_assignment_form(request):
    """
    Affiche le formulaire pour attribuer un grade à plusieurs pratiquants en une fois.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('dashboard:index')
    
    # Récupérer tous les pratiquants du club via l'organisation
    practitioners = Practitioner.objects.filter(organization=organization).order_by('last_name', 'first_name')
    
    # Récupérer les disciplines disponibles
    disciplines = Discipline.objects.filter(is_active=True).order_by('name')
    
    # Filtrer par discipline si demandé
    discipline_id = request.GET.get('discipline')
    selected_discipline = None
    
    if discipline_id:
        try:
            selected_discipline = Discipline.objects.get(id=discipline_id)
            practitioners = practitioners.filter(disciplines=selected_discipline)
        except Discipline.DoesNotExist:
            pass
    
    # Filtrer par recherche si demandé
    search_query = request.GET.get('q')
    if search_query:
        from django.db.models import Q
        practitioners = practitioners.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Si une discipline est sélectionnée, récupérer ses grades
    grades = []
    if selected_discipline:
        from grades.utils import get_grades_for_discipline
        grades = get_grades_for_discipline(selected_discipline)
    
    return render(request, 'grades/bulk_assignment.html', {
        'practitioners': practitioners,
        'disciplines': disciplines,
        'selected_discipline': selected_discipline,
        'grades': grades,
        'search_query': search_query,
        'club': club,
    })

@login_required
@require_POST
def batch_update_grades(request):
    """
    Permet de mettre à jour les grades de plusieurs pratiquants en une seule opération.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    try:
        practitioners_ids = request.POST.getlist('practitioners')
        grade_id = request.POST.get('grade')
        discipline_id = request.POST.get('discipline')
        obtained_date = request.POST.get('obtained_date', timezone.now().date().isoformat())
        notes = request.POST.get('notes', _('Mise à jour groupée'))
        
        # Vérifier que nous avons des IDs et un grade
        if not practitioners_ids or not grade_id:
            messages.error(request, _("Veuillez sélectionner des pratiquants et un grade."))
            return redirect('grades:bulk_assignment')
        
        # Récupérer le grade et la discipline
        grade = get_object_or_404(Grade, id=grade_id)
        
        discipline = None
        if discipline_id:
            try:
                discipline = get_object_or_404(Discipline, id=discipline_id)
            except Discipline.DoesNotExist:
                messages.warning(request, _("La discipline sélectionnée n'existe pas."))
        
        # Récupérer l'organisation associée au club
        organization = club.organization or club.as_organization
        if not organization:
            messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
            return redirect('grades:bulk_assignment')
        
        with transaction.atomic():
            updated_count = 0
            for practitioner_id in practitioners_ids:
                try:
                    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
                    
                    # Mettre à jour le grade principal
                    practitioner.grade = grade
                    practitioner.save(update_fields=['grade'])
                    
                    # Créer une entrée dans l'historique
                    PractitionerGrade.objects.create(
                        practitioner=practitioner,
                        grade=grade,
                        discipline=discipline,
                        obtained_date=obtained_date,
                        awarded_by=request.user,
                        notes=notes
                    )
                    
                    updated_count += 1
                except Practitioner.DoesNotExist:
                    # Pratiquant non trouvé ou n'appartenant pas au club, ignorer
                    continue
            
            messages.success(
                request, 
                _("{} pratiquant(s) ont été mis à jour avec le grade '{}'.").format(updated_count, grade.name)
            )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour groupée des grades: {e}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de la mise à jour des grades: {}").format(str(e)))
    
    return redirect('grades:dashboard')

@login_required
def import_grades_from_excel(request):
    """
    Permet d'importer des grades depuis un fichier Excel.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        if 'excel_file' not in request.FILES:
            messages.error(request, _("Veuillez sélectionner un fichier Excel."))
            return redirect('grades:import_excel')
        
        excel_file = request.FILES['excel_file']
        
        try:
            # Utiliser pandas pour lire le fichier Excel
            import pandas as pd
            
            # Lire le fichier Excel
            df = pd.read_excel(excel_file)
            
            # Valider les colonnes requises
            required_columns = ['nom', 'prenom', 'grade', 'discipline', 'date_obtention']
            for column in required_columns:
                if column not in df.columns:
                    messages.error(request, _("Le fichier Excel doit contenir les colonnes: {}").format(", ".join(required_columns)))
                    return redirect('grades:import_excel')
            
            # Initialiser les compteurs
            total_rows = len(df)
            success_count = 0
            error_count = 0
            
            # Traiter les données
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Récupérer l'organisation associée au club
                        organization = club.organization or club.as_organization
                        if not organization:
                            logger.error(f"Aucune organisation associée trouvée pour le club {club}")
                            error_count += 1
                            continue
                        
                        # Rechercher le pratiquant
                        practitioner = Practitioner.objects.get(
                            first_name__iexact=row['prenom'],
                            last_name__iexact=row['nom'],
                            organization=organization
                        )
                        
                        # Rechercher la discipline
                        discipline = None
                        if row['discipline']:
                            discipline = Discipline.objects.filter(
                                name__icontains=row['discipline']
                            ).first()
                        
                        # Rechercher le grade
                        grade_name = row['grade']
                        grade = None
                        
                        if discipline:
                            # Chercher dans les grades de la discipline
                            from grades.utils import get_grades_for_discipline
                            grades = get_grades_for_discipline(discipline)
                            grade = next((g for g in grades if g.name.lower() == grade_name.lower()), None)
                        
                        if not grade:
                            # Chercher dans tous les grades
                            grade = Grade.objects.filter(name__iexact=grade_name).first()
                        
                        if not grade:
                            logger.warning(f"Grade non trouvé: {grade_name} pour {practitioner}")
                            error_count += 1
                            continue
                        
                        # Déterminer la date d'obtention
                        obtained_date = row['date_obtention']
                        if pd.isna(obtained_date):
                            obtained_date = timezone.now().date()
                        
                        # Mettre à jour le grade
                        practitioner.grade = grade
                        practitioner.save(update_fields=['grade'])
                        
                        # Créer l'entrée dans l'historique
                        PractitionerGrade.objects.create(
                            practitioner=practitioner,
                            grade=grade,
                            discipline=discipline,
                            obtained_date=obtained_date,
                            awarded_by=request.user,
                            notes=_("Importé depuis Excel")
                        )
                        
                        success_count += 1
                        
                    except Practitioner.DoesNotExist:
                        logger.warning(f"Practitioner not found: {row['nom']} {row['prenom']}")
                        error_count += 1
                    except Exception as e:
                        logger.error(f"Error processing row {index}: {e}", exc_info=True)
                        error_count += 1
            
            messages.success(request, _(
                "Import terminé. {}/{} enregistrements traités avec succès. {} erreurs."
            ).format(success_count, total_rows, error_count))
            
            return redirect('grades:dashboard')
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import Excel: {e}", exc_info=True)
            messages.error(request, _("Une erreur est survenue lors de l'import: {}").format(str(e)))
    
    return render(request, 'grades/import_excel.html', {
        'club': club,
    })