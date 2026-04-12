from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from django.db import models
from django.http import JsonResponse
import logging

# Désactiver modeltranslation pour éviter les colonnes inexistantes
# Utiliser raw SQL pour les requêtes problématiques
from django.db import connection

from ...models import (
    Club, Practitioner, Competition, CompetitionRegistration, Notification,
    TrainingProgram, TrainingSession, TrainingSlot, Attendance
)
from apps.finances.models import PaymentAttempt, Invoice
from apps.shop.models import Order
from apps.finances.currency_service import COUNTRY_TO_CURRENCY
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
from apps.competitions.utils.organization_discipline_filtering import (
    filter_practitioners_by_org_disciplines,
    filter_competitions_by_org_disciplines,
    filter_judges_by_org_disciplines,
    filter_by_specific_discipline,
    get_organization_disciplines
)
from apps.competitions.services.member_statistics_service import (
    calculate_member_statistics,
    get_grade_distribution,
)

logger = logging.getLogger(__name__)


def calculate_site_stats(organization):
    """
    Calcule les statistiques réelles du site pour une organisation.
    """
    stats = {
        'total_visits': 0,
        'qr_scans': 0,
        'registrations_via_site': 0,
        'gallery_photos': 0
    }

    if not organization:
        return stats

    try:
        # Compter les photos de galerie
        from apps.organizations.models import OrganizationGalleryImage
        stats['gallery_photos'] = OrganizationGalleryImage.objects.filter(
            organization=organization
        ).count()
    except Exception as e:
        logger.warning(f"Erreur comptage galerie: {e}")

    try:
        # Compter les compétitions publiées (indicateur d'activité)
        from apps.competitions.models import Competition
        published_competitions = Competition.objects.filter(
            organizing_organization=organization,
            is_published=True
        ).count()
        # Estimation des visites basée sur l'activité
        stats['total_visits'] = published_competitions * 10  # Estimation
    except Exception as e:
        logger.warning(f"Erreur comptage compétitions: {e}")

    try:
        # Compter les inscriptions via le site
        from apps.competitions.models import CompetitionRegistration
        stats['registrations_via_site'] = CompetitionRegistration.objects.filter(
            competition__organizing_organization=organization
        ).count()
    except Exception as e:
        logger.warning(f"Erreur comptage inscriptions: {e}")

    return stats


# Task Management Integration
try:
    from apps.task_management.dashboard_utils import get_dashboard_task_data, get_club_dashboard_task_data
    TASK_MANAGEMENT_AVAILABLE = True
except ImportError:
    TASK_MANAGEMENT_AVAILABLE = False
    logger.warning("Task Management module not available")

