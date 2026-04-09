"""
Vue professionnelle pour la gestion complète des compétitions
Utilisée par competition_management_detail.html (nouveau template pro)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from django.db.models import Count, Q
import json

from ..models import Competition, CompetitionCategory, CompetitionRegistration, CompetitionType
from apps.grades.models import Grade


@login_required
def competition_management_pro(request, competition_id):
    """
    Vue principale pour la gestion professionnelle d'une compétition.
    Inclut toutes les fonctionnalités avancées.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # TODO: Vérifier les permissions

    # Récupérer toutes les inscriptions avec les relations nécessaires
    registrations_list = CompetitionRegistration.objects.filter(
        competition=competition
    ).select_related(
        'practitioner',
        'practitioner__organization'
    ).prefetch_related(
        'competition_types',
        'categories'
    ).order_by('-registration_date')

    # Récupérer les clubs pour les filtres
    clubs = set()
    for reg in registrations_list:
        practitioner = reg.practitioner
        # Essayer d'obtenir le club via l'organisation
        if practitioner.organization:
            # Chercher le club associé à l'organisation
            try:
                from ..models import Club
                club = Club.objects.filter(organization=practitioner.organization).first()
                if club:
                    clubs.add(club)
            except ImportError:
                pass

    # Récupérer les catégories et types de compétition
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).select_related('competition_type').annotate(
        practitioners_count=Count('registrations')
    ).order_by('assigned_tatami', 'schedule_order', 'name')

    # Organiser les catégories par tatami pour l'onglet programmation
    categories_by_tatami = {}
    unassigned_categories = []
    for cat in categories:
        if cat.assigned_tatami:
            tatami_key = cat.assigned_tatami
            if tatami_key not in categories_by_tatami:
                categories_by_tatami[tatami_key] = []
            categories_by_tatami[tatami_key].append(cat)
        else:
            unassigned_categories.append(cat)

    # Liste des tatamis existants (1 à 5 par défaut ou selon les données)
    tatami_numbers = sorted(categories_by_tatami.keys()) if categories_by_tatami else [1, 2, 3]

    # Créer un dictionnaire des catégories par type pour cette compétition spécifique
    categories_by_type = {}
    for cat in categories:
        if cat.competition_type_id:
            if cat.competition_type_id not in categories_by_type:
                categories_by_type[cat.competition_type_id] = []
            categories_by_type[cat.competition_type_id].append(cat)

    competition_types = CompetitionType.objects.filter(
        competitions=competition
    ).order_by('name')

    # Ajouter les catégories filtrées à chaque type
    for comp_type in competition_types:
        comp_type.type_categories = categories_by_type.get(comp_type.id, [])

    # Recuperer les juges pour cette competition
    # IMPORTANT: Ne recuperer QUE les juges invites/assignes a cette competition
    technical_judges = []
    combat_referees = []

    # 1. Recuperer les juges OFFICIELS via CompetitionRegistration + Judge profile
    try:
        from ..models import Judge

        # Récupérer les inscriptions marquées comme juges techniques
        tech_judge_regs = CompetitionRegistration.objects.filter(
            competition=competition,
            is_technical_judge=True
        ).select_related('practitioner', 'practitioner__organization')

        # IDs des pratiquants déjà ajoutés (pour éviter les doublons avec ad-hoc)
        seen_tech_practitioners = set()

        for reg in tech_judge_regs:
            if reg.practitioner_id in seen_tech_practitioners:
                continue
            seen_tech_practitioners.add(reg.practitioner_id)

            # Vérifier s'il a un profil Judge officiel
            judge_profile = None
            try:
                judge_profile = Judge.objects.get(practitioner=reg.practitioner, active=True)
            except (Judge.DoesNotExist, Exception):
                pass

            technical_judges.append({
                'id': reg.id,
                'practitioner': reg.practitioner,
                'practitioner_id': reg.practitioner_id,
                'name': reg.practitioner.full_name,
                'qualification_level_display': judge_profile.get_qualification_level_display() if judge_profile else _("Non qualifié"),
                'years_experience': judge_profile.years_experience if judge_profile else 0,
                'is_adhoc': False,
                'is_technical_judge': True,
                'is_combat_referee': False,
            })

        # Récupérer les inscriptions marquées comme arbitres combat
        referee_regs = CompetitionRegistration.objects.filter(
            competition=competition,
            is_combat_referee=True
        ).select_related('practitioner', 'practitioner__organization')

        seen_referee_practitioners = set()

        for reg in referee_regs:
            if reg.practitioner_id in seen_referee_practitioners:
                continue
            seen_referee_practitioners.add(reg.practitioner_id)

            judge_profile = None
            try:
                judge_profile = Judge.objects.get(practitioner=reg.practitioner, active=True)
            except (Judge.DoesNotExist, Exception):
                pass

            combat_referees.append({
                'id': reg.id,
                'practitioner': reg.practitioner,
                'practitioner_id': reg.practitioner_id,
                'name': reg.practitioner.full_name,
                'qualification_level_display': judge_profile.get_qualification_level_display() if judge_profile else _("Non qualifié"),
                'is_adhoc': False,
            })

    except (ImportError, Exception) as e:
        pass  # Judge model not available

    # 2. Récupérer les juges AD-HOC (créés spécifiquement pour cette compétition)
    # Utiliser les sets de practitioner IDs déjà vus pour éviter les doublons
    try:
        seen_tech_practitioners
    except NameError:
        seen_tech_practitioners = set()
    try:
        seen_referee_practitioners
    except NameError:
        seen_referee_practitioners = set()

    try:
        from ..models import AdHocJudge
        if AdHocJudge is not None:
            # Juges techniques ad-hoc actifs
            adhoc_tech_judges = AdHocJudge.objects.filter(
                competition=competition,
                judge_type='technical_judge',
                status='active'
            ).select_related('practitioner', 'practitioner__organization')

            for adhoc in adhoc_tech_judges:
                if adhoc.practitioner_id in seen_tech_practitioners:
                    continue
                seen_tech_practitioners.add(adhoc.practitioner_id)
                technical_judges.append({
                    'id': adhoc.id,
                    'practitioner': adhoc.practitioner,
                    'practitioner_id': adhoc.practitioner_id,
                    'name': adhoc.practitioner.full_name,
                    'qualification_level_display': adhoc.get_experience_level_display(),
                    'years_experience': 0,  # Ad-hoc, pas d'expérience officielle
                    'is_adhoc': True,
                })

            # Arbitres ad-hoc actifs
            adhoc_referees = AdHocJudge.objects.filter(
                competition=competition,
                judge_type__in=['combat_referee', 'assistant_referee'],
                status='active'
            ).select_related('practitioner', 'practitioner__organization')

            for adhoc in adhoc_referees:
                if adhoc.practitioner_id in seen_referee_practitioners:
                    continue
                seen_referee_practitioners.add(adhoc.practitioner_id)
                combat_referees.append({
                    'id': adhoc.id,
                    'practitioner': adhoc.practitioner,
                    'practitioner_id': adhoc.practitioner_id,
                    'name': adhoc.practitioner.full_name,
                    'qualification_level_display': adhoc.get_experience_level_display(),
                    'is_adhoc': True,
                })
    except (ImportError, Exception) as e:
        pass  # AdHocJudge n'est pas disponible

    # Récupérer les grades disponibles pour les filtres (liés à la discipline)
    try:
        if competition.discipline:
            available_grades = Grade.objects.filter(
                discipline=competition.discipline
            ).order_by('level', 'order', 'name')
        else:
            available_grades = Grade.objects.none()
    except Exception:
        available_grades = Grade.objects.none()

    # Générer l'URL publique de la compétition
    from django.urls import reverse
    try:
        competition_public_url = request.build_absolute_uri(
            reverse('competitions:competitions:detail', kwargs={'pk': competition.id})
        )
    except Exception:
        competition_public_url = request.build_absolute_uri(
            f'/{request.LANGUAGE_CODE}/competitions/competitions/{competition.id}/'
        )

    # Lien d'inscription directe pour les responsables de clubs
    try:
        competition_registration_url = request.build_absolute_uri(
            reverse('competitions:club:competition_registration_form', kwargs={'competition_id': competition.id})
        )
    except Exception:
        competition_registration_url = request.build_absolute_uri(
            f'/{request.LANGUAGE_CODE}/competitions/club/competition-registration/{competition.id}/'
        )

    context = {
        'competition': competition,
        'registrations_list': registrations_list,
        'registrations_count': registrations_list.count(),
        'clubs': list(clubs),
        'categories': categories,
        'competition_types': competition_types,
        'competition_types_count': competition_types.count(),
        'registrations_exists': registrations_list.exists(),
        'technical_judges': technical_judges,
        'combat_referees': combat_referees,
        'competition_public_url': competition_public_url,
        'competition_registration_url': competition_registration_url,
        # Données pour l'onglet Programmation
        'categories_by_tatami': categories_by_tatami,
        'unassigned_categories': unassigned_categories,
        'tatami_numbers': tatami_numbers,
        # Données pour les filtres de pratiquants
        'available_grades': available_grades,
    }

    return render(request, 'competitions/club/competition_management_pro.html', context)


