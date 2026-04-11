"""
Vues pour la gestion des Aires de Combat (Mode Kiosque Multi-Tatami).

Ce module fournit:
- CRUD pour les aires de combat (gestionnaire)
- Interface kiosque publique protégée par PIN
- API pour les opérations en temps réel
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from django.db.models import Q, Count

import json
import logging

from apps.competitions.models import Competition, CompetitionCategory
from apps.competitions.models.combat import (
    AireCombat,
    AireCombatSession,
    Combat,
)
from apps.competitions.utils.permission_helpers import manual_permission_check

logger = logging.getLogger(__name__)


# =============================================================================
# VUES MANAGER: Gestion des Aires de Combat
# =============================================================================

@login_required
def liste_aires(request, competition_id):
    """
    Liste des aires de combat pour une compétition.
    Accessible uniquement aux gestionnaires.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.view_airecombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    aires = AireCombat.objects.filter(
        competition=competition
    ).prefetch_related('categories').order_by('numero')

    # Calculer les stats pour chaque aire
    aires_with_stats = []
    for aire in aires:
        stats = aire.stats
        aires_with_stats.append({
            'aire': aire,
            'stats': stats,
        })

    return render(request, 'competitions/combat/aires/liste_aires.html', {
        'competition': competition,
        'aires_with_stats': aires_with_stats,
        'total_aires': aires.count(),
    })


