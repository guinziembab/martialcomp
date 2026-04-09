# apps/competitions/views/adhoc_judges.py
"""
Vues pour la gestion des juges ad-hoc (temporaires/bénévoles).
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q
import json
import logging

from apps.competitions.models import Competition, Practitioner, CompetitionCategory, CompetitionRegistration
from apps.competitions.models.adhoc_judges import AdHocJudge
from apps.competitions.utils.decorators import manager_required

logger = logging.getLogger(__name__)


@login_required
@manager_required
def adhoc_judges_list(request, competition_id):
    """
    API pour récupérer la liste des juges ad-hoc d'une compétition.
    Retourne les juges actifs et en attente.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    adhoc_judges = AdHocJudge.objects.filter(
        competition=competition
    ).select_related('practitioner', 'practitioner__organization', 'recruited_by').prefetch_related('assigned_categories')

    judges_data = []
    for adhoc in adhoc_judges:
        judges_data.append({
            'id': adhoc.id,
            'practitioner_id': adhoc.practitioner.id,
            'practitioner_name': adhoc.practitioner.full_name,
            'practitioner_age': adhoc.practitioner_age,
            'club': adhoc.practitioner.organization.name if adhoc.practitioner.organization else None,
            'judge_type': adhoc.judge_type,
            'judge_type_display': adhoc.get_judge_type_display(),
            'status': adhoc.status,
            'status_display': adhoc.get_status_display(),
            'experience_level': adhoc.experience_level,
            'experience_level_display': adhoc.get_experience_level_display(),
            'source': adhoc.source,
            'source_display': adhoc.get_source_display(),
            'categories': [{'id': c.id, 'name': c.name} for c in adhoc.assigned_categories.all()],
            'activated_at': adhoc.activated_at.isoformat() if adhoc.activated_at else None,
            'briefing_completed': adhoc.briefing_completed,
            'has_account': adhoc.practitioner.user is not None,
            'recruited_by': adhoc.recruited_by.get_full_name() if adhoc.recruited_by else None,
            'recruitment_date': adhoc.recruitment_date.isoformat() if adhoc.recruitment_date else None,
        })

    return JsonResponse({
        'success': True,
        'judges': judges_data,
        'count': len(judges_data)
    })


