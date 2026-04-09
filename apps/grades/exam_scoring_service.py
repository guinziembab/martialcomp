"""Service de calcul pour la notation des examens de grade."""
from decimal import Decimal
from django.db.models import Avg, Count, Q
from django.utils import timezone


def get_score_color(value, max_score=10.0):
    """Retourne le code couleur CSS selon la note."""
    if value is None:
        return '#6c757d'  # gris
    ratio = float(value) / float(max_score)
    if ratio >= 0.7:
        return '#28a745'  # vert
    elif ratio >= 0.5:
        return '#ffc107'  # jaune
    else:
        return '#dc3545'  # rouge


def get_score_class(value, max_score=10.0):
    """Retourne la classe CSS selon la note."""
    if value is None:
        return 'score-none'
    ratio = float(value) / float(max_score)
    if ratio >= 0.7:
        return 'score-good'
    elif ratio >= 0.5:
        return 'score-average'
    else:
        return 'score-poor'


def calculate_criterion_score(registration, criterion):
    """Calcule la moyenne des notes des examinateurs pour un critère."""
    from .models import ExamScore
    result = ExamScore.objects.filter(
        registration=registration,
        criterion=criterion
    ).aggregate(avg=Avg('value'), count=Count('id'))
    return {
        'average': result['avg'],
        'count': result['count'],
        'color': get_score_color(result['avg'], float(criterion.max_score)),
        'css_class': get_score_class(result['avg'], float(criterion.max_score)),
    }


def calculate_module_score(registration, module):
    """Calcule la moyenne pondérée (coefficients) des critères d'un module."""
    from .models import ExamScore
    criteria = module.criteria.all()
    total_weighted = Decimal('0')
    total_coeff = Decimal('0')
    scored_count = 0

    for criterion in criteria:
        avg = ExamScore.objects.filter(
            registration=registration,
            criterion=criterion
        ).aggregate(avg=Avg('value'))['avg']
        if avg is not None:
            total_weighted += Decimal(str(avg)) * criterion.coefficient
            total_coeff += criterion.coefficient
            scored_count += 1

    if total_coeff > 0:
        score = total_weighted / total_coeff
        return {
            'score': round(score, 2),
            'color': get_score_color(float(score)),
            'css_class': get_score_class(float(score)),
            'scored_criteria': scored_count,
            'total_criteria': criteria.count(),
        }
    return {
        'score': None,
        'color': '#6c757d',
        'css_class': 'score-none',
        'scored_criteria': 0,
        'total_criteria': criteria.count(),
    }


def calculate_total_score(registration):
    """Calcule le score total d'un pratiquant pour un examen."""
    modules = registration.exam.scoring_modules.all()
    total_weighted = Decimal('0')
    total_coeff = Decimal('0')
    module_scores = []

    for module in modules:
        ms = calculate_module_score(registration, module)
        module_scores.append({
            'module': module,
            **ms,
        })
        if ms['score'] is not None:
            # Poids uniforme par module (1.0 chacun)
            total_weighted += ms['score']
            total_coeff += Decimal('1')

    final_score = round(total_weighted / total_coeff, 2) if total_coeff > 0 else None
    return {
        'total': final_score,
        'color': get_score_color(float(final_score)) if final_score else '#6c757d',
        'css_class': get_score_class(float(final_score)) if final_score else 'score-none',
        'module_scores': module_scores,
    }


def get_scoring_dashboard_data(exam):
    """Génère les données pour le dashboard de notation."""
    from .models import ExamScore, ExamScoringCriterion
    registrations = exam.registrations.filter(
        status__in=['approved', 'passed', 'failed']
    ).select_related('practitioner', 'target_grade')

    modules = exam.scoring_modules.prefetch_related('criteria').all()

    # Nombre total de notes attendues
    total_criteria = ExamScoringCriterion.objects.filter(module__exam=exam).count()
    total_examiners = 0
    for module in modules:
        total_examiners = max(total_examiners, module.assigned_examiners.count())
    # Approximation: chaque critère noté par les examinateurs du module
    expected_scores = 0
    for module in modules:
        n_examiners = module.assigned_examiners.count() or 1
        n_criteria = module.criteria.count()
        expected_scores += n_examiners * n_criteria * registrations.count()

    actual_scores = ExamScore.objects.filter(
        registration__exam=exam
    ).count()

    # Données par pratiquant
    practitioner_data = []
    for reg in registrations:
        result = calculate_total_score(reg)
        practitioner_data.append({
            'registration': reg,
            'total_score': result['total'],
            'total_color': result['color'],
            'total_class': result['css_class'],
            'module_scores': result['module_scores'],
        })

    # Tri par score décroissant
    practitioner_data.sort(
        key=lambda x: float(x['total_score']) if x['total_score'] is not None else -1,
        reverse=True
    )

    # Stats
    scores = [float(p['total_score']) for p in practitioner_data if p['total_score'] is not None]
    return {
        'modules': modules,
        'practitioner_data': practitioner_data,
        'total_registrations': registrations.count(),
        'expected_scores': expected_scores,
        'actual_scores': actual_scores,
        'progress_percent': round(actual_scores / expected_scores * 100) if expected_scores > 0 else 0,
        'avg_score': round(sum(scores) / len(scores), 2) if scores else None,
        'max_score': round(max(scores), 2) if scores else None,
        'min_score': round(min(scores), 2) if scores else None,
    }


def publish_results(exam, passing_threshold=5.0):
    """Publie les résultats : met à jour les statuts et crée les PractitionerGrade."""
    from .models import PractitionerGrade
    registrations = exam.registrations.filter(status='approved')
    results = {'passed': 0, 'failed': 0}

    for reg in registrations:
        result = calculate_total_score(reg)
        total = result['total']
        if total is not None:
            reg.score = total
            if float(total) >= passing_threshold:
                reg.status = 'passed'
                results['passed'] += 1
                # Créer le PractitionerGrade automatiquement
                PractitionerGrade.objects.get_or_create(
                    practitioner=reg.practitioner,
                    grade=reg.target_grade,
                    discipline=reg.target_grade.discipline,
                    defaults={
                        'date_obtained': exam.date,
                        'awarded_by': exam.examiners or exam.title,
                        'location': exam.location,
                        'is_current': True,
                        'notes': f"Score: {total}/10 - Examen: {exam.title}",
                    }
                )
            else:
                reg.status = 'failed'
                results['failed'] += 1
            reg.save()

    # Mettre à jour le statut de l'examen
    exam.status = 'completed'
    exam.save()

    return results
