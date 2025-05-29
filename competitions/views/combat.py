"""
Vues pour la gestion des combats.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

# Importation de notre helper de permission personnalisé
from competitions.utils.permission_helpers import manual_permission_check, get_user_club

import json
import random
import logging

from competitions.models.combat import (
    CombatConfiguration, 
    Equipe, 
    MembreEquipe, 
    Poule, 
    Combat, 
    ActionCombat
)
from competitions.forms.combat_forms import (
    CombatConfigurationForm,
    EquipeForm,
    MembreEquipeForm,
    PouleForm,
    CombatForm,
    ActionCombatForm,
    GenerationPoulesForm,
    AttributionPointForm
)

logger = logging.getLogger(__name__)

# Vues pour la configuration des combats
@login_required
def liste_configurations(request):
    """
    Affiche la liste des configurations de combat disponibles.
    """
    configurations = CombatConfiguration.objects.all().order_by('discipline__name', 'nom')
    return render(request, 'competitions/combat/liste_configurations.html', {
        'configurations': configurations
    })

@login_required
def creer_configuration(request):
    """Permet de créer une nouvelle configuration de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    if request.method == 'POST':
        form = CombatConfigurationForm(request.POST)
        if form.is_valid():
            configuration = form.save()
            messages.success(request, _("La configuration de combat a été créée avec succès."))
            return redirect('competitions:combat:liste_configurations')
    else:
        form = CombatConfigurationForm()
    
    return render(request, 'competitions/combat/form_configuration.html', {
        'form': form,
        'title': _("Créer une configuration de combat")
    })

@login_required
def modifier_configuration(request, config_id):
    """Permet de modifier une configuration de combat existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    configuration = get_object_or_404(CombatConfiguration, id=config_id)
    
    if request.method == 'POST':
        form = CombatConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, _("La configuration de combat a été modifiée avec succès."))
            return redirect('competitions:combat:liste_configurations')
    else:
        form = CombatConfigurationForm(instance=configuration)
    
    return render(request, 'competitions/combat/form_configuration.html', {
        'form': form,
        'configuration': configuration,
        'title': _("Modifier une configuration de combat")
    })

@login_required
def supprimer_configuration(request, config_id):
    """Permet de supprimer une configuration de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    configuration = get_object_or_404(CombatConfiguration, id=config_id)
    
    if request.method == 'POST':
        configuration.delete()
        messages.success(request, _("La configuration de combat a été supprimée avec succès."))
        return redirect('competitions:combat:liste_configurations')
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': configuration,
        'title': _("Supprimer la configuration de combat"),
        'message': _("Êtes-vous sûr de vouloir supprimer cette configuration de combat ?"),
        'cancel_url': reverse('competitions:liste_configurations')
    })

# Vues pour la gestion des équipes
@login_required
def liste_equipes(request, competition_id=None):
    """
    Affiche la liste des équipes, filtrées par compétition si spécifié.
    """
    if competition_id:
        from competitions.models import Competition
        competition = get_object_or_404(Competition, id=competition_id)
        equipes = Equipe.objects.filter(competition=competition).order_by('nom')
        context = {
            'equipes': equipes,
            'competition': competition
        }
    else:
        equipes = Equipe.objects.all().order_by('-created_at', 'nom')
        context = {'equipes': equipes}
    
    return render(request, 'competitions/combat/liste_equipes.html', context)