@login_required
@manager_required
def eligible_practitioners(request, competition_id):
    """
    API pour récupérer les pratiquants éligibles pour être juges ad-hoc.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    judge_type = request.GET.get('judge_type', 'technical_judge')
    min_age = int(request.GET.get('min_age', 18))

    eligible = AdHocJudge.get_eligible_participants(
        competition,
        judge_type=judge_type,
        min_age=min_age
    )

    def serialize_practitioner(p, is_registered=False):
        # Récupérer les catégories d'inscription si inscrit
        categories = []
        if is_registered:
            try:
                reg = CompetitionRegistration.objects.get(
                    competition=competition,
                    practitioner=p
                )
                categories = [{'id': c.id, 'name': c.name} for c in reg.categories.all()]
            except CompetitionRegistration.DoesNotExist:
                pass

        return {
            'id': p.id,
            'full_name': p.full_name,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'age': p.age if hasattr(p, 'age') and p.birth_date else None,
            'club': p.organization.name if p.organization else None,
            'club_id': p.organization.id if p.organization else None,
            'grade': str(p.current_grade) if hasattr(p, 'current_grade') and p.current_grade else None,
            'has_account': p.user is not None,
            'is_registered': is_registered,
            'categories': categories,
        }

    registered_list = [serialize_practitioner(p, True) for p in eligible['registered_participants']]
    discipline_list = [serialize_practitioner(p, False) for p in eligible['discipline_practitioners']]

    return JsonResponse({
        'success': True,
        'registered': registered_list,
        'registered_count': len(registered_list),
        'discipline': discipline_list,
        'discipline_count': len(discipline_list),
    })


@login_required
@require_POST
@manager_required
def recruit_adhoc_judge(request, competition_id):
    """
    API pour recruter un juge ad-hoc.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        # Parser le JSON ou les données POST
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        practitioner_id = data.get('practitioner_id')
        judge_type = data.get('judge_type', 'technical_judge')
        experience_level = data.get('experience_level', 'novice')
        category_ids = data.get('categories', [])
        if isinstance(category_ids, str):
            category_ids = [int(x) for x in category_ids.split(',') if x.strip()]
        notes = data.get('notes', '')
        activate_immediately = data.get('activate_immediately', True)
        if isinstance(activate_immediately, str):
            activate_immediately = activate_immediately.lower() in ('true', '1', 'on', 'yes')

        # Récupérer le pratiquant
        practitioner = Practitioner.objects.get(id=practitioner_id)

        # Vérifier l'âge
        if practitioner.age < 18:
            return JsonResponse({
                'success': False,
                'error': _("Le pratiquant doit avoir au moins 18 ans.")
            }, status=400)

        # Vérifier s'il n'est pas déjà assigné pour ce type
        existing = AdHocJudge.objects.filter(
            competition=competition,
            practitioner=practitioner,
            judge_type=judge_type,
            status__in=['pending', 'active']
        ).exists()

        if existing:
            return JsonResponse({
                'success': False,
                'error': _("Ce pratiquant est déjà assigné comme {} pour cette compétition.").format(
                    dict(AdHocJudge.JUDGE_TYPE_CHOICES).get(judge_type, judge_type)
                )
            }, status=400)

        # Déterminer la source
        is_registered = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner=practitioner
        ).exists()
        source = 'competition_participant' if is_registered else 'discipline_practitioner'

        # Créer le juge ad-hoc
        adhoc = AdHocJudge.objects.create(
            competition=competition,
            practitioner=practitioner,
            judge_type=judge_type,
            experience_level=experience_level,
            source=source,
            recruited_by=request.user,
            notes=notes,
            status='pending'
        )

        # Assigner les catégories
        if category_ids:
            categories = CompetitionCategory.objects.filter(
                id__in=category_ids,
                competition=competition
            )
            adhoc.assigned_categories.set(categories)

        # Activer immédiatement si demandé
        if activate_immediately:
            adhoc.activate(user=request.user)

            # Créer un compte utilisateur si nécessaire
            if not practitioner.user:
                try:
                    user, password, created = practitioner.create_user_account()
                    if created:
                        logger.info(f"Compte créé pour le juge ad-hoc {practitioner.full_name}")
                except Exception as e:
                    logger.warning(f"Erreur création compte pour {practitioner.full_name}: {e}")

        logger.info(f"Juge ad-hoc recruté: {practitioner.full_name} comme {judge_type} pour {competition.title}")

        return JsonResponse({
            'success': True,
            'message': _("Juge ad-hoc recruté avec succès."),
            'adhoc_id': adhoc.id,
            'activated': activate_immediately,
            'has_account': practitioner.user is not None
        })

    except Practitioner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _("Pratiquant non trouvé.")
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': _("Format de données invalide.")
        }, status=400)
    except Exception as e:
        logger.exception(f"Erreur recrutement juge ad-hoc: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@manager_required
def update_adhoc_judge(request, adhoc_id):
    """
    API pour mettre à jour un juge ad-hoc.
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Mise à jour des champs modifiables
        if 'experience_level' in data:
            adhoc.experience_level = data['experience_level']

        if 'notes' in data:
            adhoc.notes = data['notes']

        if 'categories' in data:
            category_ids = data['categories']
            if isinstance(category_ids, str):
                category_ids = [int(x) for x in category_ids.split(',') if x.strip()]
            categories = CompetitionCategory.objects.filter(
                id__in=category_ids,
                competition=adhoc.competition
            )
            adhoc.assigned_categories.set(categories)

        adhoc.save()

        return JsonResponse({
            'success': True,
            'message': _("Juge ad-hoc mis à jour.")
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@manager_required
def activate_adhoc_judge(request, adhoc_id):
    """
    API pour activer un juge ad-hoc.
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    if adhoc.status == 'active':
        return JsonResponse({
            'success': False,
            'error': _("Ce juge est déjà actif.")
        }, status=400)

    adhoc.activate(user=request.user)

    # Créer un compte si nécessaire
    account_created = False
    if not adhoc.practitioner.user:
        try:
            user, password, created = adhoc.practitioner.create_user_account()
            account_created = created
        except Exception as e:
            logger.warning(f"Erreur création compte: {e}")

    return JsonResponse({
        'success': True,
        'message': _("Juge ad-hoc activé."),
        'account_created': account_created,
        'has_account': adhoc.practitioner.user is not None
    })


@login_required
@require_POST
@manager_required
def deactivate_adhoc_judge(request, adhoc_id):
    """
    API pour désactiver un juge ad-hoc.
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        reason = data.get('reason', 'completed')

        if reason not in ['completed', 'revoked', 'declined']:
            reason = 'completed'

        adhoc.deactivate(reason=reason)

        return JsonResponse({
            'success': True,
            'message': _("Juge ad-hoc désactivé.")
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@manager_required
def mark_briefing_completed(request, adhoc_id):
    """
    API pour marquer le briefing comme effectué.
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    adhoc.mark_briefing_completed()

    return JsonResponse({
        'success': True,
        'message': _("Briefing marqué comme effectué."),
        'briefing_date': adhoc.briefing_date.isoformat() if adhoc.briefing_date else None
    })


@login_required
@require_POST
@manager_required
def rate_adhoc_judge(request, adhoc_id):
    """
    API pour évaluer la performance d'un juge ad-hoc.
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        rating = int(data.get('rating', 0))
        if rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'error': _("La note doit être entre 1 et 5.")
            }, status=400)

        adhoc.performance_rating = rating
        adhoc.performance_comments = data.get('comments', '')
        adhoc.save()

        return JsonResponse({
            'success': True,
            'message': _("Évaluation enregistrée.")
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': _("Note invalide.")
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@manager_required
def delete_adhoc_judge(request, adhoc_id):
    """
    API pour supprimer un juge ad-hoc (seulement si pending).
    """
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)

    if adhoc.status not in ['pending', 'declined']:
        return JsonResponse({
            'success': False,
            'error': _("Seuls les juges en attente ou ayant décliné peuvent être supprimés.")
        }, status=400)

    practitioner_name = adhoc.practitioner.full_name
    adhoc.delete()

    return JsonResponse({
        'success': True,
        'message': _("Juge ad-hoc {} supprimé.").format(practitioner_name)
    })


# ============================================
# Vues pour le dashboard juge (côté pratiquant)
# ============================================

@login_required
def my_adhoc_assignments(request):
    """
    Vue pour un pratiquant qui veut voir ses assignations ad-hoc.
    """
    user = request.user

    # Trouver le practitioner lié à l'utilisateur
    try:
        practitioner = Practitioner.objects.get(user=user)
    except Practitioner.DoesNotExist:
        return JsonResponse({
            'success': True,
            'assignments': [],
            'count': 0,
            'is_adhoc_judge': False
        })

    # Récupérer les assignations actives
    active_assignments = AdHocJudge.get_active_for_practitioner(practitioner)

    assignments_data = []
    for adhoc in active_assignments:
        assignments_data.append({
            'id': adhoc.id,
            'competition_id': adhoc.competition.id,
            'competition_title': adhoc.competition.title,
            'competition_date': adhoc.competition.start_date.isoformat() if adhoc.competition.start_date else None,
            'judge_type': adhoc.judge_type,
            'judge_type_display': adhoc.get_judge_type_display(),
            'categories': [{'id': c.id, 'name': c.name} for c in adhoc.assigned_categories.all()],
            'briefing_completed': adhoc.briefing_completed,
            'activated_at': adhoc.activated_at.isoformat() if adhoc.activated_at else None,
        })

    return JsonResponse({
        'success': True,
        'assignments': assignments_data,
        'count': len(assignments_data),
        'is_adhoc_judge': len(assignments_data) > 0
    })


def get_adhoc_judge_context(user):
    """
    Fonction utilitaire pour récupérer le contexte ad-hoc d'un utilisateur.
    À utiliser dans les vues du dashboard juge.
    """
    context = {
        'is_adhoc_judge': False,
        'adhoc_assignments': [],
    }

    try:
        practitioner = Practitioner.objects.get(user=user)
        adhoc_active = AdHocJudge.get_active_for_practitioner(practitioner)

        if adhoc_active.exists():
            context['is_adhoc_judge'] = True
            context['adhoc_assignments'] = adhoc_active
    except Practitioner.DoesNotExist:
        pass

    return context


# ============================================
# API pour les affectations de juges aux catégories
# ============================================

@login_required
@require_POST
@manager_required
def assign_judge_to_category(request, competition_id):
    """
    API pour assigner un juge à une catégorie (drag & drop).
    Supporte à la fois les juges Ad-Hoc et les juges officiels.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        adhoc_id = data.get('adhoc_id')
        judge_id = data.get('judge_id')  # ID du juge officiel (modèle Judge)
        practitioner_id = data.get('practitioner_id')  # ID du pratiquant
        category_id = data.get('category_id')
        is_adhoc = data.get('is_adhoc', True)  # Par défaut ad-hoc pour rétrocompatibilité

        if not category_id:
            return JsonResponse({
                'success': False,
                'error': _("Catégorie manquante.")
            }, status=400)

        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        # Cas 1: Juge Ad-Hoc (avec un AdHocJudge existant)
        if adhoc_id and (is_adhoc == True or is_adhoc == 'true'):
            adhoc = get_object_or_404(AdHocJudge, id=adhoc_id, competition=competition)
            adhoc.assigned_categories.add(category)

            return JsonResponse({
                'success': True,
                'message': _("Juge affecté à la catégorie."),
                'judge_name': adhoc.practitioner.full_name,
                'category_name': category.name,
                'is_adhoc': True,
                'categories': [{'id': c.id, 'name': c.name} for c in adhoc.assigned_categories.all()]
            })

        # Cas 2: Juge officiel - via practitioner_id (préféré) ou judge_id
        elif practitioner_id or judge_id or (adhoc_id and is_adhoc in [False, 'false']):
            practitioner = None

            # Résoudre le pratiquant par practitioner_id (méthode préférée)
            if practitioner_id:
                practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            elif judge_id:
                from apps.competitions.models import Judge
                judge = get_object_or_404(Judge, id=judge_id, active=True)
                practitioner = judge.practitioner
            elif adhoc_id:
                # Fallback: essayer comme registration ID
                reg = CompetitionRegistration.objects.filter(
                    id=adhoc_id, competition=competition
                ).select_related('practitioner').first()
                if reg:
                    practitioner = reg.practitioner

            if not practitioner:
                return JsonResponse({
                    'success': False,
                    'error': _("Pratiquant introuvable.")
                }, status=404)

            # Déterminer le type de juge basé sur la CompetitionRegistration
            judge_type = 'technical_judge'
            try:
                reg = CompetitionRegistration.objects.get(
                    competition=competition, practitioner=practitioner
                )
                if reg.is_combat_referee and not reg.is_technical_judge:
                    judge_type = 'combat_referee'
            except CompetitionRegistration.DoesNotExist:
                pass

            # Chercher un profil Judge officiel pour les notes
            judge_profile = None
            try:
                from apps.competitions.models import Judge
                judge_profile = Judge.objects.get(practitioner=practitioner, active=True)
            except Exception:
                pass

            # Créer ou récupérer un AdHocJudge pour tracker l'assignation
            adhoc_temp, created = AdHocJudge.objects.get_or_create(
                competition=competition,
                practitioner=practitioner,
                judge_type=judge_type,
                defaults={
                    'status': 'active',
                    'experience_level': judge_profile.qualification_level if judge_profile else 'intermediate',
                    'recruited_by': request.user,
                    'source': 'official_judge' if judge_profile else 'competition_participant',
                    'notes': f"Juge officiel - {judge_profile.get_qualification_level_display()}" if judge_profile else "Assigné via interface"
                }
            )

            # S'assurer qu'il est actif
            if adhoc_temp.status != 'active':
                adhoc_temp.status = 'active'
                adhoc_temp.save()

            adhoc_temp.assigned_categories.add(category)

            return JsonResponse({
                'success': True,
                'message': _("Juge affecté à la catégorie."),
                'judge_name': practitioner.full_name,
                'category_name': category.name,
                'is_adhoc': False,
                'adhoc_id': adhoc_temp.id,
                'categories': [{'id': c.id, 'name': c.name} for c in adhoc_temp.assigned_categories.all()]
            })

        else:
            return JsonResponse({
                'success': False,
                'error': _("ID du juge manquant.")
            }, status=400)

    except Exception as e:
        logger.exception(f"Erreur affectation juge à catégorie: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@manager_required
def remove_judge_from_category(request, competition_id):
    """
    API pour retirer un juge ad-hoc d'une catégorie.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        adhoc_id = data.get('adhoc_id')
        category_id = data.get('category_id')

        if not adhoc_id or not category_id:
            return JsonResponse({
                'success': False,
                'error': _("Données manquantes.")
            }, status=400)

        adhoc = get_object_or_404(AdHocJudge, id=adhoc_id, competition=competition)
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        # Retirer la catégorie
        adhoc.assigned_categories.remove(category)

        return JsonResponse({
            'success': True,
            'message': _("Juge retiré de la catégorie."),
            'judge_name': adhoc.practitioner.full_name,
            'category_name': category.name,
            'categories': [{'id': c.id, 'name': c.name} for c in adhoc.assigned_categories.all()]
        })

    except Exception as e:
        logger.exception(f"Erreur retrait juge de catégorie: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@manager_required
def get_category_judges(request, competition_id, category_id):
    """
    API pour récupérer les juges assignés à une catégorie.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

    # Récupérer les juges ad-hoc assignés à cette catégorie
    adhoc_judges = AdHocJudge.objects.filter(
        competition=competition,
        assigned_categories=category,
        status='active'
    ).select_related('practitioner', 'practitioner__organization')

    judges_data = []
    for adhoc in adhoc_judges:
        judges_data.append({
            'id': adhoc.id,
            'practitioner_id': adhoc.practitioner.id,
            'name': adhoc.practitioner.full_name,
            'judge_type': adhoc.judge_type,
            'judge_type_display': adhoc.get_judge_type_display(),
            'experience_level': adhoc.experience_level,
            'experience_level_display': adhoc.get_experience_level_display(),
            'is_adhoc': True
        })

    return JsonResponse({
        'success': True,
        'judges': judges_data,
        'count': len(judges_data),
        'category_name': category.name
    })
