"""
Utilitaires pour le filtrage par disciplines d'organisation.

Ce module fournit des fonctions pour filtrer les données selon les disciplines
sélectionnées dans une organisation. Cela permet d'isoler les données par discipline
(ex: Karaté ne voit pas les données du Kung Fu).
"""
from django.db.models import Q
from apps.competitions.models import Practitioner, Competition, Discipline
from apps.organizations.models import Organization


def get_organization_disciplines(organization):
    """
    Récupère les disciplines d'une organisation.
    
    Args:
        organization: Instance de Organization
        
    Returns:
        QuerySet: Les disciplines de l'organisation, ou toutes les disciplines si None
    """
    if not organization:
        return Discipline.objects.none()
    
    return organization.disciplines.all()


def filter_by_organization_disciplines(queryset, organization, discipline_field='discipline'):
    """
    Filtre un queryset selon les disciplines d'une organisation.
    
    Args:
        queryset: Le queryset à filtrer
        organization: L'organisation pour laquelle filtrer
        discipline_field: Le nom du champ discipline dans le modèle (par défaut 'discipline')
        
    Returns:
        QuerySet: Le queryset filtré par les disciplines de l'organisation
    """
    if not organization:
        return queryset.none()
    
    # Récupérer les disciplines de l'organisation
    org_disciplines = get_organization_disciplines(organization)
    
    if not org_disciplines.exists():
        # Si l'organisation n'a pas de disciplines, retourner un queryset vide
        # ou tous les résultats selon le contexte (ici, on retourne vide pour sécurité)
        return queryset.none()
    
    # Filtrer par les disciplines de l'organisation
    discipline_ids = list(org_disciplines.values_list('id', flat=True))
    
    # Construire le filtre selon le type de champ discipline
    if discipline_field == 'discipline':
        # Champ direct discipline
        return queryset.filter(discipline_id__in=discipline_ids)
    elif discipline_field == 'disciplines':
        # ManyToMany field
        return queryset.filter(disciplines__id__in=discipline_ids).distinct()
    elif discipline_field == 'primary_discipline':
        # Champ primary_discipline
        return queryset.filter(primary_discipline_id__in=discipline_ids)
    else:
        # Champ personnalisé
        filter_kwargs = {f'{discipline_field}__id__in': discipline_ids}
        return queryset.filter(**filter_kwargs)


def filter_practitioners_by_org_disciplines(organization, queryset=None):
    """
    Filtre les pratiquants selon les disciplines d'une organisation.
    
    Args:
        organization: L'organisation pour laquelle filtrer
        queryset: QuerySet de base (optionnel, par défaut tous les Practitioner)
        
    Returns:
        QuerySet: Les pratiquants filtrés
    """
    if queryset is None:
        queryset = Practitioner.objects.all()
    
    if not organization:
        return queryset.none()
    
    # Filtrer d'abord par organisation
    queryset = queryset.filter(organization=organization)
    
    # Récupérer les disciplines de l'organisation
    org_disciplines = get_organization_disciplines(organization)
    
    if not org_disciplines.exists():
        return queryset.none()
    
    discipline_ids = list(org_disciplines.values_list('id', flat=True))
    
    # Filtrer les pratiquants qui ont au moins une discipline en commun avec l'organisation
    return queryset.filter(disciplines__id__in=discipline_ids).distinct()


def filter_competitions_by_org_disciplines(organization, queryset=None):
    """
    Filtre les compétitions selon les disciplines d'une organisation.
    
    Args:
        organization: L'organisation pour laquelle filtrer
        queryset: QuerySet de base (optionnel, par défaut tous les Competition)
        
    Returns:
        QuerySet: Les compétitions filtrées
    """
    if queryset is None:
        queryset = Competition.objects.all()
    
    if not organization:
        return queryset.none()
    
    # Filtrer d'abord par organisation
    queryset = queryset.filter(organizing_organization=organization)
    
    # Récupérer les disciplines de l'organisation
    org_disciplines = get_organization_disciplines(organization)
    
    if not org_disciplines.exists():
        return queryset.none()
    
    discipline_ids = list(org_disciplines.values_list('id', flat=True))
    
    # Filtrer les compétitions par discipline
    return queryset.filter(discipline_id__in=discipline_ids).distinct()


def filter_judges_by_org_disciplines(organization, queryset=None):
    """
    Filtre les juges selon les disciplines d'une organisation.
    
    Args:
        organization: L'organisation pour laquelle filtrer
        queryset: QuerySet de base (optionnel)
        
    Returns:
        QuerySet: Les juges filtrés
    """
    try:
        from apps.competitions.models import Judge
    except ImportError:
        return queryset.none() if queryset else Judge.objects.none()
    
    if queryset is None:
        queryset = Judge.objects.all()
    
    if not organization:
        return queryset.none()
    
    # Filtrer d'abord par organisation (via practitioner)
    queryset = queryset.filter(practitioner__organization=organization)
    
    # Récupérer les disciplines de l'organisation
    org_disciplines = get_organization_disciplines(organization)
    
    if not org_disciplines.exists():
        return queryset.none()
    
    discipline_ids = list(org_disciplines.values_list('id', flat=True))
    
    # Filtrer les juges par discipline (via practitioner.disciplines)
    return queryset.filter(practitioner__disciplines__id__in=discipline_ids).distinct()


def filter_by_specific_discipline(queryset, organization, discipline_id, discipline_field='discipline'):
    """
    Filtre un queryset par une discipline spécifique de l'organisation.
    Utile pour permettre à l'utilisateur de sélectionner une discipline dans l'interface.
    
    Args:
        queryset: Le queryset à filtrer
        organization: L'organisation
        discipline_id: L'ID de la discipline à filtrer (None = toutes les disciplines de l'org)
        discipline_field: Le nom du champ discipline
        
    Returns:
        QuerySet: Le queryset filtré
    """
    if not organization:
        return queryset.none()
    
    # Vérifier que la discipline appartient à l'organisation
    org_disciplines = get_organization_disciplines(organization)
    
    if discipline_id:
        # Vérifier que la discipline est dans les disciplines de l'organisation
        if not org_disciplines.filter(id=discipline_id).exists():
            return queryset.none()
        
        # Filtrer par la discipline spécifique
        if discipline_field == 'discipline':
            return queryset.filter(discipline_id=discipline_id)
        elif discipline_field == 'disciplines':
            return queryset.filter(disciplines__id=discipline_id).distinct()
        else:
            filter_kwargs = {f'{discipline_field}__id': discipline_id}
            return queryset.filter(**filter_kwargs)
    else:
        # Pas de discipline spécifique, utiliser toutes les disciplines de l'organisation
        return filter_by_organization_disciplines(queryset, organization, discipline_field)
