# Dans competitions/utils/competitions.py

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

def get_competition_progress(competition):
    """
    Calcule la progression globale d'une compétition.
    Retourne un dictionnaire avec les pourcentages d'avancement.
    
    Args:
        competition: L'instance de Competition Ã  analyser
        
    Returns:
        dict: Dictionnaire contenant les informations de progression
    """
    # Import ici pour éviter l'import circulaire
    from apps.competitions.models import TechnicalPerformance, Match
    
    result = {
        'total_percent': 0,
        'technical_percent': 0,
        'combat_percent': 0,
        'total_categories': 0,
        'completed_categories': 0
    }
    
    # Compter les catégories
    categories = competition.categories.all()
    total_categories = categories.count()
    result['total_categories'] = total_categories
    
    if total_categories == 0:
        return result
    
    # Calculer la progression des performances techniques
    if hasattr(competition, 'technical_performances'):
        total_performances = TechnicalPerformance.objects.filter(competition=competition).count()
        completed_performances = TechnicalPerformance.objects.filter(
            competition=competition, 
            status__in=['completed', 'disqualified']
        ).count()
        
        if total_performances > 0:
            result['technical_percent'] = int((completed_performances / total_performances) * 100)
    
    # Calculer la progression des combats
    if hasattr(competition, 'matches'):
        total_matches = Match.objects.filter(competition=competition).count()
        completed_matches = Match.objects.filter(
            competition=competition,
            status__in=['completed', 'cancelled']
        ).count()
        
        if total_matches > 0:
            result['combat_percent'] = int((completed_matches / total_matches) * 100)
    
    # Compter les catégories terminées
    completed_categories = 0
    for category in categories:
        # Une catégorie est considérée comme terminée si tous ses matchs/performances sont terminés
        if hasattr(category, 'performances'):
            total_cat_perfs = category.performances.count()
            if total_cat_perfs > 0:
                completed_cat_perfs = category.performances.filter(
                    status__in=['completed', 'disqualified']
                ).count()
                
                if completed_cat_perfs == total_cat_perfs:
                    completed_categories += 1
        
        if hasattr(category, 'matches'):
            total_cat_matches = category.matches.count()
            if total_cat_matches > 0:
                completed_cat_matches = category.matches.filter(
                    status__in=['completed', 'cancelled']
                ).count()
                
                if completed_cat_matches == total_cat_matches:
                    completed_categories += 1
    
    result['completed_categories'] = completed_categories
    
    # Calculer le pourcentage global
    total_elements = 0
    completed_elements = 0
    
    if hasattr(competition, 'technical_performances'):
        total_elements += TechnicalPerformance.objects.filter(competition=competition).count()
        completed_elements += TechnicalPerformance.objects.filter(
            competition=competition,
            status__in=['completed', 'disqualified']
        ).count()
    
    if hasattr(competition, 'matches'):
        total_elements += Match.objects.filter(competition=competition).count()
        completed_elements += Match.objects.filter(
            competition=competition,
            status__in=['completed', 'cancelled']
        ).count()
    
    if total_elements > 0:
        result['total_percent'] = int((completed_elements / total_elements) * 100)
    
    return result


def get_competition_statistics(competition):
    """
    Calcule diverses statistiques pour une compétition.
    
    Args:
        competition: L'instance de Competition Ã  analyser
        
    Returns:
        dict: Dictionnaire contenant les statistiques de la compétition
    """
    # Import ici pour éviter l'import circulaire
    from apps.competitions.models import CompetitionRegistration, JudgeAssignment
    
    stats = {
        'participants_count': 0,
        'clubs_count': 0,
        'categories_count': 0,
        'judges_count': 0,
        'performances_today': 0,
        'registrations_pending': 0,
        'is_active': False
    }
    
    # Vérifier si la compétition est active
    today = timezone.now().date()
    stats['is_active'] = (
        competition.start_date <= today and 
        (competition.end_date is None or competition.end_date >= today)
    )
    
    # Compter les catégories
    stats['categories_count'] = competition.categories.count()
    
    # Compter les participants (inscriptions validées)
    if hasattr(competition, 'registrations'):
        stats['participants_count'] = CompetitionRegistration.objects.filter(
            competition=competition,
            status='approved',
            is_competitor=True
        ).count()
        
        # Compter les inscriptions en attente
        stats['registrations_pending'] = CompetitionRegistration.objects.filter(
            competition=competition,
            status='pending'
        ).count()
        
        # Compter les clubs participants
        stats['clubs_count'] = CompetitionRegistration.objects.filter(
            competition=competition,
            status='approved'
        ).values('practitioner__club').distinct().count()
    
    # Compter les juges
    if hasattr(competition, 'categories'):
        stats['judges_count'] = JudgeAssignment.objects.filter(
            category__competition=competition
        ).values('judge').distinct().count()
    
    # Compter les performances d'aujourd'hui
    if hasattr(competition, 'technical_performances'):
        from apps.competitions.models import TechnicalPerformance
        
        stats['performances_today'] = TechnicalPerformance.objects.filter(
            competition=competition,
            start_time__date=today
        ).count()
    
    return stats

