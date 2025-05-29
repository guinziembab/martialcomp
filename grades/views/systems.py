"""
Module pour la gestion des systèmes de grades.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse

from competitions.models import Discipline
from grades.models import Grade, GradeCategory
from grades.forms import GradeCategoryForm, GradeForm
from competitions.utils.decorators import club_required

# Suppression de l'import de GradeSystem qui n'existe pas
# Suppression de l'import de GradeSystemForm qui n'existe probablement pas

@login_required
@club_required
def grade_systems_list(request):
    """
    Liste tous les systèmes de grades disponibles.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Au lieu d'utiliser GradeSystem, on utilise les disciplines comme base
    disciplines = Discipline.objects.filter(is_active=True).order_by('name')
    
    # Filtrage optionnel
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        disciplines = disciplines.filter(id=discipline_id)
    
    return render(request, 'grades/systems_list.html', {
        'club': club,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
    })

@login_required
@club_required
def grade_system_detail(request, discipline_id):
    """
    Affiche les détails des grades d'une discipline spécifique.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer la discipline au lieu du système de grades
    discipline = get_object_or_404(Discipline, id=discipline_id)
    
    # Récupérer les catégories et grades associés
    categories = GradeCategory.objects.filter(discipline=discipline).prefetch_related('grades').order_by('order', 'name')
    
    return render(request, 'grades/system_detail.html', {
        'club': club,
        'discipline': discipline,
        'categories': categories,
    })

# Les fonctions suivantes doivent être adaptées pour fonctionner sans GradeSystem
# Par exemple, on peut associer les catégories directement aux disciplines

@login_required
@club_required
def add_grade_category(request, discipline_id):
    """
    Ajout d'une nouvelle catégorie de grades pour une discipline.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer la discipline
    discipline = get_object_or_404(Discipline, id=discipline_id)
    
    if request.method == 'POST':
        form = GradeCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.discipline = discipline
            category.save()
            
            messages.success(request, _("Catégorie ajoutée avec succès."))
            return redirect('grades:system_detail', discipline_id=discipline.id)
    else:
        form = GradeCategoryForm(initial={'discipline': discipline})
    
    return render(request, 'grades/category_form.html', {
        'club': club,
        'form': form,
        'discipline': discipline,
        'title': _("Ajouter une catégorie"),
    })

@login_required
@club_required
def edit_grade_category(request, category_id):
    """
    Modification d'une catégorie de grades existante.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer la catégorie
    category = get_object_or_404(GradeCategory, id=category_id)
    discipline = category.discipline
    
    if request.method == 'POST':
        form = GradeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie mise à jour avec succès."))
            return redirect('grades:system_detail', discipline_id=discipline.id)
    else:
        form = GradeCategoryForm(instance=category)
    
    return render(request, 'grades/category_form.html', {
        'club': club,
        'form': form,
        'category': category,
        'discipline': discipline,
        'title': _("Modifier la catégorie"),
    })

@login_required
@club_required
def add_grade(request, category_id):
    """
    Ajout d'un nouveau grade à une catégorie.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer la catégorie
    category = get_object_or_404(GradeCategory, id=category_id)
    discipline = category.discipline
    
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.category = category
            grade.discipline = discipline  # S'assurer que le grade est associé à la discipline
            
            # Déterminer l'ordre automatiquement si non spécifié
            if not grade.order:
                max_order = Grade.objects.filter(category=category).order_by('-order').first()
                grade.order = (max_order.order + 1) if max_order else 1
            
            grade.save()
            
            messages.success(request, _("Grade ajouté avec succès."))
            return redirect('grades:system_detail', discipline_id=discipline.id)
    else:
        form = GradeForm(initial={'category': category, 'discipline': discipline})
    
    return render(request, 'grades/grade_form.html', {
        'club': club,
        'form': form,
        'category': category,
        'discipline': discipline,
        'title': _("Ajouter un grade"),
    })

@login_required
@club_required
def edit_grade(request, grade_id):
    """
    Modification d'un grade existant.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer le grade
    grade = get_object_or_404(Grade, id=grade_id)
    category = grade.category
    discipline = grade.discipline
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            messages.success(request, _("Grade mis à jour avec succès."))
            return redirect('grades:system_detail', discipline_id=discipline.id)
    else:
        form = GradeForm(instance=grade)
    
    return render(request, 'grades/grade_form.html', {
        'club': club,
        'form': form,
        'grade': grade,
        'category': category,
        'discipline': discipline,
        'title': _("Modifier le grade"),
    })

@login_required
@club_required
def delete_grade(request, grade_id):
    """
    Suppression d'un grade.
    """
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer le grade
    grade = get_object_or_404(Grade, id=grade_id)
    discipline_id = grade.discipline.id
    
    if request.method == 'POST':
        grade.delete()
        messages.success(request, _("Grade supprimé avec succès."))
        return redirect('grades:system_detail', discipline_id=discipline_id)
    
    return render(request, 'grades/confirm_delete.html', {
        'club': club,
        'object': grade,
        'title': _("Supprimer le grade"),
        'message': _("Êtes-vous sûr de vouloir supprimer ce grade ?"),
        'warning': _("Cette action est irréversible et peut affecter les pratiquants qui possèdent ce grade."),
    })

@login_required
@club_required
def reorder_grades(request, category_id):
    """
    Réorganisation des grades dans une catégorie par glisser-déposer.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Récupérer les données JSON
            import json
            data = json.loads(request.body)
            
            # Vérifier que nous avons une liste d'IDs
            if not isinstance(data.get('grades'), list):
                return JsonResponse({'status': 'error', 'message': _("Format de données invalide.")}, status=400)
            
            # Récupérer la catégorie
            category = get_object_or_404(GradeCategory, id=category_id)
            
            # Mettre à jour l'ordre des grades
            with transaction.atomic():
                for index, grade_id in enumerate(data['grades']):
                    Grade.objects.filter(id=grade_id, category=category).update(order=index + 1)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': _("Méthode non autorisée.")}, status=405)