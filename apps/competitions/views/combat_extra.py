"""
Vues supplémentaires pour la gestion avancée des combats
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
import json

from apps.competitions.models.combat import Combat, Poule
from apps.competitions.models import Competition
from apps.competitions.utils.permission_helpers import manual_permission_check

@login_required
@csrf_exempt
def update_duree_combat(request, combat_id):
    """Met à jour les durées d'un combat spécifique."""
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
    
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            duree_combat = int(data.get('duree_combat', 120))
            duree_prolongation = data.get('duree_prolongation')
            
            # Validation
            if duree_combat not in [60, 90, 120, 180, 240]:
                return JsonResponse({'success': False, 'error': 'Durée invalide'})
            
            # Mise à jour
            combat.duree_combat = duree_combat
            if duree_prolongation:
                combat.duree_prolongation = int(duree_prolongation)
            else:
                combat.duree_prolongation = None
            
            combat.save()
            
            return JsonResponse({
                'success': True,
                'duree_combat': combat.duree_combat,
                'duree_prolongation': combat.duree_prolongation
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


@login_required
def suivi_poule(request, poule_id):
    """Affiche le suivi en temps réel d'une poule avec ordre de passage."""
    poule = get_object_or_404(Poule, id=poule_id)
    
    # Récupérer tous les combats de la poule
    combats = Combat.objects.filter(poule=poule).order_by('date_planifiee', 'id')
    
    # Calculer les statistiques
    combats_termines = combats.filter(status='termine').count()
    combats_en_cours = combats.filter(status='en_cours').count()
    combats_planifies = combats.filter(status='planifie').count()
    
    # Classement actuel (équipes ou individuels)
    classement = []
    is_team_mode = poule.equipes.exists()

    # Fallback: détecter équipes depuis les combats si M2M vide
    if not is_team_mode and not poule.pratiquants.exists():
        has_combat_equipes = combats.filter(equipe_rouge__isnull=False).exists()
        if has_combat_equipes:
            is_team_mode = True

    if is_team_mode:
        equipes_list = list(poule.equipes.all())
        if not equipes_list:
            from apps.competitions.models.combat import Equipe
            equipe_ids = set()
            for c in combats:
                if c.equipe_rouge_id:
                    equipe_ids.add(c.equipe_rouge_id)
                if c.equipe_blanc_id:
                    equipe_ids.add(c.equipe_blanc_id)
            equipes_list = list(Equipe.objects.filter(id__in=equipe_ids))

        for equipe in equipes_list:
            victoires = Combat.objects.filter(
                Q(poule=poule, status='termine') &
                (
                    Q(equipe_rouge=equipe, vainqueur='rouge') |
                    Q(equipe_blanc=equipe, vainqueur='blanc')
                )
            ).count()

            points_marques = Combat.objects.filter(
                Q(poule=poule, status='termine') &
                (Q(equipe_rouge=equipe) | Q(equipe_blanc=equipe))
            ).aggregate(
                total_rouge=Sum('score_rouge', default=0),
                total_blanc=Sum('score_blanc', default=0)
            )

            classement.append({
                'nom': equipe.nom,
                'club_name': equipe.club.name if equipe.club else '-',
                'equipe': equipe,
                'is_team': True,
                'victoires': victoires,
                'points': points_marques
            })

        classement.sort(key=lambda x: (-x['victoires'], -(x['points']['total_rouge'] + x['points']['total_blanc'])))

    elif poule.pratiquants.exists():
        for pratiquant in poule.pratiquants.all():
            victoires = Combat.objects.filter(
                Q(poule=poule, status='termine') &
                (
                    Q(pratiquant_rouge=pratiquant, vainqueur='rouge') |
                    Q(pratiquant_blanc=pratiquant, vainqueur='blanc')
                )
            ).count()

            points_marques = Combat.objects.filter(
                Q(poule=poule, status='termine') &
                (Q(pratiquant_rouge=pratiquant) | Q(pratiquant_blanc=pratiquant))
            ).aggregate(
                total_rouge=Sum('score_rouge', default=0),
                total_blanc=Sum('score_blanc', default=0)
            )

            classement.append({
                'nom': pratiquant.full_name,
                'club_name': pratiquant.club.name if pratiquant.club else '-',
                'pratiquant': pratiquant,
                'is_team': False,
                'victoires': victoires,
                'points': points_marques
            })

        classement.sort(key=lambda x: (-x['victoires'], -(x['points']['total_rouge'] + x['points']['total_blanc'])))
    
    context = {
        'poule': poule,
        'combats': combats,
        'combats_termines': combats_termines,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
        'classement': classement,
        'progression': (combats_termines / combats.count() * 100) if combats.exists() else 0
    }
    
    return render(request, 'competitions/combat/suivi_poule.html', context)


@login_required
def classement_live(request, competition_id):
    """
    Affiche le classement en temps réel d'une compétition.
    Groupé par catégorie avec filtres par type de compétition.
    """
    from apps.competitions.models import CompetitionCategory, CompetitionType

    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer les filtres depuis GET
    selected_type_id = request.GET.get('type')
    selected_category_id = request.GET.get('category')

    # Récupérer tous les types de compétition disponibles
    competition_types = CompetitionType.objects.filter(
        categories__competition=competition
    ).distinct().order_by('name')

    # Récupérer toutes les catégories
    categories_query = CompetitionCategory.objects.filter(
        competition=competition
    ).select_related('competition_type').order_by('competition_type__name', 'name')

    # Appliquer le filtre par type si spécifié
    if selected_type_id:
        categories_query = categories_query.filter(competition_type_id=selected_type_id)

    # Appliquer le filtre par catégorie si spécifié
    if selected_category_id:
        categories_query = categories_query.filter(id=selected_category_id)

    # Récupérer toutes les poules avec leurs catégories
    poules = Poule.objects.filter(
        competition=competition,
        category__in=categories_query
    ).select_related('category', 'category__competition_type').order_by('category__name', 'phase', 'numero')

    # Construire le classement PAR CATÉGORIE et PAR POULE
    classements_par_categorie = {}

    for poule in poules:
        category = poule.category
        if not category:
            continue

        category_id = category.id

        if category_id not in classements_par_categorie:
            classements_par_categorie[category_id] = {
                'category': category,
                'competition_type': category.competition_type,
                'poules_data': [],  # Liste des poules avec leurs classements
                'classement': {},   # Classement global de la catégorie
                'combats_termines': 0,
                'combats_total': 0,
            }

        # Compter les combats de la poule
        combats_poule = Combat.objects.filter(poule=poule)
        poule_combats_total = combats_poule.count()
        poule_combats_termines = combats_poule.filter(status='termine').count()

        classements_par_categorie[category_id]['combats_total'] += poule_combats_total
        classements_par_categorie[category_id]['combats_termines'] += poule_combats_termines

        # Calculer le classement de cette poule
        classement_poule = {}

        # Déterminer le mode: équipe ou individuel
        is_team_mode = poule.equipes.exists()

        # Fallback: si la poule n'a pas d'équipes en M2M mais a des combats avec équipes
        # (cas des poules demi-finales/finales où les équipes ne sont pas ajoutées au M2M)
        if not is_team_mode and not poule.pratiquants.exists():
            has_combat_equipes = combats_poule.filter(equipe_rouge__isnull=False).exists()
            if has_combat_equipes:
                is_team_mode = True

        if is_team_mode:
            # MODE EQUIPE: récupérer les équipes depuis M2M ou depuis les combats
            equipes_m2m = list(poule.equipes.all())
            if not equipes_m2m:
                # Extraire les équipes uniques depuis les combats de cette poule
                from apps.competitions.models.combat import Equipe
                equipe_ids = set()
                for c in combats_poule:
                    if c.equipe_rouge_id:
                        equipe_ids.add(c.equipe_rouge_id)
                    if c.equipe_blanc_id:
                        equipe_ids.add(c.equipe_blanc_id)
                equipes_m2m = list(Equipe.objects.filter(id__in=equipe_ids))

            for equipe in equipes_m2m:
                eq_id = f'eq_{equipe.id}'

                # Récupérer les membres titulaires pour les photos
                team_members = list(
                    equipe.memberships.filter(est_remplacant=False)
                    .select_related('pratiquant')
                    .order_by('ordre')
                )

                entry_base = {
                    'nom': equipe.nom,
                    'club_name': equipe.club.name if equipe.club else '-',
                    'equipe': equipe,
                    'is_team': True,
                    'team_members': team_members,
                    'victoires': 0,
                    'points_pour': 0,
                    'points_contre': 0,
                    'combats': 0,
                    'combats_detail': [],
                }

                if eq_id not in classements_par_categorie[category_id]['classement']:
                    classements_par_categorie[category_id]['classement'][eq_id] = dict(entry_base)
                    classements_par_categorie[category_id]['classement'][eq_id]['combats_detail'] = []

                classement_poule[eq_id] = dict(entry_base)
                classement_poule[eq_id]['combats_detail'] = []

                combats_equipe = Combat.objects.filter(
                    Q(poule=poule, status='termine') &
                    (Q(equipe_rouge=equipe) | Q(equipe_blanc=equipe))
                ).select_related('equipe_rouge', 'equipe_blanc')

                for combat in combats_equipe:
                    entry_poule = classement_poule[eq_id]
                    entry_poule['combats'] += 1

                    entry_cat = classements_par_categorie[category_id]['classement'][eq_id]
                    entry_cat['combats'] += 1

                    if combat.equipe_rouge == equipe:
                        score_pour = float(combat.score_rouge or 0)
                        score_contre = float(combat.score_blanc or 0)
                        victoire = combat.vainqueur == 'rouge'
                        adversaire = combat.equipe_blanc.nom if combat.equipe_blanc else '-'
                    else:
                        score_pour = float(combat.score_blanc or 0)
                        score_contre = float(combat.score_rouge or 0)
                        victoire = combat.vainqueur == 'blanc'
                        adversaire = combat.equipe_rouge.nom if combat.equipe_rouge else '-'

                    resultat = 'nul'
                    if combat.est_nul:
                        resultat = 'nul'
                    elif victoire:
                        resultat = 'victoire'
                    else:
                        resultat = 'defaite'

                    combat_detail = {
                        'adversaire': adversaire,
                        'score_pour': score_pour,
                        'score_contre': score_contre,
                        'resultat': resultat,
                        'poule_nom': poule.nom,
                        'status': combat.get_status_display(),
                    }

                    entry_poule['combats_detail'].append(combat_detail)
                    entry_cat['combats_detail'].append(combat_detail)

                    entry_poule['points_pour'] += score_pour
                    entry_poule['points_contre'] += score_contre
                    entry_cat['points_pour'] += score_pour
                    entry_cat['points_contre'] += score_contre

                    if victoire:
                        entry_poule['victoires'] += 1
                        entry_cat['victoires'] += 1

        elif poule.pratiquants.exists():
            # MODE INDIVIDUEL: itérer sur les pratiquants
            for pratiquant in poule.pratiquants.all():
                prat_id = pratiquant.id

                entry_base = {
                    'nom': pratiquant.full_name,
                    'club_name': pratiquant.club.name if pratiquant.club else '-',
                    'pratiquant': pratiquant,
                    'is_team': False,
                    'victoires': 0,
                    'points_pour': 0,
                    'points_contre': 0,
                    'combats': 0,
                    'combats_detail': [],
                }

                if prat_id not in classements_par_categorie[category_id]['classement']:
                    classements_par_categorie[category_id]['classement'][prat_id] = dict(entry_base)
                    classements_par_categorie[category_id]['classement'][prat_id]['combats_detail'] = []

                classement_poule[prat_id] = dict(entry_base)
                classement_poule[prat_id]['combats_detail'] = []

                combats_pratiquant = Combat.objects.filter(
                    Q(poule=poule, status='termine') &
                    (Q(pratiquant_rouge=pratiquant) | Q(pratiquant_blanc=pratiquant))
                ).select_related('pratiquant_rouge', 'pratiquant_blanc')

                for combat in combats_pratiquant:
                    entry_poule = classement_poule[prat_id]
                    entry_poule['combats'] += 1

                    entry_cat = classements_par_categorie[category_id]['classement'][prat_id]
                    entry_cat['combats'] += 1

                    if combat.pratiquant_rouge == pratiquant:
                        score_pour = float(combat.score_rouge or 0)
                        score_contre = float(combat.score_blanc or 0)
                        victoire = combat.vainqueur == 'rouge'
                        adversaire = combat.pratiquant_blanc.full_name if combat.pratiquant_blanc else '-'
                    else:
                        score_pour = float(combat.score_blanc or 0)
                        score_contre = float(combat.score_rouge or 0)
                        victoire = combat.vainqueur == 'blanc'
                        adversaire = combat.pratiquant_rouge.full_name if combat.pratiquant_rouge else '-'

                    resultat = 'nul'
                    if combat.est_nul:
                        resultat = 'nul'
                    elif victoire:
                        resultat = 'victoire'
                    else:
                        resultat = 'defaite'

                    combat_detail = {
                        'adversaire': adversaire,
                        'score_pour': score_pour,
                        'score_contre': score_contre,
                        'resultat': resultat,
                        'poule_nom': poule.nom,
                        'status': combat.get_status_display(),
                    }

                    entry_poule['combats_detail'].append(combat_detail)
                    entry_cat['combats_detail'].append(combat_detail)

                    entry_poule['points_pour'] += score_pour
                    entry_poule['points_contre'] += score_contre
                    entry_cat['points_pour'] += score_pour
                    entry_cat['points_contre'] += score_contre

                    if victoire:
                        entry_poule['victoires'] += 1
                        entry_cat['victoires'] += 1

        # Convertir et trier le classement de la poule
        classement_poule_liste = list(classement_poule.values())
        classement_poule_liste.sort(key=lambda x: (
            -x['victoires'],
            -(x['points_pour'] - x['points_contre']),
            -x['points_pour']
        ))

        # Ajouter la poule avec son classement
        poule_progression = (poule_combats_termines / poule_combats_total * 100) if poule_combats_total > 0 else 0

        classements_par_categorie[category_id]['poules_data'].append({
            'poule': poule,
            'classement': classement_poule_liste,
            'combats_termines': poule_combats_termines,
            'combats_total': poule_combats_total,
            'progression': poule_progression,
            'podium': classement_poule_liste[:3] if len(classement_poule_liste) >= 3 else classement_poule_liste,
        })

    # Convertir et trier le classement global de chaque catégorie
    categories_avec_classement = []

    for cat_id, data in classements_par_categorie.items():
        classement_liste = list(data['classement'].values())
        classement_liste.sort(key=lambda x: (
            -x['victoires'],
            -(x['points_pour'] - x['points_contre']),
            -x['points_pour']
        ))

        progression = 0
        if data['combats_total'] > 0:
            progression = (data['combats_termines'] / data['combats_total']) * 100

        categories_avec_classement.append({
            'category': data['category'],
            'competition_type': data['competition_type'],
            'poules_data': data['poules_data'],  # Classements par poule
            'classement': classement_liste,       # Classement global catégorie
            'combats_termines': data['combats_termines'],
            'combats_total': data['combats_total'],
            'progression': progression,
            'podium': classement_liste[:3] if len(classement_liste) >= 3 else classement_liste,
            'has_multiple_poules': len(data['poules_data']) > 1,  # Flag pour affichage conditionnel
        })

    # Trier par type de compétition puis par nom de catégorie
    categories_avec_classement.sort(key=lambda x: (
        x['competition_type'].name if x['competition_type'] else '',
        x['category'].name
    ))

    # Statistiques globales
    total_combats = sum(c['combats_total'] for c in categories_avec_classement)
    total_termines = sum(c['combats_termines'] for c in categories_avec_classement)
    total_participants = sum(len(c['classement']) for c in categories_avec_classement)

    context = {
        'competition': competition,
        'categories_avec_classement': categories_avec_classement,
        'competition_types': competition_types,
        'all_categories': CompetitionCategory.objects.filter(competition=competition).order_by('name'),
        'selected_type_id': int(selected_type_id) if selected_type_id else None,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
        'total_combats': total_combats,
        'total_termines': total_termines,
        'total_participants': total_participants,
        'progression_globale': (total_termines / total_combats * 100) if total_combats > 0 else 0,
        'auto_refresh': True,
        'poules': poules,  # Pour compatibilité avec l'ancien template
    }

    return render(request, 'competitions/combat/classement_live.html', context)


@login_required
def classement_live_pdf(request, competition_id):
    """
    Génère un PDF exportable du classement de la compétition.
    Groupé par catégorie avec podium et classement complet.
    """
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from apps.competitions.models import CompetitionCategory, CompetitionType
    from io import BytesIO
    from datetime import datetime

    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer les filtres depuis GET
    selected_type_id = request.GET.get('type')
    selected_category_id = request.GET.get('category')

    # Récupérer toutes les catégories
    categories_query = CompetitionCategory.objects.filter(
        competition=competition
    ).select_related('competition_type').order_by('competition_type__name', 'name')

    if selected_type_id:
        categories_query = categories_query.filter(competition_type_id=selected_type_id)
    if selected_category_id:
        categories_query = categories_query.filter(id=selected_category_id)

    # Récupérer toutes les poules
    poules = Poule.objects.filter(
        competition=competition,
        category__in=categories_query
    ).select_related('category', 'category__competition_type')

    # Construire le classement par catégorie (même logique que classement_live)
    classements_par_categorie = {}

    for poule in poules:
        category = poule.category
        if not category:
            continue

        category_id = category.id

        if category_id not in classements_par_categorie:
            classements_par_categorie[category_id] = {
                'category': category,
                'competition_type': category.competition_type,
                'classement': {},
                'combats_termines': 0,
                'combats_total': 0,
            }

        combats_poule = Combat.objects.filter(poule=poule)
        classements_par_categorie[category_id]['combats_total'] += combats_poule.count()
        classements_par_categorie[category_id]['combats_termines'] += combats_poule.filter(status='termine').count()

        is_team_mode = poule.equipes.exists()

        # Fallback: détecter équipes depuis les combats si M2M vide
        if not is_team_mode and not poule.pratiquants.exists():
            has_combat_equipes = combats_poule.filter(equipe_rouge__isnull=False).exists()
            if has_combat_equipes:
                is_team_mode = True

        if is_team_mode:
            equipes_pdf = list(poule.equipes.all())
            if not equipes_pdf:
                from apps.competitions.models.combat import Equipe
                equipe_ids = set()
                for c in combats_poule:
                    if c.equipe_rouge_id:
                        equipe_ids.add(c.equipe_rouge_id)
                    if c.equipe_blanc_id:
                        equipe_ids.add(c.equipe_blanc_id)
                equipes_pdf = list(Equipe.objects.filter(id__in=equipe_ids))

            for equipe in equipes_pdf:
                eq_id = f'eq_{equipe.id}'

                if eq_id not in classements_par_categorie[category_id]['classement']:
                    classements_par_categorie[category_id]['classement'][eq_id] = {
                        'nom': equipe.nom,
                        'club_name': equipe.club.name if equipe.club else '-',
                        'equipe': equipe,
                        'is_team': True,
                        'victoires': 0,
                        'points_pour': 0,
                        'points_contre': 0,
                        'combats': 0
                    }

                combats = Combat.objects.filter(
                    Q(poule=poule, status='termine') &
                    (Q(equipe_rouge=equipe) | Q(equipe_blanc=equipe))
                )

                for combat in combats:
                    entry = classements_par_categorie[category_id]['classement'][eq_id]
                    entry['combats'] += 1

                    if combat.equipe_rouge == equipe:
                        entry['points_pour'] += float(combat.score_rouge or 0)
                        entry['points_contre'] += float(combat.score_blanc or 0)
                        if combat.vainqueur == 'rouge':
                            entry['victoires'] += 1
                    else:
                        entry['points_pour'] += float(combat.score_blanc or 0)
                        entry['points_contre'] += float(combat.score_rouge or 0)
                        if combat.vainqueur == 'blanc':
                            entry['victoires'] += 1

        elif poule.pratiquants.exists():
            for pratiquant in poule.pratiquants.all():
                prat_id = pratiquant.id

                if prat_id not in classements_par_categorie[category_id]['classement']:
                    classements_par_categorie[category_id]['classement'][prat_id] = {
                        'nom': pratiquant.full_name,
                        'club_name': pratiquant.club.name if pratiquant.club else '-',
                        'pratiquant': pratiquant,
                        'is_team': False,
                        'victoires': 0,
                        'points_pour': 0,
                        'points_contre': 0,
                        'combats': 0
                    }

                combats = Combat.objects.filter(
                    Q(poule__category=category, poule__competition=competition, status='termine') &
                    (Q(pratiquant_rouge=pratiquant) | Q(pratiquant_blanc=pratiquant))
                )

                for combat in combats:
                    entry = classements_par_categorie[category_id]['classement'][prat_id]
                    entry['combats'] += 1

                    if combat.pratiquant_rouge == pratiquant:
                        entry['points_pour'] += float(combat.score_rouge or 0)
                        entry['points_contre'] += float(combat.score_blanc or 0)
                        if combat.vainqueur == 'rouge':
                            entry['victoires'] += 1
                    else:
                        entry['points_pour'] += float(combat.score_blanc or 0)
                        entry['points_contre'] += float(combat.score_rouge or 0)
                        if combat.vainqueur == 'blanc':
                            entry['victoires'] += 1

    # Convertir et trier
    categories_avec_classement = []
    for cat_id, data in classements_par_categorie.items():
        classement_liste = list(data['classement'].values())
        classement_liste.sort(key=lambda x: (
            -x['victoires'],
            -(x['points_pour'] - x['points_contre']),
            -x['points_pour']
        ))

        seen = set()
        classement_dedupe = []
        for entry in classement_liste:
            entry_id = id(entry)
            if entry_id not in seen:
                seen.add(entry_id)
                classement_dedupe.append(entry)

        categories_avec_classement.append({
            'category': data['category'],
            'competition_type': data['competition_type'],
            'classement': classement_dedupe,
            'combats_termines': data['combats_termines'],
            'combats_total': data['combats_total'],
        })

    categories_avec_classement.sort(key=lambda x: (
        x['competition_type'].name if x['competition_type'] else '',
        x['category'].name
    ))

    # Générer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#c41e3a'),
        alignment=TA_CENTER,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    category_style = ParagraphStyle(
        'CategoryTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=15,
        spaceAfter=8
    )

    type_style = ParagraphStyle(
        'TypeStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=5
    )

    elements = []

    # En-tête du document
    elements.append(Paragraph(f"🏆 {competition.title}", title_style))
    elements.append(Paragraph(
        f"Classement officiel - Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))

    # Statistiques globales
    total_participants = sum(len(c['classement']) for c in categories_avec_classement)
    total_combats = sum(c['combats_total'] for c in categories_avec_classement)
    total_termines = sum(c['combats_termines'] for c in categories_avec_classement)

    stats_data = [[
        f"Catégories: {len(categories_avec_classement)}",
        f"Participants: {total_participants}",
        f"Combats: {total_termines}/{total_combats}"
    ]]
    stats_table = Table(stats_data, colWidths=[6*cm, 6*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#495057')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Classement par catégorie
    for cat_data in categories_avec_classement:
        category = cat_data['category']
        competition_type = cat_data['competition_type']
        classement = cat_data['classement']

        if not classement:
            continue

        # Titre de la catégorie
        elements.append(Paragraph(f"📋 {category.name}", category_style))
        if competition_type:
            elements.append(Paragraph(f"Type: {competition_type.name}", type_style))

        # Tableau de classement
        table_data = [['Pos.', 'Nom', 'Club', 'V', 'C', 'Pts+', 'Pts-', 'Diff']]

        for idx, entry in enumerate(classement, 1):
            diff = entry['points_pour'] - entry['points_contre']
            diff_str = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"

            pos_str = f"🥇 {idx}" if idx == 1 else f"🥈 {idx}" if idx == 2 else f"🥉 {idx}" if idx == 3 else str(idx)

            table_data.append([
                pos_str,
                entry['nom'][:30],
                entry['club_name'][:20],
                str(entry['victoires']),
                str(entry['combats']),
                f"{entry['points_pour']:.2f}",
                f"{entry['points_contre']:.2f}",
                diff_str
            ])

        col_widths = [1.2*cm, 5*cm, 4*cm, 1*cm, 1*cm, 1.5*cm, 1.5*cm, 1.5*cm]
        table = Table(table_data, colWidths=col_widths)

        table_style = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Corps
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Position
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),  # Stats

            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]

        # Couleurs pour le podium
        if len(classement) >= 1:
            table_style.append(('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff8dc')))  # Or
        if len(classement) >= 2:
            table_style.append(('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f5f5f5')))  # Argent
        if len(classement) >= 3:
            table_style.append(('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#faebd7')))  # Bronze

        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 15))

    # Pied de page
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"Document généré par MartialComp - {competition.title}",
        footer_style
    ))

    # Construire le PDF
    doc.build(elements)

    # Retourner la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')

    # Nom du fichier
    filename = f"classement_{competition.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response