@login_required
def club_dashboard(request):
    """
    Tableau de bord pour les responsables de club.
    Affiche les statistiques et les informations relatives au club.
    """
    # Debug des informations utilisateur
    logger.info(f"User: {request.user.username}, authenticated: {request.user.is_authenticated}")
    if hasattr(request.user, 'profile'):
        logger.info(f"User profile role: {request.user.profile.role}")
    else:
        logger.info("User n'a pas d'attribut 'profile'")
    
    # Récupérer le club associé à l'utilisateur avec debug
    club = None
    club_found_via = "non trouvé"
    
    # Récupérer le club avec raw SQL pour éviter modeltranslation
    # Utiliser un dictionnaire pour stocker les données du club
    club_data_dict = None
    
    # Méthode 1: Via attribut direct
    if hasattr(request.user, 'club_id') and request.user.club_id:
        club_id = request.user.club_id
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, organization_id, owner_id
                FROM competitions_club
                WHERE id = %s
            """, [club_id])
            row = cursor.fetchone()
            if row:
                club_data_dict = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if len(row) > 2 else '',
                    'organization_id': row[3] if len(row) > 3 else None,
                    'owner_id': row[4] if len(row) > 4 else None
                }
                club_found_via = "attribut direct"
    
    # Méthode 2: Via relation de propriété
    if not club_data_dict:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, organization_id, owner_id
                FROM competitions_club
                WHERE owner_id = %s
                LIMIT 1
            """, [request.user.id])
            row = cursor.fetchone()
            if row:
                club_data_dict = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if len(row) > 2 else '',
                    'organization_id': row[3] if len(row) > 3 else None,
                    'owner_id': row[4] if len(row) > 4 else None
                }
                club_found_via = "propriété"
    
    # Méthode 3: Via profil utilisateur
    if not club_data_dict and hasattr(request.user, 'profile_id') and request.user.profile_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, c.description, c.organization_id, c.owner_id
                FROM competitions_club c
                INNER JOIN competitions_userprofile p ON c.id = p.club_id
                WHERE p.id = %s
                LIMIT 1
            """, [request.user.profile_id])
            row = cursor.fetchone()
            if row:
                club_data_dict = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if len(row) > 2 else '',
                    'organization_id': row[3] if len(row) > 3 else None,
                    'owner_id': row[4] if len(row) > 4 else None
                }
                club_found_via = "profil"
    
    # Méthode 4: Via OrganizationMember (remplace clubmembership qui n'existe plus)
    if not club_data_dict:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.id, c.name, c.description, c.organization_id, c.owner_id
                    FROM competitions_club c
                    INNER JOIN organizations_organizationmember om ON c.organization_id = om.organization_id
                    WHERE om.user_id = %s
                    LIMIT 1
                """, [request.user.id])
                row = cursor.fetchone()
                if row:
                    club_data_dict = {
                        'id': row[0],
                        'name': row[1],
                        'description': row[2] if len(row) > 2 else '',
                        'organization_id': row[3] if len(row) > 3 else None,
                        'owner_id': row[4] if len(row) > 4 else None
                    }
                    club_found_via = "organization_member"
        except Exception as e:
            logger.warning(f"Méthode 4 (OrganizationMember) a échoué: {e}")
    
    # Créer un objet Club réel depuis la base de données
    club = None
    if club_data_dict:
        from ...models import Club
        try:
            # Charger le club depuis la base sans passer par les champs traduits
            club = Club.objects.raw('SELECT * FROM competitions_club WHERE id = %s', [club_data_dict['id']])[0]
        except:
            # Si ça échoue, créer un objet Club avec les données minimales
            club = Club(
                id=club_data_dict['id'],
                name=club_data_dict['name'],
                description=club_data_dict['description'] or '',
                organization_id=club_data_dict['organization_id'],
                owner_id=club_data_dict['owner_id']
            )
            club.pk = club_data_dict['id']  # S'assurer que pk est défini
    
    logger.info(f"Club: {club}, trouvé via: {club_found_via}")
    
    # Date actuelle pour les calculs - DÉPLACÉ ICI POUR ÉVITER L'ERREUR
    now = timezone.now().date()
    
    # Initialiser club_organization
    club_organization = None
    
    # Diagnostic mode - Ajouter un paramètre pour activer le mode diagnostic
    if request.GET.get('diagnostic') == '1':
        context = {
            'club': club,
            'club_found_via': club_found_via,
            'context_keys': ['club', 'club_found_via', 'stats', 'financial_stats'],
            'stats': {
                'total_practitioners': 0,
                'club_competitions': 0,
                'active_registrations': 0,
                'judges_count': 0
            }
        }
        return render(request, 'competitions/dashboard/club_diagnostic.html', context)
    
    # Si aucun club n'est trouvé, rediriger vers la création de club
    if not club:
        messages.warning(request, _("Vous devez d'abord créer ou rejoindre un club pour accéder au tableau de bord."))
        
        # Essayer différentes URLs de redirection dans un ordre logique
        redirect_urls = [
            'competitions:clubs:create',
            'competitions:club:create',
            'competitions:onboarding:club_creation',
            'competitions:welcome'
        ]
        
        for url_name in redirect_urls:
            try:
                return redirect(url_name)
            except:
                continue
        
        # Fallback ultime si aucune URL ne fonctionne
        return redirect('/')
    
    # S'assurer qu'une Organization associée est attachée au club si possible
    # Utiliser organization_id directement pour éviter modeltranslation
    club_organization_id = club_data_dict['organization_id'] if club_data_dict else None
    
    # Récupérer les compétitions que ce club peut gérer
    competitions_to_manage = []  # Liste d'IDs pour éviter modeltranslation
    
    if club:
        try:
            # Vérifier si le club a une organisation associée
            # Charger l'organisation complète pour avoir accès au logo
            club_organization = None
            if club_organization_id:
                try:
                    from apps.organizations.models import Organization
                    club_organization = Organization.objects.get(id=club_organization_id)
                except Organization.DoesNotExist:
                    logger.warning(f"Organisation {club_organization_id} non trouvée")
                    club_organization = None
                except Exception as e:
                    logger.error(_("Erreur lors du chargement de l'organisation {}: {}").format(club_organization_id, str(e)))
                    # Fallback avec raw SQL si l'ORM échoue
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT id, name, description
                            FROM organizations_organization
                            WHERE id = %s
                        """, [club_organization_id])
                        org_data = cursor.fetchone()
                        if org_data:
                            from apps.organizations.models import Organization
                            club_organization = Organization(id=org_data[0], name=org_data[1], description=org_data[2] if len(org_data) > 2 else '')
            
            if club_organization:
                # Récupérer les compétitions où l'organisation du club est organisatrice
                # Utiliser raw SQL pour éviter modeltranslation
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT c.id 
                        FROM competitions_competition c
                        WHERE c.organizing_organization_id = %s
                    """, [club_organization.id])
                    competition_ids = [row[0] for row in cursor.fetchall()]
                # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
                competitions_to_manage = competition_ids  # Liste d'IDs pour l'instant
            else:
                club_name = getattr(club, 'name', 'N/A') if club else 'N/A'
                club_id = getattr(club, 'id', None) if club else None
                logger.warning(f"Aucune organisation associée trouvée pour le club {club_name} (id={club_id})")
            
            # Si le modèle Competition a un champ manager, ajouter les compétitions où l'utilisateur est manager
            if hasattr(Competition, 'manager'):
                # Utiliser raw SQL pour éviter modeltranslation
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT id 
                        FROM competitions_competition
                        WHERE manager_id = %s
                    """, [request.user.id])
                    manager_competition_ids = [row[0] for row in cursor.fetchall()]
                # Fusionner les listes d'IDs
                if isinstance(competitions_to_manage, list):
                    competitions_to_manage = list(set(competitions_to_manage + manager_competition_ids))
                else:
                    competitions_to_manage = manager_competition_ids
            
            # Debug: Afficher le nombre de compétitions trouvées - CORRIGÉ UTF-8
            logger.info(f"Compétitions à gérer trouvées: {len(competitions_to_manage)}")
            
        except Exception as e:
            logger.error(_("Erreur lors de la récupération des compétitions à gérer: {}").format(str(e)))
            # Fallback simple - prendre uniquement les compétitions du club
            # Vérifier si le club a une organisation associée
            # Utiliser club_organization déjà chargé ou charger depuis organization_id
            if not club_organization and club_organization_id:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, description
                        FROM organizations_organization
                        WHERE id = %s
                    """, [club_organization_id])
                    org_data = cursor.fetchone()
                    if org_data:
                        from apps.organizations.models import Organization
                        club_organization = Organization(id=org_data[0], name=org_data[1], description=org_data[2] if len(org_data) > 2 else '')
            
            if club_organization:
                # Utiliser raw SQL pour éviter modeltranslation
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id 
                        FROM competitions_competition
                        WHERE organizing_organization_id = %s
                    """, [club_organization.id])
                    competition_ids = [row[0] for row in cursor.fetchall()]
                # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
                competitions_to_manage = competition_ids  # Liste d'IDs pour l'instant
            else:
                club_name = getattr(club, 'name', 'N/A') if club else 'N/A'
                club_id = getattr(club, 'id', None) if club else None
                logger.warning(f"Aucune organisation associée trouvée pour le club {club_name} (id={club_id})")
    
    # Statistiques du club
    stats = {}
    
    # Nombre total de pratiquants
    # Vérifier si le club a une organisation associée
    # Utiliser club_organization déjà chargé ou charger depuis organization_id
    if not club_organization and club_organization_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description
                FROM organizations_organization
                WHERE id = %s
            """, [club_organization_id])
            org_data = cursor.fetchone()
            if org_data:
                from apps.organizations.models import Organization
                club_organization = Organization(id=org_data[0], name=org_data[1], description=org_data[2] if len(org_data) > 2 else '')
    if club_organization:
        # Compter TOUS les pratiquants de l'organisation (sans filtre discipline)
        # Le filtre par discipline est trop restrictif pour le compteur total :
        # les pratiquants sans discipline assignée ne seraient pas comptés.
        from apps.competitions.models import Practitioner as PractitionerModel
        stats['total_practitioners'] = PractitionerModel.objects.filter(
            organization=club_organization
        ).count()
        # Garder le queryset filtré par discipline pour les statistiques détaillées
        practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
    else:
        club_name = getattr(club, 'name', 'N/A') if club else 'N/A'
        club_id = getattr(club, 'id', None) if club else None
        logger.warning(f"Aucune organisation associée trouvée pour le club {club_name} (id={club_id})")
        stats['total_practitioners'] = 0
    
    # Récupérer les disciplines du club
    # Utiliser raw SQL pour éviter modeltranslation
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.name, d.description
            FROM competitions_discipline d
            INNER JOIN competitions_club_disciplines cd ON d.id = cd.discipline_id
            WHERE cd.club_id = %s
        """, [club_data_dict['id'] if club_data_dict else None])
        discipline_data = cursor.fetchall()
    # Créer des objets Discipline sans passer par ORM pour éviter modeltranslation
    from ...models import Discipline
    club_disciplines = []
    for row in discipline_data:
        disc = Discipline(id=row[0], name=row[1], description=row[2] if len(row) > 2 else '')
        club_disciplines.append(disc)
    
    # Récupérer les compétitions organisées par le club
    # Utiliser organizing_organization avec l'organisation associée au club
    # Utiliser club_organization déjà chargé ou charger depuis organization_id
    if not club_organization and club_organization_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description
                FROM organizations_organization
                WHERE id = %s
            """, [club_organization_id])
            org_data = cursor.fetchone()
            if org_data:
                from apps.organizations.models import Organization
                club_organization = Organization(id=org_data[0], name=org_data[1], description=org_data[2] if len(org_data) > 2 else '')
    
    club_competitions_ids = []  # Liste d'IDs pour éviter modeltranslation
    club_competitions = []  # Sera rempli plus tard si nécessaire
    if club_organization:
        # Filtrer les compétitions par disciplines de l'organisation
        competitions_qs = filter_competitions_by_org_disciplines(club_organization)
        # Utiliser raw SQL pour éviter modeltranslation, mais filtrer par discipline
        org_disciplines = get_organization_disciplines(club_organization)
        discipline_ids = list(org_disciplines.values_list('id', flat=True)) if org_disciplines.exists() else []
        
        with connection.cursor() as cursor:
            if discipline_ids:
                cursor.execute("""
                    SELECT id 
                    FROM competitions_competition
                    WHERE organizing_organization_id = %s
                    AND discipline_id IN %s
                    ORDER BY start_date DESC
                """, [club_organization.id, tuple(discipline_ids)])
            else:
                cursor.execute("""
                    SELECT id 
                    FROM competitions_competition
                    WHERE organizing_organization_id = %s
                    ORDER BY start_date DESC
                """, [club_organization.id])
            competition_ids = [row[0] for row in cursor.fetchall()]
        # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
        club_competitions_ids = competition_ids  # Liste d'IDs pour l'instant
        club_competitions = []  # Sera rempli plus tard si nécessaire
    
    stats['club_competitions'] = len(club_competitions_ids) if 'club_competitions_ids' in locals() else 0
    
    # Récupérer les compétitions à venir (où le club peut participer)
    # Utiliser raw SQL pour éviter modeltranslation
    club_competition_ids = club_competitions_ids if 'club_competitions_ids' in locals() else []
    with connection.cursor() as cursor:
        if club_competition_ids:
            cursor.execute("""
                SELECT id 
                FROM competitions_competition
                WHERE end_date >= %s
                AND status IN ('published', 'open')
                AND id NOT IN %s
                ORDER BY start_date ASC
                LIMIT 5
            """, [now, tuple(club_competition_ids)])
        else:
            cursor.execute("""
                SELECT id 
                FROM competitions_competition
                WHERE end_date >= %s
                AND status IN ('published', 'open')
                ORDER BY start_date ASC
                LIMIT 5
            """, [now])
        competition_ids = [row[0] for row in cursor.fetchall()]
    # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
    upcoming_competitions_ids = competition_ids[:5]  # Liste d'IDs pour l'instant
    upcoming_competitions = []  # Sera rempli plus tard si nécessaire
    
    stats['upcoming_competitions'] = len(upcoming_competitions_ids) if 'upcoming_competitions_ids' in locals() else 0
    
    # Nombre d'inscriptions actives (pratiquants de ce club inscrits à des compétitions à venir)
    # Filtrer par disciplines de l'organisation
    if club_organization:
        # Filtrer d'abord les pratiquants par disciplines
        practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
        active_registrations = CompetitionRegistration.objects.filter(
            practitioner__in=practitioners_qs,
            competition__end_date__gte=now
        )
    else:
        active_registrations = CompetitionRegistration.objects.none()
    stats['active_registrations'] = active_registrations.count()
    
    # Récupérer les inscriptions récentes pour l'onglet
    recent_registrations = active_registrations.order_by('-registration_date')[:5]
    
    # Nombre de juges/arbitres du club
    try:
        from ...models import Judge
        # Méthode 1: Utiliser le modèle Judge
        if club_organization:
            # Filtrer les juges par les disciplines de l'organisation
            club_judges = filter_judges_by_org_disciplines(club_organization)
        else:
            club_judges = Judge.objects.none()
        stats['judges_count'] = club_judges.count()
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des juges: {}").format(str(e)))
        try:
            # Méthode 2: Utiliser les qualifications
            if club_organization:
                # Filtrer par disciplines de l'organisation
                practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
                stats['judges_count'] = practitioners_qs.filter(
                    qualifications__isnull=False
                ).distinct().count()
            else:
                stats['judges_count'] = 0
        except Exception as e:
            logger.error(_("Erreur lors de la récupération des qualifications: {}").format(str(e)))
            # Fallback : compter les pratiquants marqués comme juges
            stats['judges_count'] = 0
    
    # Récupérer les 5 pratiquants les plus récemment ajoutés
    if club_organization:
        try:
            # Filtrer par disciplines de l'organisation
            recent_practitioners = filter_practitioners_by_org_disciplines(club_organization).order_by('-created_at', '-id')[:5]
        except Exception as e:
            logger.error(_("Erreur lors du tri par created_at: {}").format(str(e)))
            # Filtrer par disciplines de l'organisation
            recent_practitioners = filter_practitioners_by_org_disciplines(club_organization).order_by('-id')[:5]
    else:
        recent_practitioners = Practitioner.objects.none()
    
    # Récupérer TOUS les pratiquants pour l'onglet pratiquants
    # Paramètres de filtrage côté serveur (GET parameters)
    filter_search = request.GET.get('search', '').strip()
    filter_discipline = request.GET.get('discipline', '')
    filter_grade = request.GET.get('grade', '')
    filter_status = request.GET.get('status', 'active')  # Par défaut: actifs seulement
    filter_gender = request.GET.get('gender', '')

    if club_organization:
        try:
            # Récupérer TOUS les pratiquants de l'organisation (sans filtre discipline)
            all_practitioners = PractitionerModel.objects.filter(
                organization=club_organization
            ).select_related('grade').prefetch_related('disciplines').order_by('last_name', 'first_name')

            # Appliquer les filtres côté serveur
            if filter_search:
                all_practitioners = all_practitioners.filter(
                    Q(first_name__icontains=filter_search) |
                    Q(last_name__icontains=filter_search) |
                    Q(email__icontains=filter_search) |
                    Q(license_number__icontains=filter_search)
                )

            if filter_discipline:
                try:
                    discipline_id = int(filter_discipline)
                    all_practitioners = all_practitioners.filter(
                        Q(primary_discipline_id=discipline_id) |
                        Q(disciplines__id=discipline_id)
                    ).distinct()
                except (ValueError, TypeError):
                    pass

            if filter_grade:
                try:
                    grade_id = int(filter_grade)
                    all_practitioners = all_practitioners.filter(grade_id=grade_id)
                except (ValueError, TypeError):
                    pass

            if filter_status and filter_status != 'all':
                if filter_status == 'active':
                    all_practitioners = all_practitioners.filter(is_active=True)
                elif filter_status == 'inactive':
                    all_practitioners = all_practitioners.filter(is_active=False)

            if filter_gender and filter_gender != 'all':
                all_practitioners = all_practitioners.filter(gender=filter_gender)
            
            # Charger la liste des grades disponibles pour les filtres
            grades_list = []
            try:
                from apps.grades.models import Grade as GradeModel
                # Récupérer les grades des disciplines du club
                discipline_ids = [d.id for d in club_disciplines] if club_disciplines else []
                if discipline_ids:
                    grades_list = list(GradeModel.objects.filter(
                        discipline_id__in=discipline_ids,
                        is_active=True
                    ).order_by('discipline__name', 'level').values('id', 'name', 'discipline__name'))
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de la liste des grades: {str(e)}")

            # Charger les grades actuels pour chaque pratiquant
            try:
                from apps.grades.models import PractitionerGrade
                for practitioner in all_practitioners:
                    # Récupérer le grade principal (le plus élevé)
                    main_grade = PractitionerGrade.objects.filter(
                        practitioner=practitioner,
                        is_current=True
                    ).select_related('grade', 'grade__discipline').order_by('-grade__level').first()
                    
                    if main_grade and main_grade.grade:
                        practitioner.computed_grade_display = main_grade.grade.name
                        practitioner.computed_grade_css_class = f"grade-{main_grade.grade.color.lower().replace(' ', '-')}" if main_grade.grade.color else 'grade-cap-blanc'
                        practitioner.computed_grade_color = main_grade.grade.color_code or '#6c757d'
                    elif practitioner.grade:
                        # Fallback sur le champ grade du pratiquant
                        practitioner.computed_grade_display = practitioner.grade if isinstance(practitioner.grade, str) else getattr(practitioner.grade, 'name', '')
                        practitioner.computed_grade_css_class = 'grade-cap-blanc'
                        practitioner.computed_grade_color = '#6c757d'
                    else:
                        practitioner.computed_grade_display = ''
                        practitioner.computed_grade_css_class = 'grade-cap-blanc'
                        practitioner.computed_grade_color = '#6c757d'
            except ImportError:
                # Si le module grades n'est pas disponible, utiliser le champ grade simple
                for practitioner in all_practitioners:
                    if practitioner.grade:
                        practitioner.computed_grade_display = practitioner.grade if isinstance(practitioner.grade, str) else getattr(practitioner.grade, 'name', '')
                    else:
                        practitioner.computed_grade_display = ''
                    practitioner.computed_grade_css_class = 'grade-cap-blanc'
                    practitioner.computed_grade_color = '#6c757d'
            except Exception as e:
                logger.warning(f"Erreur lors du chargement des grades pour les pratiquants: {str(e)}")
                for practitioner in all_practitioners:
                    practitioner.computed_grade_display = getattr(practitioner, 'grade', '') or ''
                    practitioner.computed_grade_css_class = 'grade-cap-blanc'
                    practitioner.computed_grade_color = '#6c757d'
        except Exception as e:
            logger.error(_("Erreur lors de la récupération de tous les pratiquants: {}").format(str(e)))
            all_practitioners = Practitioner.objects.none()
    else:
        all_practitioners = Practitioner.objects.none()

    # Calculer les statistiques détaillées des membres par catégorie d'âge et genre
    member_statistics = {}
    grade_distribution = {}
    try:
        if club_organization:
            # Récupérer TOUS les pratiquants de l'organisation pour les statistiques complètes
            # (sans filtre discipline pour inclure tous les membres du club)
            from apps.competitions.models import Practitioner as PractitionerModel
            practitioners_for_stats = PractitionerModel.objects.filter(organization=club_organization)
            member_statistics = calculate_member_statistics(practitioners_for_stats)
            grade_distribution = get_grade_distribution(practitioners_for_stats)
        else:
            member_statistics = {
                'total': 0,
                'total_female': 0,
                'total_male': 0,
                'total_unknown_gender': 0,
                'categories': [],
                'encadrement': {'total': 0, 'qualifications': []}
            }
            grade_distribution = {
                'beginners': {'count': 0, 'percentage': 0},
                'intermediates': {'count': 0, 'percentage': 0},
                'advanced': {'count': 0, 'percentage': 0},
            }
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques membres: {str(e)}")
        member_statistics = {
            'total': 0,
            'total_female': 0,
            'total_male': 0,
            'total_unknown_gender': 0,
            'categories': [],
            'encadrement': {'total': 0, 'qualifications': []}
        }
        grade_distribution = {
            'beginners': {'count': 0, 'percentage': 0},
            'intermediates': {'count': 0, 'percentage': 0},
            'advanced': {'count': 0, 'percentage': 0},
        }

    # Récupérer les affectations des juges si disponible
    judge_assignments = []
    try:
        from ...models import JudgeAssignment
        if club_organization:
            judge_assignments = JudgeAssignment.objects.filter(
                registration__practitioner__organization=club_organization,
                category__competition__end_date__gte=now
            ).select_related(
                'registration__practitioner',
                'category__competition'
            ).order_by('category__competition__start_date')[:10]
        else:
            judge_assignments = JudgeAssignment.objects.none()
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des affectations: {}").format(str(e)))
    
    # Informations de configuration (non invasives)
    club_setup_info = []
    if not upcoming_competitions_ids or len(upcoming_competitions_ids) == 0:
        if not club_disciplines or len(club_disciplines) == 0:
            club_setup_info.append({
                'type': 'discipline',
                'message': _("Votre club n'a pas encore de discipline assignée. Veuillez configurer les disciplines pour voir les compétitions disponibles."),
                'action_url': '#',  # TODO: Ajouter URL vers configuration disciplines
                'action_text': _("Configurer les disciplines")
            })
    
    if stats['total_practitioners'] == 0:
        club_setup_info.append({
            'type': 'practitioners',
            'message': _("Vous n'avez pas encore de pratiquants dans votre club. Commencez par ajouter des membres."),
            'action_url': '#',  # TODO: Ajouter URL vers ajout de pratiquants
            'action_text': _("Ajouter des membres")
        })
    
    # Récupérer les paiements récents
    recent_payments = []
    try:
        from apps.finances.models import PaymentAttempt
        # Obtenir les pratiquants du club (filtrés par disciplines)
        if club_organization:
            club_practitioners = filter_practitioners_by_org_disciplines(club_organization)
            practitioner_users = set(club_practitioners.values_list('user_id', flat=True).distinct())
            
            # Obtenir les paiements récents pour les pratiquants du club
            recent_payments = PaymentAttempt.objects.filter(
                transaction__created_by__id__in=practitioner_users
            ).select_related('transaction', 'transaction__created_by', 'payment_method', 'transaction__category'
            ).order_by('-initiated_at')[:10]
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des paiements récents: {}").format(str(e)))

    # Récupérer les sessions d'entraînement récentes et programmes
    recent_sessions = []
    attendance_stats = {}
    top_attendees = []
    training_programs = []
    training_programs_count = 0
    
    try:
        from datetime import timedelta
        
        # Programmes d'entraînement actifs
        # Utiliser raw SQL pour éviter modeltranslation sur les disciplines
        training_programs = TrainingProgram.objects.filter(
            is_active=True
        )[:5]
        # Recharger les disciplines avec raw SQL pour éviter modeltranslation
        for program in training_programs:
            if hasattr(program, 'disciplines'):
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT d.id 
                        FROM competitions_discipline d
                        INNER JOIN competitions_trainingprogram_disciplines td ON d.id = td.discipline_id
                        WHERE td.trainingprogram_id = %s
                    """, [program.id])
                    discipline_ids = [row[0] for row in cursor.fetchall()]
                from ...models import Discipline
                # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
                program.disciplines_list = []  # Sera rempli plus tard si nécessaire
                # Note: Les disciplines seront chargées via le template si nécessaire
        training_programs_count = TrainingProgram.objects.filter(is_active=True).count()
        
        # Sessions récentes du club - Utiliser raw SQL pour éviter modeltranslation
        club_id = club_data_dict['id'] if club_data_dict else None
        if club_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT ts.id 
                    FROM competitions_trainingsession ts
                    INNER JOIN competitions_trainingslot tsl ON ts.training_slot_id = tsl.id
                    WHERE tsl.club_id = %s
                    AND ts.date >= %s
                    ORDER BY ts.date DESC
                    LIMIT 10
                """, [club_id, now - timedelta(days=30)])
                session_ids = [row[0] for row in cursor.fetchall()]
            # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
            recent_sessions = []  # Sera rempli plus tard si nécessaire
            # Note: Les sessions seront chargées via le template si nécessaire
        else:
            recent_sessions = []
        # Recharger les disciplines avec raw SQL pour éviter modeltranslation
        for session in recent_sessions:
            if hasattr(session, 'training_slot') and hasattr(session.training_slot, 'discipline_id') and session.training_slot.discipline_id:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, description 
                        FROM competitions_discipline
                        WHERE id = %s
                    """, [session.training_slot.discipline_id])
                    row = cursor.fetchone()
                    if row:
                        from ...models import Discipline
                        session.training_slot.discipline = Discipline(id=row[0], name=row[1], description=row[2] if len(row) > 2 else '')
                    else:
                        session.training_slot.discipline = None
        
        # Calculer les statistiques pour chaque session
        for session in recent_sessions:
            attendance_data = Attendance.objects.filter(session=session).aggregate(
                total_count=Count('id'),
                presents_count=Count('id', filter=Q(status='present')),
            )
            session.total_count = attendance_data['total_count']
            session.presents_count = attendance_data['presents_count']
            session.attendance_rate = (session.presents_count / session.total_count * 100) if session.total_count > 0 else 0
        
        # Statistiques globales
        month_start = now.replace(day=1)
        # Utiliser raw SQL pour éviter modeltranslation
        club_id = club_data_dict['id'] if club_data_dict else None
        if club_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM competitions_trainingsession ts
                    INNER JOIN competitions_trainingslot tsl ON ts.training_slot_id = tsl.id
                    WHERE tsl.club_id = %s
                    AND ts.date >= %s
                """, [club_id, month_start])
                attendance_stats['month_sessions'] = cursor.fetchone()[0]
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM competitions_attendance a
                    INNER JOIN competitions_trainingsession ts ON a.session_id = ts.id
                    INNER JOIN competitions_trainingslot tsl ON ts.training_slot_id = tsl.id
                    WHERE tsl.club_id = %s
                    AND a.status = 'present'
                """, [club_id])
                attendance_stats['total_attendances'] = cursor.fetchone()[0]
            
            # Taux de présence moyen - Utiliser raw SQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COALESCE(AVG(CASE WHEN a.status = 'present' THEN 100.0 ELSE 0.0 END), 0) as avg_rate
                    FROM competitions_trainingsession ts
                    INNER JOIN competitions_trainingslot tsl ON ts.training_slot_id = tsl.id
                    LEFT JOIN competitions_attendance a ON ts.id = a.session_id
                    WHERE tsl.club_id = %s
                    AND ts.date >= %s
                """, [club_id, now - timedelta(days=30)])
                avg_rate = cursor.fetchone()[0] or 0
                attendance_stats['average_rate'] = avg_rate
            
            # Top pratiquants assidus - Utiliser raw SQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        a.practitioner_id,
                        p.last_name,
                        p.first_name,
                        COUNT(*) as attendance_count
                    FROM competitions_attendance a
                    INNER JOIN competitions_trainingsession ts ON a.session_id = ts.id
                    INNER JOIN competitions_trainingslot tsl ON ts.training_slot_id = tsl.id
                    INNER JOIN competitions_practitioner p ON a.practitioner_id = p.id
                    WHERE tsl.club_id = %s
                    AND a.status = 'present'
                    AND ts.date >= %s
                    GROUP BY a.practitioner_id, p.last_name, p.first_name
                    ORDER BY attendance_count DESC
                    LIMIT 5
                """, [club_id, now - timedelta(days=30)])
                top_attendees = []
                for row in cursor.fetchall():
                    top_attendees.append({
                        'practitioner': type('obj', (object,), {'id': row[0]})(),
                        'practitioner__last_name': row[1],
                        'practitioner__first_name': row[2],
                        'attendance_count': row[3]
                    })
        else:
            attendance_stats['month_sessions'] = 0
            attendance_stats['total_attendances'] = 0
            attendance_stats['average_rate'] = 0
            top_attendees = []
        
        # Ajouter le nom complet pour chaque pratiquant
        for attendee in top_attendees:
            attendee['practitioner'] = type('obj', (object,), {
                'full_name': f"{attendee['practitioner__first_name']} {attendee['practitioner__last_name']}"
            })
        
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des données d'entraînement: {}").format(str(e)))

    # Récupérer les commandes en ligne récentes et statistiques boutique complètes
    recent_orders = []
    order_stats = {}
    shop_stats = {}
    popular_products = []
    try:
        from apps.shop.models import Order, OrderItem, Product
        from django.db.models import Sum, Count, F
        
        # Commandes récentes du club - Utiliser raw SQL pour éviter modeltranslation
        club_id = club_data_dict['id'] if club_data_dict else None
        if club_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id
                    FROM shop_order
                    WHERE club_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10
                """, [club_id])
                order_ids = [row[0] for row in cursor.fetchall()]
            # Charger les objets Order via ORM en préservant l'ordre
            if order_ids:
                recent_orders = list(Order.objects.filter(id__in=order_ids).select_related('user').order_by('-created_at'))
            else:
                recent_orders = []
            
            # Statistiques des commandes
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM shop_order
                    WHERE club_id = %s
                    GROUP BY status
                """, [club_id])
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM shop_order
                    WHERE club_id = %s
                """, [club_id])
                total_orders = cursor.fetchone()[0]
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0)
                    FROM shop_order
                    WHERE club_id = %s
                    AND status IN ('delivered', 'shipped', 'processing')
                """, [club_id])
                total_revenue = cursor.fetchone()[0] or 0
            
            order_stats['total_orders'] = total_orders
            order_stats['pending_orders'] = status_counts.get('pending', 0)
            order_stats['processing_orders'] = status_counts.get('processing', 0)
            order_stats['total_revenue'] = total_revenue
            pending_orders = status_counts.get('pending', 0)
        else:
            recent_orders = []
            order_stats['total_orders'] = 0
            order_stats['pending_orders'] = 0
            order_stats['processing_orders'] = 0
            order_stats['total_revenue'] = 0
            pending_orders = 0
            total_orders = 0
            total_revenue = 0
        
        # Statistiques des produits
        # Utiliser raw SQL pour éviter modeltranslation
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT discipline_id 
                FROM competitions_club_disciplines 
                WHERE club_id = %s
            """, [club_data_dict['id'] if club_data_dict else None])
            discipline_ids = [row[0] for row in cursor.fetchall()]
        if discipline_ids:
            club_products = Product.objects.filter(disciplines__in=discipline_ids, is_active=True).distinct()
        else:
            club_products = Product.objects.filter(is_active=True)
        
        active_products = club_products.count()
        low_stock_products = club_products.filter(stock_quantity__lte=F('low_stock_threshold')).count()
        out_of_stock = club_products.filter(stock_quantity=0).count()
        
        shop_stats = {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'active_products': active_products,
            'low_stock_products': low_stock_products,
            'out_of_stock': out_of_stock
        }
        
        # Produits populaires (basés sur les ventes du club) - limité aux 30 derniers jours
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        popular_products = (
            OrderItem.objects
            .filter(order__club_id=club.id if club else None, order__created_at__gte=thirty_days_ago)
            .values('product_name')
            .annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum(F('price') * F('quantity'))
            )
            .order_by('-total_revenue')[:5]
        )
        
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des commandes: {}").format(str(e)))
        shop_stats = {
            'total_orders': 0,
            'total_revenue': 0,
            'pending_orders': 0,
            'active_products': 0,
            'low_stock_products': 0,
            'out_of_stock': 0
        }

    # Récupérer les notifications récentes
    recent_notifications = []
    unread_count = 0
    try:
        from datetime import timedelta
        from ...models import Notification
        
        # Toutes les notifications récentes
        recent_notifications = Notification.objects.filter(
            user=request.user,
            created_at__gte=now - timedelta(days=30)
        ).order_by('-created_at')[:10]
        
        # Nombre de notifications non lues
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des notifications: {}").format(str(e)))
        recent_notifications = []
        unread_count = 0

    # Récupérer les tickets de support récents
    recent_tickets = []
    ticket_stats = {}
    try:
        from ...models import SupportTicket
        
        # Tickets récents créés par les pratiquants du club (filtrés par disciplines)
        if club_organization:
            club_practitioners = filter_practitioners_by_org_disciplines(club_organization)
            practitioner_users = set(club_practitioners.values_list('user_id', flat=True).distinct())
            
            recent_tickets = SupportTicket.objects.filter(
                user__id__in=practitioner_users
            ).order_by('-created_at')[:10]
            
            # Statistiques des tickets
            ticket_counts = SupportTicket.objects.filter(
                user__id__in=practitioner_users
            ).values('status').annotate(count=Count('id'))
            status_counts = {item['status']: item['count'] for item in ticket_counts}
            
            ticket_stats['total_tickets'] = SupportTicket.objects.filter(user__id__in=practitioner_users).count()
            ticket_stats['open_tickets'] = status_counts.get('open', 0)
            ticket_stats['in_progress_tickets'] = status_counts.get('in_progress', 0)
            ticket_stats['resolved_tickets'] = status_counts.get('resolved', 0)
            
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des tickets de support: {}").format(str(e)))

    # Récupérer les données financières (utilise l'owner des comptes financiers de l'organisation)
    # MULTI-DEVISE: Détection de la devise préférée de l'utilisateur
    try:
        from apps.finances.currency_service import (
            get_preferred_currency_for_request,
            convert_amount,
        )
        preferred_currency, currency_source = get_preferred_currency_for_request(request)
    except Exception:
        preferred_currency = 'EUR'
        currency_source = 'default'

    financial_stats = {
        'balance': 0,
        'income': 0,
        'expense': 0,
        'pending_invoices': 0,
        'currency': preferred_currency,
        'base_currency': 'EUR',  # Devise de stockage en base
    }
    try:
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Sum
        from apps.finances.models.accounts import FinancialAccount
        from apps.finances.models.transactions import Transaction
        from apps.finances.models.invoices import Invoice
        if club_organization:
            ct = ContentType.objects.get_for_model(club_organization.__class__)
            owner_id = str(getattr(club_organization, 'id', ''))
            org_accounts = FinancialAccount.objects.filter(owner_content_type=ct, owner_id=owner_id)

            # Récupérer les montants en EUR (devise de base)
            balance_eur = float(org_accounts.aggregate(total=Sum('current_balance'))['total'] or 0)

            tx = Transaction.objects.filter(financial_account__in=org_accounts, status__in=['validated', 'pending'])
            income_eur = float(tx.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0)
            expense_eur = float(tx.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0)

            inv = Invoice.objects.filter(
                issuer_content_type=ct, issuer_object_id=owner_id
            )
            financial_stats['pending_invoices'] = inv.exclude(status='paid').count()

            # MULTI-DEVISE: Convertir les montants vers la devise préférée
            if preferred_currency != 'EUR':
                try:
                    from apps.finances.currency_service import convert_amount
                    balance_converted, _rate = convert_amount(balance_eur, 'EUR', preferred_currency)
                    income_converted, _rate = convert_amount(income_eur, 'EUR', preferred_currency)
                    expense_converted, _rate = convert_amount(expense_eur, 'EUR', preferred_currency)

                    financial_stats['balance'] = float(balance_converted)
                    financial_stats['income'] = float(income_converted)
                    financial_stats['expense'] = float(expense_converted)
                    # Conserver les valeurs EUR originales pour référence
                    financial_stats['balance_eur'] = balance_eur
                    financial_stats['income_eur'] = income_eur
                    financial_stats['expense_eur'] = expense_eur
                except Exception as conv_error:
                    logger.warning(f"Erreur conversion devise: {conv_error}, utilisation EUR")
                    financial_stats['balance'] = balance_eur
                    financial_stats['income'] = income_eur
                    financial_stats['expense'] = expense_eur
                    financial_stats['currency'] = 'EUR'
            else:
                financial_stats['balance'] = balance_eur
                financial_stats['income'] = income_eur
                financial_stats['expense'] = expense_eur
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des données financières: {}").format(str(e)))

    # Récupérer les événements et sondages
    event_stats = {
        'upcoming_count': 0,
        'active_polls': 0,
        'month_events': 0,
        'attendance_rate': 75
    }
    
    upcoming_events = []
    past_events = []
    recent_events = []
    active_polls = []
    
    try:
        from ...models import Event
        from datetime import timedelta
        if club_organization:
            # Récupérer les événements à venir
            upcoming_events = Event.objects.filter(
                organization=club_organization,
                start_date__gte=timezone.now().date(),
                is_archived=False
            ).order_by('start_date')[:5]
            
            # Récupérer les événements passés
            past_events = Event.objects.filter(
                organization=club_organization,
                start_date__lt=timezone.now().date(),
                is_archived=False
            ).order_by('-start_date')[:5]

            # Récupérer les événements récents
            recent_events = Event.objects.filter(
                organization=club_organization,
                is_archived=False
            ).order_by('-created_at')[:3]
            
            # Calculer les statistiques
            # Note: Event peut ne pas avoir de champ discipline, donc on filtre seulement par organisation
            event_stats.update({
                'upcoming_count': upcoming_events.count(),
                'total_events': Event.objects.filter(organization=club_organization).count(),
                'month_events': Event.objects.filter(
                    organization=club_organization,
                    start_date__gte=timezone.now().date(),
                    start_date__lt=timezone.now().date() + timedelta(days=30)
                ).count()
            })
            
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des événements: {}").format(str(e)))

    # Récupérer les statistiques de combat
    combat_stats = {
        'total_combats': 0,
        'month_combats': 0,
        'victories': 0,
        'defeats': 0,
        'win_rate': 0
    }
    
    recent_combats = []
    club_teams = []
    club_teams_count = 0
    
    try:
        from ...models.combat import Combat, Equipe
        if club_organization:
            # Combats récents
            # Utiliser raw SQL pour éviter modeltranslation
            club_id = club_data_dict['id'] if club_data_dict else None
            org_id = club_organization.id if club_organization else None
            with connection.cursor() as cursor:
                if club_id and org_id:
                    cursor.execute("""
                        SELECT c.id 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s OR p1.organization_id = %s OR p2.organization_id = %s)
                        ORDER BY c.created_at DESC
                        LIMIT 10
                    """, [club_id, club_id, org_id, org_id])
                elif club_id:
                    cursor.execute("""
                        SELECT c.id 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s)
                        ORDER BY c.created_at DESC
                        LIMIT 10
                    """, [club_id, club_id])
                elif org_id:
                    cursor.execute("""
                        SELECT c.id 
                        FROM competitions_combat c
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (p1.organization_id = %s OR p2.organization_id = %s)
                        ORDER BY c.created_at DESC
                        LIMIT 10
                    """, [org_id, org_id])
                else:
                    combat_ids = []
                    cursor = None
                if cursor:
                    combat_ids = [row[0] for row in cursor.fetchall()]
                else:
                    combat_ids = []
            # Ne pas utiliser ORM pour éviter modeltranslation - utiliser directement les IDs
            recent_combats = []  # Sera rempli plus tard si nécessaire
            # Note: Les combats seront chargés via le template si nécessaire
            
            # Équipes du club - Utiliser raw SQL pour éviter modeltranslation
            club_id = club_data_dict['id'] if club_data_dict else None
            if club_id:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id 
                        FROM competitions_equipe
                        WHERE club_id = %s
                        LIMIT 5
                    """, [club_id])
                    team_ids = [row[0] for row in cursor.fetchall()]
                club_teams = Equipe.objects.filter(id__in=team_ids).select_related('competition')[:5]
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_equipe
                        WHERE club_id = %s
                    """, [club_id])
                    club_teams_count = cursor.fetchone()[0]
            else:
                club_teams = []
                club_teams_count = 0
            
            # Statistiques - Utiliser raw SQL pour éviter modeltranslation
            club_id = club_data_dict['id'] if club_data_dict else None
            org_id = club_organization.id if club_organization else None
            with connection.cursor() as cursor:
                if club_id and org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s OR p1.organization_id = %s OR p2.organization_id = %s)
                    """, [club_id, club_id, org_id, org_id])
                elif club_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s)
                    """, [club_id, club_id])
                elif org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (p1.organization_id = %s OR p2.organization_id = %s)
                    """, [org_id, org_id])
                else:
                    total_combats = 0
                    cursor = None
                if cursor:
                    total_combats = cursor.fetchone()[0]
                else:
                    total_combats = 0
            
            # Combats ce mois
            from datetime import timedelta
            # Utiliser raw SQL pour éviter modeltranslation
            club_id = club_data_dict['id'] if club_data_dict else None
            org_id = club_organization.id if club_organization else None
            month_start = timezone.now().date() - timedelta(days=30)
            
            with connection.cursor() as cursor:
                if club_id and org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s OR p1.organization_id = %s OR p2.organization_id = %s)
                        AND c.created_at >= %s
                    """, [club_id, club_id, org_id, org_id, month_start])
                elif club_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        WHERE (e1.club_id = %s OR e2.club_id = %s)
                        AND c.created_at >= %s
                    """, [club_id, club_id, month_start])
                elif org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE (p1.organization_id = %s OR p2.organization_id = %s)
                        AND c.created_at >= %s
                    """, [org_id, org_id, month_start])
                else:
                    month_combats = 0
                    cursor = None
                if cursor:
                    month_combats = cursor.fetchone()[0]
                else:
                    month_combats = 0
            
            # Calcul victoires/défaites - Utiliser raw SQL
            with connection.cursor() as cursor:
                if club_id and org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE ((e1.club_id = %s AND c.vainqueur = 'rouge') OR 
                               (e2.club_id = %s AND c.vainqueur = 'blanc') OR
                               (p1.organization_id = %s AND c.vainqueur = 'rouge') OR
                               (p2.organization_id = %s AND c.vainqueur = 'blanc'))
                        AND c.status = 'termine'
                    """, [club_id, club_id, org_id, org_id])
                elif club_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        WHERE ((e1.club_id = %s AND c.vainqueur = 'rouge') OR 
                               (e2.club_id = %s AND c.vainqueur = 'blanc'))
                        AND c.status = 'termine'
                    """, [club_id, club_id])
                elif org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE ((p1.organization_id = %s AND c.vainqueur = 'rouge') OR
                               (p2.organization_id = %s AND c.vainqueur = 'blanc'))
                        AND c.status = 'termine'
                    """, [org_id, org_id])
                else:
                    victories = 0
                    cursor = None
                if cursor:
                    victories = cursor.fetchone()[0]
                else:
                    victories = 0
            
            with connection.cursor() as cursor:
                if club_id and org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE ((e1.club_id = %s AND c.vainqueur = 'blanc') OR 
                               (e2.club_id = %s AND c.vainqueur = 'rouge') OR
                               (p1.organization_id = %s AND c.vainqueur = 'blanc') OR
                               (p2.organization_id = %s AND c.vainqueur = 'rouge'))
                        AND c.status = 'termine'
                    """, [club_id, club_id, org_id, org_id])
                elif club_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_equipe e1 ON c.equipe_rouge_id = e1.id
                        LEFT JOIN competitions_equipe e2 ON c.equipe_blanc_id = e2.id
                        WHERE ((e1.club_id = %s AND c.vainqueur = 'blanc') OR 
                               (e2.club_id = %s AND c.vainqueur = 'rouge'))
                        AND c.status = 'termine'
                    """, [club_id, club_id])
                elif org_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM competitions_combat c
                        LEFT JOIN competitions_practitioner p1 ON c.pratiquant_rouge_id = p1.id
                        LEFT JOIN competitions_practitioner p2 ON c.pratiquant_blanc_id = p2.id
                        WHERE ((p1.organization_id = %s AND c.vainqueur = 'blanc') OR
                               (p2.organization_id = %s AND c.vainqueur = 'rouge'))
                        AND c.status = 'termine'
                    """, [org_id, org_id])
                else:
                    defeats = 0
                    cursor = None
                if cursor:
                    defeats = cursor.fetchone()[0]
                else:
                    defeats = 0
            
            win_rate = (victories * 100) // (victories + defeats) if (victories + defeats) > 0 else 0
            
            combat_stats.update({
                'total_combats': total_combats,
                'month_combats': month_combats,
                'victories': victories,
                'defeats': defeats,
                'win_rate': win_rate
            })
            
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des combats: {}").format(str(e)))
    
    # Récupérer les statistiques de documents
    document_stats = {
        'my_documents': 0,
        'shared_with_me': 0,
        'total_size': 0,
        'recent_uploads': 0,
        'certificates': 0,
        'administrative': 0,
        'technical': 0,
        'certificates_percent': 0,
        'administrative_percent': 0,
        'technical_percent': 0
    }
    
    recent_documents = []
    
    try:
        from apps.documents.models import Document
        
        # Documents de l'utilisateur
        user_documents = Document.objects.filter(
            created_by=request.user,
            is_latest_version=True
        )
        
        # Documents récents
        recent_documents = user_documents.order_by('-created_at')[:10]
        
        # Calcul des statistiques
        my_documents_count = user_documents.count()
        shared_with_me = Document.objects.filter(
            shares__user=request.user
        ).distinct().count()
        
        total_size = sum(doc.file_size for doc in user_documents if doc.file_size)
        
        # Documents cette semaine
        from datetime import timedelta
        recent_uploads = user_documents.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Par type
        certificates = user_documents.filter(document_type='certificate').count()
        administrative = user_documents.filter(document_type='administrative').count()
        technical = user_documents.filter(document_type='technical').count()
        
        # Pourcentages
        if my_documents_count > 0:
            certificates_percent = (certificates * 100) // my_documents_count
            administrative_percent = (administrative * 100) // my_documents_count
            technical_percent = (technical * 100) // my_documents_count
        else:
            certificates_percent = administrative_percent = technical_percent = 0
        
        document_stats.update({
            'my_documents': my_documents_count,
            'shared_with_me': shared_with_me,
            'total_size': total_size,
            'recent_uploads': recent_uploads,
            'certificates': certificates,
            'administrative': administrative,
            'technical': technical,
            'certificates_percent': certificates_percent,
            'administrative_percent': administrative_percent,
            'technical_percent': technical_percent
        })
        
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des documents: {}").format(str(e)))

    # Récupérer les données d'adhésion (NOUVEAU - MartialComp v2.0)
    membership_stats = {}
    recent_subscriptions = []
    membership_alerts = []
    
    try:
        from apps.membership.services import MembershipService, MembershipAnalyticsService
        from apps.membership.models import MembershipSubscription, MembershipAlert
        
        if club_organization:
            # Statistiques principales des adhésions
            membership_stats = MembershipService.get_membership_stats(club_organization)
            
            # Souscriptions récentes
            recent_subscriptions = MembershipSubscription.objects.filter(
                package__organization=club_organization
            ).select_related('practitioner', 'package').order_by('-created_at')[:10]
            
            # Alertes d'adhésion non résolues
            membership_alerts = MembershipAlert.objects.filter(
                subscription__package__organization=club_organization,
                is_resolved=False
            ).order_by('-created_at')[:5]
            
            # Analytics avancées
            membership_stats['popular_packages'] = MembershipAnalyticsService.get_popular_packages(club_organization)
            membership_stats['revenue_trend'] = MembershipAnalyticsService.get_revenue_trend(club_organization, 6)
            membership_stats['retention_rate'] = MembershipAnalyticsService.get_retention_rate(club_organization)
            
            logger.info(f"Données d'adhésion chargées pour {club_organization}: {len(recent_subscriptions)} souscriptions")
            
    except ImportError:
        logger.warning("Module membership non disponible - utilisation des données par défaut")
        membership_stats = {
            'total_active': 0,
            'total_packages': 0,
            'expiring_soon': 0,
            'revenue_this_month': 0,
            'new_this_month': 0,
            'package_distribution': {},
            'popular_packages': [],
            'revenue_trend': [],
            'retention_rate': {'retention_rate': 0}
        }
    except Exception as e:
        logger.error(_("Erreur lors de la récupération des données d'adhésion: {}").format(str(e)))
        membership_stats = {
            'total_active': 0,
            'total_packages': 0,
            'expiring_soon': 0,
            'revenue_this_month': 0,
            'new_this_month': 0,
            'package_distribution': {},
            'popular_packages': [],
            'revenue_trend': [],
            'retention_rate': {'retention_rate': 0}
        }

    # Récupérer les invitations d'affiliation en attente (NOUVEAU)
    pending_federation_invitations = []
    affiliation_stats = {
        'pending_invitations': 0,
        'active_affiliations': 0,
        'pending_requests': 0
    }
    
    try:
        from apps.organizations.models import Affiliation
        
        if club_organization:
            # Invitations recues de federations (en attente d'approbation du club)
            pending_invitations_qs = Affiliation.objects.filter(
                child_organization=club_organization,
                initiated_by='parent',
                parent_status='approved',
                child_status='pending',
                is_active=False
            ).select_related('parent_organization')
            
            pending_federation_invitations = list(pending_invitations_qs)
            affiliation_stats['pending_invitations'] = len(pending_federation_invitations)
            
            # Affiliations actives
            active_affiliations_count = Affiliation.objects.filter(
                child_organization=club_organization,
                is_active=True
            ).count()
            affiliation_stats['active_affiliations'] = active_affiliations_count
            
            # Demandes envoyees par le club (en attente)
            pending_requests_count = Affiliation.objects.filter(
                child_organization=club_organization,
                initiated_by='child',
                child_status='approved',
                parent_status='pending',
                is_active=False
            ).count()
            affiliation_stats['pending_requests'] = pending_requests_count
            
            logger.info(f"Affiliations pour {club_organization}: {affiliation_stats}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des affiliations: {e}")

    # Récupérer les données de gestion de tâches
    task_data = {}
    if TASK_MANAGEMENT_AVAILABLE:
        try:
            # Données générales des tâches de l'utilisateur
            task_data = get_dashboard_task_data(request.user, limit_tasks=5, limit_boards=3)
            
            # Données spécifiques au club si organisation disponible
            if club_organization:
                club_task_data = get_club_dashboard_task_data(request.user, club_organization)
                task_data.update(club_task_data)
                
        except Exception as e:
            logger.error(_("Erreur lors de la récupération des données de tâches: {}").format(str(e)))
            task_data = {'has_access': False}

    # Assurer un contexte minimal fonctionnel
    base_context = {
        'club': club,
        'club_found_via': club_found_via,
        'club_organization': club_organization if 'club_organization' in locals() else None,
        'stats': {
            'total_practitioners': 0,
            'active_registrations': 0,
            'club_competitions': 0,
            'judges_count': 0
        },
        'financial_stats': {
            'balance': 0,
            'income': 0,
            'expense': 0,
            'pending_invoices': 0
        },
        'event_stats': {
            'upcoming_count': 0,
            'active_polls': 0,
            'month_events': 0,
            'attendance_rate': 75
        },
        'combat_stats': {
            'total_combats': 0,
            'month_combats': 0,
            'victories': 0,
            'defeats': 0,
            'win_rate': 0
        },
        'upcoming_events': [],
        'active_polls': [],
        'upcoming_competitions': [],
        'competitions_to_manage': [],
        'competitions_to_manage_count': 0,
        'recent_practitioners': [],
        'recent_registrations': [],
        'club_disciplines': [],
        'judge_assignments': [],
        'recent_payments': [],
        'recent_sessions': [],
        'attendance_stats': {},
        'top_attendees': [],
        'training_programs': [],
        'training_programs_count': 0,
        'recent_orders': [],
        'order_stats': {},
        'shop_stats': {
            'total_orders': 0,
            'total_revenue': 0,
            'pending_orders': 0,
            'active_products': 0,
            'low_stock_products': 0,
            'out_of_stock': 0
        },
        'popular_products': [],
        'recent_notifications': [],
        'unread_count': 0,
        'recent_tickets': [],
        'ticket_stats': {},
        'current_date': now,
        'page_title': _("Tableau de bord du club"),
        'section': 'dashboard',
        # Valeurs par défaut pour les nouveaux onglets
        'recent_combats': [],
        'club_teams': [],
        'club_teams_count': 0,
        'document_stats': {
            'my_documents': 0,
            'shared_with_me': 0,
            'total_size': 0,
            'recent_uploads': 0,
            'certificates': 0,
            'administrative': 0,
            'technical': 0,
            'certificates_percent': 0,
            'administrative_percent': 0,
            'technical_percent': 0
        },
        'recent_documents': [],
        # Données d'affiliation par defaut
        'pending_federation_invitations': [],
        'affiliation_stats': {
            'pending_invitations': 0,
            'active_affiliations': 0,
            'pending_requests': 0
        },
        'subscription_info': None,
    }
    
    # Convertir les IDs en objets simples pour le template (éviter modeltranslation)
    
    # Fonction helper pour charger les données de compétition
    def load_competition_data(comp_ids):
        if not comp_ids:
            return []
        
        competitions_data = []
        with connection.cursor() as cursor:
            for comp_id in comp_ids:
                try:
                    cursor.execute("""
                        SELECT c.id, c.title, c.start_date, c.end_date, c.status,
                               c.venue_name, c.city, c.registration_deadline,
                               d.id as discipline_id, d.name as discipline_name
                        FROM competitions_competition c
                        LEFT JOIN competitions_discipline d ON c.discipline_id = d.id
                        WHERE c.id = %s
                    """, [comp_id])
                    row = cursor.fetchone()
                    if row:
                        # Créer un objet simple avec les données nécessaires
                        comp = type('Competition', (), {
                            'id': row[0],
                            'title': row[1],
                            'start_date': row[2],
                            'end_date': row[3],
                            'status': row[4],
                            'venue_name': row[5] or '',
                            'city': row[6] or '',
                            'registration_deadline': row[7],
                            'discipline': type('Discipline', (), {
                                'id': row[8],
                                'name': row[9]
                            })() if row[8] else None
                        })()
                        competitions_data.append(comp)
                except Exception as e:
                    logger.error(_("Erreur lors du chargement de la compétition {}: {}").format(comp_id, str(e)))
        return competitions_data
    
    # Convertir competitions_to_manage
    if isinstance(competitions_to_manage, list) and competitions_to_manage:
        competitions_to_manage = load_competition_data(competitions_to_manage)
    else:
        competitions_to_manage = []
    
    # Convertir club_competitions_ids
    if 'club_competitions_ids' in locals() and club_competitions_ids:
        club_competitions = load_competition_data(club_competitions_ids)
    else:
        club_competitions = []
    
    # Convertir upcoming_competitions_ids
    if 'upcoming_competitions_ids' in locals() and upcoming_competitions_ids:
        upcoming_competitions = load_competition_data(upcoming_competitions_ids)
    else:
        upcoming_competitions = []

    # ==========================================================================
    # MULTI-DEVISE: Conversion des montants financiers dans shop_stats, order_stats, membership_stats
    # ==========================================================================
    if preferred_currency != 'EUR':
        try:
            from apps.finances.currency_service import convert_amount as conv_amount

            # Convertir shop_stats
            if shop_stats.get('total_revenue'):
                converted_rev, _rate = conv_amount(float(shop_stats['total_revenue']), 'EUR', preferred_currency)
                shop_stats['total_revenue_eur'] = shop_stats['total_revenue']
                shop_stats['total_revenue'] = float(converted_rev)

            # Convertir order_stats
            if order_stats.get('total_revenue'):
                converted_ord_rev, _rate = conv_amount(float(order_stats['total_revenue']), 'EUR', preferred_currency)
                order_stats['total_revenue_eur'] = order_stats['total_revenue']
                order_stats['total_revenue'] = float(converted_ord_rev)

            # Convertir membership_stats
            if membership_stats.get('revenue_this_month'):
                converted_mem_rev, _rate = conv_amount(float(membership_stats['revenue_this_month']), 'EUR', preferred_currency)
                membership_stats['revenue_this_month_eur'] = membership_stats['revenue_this_month']
                membership_stats['revenue_this_month'] = float(converted_mem_rev)

            if membership_stats.get('total_revenue'):
                converted_total_mem, _rate = conv_amount(float(membership_stats['total_revenue']), 'EUR', preferred_currency)
                membership_stats['total_revenue_eur'] = membership_stats['total_revenue']
                membership_stats['total_revenue'] = float(converted_total_mem)

            # Convertir popular_products (si présent)
            if 'popular_products' in locals() and popular_products:
                for product in popular_products:
                    if product.get('total_revenue'):
                        conv_prod_rev, _rate = conv_amount(float(product['total_revenue']), 'EUR', preferred_currency)
                        product['total_revenue_eur'] = product['total_revenue']
                        product['total_revenue'] = float(conv_prod_rev)

        except Exception as conv_err:
            logger.warning(f"Erreur conversion multi-devise shop/membership: {conv_err}")

    # Ajouter la devise aux stats pour l'affichage dans le template
    shop_stats['currency'] = preferred_currency
    order_stats['currency'] = preferred_currency
    membership_stats['currency'] = preferred_currency

    # Préparer le contexte pour le template
    context = {
        'club': club,
        'club_found_via': club_found_via,
        'club_organization': club_organization,  # Ajouter l'organisation pour accéder au logo
        'stats': stats,
        'financial_stats': financial_stats,
        'event_stats': event_stats,
        'combat_stats': combat_stats,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'recent_events': recent_events,
        'active_polls': active_polls,
        'club_competitions': club_competitions,
        'upcoming_competitions': upcoming_competitions,
        'competitions_to_manage': competitions_to_manage,
        'competitions_to_manage_count': len(competitions_to_manage) if isinstance(competitions_to_manage, list) else 0,
        'recent_practitioners': recent_practitioners,
        'all_practitioners': all_practitioners,  # Ajouter tous les pratiquants
        'member_statistics': member_statistics,  # Statistiques membres par âge/genre
        'grade_distribution': grade_distribution,  # Distribution des grades
        'recent_registrations': recent_registrations,
        'club_disciplines': club_disciplines,
        'judge_assignments': judge_assignments,
        'recent_payments': recent_payments,
        'recent_sessions': recent_sessions,
        'attendance_stats': attendance_stats,
        'top_attendees': top_attendees,
        'training_programs': training_programs,
        'training_programs_count': training_programs_count,
        'recent_orders': recent_orders,
        'order_stats': order_stats,
        'shop_stats': shop_stats,
        'popular_products': popular_products,
        'recent_notifications': recent_notifications,
        'unread_count': unread_count,
        'recent_tickets': recent_tickets,
        'ticket_stats': ticket_stats,
        'club_setup_info': club_setup_info,
        'current_date': now,
        'page_title': _("Tableau de bord du club"),
        'section': 'dashboard',
        # NOUVEAU - Données d'adhésion MartialComp v2.0
        'membership_stats': membership_stats,
        'recent_subscriptions': recent_subscriptions,
        'membership_alerts': membership_alerts,
        # NOUVEAU - Données d'affiliation
        'pending_federation_invitations': pending_federation_invitations,
        'affiliation_stats': affiliation_stats,
        # NOUVEAU - Données de combat
        'recent_combats': recent_combats,
        'club_teams': club_teams,
        'club_teams_count': club_teams_count,
        # NOUVEAU - Données de documents
        'document_stats': document_stats,
        'recent_documents': recent_documents,
        # NOUVEAU - Données de rôles
        'roles_stats': {
            'admin_count': 0,
            'manager_count': 0,
            'coach_count': 0,
            'member_count': 0
        },
        # NOUVEAU - Données de sites (calculées dynamiquement)
        'site_stats': calculate_site_stats(club_organization) if club_organization else {
            'total_visits': 0,
            'qr_scans': 0,
            'registrations_via_site': 0,
            'gallery_photos': 0
        },
        # FILTRES CÔTÉ SERVEUR pour l'onglet Pratiquants
        'filter_search': filter_search,
        'filter_discipline': filter_discipline,
        'filter_grade': filter_grade,
        'filter_status': filter_status,
        'filter_gender': filter_gender,
        'filter_options': {
            'disciplines': club_disciplines,
            'grades': grades_list if 'grades_list' in locals() else [],
        },
    }
    
    # Ajouter les données de gestion de tâches au contexte si disponibles
    if task_data:
        context.update(task_data)
    
    # Fusionner avec le contexte de base pour assurer qu'aucune variable ne soit None
    for key, value in base_context.items():
        if key not in context or context[key] is None:
            context[key] = value
    
    # Ajouter club_judges au contexte si disponible
    if 'club_judges' in locals():
        context['club_judges'] = club_judges
    
    # Ajouter les infos d'abonnement pour le badge sidebar
    try:
        from apps.finances.services.subscription_service import get_subscription_info
        org_for_sub = club_organization if 'club_organization' in locals() and club_organization else club
        context['subscription_info'] = get_subscription_info(org_for_sub)
    except Exception as e:
        logger.warning(f"Erreur chargement subscription_info: {e}")

    # Ajouter les clés disponibles pour le diagnostic
    context['context_keys'] = list(context.keys())

    return render(request, 'competitions/dashboard/club.html', context)