@login_required
def creer_equipe(request, competition_id=None):
    """Permet de créer une nouvelle équipe, avec pré-sélection de la compétition si spécifiée."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from competitions.models import Competition
    
    initial = {}
    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        initial['competition'] = competition
    
    if request.method == 'POST':
        form = EquipeForm(request.POST)
        if form.is_valid():
            equipe = form.save()
            messages.success(request, _("L'équipe a été créée avec succès."))
            return redirect('competitions:detail_equipe', equipe_id=equipe.id)
    else:
        form = EquipeForm(initial=initial)
    
    return render(request, 'competitions/combat/form_equipe.html', {
        'form': form,
        'title': _("Créer une équipe")
    })

@login_required
def detail_equipe(request, equipe_id):
    """
    Affiche les détails d'une équipe, y compris ses membres.
    """
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membres = MembreEquipe.objects.filter(equipe=equipe).order_by('ordre', '-est_remplacant')
    
    context = {
        'equipe': equipe,
        'membres': membres,
        'titulaires': membres.filter(est_remplacant=False).count(),
        'remplacants': membres.filter(est_remplacant=True).count()
    }
    
    return render(request, 'competitions/combat/detail_equipe.html', context)

@login_required
def modifier_equipe(request, equipe_id):
    """Permet de modifier une équipe existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)
    
    if request.method == 'POST':
        form = EquipeForm(request.POST, instance=equipe)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'équipe a été modifiée avec succès."))
            return redirect('competitions:detail_equipe', equipe_id=equipe.id)
    else:
        form = EquipeForm(instance=equipe)
    
    return render(request, 'competitions/combat/form_equipe.html', {
        'form': form,
        'equipe': equipe,
        'title': _("Modifier l'équipe")
    })

@login_required
def supprimer_equipe(request, equipe_id):
    """Permet de supprimer une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)
    
    if request.method == 'POST':
        competition_id = equipe.competition.id
        equipe.delete()
        messages.success(request, _("L'équipe a été supprimée avec succès."))
        return redirect('competitions:liste_equipes', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': equipe,
        'title': _("Supprimer l'équipe"),
        'message': _("Êtes-vous sûr de vouloir supprimer cette équipe ? Cette action supprimera également tous les membres associés."),
        'cancel_url': reverse('competitions:detail_equipe', kwargs={'equipe_id': equipe.id})
    })

@login_required
def ajouter_membre_equipe(request, equipe_id):
    """Permet d'ajouter un membre à une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)
    
    if request.method == 'POST':
        form = MembreEquipeForm(request.POST)
        if form.is_valid():
            # Vérifier si ce pratiquant n'est pas déjà membre de cette équipe
            membre = form.save(commit=False)
            if MembreEquipe.objects.filter(equipe=equipe, pratiquant=membre.pratiquant).exists():
                messages.error(request, _("Ce pratiquant est déjà membre de cette équipe."))
            else:
                membre.equipe = equipe
                membre.save()
                messages.success(request, _("Le membre a été ajouté à l'équipe avec succès."))
                return redirect('competitions:detail_equipe', equipe_id=equipe.id)
    else:
        form = MembreEquipeForm(initial={'equipe': equipe})
    
    return render(request, 'competitions/combat/form_membre_equipe.html', {
        'form': form,
        'equipe': equipe,
        'title': _("Ajouter un membre à l'équipe")
    })

@login_required
def modifier_membre_equipe(request, membre_id):
    """Permet de modifier le statut d'un membre d'équipe (titulaire/remplaçant, ordre)."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    membre = get_object_or_404(MembreEquipe, id=membre_id)
    
    if request.method == 'POST':
        form = MembreEquipeForm(request.POST, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le membre de l'équipe a été modifié avec succès."))
            return redirect('competitions:detail_equipe', equipe_id=membre.equipe.id)
    else:
        form = MembreEquipeForm(instance=membre)
    
    return render(request, 'competitions/combat/form_membre_equipe.html', {
        'form': form,
        'membre': membre,
        'equipe': membre.equipe,
        'title': _("Modifier le membre de l'équipe")
    })

@login_required
def supprimer_membre_equipe(request, membre_id):
    """Permet de supprimer un membre d'une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    membre = get_object_or_404(MembreEquipe, id=membre_id)
    equipe_id = membre.equipe.id
    
    if request.method == 'POST':
        membre.delete()
        messages.success(request, _("Le membre a été retiré de l'équipe avec succès."))
        return redirect('competitions:detail_equipe', equipe_id=equipe_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': membre,
        'title': _("Retirer le membre de l'équipe"),
        'message': _("Êtes-vous sûr de vouloir retirer ce membre de l'équipe ?"),
        'cancel_url': reverse('competitions:detail_equipe', kwargs={'equipe_id': equipe_id})
    })

