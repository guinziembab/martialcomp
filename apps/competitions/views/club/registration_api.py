"""
API views for competition registration
"""
import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Prefetch
from django.views.decorators.http import require_POST, require_http_methods

from apps.competitions.models import (
    Competition, CompetitionType, CompetitionCategory,
    CompetitionRegistration, Practitioner
)
from apps.competitions.models.combat import Equipe, MembreEquipe
from apps.competitions.utils.permission_helpers import get_user_club

import logging
logger = logging.getLogger(__name__)


@login_required
def get_categories_by_type_api(request, competition_id, type_id):
    """API endpoint pour récupérer les catégories d'un type de compétition."""
    try:
        # Vérifier que l'utilisateur a un club
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': 'Unauthorized'
            }, status=403)
        
        # Récupérer la compétition
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Récupérer le type de compétition
        competition_type = get_object_or_404(CompetitionType, id=type_id)
        
        # Vérifier que le type appartient bien à cette compétition
        if not competition.competition_types.filter(id=type_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Type not found in competition'
            }, status=404)
        
        # Récupérer les catégories pour ce type
        categories = CompetitionCategory.objects.filter(
            competition=competition,
            competition_type=competition_type
        ).order_by('min_age', 'name')
        
        # Compter les inscriptions par catégorie
        categories_data = []
        
        for category in categories:
            # Compter le nombre d'inscriptions dans cette catégorie
            registrations_count = CompetitionRegistration.objects.filter(
                competition=competition,
                categories=category
            ).count()
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender,
                'min_age': category.min_age,
                'max_age': category.max_age,
                'min_weight': category.min_weight,
                'max_weight': category.max_weight,
                'registrations_count': registrations_count
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data,
            'total': len(categories_data)
        })
        
    except Exception as e:
        logger.error(_("Erreur API catégories: {}").format(str(e)), exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_category_registrations_api(request, competition_id, category_id):
    """API endpoint pour récupérer les inscriptions d'une catégorie."""
    try:
        # Récupérer la compétition et la catégorie
        competition = get_object_or_404(Competition, id=competition_id)
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

        # Récupérer toutes les inscriptions pour cette catégorie
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            categories=category
        ).select_related('practitioner', 'practitioner__organization')

        registrations_data = []
        for reg in registrations:
            practitioner = reg.practitioner
            # Récupérer le club du pratiquant
            club_name = ''
            club_id = None
            if practitioner.organization:
                club_name = practitioner.organization.name
                # Essayer de récupérer l'ID du club associé
                if hasattr(practitioner.organization, 'club') and practitioner.organization.club:
                    club_id = practitioner.organization.club.id
                elif hasattr(practitioner.organization, 'old_club_id'):
                    club_id = practitioner.organization.old_club_id

            registrations_data.append({
                'id': reg.id,
                'practitioner_id': practitioner.id,
                'practitioner_name': f"{practitioner.first_name} {practitioner.last_name}",
                'club_name': club_name,
                'club_id': club_id,
                'registered_at': reg.registration_date.strftime('%Y-%m-%d %H:%M') if reg.registration_date else None
            })

        return JsonResponse({
            'success': True,
            'registrations': registrations_data,
            'total': len(registrations_data)
        })

    except Exception as e:
        logger.error(f"Erreur API inscriptions catégorie: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def competition_registration_simple(request, competition_id):
    """Version simplifiée du formulaire d'inscription pour les clubs."""
    club = get_user_club(request)
    if not club:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:index')
    
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)

    # Si pas d'organisation trouvée, essayer de la trouver via old_club_id
    if not club_organization:
        try:
            from apps.organizations.models import Organization
            club_organization = Organization.objects.filter(old_club_id=club.id).first()
            logger.info(f"[DEBUG] Found organization via old_club_id: {club_organization}")
        except Exception as e:
            logger.error(f"[DEBUG] Error finding organization via old_club_id: {e}")

    if not club_organization:
        from django.contrib import messages
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        practitioners = Practitioner.objects.none()
    else:
        # Récupérer tous les pratiquants du club avec leurs grades actuels
        practitioners = Practitioner.objects.filter(
            organization=club_organization
        ).select_related('grade').order_by('last_name', 'first_name')

        # Note: L'âge est calculé automatiquement via la propriété @property du modèle Practitioner
        # Pas besoin de le définir manuellement
    
    # Récupérer les IDs des pratiquants du club (pour filtrage)
    club_practitioner_ids = list(practitioners.values_list('id', flat=True)) if practitioners.exists() else []

    # Récupérer les inscriptions existantes avec leurs catégories et types
    # Utiliser la liste des pratiquants du club au lieu de filtrer par organization
    # Cela permet de récupérer les inscriptions même si l'organization n'est pas bien définie
    existing_registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        practitioner_id__in=club_practitioner_ids
    ).prefetch_related('competition_types', 'categories').select_related('practitioner')

    # Créer un dictionnaire structuré des pratiquants déjà inscrits
    registered_practitioners = {}
    for reg in existing_registrations:
        if reg.practitioner_id not in registered_practitioners:
            registered_practitioners[reg.practitioner_id] = {
                'registration': reg,
                'types': list(reg.competition_types.all()),
                'categories': list(reg.categories.all())
            }
    
    # Compter le total d'inscriptions pour cette compétition
    total_competition_registrations = CompetitionRegistration.objects.filter(
        competition=competition
    ).count()
    
    # Compter les inscriptions du club
    club_registrations_count = len(registered_practitioners)
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Traiter l'inscription via AJAX
        competition_type_id = request.POST.get('competition_type_id')
        category_id = request.POST.get('category_id')
        practitioner_ids = request.POST.getlist('practitioner_ids[]')
        
        if not all([competition_type_id, category_id, practitioner_ids]):
            return JsonResponse({
                'success': False,
                'message': _("Veuillez remplir tous les champs obligatoires.")
            }, status=400)
        
        try:
            competition_type = CompetitionType.objects.get(id=competition_type_id)
            category = CompetitionCategory.objects.get(id=category_id)
            
            success_count = 0
            already_registered = 0
            
            for practitioner_id in practitioner_ids:
                practitioner = Practitioner.objects.get(
                    id=practitioner_id, 
                    organization=club_organization
                )
                
                # Vérifier ou créer l'inscription
                registration, created = CompetitionRegistration.objects.get_or_create(
                    competition=competition,
                    practitioner=practitioner,
                    defaults={
                        'registration_date': timezone.now(),
                        'status': 'pending'
                    }
                )
                
                # Ajouter le type et la catégorie
                if competition_type not in registration.competition_types.all():
                    registration.competition_types.add(competition_type)
                
                if category not in registration.categories.all():
                    registration.categories.add(category)
                    success_count += 1
                else:
                    already_registered += 1
            
            message = _("{} pratiquant(s) inscrit(s) avec succès.").format(success_count)
            if already_registered > 0:
                message += " " + _("{} déjà inscrit(s) dans cette catégorie.").format(already_registered)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'registered_count': success_count
            })
            
        except Exception as e:
            logger.error(_("Erreur inscription simple: {}").format(str(e)), exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    # Pour les requêtes GET, retourner le template
    from django.shortcuts import render
    from collections import defaultdict

    # === DEBUG: Logging pour diagnostiquer le problème ===
    logger.info(f"[DEBUG TEAM MODAL] User: {request.user.username}")
    logger.info(f"[DEBUG TEAM MODAL] Club: {club} (ID: {club.id if club else 'None'})")
    logger.info(f"[DEBUG TEAM MODAL] Club Organization: {club_organization} (ID: {club_organization.id if club_organization else 'None'})")
    logger.info(f"[DEBUG TEAM MODAL] Practitioners count: {practitioners.count() if practitioners else 0}")
    logger.info(f"[DEBUG TEAM MODAL] Club practitioner IDs: {club_practitioner_ids[:10]}...")  # Premier 10
    logger.info(f"[DEBUG TEAM MODAL] Existing registrations count: {existing_registrations.count()}")

    # Afficher les registrations avec leurs catégories
    for reg in existing_registrations[:5]:  # Premier 5
        cats = list(reg.categories.all())
        logger.info(f"[DEBUG TEAM MODAL] Registration: {reg.practitioner} - Categories: {cats}")

    # === Préparer les pratiquants inscrits regroupés par catégorie pour la création d'équipes ===
    registered_by_category = defaultdict(list)
    registered_practitioners_list = []  # Liste des pratiquants déjà inscrits à la compétition

    for reg in existing_registrations:
        practitioner = reg.practitioner
        # Ajouter à la liste globale des inscrits (éviter les doublons)
        if practitioner not in registered_practitioners_list:
            registered_practitioners_list.append(practitioner)

        # Regrouper par catégorie
        for cat in reg.categories.all():
            # Éviter les doublons dans la même catégorie
            practitioner_ids = [p['id'] for p in registered_by_category[cat.id]]
            if practitioner.id not in practitioner_ids:
                registered_by_category[cat.id].append({
                    'id': practitioner.id,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'full_name': f"{practitioner.first_name} {practitioner.last_name}",
                    'grade': str(practitioner.grade) if practitioner.grade else None,
                })

    # Récupérer les catégories de la compétition avec les inscrits
    categories_with_practitioners = []
    competition_categories = CompetitionCategory.objects.filter(
        competition=competition
    ).select_related('competition_type').order_by('competition_type__name', 'name')

    for cat in competition_categories:
        cat_practitioners = registered_by_category.get(cat.id, [])
        if cat_practitioners:  # N'afficher que les catégories avec des inscrits
            categories_with_practitioners.append({
                'id': cat.id,
                'name': cat.name,
                'type_name': cat.competition_type.name if cat.competition_type else '',
                'gender': cat.get_gender_display() if hasattr(cat, 'get_gender_display') else cat.gender,
                'practitioners': cat_practitioners,
                'count': len(cat_practitioners)
            })

    # === DEBUG: Logging final ===
    logger.info(f"[DEBUG TEAM MODAL] registered_practitioners_list count: {len(registered_practitioners_list)}")
    logger.info(f"[DEBUG TEAM MODAL] categories_with_practitioners count: {len(categories_with_practitioners)}")
    logger.info(f"[DEBUG TEAM MODAL] registered_by_category keys: {list(registered_by_category.keys())}")

    # === Préparer les équipes regroupées par catégorie pour les pools ===
    # Les équipes sont créées pour une compétition
    # Pour déterminer les catégories des équipes, on regarde les catégories des membres inscrits

    from collections import defaultdict
    all_competition_teams = Equipe.objects.filter(
        competition=competition,
        status__in=['active', 'fusion_complete']
    ).prefetch_related(
        'memberships__pratiquant',
        'club'
    ).order_by('nom')

    # Pour chaque équipe, déterminer ses catégories (basé sur les inscriptions des membres)
    teams_by_category = defaultdict(list)

    for equipe in all_competition_teams:
        # Récupérer les IDs des membres de l'équipe
        member_ids = list(equipe.memberships.values_list('pratiquant_id', flat=True))

        if member_ids:
            # Trouver les catégories où les membres sont inscrits
            member_registrations = CompetitionRegistration.objects.filter(
                competition=competition,
                practitioner_id__in=member_ids
            ).prefetch_related('categories')

            # Collecter les catégories de tous les membres
            team_categories = set()
            for reg in member_registrations:
                for cat in reg.categories.all():
                    team_categories.add(cat.id)

            # Ajouter l'équipe à chaque catégorie
            titulaires_count = equipe.memberships.filter(est_remplacant=False).count()
            remplacants_count = equipe.memberships.filter(est_remplacant=True).count()
            min_membres = getattr(equipe, 'min_membres', 3)

            # Récupérer les membres de l'équipe
            membres_list = []
            for membre in equipe.memberships.all().select_related('pratiquant', 'pratiquant__grade').order_by('est_remplacant', 'ordre'):
                pratiquant = membre.pratiquant
                # Récupérer le grade de manière sécurisée (éviter l'erreur si discipline n'existe pas)
                grade_str = None
                if pratiquant.grade:
                    try:
                        grade_str = str(pratiquant.grade)
                    except Exception:
                        # Si la discipline associée n'existe plus, utiliser juste le nom du grade
                        grade_str = getattr(pratiquant.grade, 'name', None)
                membres_list.append({
                    'id': pratiquant.id,
                    'first_name': pratiquant.first_name,
                    'last_name': pratiquant.last_name,
                    'full_name': f"{pratiquant.first_name} {pratiquant.last_name}",
                    'grade': grade_str,
                    'is_substitute': membre.est_remplacant,
                    'ordre': membre.ordre,
                })

            # Logo du club
            club_logo_url = None
            if equipe.club and equipe.club.logo:
                club_logo_url = equipe.club.logo.url

            team_info = {
                'id': equipe.id,
                'name': equipe.nom,
                'club_name': equipe.club.name if equipe.club else 'N/A',
                'club_id': equipe.club.id if equipe.club else None,
                'club_logo_url': club_logo_url,
                'titulaires_count': titulaires_count,
                'remplacants_count': remplacants_count,
                'total_count': titulaires_count + remplacants_count,
                'min_membres': min_membres,
                'is_complete': titulaires_count >= min_membres,
                'status': getattr(equipe, 'status', 'active'),
                'type_equipe': getattr(equipe, 'type_equipe', 'mono_club'),
                'membres': membres_list,
            }

            for cat_id in team_categories:
                teams_by_category[cat_id].append(team_info)

    # Créer la liste des catégories avec leurs équipes pour le template
    # Filtrer les catégories individuelles (Quyen Individuel, etc.) qui ne sont pas pour les pools
    INDIVIDUAL_TYPE_KEYWORDS = ['individuel', 'individual', 'quyen', 'quyền', 'solo', 'poomsae']

    categories_with_teams = []
    categories_without_teams = []  # Catégories sans équipes (pour permettre de les masquer/annuler)

    for cat in competition_categories:
        cat_teams = teams_by_category.get(cat.id, [])
        type_name = cat.competition_type.name.lower() if cat.competition_type else ''

        # Vérifier si c'est une catégorie individuelle (à exclure des pools)
        is_individual = any(keyword in type_name for keyword in INDIVIDUAL_TYPE_KEYWORDS)

        category_data = {
            'id': cat.id,
            'name': cat.name,
            'type_id': cat.competition_type.id if cat.competition_type else 0,
            'type_name': cat.competition_type.name if cat.competition_type else '',
            'gender': cat.get_gender_display() if hasattr(cat, 'get_gender_display') else cat.gender,
            'teams': cat_teams,
            'teams_count': len(cat_teams),
            'is_individual': is_individual,
            # Calcul des pools suggérés (2-4 équipes par pool)
            'suggested_pools': max(1, (len(cat_teams) + 3) // 4) if cat_teams else 0,
        }

        # Ne pas inclure les catégories individuelles dans les pools
        if not is_individual:
            if cat_teams:
                categories_with_teams.append(category_data)
            else:
                categories_without_teams.append(category_data)

    # Compter le total des équipes (toutes confondues, éviter les doublons)
    total_teams_count = all_competition_teams.count()

    # Liste complète des catégories (pour le sélecteur de catégorie dans la création d'équipe)
    competition_categories_list = [
        {
            'id': cat.id,
            'name': cat.name,
            'type_name': cat.competition_type.name if cat.competition_type else '',
        }
        for cat in competition_categories
    ]

    context = {
        'competition': competition,
        'practitioners': practitioners,
        'registered_practitioners': registered_practitioners,
        'registered_practitioners_list': registered_practitioners_list,  # Pour la création d'équipe
        'categories_with_practitioners': categories_with_practitioners,  # Regroupés par catégorie
        'competition_categories_list': competition_categories_list,  # Toutes les catégories pour le sélecteur
        'categories_with_teams': categories_with_teams,  # Équipes regroupées par catégorie pour les pools
        'categories_without_teams': categories_without_teams,  # Catégories sans équipes (combat)
        'total_teams_count': total_teams_count,
        'club': club,
        'total_competition_registrations': total_competition_registrations,
        'club_registrations_count': club_registrations_count
    }

    return render(request, 'competitions/club/competition_registration_simple.html', context)


@login_required
@require_POST
def unregister_practitioner(request, competition_id):
    """Désinscrire un pratiquant d'une catégorie spécifique."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, _("Requête invalide."))
        return redirect('competitions:club:competition_registration_simple', competition_id=competition_id)
    
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)
        
        club_organization = club.organization or getattr(club, 'as_organization', None)
        if not club_organization:
            return JsonResponse({
                'success': False,
                'message': _("Aucune organisation associée trouvée pour ce club.")
            }, status=400)
        
        practitioner_id = request.POST.get('practitioner_id')
        category_id = request.POST.get('category_id')
        
        if not practitioner_id or not category_id:
            return JsonResponse({
                'success': False,
                'message': _("Données manquantes.")
            }, status=400)
        
        # Récupérer l'inscription
        competition = get_object_or_404(Competition, id=competition_id)
        registration = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner_id=practitioner_id,
            practitioner__organization=club_organization
        ).first()
        
        if not registration:
            return JsonResponse({
                'success': False,
                'message': _("Inscription non trouvée.")
            }, status=404)
        
        # Retirer la catégorie
        category = get_object_or_404(CompetitionCategory, id=category_id)
        registration.categories.remove(category)
        
        # Si plus aucune catégorie, supprimer l'inscription
        if not registration.categories.exists() and not registration.competition_types.exists():
            registration.delete()
            message = _("Pratiquant désinscrit complètement de la compétition.")
        else:
            message = _("Pratiquant désinscrit de la catégorie avec succès.")
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(_("Erreur désinscription: {}").format(str(e)), exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def available_competitions_api(request):
    """API endpoint pour récupérer les compétitions disponibles en JSON."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': 'Unauthorized',
                'competitions': []
            }, status=403)
        
        club_organization = club.organization or getattr(club, 'as_organization', None)
        if not club_organization:
            return JsonResponse({
                'success': False,
                'error': 'No organization',
                'competitions': []
            }, status=400)
        
        # Récupérer les compétitions à venir
        now = timezone.now().date()
        competitions = Competition.objects.filter(
            end_date__gte=now,
            status__in=['published', 'open']
        ).order_by('start_date')
        
        # Appliquer le filtrage par discipline si disponible
        try:
            from apps.competitions.utils.discipline_filtering import filter_queryset_by_discipline_federation
            competitions = filter_queryset_by_discipline_federation(competitions, request.user)
        except ImportError:
            pass
        
        # Formater les données pour le JavaScript
        competitions_data = []
        for comp in competitions[:50]:  # Limiter à 50 compétitions
            competitions_data.append({
                'id': comp.id,
                'name': comp.title,  # Utiliser title au lieu de name
                'date': comp.start_date.strftime('%d/%m/%Y') if comp.start_date else '',
                'location': comp.venue_name or comp.city or '',  # Utiliser venue_name au lieu de location
                'registration_deadline': comp.registration_deadline.strftime('%d/%m/%Y') if comp.registration_deadline else '',
                'status': comp.status
            })
        
        return JsonResponse({
            'success': True,
            'competitions': competitions_data
        })
        
    except Exception as e:
        logger.error(_("Erreur API compétitions disponibles: {}").format(str(e)), exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'competitions': []
        }, status=500)


