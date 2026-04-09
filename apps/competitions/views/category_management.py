"""
Vues pour la gestion des catégories de compétition - Version simplifiée
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from ..models import Competition, CompetitionCategory, CompetitionType


@login_required
def manage_categories(request, competition_id):
    """Gérer les catégories d'une compétition - Vue simplifiée"""
    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer les catégories existantes avec leurs inscriptions
    from ..models import CompetitionRegistration

    # Récupérer les catégories triées par type puis par âge minimum
    categories = competition.categories.all().select_related(
        'competition_type'
    ).prefetch_related(
        'registrations'
    ).order_by(
        'competition_type__name',  # D'abord par type
        'min_age',                  # Puis par âge minimum
        'min_grade',                # Puis par grade minimum
        'name'                      # Puis par nom
    )

    # Note: judge_user_ids n'est plus utilisé, on vérifie directement via Judge.objects.filter(practitioner=...)

    # Organiser les catégories par type de compétition
    categories_by_type = {}
    for category in categories:
        type_name = category.competition_type.name if category.competition_type else _("Sans type")
        type_id = category.competition_type.id if category.competition_type else 0

        if type_id not in categories_by_type:
            categories_by_type[type_id] = {
                'type': category.competition_type,
                'type_name': type_name,
                'categories': []
            }

        # Récupérer les inscriptions
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            categories=category
        ).select_related(
            'practitioner',
            'practitioner__organization'
        ).prefetch_related(
            'practitioner__disciplines'
        )

        # Vérifier si les pratiquants sont juges/arbitres
        registrations_with_roles = []
        for reg in registrations:
            practitioner = reg.practitioner
            is_judge = False
            is_referee = False

            # Vérifier directement via le modèle Judge
            try:
                from apps.competitions.models import Judge
                judge = Judge.objects.filter(practitioner=practitioner).first()
                if judge:
                    is_judge = judge.is_technical_judge
                    is_referee = judge.is_combat_referee
            except Exception:
                pass

            registrations_with_roles.append({
                'registration': reg,
                'practitioner': practitioner,
                'is_judge': is_judge,
                'is_referee': is_referee
            })

        categories_by_type[type_id]['categories'].append({
            'category': category,
            'registrations': registrations_with_roles,
            'count': len(registrations_with_roles)
        })

    # Préparer les données pour le template (liste plate aussi pour compatibilité)
    categories_with_registrations = []
    for type_data in categories_by_type.values():
        categories_with_registrations.extend(type_data['categories'])

    # Récupérer les grades pour la discipline
    grades = []
    try:
        if competition.discipline:
            from apps.grades.models import Grade
            grades = list(Grade.objects.filter(
                discipline=competition.discipline
            ).order_by('level'))
    except Exception:
        pass

    context = {
        'competition': competition,
        'categories': categories,
        'categories_with_registrations': categories_with_registrations,
        'categories_by_type': categories_by_type,
        'grades': grades,
    }

    return render(request, 'competitions/club/competition_management_simple.html', context)


@login_required
def add_category(request, competition_id):
    """Ajouter une catégorie à une compétition - Version simplifiée"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Si c'est une requête GET, rediriger vers la page de gestion des catégories
    if request.method == 'GET':
        return redirect('competitions:competitions:manage_categories', competition_id=competition_id)
    
    try:
        # Récupérer les données
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({
                'success': False,
                'message': _("Le nom de la catégorie est requis.")
            })
        
        # Récupérer un type de compétition par défaut
        comp_type = CompetitionType.objects.filter(discipline=competition.discipline).first()
        if not comp_type:
            return JsonResponse({
                'success': False,
                'message': _("Aucun type de compétition trouvé pour cette discipline.")
            })
        
        # Gérer les champs optionnels
        min_age = request.POST.get('min_age')
        max_age = request.POST.get('max_age')
        min_weight = request.POST.get('min_weight')
        max_weight = request.POST.get('max_weight')
        min_grade = request.POST.get('min_grade')
        max_grade = request.POST.get('max_grade')
        
        # Convertir en types appropriés
        min_age = int(min_age) if min_age and min_age.strip() else None
        max_age = int(max_age) if max_age and max_age.strip() else None
        min_weight = float(min_weight) if min_weight and min_weight.strip() else None
        max_weight = float(max_weight) if max_weight and max_weight.strip() else None
        
        # Gérer le genre
        gender = request.POST.get('gender', 'mixed')
        if gender == 'male':
            gender = 'male'
        elif gender == 'female':
            gender = 'female'
        else:
            gender = 'mixed'
        
        # Créer la catégorie
        category = CompetitionCategory.objects.create(
            competition=competition,
            competition_type=comp_type,
            name=name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            min_weight=min_weight,
            max_weight=max_weight,
            min_grade=min_grade,
            max_grade=max_grade
        )
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie ajoutée avec succès."),
            'category_id': category.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'ajout de la catégorie: {}").format(str(e))
        })


@login_required
@require_POST
def delete_category(request, competition_id):
    """Supprimer une catégorie d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        
        if not category_id:
            return JsonResponse({
                'success': False,
                'message': _("ID de la catégorie requis.")
            })
        
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        
        # Vérifier s'il y a des inscriptions liées
        from apps.competitions.models import CompetitionRegistration
        registrations_count = CompetitionRegistration.objects.filter(
            competition=competition,
            category=category
        ).count()
        
        if registrations_count > 0:
            return JsonResponse({
                'success': False,
                'message': _("Impossible de supprimer cette catégorie car {} inscription(s) y sont liées.").format(registrations_count)
            })
        
        category_name = category.name
        category.delete()

        return JsonResponse({
            'success': True,
            'message': _("Catégorie '{}' supprimée avec succès.").format(category_name)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la suppression de la catégorie: {}").format(str(e))
        })


