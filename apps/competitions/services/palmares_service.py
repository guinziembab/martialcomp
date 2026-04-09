# -*- coding: utf-8 -*-
"""
Service pour la gestion du palmarès des pratiquants
Fournit les statistiques et l'historique des résultats en compétition
"""

from django.db.models import Count, Q, Min, Max
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PalmaresService:
    """
    Service pour récupérer et analyser le palmarès d'un pratiquant.

    Utilise les modèles:
    - CompetitionRegistration (apps.competitions)
    - RankingEntry / CategoryRanking (apps.competitions)
    - Combat (apps.competitions)
    - TechnicalPerformanceResult / PerformanceResult (apps.competitions)
    - CompetitionResult (apps.competitions)
    """

    def __init__(self, practitioner):
        """
        Initialise le service avec un pratiquant.

        Args:
            practitioner: Instance du modèle Practitioner
        """
        self.practitioner = practitioner
        self._stats = None
        self._results = None

    def get_palmares_summary(self):
        """
        Retourne un résumé complet du palmarès du pratiquant.

        Returns:
            dict: Résumé complet du palmarès
        """
        return {
            'statistics': self.get_statistics(),
            'recent_results': self.get_recent_results(limit=5),
            'best_result': self.get_best_result(),
            'evolution_data': self.get_evolution_data(months=12),
        }

    def get_statistics(self):
        """
        Calcule les statistiques globales du palmarès.

        Returns:
            dict: Statistiques globales
        """
        try:
            stats = {
                'total_participations': 0,
                'gold_medals': 0,
                'silver_medals': 0,
                'bronze_medals': 0,
                'other_rankings': 0,
                'best_ranking': None,
                'best_competition': None,
                'podiums': 0,
                'win_rate': 0,
            }

            # Récupérer les résultats depuis RankingEntry
            from apps.competitions.models import RankingEntry, CategoryRanking

            ranking_entries = RankingEntry.objects.filter(
                practitioner=self.practitioner,
                ranking__is_final=True
            ).select_related('ranking', 'ranking__category', 'ranking__competition')

            # Compter les participations et médailles
            for entry in ranking_entries:
                stats['total_participations'] += 1
                rank = entry.rank

                if rank == 1:
                    stats['gold_medals'] += 1
                    stats['podiums'] += 1
                elif rank == 2:
                    stats['silver_medals'] += 1
                    stats['podiums'] += 1
                elif rank == 3:
                    stats['bronze_medals'] += 1
                    stats['podiums'] += 1
                elif rank and rank > 3:
                    stats['other_rankings'] += 1

                # Trouver le meilleur classement
                if rank and (stats['best_ranking'] is None or rank < stats['best_ranking']):
                    stats['best_ranking'] = rank
                    if entry.ranking and entry.ranking.competition:
                        stats['best_competition'] = entry.ranking.competition.name

            # Également chercher dans CompetitionResult si disponible
            try:
                from apps.competitions.models import CompetitionResult

                competition_results = CompetitionResult.objects.filter(
                    practitioner=self.practitioner
                ).select_related('competition', 'category')

                for result in competition_results:
                    # Éviter les doublons si déjà compté via RankingEntry
                    if not ranking_entries.filter(
                        ranking__competition=result.competition,
                        ranking__category=result.category
                    ).exists():
                        stats['total_participations'] += 1
                        rank = result.rank

                        if result.medal == 'gold' or rank == 1:
                            stats['gold_medals'] += 1
                            stats['podiums'] += 1
                        elif result.medal == 'silver' or rank == 2:
                            stats['silver_medals'] += 1
                            stats['podiums'] += 1
                        elif result.medal == 'bronze' or rank == 3:
                            stats['bronze_medals'] += 1
                            stats['podiums'] += 1
                        elif rank and rank > 3:
                            stats['other_rankings'] += 1

                        if rank and (stats['best_ranking'] is None or rank < stats['best_ranking']):
                            stats['best_ranking'] = rank
                            if result.competition:
                                stats['best_competition'] = result.competition.name

            except Exception as e:
                logger.debug(f"CompetitionResult non disponible: {e}")

            # Chercher aussi dans CompetitionRanking (système de notation technique)
            try:
                from apps.competitions.models.technical_scoring import CompetitionRanking

                technical_rankings = CompetitionRanking.objects.filter(
                    practitioner=self.practitioner
                ).select_related('competition', 'category')

                # Créer un set des compétitions/catégories déjà comptées
                counted_pairs = set()
                for entry in ranking_entries:
                    if entry.ranking and entry.ranking.competition and entry.ranking.category:
                        counted_pairs.add((entry.ranking.competition.id, entry.ranking.category.id))

                for ranking in technical_rankings:
                    # Éviter les doublons
                    pair = (ranking.competition.id, ranking.category.id) if ranking.competition and ranking.category else None
                    if pair and pair not in counted_pairs:
                        counted_pairs.add(pair)
                        stats['total_participations'] += 1
                        rank = ranking.rank

                        if rank == 1:
                            stats['gold_medals'] += 1
                            stats['podiums'] += 1
                        elif rank == 2:
                            stats['silver_medals'] += 1
                            stats['podiums'] += 1
                        elif rank == 3:
                            stats['bronze_medals'] += 1
                            stats['podiums'] += 1
                        elif rank and rank > 3:
                            stats['other_rankings'] += 1

                        if rank and (stats['best_ranking'] is None or rank < stats['best_ranking']):
                            stats['best_ranking'] = rank
                            if ranking.competition:
                                stats['best_competition'] = ranking.competition.title

            except Exception as e:
                logger.debug(f"CompetitionRanking non disponible: {e}")

            # Ajouter les statistiques de combat
            combat_stats = self._get_combat_statistics()
            stats['combat_wins'] = combat_stats.get('wins', 0)
            stats['combat_losses'] = combat_stats.get('losses', 0)
            stats['combat_draws'] = combat_stats.get('draws', 0)
            stats['total_combats'] = combat_stats.get('total', 0)

            if stats['total_combats'] > 0:
                stats['win_rate'] = round((stats['combat_wins'] / stats['total_combats']) * 100, 1)

            return stats

        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques palmarès: {e}")
            return {
                'total_participations': 0,
                'gold_medals': 0,
                'silver_medals': 0,
                'bronze_medals': 0,
                'other_rankings': 0,
                'best_ranking': None,
                'best_competition': None,
                'podiums': 0,
                'win_rate': 0,
                'combat_wins': 0,
                'combat_losses': 0,
                'combat_draws': 0,
                'total_combats': 0,
            }

    def _get_combat_statistics(self):
        """
        Calcule les statistiques de combat du pratiquant.

        Returns:
            dict: Statistiques de combat (wins, losses, draws)
        """
        try:
            from apps.competitions.models import Combat

            # Combats gagnés (en tant que rouge)
            wins_as_red = Combat.objects.filter(
                pratiquant_rouge=self.practitioner,
                status='termine',
                vainqueur='rouge'
            ).count()

            # Combats gagnés (en tant que blanc)
            wins_as_white = Combat.objects.filter(
                pratiquant_blanc=self.practitioner,
                status='termine',
                vainqueur='blanc'
            ).count()

            # Combats perdus (en tant que rouge)
            losses_as_red = Combat.objects.filter(
                pratiquant_rouge=self.practitioner,
                status='termine',
                vainqueur='blanc'
            ).count()

            # Combats perdus (en tant que blanc)
            losses_as_white = Combat.objects.filter(
                pratiquant_blanc=self.practitioner,
                status='termine',
                vainqueur='rouge'
            ).count()

            # Combats nuls
            draws = Combat.objects.filter(
                Q(pratiquant_rouge=self.practitioner) | Q(pratiquant_blanc=self.practitioner),
                status='termine',
                est_nul=True
            ).count()

            wins = wins_as_red + wins_as_white
            losses = losses_as_red + losses_as_white
            total = wins + losses + draws

            return {
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'total': total,
            }

        except Exception as e:
            logger.debug(f"Erreur calcul stats combat: {e}")
            return {'wins': 0, 'losses': 0, 'draws': 0, 'total': 0}

    def get_recent_results(self, limit=5):
        """
        Récupère les derniers résultats du pratiquant.

        Args:
            limit: Nombre maximum de résultats à retourner

        Returns:
            list: Liste des résultats récents
        """
        results = []

        try:
            # D'abord, essayer CompetitionResult (modèle dédié)
            try:
                from apps.competitions.models import CompetitionResult

                competition_results = CompetitionResult.objects.filter(
                    practitioner=self.practitioner
                ).select_related(
                    'competition', 'category'
                ).order_by('-date', '-competition__start_date')[:limit * 2]

                for result in competition_results:
                    medal = None
                    if result.medal == 'gold' or result.rank == 1:
                        medal = 'gold'
                    elif result.medal == 'silver' or result.rank == 2:
                        medal = 'silver'
                    elif result.medal == 'bronze' or result.rank == 3:
                        medal = 'bronze'

                    competition_date = result.date
                    if not competition_date and result.competition:
                        competition_date = result.competition.start_date

                    results.append({
                        'date': competition_date,
                        'competition_name': result.competition.name if result.competition else 'N/A',
                        'category_name': result.category.name if result.category else 'N/A',
                        'ranking': result.rank,
                        'score': float(result.score) if result.score else None,
                        'medal': medal,
                        'type': 'result',
                    })

            except Exception as e:
                logger.debug(f"CompetitionResult non disponible: {e}")

            # Puis, ajouter depuis RankingEntry
            from apps.competitions.models import RankingEntry

            ranking_entries = RankingEntry.objects.filter(
                practitioner=self.practitioner,
                ranking__is_final=True
            ).select_related(
                'ranking', 'ranking__category', 'ranking__competition'
            ).order_by('-ranking__competition__start_date')[:limit * 2]

            for entry in ranking_entries:
                # Éviter les doublons
                if entry.ranking and entry.ranking.competition:
                    comp_name = entry.ranking.competition.name
                    cat_name = entry.ranking.category.name if entry.ranking.category else ''

                    # Vérifier si déjà dans results
                    already_exists = any(
                        r.get('competition_name') == comp_name and
                        r.get('category_name') == cat_name
                        for r in results
                    )

                    if not already_exists:
                        medal = None
                        if entry.rank == 1:
                            medal = 'gold'
                        elif entry.rank == 2:
                            medal = 'silver'
                        elif entry.rank == 3:
                            medal = 'bronze'

                        results.append({
                            'date': entry.ranking.competition.start_date if entry.ranking.competition else None,
                            'competition_name': comp_name,
                            'category_name': cat_name,
                            'ranking': entry.rank,
                            'score': float(entry.score) if entry.score else None,
                            'medal': medal,
                            'type': 'ranking',
                        })

            # Ajouter les performances techniques finalisées
            try:
                from apps.competitions.models import PerformanceResult, TechnicalPerformanceResult

                performance_results = PerformanceResult.objects.filter(
                    performance__practitioner=self.practitioner,
                    status='final'
                ).select_related(
                    'performance',
                    'performance__competition',
                    'performance__category'
                ).order_by('-performance__competition__start_date')[:limit]

                for perf_result in performance_results:
                    perf = perf_result.performance
                    comp_name = perf.competition.name if perf.competition else 'N/A'
                    cat_name = perf.category.name if perf.category else 'N/A'

                    # Vérifier si déjà dans results
                    already_exists = any(
                        r.get('competition_name') == comp_name and
                        r.get('category_name') == cat_name
                        for r in results
                    )

                    if not already_exists:
                        medal = None
                        if perf_result.rank == 1:
                            medal = 'gold'
                        elif perf_result.rank == 2:
                            medal = 'silver'
                        elif perf_result.rank == 3:
                            medal = 'bronze'

                        results.append({
                            'date': perf.competition.start_date if perf.competition else None,
                            'competition_name': comp_name,
                            'category_name': cat_name,
                            'ranking': perf_result.rank,
                            'score': float(perf_result.final_score) if perf_result.final_score else None,
                            'medal': medal,
                            'type': 'performance',
                        })

            except Exception as e:
                logger.debug(f"PerformanceResult non disponible: {e}")

            # Ajouter les résultats depuis CompetitionRanking (système de notation technique)
            try:
                from apps.competitions.models.technical_scoring import CompetitionRanking

                technical_rankings = CompetitionRanking.objects.filter(
                    practitioner=self.practitioner
                ).select_related(
                    'competition', 'category'
                ).order_by('-competition__start_date')[:limit * 2]

                for ranking in technical_rankings:
                    comp_name = ranking.competition.title if ranking.competition else 'N/A'
                    cat_name = ranking.category.name if ranking.category else 'N/A'

                    # Vérifier si déjà dans results
                    already_exists = any(
                        r.get('competition_name') == comp_name and
                        r.get('category_name') == cat_name
                        for r in results
                    )

                    if not already_exists:
                        medal = None
                        if ranking.rank == 1:
                            medal = 'gold'
                        elif ranking.rank == 2:
                            medal = 'silver'
                        elif ranking.rank == 3:
                            medal = 'bronze'

                        results.append({
                            'date': ranking.competition.start_date if ranking.competition else None,
                            'competition_name': comp_name,
                            'category_name': cat_name,
                            'ranking': ranking.rank,
                            'score': float(ranking.final_score) if ranking.final_score else None,
                            'medal': medal,
                            'type': 'technical_ranking',
                        })

            except Exception as e:
                logger.debug(f"CompetitionRanking non disponible pour résultats récents: {e}")

            # Trier par date décroissante et limiter
            results.sort(key=lambda x: x.get('date') or timezone.now().date(), reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des résultats récents: {e}")
            return []

    def get_best_result(self):
        """
        Récupère le meilleur résultat du pratiquant.

        Returns:
            dict: Meilleur résultat ou None
        """
        try:
            results = self.get_recent_results(limit=100)

            if not results:
                return None

            # Trouver le meilleur classement (priorité aux médailles d'or)
            best = None
            for result in results:
                if result.get('ranking'):
                    if best is None:
                        best = result
                    elif result['ranking'] < best['ranking']:
                        best = result
                    elif result['ranking'] == best['ranking'] and result.get('score'):
                        # À classement égal, prendre le meilleur score
                        if best.get('score') is None or result['score'] > best['score']:
                            best = result

            return best

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du meilleur résultat: {e}")
            return None

    def get_evolution_data(self, months=12):
        """
        Récupère les données d'évolution des classements pour le graphique.

        Args:
            months: Nombre de mois à remonter

        Returns:
            list: Données pour Chart.js
        """
        try:
            from apps.competitions.models import RankingEntry, CompetitionResult

            # Date limite
            date_limit = timezone.now().date() - timedelta(days=months * 30)

            evolution = []

            # Récupérer les résultats depuis RankingEntry
            ranking_entries = RankingEntry.objects.filter(
                practitioner=self.practitioner,
                ranking__is_final=True,
                ranking__competition__start_date__gte=date_limit
            ).select_related(
                'ranking', 'ranking__competition'
            ).order_by('ranking__competition__start_date')

            for entry in ranking_entries:
                if entry.ranking and entry.ranking.competition:
                    evolution.append({
                        'date': entry.ranking.competition.start_date.strftime('%Y-%m-%d'),
                        'label': entry.ranking.competition.name[:20],
                        'ranking': entry.rank,
                        'score': float(entry.score) if entry.score else None,
                    })

            # Compléter avec CompetitionResult si disponible
            try:
                competition_results = CompetitionResult.objects.filter(
                    practitioner=self.practitioner,
                    date__gte=date_limit
                ).select_related('competition').order_by('date')

                for result in competition_results:
                    result_date = result.date or (result.competition.start_date if result.competition else None)
                    if result_date:
                        date_str = result_date.strftime('%Y-%m-%d')
                        # Éviter les doublons
                        if not any(e['date'] == date_str for e in evolution):
                            evolution.append({
                                'date': date_str,
                                'label': result.competition.name[:20] if result.competition else 'N/A',
                                'ranking': result.rank,
                                'score': float(result.score) if result.score else None,
                            })

            except Exception as e:
                logger.debug(f"CompetitionResult non disponible pour évolution: {e}")

            # Trier par date
            evolution.sort(key=lambda x: x['date'])

            return evolution

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données d'évolution: {e}")
            return []

    def get_results_by_year(self, year=None):
        """
        Récupère les résultats d'une année spécifique.

        Args:
            year: Année (défaut: année en cours)

        Returns:
            list: Résultats de l'année
        """
        if year is None:
            year = timezone.now().year

        results = self.get_recent_results(limit=100)
        return [r for r in results if r.get('date') and r['date'].year == year]

    def get_results_by_discipline(self, discipline_id=None):
        """
        Récupère les résultats filtrés par discipline.

        Args:
            discipline_id: ID de la discipline

        Returns:
            list: Résultats filtrés
        """
        try:
            from apps.competitions.models import RankingEntry

            query = RankingEntry.objects.filter(
                practitioner=self.practitioner,
                ranking__is_final=True
            )

            if discipline_id:
                query = query.filter(ranking__category__discipline_id=discipline_id)

            results = []
            for entry in query.select_related('ranking', 'ranking__competition', 'ranking__category'):
                if entry.ranking and entry.ranking.competition:
                    medal = None
                    if entry.rank == 1:
                        medal = 'gold'
                    elif entry.rank == 2:
                        medal = 'silver'
                    elif entry.rank == 3:
                        medal = 'bronze'

                    results.append({
                        'date': entry.ranking.competition.start_date,
                        'competition_name': entry.ranking.competition.name,
                        'category_name': entry.ranking.category.name if entry.ranking.category else 'N/A',
                        'ranking': entry.rank,
                        'score': float(entry.score) if entry.score else None,
                        'medal': medal,
                    })

            results.sort(key=lambda x: x.get('date') or timezone.now().date(), reverse=True)
            return results

        except Exception as e:
            logger.error(f"Erreur filtre par discipline: {e}")
            return []

    @staticmethod
    def get_medal_icon(medal):
        """
        Retourne l'icône emoji pour une médaille.

        Args:
            medal: Type de médaille ('gold', 'silver', 'bronze')

        Returns:
            str: Emoji de la médaille
        """
        icons = {
            'gold': '🥇',
            'silver': '🥈',
            'bronze': '🥉',
        }
        return icons.get(medal, '')

    @staticmethod
    def get_medal_class(medal):
        """
        Retourne la classe CSS pour une médaille.

        Args:
            medal: Type de médaille

        Returns:
            str: Classe CSS
        """
        classes = {
            'gold': 'medal-gold',
            'silver': 'medal-silver',
            'bronze': 'medal-bronze',
        }
        return classes.get(medal, '')
