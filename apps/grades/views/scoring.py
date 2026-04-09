"""Vues pour la notation des examens de grade."""
import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.translation import gettext_lazy as _

from apps.competitions.models import Practitioner
from apps.competitions.utils.permission_helpers import get_user_organization
from apps.grades.models import (
    GradeExam,
    GradeExamRegistration,
    ExamScoringModule,
    ExamScoringCriterion,
    ExamScore,
)
from apps.grades.forms import ExamScoringModuleForm, ExamScoringCriterionForm
from apps.grades.exam_scoring_service import (
    calculate_criterion_score,
    calculate_module_score,
    calculate_total_score,
    get_scoring_dashboard_data,
    get_score_color,
    publish_results,
)


@login_required
def scoring_config(request, exam_id):
    """Configuration de la feuille de notation (modules + critères)."""
    exam = get_object_or_404(GradeExam, pk=exam_id)
    modules = exam.scoring_modules.prefetch_related('criteria', 'assigned_examiners').all()

    # Examinateurs disponibles (ceux définis sur l'examen)
    org = get_user_organization(request.user)
    if org:
        available_examiners = Practitioner.objects.filter(
            organization=org
        ).order_by('last_name', 'first_name')
    else:
        available_examiners = Practitioner.objects.none()

    # Récupérer les noms des examinateurs de l'examen pour pré-filtrer
    exam_examiner_names = [n.strip() for n in exam.examiners.split(',') if n.strip()] if exam.examiners else []

    context = {
        'exam': exam,
        'modules': modules,
        'available_examiners': available_examiners,
        'exam_examiner_names': exam_examiner_names,
        'module_form': ExamScoringModuleForm(),
        'criterion_form': ExamScoringCriterionForm(),
    }
    return render(request, 'grades/scoring/scoring_config.html', context)


@login_required
def examiner_sheet(request, exam_id):
    """Feuille de notation pour un examinateur."""
    exam = get_object_or_404(GradeExam, pk=exam_id)

    # Identifier le Practitioner correspondant à l'utilisateur connecté
    org = get_user_organization(request.user)
    current_examiner = None
    if org:
        current_examiner = Practitioner.objects.filter(
            organization=org,
            user=request.user
        ).first()

    # Modules assignés à cet examinateur (ou tous si admin/organisateur)
    all_modules = exam.scoring_modules.prefetch_related('criteria').all()
    if current_examiner:
        assigned_modules = [m for m in all_modules if current_examiner in m.assigned_examiners.all()]
        if not assigned_modules:
            # Si pas assigné spécifiquement, montrer tous les modules
            assigned_modules = list(all_modules)
    else:
        assigned_modules = list(all_modules)

    # Récupérer les inscriptions approuvées
    registrations = exam.registrations.filter(
        status__in=['approved', 'passed', 'failed']
    ).select_related('practitioner', 'target_grade').order_by('practitioner__last_name')

    # Construire la grille de données: scores existants
    score_grid = {}
    existing_scores = ExamScore.objects.filter(
        registration__exam=exam
    ).select_related('registration', 'criterion')
    if current_examiner:
        existing_scores = existing_scores.filter(examiner=current_examiner)

    for score in existing_scores:
        key = (score.registration_id, score.criterion_id)
        score_grid[key] = {
            'value': float(score.value),
            'color': get_score_color(float(score.value), float(score.criterion.max_score)),
        }

    # Compiler les critères de tous les modules assignés
    all_criteria = []
    for module in assigned_modules:
        for criterion in module.criteria.all():
            all_criteria.append({
                'id': criterion.id,
                'name': criterion.name,
                'module_name': module.name,
                'coefficient': float(criterion.coefficient),
                'max_score': float(criterion.max_score),
            })

    context = {
        'exam': exam,
        'modules': assigned_modules,
        'registrations': registrations,
        'score_grid': score_grid,
        'all_criteria': all_criteria,
        'current_examiner': current_examiner,
        'score_options': [round(x * 0.5, 1) for x in range(0, 21)],  # 0, 0.5, 1, ..., 10
    }
    return render(request, 'grades/scoring/examiner_sheet.html', context)