# Vues pour la gestion des poules
@login_required
def liste_poules(request, competition_id):
    """
    Affiche la liste des poules pour une compétition.
    """
    from competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)
    poules = Poule.objects.filter(competition=competition).order_by('phase', 'numero')
    
    return render(request, 'competitions/combat/liste_poules.html', {
        'competition': competition,
        'poules': poules
    })

@login_required
def creer_poule(request, competition_id):
    """Permet de créer une nouvelle poule pour une compétition."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)
    
    if request.method == 'POST':
        form = PouleForm(request.POST)
        if form.is_valid():
            poule = form.save(commit=False)
            poule.competition = competition
            poule.save()
            
            # Enregistrer les relations ManyToMany
            form.save_m2m()
            
            messages.success(request, _("La poule a été créée avec succès."))
            return redirect('competitions:detail_poule', poule_id=poule.id)
    else:
        # Prérégler le numéro de poule au nombre actuel + 1
        next_num = Poule.objects.filter(competition=competition).count() + 1
        form = PouleForm(initial={
            'competition': competition,
            'numero': next_num,
            'nom': f"Poule {next_num}"
        })
    
    return render(request, 'competitions/combat/form_poule.html', {
        'form': form,
        'competition': competition,
        'title': _("Créer une poule")
    })

@login_required
def detail_poule(request, poule_id):
    """
    Affiche les détails d'une poule, y compris les équipes/participants et les combats.
    """
    poule = get_object_or_404(Poule, id=poule_id)
    combats = Combat.objects.filter(poule=poule).order_by('date_planifiee')
    
    return render(request, 'competitions/combat/detail_poule.html', {
        'poule': poule,
        'combats': combats,
        'equipes': poule.equipes.all(),
        'pratiquants': poule.pratiquants.all()
    })

@login_required
def modifier_poule(request, poule_id):
    """Permet de modifier une poule existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    poule = get_object_or_404(Poule, id=poule_id)
    
    if request.method == 'POST':
        form = PouleForm(request.POST, instance=poule)
        if form.is_valid():
            form.save()
            messages.success(request, _("La poule a été modifiée avec succès."))
            return redirect('competitions:detail_poule', poule_id=poule.id)
    else:
        form = PouleForm(instance=poule)
    
    return render(request, 'competitions/combat/form_poule.html', {
        'form': form,
        'poule': poule,
        'competition': poule.competition,
        'title': _("Modifier la poule")
    })

