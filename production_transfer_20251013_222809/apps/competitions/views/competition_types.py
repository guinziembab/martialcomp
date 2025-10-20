from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from ..models import CompetitionType, Discipline
from ..forms import CompetitionTypeForm


@login_required
def competition_type_list(request):
    """Liste des types de compétition avec filtres et recherche."""
    types = CompetitionType.objects.select_related('discipline').all()
    
    # Filtres
    discipline_filter = request.GET.get('discipline')
    search_query = request.GET.get('q')
    
    if discipline_filter:
        types = types.filter(discipline_id=discipline_filter)
    
    if search_query:
        types = types.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(types, 20)
    page = request.GET.get('page')
    types_page = paginator.get_page(page)
    
    # Contexte
    disciplines = Discipline.objects.filter(is_active=True)
    
    context = {
        'types': types_page,
        'disciplines': disciplines,
        'discipline_filter': discipline_filter,
        'search_query': search_query,
    }
    
    return render(request, 'competitions/competition_types/list.html', context)


@login_required
def competition_type_create(request):
    """Créer un nouveau type de compétition."""
    if request.method == 'POST':
        form = CompetitionTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le type de compétition a été créé avec succès."))
            return redirect('competitions:competition_types:list')
    else:
        form = CompetitionTypeForm()
    
    context = {
        'form': form,
        'title': _("Créer un type de compétition"),
    }
    
    return render(request, 'competitions/competition_types/form.html', context)


@login_required
def competition_type_detail(request, pk):
    """Détail d'un type de compétition."""
    type_obj = get_object_or_404(CompetitionType, pk=pk)
    
    context = {
        'type_obj': type_obj,
    }
    
    return render(request, 'competitions/competition_types/detail.html', context)


@login_required
def competition_type_update(request, pk):
    """Modifier un type de compétition."""
    type_obj = get_object_or_404(CompetitionType, pk=pk)
    
    if request.method == 'POST':
        form = CompetitionTypeForm(request.POST, instance=type_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le type de compétition a été modifié avec succès."))
            return redirect('competitions:competition_types:detail', pk=type_obj.pk)
    else:
        form = CompetitionTypeForm(instance=type_obj)
    
    context = {
        'form': form,
        'type_obj': type_obj,
        'title': _("Modifier le type de compétition"),
    }
    
    return render(request, 'competitions/competition_types/form.html', context)


@login_required
def competition_type_delete(request, pk):
    """Supprimer un type de compétition."""
    type_obj = get_object_or_404(CompetitionType, pk=pk)
    
    if request.method == 'POST':
        type_obj.delete()
        messages.success(request, _("Le type de compétition a été supprimé avec succès."))
        return redirect('competitions:competition_types:list')
    
    context = {
        'type_obj': type_obj,
    }
    
    return render(request, 'competitions/competition_types/confirm_delete.html', context)


@login_required
def competition_type_api_list(request):
    """API pour récupérer les types de compétition (AJAX)."""
    discipline_id = request.GET.get('discipline_id')
    
    if discipline_id:
        types = CompetitionType.objects.filter(discipline_id=discipline_id)
    else:
        types = CompetitionType.objects.all()
    
    types_data = [
        {
            'id': type_obj.id,
            'name': type_obj.name,
            'description': type_obj.description,
            'scoring_system': type_obj.scoring_system,
            'team_based': type_obj.team_based,
            'discipline': type_obj.discipline.name,
        }
        for type_obj in types
    ]
    
    return JsonResponse({
        'types': types_data,
        'count': len(types_data)
    })