@login_required
def update_organization_logo(request):
    """
    Vue pour mettre à jour le logo de l'organisation du club.
    """
    if request.method == 'POST':
        try:
            # Récupérer le club de l'utilisateur
            club = None
            # Méthode 1: Via attribut direct
            if hasattr(request.user, 'club_id') and request.user.club_id:
                club = Club.objects.filter(id=request.user.club_id).first()
            # Méthode 2: Via profile
            if not club and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
                club = request.user.profile.club
            # Méthode 3: Via propriété (owner)
            if not club:
                club = Club.objects.filter(owner=request.user).first()
            # Méthode 4: Via membership (membre de l'organisation)
            if not club:
                from apps.organizations.models import OrganizationMember
                membership = OrganizationMember.objects.filter(
                    user=request.user,
                    role__in=['admin', 'owner', 'manager']
                ).select_related('organization').first()
                if membership and membership.organization:
                    club = Club.objects.filter(organization=membership.organization).first()

            if not club:
                return JsonResponse({'success': False, 'error': _("Club non trouvé")}, status=404)
            
            # Récupérer l'organisation
            club_organization = None
            if hasattr(club, 'organization') and club.organization:
                club_organization = club.organization
            elif hasattr(club, 'organization_id') and club.organization_id:
                from apps.organizations.models import Organization
                try:
                    club_organization = Organization.objects.get(id=club.organization_id)
                except Organization.DoesNotExist:
                    return JsonResponse({'success': False, 'error': _("Organisation non trouvée")}, status=404)
            
            if not club_organization:
                return JsonResponse({'success': False, 'error': _("Aucune organisation associée au club")}, status=404)
            
            # Vérifier les permissions
            is_owner = hasattr(club, 'owner') and request.user == club.owner
            is_staff = request.user.is_staff or request.user.is_superuser
            is_admin_role = hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role in ['admin', 'manager']
            # Vérifier aussi si l'utilisateur est membre admin de l'organisation
            is_org_admin = False
            if club_organization:
                from apps.organizations.models import OrganizationMember
                is_org_admin = OrganizationMember.objects.filter(
                    organization=club_organization,
                    user=request.user,
                    role__in=['admin', 'owner', 'manager']
                ).exists()
            if not (is_owner or is_staff or is_admin_role or is_org_admin):
                return JsonResponse({'success': False, 'error': _("Permission refusée")}, status=403)
            
            action = request.POST.get('action')
            
            if action == 'upload':
                # Upload du logo
                if 'logo' not in request.FILES:
                    return JsonResponse({'success': False, 'error': _("Aucun fichier fourni")}, status=400)
                
                logo_file = request.FILES['logo']
                
                # Validation du fichier
                if logo_file.size > 2 * 1024 * 1024:  # 2 MB
                    return JsonResponse({'success': False, 'error': _("Le fichier est trop volumineux (max 2 MB)")}, status=400)
                
                # Vérifier le type de fichier
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if logo_file.content_type not in allowed_types:
                    return JsonResponse({'success': False, 'error': _("Type de fichier non autorisé")}, status=400)
                
                # Sauvegarder le logo
                club_organization.logo = logo_file
                club_organization.save(update_fields=['logo'])
                
                return JsonResponse({
                    'success': True,
                    'message': _("Logo mis à jour avec succès"),
                    'logo_url': club_organization.logo.url
                })
            
            elif action == 'delete':
                # Supprimer le logo
                if club_organization.logo:
                    club_organization.logo.delete(save=False)
                    club_organization.logo = None
                    club_organization.save(update_fields=['logo'])
                
                return JsonResponse({
                    'success': True,
                    'message': _("Logo supprimé avec succès")
                })
            
            else:
                return JsonResponse({'success': False, 'error': _("Action non valide")}, status=400)
        
        except Exception as e:
            logger.error(_("Erreur lors de la mise à jour du logo: {}").format(str(e)))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': _("Méthode non autorisée")}, status=405)