@login_required
def supprimer_poule(request, poule_id):
    """Permet de supprimer une poule."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    poule = get_object_or_404(Poule, id=poule_id)
    competition_id = poule.competition.id
    
    if request.method == 'POST':
        poule.delete()
        messages.success(request, _("La poule a été supprimée avec succès."))
        return redirect('competitions:liste_poules', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': poule,
        'title': _("Supprimer la poule"),
        'message': _("Êtes-vous sûr de vouloir supprimer cette poule ? Cette action supprimera également tous les combats associés."),
        'cancel_url': reverse('competitions:detail_poule', kwargs={'poule_id': poule.id})
    })

@login_required
def generer_poules(request, competition_id):
    """Permet de générer automatiquement des poules pour une compétition."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)
    
    if request.method == 'POST':
        form = GenerationPoulesForm(request.POST)
        if form.is_valid():
            nombre_poules = form.cleaned_data['nombre_poules']
            eviter_clubs = form.cleaned_data['eviter_clubs_meme_poule']
            eviter_pays = form.cleaned_data['eviter_pays_meme_poule']
            
            # Sélectionner les équipes et/ou pratiquants individuels qui ne sont pas déjà dans une poule
            equipes_disponibles = Equipe.objects.filter(
                competition=competition
            ).exclude(
                poules__competition=competition
            )
            
            from competitions.models import Practitioner
            pratiquants_disponibles = Practitioner.objects.filter(
                equipe_memberships__equipe__competition=competition
            ).exclude(
                poules_individuelles__competition=competition
            ).distinct()
            
            # Créer les poules et distribuer les participants
            poules_creees = 0
            
            if equipes_disponibles.exists():
                # Distribution des équipes en poules
                equipes_list = list(equipes_disponibles)
                random.shuffle(equipes_list)
                
                # Algorithme pour éviter les équipes du même club/pays dans la même poule
                if eviter_clubs or eviter_pays:
                    # TODO: Implémenter un algorithme plus sophistiqué
                    pass
                
                # Créer les poules et distribuer les équipes
                nb_equipes_par_poule = max(1, len(equipes_list) // nombre_poules)
                for i in range(min(nombre_poules, len(equipes_list))):
                    start_idx = i * nb_equipes_par_poule
                    end_idx = min((i + 1) * nb_equipes_par_poule, len(equipes_list))
                    
                    poule = Poule.objects.create(
                        competition=competition,
                        nom=f"Poule {i+1}",
                        numero=i+1,
                        phase='eliminatoire'
                    )
                    
                    for equipe in equipes_list[start_idx:end_idx]:
                        poule.equipes.add(equipe)
                    
                    poules_creees += 1
            
            if pratiquants_disponibles.exists() and poules_creees < nombre_poules:
                # Gestion des pratiquants individuels si nécessaire
                pass
            
            messages.success(request, _("{} poules ont été créées avec succès.").format(poules_creees))
            return redirect('competitions:liste_poules', competition_id=competition.id)
    else:
        form = GenerationPoulesForm(initial={'competition': competition})
    
    return render(request, 'competitions/combat/generer_poules.html', {
        'form': form,
        'competition': competition,
        'title': _("Générer des poules automatiquement")
    })

# Vues pour la gestion des combats
@login_required
def liste_combats(request, competition_id=None, poule_id=None):
    """
    Affiche la liste des combats, filtrés par compétition et/ou poule si spécifié.
    """
    from competitions.models import Competition
    
    if poule_id:
        poule = get_object_or_404(Poule, id=poule_id)
        competition = poule.competition
        combats = Combat.objects.filter(poule=poule)
        context = {
            'combats': combats,
            'competition': competition,
            'poule': poule,
            'title': _("Combats de la poule {}").format(poule.nom)
        }
    elif competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        combats = Combat.objects.filter(competition=competition)
        context = {
            'combats': combats,
            'competition': competition,
            'title': _("Combats de la compétition")
        }
    else:
        combats = Combat.objects.all().order_by('-date_planifiee')
        context = {
            'combats': combats,
            'title': _("Tous les combats")
        }
    
    # Pagination
    paginator = Paginator(combats.order_by('-date_planifiee', 'status'), 20)
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)
    
    return render(request, 'competitions/combat/liste_combats.html', context)

