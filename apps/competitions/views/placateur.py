"""
Vues pour le rôle Placateur — accès BÉNÉVOLE sans compte.
Accès via lien public + code PIN (même pattern que le kiosque aire de combat).
Interface optimisée tablette.
"""
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

from apps.competitions.models.session_workflow import CategorySession
from apps.competitions.models.placateur import PlacateurAccess, CompetitorCallStatus
from apps.competitions.models.technical_scoring import TechnicalPerformance, Performance


# ── Helpers ──

PLACATEUR_SESSION_KEY = 'placateur_token'


def _get_placateur_from_session(request, token):
    """Vérifie que la session contient bien le token placateur."""
    if request.session.get(PLACATEUR_SESSION_KEY) != str(token):
        return None
    return PlacateurAccess.objects.filter(
        access_token=token, is_active=True
    ).select_related('competition').first()


def _ensure_call_statuses(session):
    """Crée les statuts d'appel pour les performances manquantes.
    Crée les TechnicalPerformance depuis les inscriptions si nécessaire."""
    from apps.competitions.models import CompetitionRegistration

    category = session.category
    competition = session.competition

    # 1. Créer TechnicalPerformance depuis les inscriptions si aucune n'existe
    existing_practitioners = set(
        TechnicalPerformance.objects.filter(category=category)
        .values_list('practitioner_id', flat=True)
    )

    # D'abord depuis Performance (si la scoring sheet les a déjà créées)
    performances = Performance.objects.filter(
        category=category
    ).select_related('practitioner').order_by('order')

    for perf in performances:
        if perf.practitioner_id not in existing_practitioners:
            TechnicalPerformance.objects.get_or_create(
                category=category,
                practitioner=perf.practitioner,
                defaults={
                    'competition': competition,
                    'performance_order': perf.order or 0,
                }
            )
            existing_practitioners.add(perf.practitioner_id)

    # Ensuite depuis les inscriptions (approved + pending)
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        categories__id=category.id,
        status__in=['approved', 'pending']
    ).select_related('practitioner')

    order = len(existing_practitioners)
    for reg in registrations:
        if reg.practitioner_id and reg.practitioner_id not in existing_practitioners:
            order += 1
            TechnicalPerformance.objects.get_or_create(
                category=category,
                practitioner=reg.practitioner,
                defaults={
                    'competition': competition,
                    'performance_order': order,
                }
            )
            existing_practitioners.add(reg.practitioner_id)

    # Maintenant utiliser TechnicalPerformance pour créer les call statuses
    tech_perfs = TechnicalPerformance.objects.filter(
        category=session.category
    ).order_by('performance_order')

    existing_ids = set(
        CompetitorCallStatus.objects.filter(session=session)
        .values_list('performance_id', flat=True)
    )

    to_create = []
    for perf in tech_perfs:
        if perf.pk not in existing_ids:
            to_create.append(CompetitorCallStatus(
                session=session,
                performance=perf,
                call_order=perf.performance_order,
            ))
    if to_create:
        CompetitorCallStatus.objects.bulk_create(to_create, ignore_conflicts=True)


# ── Vues publiques (sans login) ──

def placateur_login(request, token):
    """Page de connexion placateur — demande le code PIN."""
    placateur = get_object_or_404(PlacateurAccess, access_token=token, is_active=True)

    error = None
    if request.method == 'POST':
        pin = request.POST.get('pin', '').strip()
        if pin == placateur.pin_code:
            request.session[PLACATEUR_SESSION_KEY] = str(token)
            return redirect(
                'competitions:technical_scoring:placateur_categories',
                token=token
            )
        else:
            error = _("Code PIN incorrect. Veuillez réessayer.")

    return render(request, 'competitions/placateur/login.html', {
        'placateur': placateur,
        'competition': placateur.competition,
        'error': error,
    })


def placateur_categories(request, token):
    """Liste des catégories accessibles au placateur."""
    placateur = _get_placateur_from_session(request, token)
    if not placateur:
        return redirect(
            'competitions:technical_scoring:placateur_login', token=token
        )

    categories = placateur.get_visible_categories().select_related(
        'competition'
    ).order_by('name')

    # Pour chaque catégorie, trouver la session active
    cat_data = []
    for cat in categories:
        session = CategorySession.objects.filter(
            category=cat
        ).exclude(status='closed').order_by('-round_number').first()

        # Compter les compétiteurs (TP si existent, sinon inscriptions)
        from apps.competitions.models import CompetitionRegistration
        total = TechnicalPerformance.objects.filter(category=cat).count()
        if total == 0:
            total = CompetitionRegistration.objects.filter(
                competition=placateur.competition,
                categories__id=cat.id,
                status__in=['approved', 'pending']
            ).count()
        absent = TechnicalPerformance.objects.filter(category=cat, is_absent=True).count()

        # Compter les aires assignées
        aires = list(cat.aires_combat.filter(is_active=True).values_list('nom', flat=True))

        cat_data.append({
            'category': cat,
            'session': session,
            'total_competitors': total,
            'absent_count': absent,
            'aires': aires,
        })

    return render(request, 'competitions/placateur/categories.html', {
        'placateur': placateur,
        'competition': placateur.competition,
        'cat_data': cat_data,
        'token': token,
    })