@login_required
def club_results(request):
    """
    Affiche les résultats des pratiquants du club.
    Accessible aux responsables de club pour voir les performances de leurs membres.
    Inclut les statistiques de combat détaillées pour analyse des performances.
    """
    from apps.competitions.models.technical_scoring import CompetitionRanking
    from apps.competitions.models.combat import Combat
    from django.core.paginator import Paginator
    from django.db.models import Sum

    # Récupérer le club de l'utilisateur
    club = None
    club_organization = None

    # Méthode 1: Via attribut direct
    if hasattr(request.user, 'club_id') and request.user.club_id:
        club = Club.objects.filter(id=request.user.club_id).first()

    # Méthode 2: Via relation de propriété
    if not club:
        club = Club.objects.filter(owner=request.user).first()

    # Méthode 3: Via profil utilisateur
    if not club and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club

    if not club:
        messages.warning(request, _("Vous devez être associé à un club pour voir les résultats."))
        return redirect('competitions:dashboard:club')

    # Récupérer l'organisation du club
    if hasattr(club, 'organization') and club.organization:
        club_organization = club.organization
    elif hasattr(club, 'organization_id') and club.organization_id:
        from apps.organizations.models import Organization
        try:
            club_organization = Organization.objects.get(id=club.organization_id)
        except Organization.DoesNotExist:
            pass

    # Récupérer les pratiquants du club
    if club_organization:
        practitioners = filter_practitioners_by_org_disciplines(club_organization)
    else:
        practitioners = Practitioner.objects.none()

    # Récupérer les résultats des pratiquants du club
    rankings = CompetitionRanking.objects.filter(
        practitioner__in=practitioners
    ).select_related(
        'competition', 'category', 'practitioner', 'practitioner__organization'
    ).order_by('-competition__start_date', 'rank')

    # Filtrer par compétition si paramètre fourni
    competition_id = request.GET.get('competition')
    if competition_id:
        rankings = rankings.filter(competition_id=competition_id)

    # Filtrer par pratiquant si paramètre fourni
    practitioner_id = request.GET.get('practitioner')
    if practitioner_id:
        rankings = rankings.filter(practitioner_id=practitioner_id)

    # Recherche par nom
    search_query = request.GET.get('q', '').strip()
    if search_query:
        rankings = rankings.filter(
            Q(practitioner__first_name__icontains=search_query) |
            Q(practitioner__last_name__icontains=search_query) |
            Q(competition__title__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # ===== RÉSULTATS COMBAT (poules) par pratiquant =====
    combat_filter_q = {'status': 'termine'}
    if competition_id:
        combat_filter_q['competition_id'] = competition_id

    from collections import defaultdict
    combat_stats_map = defaultdict(lambda: {'v': 0, 'd': 0, 'n': 0, 'pts_for': 0, 'pts_against': 0, 'comp': None, 'cat': None, 'prat': None})

    for c in Combat.objects.filter(pratiquant_rouge__in=practitioners, **combat_filter_q).select_related('competition', 'pratiquant_rouge', 'poule__category', 'equipe_rouge__category'):
        cat = (c.poule.category if c.poule and c.poule.category else None) or (c.equipe_rouge.category if c.equipe_rouge and hasattr(c.equipe_rouge, 'category') else None)
        if not cat:
            continue
        s = combat_stats_map[(c.pratiquant_rouge_id, cat.id, c.competition_id)]
        s['comp'], s['cat'], s['prat'] = c.competition, cat, c.pratiquant_rouge
        s['pts_for'] += float(c.score_rouge or 0)
        s['pts_against'] += float(c.score_blanc or 0)
        if c.est_nul: s['n'] += 1
        elif c.vainqueur == 'rouge': s['v'] += 1
        else: s['d'] += 1

    for c in Combat.objects.filter(pratiquant_blanc__in=practitioners, **combat_filter_q).select_related('competition', 'pratiquant_blanc', 'poule__category', 'equipe_blanc__category'):
        cat = (c.poule.category if c.poule and c.poule.category else None) or (c.equipe_blanc.category if c.equipe_blanc and hasattr(c.equipe_blanc, 'category') else None)
        if not cat:
            continue
        s = combat_stats_map[(c.pratiquant_blanc_id, cat.id, c.competition_id)]
        s['comp'], s['cat'], s['prat'] = c.competition, cat, c.pratiquant_blanc
        s['pts_for'] += float(c.score_blanc or 0)
        s['pts_against'] += float(c.score_rouge or 0)
        if c.est_nul: s['n'] += 1
        elif c.vainqueur == 'blanc': s['v'] += 1
        else: s['d'] += 1

    combat_results = []
    for key, s in combat_stats_map.items():
        combat_results.append(type('CombatResult', (), {
            'practitioner': s['prat'],
            'competition': s['comp'],
            'category': s['cat'],
            'rank': None,
            'final_score': None,
            'is_combat': True,
            'is_tie': False,
            'victories': s['v'],
            'defeats': s['d'],
            'draws': s['n'],
            'score_display': f"{s['v']}V / {s['d']}D / {s['n']}N",
        })())

    # Filtrer les résultats combat par pratiquant et recherche
    if practitioner_id:
        combat_results = [r for r in combat_results if str(r.practitioner.id) == str(practitioner_id)]
    if search_query:
        sq = search_query.lower()
        combat_results = [r for r in combat_results if
            sq in r.practitioner.first_name.lower() or
            sq in r.practitioner.last_name.lower() or
            sq in r.competition.title.lower() or
            sq in r.category.name.lower()
        ]

    # Calculer les statistiques de médailles
    gold_medals = rankings.filter(rank=1).count()
    silver_medals = rankings.filter(rank=2).count()
    bronze_medals = rankings.filter(rank=3).count()

    # ===== STATISTIQUES DE COMBAT DU CLUB =====
    # Filtrées par compétition si un filtre est actif
    combats_rouge = Combat.objects.filter(
        pratiquant_rouge__in=practitioners,
        status='termine'
    )
    combats_blanc = Combat.objects.filter(
        pratiquant_blanc__in=practitioners,
        status='termine'
    )
    if competition_id:
        combats_rouge = combats_rouge.filter(competition_id=competition_id)
        combats_blanc = combats_blanc.filter(competition_id=competition_id)

    # Statistiques globales de combat du club
    total_combats = combats_rouge.count() + combats_blanc.count()

    # Victoires
    victoires_rouge = combats_rouge.filter(vainqueur='rouge').count()
    victoires_blanc = combats_blanc.filter(vainqueur='blanc').count()
    total_victoires = victoires_rouge + victoires_blanc

    # Défaites
    defaites_rouge = combats_rouge.filter(vainqueur='blanc').count()
    defaites_blanc = combats_blanc.filter(vainqueur='rouge').count()
    total_defaites = defaites_rouge + defaites_blanc

    # Matchs nuls
    nuls_rouge = combats_rouge.filter(est_nul=True).count()
    nuls_blanc = combats_blanc.filter(est_nul=True).count()
    total_nuls = nuls_rouge + nuls_blanc

    # Points marqués et encaissés
    points_marques_rouge = combats_rouge.aggregate(total=Sum('score_rouge'))['total'] or 0
    points_marques_blanc = combats_blanc.aggregate(total=Sum('score_blanc'))['total'] or 0
    total_points_marques = float(points_marques_rouge) + float(points_marques_blanc)

    points_encaisses_rouge = combats_rouge.aggregate(total=Sum('score_blanc'))['total'] or 0
    points_encaisses_blanc = combats_blanc.aggregate(total=Sum('score_rouge'))['total'] or 0
    total_points_encaisses = float(points_encaisses_rouge) + float(points_encaisses_blanc)

    # Différentiel de points
    differentiel_points = total_points_marques - total_points_encaisses

    # Taux de victoire
    taux_victoire = (total_victoires / total_combats * 100) if total_combats > 0 else 0

    # Combiner résultats techniques + combat
    all_results = list(rankings) + combat_results
    # Trier par compétition (date desc), puis rang
    all_results.sort(key=lambda r: (
        -(r.competition.start_date.toordinal() if r.competition and r.competition.start_date else 0),
        r.rank or 999
    ))

    # Pagination
    paginator = Paginator(all_results, 20)
    page_number = request.GET.get('page')
    results_page = paginator.get_page(page_number)

    # Récupérer les compétitions distinctes pour le filtre (toutes, pas filtrées)
    all_competition_ids = CompetitionRanking.objects.filter(
        practitioner__in=practitioners
    ).values_list('competition_id', flat=True).distinct()
    competitions = Competition.objects.filter(id__in=all_competition_ids).order_by('-start_date')

    # Médailles par saison sportive (sept-août) — suit les filtres actifs
    all_rankings_for_chart = rankings.filter(
        competition__start_date__isnull=False,
    ).select_related('competition')

    # Regrouper par saison sportive
    from collections import OrderedDict
    seasons = OrderedDict()
    for r in all_rankings_for_chart.order_by('competition__start_date'):
        d = r.competition.start_date
        # Saison = année de début en septembre (ex: compétition en mars 2026 -> saison 2025-2026)
        season_year = d.year if d.month >= 9 else d.year - 1
        season_key = f'{season_year}-{season_year + 1}'
        if season_key not in seasons:
            seasons[season_key] = {'name': season_key, 'gold': 0, 'silver': 0, 'bronze': 0}
        if r.rank == 1:
            seasons[season_key]['gold'] += 1
        elif r.rank == 2:
            seasons[season_key]['silver'] += 1
        elif r.rank == 3:
            seasons[season_key]['bronze'] += 1

    medals_by_competition = list(seasons.values())

    context = {
        'club': club,
        'club_organization': club_organization,
        'results': results_page,
        'practitioners': practitioners[:50],  # Limiter pour le select
        'competitions': competitions,
        'gold_medals': gold_medals,
        'silver_medals': silver_medals,
        'bronze_medals': bronze_medals,
        'total_results': rankings.count(),
        'search_query': search_query,
        'selected_competition': competition_id,
        'selected_practitioner': practitioner_id,
        'medals_by_competition': medals_by_competition,
        'page_title': _("Résultats du club"),
        # Statistiques globales de combat du club
        'combat_stats': {
            'total_combats': total_combats,
            'victoires': total_victoires,
            'defaites': total_defaites,
            'nuls': total_nuls,
            'taux_victoire': round(taux_victoire, 1),
            'points_marques': round(total_points_marques, 1),
            'points_encaisses': round(total_points_encaisses, 1),
            'differentiel': round(differentiel_points, 1),
        },
    }

    return render(request, 'competitions/dashboard/club_results.html', context)


@login_required
def my_results(request):
    """
    Affiche les résultats personnels du responsable de club.
    Permet aux responsables de voir leurs propres performances de compétition.
    Inclut les statistiques détaillées de combat (victoires, points marqués, etc.)
    """
    from apps.competitions.models.technical_scoring import CompetitionRanking
    from apps.competitions.models.combat import Combat
    from django.core.paginator import Paginator
    from django.db.models import Sum, Case, When, IntegerField, DecimalField

    # Récupérer le pratiquant associé à l'utilisateur
    practitioner = Practitioner.objects.filter(user=request.user).first()

    if not practitioner:
        # Essayer de trouver un pratiquant par email
        practitioner = Practitioner.objects.filter(email=request.user.email).first()

    if not practitioner:
        messages.info(request, _("Aucun profil pratiquant n'est associé à votre compte."))
        return redirect('competitions:dashboard:club')

    # Récupérer les résultats du pratiquant (classements)
    rankings = CompetitionRanking.objects.filter(
        practitioner=practitioner
    ).select_related(
        'competition', 'category'
    ).order_by('-competition__start_date', 'rank')

    # Recherche par compétition
    search_query = request.GET.get('q', '').strip()
    if search_query:
        rankings = rankings.filter(
            Q(competition__title__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Calculer les statistiques de médailles
    gold_medals = rankings.filter(rank=1).count()
    silver_medals = rankings.filter(rank=2).count()
    bronze_medals = rankings.filter(rank=3).count()

    # ===== STATISTIQUES DE COMBAT DÉTAILLÉES =====
    # Récupérer tous les combats du pratiquant (comme rouge ou blanc)
    combats_rouge = Combat.objects.filter(
        pratiquant_rouge=practitioner,
        status='termine'
    )
    combats_blanc = Combat.objects.filter(
        pratiquant_blanc=practitioner,
        status='termine'
    )

    # Statistiques globales de combat
    total_combats = combats_rouge.count() + combats_blanc.count()

    # Victoires
    victoires_rouge = combats_rouge.filter(vainqueur='rouge').count()
    victoires_blanc = combats_blanc.filter(vainqueur='blanc').count()
    total_victoires = victoires_rouge + victoires_blanc

    # Défaites
    defaites_rouge = combats_rouge.filter(vainqueur='blanc').count()
    defaites_blanc = combats_blanc.filter(vainqueur='rouge').count()
    total_defaites = defaites_rouge + defaites_blanc

    # Matchs nuls
    nuls_rouge = combats_rouge.filter(est_nul=True).count()
    nuls_blanc = combats_blanc.filter(est_nul=True).count()
    total_nuls = nuls_rouge + nuls_blanc

    # Points marqués et encaissés
    points_marques_rouge = combats_rouge.aggregate(
        total=Sum('score_rouge')
    )['total'] or 0
    points_marques_blanc = combats_blanc.aggregate(
        total=Sum('score_blanc')
    )['total'] or 0
    total_points_marques = float(points_marques_rouge) + float(points_marques_blanc)

    points_encaisses_rouge = combats_rouge.aggregate(
        total=Sum('score_blanc')
    )['total'] or 0
    points_encaisses_blanc = combats_blanc.aggregate(
        total=Sum('score_rouge')
    )['total'] or 0
    total_points_encaisses = float(points_encaisses_rouge) + float(points_encaisses_blanc)

    # Différentiel de points
    differentiel_points = total_points_marques - total_points_encaisses

    # Taux de victoire
    taux_victoire = (total_victoires / total_combats * 100) if total_combats > 0 else 0

    # Moyenne de points par combat
    moyenne_points_marques = total_points_marques / total_combats if total_combats > 0 else 0
    moyenne_points_encaisses = total_points_encaisses / total_combats if total_combats > 0 else 0

    # Enrichir les résultats avec les stats de combat par compétition
    results_with_stats = []
    for ranking in rankings:
        # Stats de combat pour cette compétition spécifique
        comp_combats_rouge = combats_rouge.filter(competition=ranking.competition)
        comp_combats_blanc = combats_blanc.filter(competition=ranking.competition)

        comp_total = comp_combats_rouge.count() + comp_combats_blanc.count()
        comp_victoires = (
            comp_combats_rouge.filter(vainqueur='rouge').count() +
            comp_combats_blanc.filter(vainqueur='blanc').count()
        )
        comp_defaites = (
            comp_combats_rouge.filter(vainqueur='blanc').count() +
            comp_combats_blanc.filter(vainqueur='rouge').count()
        )
        comp_nuls = (
            comp_combats_rouge.filter(est_nul=True).count() +
            comp_combats_blanc.filter(est_nul=True).count()
        )

        comp_pts_marques = float(
            (comp_combats_rouge.aggregate(Sum('score_rouge'))['score_rouge__sum'] or 0) +
            (comp_combats_blanc.aggregate(Sum('score_blanc'))['score_blanc__sum'] or 0)
        )
        comp_pts_encaisses = float(
            (comp_combats_rouge.aggregate(Sum('score_blanc'))['score_blanc__sum'] or 0) +
            (comp_combats_blanc.aggregate(Sum('score_rouge'))['score_rouge__sum'] or 0)
        )

        results_with_stats.append({
            'ranking': ranking,
            'combat_stats': {
                'total_combats': comp_total,
                'victoires': comp_victoires,
                'defaites': comp_defaites,
                'nuls': comp_nuls,
                'points_marques': comp_pts_marques,
                'points_encaisses': comp_pts_encaisses,
                'differentiel': comp_pts_marques - comp_pts_encaisses,
            } if comp_total > 0 else None
        })

    # Pagination
    paginator = Paginator(results_with_stats, 20)
    page_number = request.GET.get('page')
    results_page = paginator.get_page(page_number)

    context = {
        'practitioner': practitioner,
        'results': results_page,
        'gold_medals': gold_medals,
        'silver_medals': silver_medals,
        'bronze_medals': bronze_medals,
        'total_results': rankings.count(),
        'search_query': search_query,
        'page_title': _("Mes résultats"),
        # Statistiques globales de combat
        'combat_stats': {
            'total_combats': total_combats,
            'victoires': total_victoires,
            'defaites': total_defaites,
            'nuls': total_nuls,
            'taux_victoire': round(taux_victoire, 1),
            'points_marques': round(total_points_marques, 1),
            'points_encaisses': round(total_points_encaisses, 1),
            'differentiel': round(differentiel_points, 1),
            'moyenne_marques': round(moyenne_points_marques, 2),
            'moyenne_encaisses': round(moyenne_points_encaisses, 2),
        },
    }

    return render(request, 'competitions/dashboard/my_results.html', context)


@login_required
def update_club_settings(request):
    """
    Vue pour mettre à jour les paramètres du club (nom, disciplines, etc.).
    Permet au propriétaire du club de modifier les informations de base.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _("Méthode non autorisée")}, status=405)

    try:
        # Récupérer le club de l'utilisateur
        club = None
        if hasattr(request.user, 'club_id') and request.user.club_id:
            club = Club.objects.filter(id=request.user.club_id).first()
        elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
            club = request.user.profile.club
        elif hasattr(request.user, 'owned_clubs'):
            club = request.user.owned_clubs.first()

        if not club:
            return JsonResponse({'success': False, 'error': _("Club non trouvé")}, status=404)

        # Vérifier les permissions
        if not (request.user == club.owner or request.user.is_staff or
                (hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager', 'club_manager'])):
            return JsonResponse({'success': False, 'error': _("Permission refusée")}, status=403)

        # Récupérer l'action
        action = request.POST.get('action', 'update')

        if action == 'update_name':
            # Mise à jour du nom
            new_name = request.POST.get('name', '').strip()
            if not new_name:
                return JsonResponse({'success': False, 'error': _("Le nom ne peut pas être vide")}, status=400)

            club.name = new_name
            club.save(update_fields=['name'])

            # Mettre à jour aussi l'organisation associée
            if club.organization:
                club.organization.name = new_name
                club.organization.save(update_fields=['name'])

            return JsonResponse({
                'success': True,
                'message': _("Nom du club mis à jour avec succès"),
                'name': new_name
            })

        elif action == 'update_disciplines':
            # Mise à jour des disciplines
            discipline_ids = request.POST.getlist('disciplines')

            if discipline_ids:
                from ...models import Discipline
                selected_disciplines = Discipline.objects.filter(id__in=discipline_ids, is_active=True)
                club.disciplines.set(selected_disciplines)

                # Mettre à jour la discipline principale si nécessaire
                if not club.main_discipline or club.main_discipline.id not in discipline_ids:
                    club.main_discipline = selected_disciplines.first()
                    club.save(update_fields=['main_discipline'])

                # Synchroniser avec l'organisation
                if club.organization:
                    club.organization.disciplines.set(selected_disciplines)

                return JsonResponse({
                    'success': True,
                    'message': _("Disciplines mises à jour avec succès"),
                    'disciplines': list(selected_disciplines.values_list('name', flat=True))
                })
            else:
                # Aucune discipline sélectionnée - vider la liste
                club.disciplines.clear()
                club.main_discipline = None
                club.save(update_fields=['main_discipline'])

                if club.organization:
                    club.organization.disciplines.clear()

                return JsonResponse({
                    'success': True,
                    'message': _("Disciplines supprimées"),
                    'disciplines': []
                })

        elif action == 'update_all':
            # Mise à jour complète (nom + disciplines + autres champs)
            updated_fields = []

            # Nom
            if 'name' in request.POST:
                new_name = request.POST.get('name', '').strip()
                if new_name:
                    club.name = new_name
                    updated_fields.append('name')
                    if club.organization:
                        club.organization.name = new_name

            # Description
            if 'description' in request.POST:
                club.description = request.POST.get('description', '')
                updated_fields.append('description')

            # Email
            if 'contact_email' in request.POST:
                club.contact_email = request.POST.get('contact_email', '')
                updated_fields.append('contact_email')

            # Téléphone
            if 'contact_phone' in request.POST:
                club.contact_phone = request.POST.get('contact_phone', '')
                updated_fields.append('contact_phone')

            # Site web
            if 'website' in request.POST:
                club.website = request.POST.get('website', '')
                updated_fields.append('website')

            # Adresse
            if 'address' in request.POST:
                club.address = request.POST.get('address', '')
                updated_fields.append('address')

            if 'city' in request.POST:
                club.city = request.POST.get('city', '')
                updated_fields.append('city')

            if 'postal_code' in request.POST:
                club.postal_code = request.POST.get('postal_code', '')
                updated_fields.append('postal_code')

            if updated_fields:
                club.save(update_fields=updated_fields)
                if club.organization:
                    club.organization.save()

            # Disciplines (traitement séparé car c'est une relation M2M)
            if 'disciplines' in request.POST:
                discipline_ids = request.POST.getlist('disciplines')
                if discipline_ids:
                    from ...models import Discipline
                    selected_disciplines = Discipline.objects.filter(id__in=discipline_ids, is_active=True)
                    club.disciplines.set(selected_disciplines)
                    if club.organization:
                        club.organization.disciplines.set(selected_disciplines)
                else:
                    club.disciplines.clear()
                    if club.organization:
                        club.organization.disciplines.clear()

            return JsonResponse({
                'success': True,
                'message': _("Paramètres du club mis à jour avec succès"),
                'updated_fields': updated_fields
            })

        else:
            return JsonResponse({'success': False, 'error': _("Action non valide")}, status=400)

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres du club: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def combat_analysis(request):
    """
    Analyse détaillée des combats par compétition et par pratiquant.
    Permet à l'instructeur de faire un retour détaillé à chaque élève.

    Fonctionnalités:
    - Filtre par compétition
    - Performance par pratiquant avec stats détaillées
    - Liste des combats avec scores et résultats
    - Statistiques globales par compétition
    """
    from apps.competitions.models.combat import Combat, Equipe, Poule
    from apps.competitions.models import CompetitionCategory
    from django.db.models import Sum, Count, Q, F, Value, CharField
    from django.db.models.functions import Concat

    # Récupérer le club de l'utilisateur
    club = None
    club_organization = None

    if hasattr(request.user, 'club_id') and request.user.club_id:
        club = Club.objects.filter(id=request.user.club_id).first()

    if not club:
        club = Club.objects.filter(owner=request.user).first()

    if not club and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club

    if not club:
        messages.warning(request, _("Vous devez être associé à un club pour voir l'analyse des combats."))
        return redirect('competitions:dashboard:club')

    # Récupérer l'organisation du club
    if hasattr(club, 'organization') and club.organization:
        club_organization = club.organization
    elif hasattr(club, 'organization_id') and club.organization_id:
        from apps.organizations.models import Organization
        try:
            club_organization = Organization.objects.get(id=club.organization_id)
        except Organization.DoesNotExist:
            pass

    # Récupérer les pratiquants du club
    if club_organization:
        practitioners = filter_practitioners_by_org_disciplines(club_organization)
    else:
        practitioners = Practitioner.objects.none()

    practitioner_ids = list(practitioners.values_list('id', flat=True))

    # Récupérer les compétitions où le club a participé à des combats
    competition_ids = set()

    # Combats individuels
    combat_competitions = Combat.objects.filter(
        Q(pratiquant_rouge__in=practitioner_ids) | Q(pratiquant_blanc__in=practitioner_ids),
        status='termine'
    ).values_list('competition_id', flat=True).distinct()
    competition_ids.update(combat_competitions)

    # Combats par équipe (via club_id de l'équipe)
    team_competition_ids = Combat.objects.filter(
        Q(equipe_rouge__club_id=club.id) | Q(equipe_blanc__club_id=club.id),
        status='termine'
    ).values_list('competition_id', flat=True).distinct()
    competition_ids.update(team_competition_ids)

    competitions = Competition.objects.filter(id__in=competition_ids).order_by('-start_date')

    # Filtre par compétition sélectionnée
    selected_competition_id = request.GET.get('competition')
    selected_competition = None

    if selected_competition_id:
        selected_competition = Competition.objects.filter(id=selected_competition_id).first()
    elif competitions.exists():
        # Par défaut, prendre la compétition la plus récente
        selected_competition = competitions.first()

    # Données pour la compétition sélectionnée
    competition_stats = {
        'total_combats': 0,
        'victoires': 0,
        'defaites': 0,
        'nuls': 0,
        'taux_victoire': 0,
        'points_marques': 0,
        'points_encaisses': 0,
        'differentiel': 0,
    }
    practitioner_stats = []
    combats_by_category = []

    if selected_competition:
        # Récupérer tous les combats de cette compétition impliquant le club
        combats_club = Combat.objects.filter(
            competition=selected_competition,
            status='termine'
        ).filter(
            Q(pratiquant_rouge__in=practitioner_ids) |
            Q(pratiquant_blanc__in=practitioner_ids) |
            Q(equipe_rouge__club_id=club.id) |
            Q(equipe_blanc__club_id=club.id)
        ).select_related(
            'pratiquant_rouge', 'pratiquant_blanc',
            'equipe_rouge', 'equipe_blanc',
            'poule', 'poule__category'
        ).order_by('poule__category__name', 'date_planifiee', 'id')

        # Calculer les stats globales pour cette compétition
        total_combats = 0
        victoires = 0
        defaites = 0
        nuls = 0
        points_marques = 0
        points_encaisses = 0

        # Stats par pratiquant
        practitioner_data = {}

        for combat in combats_club:
            is_rouge = False
            is_blanc = False
            practitioner = None

            # Vérifier si c'est un combat individuel
            if combat.pratiquant_rouge_id in practitioner_ids:
                is_rouge = True
                practitioner = combat.pratiquant_rouge
            if combat.pratiquant_blanc_id in practitioner_ids:
                is_blanc = True
                practitioner = combat.pratiquant_blanc

            # Vérifier si c'est un combat par équipe
            if combat.equipe_rouge and combat.equipe_rouge.club_id == club.id:
                is_rouge = True
            if combat.equipe_blanc and combat.equipe_blanc.club_id == club.id:
                is_blanc = True

            if is_rouge or is_blanc:
                total_combats += 1

                # Déterminer victoire/défaite/nul
                if combat.est_nul:
                    nuls += 1
                elif (is_rouge and combat.vainqueur == 'rouge') or (is_blanc and combat.vainqueur == 'blanc'):
                    victoires += 1
                else:
                    defaites += 1

                # Points
                if is_rouge:
                    points_marques += float(combat.score_rouge or 0)
                    points_encaisses += float(combat.score_blanc or 0)
                if is_blanc:
                    points_marques += float(combat.score_blanc or 0)
                    points_encaisses += float(combat.score_rouge or 0)

                # Accumuler stats par pratiquant (seulement pour combats individuels)
                if practitioner:
                    if practitioner.id not in practitioner_data:
                        practitioner_data[practitioner.id] = {
                            'practitioner': practitioner,
                            'combats': 0,
                            'victoires': 0,
                            'defaites': 0,
                            'nuls': 0,
                            'points_marques': 0,
                            'points_encaisses': 0,
                            'combat_details': []
                        }

                    p_data = practitioner_data[practitioner.id]
                    p_data['combats'] += 1

                    if combat.est_nul:
                        p_data['nuls'] += 1
                    elif (is_rouge and combat.vainqueur == 'rouge') or (is_blanc and combat.vainqueur == 'blanc'):
                        p_data['victoires'] += 1
                    else:
                        p_data['defaites'] += 1

                    if is_rouge:
                        p_data['points_marques'] += float(combat.score_rouge or 0)
                        p_data['points_encaisses'] += float(combat.score_blanc or 0)
                    else:
                        p_data['points_marques'] += float(combat.score_blanc or 0)
                        p_data['points_encaisses'] += float(combat.score_rouge or 0)

                    # Détails du combat
                    adversaire = None
                    if is_rouge and combat.pratiquant_blanc:
                        adversaire = combat.pratiquant_blanc
                    elif is_blanc and combat.pratiquant_rouge:
                        adversaire = combat.pratiquant_rouge

                    p_data['combat_details'].append({
                        'combat': combat,
                        'is_rouge': is_rouge,
                        'adversaire': adversaire,
                        'score_club': float(combat.score_rouge if is_rouge else combat.score_blanc or 0),
                        'score_adversaire': float(combat.score_blanc if is_rouge else combat.score_rouge or 0),
                        'resultat': 'nul' if combat.est_nul else ('victoire' if ((is_rouge and combat.vainqueur == 'rouge') or (is_blanc and combat.vainqueur == 'blanc')) else 'defaite'),
                        'category_name': combat.poule.category.name if combat.poule and combat.poule.category else _('Sans catégorie'),
                    })

        # Calculer les statistiques finales
        taux_victoire = (victoires / total_combats * 100) if total_combats > 0 else 0

        competition_stats = {
            'total_combats': total_combats,
            'victoires': victoires,
            'defaites': defaites,
            'nuls': nuls,
            'taux_victoire': round(taux_victoire, 1),
            'points_marques': round(points_marques, 1),
            'points_encaisses': round(points_encaisses, 1),
            'differentiel': round(points_marques - points_encaisses, 1),
        }

        # Formatter les stats par pratiquant
        for p_id, p_data in practitioner_data.items():
            taux = (p_data['victoires'] / p_data['combats'] * 100) if p_data['combats'] > 0 else 0
            diff = p_data['points_marques'] - p_data['points_encaisses']
            practitioner_stats.append({
                'practitioner': p_data['practitioner'],
                'combats': p_data['combats'],
                'victoires': p_data['victoires'],
                'defaites': p_data['defaites'],
                'nuls': p_data['nuls'],
                'taux_victoire': round(taux, 1),
                'points_marques': round(p_data['points_marques'], 1),
                'points_encaisses': round(p_data['points_encaisses'], 1),
                'differentiel': round(diff, 1),
                'combat_details': p_data['combat_details'],
            })

        # Trier par nombre de victoires puis par différentiel
        practitioner_stats.sort(key=lambda x: (-x['victoires'], -x['differentiel']))

        # Grouper les combats par catégorie pour l'affichage
        categories_dict = {}
        for combat in combats_club:
            cat_name = combat.poule.category.name if combat.poule and combat.poule.category else _('Sans catégorie')
            cat_id = combat.poule.category.id if combat.poule and combat.poule.category else 0

            if cat_id not in categories_dict:
                categories_dict[cat_id] = {
                    'name': cat_name,
                    'combats': []
                }

            # Déterminer qui est du club
            is_rouge = (combat.pratiquant_rouge_id in practitioner_ids or
                       (combat.equipe_rouge and combat.equipe_rouge.club_id == club.id))
            is_blanc = (combat.pratiquant_blanc_id in practitioner_ids or
                       (combat.equipe_blanc and combat.equipe_blanc.club_id == club.id))

            # Nom du combattant du club
            club_fighter = None
            adversaire = None
            if is_rouge:
                if combat.pratiquant_rouge:
                    club_fighter = combat.pratiquant_rouge.full_name
                elif combat.equipe_rouge:
                    club_fighter = combat.equipe_rouge.nom
                if combat.pratiquant_blanc:
                    adversaire = combat.pratiquant_blanc.full_name
                elif combat.equipe_blanc:
                    adversaire = combat.equipe_blanc.nom
            else:
                if combat.pratiquant_blanc:
                    club_fighter = combat.pratiquant_blanc.full_name
                elif combat.equipe_blanc:
                    club_fighter = combat.equipe_blanc.nom
                if combat.pratiquant_rouge:
                    adversaire = combat.pratiquant_rouge.full_name
                elif combat.equipe_rouge:
                    adversaire = combat.equipe_rouge.nom

            categories_dict[cat_id]['combats'].append({
                'combat': combat,
                'club_fighter': club_fighter or _('Inconnu'),
                'adversaire': adversaire or _('Inconnu'),
                'score_club': float(combat.score_rouge if is_rouge else combat.score_blanc or 0),
                'score_adversaire': float(combat.score_blanc if is_rouge else combat.score_rouge or 0),
                'resultat': 'nul' if combat.est_nul else ('victoire' if ((is_rouge and combat.vainqueur == 'rouge') or (is_blanc and combat.vainqueur == 'blanc')) else 'defaite'),
                'is_rouge': is_rouge,
            })

        combats_by_category = list(categories_dict.values())

    context = {
        'club': club,
        'club_organization': club_organization,
        'competitions': competitions,
        'selected_competition': selected_competition,
        'competition_stats': competition_stats,
        'practitioner_stats': practitioner_stats,
        'combats_by_category': combats_by_category,
        'page_title': _("Analyse des combats"),
    }

    return render(request, 'competitions/dashboard/combat_analysis.html', context)