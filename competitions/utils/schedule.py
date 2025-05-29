"""
Utilitaires pour la gestion des plannings de compétition.
Contient des fonctions pour générer des plannings, optimiser l'utilisation des tatamis
et détecter les conflits.
"""
from datetime import datetime, timedelta
import random


def generate_match_schedule(category_schedule):
    """
    Génère automatiquement le planning des matchs pour une catégorie.
    
    Args:
        category_schedule: Le planning de catégorie
    
    Returns:
        Liste des créneaux horaires générés
    """
    # Import à l'intérieur de la fonction pour éviter des imports circulaires
    from competitions.models.schedule import MatchTimeSlot
    
    # Récupérer les matchs de la catégorie
    matches = category_schedule.category.matches.all().order_by('order')
    
    if not matches.exists():
        raise ValueError("Aucun match à planifier pour cette catégorie.")
    
    # Récupérer l'heure de début de la catégorie
    start_time = category_schedule.estimated_start_time
    if not start_time:
        # Si aucune heure de début n'est spécifiée, utiliser l'heure de début de la compétition
        start_time = category_schedule.competition_schedule.start_time
    
    # Récupérer la durée par défaut des matchs
    match_duration = category_schedule.competition_schedule.match_duration
    
    # Générer les créneaux horaires
    created_slots = []
    current_time = start_time
    
    for match in matches:
        # Créer le créneau horaire
        end_time = add_minutes_to_time(current_time, match_duration)
        
        time_slot = MatchTimeSlot.objects.create(
            category_schedule=category_schedule,
            match=match,
            start_time=current_time,
            end_time=end_time,
            status='scheduled'
        )
        
        created_slots.append(time_slot)
        
        # Ajouter la durée du match + 5 minutes de transition
        current_time = add_minutes_to_time(end_time, 5)
    
    # Mettre à jour l'heure de fin estimée de la catégorie
    category_schedule.estimated_end_time = current_time
    category_schedule.save()
    
    return created_slots


def optimize_tatami_usage(competition_schedule):
    """
    Optimise l'utilisation des tatamis pour réduire la durée totale de la compétition.
    
    Args:
        competition_schedule: Le planning de la compétition
        
    Returns:
        Liste des plannings de catégorie mis à jour
    """
    from competitions.models.schedule import CategorySchedule
    
    # Récupérer les tatamis
    tatamis = competition_schedule.tatami_schedules.all()
    if not tatamis.exists():
        raise ValueError("Aucun tatami disponible pour cette compétition.")
    
    # Récupérer les plannings de catégorie et les trier par nombre de participants (décroissant)
    category_schedules = list(CategorySchedule.objects.filter(
        competition_schedule=competition_schedule
    ).select_related('category'))
    
    # Trier par nombre de participants
    category_schedules.sort(
        key=lambda cs: cs.category.registrations.count() if hasattr(cs.category, 'registrations') else 0,
        reverse=True
    )
    
    # Assigner les catégories aux tatamis
    tatami_end_times = {tatami.id: competition_schedule.start_time for tatami in tatamis}
    updated_schedules = []
    
    for cs in category_schedules:
        # Trouver le tatami qui finit le plus tôt
        tatami_id = min(tatami_end_times, key=tatami_end_times.get)
        tatami = next(t for t in tatamis if t.id == tatami_id)
        
        # Assigner la catégorie à ce tatami
        cs.tatami = tatami
        cs.estimated_start_time = tatami_end_times[tatami_id]
        cs.save()
        updated_schedules.append(cs)
        
        # Estimer la durée de la catégorie
        duration_minutes = estimate_category_duration(cs)
        
        # Mettre à jour l'heure de fin du tatami
        end_time = add_minutes_to_time(cs.estimated_start_time, duration_minutes)
        tatami_end_times[tatami_id] = end_time
        
        # Mettre à jour l'heure de fin estimée
        cs.estimated_end_time = end_time
        cs.save()
    
    return updated_schedules