@login_required
@require_POST
def toggle_practitioner_role(request, competition_id):
    """Toggle le rôle juge/arbitre d'un pratiquant inscrit"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)
        practitioner_id = data.get('practitioner_id')
        role = data.get('role')  # 'judge' ou 'referee'
        action = data.get('action')  # 'add' ou 'remove'

        if not practitioner_id or not role:
            return JsonResponse({
                'success': False,
                'message': _("Paramètres manquants.")
            })

        from ..models import Practitioner, Judge
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)

        # Vérifier ou créer le profil Judge
        judge, created = Judge.objects.get_or_create(
            practitioner=practitioner,
            defaults={
                'user': practitioner.user if hasattr(practitioner, 'user') else None,
                'qualification_level': 'novice',
                'is_technical_judge': False,
                'is_combat_referee': False,
                'active': True
            }
        )

        # Appliquer le changement de rôle
        if role == 'judge':
            if action == 'add':
                judge.is_technical_judge = True
                message = _("Statut juge technique attribué à {}").format(practitioner.full_name)
            else:
                judge.is_technical_judge = False
                message = _("Statut juge technique retiré de {}").format(practitioner.full_name)
        elif role == 'referee':
            if action == 'add':
                judge.is_combat_referee = True
                message = _("Statut arbitre combat attribué à {}").format(practitioner.full_name)
            else:
                judge.is_combat_referee = False
                message = _("Statut arbitre combat retiré de {}").format(practitioner.full_name)
        else:
            return JsonResponse({
                'success': False,
                'message': _("Rôle non reconnu.")
            })

        judge.save()

        # Ajouter le juge à la compétition si pas déjà fait
        if not competition.judges.filter(id=judge.id).exists():
            competition.judges.add(judge)

        return JsonResponse({
            'success': True,
            'message': message,
            'is_judge': judge.is_technical_judge,
            'is_referee': judge.is_combat_referee
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur: {}").format(str(e))
        })


@login_required
@require_POST
def merge_categories(request, competition_id):
    """Fusionner plusieurs catégories en une seule"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)
        category_ids = data.get('category_ids', [])
        new_name = data.get('new_name', '').strip()
        target_category_id = data.get('target_category_id')

        if len(category_ids) < 2:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez sélectionner au moins 2 catégories à fusionner.")
            })

        if not new_name and not target_category_id:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez spécifier un nom pour la nouvelle catégorie ou une catégorie cible.")
            })

        # Récupérer les catégories à fusionner
        categories_to_merge = CompetitionCategory.objects.filter(
            id__in=category_ids,
            competition=competition
        )

        if categories_to_merge.count() != len(category_ids):
            return JsonResponse({
                'success': False,
                'message': _("Une ou plusieurs catégories n'ont pas été trouvées.")
            })

        from ..models import CompetitionRegistration
        from django.db import transaction

        with transaction.atomic():
            # Déterminer la catégorie cible
            if target_category_id:
                target_category = get_object_or_404(
                    CompetitionCategory, id=target_category_id, competition=competition
                )
            else:
                # Créer une nouvelle catégorie en prenant les attributs de la première
                first_cat = categories_to_merge.first()
                target_category = CompetitionCategory.objects.create(
                    competition=competition,
                    competition_type=first_cat.competition_type,
                    name=new_name,
                    gender=first_cat.gender,
                    min_age=min(c.min_age for c in categories_to_merge if c.min_age) if any(c.min_age for c in categories_to_merge) else None,
                    max_age=max(c.max_age for c in categories_to_merge if c.max_age) if any(c.max_age for c in categories_to_merge) else None,
                )

            # Déplacer toutes les inscriptions vers la catégorie cible
            moved_count = 0
            for category in categories_to_merge:
                if category.id == target_category.id:
                    continue

                # Récupérer les inscriptions de cette catégorie
                registrations = CompetitionRegistration.objects.filter(
                    competition=competition,
                    categories=category
                )

                for reg in registrations:
                    # Ajouter à la catégorie cible
                    reg.categories.add(target_category)
                    # Retirer de l'ancienne catégorie
                    reg.categories.remove(category)
                    moved_count += 1

                # Supprimer l'ancienne catégorie
                category.delete()

            # Mettre à jour le nom si spécifié
            if new_name and target_category_id:
                target_category.name = new_name
                target_category.save()

        return JsonResponse({
            'success': True,
            'message': _("Fusion réussie ! {} inscription(s) déplacée(s) vers la catégorie '{}'.").format(
                moved_count, target_category.name
            ),
            'target_category_id': target_category.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la fusion des catégories: {}").format(str(e))
        })