@login_required
def creer_aire(request, competition_id):
    """
    Créer une nouvelle aire de combat.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.add_airecombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    # Récupérer les catégories de la compétition
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        numero = request.POST.get('numero', '1')
        couleur = request.POST.get('couleur', 'blue')
        couleur_interieur = request.POST.get('couleur_interieur', 'red')
        description = request.POST.get('description', '')
        category_ids = request.POST.getlist('categories')

        if not nom:
            messages.error(request, _("Le nom de l'aire est obligatoire."))
        else:
            try:
                numero = int(numero)
            except ValueError:
                numero = 1

            # Vérifier l'unicité du numéro
            if AireCombat.objects.filter(competition=competition, numero=numero).exists():
                messages.error(request, _("Une aire avec ce numéro existe déjà."))
            else:
                aire = AireCombat.objects.create(
                    competition=competition,
                    nom=nom,
                    numero=numero,
                    couleur=couleur,
                    couleur_interieur=couleur_interieur,
                    description=description,
                )

                # Assigner les catégories
                if category_ids:
                    aire.categories.set(category_ids)

                messages.success(request, _("L'aire de combat a été créée avec succès."))
                messages.info(
                    request,
                    _("Code PIN: %(pin)s - Partagez ce code avec les arbitres de cette aire.") % {'pin': aire.pin_code}
                )
                return redirect('competitions:combat:liste_aires', competition_id=competition_id)

    # Prochain numéro disponible
    last_aire = AireCombat.objects.filter(competition=competition).order_by('-numero').first()
    next_numero = (last_aire.numero + 1) if last_aire else 1

    return render(request, 'competitions/combat/aires/form_aire.html', {
        'competition': competition,
        'categories': categories,
        'next_numero': next_numero,
        'couleurs': AireCombat.COLOR_CHOICES,
        'title': _("Créer une aire de combat"),
        'is_edit': False,
    })


@login_required
def modifier_aire(request, aire_id):
    """
    Modifier une aire de combat existante.
    """
    aire = get_object_or_404(AireCombat, id=aire_id)
    competition = aire.competition

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.change_airecombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        numero = request.POST.get('numero', '1')
        couleur = request.POST.get('couleur', 'blue')
        couleur_interieur = request.POST.get('couleur_interieur', 'red')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        category_ids = request.POST.getlist('categories')

        if not nom:
            messages.error(request, _("Le nom de l'aire est obligatoire."))
        else:
            try:
                numero = int(numero)
            except ValueError:
                numero = aire.numero

            # Vérifier l'unicité du numéro (sauf pour cette aire)
            if AireCombat.objects.filter(
                competition=competition, numero=numero
            ).exclude(id=aire.id).exists():
                messages.error(request, _("Une autre aire avec ce numéro existe déjà."))
            else:
                aire.nom = nom
                aire.numero = numero
                aire.couleur = couleur
                aire.couleur_interieur = couleur_interieur
                aire.description = description
                aire.is_active = is_active
                aire.save()

                # Mettre à jour les catégories
                aire.categories.set(category_ids)

                messages.success(request, _("L'aire de combat a été modifiée avec succès."))
                return redirect('competitions:combat:liste_aires', competition_id=competition.id)

    return render(request, 'competitions/combat/aires/form_aire.html', {
        'competition': competition,
        'aire': aire,
        'categories': categories,
        'couleurs': AireCombat.COLOR_CHOICES,
        'title': _("Modifier l'aire de combat"),
        'is_edit': True,
    })


@login_required
def supprimer_aire(request, aire_id):
    """
    Supprimer une aire de combat.
    """
    aire = get_object_or_404(AireCombat, id=aire_id)
    competition_id = aire.competition.id

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.delete_airecombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    if request.method == 'POST':
        nom = aire.nom
        aire.delete()
        messages.success(request, _("L'aire '%(nom)s' a été supprimée.") % {'nom': nom})
        return redirect('competitions:combat:liste_aires', competition_id=competition_id)

    return render(request, 'competitions/combat/aires/confirmer_suppression.html', {
        'aire': aire,
        'competition': aire.competition,
    })


@login_required
def regenerer_pin_aire(request, aire_id):
    """
    Régénère le PIN d'une aire de combat.
    """
    aire = get_object_or_404(AireCombat, id=aire_id)

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.change_airecombat'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        aire.regenerate_access()
        return JsonResponse({
            'success': True,
            'new_pin': aire.pin_code,
            'message': _("Nouveau PIN généré avec succès.")
        })

    return JsonResponse({'success': False, 'error': 'POST required'}, status=400)


@login_required
def detail_aire(request, aire_id):
    """
    Détail d'une aire de combat avec ses combats assignés.
    """
    aire = get_object_or_404(AireCombat, id=aire_id)

    # Vérifier les permissions
    if not manual_permission_check(request.user, 'competitions.view_airecombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    # Sessions actives
    sessions_actives = aire.sessions.filter(is_active=True).order_by('-started_at')[:5]

    # Combats par statut
    combats_planifies = aire.get_pending_combats()[:10]
    combats_en_cours = aire.get_active_combats()
    combats_termines = aire.get_completed_combats()[:10]

    return render(request, 'competitions/combat/aires/detail_aire.html', {
        'aire': aire,
        'competition': aire.competition,
        'sessions_actives': sessions_actives,
        'combats_planifies': combats_planifies,
        'combats_en_cours': combats_en_cours,
        'combats_termines': combats_termines,
        'stats': aire.stats,
    })


# =============================================================================
# VUES KIOSQUE: Interface publique protégée par PIN
# =============================================================================

def aire_kiosque_login(request, token):
    """
    Page de connexion kiosque pour une aire de combat.
    Demande le code PIN pour accéder à l'interface.
    """
    try:
        from uuid import UUID
        token_uuid = UUID(str(token))
        aire = get_object_or_404(AireCombat, access_token=token_uuid)
    except (ValueError, TypeError):
        messages.error(request, _("Lien d'accès invalide."))
        return render(request, 'competitions/combat/kiosque/erreur.html', {
            'message': _("Ce lien d'accès n'est pas valide.")
        })

    if not aire.is_active:
        return render(request, 'competitions/combat/kiosque/erreur.html', {
            'message': _("Cette aire de combat n'est plus active.")
        })

    # Vérifier si déjà authentifié via session
    session_token = request.session.get(f'aire_session_{aire.id}')
    if session_token:
        session = AireCombatSession.objects.filter(
            session_token=session_token,
            aire=aire,
            is_active=True
        ).first()
        if session:
            session.update_activity()
            return redirect('competitions:combat:aire_kiosque_interface', token=token)

    if request.method == 'POST':
        pin_entered = request.POST.get('pin', '')

        if aire.verify_pin(pin_entered):
            # Créer une session
            session = AireCombatSession.objects.create(
                aire=aire,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )

            # Stocker le token de session
            request.session[f'aire_session_{aire.id}'] = str(session.session_token)

            # Enregistrer l'accès
            aire.record_access()

            return redirect('competitions:combat:aire_kiosque_interface', token=token)
        else:
            messages.error(request, _("Code PIN incorrect."))

    return render(request, 'competitions/combat/kiosque/login.html', {
        'aire': aire,
        'competition': aire.competition,
    })


def aire_kiosque_interface(request, token):
    """
    Interface kiosque principale pour une aire de combat.
    Affiche les catégories assignées et les combats.
    """
    try:
        from uuid import UUID
        token_uuid = UUID(str(token))
        aire = get_object_or_404(AireCombat, access_token=token_uuid)
    except (ValueError, TypeError):
        return render(request, 'competitions/combat/kiosque/erreur.html', {
            'message': _("Lien d'accès invalide.")
        })

    if not aire.is_active:
        return render(request, 'competitions/combat/kiosque/erreur.html', {
            'message': _("Cette aire de combat n'est plus active.")
        })

    # Vérifier la session
    session_token = request.session.get(f'aire_session_{aire.id}')
    if not session_token:
        return redirect('competitions:combat:aire_kiosque_login', token=token)

    session = AireCombatSession.objects.filter(
        session_token=session_token,
        aire=aire,
        is_active=True
    ).first()

    if not session:
        # Session expirée, rediriger vers login
        if f'aire_session_{aire.id}' in request.session:
            del request.session[f'aire_session_{aire.id}']
        return redirect('competitions:combat:aire_kiosque_login', token=token)

    # Mettre à jour l'activité
    session.update_activity()

    # Récupérer les catégories et combats
    categories = aire.categories.all().order_by('name')
    combats_en_cours = aire.get_active_combats()
    # Récupérer tous les combats planifiés sans slice pour pouvoir filtrer
    all_combats_planifies = aire.get_pending_combats()

    # Regrouper les combats par catégorie
    combats_par_categorie = {}
    for cat in categories:
        cat_combats = all_combats_planifies.filter(
            Q(poule__category=cat) |
            Q(equipe_rouge__category=cat) |
            Q(equipe_blanc__category=cat)
        ).distinct()[:20]  # Limiter à 20 par catégorie
        combats_par_categorie[cat.id] = {
            'category': cat,
            'combats': list(cat_combats),
            'count': cat_combats.count() if hasattr(cat_combats, 'count') else len(cat_combats)
        }

    # Afficher tous les combats planifiés (pas de limite)
    combats_planifies = all_combats_planifies

    return render(request, 'competitions/combat/kiosque/interface.html', {
        'aire': aire,
        'competition': aire.competition,
        'categories': categories,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
        'combats_par_categorie': combats_par_categorie,
        'stats': aire.stats,
    })


def aire_kiosque_logout(request, token):
    """
    Déconnexion de l'interface kiosque.
    """
    try:
        from uuid import UUID
        token_uuid = UUID(str(token))
        aire = get_object_or_404(AireCombat, access_token=token_uuid)
    except (ValueError, TypeError):
        return redirect('competitions:dashboard:index')

    # Terminer la session
    session_token = request.session.get(f'aire_session_{aire.id}')
    if session_token:
        session = AireCombatSession.objects.filter(
            session_token=session_token,
            aire=aire
        ).first()
        if session:
            session.end_session()

        del request.session[f'aire_session_{aire.id}']

    messages.success(request, _("Vous avez été déconnecté de l'aire de combat."))
    return redirect('competitions:combat:aire_kiosque_login', token=token)


def aire_kiosque_combat(request, token, combat_id):
    """
    Interface de combat pour le mode kiosque.
    Redirige vers l'interface de combat v2 existante.
    Si l'utilisateur n'est pas connecté, il sera redirigé vers la page de login
    puis reviendra automatiquement à l'interface de combat.
    """
    try:
        from uuid import UUID
        token_uuid = UUID(str(token))
        aire = get_object_or_404(AireCombat, access_token=token_uuid)
    except (ValueError, TypeError):
        return render(request, 'competitions/combat/kiosque/erreur.html', {
            'message': _("Lien d'accès invalide.")
        })

    # Vérifier la session kiosque (PIN)
    session_token = request.session.get(f'aire_session_{aire.id}')
    if not session_token:
        return redirect('competitions:combat:aire_kiosque_login', token=token)

    session = AireCombatSession.objects.filter(
        session_token=session_token,
        aire=aire,
        is_active=True
    ).first()

    if not session:
        # Session expirée, rediriger vers login kiosque
        if f'aire_session_{aire.id}' in request.session:
            del request.session[f'aire_session_{aire.id}']
        return redirect('competitions:combat:aire_kiosque_login', token=token)

    # Mettre à jour l'activité de la session
    session.update_activity()

    combat = get_object_or_404(Combat, id=combat_id)

    # Vérifier que le combat appartient à cette aire
    # (via les catégories assignées ou la poule)
    category_ids = list(aire.categories.values_list('id', flat=True))

    combat_in_aire = False

    # Vérifier via les équipes (combats par équipe)
    if combat.equipe_rouge and combat.equipe_rouge.category_id in category_ids:
        combat_in_aire = True
    elif combat.equipe_blanc and combat.equipe_blanc.category_id in category_ids:
        combat_in_aire = True
    # Vérifier via la poule (combats individuels ou par équipe)
    elif combat.poule and combat.poule.category_id in category_ids:
        combat_in_aire = True
    # Vérifier via la catégorie directe du combat si elle existe
    elif hasattr(combat, 'category') and combat.category and combat.category_id in category_ids:
        combat_in_aire = True

    if not combat_in_aire:
        messages.error(request, _("Ce combat n'est pas assigné à cette aire."))
        return redirect('competitions:combat:aire_kiosque_interface', token=token)

    # Rediriger vers l'interface de combat v2 (requiert authentification juge)
    # Si l'utilisateur n'est pas connecté, Django le redirigera vers login
    # puis reviendra automatiquement à l'interface de combat
    return redirect('competitions:combat:interface_combat_v2', combat_id=combat_id)


# =============================================================================
# API KIOSQUE
# =============================================================================

@csrf_exempt
def api_kiosque_combats(request, token):
    """
    API: Retourne les combats pour une aire de combat.
    """
    try:
        from uuid import UUID
        token_uuid = UUID(str(token))
        aire = get_object_or_404(AireCombat, access_token=token_uuid)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid token'}, status=400)

    # Vérifier la session (optionnel pour l'API)
    session_token = request.session.get(f'aire_session_{aire.id}')
    if not session_token:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    combats_data = []
    for combat in aire.get_assigned_combats():
        combats_data.append({
            'id': combat.id,
            'status': combat.status,
            'status_display': combat.get_status_display(),
            'type': combat.type_combat,
            'rouge': {
                'nom': combat.equipe_rouge.nom if combat.equipe_rouge else (
                    combat.pratiquant_rouge.full_name if combat.pratiquant_rouge else "TBD"
                ),
                'score': float(combat.score_rouge)
            },
            'blanc': {
                'nom': combat.equipe_blanc.nom if combat.equipe_blanc else (
                    combat.pratiquant_blanc.full_name if combat.pratiquant_blanc else "TBD"
                ),
                'score': float(combat.score_blanc)
            },
            'date_planifiee': combat.date_planifiee.isoformat() if combat.date_planifiee else None,
        })

    return JsonResponse({
        'success': True,
        'aire': {
            'id': aire.id,
            'nom': aire.nom,
            'couleur': aire.couleur,
        },
        'combats': combats_data,
        'stats': aire.stats,
    })


# =============================================================================
# HELPERS
# =============================================================================

def get_client_ip(request):
    """Récupère l'adresse IP du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