@login_required
def detail_combat(request, combat_id):
    """
    Affiche les détails d'un combat, y compris les actions et les scores.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('temps')
    
    context = {
        'combat': combat,
        'actions': actions,
        'can_start': combat.status == 'planifie',
        'can_end': combat.status == 'en_cours',
        'configuration': combat.configuration,
        'point_form': AttributionPointForm(combat=combat) if combat.status == 'en_cours' else None
    }
    
    return render(request, 'competitions/combat/detail_combat.html', context)

@login_required
def creer_combat(request, competition_id=None, poule_id=None):
    """Permet de créer un nouveau combat, avec pré-sélection de la compétition et/ou poule."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from competitions.models import Competition
    
    initial = {}
    if poule_id:
        poule = get_object_or_404(Poule, id=poule_id)
        competition = poule.competition
        initial['poule'] = poule
        initial['competition'] = competition
    elif competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        initial['competition'] = competition
    
    if request.method == 'POST':
        form = CombatForm(request.POST)
        if form.is_valid():
            combat = form.save()
            messages.success(request, _("Le combat a été créé avec succès."))
            return redirect('competitions:detail_combat', combat_id=combat.id)
    else:
        form = CombatForm(initial=initial)
    
    return render(request, 'competitions/combat/form_combat.html', {
        'form': form,
        'title': _("Créer un combat")
    })

@login_required
def modifier_combat(request, combat_id):
    """Permet de modifier un combat existant."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        form = CombatForm(request.POST, instance=combat)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le combat a été modifié avec succès."))
            return redirect('competitions:detail_combat', combat_id=combat.id)
    else:
        form = CombatForm(instance=combat)
    
    return render(request, 'competitions/combat/form_combat.html', {
        'form': form,
        'combat': combat,
        'title': _("Modifier le combat")
    })

@login_required
def supprimer_combat(request, combat_id):
    """Permet de supprimer un combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        poule_id = combat.poule.id if combat.poule else None
        competition_id = combat.competition.id
        combat.delete()
        messages.success(request, _("Le combat a été supprimé avec succès."))
        
        if poule_id:
            return redirect('competitions:liste_combats', poule_id=poule_id)
        else:
            return redirect('competitions:liste_combats', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': combat,
        'title': _("Supprimer le combat"),
        'message': _("Êtes-vous sûr de vouloir supprimer ce combat ? Cette action supprimera également toutes les actions associées."),
        'cancel_url': reverse('competitions:detail_combat', kwargs={'combat_id': combat.id})
    })

@login_required
def demarrer_combat(request, combat_id):
    """Permet de démarrer un combat planifié."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.start_combat():
        messages.success(request, _("Le combat a été démarré."))
    else:
        messages.error(request, _("Impossible de démarrer ce combat."))
    
    return redirect('competitions:detail_combat', combat_id=combat.id)

@login_required
def terminer_combat(request, combat_id):
    """Permet de terminer un combat en cours."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.end_combat():
        # Déterminer le vainqueur automatiquement
        if combat.score_rouge > combat.score_blanc:
            messages.success(request, _("Combat terminé. Victoire de l'équipe/pratiquant rouge."))
        elif combat.score_blanc > combat.score_rouge:
            messages.success(request, _("Combat terminé. Victoire de l'équipe/pratiquant blanc."))
        else:
            messages.success(request, _("Combat terminé. Match nul."))
    else:
        messages.error(request, _("Impossible de terminer ce combat."))
    
    return redirect('competitions:detail_combat', combat_id=combat.id)