@login_required
@require_POST
def add_competition_type(request, competition_id):
    """Ajouter un type de compétition"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)

        # Créer le type de compétition avec la discipline de la compétition
        comp_type = CompetitionType.objects.create(
            name=data.get('name'),
            description=data.get('description', ''),
            discipline=competition.discipline,
            scoring_system=data.get('rules', 'technical')  # 'rules' du frontend -> 'scoring_system' du modèle
        )

        # L'associer à la compétition
        competition.competition_types.add(comp_type)

        return JsonResponse({
            'success': True,
            'message': _("Type de compétition créé avec succès"),
            'type_id': comp_type.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def delete_competition_type(request, competition_id, type_id):
    """Supprimer un type de compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        comp_type = get_object_or_404(CompetitionType, id=type_id)
        
        # Vérifier que le type est associé à cette compétition
        if competition not in comp_type.competitions.all():
            return JsonResponse({
                'success': False,
                'message': _("Ce type de compétition n'est pas associé à cette compétition")
            })
        
        # Supprimer l'association
        competition.competition_types.remove(comp_type)
        
        # Si le type n'est plus utilisé ailleurs, on peut le supprimer
        # (optionnel, selon les besoins métier)
        # comp_type.delete()
        
        return JsonResponse({
            'success': True,
            'message': _("Type de compétition supprimé avec succès")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def update_competition_type(request, competition_id, type_id):
    """Mettre à jour un type de compétition"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        comp_type = get_object_or_404(CompetitionType, id=type_id)

        # Vérifier que le type est associé à cette compétition
        if competition not in comp_type.competitions.all():
            return JsonResponse({
                'success': False,
                'message': _("Ce type de compétition n'est pas associé à cette compétition")
            })

        data = json.loads(request.body)

        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({
                'success': False,
                'message': _("Le nom du type est requis.")
            })

        comp_type.name = name
        comp_type.description = data.get('description', '')
        comp_type.scoring_system = data.get('rules', comp_type.scoring_system)
        comp_type.save()

        return JsonResponse({
            'success': True,
            'message': _("Type de compétition '{}' mis à jour avec succès").format(comp_type.name)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def assign_to_category(request, competition_id):
    """Assigner un pratiquant à une catégorie par drag & drop"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        category_id = data.get('category_id')
        
        registration = get_object_or_404(
            CompetitionRegistration,
            id=registration_id,
            competition=competition
        )
        category = get_object_or_404(
            CompetitionCategory,
            id=category_id,
            competition=competition
        )
        
        # Si déjà dans une catégorie du même type, retirer l'ancienne (déplacement)
        if category.competition_type:
            existing_categories = registration.categories.filter(
                competition_type=category.competition_type
            )
            if existing_categories.exists():
                registration.categories.remove(*existing_categories)

        # Assigner à la catégorie
        registration.categories.add(category)
        
        return JsonResponse({
            'success': True,
            'message': _("Pratiquant affecté avec succès"),
            'practitioner_name': registration.practitioner.get_full_name(),
            'category_name': category.name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def remove_from_category(request, competition_id):
    """Retirer un pratiquant d'une catégorie"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        category_id = data.get('category_id')
        
        registration = get_object_or_404(
            CompetitionRegistration,
            id=registration_id,
            competition=competition
        )
        category = get_object_or_404(
            CompetitionCategory,
            id=category_id,
            competition=competition
        )
        
        registration.categories.remove(category)
        
        return JsonResponse({
            'success': True,
            'message': _("Pratiquant retiré de la catégorie")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def publish_competition(request, competition_id):
    """Publier une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier que la méthode est POST
    if request.method != 'POST':
        # Si c'est une requête AJAX, retourner JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _("Cette action nécessite une requête POST.")
            }, status=405)
        # Sinon, rediriger vers la page de gestion avec un message
        messages.error(request, _("Cette action doit être effectuée via le bouton de publication sur la page de gestion."))
        return redirect('competitions:club:competition_management_detail', competition_id=competition_id)
    
    try:
        # Vérifications avant publication
        if not competition.venue_name:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez définir le lieu de la compétition avant de publier")
            })
        
        if not competition.categories.exists():
            return JsonResponse({
                'success': False,
                'message': _("Veuillez créer au moins une catégorie avant de publier")
            })
        
        # Publier
        competition.is_published = True
        competition.save()
        
        # TODO: Envoyer des notifications aux clubs
        
        return JsonResponse({
            'success': True,
            'message': _("Compétition publiée avec succès !")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def update_visibility_option(request, competition_id):
    """Mettre à jour une option de visibilité de la compétition"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        import json
        data = json.loads(request.body)
        option = data.get('option')
        value = data.get('value')

        allowed_options = ['allow_online_registration', 'show_participants_list', 'live_results']
        if option not in allowed_options:
            return JsonResponse({'success': False, 'message': _("Option invalide.")})

        setattr(competition, option, bool(value))
        competition.save(update_fields=[option])

        return JsonResponse({
            'success': True,
            'message': _("Option mise à jour")
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def assign_judge(request, competition_id):
    """Assigner un juge à une zone/rôle"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        judge_id = data.get('judge_id')
        zone = data.get('zone')
        role = data.get('role')
        
        # TODO: Implémenter l'assignation des juges
        
        return JsonResponse({
            'success': True,
            'message': _("Juge affecté avec succès")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_competition_stats(request, competition_id):
    """Obtenir les statistiques de la compétition en temps réel"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    stats = {
        'practitioners': competition.registrations.count(),
        'categories': competition.categories.count(),
        'judges': 0,  # TODO: Implémenter le compte des juges
        'types': competition.competition_types.count(),
        'unassigned': competition.registrations.filter(categories__isnull=True).count(),
        'by_category': {}
    }
    
    # Statistiques par catégorie
    for category in competition.categories.all():
        stats['by_category'][category.id] = {
            'name': category.name,
            'count': category.registrations.count()
        }
    
    return JsonResponse(stats)


@login_required
def get_competition_types_api(request, competition_id):
    """API pour récupérer les types de compétition avec leurs catégories"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer les types de compétition associés à cette compétition
        competition_types = CompetitionType.objects.filter(
            competitions=competition
        ).prefetch_related('categories').order_by('name')
        
        types_data = []
        for comp_type in competition_types:
            # Récupérer les catégories liées à ce type pour cette compétition
            categories = CompetitionCategory.objects.filter(
                competition=competition,
                competition_type=comp_type
            ).annotate(
                registrations_count=Count('registrations')
            )
            
            types_data.append({
                'id': comp_type.id,
                'name': comp_type.name,
                'description': comp_type.description or '',
                'scoring_system': comp_type.scoring_system or 'custom',
                'categories_count': categories.count(),
                'categories': [
                    {
                        'id': cat.id,
                        'name': cat.name,
                        'registrations_count': cat.registrations_count
                    }
                    for cat in categories
                ],
                'created_at': comp_type.created_at.isoformat() if hasattr(comp_type, 'created_at') else None
            })
        
        return JsonResponse({
            'success': True,
            'types': types_data,
            'count': len(types_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def get_competition_categories_api(request, competition_id):
    """API pour récupérer les catégories avec leurs inscrits"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer les catégories avec les inscrits
        categories = CompetitionCategory.objects.filter(
            competition=competition
        ).select_related('competition_type').prefetch_related(
            'registrations__practitioner',
            'registrations__practitioner__organization'
        ).annotate(
            registrations_count=Count('registrations')
        ).order_by('name')
        
        categories_data = []
        for category in categories:
            # Récupérer les inscrits de cette catégorie
            registrations = category.registrations.all()
            
            registrations_data = []
            for reg in registrations:
                practitioner = reg.practitioner
                registrations_data.append({
                    'id': reg.id,
                    'practitioner_id': practitioner.id,
                    'practitioner_name': practitioner.get_full_name(),
                    'club_name': practitioner.organization.name if practitioner.organization else '-',
                    'license_number': practitioner.license_number or '-',
                    'date_of_birth': practitioner.birth_date.isoformat() if practitioner.birth_date else None,
                    'gender': practitioner.gender,
                    'registration_date': reg.registration_date.isoformat() if hasattr(reg, 'registration_date') else None
                })
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': getattr(category, 'description', '') or '',
                'competition_type': {
                    'id': category.competition_type.id,
                    'name': category.competition_type.name
                } if category.competition_type else None,
                'gender': category.gender,
                'min_age': category.min_age,
                'max_age': category.max_age,
                'min_weight': float(category.min_weight) if category.min_weight else None,
                'max_weight': float(category.max_weight) if category.max_weight else None,
                'registrations_count': registrations.count(),
                'registrations': registrations_data,
                # Champs de planning pour restaurer les assignations
                'assigned_tatami': category.assigned_tatami,
                'schedule_order': category.schedule_order,
                'estimated_start_time': category.estimated_start_time.strftime('%H:%M') if category.estimated_start_time else None,
                'estimated_duration': category.estimated_duration,
                'is_completed': getattr(category, 'is_completed', False)
            })

        return JsonResponse({
            'success': True,
            'categories': categories_data,
            'count': len(categories_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def get_scoring_stats_api(request, competition_id):
    """
    API pour récupérer les statistiques de scoring d'une compétition.
    Retourne le nombre de performances non notées, en cours et terminées.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        # Essayer d'importer les modèles de scoring
        try:
            from ..models import Performance

            # Compter les performances par statut
            performances = Performance.objects.filter(
                category__competition=competition
            )

            not_scored = performances.filter(
                Q(status='pending') | Q(status='not_started')
            ).count()

            in_progress = performances.filter(
                status='in_progress'
            ).count()

            completed = performances.filter(
                Q(status='completed') | Q(status='scored')
            ).count()

        except (ImportError, AttributeError):
            # Si le modèle Performance n'existe pas, calculer à partir des inscriptions
            registrations = CompetitionRegistration.objects.filter(
                competition=competition
            )

            # Estimation basée sur les inscriptions
            total = registrations.count()
            not_scored = total  # Par défaut, tout est non noté
            in_progress = 0
            completed = 0

        return JsonResponse({
            'success': True,
            'not_scored': not_scored,
            'in_progress': in_progress,
            'completed': completed,
            'total': not_scored + in_progress + completed
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'not_scored': 0,
            'in_progress': 0,
            'completed': 0
        }, status=500)


@login_required
def search_users_api(request, competition_id):
    """
    API pour rechercher des utilisateurs (juges/arbitres potentiels).
    Recherche par nom, email ou licence.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    query = request.GET.get('q', '').strip()
    role_type = request.GET.get('role', 'judge')  # 'judge' ou 'referee'

    if len(query) < 2:
        return JsonResponse({
            'success': True,
            'users': [],
            'message': _("Veuillez saisir au moins 2 caractères")
        })

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Rechercher les utilisateurs par nom ou email
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(username__icontains=query)
    ).filter(is_active=True)[:20]

    users_data = []
    for user in users:
        # Essayer de récupérer les infos du pratiquant associé
        practitioner = None
        judge_info = None
        try:
            from ..models import Practitioner, Judge
            practitioner = Practitioner.objects.filter(user=user).first()

            # Récupérer les informations de juge si le pratiquant est qualifié
            if practitioner:
                try:
                    judge = Judge.objects.get(practitioner=practitioner, active=True)
                    judge_info = {
                        'is_technical_judge': judge.is_technical_judge,
                        'is_combat_referee': judge.is_combat_referee,
                        'qualification_level': judge.qualification_level,
                        'qualification_level_display': judge.get_qualification_level_display(),
                        'years_experience': judge.years_experience,
                    }
                except Judge.DoesNotExist:
                    pass
        except:
            pass

        # Construire l'info pratiquant
        practitioner_info = None
        if practitioner:
            info_parts = []
            if practitioner.organization:
                info_parts.append(practitioner.organization.name)
            if hasattr(practitioner, 'current_grade') and practitioner.current_grade:
                info_parts.append(str(practitioner.current_grade))
            if info_parts:
                practitioner_info = ' - '.join(info_parts)

        users_data.append({
            'id': user.id,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'username': user.username,
            'has_practitioner': practitioner is not None,
            'practitioner_info': practitioner_info,
            'grade': str(practitioner.current_grade) if practitioner and hasattr(practitioner, 'current_grade') and practitioner.current_grade else None,
            'club': practitioner.organization.name if practitioner and practitioner.organization else None,
            'judge_info': judge_info,  # Informations de qualification de juge
            'is_qualified_judge': judge_info is not None,
        })

    return JsonResponse({
        'success': True,
        'users': users_data,
        'count': len(users_data)
    })


@login_required
@require_POST
def add_judge_to_competition(request, competition_id):
    """
    Ajouter un juge/arbitre à la compétition.
    Crée ou met à jour le CompetitionRegistration avec les flags appropriés.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        role = data.get('role', 'technical')  # 'judge' ou 'referee'
        qualification = data.get('qualification', '')

        if not user_id:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez sélectionner un utilisateur")
            }, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = get_object_or_404(User, id=user_id)

        # Trouver le pratiquant associé à cet utilisateur
        from ..models import Practitioner
        practitioner = Practitioner.objects.filter(user=user).first()
        if not practitioner:
            return JsonResponse({
                'success': False,
                'message': _("Cet utilisateur n'a pas de profil pratiquant associé")
            }, status=400)

        # Créer ou récupérer l'inscription à la compétition
        registration, created = CompetitionRegistration.objects.get_or_create(
            competition=competition,
            practitioner=practitioner,
            defaults={
                'is_competitor': False,
                'is_technical_judge': (role in ('judge', 'technical', 'chief')),
                'is_combat_referee': (role in ('referee', 'central', 'corner', 'table', 'placator')),
            }
        )

        # Si l'inscription existait déjà, mettre à jour les flags
        if not created:
            if role in ('judge', 'technical', 'chief'):
                registration.is_technical_judge = True
            elif role in ('referee', 'central', 'corner', 'table', 'placator'):
                registration.is_combat_referee = True
            registration.save()

        judge_name = practitioner.full_name

        return JsonResponse({
            'success': True,
            'message': _("%(name)s ajouté comme %(role)s") % {
                'name': judge_name,
                'role': _("juge technique") if role in ('judge', 'technical', 'chief') else _("arbitre")
            },
            'judge': {
                'id': registration.id,
                'name': judge_name,
                'role': role,
                'qualification': qualification
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
