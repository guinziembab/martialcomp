"""
Vues pour le workflow de session de notation technique.
Start / Stop / Validate / Close / Progress.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_GET

from apps.competitions.models.session_workflow import CategorySession


@login_required
@require_POST
def session_start(request, session_id):
    """Le juge principal démarre la session."""
    session = get_object_or_404(CategorySession, pk=session_id)
    try:
        session.start(request.user)
        return JsonResponse({
            'success': True,
            'message': _("Session démarrée. Les juges peuvent maintenant noter."),
            'status': session.status,
            'started_at': session.started_at.isoformat()
        })
    except (ValueError, PermissionError) as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=403)


@login_required
@require_POST
def session_stop(request, session_id):
    """Le juge principal arrête la notation."""
    session = get_object_or_404(CategorySession, pk=session_id)
    try:
        session.stop(request.user)
        return JsonResponse({
            'success': True,
            'message': _("Notation arrêtée. En attente de vérification par l'admin central."),
            'status': session.status,
            'progress': session.scoring_progress
        })
    except (ValueError, PermissionError) as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=403)


@login_required
@require_POST
def session_validate(request, session_id):
    """L'admin central valide les résultats."""
    session = get_object_or_404(CategorySession, pk=session_id)
    result = request.POST.get('result', 'ok')
    notes = request.POST.get('notes', '')

    try:
        session.validate(request.user, result, notes)
        if result != 'ok':
            next_round = session.create_next_round()
            return JsonResponse({
                'success': True,
                'message': _("Égalité détectée. Un 2e tour a été créé."),
                'status': session.status,
                'next_round_id': next_round.pk
            })
        return JsonResponse({
            'success': True,
            'message': _("Résultats validés. Le juge principal peut clôturer."),
            'status': session.status
        })
    except (ValueError, PermissionError) as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=403)


@login_required
@require_POST
def session_close(request, session_id):
    """Le juge principal clôture définitivement."""
    session = get_object_or_404(CategorySession, pk=session_id)
    try:
        session.close(request.user)
        return JsonResponse({
            'success': True,
            'message': _("Session clôturée. Les résultats sont publiés."),
            'status': session.status
        })
    except (ValueError, PermissionError) as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=403)


@login_required
@require_GET
def session_progress(request, session_id):
    """Polling pour l'avancement de la notation."""
    session = get_object_or_404(CategorySession, pk=session_id)
    return JsonResponse({
        'session_id': session.pk,
        'category': str(session.category),
        'status': session.status,
        'status_display': session.get_status_display(),
        'progress': session.scoring_progress,
        'round': session.round_number,
        'has_ties': session.has_ties if session.status in ('stopped', 'validating') else None,
        'is_scoring_allowed': session.is_scoring_allowed,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'stopped_at': session.stopped_at.isoformat() if session.stopped_at else None,
        'validated_at': session.validated_at.isoformat() if session.validated_at else None,
        'validation_result': session.validation_result or None,
    })


@login_required
def head_judge_panel(request, session_id):
    """Interface du juge principal — panneau de contrôle."""
    session = get_object_or_404(
        CategorySession.objects.select_related('competition', 'category', 'head_judge'),
        pk=session_id
    )
    return render(request, 'competitions/technical_scoring/head_judge_panel.html', {
        'session': session,
        'competition': session.competition,
        'category': session.category,
    })


@login_required
def admin_sessions_dashboard(request, competition_id):
    """Dashboard admin central — vue de toutes les sessions."""
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, pk=competition_id)
    sessions = CategorySession.objects.filter(
        competition=competition
    ).select_related('category', 'head_judge').order_by('category__name', 'round_number')

    return render(request, 'competitions/technical_scoring/admin_sessions_dashboard.html', {
        'competition': competition,
        'sessions': sessions,
        'active_sessions': sessions.exclude(status=CategorySession.Status.CLOSED),
        'closed_sessions': sessions.filter(status=CategorySession.Status.CLOSED),
    })
