# ===========================================================
# 1. FICHIER: competitions/views/federation_grades.py
# ===========================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
import json

from competitions.models import Federation, Discipline
from grades.models import GradeCategory, Grade
from grades.forms import GradeCategoryForm  # Ajustez selon votre structure réelle

def grades_view(request, federation_id):
    """Vue pour gérer les grades d'une fédération."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer toutes les disciplines
    disciplines = Discipline.objects.all().order_by('name')
    
    # Récupérer la discipline sélectionnée s'il y en a une
    discipline_id = request.GET.get('discipline')
    selected_discipline = None
    discipline_grades = []
    discipline_grades_json = None
    
    # Traitement du formulaire si POST
    if request.method == 'POST':
        if 'add_grade' in request.POST:
            form = GradeCategoryForm(request.POST)
            if form.is_valid():
                grade_category = form.save(commit=False)
                # Assurez-vous que les champs obligatoires sont présents
                if not hasattr(grade_category, 'discipline') or not grade_category.discipline:
                    grade_category.discipline = selected_discipline
                grade_category.save()
                messages.success(request, _("La catégorie de grade a été créée avec succès."))
                return redirect('competitions:federations:grades', federation_id=federation.id)
            else:
                messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
        elif 'delete_grade' in request.POST:
            grade_id = request.POST.get('grade_id')
            if grade_id:
                try:
                    grade_category = GradeCategory.objects.get(id=grade_id)
                    grade_category.delete()
                    messages.success(request, _("La catégorie de grade a été supprimée avec succès."))
                except GradeCategory.DoesNotExist:
                    messages.error(request, _("Catégorie de grade introuvable."))
                return redirect('competitions:federations:grades', federation_id=federation.id)
    else:
        form = GradeCategoryForm(initial={'discipline': selected_discipline})
    
    # Récupération des grades pour la discipline sélectionnée
    if discipline_id:
        try:
            selected_discipline = Discipline.objects.get(id=discipline_id)
            
            # Récupérer directement les grades depuis la base de données
            try:
                db_grades = Grade.objects.filter(discipline=selected_discipline).order_by('level')
                
                discipline_grades = []
                if db_grades.exists():
                    for grade in db_grades:
                        discipline_grades.append({
                            'id': grade.id,
                            'name': grade.name,
                            'nom': grade.name,
                            'category': grade.category.name if grade.category else "",
                            'discipline': selected_discipline.name,
                            'color': grade.color,
                            'color_code': getattr(grade, 'color_code', grade.color),
                            'level': grade.level,
                        })
                
                # Si aucun grade trouvé, utiliser les grades par défaut
                if not discipline_grades:
                    # Importer les grades par défaut
                    from grades.views.api import get_default_grades_for_discipline
                    discipline_grades = get_default_grades_for_discipline(selected_discipline.name)
                
                # Convertir en JSON pour le template
                discipline_grades_json = json.dumps(discipline_grades)
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la récupération des grades: {str(e)}")
                
        except Discipline.DoesNotExist:
            messages.error(request, _("Discipline introuvable."))
    
    # Récupérer les catégories de grades pour affichage
    grade_categories = []
    if selected_discipline:
        grade_categories = GradeCategory.objects.filter(discipline=selected_discipline).order_by('order')
    
    context = {
        'federation': federation,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'selected_discipline_name': selected_discipline.name if selected_discipline else None,
        'form': form,
        'discipline_grades': discipline_grades,
        'discipline_grades_json': discipline_grades_json,
        'grade_categories': grade_categories
    }
    
    return render(request, 'competitions/federations/grades.html', context)

# Endpoint API pour récupérer les grades d'une discipline directement
def get_grades_ajax(request, federation_id):
    discipline_id = request.GET.get('discipline_id')
    if not discipline_id:
        return JsonResponse({'error': 'Discipline ID manquant', 'grades': []}, status=400)
    
    try:
        discipline = Discipline.objects.get(id=discipline_id)
        
        # Récupérer les grades depuis la base de données
        db_grades = Grade.objects.filter(discipline=discipline).order_by('level')
        
        grades_data = []
        if db_grades.exists():
            for grade in db_grades:
                grades_data.append({
                    'id': grade.id,
                    'name': grade.name,
                    'category': grade.category.name if grade.category else "",
                    'discipline': discipline.name,
                    'color': grade.color,
                    'level': grade.level,
                })
        else:
            # Utiliser les grades par défaut
            from grades.views.api import get_default_grades_for_discipline
            grades_data = get_default_grades_for_discipline(discipline.name)
        
        return JsonResponse({'grades': grades_data})
    
    except Discipline.DoesNotExist:
        return JsonResponse({'error': 'Discipline introuvable', 'grades': []}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'grades': []}, status=500)