def generate_match_schedule(competition, categories=None, date=None, start_time=None, end_time=None):
    """
    Génère un planning de matchs pour une compétition.
    
    Args:
        competition: Instance de Competition
        categories: Liste optionnelle de CompetitionCategory (si None, toutes les catégories)
        date: Date optionnelle pour le planning (si None, utilise la date de début de la compétition)
        start_time: Heure de début optionnelle
        end_time: Heure de fin optionnelle
        
    Returns:
        Liste d'objets représentant les créneaux de matchs.
    """
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Utiliser les valeurs par défaut si nécessaire
    if not categories:
        categories = competition.categories.all()
    
    if not date:
        date = competition.start_date
        
    if not start_time:
        start_time = competition.start_time or datetime.strptime('09:00', '%H:%M').time()
        
    if not end_time:
        end_time = competition.end_time or datetime.strptime('18:00', '%H:%M').time()
    
    # Calculer la durée disponible en minutes
    start_datetime = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)
    total_minutes = (end_datetime - start_datetime).total_seconds() / 60
    
    # Estimer le temps par catégorie
    category_count = categories.count()
    if category_count == 0:
        return []
        
    # Donner 30 minutes par défaut par catégorie, ou ajuster selon le temps disponible
    minutes_per_category = min(30, total_minutes / category_count)
    
    # Générer les créneaux
    timeslots = []
    current_time = start_datetime
    
    for category in categories:
        # Créer un créneau pour cette catégorie
        slot_end_time = current_time + timedelta(minutes=minutes_per_category)
        
        # S'assurer de ne pas dépasser la fin prévue
        if slot_end_time > end_datetime:
            slot_end_time = end_datetime
            
        timeslot = {
            'category': category,
            'date': date,
            'start_time': current_time.time(),
            'end_time': slot_end_time.time(),
            'duration_minutes': minutes_per_category
        }
        
        timeslots.append(timeslot)
        
        # Avancer l'heure actuelle
        current_time = slot_end_time
        
        # ArrÃªter si on a atteint la fin de la journée
        if current_time >= end_datetime:
            break
    
    return timeslots

def optimize_tatami_usage(competition, date=None, available_tatamis=None):
    """
    Optimise l'utilisation des tatamis pour une compétition donnée.
    
    Cette fonction répartit les catégories sur les tatamis disponibles
    de manière Ã  minimiser le temps total de la compétition.
    
    Args:
        competition: Instance de Competition
        date: Date optionnelle pour la planification
        available_tatamis: Nombre de tatamis disponibles (par défaut : utilise tous les tatamis de la compétition)
        
    Returns:
        Dictionnaire avec les attributions de tatami pour chaque catégorie
    """
    from django.utils import timezone
    from collections import defaultdict
    
    # Utiliser les valeurs par défaut si nécessaire
    if not date:
        date = competition.start_date
    
    if not available_tatamis:
        # Déterminer le nombre de tatamis disponibles pour cette compétition
        # (logique simplifiée, Ã  adapter selon votre modèle)
        available_tatamis = 3  # Par défaut, supposons 3 tatamis
    
    # Récupérer toutes les catégories de la compétition
    categories = competition.categories.all()
    
    # Estimer la durée de chaque catégorie (en minutes)
    # Cette estimation pourrait Ãªtre basée sur le nombre de participants, le type de compétition, etc.
    category_durations = {}
    for category in categories:
        # Exemple simple : 10 minutes de base + 5 minutes par participant
        participant_count = category.registrations.count()
        duration = 10 + (participant_count * 5)
        category_durations[category.id] = duration
    
    # Algorithme simple de répartition des tatamis
    # Nous utilisons l'algorithme "Greedy" pour l'attribution des tatamis
    tatami_assignments = {}
    tatami_loads = defaultdict(int)  # Charge actuelle de chaque tatami en minutes
    
    # Trier les catégories par durée décroissante
    sorted_categories = sorted(
        categories, 
        key=lambda c: category_durations[c.id], 
        reverse=True
    )
    
    # Attribuer chaque catégorie au tatami le moins chargé
    for category in sorted_categories:
        # Trouver le tatami avec la charge minimale
        min_load_tatami = min(
            range(1, available_tatamis + 1), 
            key=lambda t: tatami_loads[t]
        )
        
        # Attribuer la catégorie Ã  ce tatami
        tatami_assignments[category.id] = min_load_tatami
        
        # Mettre Ã  jour la charge de ce tatami
        tatami_loads[min_load_tatami] += category_durations[category.id]
    
    # Calculer les heures de début et de fin pour chaque catégorie
    schedule = {}
    start_times = defaultdict(lambda: timezone.datetime.combine(date, timezone.datetime.min.time()).replace(hour=9, minute=0))
    
    for category in categories:
        tatami = tatami_assignments[category.id]
        duration = category_durations[category.id]
        
        start = start_times[tatami]
        end = start + timezone.timedelta(minutes=duration)
        
        schedule[category.id] = {
            'category': category,
            'tatami': tatami,
            'start_time': start.time(),
            'end_time': end.time(),
            'duration_minutes': duration
        }
        
        # Mettre Ã  jour l'heure de début pour le prochain match sur ce tatami
        start_times[tatami] = end
    
    return {
        'tatami_assignments': tatami_assignments,
        'tatami_loads': dict(tatami_loads),
        'schedule': schedule,
        'total_duration': max(tatami_loads.values()) if tatami_loads else 0
    }
    