@login_required
@require_POST
def bulk_registration_process(request):
    """API endpoint pour l'inscription en masse via JSON."""
    if request.headers.get('Content-Type') != 'application/json':
        return JsonResponse({
            'success': False,
            'message': _("Content-Type doit être application/json")
        }, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)
        
        club_organization = club.organization or getattr(club, 'as_organization', None)
        if not club_organization:
            return JsonResponse({
                'success': False,
                'message': _("Aucune organisation associée trouvée pour ce club.")
            }, status=400)
        
        competition_id = data.get('competition_id')
        practitioner_ids = data.get('practitioner_ids', [])
        
        if not competition_id or not practitioner_ids:
            return JsonResponse({
                'success': False,
                'message': _("Données manquantes.")
            }, status=400)
        
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Récupérer les types de compétition (optionnel)
        competition_types = competition.competition_types.all()
        competition_type_ids = data.get('competition_type_ids', [])
        if not competition_type_ids and competition_types.exists():
            # Prendre le premier type par défaut
            competition_type_ids = [competition_types.first().id]
        
        count = 0
        errors = 0
        
        for practitioner_id in practitioner_ids:
            try:
                practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
                
                # Créer ou récupérer l'inscription
                registration, created = CompetitionRegistration.objects.get_or_create(
                    competition=competition,
                    practitioner=practitioner,
                    defaults={
                        'registration_date': timezone.now(),
                        'status': 'pending'
                    }
                )
                
                # Ajouter les types de compétition
                if competition_type_ids:
                    registration.competition_types.set(competition_type_ids)
                
                count += 1
            except Exception as e:
                errors += 1
                logger.error(_("Erreur inscription pratiquant {}: {}").format(practitioner_id, str(e)), exc_info=True)
        
        return JsonResponse({
            'success': True,
            'message': _("{} pratiquant(s) inscrit(s) avec succès.").format(count),
            'registered_count': count,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Format JSON invalide.")
        }, status=400)
    except Exception as e:
        logger.error(_("Erreur inscription en masse: {}").format(str(e)), exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============================================================================
# GESTION DES ÉQUIPES
# ============================================================================

@login_required
def get_competition_teams(request, competition_id):
    """Récupérer les équipes d'une compétition pour un club."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Récupérer les équipes du club pour cette compétition
        equipes = Equipe.objects.filter(
            competition=competition,
            club=club
        ).select_related('category', 'category__competition_type').prefetch_related(
            Prefetch(
                'memberships',
                queryset=MembreEquipe.objects.select_related('pratiquant').order_by('ordre')
            )
        ).order_by('nom')

        teams_data = []
        for equipe in equipes:
            membres_data = []
            for membre in equipe.memberships.all():
                membres_data.append({
                    'id': membre.id,
                    'practitioner_id': membre.pratiquant.id,
                    'name': f"{membre.pratiquant.first_name} {membre.pratiquant.last_name}",
                    'is_substitute': membre.est_remplacant,
                    'order': membre.ordre,
                    'grade': str(membre.pratiquant.grade) if membre.pratiquant.grade else None,
                    'age': membre.pratiquant.age
                })

            titulaires_count = sum(1 for m in membres_data if not m['is_substitute'])
            min_membres = getattr(equipe, 'min_membres', 3)
            is_complete = titulaires_count >= min_membres
            status = getattr(equipe, 'status', 'active')
            type_equipe = getattr(equipe, 'type_equipe', 'mono_club')

            teams_data.append({
                'id': equipe.id,
                'name': equipe.nom,
                'category_id': equipe.category_id,
                'category_name': str(equipe.category) if equipe.category else None,
                'coach_id': equipe.coach_id,
                'coach_name': equipe.coach.get_full_name() if equipe.coach else None,
                'members': membres_data,
                'members_count': len(membres_data),
                'titulaires_count': titulaires_count,
                'remplacants_count': sum(1 for m in membres_data if m['is_substitute']),
                'min_membres': min_membres,
                'is_complete': is_complete,
                'membres_manquants': max(0, min_membres - titulaires_count),
                'status': status,
                'type_equipe': type_equipe,
                'peut_fusionner': not is_complete and type_equipe == 'mono_club' and status == 'active',
                'created_at': equipe.created_at.strftime('%d/%m/%Y %H:%M')
            })

        return JsonResponse({
            'success': True,
            'teams': teams_data,
            'total': len(teams_data)
        })

    except Exception as e:
        logger.error(f"Erreur récupération équipes: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def create_team(request, competition_id):
    """Créer une nouvelle équipe pour une compétition."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)
        club_organization = club.organization or getattr(club, 'as_organization', None)

        # Récupérer les données
        team_name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category_id')
        coach_id = request.POST.get('coach_id')
        member_ids = request.POST.getlist('member_ids[]', [])
        substitute_ids = request.POST.getlist('substitute_ids[]', [])

        if not team_name:
            return JsonResponse({
                'success': False,
                'message': _("Le nom de l'équipe est obligatoire.")
            }, status=400)

        # Vérifier que l'équipe n'existe pas déjà
        if Equipe.objects.filter(competition=competition, club=club, nom=team_name).exists():
            return JsonResponse({
                'success': False,
                'message': _("Une équipe avec ce nom existe déjà pour cette compétition.")
            }, status=400)

        # Récupérer la catégorie
        category = None
        if category_id:
            category = CompetitionCategory.objects.filter(
                id=category_id, competition=competition
            ).first()

        # Créer l'équipe
        coach = None
        if coach_id:
            from django.contrib.auth.models import User
            coach = User.objects.filter(id=coach_id).first()

        equipe = Equipe.objects.create(
            nom=team_name,
            competition=competition,
            club=club,
            coach=coach,
            category=category
        )

        # Ajouter les membres titulaires
        ordre = 1
        for practitioner_id in member_ids:
            try:
                practitioner = Practitioner.objects.get(
                    id=practitioner_id,
                    organization=club_organization
                )
                MembreEquipe.objects.create(
                    equipe=equipe,
                    pratiquant=practitioner,
                    est_remplacant=False,
                    ordre=ordre
                )
                ordre += 1
            except Practitioner.DoesNotExist:
                continue

        # Ajouter les remplaçants
        for practitioner_id in substitute_ids:
            try:
                practitioner = Practitioner.objects.get(
                    id=practitioner_id,
                    organization=club_organization
                )
                # Vérifier qu'il n'est pas déjà dans l'équipe
                if not MembreEquipe.objects.filter(equipe=equipe, pratiquant=practitioner).exists():
                    MembreEquipe.objects.create(
                        equipe=equipe,
                        pratiquant=practitioner,
                        est_remplacant=True,
                        ordre=ordre
                    )
                    ordre += 1
            except Practitioner.DoesNotExist:
                continue

        logger.info(f"Équipe créée: {equipe.nom} pour compétition {competition.id} par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Équipe '{}' créée avec succès.").format(team_name),
            'team_id': equipe.id
        })

    except Exception as e:
        logger.error(f"Erreur création équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def update_team(request, competition_id, team_id):
    """Modifier une équipe existante."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)

        # Mettre à jour le nom
        team_name = request.POST.get('name', '').strip()
        if team_name:
            # Vérifier l'unicité
            if Equipe.objects.filter(
                competition_id=competition_id,
                club=club,
                nom=team_name
            ).exclude(id=team_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': _("Une équipe avec ce nom existe déjà.")
                }, status=400)
            equipe.nom = team_name

        # Mettre à jour la catégorie
        category_id = request.POST.get('category_id')
        if category_id:
            from apps.competitions.models import CompetitionCategory
            category = CompetitionCategory.objects.filter(
                id=category_id,
                competition_id=competition_id
            ).first()
            if category:
                equipe.category = category
            else:
                return JsonResponse({
                    'success': False,
                    'message': _("Catégorie invalide.")
                }, status=400)

        # Mettre à jour le coach
        coach_id = request.POST.get('coach_id')
        if coach_id:
            from django.contrib.auth.models import User
            equipe.coach = User.objects.filter(id=coach_id).first()
        else:
            equipe.coach = None

        equipe.save()

        logger.info(f"Équipe modifiée: {equipe.nom} (ID: {equipe.id}) par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Équipe '{}' modifiée avec succès.").format(equipe.nom)
        })

    except Exception as e:
        logger.error(f"Erreur modification équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def delete_team(request, competition_id, team_id):
    """Supprimer une équipe."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)
        team_name = equipe.nom

        equipe.delete()

        logger.info(f"Équipe supprimée: {team_name} (ID: {team_id}) par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Équipe '{}' supprimée avec succès.").format(team_name)
        })

    except Exception as e:
        logger.error(f"Erreur suppression équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def add_team_member(request, competition_id, team_id):
    """Ajouter un membre à une équipe."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        club_organization = club.organization or getattr(club, 'as_organization', None)
        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)

        practitioner_id = request.POST.get('practitioner_id')
        is_substitute = request.POST.get('is_substitute', 'false').lower() == 'true'

        if not practitioner_id:
            return JsonResponse({
                'success': False,
                'message': _("Pratiquant non spécifié.")
            }, status=400)

        practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)

        # Vérifier s'il n'est pas déjà dans l'équipe
        if MembreEquipe.objects.filter(equipe=equipe, pratiquant=practitioner).exists():
            return JsonResponse({
                'success': False,
                'message': _("Ce pratiquant est déjà dans l'équipe.")
            }, status=400)

        # Déterminer l'ordre
        max_ordre = MembreEquipe.objects.filter(equipe=equipe).order_by('-ordre').values_list('ordre', flat=True).first() or 0

        membre = MembreEquipe.objects.create(
            equipe=equipe,
            pratiquant=practitioner,
            est_remplacant=is_substitute,
            ordre=max_ordre + 1
        )

        return JsonResponse({
            'success': True,
            'message': _("Membre ajouté à l'équipe."),
            'member': {
                'id': membre.id,
                'practitioner_id': practitioner.id,
                'name': f"{practitioner.first_name} {practitioner.last_name}",
                'is_substitute': membre.est_remplacant,
                'order': membre.ordre
            }
        })

    except Exception as e:
        logger.error(f"Erreur ajout membre équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def remove_team_member(request, competition_id, team_id, member_id):
    """Retirer un membre d'une équipe."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)
        membre = get_object_or_404(MembreEquipe, id=member_id, equipe=equipe)

        practitioner_name = f"{membre.pratiquant.first_name} {membre.pratiquant.last_name}"
        membre.delete()

        return JsonResponse({
            'success': True,
            'message': _("{} retiré de l'équipe.").format(practitioner_name)
        })

    except Exception as e:
        logger.error(f"Erreur retrait membre équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def update_team_member(request, competition_id, team_id, member_id):
    """Modifier le statut d'un membre (titulaire/remplaçant) ou son ordre."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)
        membre = get_object_or_404(MembreEquipe, id=member_id, equipe=equipe)

        # Mettre à jour le statut
        is_substitute = request.POST.get('is_substitute')
        if is_substitute is not None:
            membre.est_remplacant = is_substitute.lower() == 'true'

        # Mettre à jour l'ordre
        ordre = request.POST.get('order')
        if ordre is not None:
            membre.ordre = int(ordre)

        membre.save()

        return JsonResponse({
            'success': True,
            'message': _("Membre mis à jour.")
        })

    except Exception as e:
        logger.error(f"Erreur mise à jour membre équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def reorder_team_members(request, competition_id, team_id):
    """Réordonner les membres d'une équipe."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        equipe = get_object_or_404(Equipe, id=team_id, competition_id=competition_id, club=club)

        # Récupérer l'ordre des membres
        member_order = request.POST.getlist('member_order[]', [])

        for index, member_id in enumerate(member_order):
            MembreEquipe.objects.filter(
                id=member_id,
                equipe=equipe
            ).update(ordre=index + 1)

        return JsonResponse({
            'success': True,
            'message': _("Ordre des membres mis à jour.")
        })

    except Exception as e:
        logger.error(f"Erreur réordonnancement équipe: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============================================================================
# FUSION D'ÉQUIPES INTER-CLUBS
# ============================================================================

@login_required
def get_incomplete_teams(request, competition_id):
    """Récupérer les équipes incomplètes disponibles pour fusion."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Toutes les équipes actives de la compétition (pour diagnostiquer)
        all_teams = Equipe.objects.filter(
            competition=competition,
            is_active=True
        )
        total_teams_count = all_teams.count()
        other_clubs_teams_count = all_teams.exclude(club=club).count()
        own_club_teams = all_teams.filter(club=club)

        # Équipes incomplètes de TOUS les clubs (sauf le club actuel)
        equipes = Equipe.objects.filter(
            competition=competition,
            type_equipe='mono_club',
            status='active',
            is_active=True
        ).exclude(
            club=club
        ).select_related('club').prefetch_related('memberships').order_by('club__name', 'nom')

        teams_data = []
        for equipe in equipes:
            titulaires_count = equipe.memberships.filter(est_remplacant=False).count()
            if titulaires_count < equipe.min_membres:  # Équipe incomplète
                teams_data.append({
                    'id': equipe.id,
                    'name': equipe.nom,
                    'club_id': equipe.club_id,
                    'club_name': equipe.club.name if equipe.club else 'N/A',
                    'titulaires_count': titulaires_count,
                    'min_membres': equipe.min_membres,
                    'membres_manquants': equipe.min_membres - titulaires_count,
                    'status': equipe.status
                })

        # Équipes du même club qui pourraient aussi fusionner entre elles
        own_incomplete = []
        source_team_id = request.GET.get('source_team_id')
        for equipe in own_club_teams.filter(
            type_equipe='mono_club', status='active'
        ).prefetch_related('memberships'):
            if source_team_id and str(equipe.id) == str(source_team_id):
                continue  # Exclure l'équipe source elle-même
            titulaires_count = equipe.memberships.filter(est_remplacant=False).count()
            if titulaires_count < equipe.min_membres:
                own_incomplete.append({
                    'id': equipe.id,
                    'name': equipe.nom,
                    'club_id': equipe.club_id,
                    'club_name': equipe.club.name if equipe.club else club.name,
                    'titulaires_count': titulaires_count,
                    'min_membres': equipe.min_membres,
                    'membres_manquants': equipe.min_membres - titulaires_count,
                    'status': equipe.status,
                    'same_club': True
                })

        logger.info(
            f"Fusion search: competition={competition_id}, club={club.name}(id={club.id}), "
            f"total_teams={total_teams_count}, other_clubs={other_clubs_teams_count}, "
            f"incomplete_other={len(teams_data)}, incomplete_own={len(own_incomplete)}"
        )

        return JsonResponse({
            'success': True,
            'teams': teams_data,
            'own_incomplete_teams': own_incomplete,
            'total': len(teams_data),
            'total_teams_in_competition': total_teams_count,
            'other_clubs_teams': other_clubs_teams_count,
            'own_club_name': club.name
        })

    except Exception as e:
        logger.error(f"Erreur récupération équipes incomplètes: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def request_team_fusion(request, competition_id, team_id):
    """Demander une fusion avec une autre équipe incomplète."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Équipe source (notre équipe incomplète)
        source_team_id = request.POST.get('source_team_id')
        if not source_team_id:
            return JsonResponse({
                'success': False,
                'message': _("Équipe source non spécifiée.")
            }, status=400)

        source_team = get_object_or_404(Equipe, id=source_team_id, competition=competition, club=club)

        # Vérifier que l'équipe source peut fusionner
        if source_team.is_complete:
            return JsonResponse({
                'success': False,
                'message': _("Votre équipe est déjà complète.")
            }, status=400)

        # Équipe cible
        target_team = get_object_or_404(Equipe, id=team_id, competition=competition)

        if target_team.id == source_team.id:
            return JsonResponse({
                'success': False,
                'message': _("Vous ne pouvez pas fusionner une équipe avec elle-même.")
            }, status=400)

        if target_team.status == 'pending_fusion':
            return JsonResponse({
                'success': False,
                'message': _("Cette équipe a déjà une demande de fusion en cours.")
            }, status=400)

        # Message de demande
        message = request.POST.get('message', '')

        # Marquer la demande de fusion
        source_team.status = 'pending_fusion'
        source_team.equipe_parent = target_team
        source_team.demande_fusion_message = message
        source_team.save()

        logger.info(f"Demande fusion: {source_team.nom} -> {target_team.nom} par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Demande de fusion envoyée à {} ({}).").format(
                target_team.nom,
                target_team.club.name if target_team.club else 'N/A'
            )
        })

    except Exception as e:
        logger.error(f"Erreur demande fusion: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def get_fusion_requests(request, competition_id):
    """Récupérer les demandes de fusion reçues par le club."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Équipes qui demandent à fusionner avec nos équipes
        our_teams = Equipe.objects.filter(competition=competition, club=club)

        requests_received = Equipe.objects.filter(
            competition=competition,
            status='pending_fusion',
            equipe_parent__in=our_teams
        ).select_related('club', 'equipe_parent').prefetch_related('memberships')

        requests_data = []
        for equipe in requests_received:
            requests_data.append({
                'id': equipe.id,
                'name': equipe.nom,
                'club_name': equipe.club.name if equipe.club else 'N/A',
                'target_team_id': equipe.equipe_parent_id,
                'target_team_name': equipe.equipe_parent.nom if equipe.equipe_parent else 'N/A',
                'message': equipe.demande_fusion_message,
                'titulaires_count': equipe.memberships.filter(est_remplacant=False).count(),
                'created_at': equipe.created_at.strftime('%d/%m/%Y %H:%M')
            })

        # Nos demandes envoyées
        requests_sent = Equipe.objects.filter(
            competition=competition,
            club=club,
            status='pending_fusion'
        ).select_related('equipe_parent', 'equipe_parent__club')

        sent_data = []
        for equipe in requests_sent:
            sent_data.append({
                'id': equipe.id,
                'name': equipe.nom,
                'target_team_name': equipe.equipe_parent.nom if equipe.equipe_parent else 'N/A',
                'target_club_name': equipe.equipe_parent.club.name if equipe.equipe_parent and equipe.equipe_parent.club else 'N/A',
                'message': equipe.demande_fusion_message
            })

        return JsonResponse({
            'success': True,
            'received': requests_data,
            'sent': sent_data,
            'received_count': len(requests_data),
            'sent_count': len(sent_data)
        })

    except Exception as e:
        logger.error(f"Erreur récupération demandes fusion: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def accept_team_fusion(request, competition_id, team_id):
    """Accepter une demande de fusion et créer l'équipe fusionnée."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Équipe qui demande la fusion
        requesting_team = get_object_or_404(
            Equipe,
            id=team_id,
            competition=competition,
            status='pending_fusion'
        )

        # Vérifier que la cible est notre équipe
        target_team = requesting_team.equipe_parent
        if not target_team or target_team.club != club:
            return JsonResponse({
                'success': False,
                'message': _("Cette demande ne vous est pas destinée.")
            }, status=403)

        # Créer la nouvelle équipe fusionnée
        fusion_name = request.POST.get('fusion_name', f"{target_team.nom} + {requesting_team.nom}")

        new_team = Equipe.objects.create(
            nom=fusion_name,
            competition=competition,
            club=target_team.club,  # Club principal = celui qui accepte
            type_equipe='multi_club',
            status='fusion_complete',
            min_membres=target_team.min_membres,
            max_membres=target_team.max_membres
        )

        # Ajouter le club partenaire
        if requesting_team.club:
            new_team.clubs_partenaires.add(requesting_team.club)

        # Fusionner les membres des deux équipes
        ordre = 1
        for membre in target_team.memberships.all():
            MembreEquipe.objects.create(
                equipe=new_team,
                pratiquant=membre.pratiquant,
                est_remplacant=membre.est_remplacant,
                ordre=ordre
            )
            ordre += 1

        for membre in requesting_team.memberships.all():
            # Éviter les doublons
            if not MembreEquipe.objects.filter(equipe=new_team, pratiquant=membre.pratiquant).exists():
                MembreEquipe.objects.create(
                    equipe=new_team,
                    pratiquant=membre.pratiquant,
                    est_remplacant=membre.est_remplacant,
                    ordre=ordre
                )
                ordre += 1

        # Copier la catégorie depuis les équipes sources vers la nouvelle équipe
        if not new_team.category:
            new_team.category = target_team.category or requesting_team.category
            new_team.save()

        # Marquer les anciennes équipes comme fusionnées et les désactiver
        target_team.status = 'fusion_complete'
        target_team.merged_into = new_team
        target_team.equipe_parent = new_team
        target_team.is_active = False
        target_team.save()

        requesting_team.status = 'fusion_complete'
        requesting_team.merged_into = new_team
        requesting_team.equipe_parent = new_team
        requesting_team.is_active = False
        requesting_team.save()

        logger.info(f"Fusion acceptée: {new_team.nom} créée à partir de {target_team.nom} et {requesting_team.nom}")

        return JsonResponse({
            'success': True,
            'message': _("Fusion acceptée! Nouvelle équipe '{}' créée.").format(new_team.nom),
            'new_team_id': new_team.id
        })

    except Exception as e:
        logger.error(f"Erreur acceptation fusion: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def reject_team_fusion(request, competition_id, team_id):
    """Refuser une demande de fusion."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        # Équipe qui demande la fusion
        requesting_team = get_object_or_404(
            Equipe,
            id=team_id,
            competition=competition,
            status='pending_fusion'
        )

        # Vérifier que la cible est notre équipe
        target_team = requesting_team.equipe_parent
        if not target_team or target_team.club != club:
            return JsonResponse({
                'success': False,
                'message': _("Cette demande ne vous est pas destinée.")
            }, status=403)

        # Annuler la demande de fusion
        requesting_team.status = 'active'
        requesting_team.equipe_parent = None
        requesting_team.demande_fusion_message = ''
        requesting_team.save()

        logger.info(f"Fusion refusée: {requesting_team.nom} par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Demande de fusion refusée.")
        })

    except Exception as e:
        logger.error(f"Erreur refus fusion: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def cancel_fusion_request(request, competition_id, team_id):
    """Annuler une demande de fusion envoyée."""
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        # Notre équipe qui a demandé la fusion
        team = get_object_or_404(
            Equipe,
            id=team_id,
            competition_id=competition_id,
            club=club,
            status='pending_fusion'
        )

        # Annuler la demande
        team.status = 'active'
        team.equipe_parent = None
        team.demande_fusion_message = ''
        team.save()

        logger.info(f"Demande fusion annulée: {team.nom} par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Demande de fusion annulée.")
        })

    except Exception as e:
        logger.error(f"Erreur annulation fusion: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def merge_teams(request, competition_id):
    """
    Fusionner 2 équipes en transférant les membres de l'équipe 2 vers l'équipe 1.
    L'équipe 1 conserve son nom et reçoit les membres de l'équipe 2.
    L'équipe 2 est supprimée après la fusion.
    """
    try:
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être responsable de club.")
            }, status=403)

        competition = get_object_or_404(Competition, id=competition_id)

        team1_id = request.POST.get('team1_id')
        team2_id = request.POST.get('team2_id')

        if not team1_id or not team2_id:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez sélectionner 2 équipes à fusionner.")
            }, status=400)

        if team1_id == team2_id:
            return JsonResponse({
                'success': False,
                'message': _("Impossible de fusionner une équipe avec elle-même.")
            }, status=400)

        # Récupérer les équipes
        team1 = get_object_or_404(Equipe, id=team1_id, competition=competition)
        team2 = get_object_or_404(Equipe, id=team2_id, competition=competition)

        # Vérifier que l'utilisateur a les droits sur au moins une des équipes
        user_has_rights = (team1.club == club) or (team2.club == club)
        if not user_has_rights:
            return JsonResponse({
                'success': False,
                'message': _("Vous n'avez pas les droits sur ces équipes.")
            }, status=403)

        # Transférer les membres de team2 vers team1
        max_ordre = MembreEquipe.objects.filter(equipe=team1).order_by('-ordre').values_list('ordre', flat=True).first() or 0
        membres_transferes = 0

        for membre in team2.memberships.all():
            # Vérifier que le pratiquant n'est pas déjà dans team1
            if not MembreEquipe.objects.filter(equipe=team1, pratiquant=membre.pratiquant).exists():
                max_ordre += 1
                MembreEquipe.objects.create(
                    equipe=team1,
                    pratiquant=membre.pratiquant,
                    est_remplacant=membre.est_remplacant,
                    ordre=max_ordre
                )
                membres_transferes += 1

        team2_name = team2.nom

        # Supprimer l'équipe 2
        team2.delete()

        # Mettre à jour le statut de team1 si elle devient complète
        titulaires_count = team1.memberships.filter(est_remplacant=False).count()
        min_membres = getattr(team1, 'min_membres', 3)
        if titulaires_count >= min_membres:
            team1.status = 'active'
            team1.save()

        logger.info(f"Fusion équipes: {team2_name} -> {team1.nom}, {membres_transferes} membres transférés par {request.user}")

        return JsonResponse({
            'success': True,
            'message': _("Équipe '{}' fusionnée avec '{}'. {} membre(s) transféré(s).").format(
                team2_name, team1.nom, membres_transferes
            ),
            'team_id': team1.id,
            'members_transferred': membres_transferes
        })

    except Exception as e:
        logger.error(f"Erreur fusion équipes: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def generate_license_number_api(request):
    """
    API pour générer un numéro de licence unique.
    Format: DISC-YYYY-CLUB-XXXX
    - DISC: Code de la discipline (2-3 lettres)
    - YYYY: Année de naissance
    - CLUB: ID du club (4 chiffres)
    - XXXX: Numéro séquentiel unique
    """
    try:
        import random
        import string

        data = json.loads(request.body)
        birth_date = data.get('birth_date', '')
        disciplines = data.get('disciplines', [])
        last_name = data.get('last_name', '')

        if not birth_date or not disciplines or not last_name:
            return JsonResponse({
                'success': False,
                'error': _("Données manquantes: date de naissance, disciplines ou nom requis")
            }, status=400)

        # Récupérer le club de l'utilisateur
        club = get_user_club(request)
        if not club:
            return JsonResponse({
                'success': False,
                'error': _("Vous devez être responsable de club.")
            }, status=403)

        # Extraire l'année de naissance
        try:
            year = birth_date.split('-')[0]
        except (IndexError, AttributeError):
            year = '0000'

        # Code discipline (première discipline, premiers caractères)
        discipline_name = disciplines[0] if disciplines else 'XX'
        # Créer un code court pour la discipline
        discipline_code = ''.join([word[0].upper() for word in discipline_name.split()[:3]])
        if len(discipline_code) < 2:
            discipline_code = discipline_name[:3].upper()

        # Code club (ID sur 4 chiffres)
        club_code = str(club.id).zfill(4)

        # Initiales du nom
        initials = last_name[:2].upper() if last_name else 'XX'

        # Générer un numéro séquentiel unique (4 caractères alphanumériques)
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

        # Construire le numéro de licence
        license_number = f"{discipline_code}-{year}-{club_code}-{initials}{random_suffix}"

        # Vérifier l'unicité
        from apps.competitions.models import Practitioner
        attempts = 0
        while Practitioner.objects.filter(license_number=license_number).exists() and attempts < 10:
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            license_number = f"{discipline_code}-{year}-{club_code}-{initials}{random_suffix}"
            attempts += 1

        return JsonResponse({
            'success': True,
            'license_number': license_number
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': _("Format JSON invalide")
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur génération licence: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)