@login_required
def scoring_dashboard(request, exam_id):
    """Dashboard central de notation pour l'organisateur."""
    exam = get_object_or_404(GradeExam, pk=exam_id)
    dashboard_data = get_scoring_dashboard_data(exam)

    context = {
        'exam': exam,
        **dashboard_data,
    }
    return render(request, 'grades/scoring/scoring_dashboard.html', context)


@login_required
def exam_results(request, exam_id):
    """Résultats publiés d'un examen."""
    exam = get_object_or_404(GradeExam, pk=exam_id)
    modules = exam.scoring_modules.prefetch_related('criteria').all()

    registrations = exam.registrations.filter(
        status__in=['passed', 'failed']
    ).select_related('practitioner', 'target_grade').order_by('-score')

    # Enrichir chaque inscription avec les scores détaillés
    results = []
    for rank, reg in enumerate(registrations, 1):
        result = calculate_total_score(reg)
        results.append({
            'rank': rank,
            'registration': reg,
            'total_score': result['total'],
            'total_color': result['color'],
            'total_class': result['css_class'],
            'module_scores': result['module_scores'],
        })

    context = {
        'exam': exam,
        'modules': modules,
        'results': results,
    }
    return render(request, 'grades/scoring/exam_results.html', context)


# ========== AJAX endpoints ==========