def placateur_call_list_page(request, token, category_id):
    """Page d'appel des compétiteurs — interface tablette."""
    placateur = _get_placateur_from_session(request, token)
    if not placateur:
        return redirect(
            'competitions:technical_scoring:placateur_login', token=token
        )

    from apps.competitions.models import CompetitionCategory
    category = get_object_or_404(CompetitionCategory, pk=category_id)

    # Trouver ou créer la session active
    session = CategorySession.objects.filter(
        category=category
    ).exclude(status='closed').order_by('-round_number').first()

    if not session:
        session = CategorySession.objects.create(
            competition=placateur.competition,
            category=category,
            round_number=1,
            status=CategorySession.Status.PENDING
        )

    _ensure_call_statuses(session)

    # Aires assignées à cette catégorie
    aires = category.aires_combat.filter(is_active=True)

    return render(request, 'competitions/placateur/call_list.html', {
        'placateur': placateur,
        'competition': placateur.competition,
        'category': category,
        'session': session,
        'aires': aires,
        'token': token,
    })


def placateur_call_list_api(request, token, category_id):
    """API JSON : liste des compétiteurs avec statuts."""
    placateur = _get_placateur_from_session(request, token)
    if not placateur:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    from apps.competitions.models import CompetitionCategory
    category = get_object_or_404(CompetitionCategory, pk=category_id)

    session = CategorySession.objects.filter(
        category=category
    ).exclude(status='closed').order_by('-round_number').first()

    if not session:
        return JsonResponse({'competitors': [], 'total': 0, 'session_status': 'none'})

    _ensure_call_statuses(session)

    call_statuses = CompetitorCallStatus.objects.filter(
        session=session
    ).select_related(
        'performance__practitioner'
    ).order_by('call_order')

    competitors = []
    for cs in call_statuses:
        pract = cs.performance.practitioner
        club_name = ''
        if hasattr(pract, 'organization') and pract.organization:
            club_name = str(pract.organization)
        elif hasattr(pract, 'club') and pract.club:
            club_name = getattr(pract.club, 'name', str(pract.club))

        competitors.append({
            'id': cs.pk,
            'order': cs.call_order,
            'name': pract.full_name,
            'club': club_name,
            'status': cs.status,
            'status_display': cs.get_status_display(),
            'called_at': cs.called_at.isoformat() if cs.called_at else None,
        })

    return JsonResponse({
        'session_status': session.status,
        'session_status_display': session.get_status_display(),
        'is_active': session.status in ('started', 'pending'),
        'category': str(category),
        'competitors': competitors,
        'total': len(competitors),
        'waiting': sum(1 for c in competitors if c['status'] == 'waiting'),
        'called': sum(1 for c in competitors if c['status'] == 'called'),
        'present': sum(1 for c in competitors if c['status'] == 'present'),
        'absent': sum(1 for c in competitors if c['status'] == 'absent'),
        'passed': sum(1 for c in competitors if c['status'] == 'passed'),
    })


@csrf_exempt
def placateur_call_action(request, token, call_status_id):
    """POST : Action du placateur sur un compétiteur."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    placateur = _get_placateur_from_session(request, token)
    if not placateur:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    cs = get_object_or_404(CompetitorCallStatus, pk=call_status_id)

    action = request.POST.get('action')
    if action == 'call':
        cs.mark_called()
    elif action == 'present':
        cs.mark_present()
    elif action == 'absent':
        cs.mark_absent()
    elif action == 'passed':
        cs.mark_passed()
    else:
        return JsonResponse({'error': _("Action inconnue")}, status=400)

    return JsonResponse({
        'success': True,
        'status': cs.status,
        'status_display': cs.get_status_display(),
    })


def placateur_logout(request, token):
    """Déconnexion du placateur."""
    if PLACATEUR_SESSION_KEY in request.session:
        del request.session[PLACATEUR_SESSION_KEY]
    return redirect(
        'competitions:technical_scoring:placateur_login', token=token
    )