def detect_schedule_conflicts(schedules, participants=None):
    """
    Détecte les conflits d'horaire dans un planning de compétition.
    
    Cette fonction identifie les situations oÃ¹:
    - Un mÃªme participant est prévu dans deux catégories qui se chevauchent
    - Un mÃªme tatami est utilisé pour deux catégories qui se chevauchent
    - Un mÃªme juge est affecté Ã  deux catégories qui se chevauchent
    
    Args:
        schedules: Liste de dictionnaires contenant les informations de planification
                  (category, tatami, start_time, end_time)
        participants: Dictionnaire optionnel avec les participations par catégorie
                     {category_id: [participant_ids]}
                     
    Returns:
        Dictionnaire des conflits détectés par type
    """
    from datetime import datetime, time
    
    # Initialiser le dictionnaire des conflits
    conflicts = {
        'tatami_conflicts': [],
        'participant_conflicts': [],
        'judge_conflicts': []
    }
    
    # Fonction pour vérifier si deux créneaux se chevauchent
    def time_slots_overlap(slot1, slot2):
        # Convertir les objets time en datetime pour la comparaison
        date1 = datetime.now().date()
        start1 = datetime.combine(date1, slot1['start_time'])
        end1 = datetime.combine(date1, slot1['end_time'])
        
        start2 = datetime.combine(date1, slot2['start_time'])
        end2 = datetime.combine(date1, slot2['end_time'])
        
        # Vérifier le chevauchement
        return start1 < end2 and start2 < end1
    
    # Vérifier les conflits de tatami
    for i, slot1 in enumerate(schedules):
        for j, slot2 in enumerate(schedules):
            if i >= j:  # Ã‰viter les comparaisons en double
                continue
                
            # Si les deux créneaux sont sur le mÃªme tatami et se chevauchent
            if slot1.get('tatami') == slot2.get('tatami') and time_slots_overlap(slot1, slot2):
                conflicts['tatami_conflicts'].append({
                    'slot1': slot1,
                    'slot2': slot2,
                    'type': 'tatami',
                    'message': f"Conflit de tatami {slot1.get('tatami')} entre {slot1['category'].name} et {slot2['category'].name}"
                })
    
    # Vérifier les conflits de participants (si fournies)
    if participants:
        for i, slot1 in enumerate(schedules):
            for j, slot2 in enumerate(schedules):
                if i >= j:  # Ã‰viter les comparaisons en double
                    continue
                    
                # Si les créneaux se chevauchent
                if time_slots_overlap(slot1, slot2):
                    # Vérifier si des participants sont communs aux deux catégories
                    cat1_participants = participants.get(slot1['category'].id, [])
                    cat2_participants = participants.get(slot2['category'].id, [])
                    
                    # Trouver les participants en commun
                    common_participants = set(cat1_participants).intersection(set(cat2_participants))
                    
                    if common_participants:
                        conflicts['participant_conflicts'].append({
                            'slot1': slot1,
                            'slot2': slot2,
                            'type': 'participant',
                            'participants': common_participants,
                            'message': f"Conflit de participants entre {slot1['category'].name} et {slot2['category'].name}"
                        })
    
    # Vérifier les conflits de juges
    # (Cette partie nécessiterait des informations sur l'attribution des juges)
    
    return conflicts