def detect_schedule_conflicts(competition_schedule):
    """
    Détecte les conflits dans le planning.
    
    Args:
        competition_schedule: Le planning de la compétition
        
    Returns:
        Liste des conflits détectés
    """
    from competitions.models.schedule import CategorySchedule
    
    conflicts = []
    
    # Récupérer tous les plannings de catégorie
    category_schedules = CategorySchedule.objects.filter(
        competition_schedule=competition_schedule
    ).select_related('category', 'tatami')
    
    # 1. Vérifier les chevauchements sur les tatamis
    tatami_schedules = {}
    for cs in category_schedules:
        if not cs.tatami or not cs.estimated_start_time or not cs.estimated_end_time:
            continue
            
        tatami_id = cs.tatami.id
        if tatami_id not in tatami_schedules:
            tatami_schedules[tatami_id] = []
            
        tatami_schedules[tatami_id].append(cs)
    
    # Vérifier les chevauchements pour chaque tatami
    for tatami_id, schedules in tatami_schedules.items():
        sorted_schedules = sorted(schedules, key=lambda cs: cs.estimated_start_time)
        
        for i in range(len(sorted_schedules) - 1):
            current = sorted_schedules[i]
            next_schedule = sorted_schedules[i + 1]
            
            if current.estimated_end_time > next_schedule.estimated_start_time:
                conflicts.append({
                    'type': 'tatami_overlap',
                    'tatami_id': tatami_id,
                    'tatami_name': current.tatami.name,
                    'category1_id': current.category.id,
                    'category1_name': current.category.name,
                    'category2_id': next_schedule.category.id,
                    'category2_name': next_schedule.category.name,
                    'start_time1': current.estimated_start_time,
                    'end_time1': current.estimated_end_time,
                    'start_time2': next_schedule.estimated_start_time,
                    'end_time2': next_schedule.estimated_end_time,
                    'message': f"Chevauchement sur le tatami {current.tatami.name} entre {current.category.name} et {next_schedule.category.name}"
                })
    
    # 2. Vérifier les conflits de participants (un même participant dans deux catégories en même temps)
    # Cette vérification est plus complexe et nécessiterait une analyse de tous les participants
    # On peut la simplifier en vérifiant juste si deux catégories qui se chevauchent ont des participants en commun
    
    # Créer une liste de toutes les paires de catégories qui se chevauchent
    overlapping_pairs = []
    for cs1 in category_schedules:
        if not cs1.estimated_start_time or not cs1.estimated_end_time:
            continue
            
        for cs2 in category_schedules:
            if cs1.id >= cs2.id or not cs2.estimated_start_time or not cs2.estimated_end_time:
                continue
                
            # Vérifier si les horaires se chevauchent
            if (cs1.estimated_start_time <= cs2.estimated_end_time and
                cs1.estimated_end_time >= cs2.estimated_start_time):
                overlapping_pairs.append((cs1, cs2))
    
    # Pour chaque paire, vérifier s'il y a des participants en commun
    for cs1, cs2 in overlapping_pairs:
        try:
            # Récupérer les participants des deux catégories
            participants1 = set(cs1.category.registrations.values_list('practitioner_id', flat=True))
            participants2 = set(cs2.category.registrations.values_list('practitioner_id', flat=True))
            
            # Trouver les participants en commun
            common_participants = participants1.intersection(participants2)
            
            if common_participants:
                conflicts.append({
                    'type': 'participant_conflict',
                    'category1_id': cs1.category.id,
                    'category1_name': cs1.category.name,
                    'category2_id': cs2.category.id,
                    'category2_name': cs2.category.name,
                    'participant_count': len(common_participants),
                    'message': f"{len(common_participants)} participants en commun entre {cs1.category.name} et {cs2.category.name} avec des horaires qui se chevauchent"
                })
        except Exception as e:
            conflicts.append({
                'type': 'error',
                'category1_id': cs1.category.id,
                'category1_name': cs1.category.name,
                'category2_id': cs2.category.id,
                'category2_name': cs2.category.name,
                'message': f"Erreur lors de la vérification des participants en commun: {str(e)}"
            })
    
    return conflicts


def estimate_category_duration(category_schedule):
    """
    Estime la durée d'une catégorie en fonction du nombre de participants et du type de compétition.
    
    Args:
        category_schedule: Le planning de catégorie
        
    Returns:
        Durée estimée en minutes
    """
    category = category_schedule.category
    
    # Récupérer le nombre de participants
    try:
        participants_count = category.registrations.count()
    except:
        participants_count = 0
    
    # Si pas de participants, durée minimale
    if participants_count == 0:
        return 30  # 30 minutes minimum
    
    # Calculer le nombre de matchs
    if hasattr(category, 'competition_type') and category.competition_type:
        competition_type = category.competition_type.name.lower()
        
        # Selon le type de compétition
        if 'poule' in competition_type:
            # Système de poules
            num_matches = (participants_count * (participants_count - 1)) // 2
        elif 'elimination' in competition_type:
            # Système à élimination directe
            num_matches = participants_count - 1
        else:
            # Système par défaut
            num_matches = participants_count
    else:
        # Système par défaut
        num_matches = participants_count
    
    # Durée moyenne par match
    match_duration = category_schedule.competition_schedule.match_duration or 5  # 5 minutes par défaut
    
    # Temps de transition entre les matchs
    transition_time = 2  # 2 minutes entre les matchs
    
    # Durée totale
    total_duration = num_matches * match_duration + (num_matches - 1) * transition_time
    
    # Ajouter du temps pour les cérémonies (ouverture, podium)
    ceremony_time = 15
    
    # Durée totale avec une marge
    return max(30, total_duration + ceremony_time)


