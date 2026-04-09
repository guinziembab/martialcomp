"""
Vue corrigée pour competition_management_pro
Résolution du problème d'affichage des catégories, types et inscriptions

PROBLÈME IDENTIFIÉ:
- Les proxies créés pour competition.categories et competition.competition_types ne s'intègrent 
  pas correctement avec le système de templates Django
- L'appel de .all() sur les proxies ne retourne pas les données attendues par le template

SOLUTION:
- Charger les données directement depuis la base de données
- Les passer au contexte sous forme de listes simples ou de querysets Django natifs
- Éviter les proxies complexes
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import translation
from django.db.models import Prefetch, Count
import logging

logger = logging.getLogger(__name__)


@login_required
def competition_management_pro(request, competition_id):
    """
    Vue de gestion professionnelle d'une compétition
    Version corrigée avec chargement direct des données
    """
    try:
        from apps.competitions.models import (
            Competition, 
            CompetitionCategory, 
            CompetitionType,
            CompetitionRegistration,
            Judge,
            Club
        )
        
        # Charger la compétition de base sans ses relations
        competition = get_object_or_404(Competition, id=competition_id)
        
        # ====================================================================
        # CHARGEMENT DES CATÉGORIES - VERSION CORRIGÉE
        # ====================================================================
        # Charger directement les catégories avec leurs relations
        categories = CompetitionCategory.objects.filter(
            competition_id=competition_id
        ).select_related(
            'competition_type',
            'template'
        ).order_by('competition_type__name', 'name')
        
        # Convertir en liste pour l'affichage
        categories_list = list(categories)
        logger.info(f"Compétition {competition_id}: {len(categories_list)} catégories chargées")
        
        # ====================================================================
        # CHARGEMENT DES TYPES DE COMPÉTITION - VERSION CORRIGÉE
        # ====================================================================
        # Récupérer les IDs des types utilisés
        competition_type_ids = list(
            categories.values_list('competition_type_id', flat=True).distinct()
        )
        
        # Charger les types avec leurs catégories
        if competition_type_ids:
            competition_types = CompetitionType.objects.filter(
                id__in=competition_type_ids
            ).prefetch_related(
                Prefetch(
                    'categories',
                    queryset=CompetitionCategory.objects.filter(
                        competition_id=competition_id
                    )
                )
            ).annotate(
                categories_count=Count('categories')
            )
            competition_types_list = list(competition_types)
        else:
            competition_types_list = []
        
        logger.info(f"Compétition {competition_id}: {len(competition_types_list)} types chargés")
        
        # ====================================================================
        # CHARGEMENT DES INSCRIPTIONS - VERSION CORRIGÉE
        # ====================================================================
        registrations = CompetitionRegistration.objects.filter(
            competition_id=competition_id
        ).select_related(
            'practitioner',
            'practitioner__club'
        ).prefetch_related(
            'categories',
            'competition_types'
        ).order_by('registration_date')
        
        registrations_list = list(registrations)
        registrations_count = len(registrations_list)
        registrations_exists = registrations_count > 0
        
        logger.info(f"Compétition {competition_id}: {registrations_count} inscriptions chargées")
        
        # ====================================================================
        # CHARGEMENT DES CLUBS
        # ====================================================================
        # Récupérer les clubs ayant des inscriptions
        club_ids = registrations.values_list(
            'practitioner__club_id', flat=True
        ).distinct()
        clubs = Club.objects.filter(id__in=club_ids).order_by('name')
        clubs_list = list(clubs)
        
        # ====================================================================
        # CHARGEMENT DES JUGES ET ARBITRES - VERSION CORRIGÉE
        # ====================================================================
        try:
            # Juges techniques
            technical_judges = list(
                Judge.objects.filter(
                    is_technical_judge=True,
                    active=True
                ).select_related('user').order_by('user__last_name', 'user__first_name')
            )
            
            # Arbitres de combat
            combat_referees = list(
                Judge.objects.filter(
                    is_combat_referee=True,
                    active=True
                ).select_related('user').order_by('user__last_name', 'user__first_name')
            )
            
            logger.info(
                f"Compétition {competition_id}: {len(technical_judges)} juges techniques, "
                f"{len(combat_referees)} arbitres de combat"
            )
        except Exception as e:
            logger.error(f"Erreur lors du chargement des juges: {str(e)}")
            technical_judges = []
            combat_referees = []
        
        # ====================================================================
        # CONSTRUCTION DU CONTEXTE - VERSION SIMPLIFIÉE
        # ====================================================================
        context = {
            # Compétition de base
            'competition': competition,
            
            # Données chargées - ATTENTION: Passer directement les querysets/listes
            # pas de proxies ni de wrapping
            'categories': categories,  # Queryset Django natif
            'competition_types': competition_types if competition_type_ids else CompetitionType.objects.none(),
            
            # Statistiques pour les inscriptions
            'registrations_count': registrations_count,
            'registrations_list': registrations_list,
            'registrations_exists': registrations_exists,
            
            # Clubs
            'clubs': clubs_list,
            
            # Juges et arbitres
            'technical_judges': technical_judges,
            'combat_referees': combat_referees,
            
            # Langue
            'LANGUAGE_CODE': translation.get_language() or 'fr',
        }
        
        # ====================================================================
        # LOGS DE DEBUG
        # ====================================================================
        logger.info(f"""
        ===== CONTEXTE COMPETITION {competition_id} =====
        - Catégories: {len(categories_list)} items
        - Types: {len(competition_types_list)} items
        - Inscriptions: {registrations_count} items
        - Clubs: {len(clubs_list)} items
        - Juges techniques: {len(technical_judges)} items
        - Arbitres combat: {len(combat_referees)} items
        ================================================
        """)
        
        return render(
            request,
            'competitions/club/competition_management_pro.html',
            context
        )
        
    except Exception as e:
        logger.error(f"Erreur dans competition_management_pro pour compétition {competition_id}: {str(e)}")
        logger.exception(e)
        
        # En cas d'erreur, retourner quand même une page avec des listes vides
        return render(
            request,
            'competitions/club/competition_management_pro.html',
            {
                'competition': competition if 'competition' in locals() else None,
                'categories': CompetitionCategory.objects.none(),
                'competition_types': CompetitionType.objects.none(),
                'registrations_count': 0,
                'registrations_list': [],
                'registrations_exists': False,
                'clubs': [],
                'technical_judges': [],
                'combat_referees': [],
                'LANGUAGE_CODE': translation.get_language() or 'fr',
                'error': str(e)
            }
        )


# ====================================================================
# NOTES IMPORTANTES POUR LA CORRECTION
# ====================================================================
"""
POURQUOI CETTE VERSION FONCTIONNE:

1. PAS DE PROXIES COMPLEXES
   - Les proxies avec __iter__, __len__, etc. ne s'intègrent pas bien avec Django templates
   - On passe directement les querysets Django natifs ou des listes Python

2. QUERYSETS NATIFS POUR LE TEMPLATE
   - Django templates sait comment itérer sur un queryset Django
   - Pas besoin de créer des proxies qui imitent les querysets

3. CONTEXTE CLAIR
   - Les données sont passées directement au contexte
   - Le template peut y accéder avec {{ categories }}, {{ competition_types }}, etc.

4. MODIFICATION DU TEMPLATE (SI NÉCESSAIRE)
   - Au lieu de {{ competition.categories.all }}, utiliser {{ categories }}
   - Au lieu de {{ competition.competition_types.all }}, utiliser {{ competition_types }}

MODIFICATIONS À FAIRE DANS LE TEMPLATE:

Remplacer:
```django
{% for category in competition.categories.all %}
```
Par:
```django
{% for category in categories %}
```

Remplacer:
```django
{% for comp_type in competition.competition_types.all %}
```
Par:
```django
{% for comp_type in competition_types %}
```

Ces changements sont minimes mais critiques pour que les données s'affichent.
"""
