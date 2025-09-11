from django.db.models import Q
from apps.competitions.models import Club, Discipline, Federation
from apps.organizations.models import Organization, Affiliation


def get_user_access_context(user):
    """
    Récupère le contexte d'accès d'un utilisateur.
    Retourne un tuple (disciplines, discipline_federation_mapping)
    
    Args:
        user: L'utilisateur pour lequel récupérer le contexte
        
    Returns:
        tuple: (disciplines, discipline_federation_mapping)
            - disciplines: Liste des disciplines auxquelles l'utilisateur a accès
            - discipline_federation_mapping: Dict {discipline_id: [federations]}
    """
    if user.is_superuser:
        # Un superuser voit tout
        disciplines = Discipline.objects.all()
        mapping = {d.id: Federation.objects.all() for d in disciplines}
        return disciplines, mapping
    
    # Récupérer le(s) club(s) de l'utilisateur
    clubs = Club.objects.filter(owner=user)
    
    # Si pas de club en tant que propriétaire, chercher en tant qu'administrateur
    if not clubs.exists():
        clubs = Club.objects.filter(administrators__user=user)
    
    # Initialiser les structures
    user_disciplines = set()
    discipline_federation_mapping = {}
    
    # Pour chaque club
    for club in clubs:
        # Récupérer les disciplines du club
        club_disciplines = club.disciplines.all()
        
        for discipline in club_disciplines:
            # Ajouter la discipline Ã  l'ensemble des disciplines autorisées
            user_disciplines.add(discipline)
            
            # Récupérer la fédération associée pour ce club et cette discipline
            federation = club.federation
            
            # Ajouter au mapping
            if discipline.id not in discipline_federation_mapping:
                discipline_federation_mapping[discipline.id] = set()
            
            if federation:
                discipline_federation_mapping[discipline.id].add(federation)
    
    return list(user_disciplines), discipline_federation_mapping


def filter_queryset_by_discipline_federation(queryset, user, discipline_field='discipline', federation_field='federation'):
    """
    Filtre un queryset selon les disciplines et fédérations accessibles Ã  l'utilisateur.
    
    Args:
        queryset: Le queryset Ã  filtrer
        user: L'utilisateur pour lequel filtrer
        discipline_field: Nom du champ discipline dans le modèle
        federation_field: Nom du champ federation dans le modèle
        
    Returns:
        QuerySet: Le queryset filtré
    """
    # Si l'utilisateur n'est pas authentifié ou est superuser, pas de filtrage
    if not user.is_authenticated or user.is_superuser:
        return queryset
    
    # Récupérer le contexte d'accès
    user_disciplines, discipline_federation_mapping = get_user_access_context(user)
    
    if not user_disciplines:
        # Si l'utilisateur n'a accès Ã  aucune discipline, retourner un queryset vide
        return queryset.none()
    
    # Construction d'une requÃªte complexe avec Q objects
    filter_condition = Q(pk=None)  # Condition toujours fausse pour initialiser
    
    # Pour chaque discipline autorisée
    for discipline in user_disciplines:
        # Récupérer les fédérations autorisées pour cette discipline
        federations = discipline_federation_mapping.get(discipline.id, [])
        
        if federations:
            # Ajouter la condition: (discipline=X AND federation in [Y, Z, ...])
            discipline_condition = Q(**{discipline_field: discipline}) & Q(**{federation_field + '__in': federations})
        else:
            # Si pas de fédération spécifique, juste filtrer par discipline
            discipline_condition = Q(**{discipline_field: discipline})
        
        # Combiner avec OR
        filter_condition |= discipline_condition
    
    # Appliquer le filtre
    return queryset.filter(filter_condition)


def has_access_to_object(user, obj):
    """
    Vérifie si un utilisateur a accès Ã  un objet selon son contexte discipline/fédération
    
    Args:
        user: L'utilisateur Ã  vérifier
        obj: L'objet Ã  vérifier
        
    Returns:
        bool: True si l'utilisateur a accès, False sinon
    """
    if user.is_superuser:
        return True
    
    user_disciplines, discipline_federation_mapping = get_user_access_context(user)
    
    # Récupérer la discipline et la fédération de l'objet
    discipline = getattr(obj, 'discipline', None)
    federation = getattr(obj, 'federation', None)
    
    # Si l'objet n'a pas de discipline ou de fédération, accès autorisé
    if not discipline or not federation:
        return True
    
    # Vérifier si la discipline est dans les disciplines autorisées
    if discipline not in user_disciplines:
        return False
    
    # Vérifier si la fédération est dans les fédérations autorisées pour cette discipline
    federations = discipline_federation_mapping.get(discipline.id, [])
    return federation in federations


def get_filtered_disciplines_for_user(user):
    """
    Retourne les disciplines accessibles Ã  un utilisateur pour les formulaires
    
    Args:
        user: L'utilisateur
        
    Returns:
        QuerySet: Les disciplines accessibles
    """
    if user.is_superuser:
        return Discipline.objects.all()
    
    user_disciplines, _ = get_user_access_context(user)
    return Discipline.objects.filter(id__in=[d.id for d in user_disciplines])


def get_filtered_federations_for_discipline(user, discipline):
    """
    Retourne les fédérations accessibles Ã  un utilisateur pour une discipline donnée
    
    Args:
        user: L'utilisateur
        discipline: La discipline pour laquelle filtrer les fédérations
        
    Returns:
        QuerySet: Les fédérations accessibles
    """
    if user.is_superuser:
        return Federation.objects.all()
    
    user_disciplines, discipline_federation_mapping = get_user_access_context(user)
    
    if discipline not in user_disciplines:
        return Federation.objects.none()
    
    federations = discipline_federation_mapping.get(discipline.id, [])
    return Federation.objects.filter(id__in=[f.id for f in federations]) 