@login_required
def annuler_combat(request, combat_id):
    """Permet d'annuler un combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        if combat.cancel_combat(motif):
            messages.success(request, _("Le combat a été annulé."))
        else:
            messages.error(request, _("Impossible d'annuler ce combat."))
        return redirect('competitions:detail_combat', combat_id=combat.id)
    
    return render(request, 'competitions/combat/annuler_combat.html', {
        'combat': combat,
        'title': _("Annuler le combat")
    })

# Vues pour la gestion des actions de combat (API)
@login_required
@csrf_exempt
def ajouter_action(request, combat_id):
    """Permet d'ajouter une action à un combat en cours (en AJAX ou formulaire standard)."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.status != 'en_cours':
        messages.error(request, _("Impossible d'ajouter une action à un combat qui n'est pas en cours."))
        return JsonResponse({'success': False, 'error': "Combat non actif"}, status=400) if request.is_ajax() else redirect('competitions:detail_combat', combat_id=combat.id)
    
    if request.method == 'POST':
        # Gérer à la fois les requêtes AJAX et les soumissions de formulaire
        if request.is_ajax():
            data = json.loads(request.body)
            type_action = data.get('type_action')
            couleur = data.get('couleur')
            valeur = float(data.get('valeur', 0))
            description = data.get('description', '')
            arbitre_id = data.get('arbitre_id')
        else:
            # Traiter les formulaires AttributionPointForm
            form = AttributionPointForm(request.POST, combat=combat)
            if form.is_valid():
                type_action = form.cleaned_data['type_action']
                couleur = form.cleaned_data['couleur']
                
                if type_action == 'point':
                    valeur = float(form.cleaned_data['valeur_point'])
                else:  # type_action == 'penalite'
                    valeur = float(form.cleaned_data['valeur_penalite'])
                
                description = ""
                arbitre_id = request.user.id if hasattr(request.user, 'judge') else None
            else:
                messages.error(request, _("Formulaire invalide."))
                return redirect('competitions:detail_combat', combat_id=combat.id)
        
        # Créer l'action
        action = ActionCombat(
            combat=combat,
            type_action=type_action,
            couleur=couleur,
            valeur=valeur,
            description=description
        )
        
        if arbitre_id:
            from competitions.models import Judge
            try:
                action.arbitre = Judge.objects.get(id=arbitre_id)
            except Judge.DoesNotExist:
                pass
        
        action.save()
        
        # Mettre à jour le combat (fait automatiquement par le modèle ActionCombat)
        combat.refresh_from_db()
        
        if request.is_ajax():
            return JsonResponse({
                'success': True, 
                'action_id': action.id,
                'score_rouge': float(combat.score_rouge),
                'score_blanc': float(combat.score_blanc)
            })
        else:
            messages.success(request, _("L'action a été enregistrée."))
            return redirect('competitions:detail_combat', combat_id=combat.id)
    
    messages.error(request, _("Méthode non autorisée."))
    return JsonResponse({'success': False, 'error': "Méthode non autorisée"}, status=405) if request.is_ajax() else redirect('competitions:detail_combat', combat_id=combat.id)

@login_required
def annuler_action(request, action_id):
    """Permet d'annuler une action de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    action = get_object_or_404(ActionCombat, id=action_id)
    combat = action.combat
    
    if combat.status != 'en_cours':
        messages.error(request, _("Impossible d'annuler une action d'un combat qui n'est pas en cours."))
        return redirect('competitions:detail_combat', combat_id=combat.id)
    
    # Inverser l'effet de l'action sur le score
    if action.type_action in ['point', 'penalite']:
        if action.couleur == 'rouge':
            combat.score_rouge -= action.valeur
        elif action.couleur == 'blanc':
            combat.score_blanc -= action.valeur
        
        combat.save()
    
    # Supprimer l'action
    action.delete()
    
    messages.success(request, _("L'action a été annulée."))
    return redirect('competitions:detail_combat', combat_id=combat.id)

# Interface de combat en temps réel
@login_required
def interface_combat(request, combat_id):
    """
    Affiche l'interface de combat en temps réel, optimisée pour l'arbitrage.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    
    context = {
        'combat': combat,
        'is_judge': hasattr(request.user, 'judge'),
        'point_form': AttributionPointForm(combat=combat) if combat.status == 'en_cours' else None
    }
    
    if combat.configuration:
        context['valeurs_points'] = combat.configuration.valeurs_points
        context['valeurs_penalites'] = combat.configuration.valeurs_penalites
    
    return render(request, 'competitions/combat/interface_combat.html', context)


