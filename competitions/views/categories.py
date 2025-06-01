from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ..models import (
    Competition, CompetitionType, CompetitionCategory,
    CategoryTemplate, Discipline
)
from ..forms import CompetitionCategoryForm, CategoryTemplateForm

# Import des modèles de l'application grades
from grades.models import Grade
from grades.utils import get_grades_for_discipline  # Fonction utilitaire à créer dans l'application grades

@login_required
def competition_categories(request, competition_id):
    """Affiche et permet de gérer les catégories d'une compétition."""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Regrouper les catégories par type de compétition
    competition_types = competition.competition_types.all()
    categories_by_type = {}
    
    for ct in competition_types:
        categories = CompetitionCategory.objects.filter(
            competition=competition,
            competition_type=ct
        ).order_by('name')
        
        # Ajouter le comptage des participants pour chaque catégorie
        categories_with_counts = []
        for category in categories:
            category.participant_count = category.registrations.count() if hasattr(category, 'registrations') else 0
            categories_with_counts.append(category)
        
        categories_by_type[ct] = categories_with_counts
    
    # Récupérer les templates disponibles pour cette discipline
    available_templates = CategoryTemplate.objects.filter(
        discipline=competition.discipline
    ).order_by('competition_type', 'name')
    
    context = {
        'competition': competition,
        'categories_by_type': categories_by_type,
        'available_templates': available_templates,
        'page_title': f"Catégories - {competition.title}"
    }
    
    return render(request, 'competitions/categories/list.html', context)

@login_required
def category_create(request, competition_id, type_id):
    """Créer une nouvelle catégorie pour une compétition."""
    competition = get_object_or_404(Competition, pk=competition_id)
    competition_type = get_object_or_404(CompetitionType, pk=type_id)
    
    # Récupérer les templates disponibles pour ce type de compétition
    templates = CategoryTemplate.objects.filter(
        discipline=competition.discipline,
        competition_type=competition_type
    )
    
    if request.method == 'POST':
        form = CompetitionCategoryForm(request.POST)
        
        # Configurer le form pour limiter les grades à ceux de la discipline
        if competition.discipline:
            discipline_grades = get_grades_for_discipline(competition.discipline)
            form.fields['min_grade'].queryset = discipline_grades
            form.fields['max_grade'].queryset = discipline_grades
            
        if form.is_valid():
            with transaction.atomic():
                category = form.save(commit=False)
                category.competition = competition
                category.competition_type = competition_type
                
                # Si un template est sélectionné, copier ses valeurs
                template_id = request.POST.get('template_id')
                if template_id:
                    template = get_object_or_404(CategoryTemplate, id=template_id)
                    category.template = template
                    category.name = template.name
                    category.min_age = template.min_age
                    category.max_age = template.max_age
                    
                    # Adapter pour les objets Grade
                    category.min_grade = template.min_grade  # Désormais une ForeignKey vers Grade
                    category.max_grade = template.max_grade  # Désormais une ForeignKey vers Grade
                    
                    category.min_weight = template.min_weight
                    category.max_weight = template.max_weight
                    category.gender = template.gender
                
                category.save()
                messages.success(request, _("Catégorie créée avec succès!"))
                return redirect('competitions:categories', competition_id=competition_id)
    else:
        form = CompetitionCategoryForm(initial={
            'competition': competition,
            'competition_type': competition_type
        })
        
        # Configurer le form pour limiter les grades à ceux de la discipline
        if competition.discipline:
            discipline_grades = get_grades_for_discipline(competition.discipline)
            form.fields['min_grade'].queryset = discipline_grades
            form.fields['max_grade'].queryset = discipline_grades
    
    return render(request, 'competitions/categories/category_form.html', {
        'form': form,
        'competition': competition,
        'competition_type': competition_type,
        'templates': templates,
        'is_create': True
    })

@login_required
def category_update(request, pk):
    """Modifier une catégorie existante."""
    category = get_object_or_404(CompetitionCategory, pk=pk)
    competition = category.competition
    
    if request.method == 'POST':
        form = CompetitionCategoryForm(request.POST, instance=category)
        
        # Configurer le form pour limiter les grades à ceux de la discipline
        if competition.discipline:
            discipline_grades = get_grades_for_discipline(competition.discipline)
            form.fields['min_grade'].queryset = discipline_grades
            form.fields['max_grade'].queryset = discipline_grades
            
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie mise à jour avec succès."))
            return redirect('competitions:categories', competition_id=category.competition.id)
    else:
        form = CompetitionCategoryForm(instance=category)
        
        # Configurer le form pour limiter les grades à ceux de la discipline
        if competition.discipline:
            discipline_grades = get_grades_for_discipline(competition.discipline)
            form.fields['min_grade'].queryset = discipline_grades
            form.fields['max_grade'].queryset = discipline_grades
    
    return render(request, 'competitions/categories/form.html', {
        'form': form,
        'category': category,
        'competition': category.competition,
        'competition_type': category.competition_type,
        'title': _("Modifier la catégorie")
    })

@login_required
def category_delete(request, category_id):
    """Supprime une catégorie."""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    if request.method == 'POST':
        name = category.name
        # Vérifier s'il y a des participants inscrits
        if hasattr(category, 'registrations') and category.registrations.exists():
            messages.error(request, _("Impossible de supprimer cette catégorie car elle contient des participants."))
            return redirect('competitions:categories', competition_id=competition.id)
        
        category.delete()
        messages.success(request, f"Catégorie '{name}' supprimée.")
        return redirect('competitions:categories', competition_id=competition.id)
    
    context = {
        'category': category,
        'competition': competition,
    }
    
    return render(request, 'competitions/categories/confirm_delete.html', context)

