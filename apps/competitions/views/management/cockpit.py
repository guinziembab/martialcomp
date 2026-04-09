"""
Cockpit — Tableau de pilotage temps réel pour le manager de compétition.
Vue Kanban : Backlog → Aires → Terminées + Juges/Placateurs en bas.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from apps.competitions.models import Competition, CompetitionCategory, JudgeAssignment
from apps.competitions.models.combat import AireCombat, Combat
from apps.competitions.models.session_workflow import CategorySession
from apps.competitions.models.placateur import PlacateurAccess
from apps.competitions.models.schedule import CompetitionSchedule, TatamiSchedule


def _sync_aires_tatamis(competition):
    """Synchronise les AireCombat avec les TatamiSchedule."""
    try:
        schedule, _ = CompetitionSchedule.objects.get_or_create(
            competition=competition,
            defaults={'tatami_count': 1}
        )
        aires = AireCombat.objects.filter(competition=competition, is_active=True).order_by('numero')

        # Mettre à jour le nombre de tatamis
        schedule.tatami_count = max(aires.count(), 1)
        schedule.save(update_fields=['tatami_count'])

        # Pour chaque aire, s'assurer qu'un TatamiSchedule existe
        for aire in aires:
            tatami, created = TatamiSchedule.objects.get_or_create(
                competition_schedule=schedule,
                tatami_number=aire.numero,
                defaults={'name': aire.nom, 'aire_combat': aire}
            )
            if not created and tatami.aire_combat != aire:
                tatami.aire_combat = aire
                tatami.name = aire.nom
                tatami.save(update_fields=['aire_combat', 'name'])

        # Supprimer les tatamis orphelins (sans aire correspondante)
        aire_numeros = set(aires.values_list('numero', flat=True))
        TatamiSchedule.objects.filter(
            competition_schedule=schedule
        ).exclude(tatami_number__in=aire_numeros).delete()

    except Exception:
        pass  # Ne pas bloquer si la synchro échoue


@login_required
def competition_cockpit(request, competition_id):
    """Tableau de pilotage principal."""
    competition = get_object_or_404(Competition, pk=competition_id)

    # Synchroniser aires ↔ tatamis à chaque chargement
    _sync_aires_tatamis(competition)

    aires = AireCombat.objects.filter(
        competition=competition, is_active=True
    ).prefetch_related('categories').order_by('numero')

    all_categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')

    # IDs des catégories assignées à une aire
    assigned_cat_ids = set()
    for aire in aires:
        assigned_cat_ids.update(aire.categories.values_list('id', flat=True))

    # IDs des catégories clôturées (session closed)
    closed_session_cat_ids = set(
        CategorySession.objects.filter(
            competition=competition, status='closed'
        ).values_list('category_id', flat=True)
    )

    # Backlog = non assignées ET non clôturées
    from apps.competitions.models import CompetitionRegistration
    from django.db.models import Count
    backlog_cats = all_categories.exclude(id__in=assigned_cat_ids).exclude(
        id__in=closed_session_cat_ids
    ).select_related('competition_type').annotate(
        registrations_count=Count('registrations')
    )

    # Types de compétition pour les filtres
    from apps.competitions.models.competitions import CompetitionType
    comp_types = CompetitionType.objects.filter(
        categories__competition=competition
    ).distinct().order_by('name')

    # Terminées = clôturées
    done_cats = all_categories.filter(id__in=closed_session_cat_ids)

    # Données par aire
    aires_data = []
    for aire in aires:
        aire_cats = aire.categories.all()
        cats_info = []
        for cat in aire_cats:
            session = CategorySession.objects.filter(
                category=cat
            ).exclude(status='closed').order_by('-round_number').first()

            combats_total = Combat.objects.filter(poule__category=cat, competition=competition).count()
            combats_done = Combat.objects.filter(poule__category=cat, competition=competition, status='termine').count()
            combats_live = Combat.objects.filter(poule__category=cat, competition=competition, status='en_cours').count()

            cat_judges = list(
                JudgeAssignment.objects.filter(category=cat, user__isnull=False)
                .select_related('user')
            )

            cats_info.append({
                'category': cat,
                'session': session,
                'combats_total': combats_total,
                'combats_done': combats_done,
                'combats_live': combats_live,
                'progress': int((combats_done / combats_total * 100)) if combats_total > 0 else 0,
                'judges': cat_judges,
                'is_closed': cat.id in closed_session_cat_ids,
            })

        # Placateurs assignés à cette aire (ceux qui ont les mêmes catégories)
        aire_cat_ids = set(aire.categories.values_list('id', flat=True))
        aire_placateurs = []
        for p in PlacateurAccess.objects.filter(competition=competition, is_active=True):
            p_cat_ids = set(p.categories.values_list('id', flat=True))
            if p_cat_ids and p_cat_ids.issubset(aire_cat_ids):
                aire_placateurs.append(p)

        aires_data.append({
            'aire': aire,
            'cats_info': cats_info,
            'placateurs': aire_placateurs,
        })

    # Juges disponibles
    from apps.competitions.models.judges import Judge
    all_judges = Judge.objects.filter(
        active=True, user__isnull=False
    ).select_related('user', 'practitioner')

    # Placateurs
    placateurs = PlacateurAccess.objects.filter(
        competition=competition, is_active=True
    )

    # Stats
    total_combats = Combat.objects.filter(competition=competition).count()
    done_combats = Combat.objects.filter(competition=competition, status='termine').count()
    live_combats = Combat.objects.filter(competition=competition, status='en_cours').count()
    total_cats = all_categories.count()
    done_cats_count = done_cats.count()

    return render(request, 'competitions/management/cockpit.html', {
        'competition': competition,
        'aires_data': aires_data,
        'backlog_cats': backlog_cats,
        'done_cats': done_cats,
        'all_judges': all_judges,
        'placateurs': placateurs,
        'total_combats': total_combats,
        'done_combats': done_combats,
        'live_combats': live_combats,
        'total_cats': total_cats,
        'done_cats_count': done_cats_count,
        'global_progress': int((done_combats / total_combats * 100)) if total_combats > 0 else 0,
        'cats_progress': int((done_cats_count / total_cats * 100)) if total_cats > 0 else 0,
        'comp_types': comp_types,
    })


@login_required
def cockpit_api(request, competition_id):
    """API JSON pour polling temps réel."""
    competition = get_object_or_404(Competition, pk=competition_id)
    total = Combat.objects.filter(competition=competition).count()
    done = Combat.objects.filter(competition=competition, status='termine').count()
    live = Combat.objects.filter(competition=competition, status='en_cours').count()
    total_cats = CompetitionCategory.objects.filter(competition=competition).count()
    done_cats = CategorySession.objects.filter(competition=competition, status='closed').count()

    return JsonResponse({
        'total': total, 'done': done, 'live': live,
        'progress': int((done / total * 100)) if total > 0 else 0,
        'total_cats': total_cats, 'done_cats': done_cats,
        'cats_progress': int((done_cats / total_cats * 100)) if total_cats > 0 else 0,
        'ts': timezone.now().isoformat(),
    })


@login_required
@require_POST
def cockpit_assign_judge(request, competition_id):
    """Assigner un juge à une catégorie."""
    competition = get_object_or_404(Competition, pk=competition_id)
    judge_user_id = request.POST.get('judge_user_id')
    category_id = request.POST.get('category_id')
    assignment_type = request.POST.get('assignment_type', 'technical_judge')

    if not judge_user_id or not category_id:
        return JsonResponse({'error': 'Params manquants'}, status=400)
    try:
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        from django.contrib.auth import get_user_model
        from apps.competitions.models import CompetitionRegistration, Practitioner
        judge_user = get_user_model().objects.get(pk=judge_user_id)

        # Trouver le practitioner
        practitioner = Practitioner.objects.filter(user=judge_user).first()
        if not practitioner:
            return JsonResponse({'error': f'Pas de profil pratiquant pour {judge_user.get_full_name()}'}, status=400)

        # Trouver ou créer l'inscription (get_or_create pour éviter race condition)
        registration, created = CompetitionRegistration.objects.get_or_create(
            competition=competition,
            practitioner=practitioner,
            defaults={
                'status': 'approved',
                'is_competitor': False,
                'is_technical_judge': assignment_type in ('technical_judge', 'chief_judge'),
                'is_combat_referee': assignment_type == 'referee',
            }
        )

        # Sync flags si l'inscription existait déjà
        if not created:
            updated = False
            if assignment_type in ('technical_judge', 'chief_judge') and not registration.is_technical_judge:
                registration.is_technical_judge = True
                updated = True
            if assignment_type == 'referee' and not getattr(registration, 'is_combat_referee', False):
                registration.is_combat_referee = True
                updated = True
            if updated:
                registration.save()

        # Vérifier si déjà assigné (quel que soit le type)
        existing = JudgeAssignment.objects.filter(
            user=judge_user, category=category
        ).first()
        if not existing:
            existing = JudgeAssignment.objects.filter(
                registration=registration, category=category
            ).first()
        if existing:
            if existing.assignment_type != assignment_type:
                existing.assignment_type = assignment_type
                existing.save(update_fields=['assignment_type'])
            return JsonResponse({'success': True, 'message': 'Assigné'})

        JudgeAssignment.objects.create(
            registration=registration,
            user=judge_user,
            category=category,
            assignment_type=assignment_type,
            status='confirmed',
            assigned_by=request.user
        )

        # Si c'est un chief_judge, l'assigner comme head_judge de la session
        if assignment_type == 'chief_judge':
            session = CategorySession.objects.filter(
                category=category
            ).exclude(status='closed').first()
            if session:
                session.head_judge = judge_user
                session.save(update_fields=['head_judge'])

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def cockpit_assign_category(request, competition_id):
    """Assigner une catégorie à une aire (drag & drop)."""
    competition = get_object_or_404(Competition, pk=competition_id)
    category_id = request.POST.get('category_id')
    aire_id = request.POST.get('aire_id')

    if not category_id or not aire_id:
        return JsonResponse({'error': 'Params manquants'}, status=400)
    try:
        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.add(category)
        # Créer une session si elle n'existe pas
        CategorySession.objects.get_or_create(
            competition=competition, category=category, round_number=1,
            defaults={'status': 'pending'}
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def cockpit_unassign_category(request, competition_id):
    """Retirer une catégorie d'une aire (remettre dans le backlog)."""
    competition = get_object_or_404(Competition, pk=competition_id)
    category_id = request.POST.get('category_id')
    aire_id = request.POST.get('aire_id')
    if not category_id or not aire_id:
        return JsonResponse({'error': 'Params manquants'}, status=400)
    try:
        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.remove(category)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def cockpit_create_placateur(request, competition_id):
    """Créer un nouveau placateur."""
    competition = get_object_or_404(Competition, pk=competition_id)
    nom = request.POST.get('nom', '').strip()
    if not nom:
        # Auto-nommer
        count = PlacateurAccess.objects.filter(competition=competition).count()
        nom = f"Placateur {count + 1}"
    pa = PlacateurAccess.objects.create(competition=competition, nom=nom)
    return JsonResponse({
        'success': True,
        'id': pa.id,
        'nom': pa.nom,
        'pin': pa.pin_code,
        'url': pa.get_absolute_url(),
    })