@login_required
def monitor_match(request, combat_id):
    """
    Affiche l'interface de suivi en temps réel optimisée pour les juges et les coachs.
    Cette vue utilise JavaScript pour mettre à jour les scores et actions en temps réel.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:10]
    
    # Vérifier si l'utilisateur a le droit d'éditer (arbitre central ou staff)
    can_edit = request.user.is_staff
    if hasattr(request.user, 'judge'):
        can_edit = can_edit or (combat.arbitre_central and combat.arbitre_central.user == request.user)
    
    context = {
        'combat': combat,
        'actions': actions,
        'can_edit': can_edit
    }
    
    return render(request, 'competitions/combat/monitor_live.html', context)

@login_required
def affichage_combat(request, combat_id):
    """
    Affiche le tableau de score grand écran pour le public.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    return render(request, 'competitions/combat/affichage_combat.html', {
        'combat': combat
    })

# API pour l'interface temps réel
@login_required
def api_statut_combat(request, combat_id):
    """
    API JSON retournant le statut actuel d'un combat.
    Utilisé pour l'interface temps réel avec polling.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:10]
    
    # Calculer le temps écoulé si le combat est en cours
    elapsed_time = None
    if combat.status == 'en_cours' and combat.debut_combat:
        elapsed_seconds = (timezone.now() - combat.debut_combat).total_seconds()
        elapsed_time = min(elapsed_seconds, combat.duree_combat)
    
    data = {
        'id': combat.id,
        'uuid': str(combat.uuid),
        'status': combat.status,
        'score_rouge': float(combat.score_rouge),
        'score_blanc': float(combat.score_blanc),
        'debut_combat': combat.debut_combat.isoformat() if combat.debut_combat else None,
        'fin_combat': combat.fin_combat.isoformat() if combat.fin_combat else None,
        'type_combat': combat.type_combat,
        'derniere_action': None,
        'elapsed_time': int(elapsed_time) if elapsed_time is not None else None,
        'total_time': combat.duree_combat,
        'vainqueur': combat.vainqueur,
        'est_nul': combat.est_nul,
        'actions': []
    }
    
    # Informations des participants
    if combat.type_combat == 'individuel':
        data['rouge'] = {
            'id': combat.pratiquant_rouge.id,
            'nom': combat.pratiquant_rouge.full_name
        } if combat.pratiquant_rouge else None
        
        data['blanc'] = {
            'id': combat.pratiquant_blanc.id,
            'nom': combat.pratiquant_blanc.full_name
        } if combat.pratiquant_blanc else None
    else:
        data['rouge'] = {
            'id': combat.equipe_rouge.id,
            'nom': combat.equipe_rouge.nom
        } if combat.equipe_rouge else None
        
        data['blanc'] = {
            'id': combat.equipe_blanc.id,
            'nom': combat.equipe_blanc.nom
        } if combat.equipe_blanc else None
    
    # Liste des actions récentes
    for action in actions:
        action_data = {
            'id': action.id,
            'action_type': action.type_action,
            'team': 'red' if action.couleur == 'rouge' else 'blue' if action.couleur == 'blanc' else 'neutral',
            'points': float(action.valeur),
            'description': action.description,
            'timestamp': action.temps.isoformat(),
            'judge': action.arbitre.user.get_full_name() if action.arbitre else None,
        }
        data['actions'].append(action_data)
        
        # Également définir la dernière action pour compatibilité
        if not data['derniere_action'] and actions.exists():
            derniere = actions.first()
            data['derniere_action'] = {
                'id': derniere.id,
                'type': derniere.type_action,
                'couleur': derniere.couleur,
                'valeur': float(derniere.valeur),
                'temps': derniere.temps.isoformat(),
                'description': derniere.description
            }
    
    return JsonResponse(data)

@login_required
def api_liste_actions(request, combat_id):
    """
    API JSON retournant la liste des actions d'un combat.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')
    
    data = {
        'id': combat.id,
        'actions': []
    }
    
    for action in actions:
        data['actions'].append({
            'id': action.id,
            'type': action.type_action,
            'couleur': action.couleur,
            'valeur': float(action.valeur),
            'temps': action.temps.isoformat(),
            'description': action.description
        })
    
    return JsonResponse(data)