@login_required
def category_template_create(request):
    """Créer un nouveau template de catégorie."""
    if request.method == 'POST':
        form = CategoryTemplateForm(request.POST)
        
        # Si une discipline est sélectionnée, configurer les grades disponibles
        discipline_id = request.POST.get('discipline')
        if discipline_id:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                discipline_grades = get_grades_for_discipline(discipline)
                form.fields['min_grade'].queryset = discipline_grades
                form.fields['max_grade'].queryset = discipline_grades
            except Discipline.DoesNotExist:
                pass
                
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, _("Template de catégorie créé avec succès."))
            return redirect('competitions:category_templates_list')
    else:
        form = CategoryTemplateForm()
    
    # JavaScript pour charger dynamiquement les grades quand la discipline change
    extra_js = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const disciplineSelect = document.getElementById('id_discipline');
            const minGradeSelect = document.getElementById('id_min_grade');
            const maxGradeSelect = document.getElementById('id_max_grade');
            
            if (disciplineSelect && minGradeSelect && maxGradeSelect) {
                disciplineSelect.addEventListener('change', function() {
                    const disciplineId = this.value;
                    if (disciplineId) {
                        // Appeler l'API pour récupérer les grades de cette discipline
                        fetch(`/grades/api/by-discipline/${disciplineId}/`)
                            .then(response => response.json())
                            .then(data => {
                                // Vider les selects
                                minGradeSelect.innerHTML = '<option value="">---------</option>';
                                maxGradeSelect.innerHTML = '<option value="">---------</option>';
                                
                                // Remplir avec les nouveaux grades
                                if (data.grades && data.grades.length > 0) {
                                    data.grades.forEach(grade => {
                                        const option = new Option(grade.name, grade.id);
                                        minGradeSelect.add(option.cloneNode(true));
                                        maxGradeSelect.add(option);
                                    });
                                }
                            })
                            .catch(error => console.error('Erreur lors du chargement des grades:', error));
                    }
                });
            }
        });
    </script>
    """
    
    return render(request, 'competitions/categories/template_form.html', {
        'form': form,
        'title': _("Créer un template de catégorie"),
        'extra_js': extra_js
    })

@login_required
def category_templates_list(request):
    """Liste des templates de catégories disponibles."""
    templates = CategoryTemplate.objects.all().order_by('discipline', 'competition_type', 'name')
    
    # Filtrage optionnel
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        templates = templates.filter(discipline_id=discipline_id)
    
    competition_type_id = request.GET.get('competition_type')
    if competition_type_id:
        templates = templates.filter(competition_type_id=competition_type_id)
    
    context = {
        'templates': templates,
        'disciplines': Discipline.objects.all(),
        'competition_types': CompetitionType.objects.all(),
    }
    
    return render(request, 'competitions/categories/templates_list.html', context)

@login_required
@require_http_methods(["POST"])
def import_templates(request, competition_id):
    """Importer des templates de catégories dans une compétition."""
    competition = get_object_or_404(Competition, id=competition_id)
    template_ids = request.POST.getlist('template_ids')
    
    if template_ids:
        with transaction.atomic():
            for template_id in template_ids:
                template = get_object_or_404(CategoryTemplate, id=template_id)
                # Vérifier si une catégorie similaire existe déjà
                existing = CompetitionCategory.objects.filter(
                    competition=competition,
                    competition_type=template.competition_type,
                    name=template.name
                ).exists()
                
                if not existing:
                    CompetitionCategory.objects.create(
                        competition=competition,
                        competition_type=template.competition_type,
                        template=template,
                        name=template.name,
                        min_age=template.min_age,
                        max_age=template.max_age,
                        min_grade=template.min_grade,  # Maintenant un objet Grade
                        max_grade=template.max_grade,  # Maintenant un objet Grade
                        min_weight=template.min_weight,
                        max_weight=template.max_weight,
                        gender=template.gender
                    )
            
            messages.success(request, _("Templates importés avec succès."))
    else:
        messages.warning(request, _("Aucun template sélectionné."))
    
    return redirect('competitions:categories', competition_id=competition.id)

@login_required
def auto_generate_categories(request, competition_id):
    """Génération automatique des catégories basée sur les participants."""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Cette fonction serait plus complexe en réalité
    # Elle analyserait les participants inscrits et créerait des catégories appropriées
    
    messages.info(request, _("La génération automatique des catégories n'est pas encore implémentée."))
    return redirect('competitions:categories', competition_id=competition.id)

@login_required
def category_participants(request, category_id):
    """Liste des participants inscrits dans une catégorie."""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    
    # Si votre modèle a une relation avec les participants
    participants = category.registrations.all() if hasattr(category, 'registrations') else []
    
    context = {
        'category': category,
        'participants': participants,
        'competition': category.competition
    }
    
    return render(request, 'competitions/categories/participants.html', context)

# Fonction utilitaire pour API dynamique des grades
@login_required
def get_discipline_grades(request, discipline_id):
    """API pour récupérer les grades d'une discipline spécifique."""
    discipline = get_object_or_404(Discipline, id=discipline_id)
    grades = get_grades_for_discipline(discipline)
    
    grades_data = [
        {'id': grade.id, 'name': grade.name, 'level': grade.level}
        for grade in grades
    ]
    
    return JsonResponse({'grades': grades_data})