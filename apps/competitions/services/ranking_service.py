# apps/competitions/services/ranking_service.py
"""
PROMPT 10 - Service de calcul des classements avec gestion des ex-aequo.

Ce service calcule les classements provisoires et finaux pour les compétitions
techniques, avec support des ex-aequo (plusieurs pratiquants à la même place).
"""

from django.db.models import Avg, Count
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from datetime import date


class RankingService:
    """
    Service pour le calcul des classements de compétitions techniques.

    Fonctionnalités:
    - Calcul du classement provisoire par round
    - Gestion des ex-aequo (même score = même rang)
    - Qualification pour le round suivant
    - Calcul du classement final
    """

    @staticmethod
    def calculate_age(birth_date):
        """Calcule l'âge à partir de la date de naissance."""
        if not birth_date:
            return None
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age

    @staticmethod
    def get_practitioner_info(practitioner):
        """
        Récupère les informations d'un pratiquant pour l'affichage.
        NEUTRALITÉ JUGE: Pas de club/pays, seulement grade/age/photo.
        """
        # Grade
        grade_display = None
        if hasattr(practitioner, 'grade') and practitioner.grade:
            grade_display = str(practitioner.grade)
        elif hasattr(practitioner, 'grade_text') and practitioner.grade_text:
            grade_display = practitioner.grade_text

        # Photo
        photo_url = None
        if hasattr(practitioner, 'photo') and practitioner.photo:
            photo_url = practitioner.photo.url

        # Âge
        age = None
        if hasattr(practitioner, 'birth_date') and practitioner.birth_date:
            age = RankingService.calculate_age(practitioner.birth_date)

        return {
            'id': practitioner.id,
            'name': practitioner.full_name,
            'grade': grade_display,
            'age': age,
            'photo_url': photo_url,
            'is_team': False,
        }

    @staticmethod
    def get_team_info(equipe):
        """
        Récupère les informations d'une équipe pour l'affichage.
        """
        photo_url = None
        members = list(
            equipe.memberships.filter(est_remplacant=False)
            .select_related('pratiquant')
            .order_by('ordre')
        )
        if members and hasattr(members[0].pratiquant, 'photo') and members[0].pratiquant.photo:
            photo_url = members[0].pratiquant.photo.url

        return {
            'id': equipe.id,
            'name': equipe.nom,
            'grade': None,
            'age': None,
            'photo_url': photo_url,
            'is_team': True,
            'members': [m.pratiquant.full_name for m in members],
        }

    @classmethod
    def calculate_round_ranking(cls, category, round_number=1, judge=None):
        """
        Calcule le classement pour un round spécifique d'une catégorie.

        GESTION DES EX-AEQUO:
        - Les pratiquants avec le même score ont le même rang
        - Le rang suivant saute les positions (1, 2, 2, 4 au lieu de 1, 2, 2, 3)

        Args:
            category: CompetitionCategory
            round_number: Numéro du round (défaut: 1)
            judge: Optionnel - filtrer par juge spécifique

        Returns:
            list: Liste des pratiquants classés avec leurs scores
        """
        from ..models.technical_scoring import Performance, Score

        # Récupérer toutes les performances de la catégorie
        performances = Performance.objects.filter(
            category=category
        ).select_related(
            'practitioner', 'practitioner__grade',
            'equipe', 'equipe__club'
        )

        # Calculer les scores
        ranking_data = []

        for perf in performances:
            # Filtrer par juge si spécifié
            scores_query = perf.scores.all()
            if judge:
                scores_query = scores_query.filter(judge=judge)

            # Calculer le score moyen
            avg_score = scores_query.aggregate(avg=Avg('value'))['avg']

            if avg_score is not None:
                if perf.equipe:
                    info = cls.get_team_info(perf.equipe)
                else:
                    info = cls.get_practitioner_info(perf.practitioner)

                ranking_data.append({
                    'performance_id': perf.id,
                    'practitioner_id': info['id'],
                    'practitioner_name': info['name'],
                    'grade': info['grade'],
                    'age': info['age'],
                    'photo_url': info['photo_url'],
                    'is_team': info.get('is_team', False),
                    'score': round(avg_score, 2),
                    'judges_count': scores_query.values('judge').distinct().count(),
                })

        # Trier par score décroissant
        ranking_data.sort(key=lambda x: x['score'], reverse=True)

        # Attribuer les rangs avec gestion des ex-aequo
        ranking_data = cls._assign_ranks_with_ties(ranking_data)

        return ranking_data

    @classmethod
    def _assign_ranks_with_ties(cls, ranking_data):
        """
        Attribue les rangs en gérant les ex-aequo.

        Exemple avec ex-aequo:
        - Score 8.5 → Rang 1
        - Score 7.5 → Rang 2
        - Score 7.5 → Rang 2 (ex-aequo)
        - Score 6.5 → Rang 4 (pas 3, car 2 personnes au rang 2)

        Args:
            ranking_data: Liste triée par score décroissant

        Returns:
            list: Liste avec les rangs attribués et indicateur ex-aequo
        """
        if not ranking_data:
            return ranking_data

        previous_score = None
        current_rank = 1

        for i, item in enumerate(ranking_data):
            if previous_score is not None and item['score'] == previous_score:
                # Ex-aequo: même rang que le groupe
                item['rank'] = current_rank
                item['is_tie'] = True
                # Marquer aussi le premier du groupe comme ex-aequo
                if i > 0 and not ranking_data[i-1].get('is_tie'):
                    ranking_data[i-1]['is_tie'] = True
            else:
                # Nouveau rang = position réelle (saute les rangs des ex-aequo)
                current_rank = i + 1
                item['rank'] = current_rank
                item['is_tie'] = False

            previous_score = item['score']

        return ranking_data

    @classmethod
    def get_podium(cls, ranking_data):
        """
        Extrait le podium (3 premiers rangs) avec gestion des ex-aequo.

        IMPORTANT: S'il y a des ex-aequo au 3ème rang, tous sont inclus.

        Args:
            ranking_data: Liste avec rangs attribués

        Returns:
            dict: Podium avec listes pour chaque position (pour gérer ex-aequo)
        """
        podium = {
            'gold': [],      # 1ère place (🥇)
            'silver': [],    # 2ème place (🥈)
            'bronze': [],    # 3ème place (🥉)
        }

        for item in ranking_data:
            rank = item.get('rank', 0)
            if rank == 1:
                podium['gold'].append(item)
            elif rank == 2:
                podium['silver'].append(item)
            elif rank == 3:
                podium['bronze'].append(item)

        return podium

    @classmethod
    def qualify_for_next_round(cls, category, round_number, top_n):
        """
        Détermine les qualifiés pour le round suivant.

        Args:
            category: CompetitionCategory
            round_number: Numéro du round actuel
            top_n: Nombre de qualifiés

        Returns:
            list: Liste des practitioner_id qualifiés
        """
        ranking = cls.calculate_round_ranking(category, round_number)

        # Prendre les top_n premiers (attention aux ex-aequo)
        qualified = []
        last_qualifying_score = None

        for item in ranking:
            if len(qualified) < top_n:
                qualified.append(item)
                last_qualifying_score = item['score']
            elif item['score'] == last_qualifying_score:
                # Ex-aequo avec le dernier qualifié: inclure aussi
                qualified.append(item)
            else:
                break

        return [q['practitioner_id'] for q in qualified]

    @classmethod
    def calculate_final_ranking(cls, category):
        """
        Calcule le classement final d'une catégorie.
        Prend en compte tous les rounds.

        Args:
            category: CompetitionCategory

        Returns:
            list: Classement final avec médailles
        """
        from ..models.technical_scoring import Performance, Score, ScoringConfiguration
        from django.db.models import Avg

        performances = Performance.objects.filter(
            category=category
        ).select_related(
            'practitioner', 'practitioner__grade',
            'equipe', 'equipe__club'
        )

        ranking_data = []

        for perf in performances:
            # Score final = moyenne de tous les scores de tous les juges
            avg_score = perf.scores.aggregate(avg=Avg('value'))['avg']

            if avg_score is not None:
                if perf.equipe:
                    info = cls.get_team_info(perf.equipe)
                else:
                    info = cls.get_practitioner_info(perf.practitioner)

                ranking_data.append({
                    'performance_id': perf.id,
                    'practitioner_id': info['id'],
                    'practitioner_name': info['name'],
                    'grade': info['grade'],
                    'age': info['age'],
                    'photo_url': info['photo_url'],
                    'is_team': info.get('is_team', False),
                    'score': round(avg_score, 2),
                    'judges_count': perf.scores.values('judge').distinct().count(),
                })

        # Trier et attribuer les rangs
        ranking_data.sort(key=lambda x: x['score'], reverse=True)
        ranking_data = cls._assign_ranks_with_ties(ranking_data)

        # Ajouter les médailles
        for item in ranking_data:
            rank = item.get('rank', 0)
            if rank == 1:
                item['medal'] = 'gold'
                item['medal_emoji'] = '🥇'
            elif rank == 2:
                item['medal'] = 'silver'
                item['medal_emoji'] = '🥈'
            elif rank == 3:
                item['medal'] = 'bronze'
                item['medal_emoji'] = '🥉'
            else:
                item['medal'] = None
                item['medal_emoji'] = ''

        return ranking_data

    @classmethod
    def get_judge_stats(cls, judge, category, round_number=1):
        """
        Calcule les statistiques de notation d'un juge pour une catégorie.

        Args:
            judge: Judge instance
            category: CompetitionCategory
            round_number: Numéro du round

        Returns:
            dict: Statistiques (count, avg, min, max)
        """
        from ..models.technical_scoring import Performance, Score
        from django.db.models import Avg, Min, Max, Count

        scores = Score.objects.filter(
            performance__category=category,
            judge=judge
        )

        stats = scores.aggregate(
            count=Count('id'),
            avg=Avg('value'),
            min=Min('value'),
            max=Max('value')
        )

        # Nombre de performances notées
        scored_performances = Performance.objects.filter(
            category=category,
            scores__judge=judge
        ).distinct().count()

        total_performances = Performance.objects.filter(category=category).count()

        return {
            'scores_count': stats['count'] or 0,
            'average_score': round(stats['avg'], 2) if stats['avg'] else 0,
            'min_score': round(stats['min'], 2) if stats['min'] else 0,
            'max_score': round(stats['max'], 2) if stats['max'] else 0,
            'scored_performances': scored_performances,
            'total_performances': total_performances,
            'all_scored': scored_performances == total_performances and total_performances > 0,
            'progress_percent': round(scored_performances / total_performances * 100, 1) if total_performances > 0 else 0,
        }

    @classmethod
    def format_ranking_for_display(cls, ranking_data):
        """
        Formate le classement pour l'affichage dans l'interface.

        Gère les ex-aequo en groupant les noms sur la même ligne.

        Args:
            ranking_data: Liste de classement avec rangs

        Returns:
            list: Liste formatée pour affichage
        """
        display_list = []
        current_rank = None
        current_group = []

        for item in ranking_data:
            if item['rank'] != current_rank:
                # Nouveau rang: sauvegarder le groupe précédent
                if current_group:
                    display_list.append({
                        'rank': current_rank,
                        'practitioners': current_group,
                        'is_tie': len(current_group) > 1,
                        'score': current_group[0]['score'],
                    })
                current_rank = item['rank']
                current_group = [item]
            else:
                # Même rang (ex-aequo)
                current_group.append(item)

        # Ajouter le dernier groupe
        if current_group:
            display_list.append({
                'rank': current_rank,
                'practitioners': current_group,
                'is_tie': len(current_group) > 1,
                'score': current_group[0]['score'],
            })

        return display_list