@login_required
@require_POST
def cockpit_assign_placateur(request, competition_id):
    """Assigner un placateur à une aire."""
    competition = get_object_or_404(Competition, pk=competition_id)
    placateur_id = request.POST.get('placateur_id')
    aire_id = request.POST.get('aire_id')
    if not placateur_id or not aire_id:
        return JsonResponse({'error': 'Params manquants'}, status=400)
    try:
        placateur = PlacateurAccess.objects.get(pk=placateur_id, competition=competition)
        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        # Assigner les catégories de l'aire au placateur
        aire_cats = aire.categories.all()
        if aire_cats.exists():
            placateur.categories.set(aire_cats)
        placateur.save()
        return JsonResponse({
            'success': True,
            'pin': placateur.pin_code,
            'url': request.build_absolute_uri(placateur.get_absolute_url()),
            'message': f"{placateur.nom} assigné à {aire.nom}. PIN: {placateur.pin_code}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def cockpit_delete_aire(request, competition_id):
    """Supprimer une aire vide."""
    competition = get_object_or_404(Competition, pk=competition_id)
    aire_id = request.POST.get('aire_id')
    if not aire_id:
        return JsonResponse({'error': 'Param manquant'}, status=400)
    try:
        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        if aire.categories.exists():
            return JsonResponse({'error': 'Impossible de supprimer une aire avec des catégories assignées'}, status=400)
        aire.delete()
        _sync_aires_tatamis(competition)
        return JsonResponse({'success': True})
    except AireCombat.DoesNotExist:
        return JsonResponse({'error': 'Aire non trouvée'}, status=404)


@login_required
@require_POST
def cockpit_create_aire(request, competition_id):
    """Créer une nouvelle aire depuis le cockpit."""
    competition = get_object_or_404(Competition, pk=competition_id)
    nom = request.POST.get('nom', '').strip()
    couleur = request.POST.get('couleur', 'blue')
    couleur_int = request.POST.get('couleur_interieur', 'red')

    last = AireCombat.objects.filter(competition=competition).order_by('-numero').first()
    numero = (last.numero + 1) if last else 1

    if not nom:
        nom = f"Aire {numero}"

    aire = AireCombat.objects.create(
        competition=competition, nom=nom, numero=numero,
        couleur=couleur, couleur_interieur=couleur_int
    )
    _sync_aires_tatamis(competition)
    return JsonResponse({
        'success': True, 'id': aire.id, 'nom': aire.nom,
        'numero': aire.numero, 'pin': aire.pin_code
    })


@login_required
@require_POST
def cockpit_judge_action(request, competition_id):
    """Retirer un juge ou le promouvoir en juge central."""
    competition = get_object_or_404(Competition, pk=competition_id)
    action = request.POST.get('action')  # 'remove' or 'promote_chief'
    assignment_id = request.POST.get('assignment_id')

    if not assignment_id or not action:
        return JsonResponse({'error': 'Params manquants'}, status=400)
    try:
        assignment = JudgeAssignment.objects.get(pk=assignment_id, category__competition=competition)
        if action == 'remove':
            # Aussi supprimer le JudgeCompetitionAssignment correspondant
            from apps.competitions.models.registrations import JudgeCompetitionAssignment
            JudgeCompetitionAssignment.objects.filter(
                registration=assignment.registration,
                category=assignment.category
            ).delete()
            # Si le juge n'a plus d'assignation dans cette compétition, retirer le flag
            if assignment.registration:
                remaining = JudgeAssignment.objects.filter(
                    registration=assignment.registration,
                    category__competition=competition
                ).exclude(pk=assignment.pk).count()
                if remaining == 0:
                    assignment.registration.is_technical_judge = False
                    assignment.registration.save(update_fields=['is_technical_judge'])
            assignment.delete()
            return JsonResponse({'success': True})
        elif action == 'promote_chief':
            assignment.assignment_type = 'chief_judge'
            assignment.save(update_fields=['assignment_type'])
            # Mettre à jour la session
            session = CategorySession.objects.filter(
                category=assignment.category
            ).exclude(status='closed').first()
            if session and assignment.user:
                session.head_judge = assignment.user
                session.save(update_fields=['head_judge'])
            return JsonResponse({'success': True})
        elif action == 'demote':
            assignment.assignment_type = 'technical_judge'
            assignment.save(update_fields=['assignment_type'])
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Action inconnue'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def cockpit_category_registrations(request, competition_id, category_id):
    """API: liste des inscrits d'une catégorie."""
    from apps.competitions.models import CompetitionRegistration
    registrations = CompetitionRegistration.objects.filter(
        competition_id=competition_id,
        categories__id=category_id
    ).select_related('practitioner', 'practitioner__organization')

    data = []
    for r in registrations:
        p = r.practitioner
        if p:
            data.append({
                'name': p.full_name,
                'club': str(p.organization) if p.organization else '',
                'photo': p.photo.url if p.photo else '',
                'status': r.status,
                'grade': str(p.grade) if p.grade else '',
            })
    return JsonResponse({'registrations': data, 'total': len(data)})


@login_required
@require_POST
def cockpit_close_session(request, competition_id, session_id):
    """Clôturer une session."""
    session = get_object_or_404(CategorySession, pk=session_id, competition_id=competition_id)
    session.status = 'closed'
    session.closed_at = timezone.now()
    session.save(update_fields=['status', 'closed_at'])
    return JsonResponse({'success': True})