@login_required
@require_POST
def split_category(request, competition_id):
    """
    Diviser une catégorie en deux en fonction de l'âge ou du grade.

    Le split se fait en triant d'abord par âge (primaire) puis par grade (secondaire),
    et en répartissant équitablement les pratiquants entre les deux nouvelles catégories.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        split_criterion = data.get('criterion', 'age')  # 'age' ou 'grade'
        name_category_1 = data.get('name_category_1', '').strip()
        name_category_2 = data.get('name_category_2', '').strip()

        if not category_id:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez sélectionner une catégorie à diviser.")
            })

        if not name_category_1 or not name_category_2:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez spécifier les noms des deux nouvelles catégories.")
            })

        # Récupérer la catégorie à diviser
        category = get_object_or_404(
            CompetitionCategory, id=category_id, competition=competition
        )

        from ..models import CompetitionRegistration
        from django.db import transaction

        # Récupérer les inscriptions de cette catégorie avec les praticiens
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            categories=category
        ).select_related('practitioner')

        if registrations.count() < 2:
            return JsonResponse({
                'success': False,
                'message': _("Il faut au moins 2 pratiquants pour diviser une catégorie.")
            })

        # Trier les pratiquants par âge (décroissant) puis par grade
        def get_sort_key(reg):
            practitioner = reg.practitioner
            # Âge (les plus vieux en premier) - utiliser 0 si pas de date de naissance
            age = practitioner.age if hasattr(practitioner, 'age') and practitioner.age else 0
            # Grade - convertir en ordre numérique si possible
            grade = practitioner.current_grade_name if hasattr(practitioner, 'current_grade_name') else ''
            grade_order = _get_grade_order(grade)
            return (-age, -grade_order)  # Négatif pour tri décroissant

        sorted_registrations = sorted(registrations, key=get_sort_key)

        # Diviser en deux groupes équitables
        midpoint = len(sorted_registrations) // 2
        group_1 = sorted_registrations[:midpoint]  # Les plus âgés/gradés
        group_2 = sorted_registrations[midpoint:]  # Les plus jeunes/moins gradés

        with transaction.atomic():
            # Calculer les bornes d'âge pour chaque groupe
            ages_group_1 = [r.practitioner.age for r in group_1 if hasattr(r.practitioner, 'age') and r.practitioner.age]
            ages_group_2 = [r.practitioner.age for r in group_2 if hasattr(r.practitioner, 'age') and r.practitioner.age]

            # Créer la première catégorie (pour les plus âgés/gradés)
            category_1 = CompetitionCategory.objects.create(
                competition=competition,
                competition_type=category.competition_type,
                name=name_category_1,
                gender=category.gender,
                min_age=min(ages_group_1) if ages_group_1 else category.min_age,
                max_age=max(ages_group_1) if ages_group_1 else category.max_age,
                min_grade=category.min_grade,
                max_grade=category.max_grade,
                min_weight=category.min_weight,
                max_weight=category.max_weight,
            )

            # Créer la deuxième catégorie (pour les plus jeunes/moins gradés)
            category_2 = CompetitionCategory.objects.create(
                competition=competition,
                competition_type=category.competition_type,
                name=name_category_2,
                gender=category.gender,
                min_age=min(ages_group_2) if ages_group_2 else category.min_age,
                max_age=max(ages_group_2) if ages_group_2 else category.max_age,
                min_grade=category.min_grade,
                max_grade=category.max_grade,
                min_weight=category.min_weight,
                max_weight=category.max_weight,
            )

            # Déplacer les inscriptions vers les nouvelles catégories
            for reg in group_1:
                reg.categories.add(category_1)
                reg.categories.remove(category)

            for reg in group_2:
                reg.categories.add(category_2)
                reg.categories.remove(category)

            # Supprimer l'ancienne catégorie
            old_category_name = category.name
            category.delete()

        return JsonResponse({
            'success': True,
            'message': _("Catégorie '{}' divisée avec succès ! {} pratiquant(s) dans '{}', {} pratiquant(s) dans '{}'.").format(
                old_category_name,
                len(group_1), name_category_1,
                len(group_2), name_category_2
            ),
            'category_1_id': category_1.id,
            'category_2_id': category_2.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la division de la catégorie: {}").format(str(e))
        })


def _get_grade_order(grade_name):
    """
    Convertit un nom de grade en ordre numérique pour le tri.
    Plus le grade est élevé, plus le nombre est grand.
    """
    if not grade_name:
        return 0

    grade_name_lower = grade_name.lower().strip()

    # Grades de ceintures courantes (Taekwondo, Karate, Judo, etc.)
    belt_order = {
        'blanche': 1, 'white': 1,
        'jaune': 2, 'yellow': 2,
        'orange': 3,
        'verte': 4, 'green': 4,
        'bleue': 5, 'blue': 5,
        'violette': 6, 'purple': 6,
        'marron': 7, 'brown': 7,
        'rouge': 8, 'red': 8,
        'noire': 10, 'black': 10,
    }

    # Vérifier si le grade correspond à une ceinture connue
    for belt, order in belt_order.items():
        if belt in grade_name_lower:
            return order

    # Gérer les caps/degrés (ex: "1er cap", "2ème cap")
    import re
    cap_match = re.search(r'(\d+)', grade_name_lower)
    if cap_match and ('cap' in grade_name_lower or 'dan' in grade_name_lower or 'kup' in grade_name_lower):
        num = int(cap_match.group(1))
        if 'dan' in grade_name_lower:
            return 10 + num  # Dan après ceinture noire
        elif 'kup' in grade_name_lower:
            return 10 - num  # Kup inverse (10 kup = débutant, 1 kup = avancé)
        else:
            return num

    return 5  # Valeur par défaut au milieu


@login_required
@require_POST
def remove_practitioner_from_category(request, competition_id):
    """
    Retirer un pratiquant d'une catégorie (désistement, absence, etc.)
    Le pratiquant reste inscrit à la compétition pour les autres catégories (ex: combat).
    """
    from ..models import CompetitionRegistration

    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        practitioner_id = data.get('practitioner_id')

        if not category_id or not practitioner_id:
            return JsonResponse({
                'success': False,
                'message': _("Paramètres manquants: category_id et practitioner_id requis")
            })

        # Récupérer la catégorie
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        # Récupérer l'inscription du pratiquant
        registration = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner_id=practitioner_id
        ).first()

        if not registration:
            return JsonResponse({
                'success': False,
                'message': _("Inscription non trouvée pour ce pratiquant")
            })

        # Récupérer le nom du pratiquant pour le message
        practitioner_name = registration.practitioner.full_name
        category_name = category.name

        # Retirer la catégorie de l'inscription
        if category in registration.categories.all():
            registration.categories.remove(category)

            # Vérifier s'il reste des catégories
            remaining_categories = registration.categories.count()

            return JsonResponse({
                'success': True,
                'message': _("%(name)s a été retiré(e) de la catégorie '%(category)s'.") % {
                    'name': practitioner_name,
                    'category': category_name
                },
                'remaining_categories': remaining_categories,
                'practitioner_id': practitioner_id,
                'category_id': category_id
            })
        else:
            return JsonResponse({
                'success': False,
                'message': _("Ce pratiquant n'est pas inscrit dans cette catégorie")
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Données JSON invalides")
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur: %(error)s") % {'error': str(e)}
        })