@login_required
@require_POST
def ajax_save_score(request):
    """Sauvegarde AJAX d'une note individuelle."""
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        criterion_id = data.get('criterion_id')
        examiner_id = data.get('examiner_id')
        value = data.get('value')

        if value == '' or value is None:
            # Supprimer la note si vide
            ExamScore.objects.filter(
                registration_id=registration_id,
                criterion_id=criterion_id,
                examiner_id=examiner_id,
            ).delete()
            criterion = get_object_or_404(ExamScoringCriterion, pk=criterion_id)
            registration = get_object_or_404(GradeExamRegistration, pk=registration_id)
            crit_data = calculate_criterion_score(registration, criterion)
            return JsonResponse({
                'status': 'deleted',
                'criterion_avg': float(crit_data['average']) if crit_data['average'] else None,
                'criterion_color': crit_data['color'],
            })

        value = Decimal(str(value))
        if value < 0 or value > 10:
            return JsonResponse({'error': 'Note invalide (0-10)'}, status=400)

        registration = get_object_or_404(GradeExamRegistration, pk=registration_id)
        criterion = get_object_or_404(ExamScoringCriterion, pk=criterion_id)
        examiner = get_object_or_404(Practitioner, pk=examiner_id)

        score, created = ExamScore.objects.update_or_create(
            registration=registration,
            criterion=criterion,
            examiner=examiner,
            defaults={'value': value}
        )

        # Recalculer les moyennes
        crit_data = calculate_criterion_score(registration, criterion)
        total_data = calculate_total_score(registration)

        return JsonResponse({
            'status': 'saved',
            'value': float(score.value),
            'color': get_score_color(float(score.value), float(criterion.max_score)),
            'criterion_avg': float(crit_data['average']) if crit_data['average'] else None,
            'criterion_color': crit_data['color'],
            'total_score': float(total_data['total']) if total_data['total'] else None,
            'total_color': total_data['color'],
        })
    except (ValueError, InvalidOperation):
        return JsonResponse({'error': 'Valeur invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_publish_results(request, exam_id):
    """Publie les résultats de l'examen."""
    exam = get_object_or_404(GradeExam, pk=exam_id)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    threshold = float(data.get('threshold', 5.0))

    results = publish_results(exam, passing_threshold=threshold)
    return JsonResponse({
        'status': 'published',
        'passed': results['passed'],
        'failed': results['failed'],
    })


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def scoring_module_manage(request, exam_id):
    """CRUD pour les modules de notation."""
    exam = get_object_or_404(GradeExam, pk=exam_id)

    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        module_id = data.get('module_id')

        if module_id:
            # Update
            module = get_object_or_404(ExamScoringModule, pk=module_id, exam=exam)
            module.name = data.get('name', module.name)
            module.order = int(data.get('order', module.order))
            module.save()
            # Mettre à jour les examinateurs assignés
            examiner_ids = data.get('examiner_ids', [])
            if isinstance(examiner_ids, str):
                examiner_ids = json.loads(examiner_ids) if examiner_ids else []
            module.assigned_examiners.set(examiner_ids)
        else:
            # Create
            module = ExamScoringModule.objects.create(
                exam=exam,
                name=data.get('name', _('Nouveau module')),
                order=int(data.get('order', 0)),
            )
            examiner_ids = data.get('examiner_ids', [])
            if isinstance(examiner_ids, str):
                examiner_ids = json.loads(examiner_ids) if examiner_ids else []
            if examiner_ids:
                module.assigned_examiners.set(examiner_ids)

        return JsonResponse({
            'status': 'ok',
            'module_id': module.id,
            'name': module.name,
            'order': module.order,
        })

    elif request.method == 'DELETE':
        data = json.loads(request.body)
        module_id = data.get('module_id')
        module = get_object_or_404(ExamScoringModule, pk=module_id, exam=exam)
        module.delete()
        return JsonResponse({'status': 'deleted'})

    # GET: retourne la liste des modules
    modules = exam.scoring_modules.prefetch_related('criteria', 'assigned_examiners').all()
    modules_data = []
    for m in modules:
        modules_data.append({
            'id': m.id,
            'name': m.name,
            'order': m.order,
            'examiner_ids': list(m.assigned_examiners.values_list('id', flat=True)),
            'criteria': [
                {
                    'id': c.id,
                    'name': c.name,
                    'coefficient': float(c.coefficient),
                    'max_score': float(c.max_score),
                    'order': c.order,
                }
                for c in m.criteria.all()
            ],
        })
    return JsonResponse({'modules': modules_data})


@login_required
@require_http_methods(["POST", "DELETE"])
def scoring_criterion_manage(request, module_id):
    """CRUD pour les critères de notation."""
    module = get_object_or_404(ExamScoringModule, pk=module_id)

    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        criterion_id = data.get('criterion_id')

        if criterion_id:
            # Update
            criterion = get_object_or_404(ExamScoringCriterion, pk=criterion_id, module=module)
            criterion.name = data.get('name', criterion.name)
            criterion.coefficient = Decimal(str(data.get('coefficient', criterion.coefficient)))
            criterion.max_score = Decimal(str(data.get('max_score', criterion.max_score)))
            criterion.order = int(data.get('order', criterion.order))
            criterion.description = data.get('description', criterion.description)
            criterion.save()
        else:
            # Create
            criterion = ExamScoringCriterion.objects.create(
                module=module,
                name=data.get('name', _('Nouveau critère')),
                coefficient=Decimal(str(data.get('coefficient', '1.0'))),
                max_score=Decimal(str(data.get('max_score', '10.0'))),
                order=int(data.get('order', 0)),
                description=data.get('description', ''),
            )

        return JsonResponse({
            'status': 'ok',
            'criterion_id': criterion.id,
            'name': criterion.name,
            'coefficient': float(criterion.coefficient),
            'max_score': float(criterion.max_score),
            'order': criterion.order,
        })

    elif request.method == 'DELETE':
        data = json.loads(request.body)
        criterion_id = data.get('criterion_id')
        criterion = get_object_or_404(ExamScoringCriterion, pk=criterion_id, module=module)
        criterion.delete()
        return JsonResponse({'status': 'deleted'})