def add_minutes_to_time(time_obj, minutes):
    """
    Ajoute des minutes à un objet time.
    
    Args:
        time_obj: Objet time
        minutes: Nombre de minutes à ajouter
        
    Returns:
        Nouvel objet time
    """
    datetime_obj = datetime.combine(datetime.today(), time_obj)
    datetime_obj += timedelta(minutes=minutes)
    return datetime_obj.time()


def generate_pool_system(participants, pool_size=4):
    """
    Génère un système de poules pour les participants.
    
    Args:
        participants: Liste des participants
        pool_size: Taille des poules
        
    Returns:
        Liste des poules générées
    """
    # Mélanger les participants
    shuffled = list(participants)
    random.shuffle(shuffled)
    
    # Créer les poules
    pools = []
    for i in range(0, len(shuffled), pool_size):
        pool = shuffled[i:i+pool_size]
        pools.append(pool)
    
    return pools


def generate_time_slots(date, start_time, end_time, slot_duration=30, buffer_duration=5):
    """
    Génère des créneaux horaires pour une journée spécifique.
    
    Args:
        date: Date pour laquelle générer les créneaux
        start_time: Heure de début
        end_time: Heure de fin
        slot_duration: Durée d'un créneau en minutes
        buffer_duration: Temps tampon entre les créneaux en minutes
        
    Returns:
        Liste des créneaux horaires générés
    """
    slots = []
    
    current_time = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)
    
    while current_time < end_datetime:
        slot_end = current_time + timedelta(minutes=slot_duration)
        
        if slot_end <= end_datetime:
            slots.append({
                'start_time': current_time.time(),
                'end_time': slot_end.time(),
                'duration': slot_duration
            })
        
        current_time = slot_end + timedelta(minutes=buffer_duration)
    
    return slots


def reorder_schedule_by_priority(competition_schedule):
    """
    Réorganise le planning en fonction des priorités des catégories.
    
    Args:
        competition_schedule: Le planning de la compétition
        
    Returns:
        Liste des plannings de catégorie mis à jour
    """
    from competitions.models.schedule import CategorySchedule
    
    # Récupérer les catégories et les trier par priorité
    category_schedules = CategorySchedule.objects.filter(
        competition_schedule=competition_schedule
    ).select_related('category')
    
    # Fonction de tri personnalisée
    def sort_key(cs):
        # Priorité par défaut
        priority = 0
        
        # Les catégories avec plus de participants ont une priorité plus élevée
        if hasattr(cs.category, 'registrations'):
            priority += cs.category.registrations.count()
        
        # Les catégories de jeunes passent tôt
        if hasattr(cs.category, 'min_age') and cs.category.min_age is not None:
            if cs.category.min_age < 12:
                priority += 100
            elif cs.category.min_age < 16:
                priority += 50
        
        return priority
    
    # Trier les catégories
    sorted_schedules = sorted(category_schedules, key=sort_key, reverse=True)
    
    # Réorganiser les catégories par tatami
    tatami_schedules = {}
    for cs in sorted_schedules:
        if cs.tatami:
            tatami_id = cs.tatami.id
            if tatami_id not in tatami_schedules:
                tatami_schedules[tatami_id] = []
            tatami_schedules[tatami_id].append(cs)
    
    # Mettre à jour les horaires pour chaque tatami
    updated_schedules = []
    
    for tatami_id, schedules in tatami_schedules.items():
        current_time = competition_schedule.start_time
        
        for i, cs in enumerate(schedules):
            cs.estimated_start_time = current_time
            cs.order = i + 1
            
            # Estimer la durée de la catégorie
            duration_minutes = estimate_category_duration(cs)
            
            # Calculer l'heure de fin
            end_time = add_minutes_to_time(current_time, duration_minutes)
            cs.estimated_end_time = end_time
            
            # Mettre à jour
            cs.save()
            updated_schedules.append(cs)
            
            # Avancer l'heure
            current_time = add_minutes_to_time(end_time, 5)  # 5 minutes de pause
    
    return updated_schedules