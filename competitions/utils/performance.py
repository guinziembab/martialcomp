# -*- coding: utf-8 -*-
"""
Utilitaires d'optimisation de performance pour les événements et sondages.
Fournit des fonctions pour optimiser les requêtes et la mise en cache.
"""

import time
import logging
from functools import wraps
from django.db.models import Prefetch, Count, Q
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.utils import timezone
from datetime import timedelta

from competitions.models.event import Event, EventParticipant
from competitions.models.event_planning import EventPoll, PollOption, PollResponse

logger = logging.getLogger(__name__)

# Constantes pour la mise en cache
CACHE_TIMEOUT = getattr(settings, 'EVENT_CACHE_TIMEOUT', 60 * 15)  # 15 minutes par défaut
CACHE_PREFIX = 'event_'
POLL_CACHE_PREFIX = 'poll_'
SURVEY_CACHE_PREFIX = 'survey_'


def measure_execution_time(func):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction.
    Enregistre le temps dans les logs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.debug(f"Exécution de {func.__name__}: {execution_time:.4f} secondes")
        
        return result
    return wrapper


def count_queries(func):
    """
    Décorateur pour compter le nombre de requêtes SQL exécutées par une fonction.
    Nécessite que settings.DEBUG soit True.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        # Réinitialiser le compteur de requêtes
        initial_queries = len(connection.queries)
        
        # Exécuter la fonction
        result = func(*args, **kwargs)
        
        # Calculer le nombre de requêtes exécutées
        final_queries = len(connection.queries)
        num_queries = final_queries - initial_queries
        
        # Calculer le temps total des requêtes
        query_time = sum(float(q.get('time', 0)) for q in connection.queries[initial_queries:final_queries])
        
        logger.debug(f"{func.__name__} a exécuté {num_queries} requêtes en {query_time:.4f} secondes")
        
        # Loguer les requêtes qui prennent le plus de temps
        if num_queries > 5:
            slow_queries = sorted(
                connection.queries[initial_queries:final_queries],
                key=lambda q: float(q.get('time', 0)),
                reverse=True
            )[:3]
            
            for i, query in enumerate(slow_queries):
                logger.debug(f"Requête lente #{i+1} ({float(query.get('time', 0)):.4f}s): {query.get('sql', '')[:100]}...")
        
        return result
    return wrapper


def get_cached_upcoming_events(days=30, user=None):
    """
    Récupère les événements à venir avec mise en cache.
    Optimisé pour les performances avec préchargement des relations.
    
    Args:
        days: Nombre de jours à considérer dans le futur
        user: Utilisateur actuel pour filtrage par organisation
    
    Returns:
        QuerySet d'événements à venir
    """
    cache_key = f"{CACHE_PREFIX}upcoming_{days}"
    
    if user and hasattr(user, 'userprofile'):
        cache_key += f"_user_{user.id}"
    
    # Essayer de récupérer du cache
    cached_events = cache.get(cache_key)
    if cached_events is not None:
        return cached_events
    
    # Calculer les événements à venir
    today = timezone.now().date()
    end_date = today + timedelta(days=days)
    
    events = Event.objects.filter(
        Q(start_date__gte=today) | 
        (Q(start_date__lte=today) & Q(end_date__gte=today))
    ).filter(
        start_date__lte=end_date
    ).select_related(
        'organization', 'created_by'
    ).prefetch_related(
        Prefetch(
            'participants',
            queryset=EventParticipant.objects.select_related('practitioner'),
            to_attr='prefetched_participants'
        )
    ).annotate(
        participants_count=Count('participants')
    ).order_by('start_date', 'start_time')
    
    # Filtrer par organisation si l'utilisateur a un profil
    if user and hasattr(user, 'userprofile') and user.userprofile.club:
        events = events.filter(
            Q(organization__members__user=user) |
            Q(club=user.userprofile.club) |
            Q(is_public=True)
        ).distinct()
    
    # Mettre en cache
    cache.set(cache_key, events, CACHE_TIMEOUT)
    
    return events


def get_cached_event_detail(event_id):
    """
    Récupère les détails d'un événement avec mise en cache.
    Précharge toutes les relations pertinentes pour les vues de détail.
    
    Args:
        event_id: ID de l'événement
    
    Returns:
        Événement avec relations préchargées ou None
    """
    cache_key = f"{CACHE_PREFIX}detail_{event_id}"
    
    # Essayer de récupérer du cache
    cached_event = cache.get(cache_key)
    if cached_event is not None:
        return cached_event
    
    try:
        event = Event.objects.select_related(
            'organization', 'created_by', 'club'
        ).prefetch_related(
            Prefetch(
                'participants',
                queryset=EventParticipant.objects.select_related('practitioner', 'registered_by'),
                to_attr='prefetched_participants'
            ),
            'reminders',
            'surveys'
        ).get(id=event_id)
        
        # Mettre en cache
        cache.set(cache_key, event, CACHE_TIMEOUT)
        
        return event
    except Event.DoesNotExist:
        return None


def get_cached_event_participants(event_id, limit=None):
    """
    Récupère les participants d'un événement avec mise en cache.
    Optimisé pour les performances avec pagination.
    
    Args:
        event_id: ID de l'événement
        limit: Nombre maximum de participants à récupérer
    
    Returns:
        Liste des participants
    """
    cache_key = f"{CACHE_PREFIX}participants_{event_id}"
    if limit:
        cache_key += f"_{limit}"
    
    # Essayer de récupérer du cache
    cached_participants = cache.get(cache_key)
    if cached_participants is not None:
        return cached_participants
    
    # Récupérer les participants avec leurs informations détaillées
    participants = EventParticipant.objects.filter(
        event_id=event_id
    ).select_related(
        'practitioner', 'practitioner__user', 'registered_by'
    ).order_by('registered_at')
    
    if limit:
        participants = participants[:limit]
    
    # Mettre en cache
    cache.set(cache_key, participants, CACHE_TIMEOUT)
    
    return participants


def invalidate_event_cache(event_id):
    """
    Invalide tous les caches liés à un événement spécifique.
    À appeler après toute modification d'un événement.
    
    Args:
        event_id: ID de l'événement
    """
    cache_keys = [
        f"{CACHE_PREFIX}detail_{event_id}",
        f"{CACHE_PREFIX}participants_{event_id}",
    ]
    
    # Invalider aussi les clés des listes qui pourraient contenir cet événement
    for days in [7, 14, 30]:
        cache_keys.append(f"{CACHE_PREFIX}upcoming_{days}")
    
    # Supprimer toutes les clés
    cache.delete_many(cache_keys)
    
    # Loguer l'invalidation
    logger.debug(f"Cache invalidé pour l'événement {event_id}")


def optimize_poll_query(poll_id):
    """
    Optimise la requête pour récupérer un sondage avec toutes ses relations.
    
    Args:
        poll_id: ID du sondage
    
    Returns:
        Sondage avec relations préchargées ou None
    """
    try:
        return EventPoll.objects.select_related(
            'organization', 'created_by', 'event'
        ).prefetch_related(
            Prefetch(
                'options',
                queryset=PollOption.objects.prefetch_related(
                    Prefetch(
                        'responses',
                        queryset=PollResponse.objects.select_related('user')
                    )
                ),
                to_attr='prefetched_options'
            )
        ).get(id=poll_id)
    except EventPoll.DoesNotExist:
        return None


def optimize_event_list_query(request=None):
    """
    Optimise la requête pour la liste des événements en fonction des filtres.
    
    Args:
        request: Objet de requête HTTP pour les filtres
    
    Returns:
        QuerySet optimisé d'événements
    """
    events = Event.objects.all()
    
    # Préchargement de base
    events = events.select_related('organization', 'created_by', 'club')
    
    # Filtrage selon les paramètres de la requête
    if request and request.GET:
        if request.GET.get('title'):
            events = events.filter(title__icontains=request.GET.get('title'))
        
        if request.GET.get('event_type'):
            events = events.filter(event_type=request.GET.get('event_type'))
        
        if request.GET.get('start_date'):
            try:
                start_date = timezone.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
                events = events.filter(start_date__gte=start_date)
            except (ValueError, TypeError):
                pass
        
        if request.GET.get('end_date'):
            try:
                end_date = timezone.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
                events = events.filter(end_date__lte=end_date)
            except (ValueError, TypeError):
                pass
        
        if request.GET.get('organization'):
            events = events.filter(organization_id=request.GET.get('organization'))
    
    # Annotation du nombre de participants
    events = events.annotate(participants_count=Count('participants'))
    
    return events


def paginate_with_optimized_count(queryset, page_size, page_number):
    """
    Optimise la pagination pour de grands ensembles de données.
    Utilise un comptage optimisé pour éviter un COUNT(*) sur toute la table.
    
    Args:
        queryset: QuerySet à paginer
        page_size: Taille de la page
        page_number: Numéro de la page (1-indexé)
    
    Returns:
        Tuple (éléments de la page, nombre total d'éléments, nombre total de pages)
    """
    # Calculer les indices de début et de fin
    start = (page_number - 1) * page_size
    end = start + page_size
    
    # Récupérer les éléments de la page actuelle
    page_items = queryset[start:end]
    
    # Estimer le nombre total d'éléments
    try:
        # Essayer de récupérer le nombre exact
        total_count = queryset.count()
    except:
        # En cas d'erreur, estimer le nombre
        try:
            # Utiliser EXPLAIN pour estimer
            estimate = queryset.query.sql_with_params()[0]
            estimate = estimate.lower().replace('select', 'explain select', 1)
            cursor = connection.cursor()
            cursor.execute(estimate)
            estimated_count = cursor.fetchone()[0]
            total_count = int(estimated_count) if estimated_count else len(page_items) * page_number
        except:
            # Si tout échoue, utiliser une estimation basique
            total_count = len(page_items) * page_number
    
    # Calculer le nombre total de pages
    total_pages = (total_count + page_size - 1) // page_size
    
    return page_items, total_count, total_pages


@measure_execution_time
def bulk_prefetch_event_data(event_ids):
    """
    Précharge en masse les données pour plusieurs événements.
    Optimisé pour réduire le nombre de requêtes lors de l'affichage de listes.
    
    Args:
        event_ids: Liste d'IDs d'événements
    
    Returns:
        Dictionnaire d'événements avec toutes leurs données associées
    """
    # Récupérer les événements avec leurs relations
    events = Event.objects.filter(id__in=event_ids).select_related(
        'organization', 'created_by', 'club'
    ).prefetch_related(
        Prefetch(
            'participants',
            queryset=EventParticipant.objects.select_related('practitioner'),
            to_attr='prefetched_participants'
        )
    ).annotate(
        participants_count=Count('participants')
    )
    
    # Organiser en dictionnaire pour un accès rapide
    events_dict = {str(event.id): event for event in events}
    
    return events_dict


def get_optimized_survey_results(survey_id):
    """
    Récupère les résultats d'un sondage de manière optimisée.
    Calcule les statistiques de manière efficace.
    
    Args:
        survey_id: ID du sondage
    
    Returns:
        Dictionnaire de résultats et statistiques
    """
    from competitions.models.event import EventSurvey, SurveyQuestion, SurveyResponse, QuestionResponse
    
    cache_key = f"{SURVEY_CACHE_PREFIX}results_{survey_id}"
    
    # Essayer de récupérer du cache
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        return cached_results
    
    # Requête optimisée
    survey = EventSurvey.objects.select_related('event', 'created_by').get(id=survey_id)
    questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')
    responses = SurveyResponse.objects.filter(survey=survey).select_related('participant')
    
    # Calculer les statistiques générales
    stats = {
        'total_responses': responses.count(),
        'completion_rate': 0,
        'avg_completion_time': None,
        'questions': {}
    }
    
    # Calculer le taux de complétion si l'événement a des participants
    if survey.event and hasattr(survey.event, 'participants_count') and survey.event.participants_count > 0:
        stats['completion_rate'] = (stats['total_responses'] / survey.event.participants_count) * 100
    
    # Temps moyen de complétion
    completion_times = [r.completion_time for r in responses if r.completion_time]
    if completion_times:
        total_seconds = sum(ct.total_seconds() for ct in completion_times)
        stats['avg_completion_time'] = total_seconds / len(completion_times)
    
    # Statistiques par question
    for question in questions:
        q_responses = QuestionResponse.objects.filter(question=question)
        
        question_stats = {
            'total': q_responses.count(),
            'type': question.question_type,
        }
        
        # Statistiques spécifiques selon le type de question
        if question.question_type in ['single_choice', 'multiple_choice']:
            choice_counts = {}
            for qr in q_responses:
                choices = qr.choice_response
                if isinstance(choices, list):
                    for choice in choices:
                        choice_counts[choice] = choice_counts.get(choice, 0) + 1
                elif choices:  # Single choice
                    choice_counts[choices] = choice_counts.get(choices, 0) + 1
            
            question_stats['choice_counts'] = choice_counts
            
        elif question.question_type in ['rating', 'scale']:
            from django.db.models import Avg
            avg_rating = q_responses.aggregate(avg=Avg('numeric_response'))['avg']
            
            # Distribution des notes
            rating_distribution = {}
            for qr in q_responses:
                if qr.numeric_response is not None:
                    rating = qr.numeric_response
                    rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
            
            question_stats['avg_rating'] = avg_rating
            question_stats['rating_distribution'] = rating_distribution
            
        elif question.question_type == 'date':
            # Regrouper par date
            date_counts = {}
            for qr in q_responses:
                if qr.date_response:
                    date_str = qr.date_response.isoformat()
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
            
            question_stats['date_counts'] = date_counts
        
        stats['questions'][question.id] = question_stats
    
    # Mettre en cache
    cache.set(cache_key, stats, CACHE_TIMEOUT)
    
    return stats