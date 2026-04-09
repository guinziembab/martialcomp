"""
Service pour le calcul des statistiques et palmares des pratiquants.
Prompt 3 - Visualisation des Resultats
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import date, timedelta
from collections import defaultdict
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class MedalCount:
    """Compteur de medailles."""
    gold: int = 0
    silver: int = 0
    bronze: int = 0

    @property
    def total(self) -> int:
        return self.gold + self.silver + self.bronze

    def to_dict(self) -> dict:
        return {
            'gold': self.gold,
            'silver': self.silver,
            'bronze': self.bronze,
            'total': self.total,
        }


@dataclass
class MedalTimelineEntry:
    """Entree de la timeline des medailles."""
    date: date
    medal: str  # 'gold', 'silver', 'bronze'
    competition_id: int
    competition_name: str
    category_name: str
    discipline_name: str
    points: int = 0

    def to_dict(self) -> dict:
        return {
            'date': self.date.isoformat(),
            'date_display': self.date.strftime('%d/%m/%Y'),
            'medal': self.medal,
            'competition_id': self.competition_id,
            'competition_name': self.competition_name,
            'category_name': self.category_name,
            'discipline_name': self.discipline_name,
            'points': self.points,
        }


@dataclass
class CompetitionStats:
    """Statistiques de competition."""
    total_competitions: int = 0
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_points: int = 0

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses + self.draws
        if total == 0:
            return 0.0
        return round((self.wins / total) * 100, 1)

    def to_dict(self) -> dict:
        return {
            'total_competitions': self.total_competitions,
            'total_matches': self.total_matches,
            'wins': self.wins,
            'losses': self.losses,
            'draws': self.draws,
            'win_rate': self.win_rate,
            'total_points': self.total_points,
        }


@dataclass
class RankingEvolution:
    """Evolution du classement sur une periode."""
    month: str  # Format: 'YYYY-MM'
    rank: int
    points: int = 0

    def to_dict(self) -> dict:
        return {
            'month': self.month,
            'rank': self.rank,
            'points': self.points,
        }


@dataclass
class DisciplinePoints:
    """Points par discipline."""
    discipline_id: int
    discipline_name: str
    points: int
    competitions_count: int = 0
    medals_count: int = 0

    def to_dict(self) -> dict:
        return {
            'discipline_id': self.discipline_id,
            'discipline_name': self.discipline_name,
            'points': self.points,
            'competitions_count': self.competitions_count,
            'medals_count': self.medals_count,
        }


@dataclass
class ResultsDashboardData:
    """Donnees completes du dashboard resultats."""
    medals: MedalCount = field(default_factory=MedalCount)
    medals_timeline: List[MedalTimelineEntry] = field(default_factory=list)
    stats: CompetitionStats = field(default_factory=CompetitionStats)
    ranking_evolution: List[RankingEvolution] = field(default_factory=list)
    points_by_discipline: List[DisciplinePoints] = field(default_factory=list)
    competition_history: List[Dict] = field(default_factory=list)
    grades: List[Dict] = field(default_factory=list)
    public_profile_enabled: bool = False
    public_profile_url: str = ""

    def to_dict(self) -> dict:
        return {
            'medals': self.medals.to_dict(),
            'medals_timeline': [m.to_dict() for m in self.medals_timeline],
            'stats': self.stats.to_dict(),
            'ranking_evolution': [r.to_dict() for r in self.ranking_evolution],
            'points_by_discipline': [d.to_dict() for d in self.points_by_discipline],
            'competition_history': self.competition_history,
            'grades': self.grades,
            'public_profile_enabled': self.public_profile_enabled,
            'public_profile_url': self.public_profile_url,
        }


class ResultsService:
    """
    Service de calcul des statistiques et palmares.

    Usage:
        data = ResultsService.get_dashboard_data(practitioner)
        # ou
        medals = ResultsService.count_medals(practitioner)
    """

    CACHE_PREFIX = "results_dashboard"
    CACHE_TTL = 3600  # 1 heure

    @classmethod
    def get_dashboard_data(
        cls,
        practitioner,
        year: Optional[int] = None,
        discipline_id: Optional[int] = None,
        use_cache: bool = True
    ) -> ResultsDashboardData:
        """
        Recupere toutes les donnees du dashboard resultats.

        Args:
            practitioner: Instance Practitioner
            year: Filtrer par annee (optionnel)
            discipline_id: Filtrer par discipline (optionnel)
            use_cache: Utiliser le cache (defaut: True)

        Returns:
            ResultsDashboardData avec toutes les statistiques
        """
        cache_key = f"{cls.CACHE_PREFIX}:{practitioner.id}:{year}:{discipline_id}"

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            data = ResultsDashboardData(
                medals=cls.count_medals(practitioner, year, discipline_id),
                medals_timeline=cls.get_medals_timeline(practitioner, year, discipline_id),
                stats=cls.get_competition_stats(practitioner, year, discipline_id),
                ranking_evolution=cls.get_ranking_evolution(practitioner, discipline_id),
                points_by_discipline=cls.get_points_by_discipline(practitioner, year),
                competition_history=cls.get_competition_history(practitioner, year, discipline_id),
                grades=cls.get_grades_history(practitioner),
                public_profile_enabled=cls._get_public_profile_setting(practitioner),
                public_profile_url=cls._generate_public_profile_url(practitioner),
            )

            if use_cache:
                cache.set(cache_key, data, cls.CACHE_TTL)

            return data

        except Exception as e:
            logger.error(f"Erreur get_dashboard_data pour {practitioner.id}: {e}")
            return ResultsDashboardData()

    @classmethod
    def count_medals(
        cls,
        practitioner,
        year: Optional[int] = None,
        discipline_id: Optional[int] = None
    ) -> MedalCount:
        """
        Compte les medailles du pratiquant.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            # Filtres pour CompetitionResult
            filters = Q(practitioner=practitioner)
            if year:
                filters &= Q(competition__start_date__year=year)
            if discipline_id:
                filters &= Q(competition__discipline_id=discipline_id)

            results = CompetitionResult.objects.filter(filters)
            gold_cr = results.filter(rank=1).count()
            silver_cr = results.filter(rank=2).count()
            bronze_cr = results.filter(rank=3).count()

            # Filtres pour CompetitionRanking (technical competitions)
            ranking_filters = Q(practitioner=practitioner)
            if year:
                ranking_filters &= Q(competition__start_date__year=year)
            if discipline_id:
                ranking_filters &= Q(competition__discipline_id=discipline_id)

            rankings = CompetitionRanking.objects.filter(ranking_filters)
            gold_rank = rankings.filter(rank=1).count()
            silver_rank = rankings.filter(rank=2).count()
            bronze_rank = rankings.filter(rank=3).count()

            # Prendre le max des deux sources
            gold = max(gold_cr, gold_rank)
            silver = max(silver_cr, silver_rank)
            bronze = max(bronze_cr, bronze_rank)

            return MedalCount(gold=gold, silver=silver, bronze=bronze)

        except ImportError as e:
            logger.warning(f"Import error in count_medals: {e}")
            return MedalCount()
        except Exception as e:
            logger.error(f"Erreur count_medals: {e}")
            return MedalCount()

    @classmethod
    def get_medals_timeline(
        cls,
        practitioner,
        year: Optional[int] = None,
        discipline_id: Optional[int] = None,
        limit: int = 50
    ) -> List[MedalTimelineEntry]:
        """
        Recupere la timeline des medailles.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            timeline = []
            seen_competitions = set()

            # D'abord chercher dans CompetitionResult
            filters = Q(practitioner=practitioner, rank__in=[1, 2, 3])
            if year:
                filters &= Q(competition__start_date__year=year)
            if discipline_id:
                filters &= Q(competition__discipline_id=discipline_id)

            results = CompetitionResult.objects.filter(filters).select_related(
                'competition', 'category', 'competition__discipline'
            ).order_by('-competition__start_date')[:limit]

            for result in results:
                medal = 'gold' if result.rank == 1 else ('silver' if result.rank == 2 else 'bronze')
                comp_key = (result.competition.id, result.category.id if result.category else 0)
                if comp_key not in seen_competitions:
                    seen_competitions.add(comp_key)
                    timeline.append(MedalTimelineEntry(
                        date=result.competition.start_date,
                        medal=medal,
                        competition_id=result.competition.id,
                        competition_name=result.competition.title,
                        category_name=result.category.name if result.category else '',
                        discipline_name=result.competition.discipline.name if result.competition.discipline else '',
                        points=getattr(result, 'points', 0) or 0,
                    ))

            # Ensuite chercher dans CompetitionRanking
            ranking_filters = Q(practitioner=practitioner, rank__in=[1, 2, 3])
            if year:
                ranking_filters &= Q(competition__start_date__year=year)
            if discipline_id:
                ranking_filters &= Q(competition__discipline_id=discipline_id)

            rankings = CompetitionRanking.objects.filter(ranking_filters).select_related(
                'competition', 'category', 'competition__discipline'
            ).order_by('-competition__start_date')[:limit]

            for ranking in rankings:
                medal = 'gold' if ranking.rank == 1 else ('silver' if ranking.rank == 2 else 'bronze')
                comp_key = (ranking.competition.id, ranking.category.id if ranking.category else 0)
                if comp_key not in seen_competitions:
                    seen_competitions.add(comp_key)
                    timeline.append(MedalTimelineEntry(
                        date=ranking.competition.start_date,
                        medal=medal,
                        competition_id=ranking.competition.id,
                        competition_name=ranking.competition.title,
                        category_name=ranking.category.name if ranking.category else '',
                        discipline_name=ranking.competition.discipline.name if ranking.competition.discipline else '',
                        points=0,
                    ))

            # Trier par date decroissante et limiter
            timeline.sort(key=lambda x: x.date, reverse=True)
            return timeline[:limit]

        except ImportError as e:
            logger.warning(f"Import error in get_medals_timeline: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur get_medals_timeline: {e}")
            return []

    @classmethod
    def get_competition_stats(
        cls,
        practitioner,
        year: Optional[int] = None,
        discipline_id: Optional[int] = None
    ) -> CompetitionStats:
        """
        Calcule les statistiques de competition.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking
            from apps.competitions.models import Combat

            filters = Q(practitioner=practitioner)
            if year:
                filters &= Q(competition__start_date__year=year)
            if discipline_id:
                filters &= Q(competition__discipline_id=discipline_id)

            # Nombre de competitions depuis CompetitionResult
            results = CompetitionResult.objects.filter(filters)
            competitions_from_results = set(results.values_list('competition_id', flat=True))

            # Nombre de competitions depuis CompetitionRanking
            ranking_filters = Q(practitioner=practitioner)
            if year:
                ranking_filters &= Q(competition__start_date__year=year)
            if discipline_id:
                ranking_filters &= Q(competition__discipline_id=discipline_id)

            rankings = CompetitionRanking.objects.filter(ranking_filters)
            competitions_from_rankings = set(rankings.values_list('competition_id', flat=True))

            # Union des deux ensembles
            all_competitions = competitions_from_results | competitions_from_rankings
            total_competitions = len(all_competitions)

            # Total points (using 'score' field, not 'points')
            total_points = results.aggregate(total=Sum('score'))['total'] or 0

            # Statistiques de combats
            # Le modele Combat utilise pratiquant_rouge et pratiquant_blanc (direct FK vers Practitioner)
            combat_filters = Q(pratiquant_rouge=practitioner) | Q(pratiquant_blanc=practitioner)

            if year:
                combat_filters &= Q(date_planifiee__year=year)

            # Le champ status utilise 'termine' (pas 'statut')
            combats = Combat.objects.filter(combat_filters, status='termine')

            total_matches = combats.count()
            wins = 0
            losses = 0
            draws = 0

            for combat in combats:
                if combat.est_nul:
                    draws += 1
                elif combat.vainqueur:
                    # Verifier si le pratiquant est le vainqueur
                    # vainqueur est 'rouge' ou 'blanc'
                    if (combat.pratiquant_rouge == practitioner and combat.vainqueur == 'rouge') or \
                       (combat.pratiquant_blanc == practitioner and combat.vainqueur == 'blanc'):
                        wins += 1
                    else:
                        losses += 1

            return CompetitionStats(
                total_competitions=total_competitions,
                total_matches=total_matches,
                wins=wins,
                losses=losses,
                draws=draws,
                total_points=total_points,
            )

        except ImportError:
            return CompetitionStats()
        except Exception as e:
            logger.error(f"Erreur get_competition_stats: {e}")
            return CompetitionStats()

    @classmethod
    def get_ranking_evolution(
        cls,
        practitioner,
        discipline_id: Optional[int] = None,
        months: int = 12
    ) -> List[RankingEvolution]:
        """
        Recupere l'evolution du classement sur les derniers mois.
        """
        try:
            from apps.competitions.models import CompetitionResult

            evolution = []
            today = timezone.now().date()

            for i in range(months - 1, -1, -1):
                month_date = today - timedelta(days=i * 30)
                month_str = month_date.strftime('%Y-%m')

                # Calculer les points cumules jusqu'a ce mois
                filters = Q(
                    practitioner=practitioner,
                    competition__start_date__lte=month_date
                )

                if discipline_id:
                    filters &= Q(competition__discipline_id=discipline_id)

                points = CompetitionResult.objects.filter(filters).aggregate(
                    total=Sum('points')
                )['total'] or 0

                # Calculer le rang (simplifie - basé sur les points)
                rank = cls._estimate_rank_from_points(points)

                evolution.append(RankingEvolution(
                    month=month_str,
                    rank=rank,
                    points=points,
                ))

            return evolution

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_ranking_evolution: {e}")
            return []

    @classmethod
    def get_points_by_discipline(
        cls,
        practitioner,
        year: Optional[int] = None
    ) -> List[DisciplinePoints]:
        """
        Recupere les points par discipline.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            disciplines_data = {}

            # D'abord depuis CompetitionResult
            filters = Q(practitioner=practitioner)
            if year:
                filters &= Q(competition__start_date__year=year)

            results = CompetitionResult.objects.filter(filters).values(
                'competition__discipline__id',
                'competition__discipline__name'
            ).annotate(
                total_score=Sum('score'),
                competitions_count=Count('competition', distinct=True),
                medals_count=Count('id', filter=Q(rank__in=[1, 2, 3]))
            ).order_by('-total_score')

            for result in results:
                disc_id = result['competition__discipline__id']
                if disc_id:
                    disciplines_data[disc_id] = {
                        'discipline_name': result['competition__discipline__name'] or 'Non defini',
                        'points': result['total_score'] or 0,
                        'competitions_count': result['competitions_count'],
                        'medals_count': result['medals_count'],
                    }

            # Ensuite depuis CompetitionRanking
            ranking_filters = Q(practitioner=practitioner)
            if year:
                ranking_filters &= Q(competition__start_date__year=year)

            rankings = CompetitionRanking.objects.filter(ranking_filters).values(
                'competition__discipline__id',
                'competition__discipline__name'
            ).annotate(
                competitions_count=Count('competition', distinct=True),
                medals_count=Count('id', filter=Q(rank__in=[1, 2, 3]))
            )

            for ranking in rankings:
                disc_id = ranking['competition__discipline__id']
                if disc_id:
                    if disc_id in disciplines_data:
                        # Fusionner les donnees
                        disciplines_data[disc_id]['competitions_count'] = max(
                            disciplines_data[disc_id]['competitions_count'],
                            ranking['competitions_count']
                        )
                        disciplines_data[disc_id]['medals_count'] = max(
                            disciplines_data[disc_id]['medals_count'],
                            ranking['medals_count']
                        )
                    else:
                        # Nouvelle discipline
                        disciplines_data[disc_id] = {
                            'discipline_name': ranking['competition__discipline__name'] or 'Non defini',
                            'points': 0,
                            'competitions_count': ranking['competitions_count'],
                            'medals_count': ranking['medals_count'],
                        }

            # Construire la liste de resultats
            disciplines = []
            for disc_id, data in disciplines_data.items():
                disciplines.append(DisciplinePoints(
                    discipline_id=disc_id,
                    discipline_name=data['discipline_name'],
                    points=data['points'],
                    competitions_count=data['competitions_count'],
                    medals_count=data['medals_count'],
                ))

            # Trier par nombre de medailles puis par points
            disciplines.sort(key=lambda x: (x.medals_count, x.points), reverse=True)
            return disciplines

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_points_by_discipline: {e}")
            return []

    @classmethod
    def get_competition_history(
        cls,
        practitioner,
        year: Optional[int] = None,
        discipline_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Recupere l'historique des competitions.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            history = []
            seen_competitions = set()

            # D'abord chercher dans CompetitionResult
            filters = Q(practitioner=practitioner)
            if year:
                filters &= Q(competition__start_date__year=year)
            if discipline_id:
                filters &= Q(competition__discipline_id=discipline_id)

            results = CompetitionResult.objects.filter(filters).select_related(
                'competition', 'category', 'competition__discipline'
            ).order_by('-competition__start_date')[:limit]

            for result in results:
                medal = None
                if result.rank == 1:
                    medal = 'gold'
                elif result.rank == 2:
                    medal = 'silver'
                elif result.rank == 3:
                    medal = 'bronze'

                comp_key = (result.competition.id, result.category.id if result.category else 0)
                if comp_key not in seen_competitions:
                    seen_competitions.add(comp_key)
                    history.append({
                        'id': result.id,
                        'competition_id': result.competition.id,
                        'competition_name': result.competition.title,
                        'date': result.competition.start_date.isoformat(),
                        'date_display': result.competition.start_date.strftime('%d/%m/%Y'),
                        'category_name': result.category.name if result.category else '',
                        'discipline_name': result.competition.discipline.name if result.competition.discipline else '',
                        'rank': result.rank,
                        'medal': medal,
                        'points': result.points or 0,
                        'score': result.final_score,
                    })

            # Ensuite chercher dans CompetitionRanking
            ranking_filters = Q(practitioner=practitioner)
            if year:
                ranking_filters &= Q(competition__start_date__year=year)
            if discipline_id:
                ranking_filters &= Q(competition__discipline_id=discipline_id)

            rankings = CompetitionRanking.objects.filter(ranking_filters).select_related(
                'competition', 'category', 'competition__discipline'
            ).order_by('-competition__start_date')[:limit]

            for ranking in rankings:
                medal = None
                if ranking.rank == 1:
                    medal = 'gold'
                elif ranking.rank == 2:
                    medal = 'silver'
                elif ranking.rank == 3:
                    medal = 'bronze'

                comp_key = (ranking.competition.id, ranking.category.id if ranking.category else 0)
                if comp_key not in seen_competitions:
                    seen_competitions.add(comp_key)
                    history.append({
                        'id': ranking.id,
                        'competition_id': ranking.competition.id,
                        'competition_name': ranking.competition.title,
                        'date': ranking.competition.start_date.isoformat(),
                        'date_display': ranking.competition.start_date.strftime('%d/%m/%Y'),
                        'category_name': ranking.category.name if ranking.category else '',
                        'discipline_name': ranking.competition.discipline.name if ranking.competition.discipline else '',
                        'rank': ranking.rank,
                        'medal': medal,
                        'points': 0,
                        'score': float(ranking.final_score) if ranking.final_score else 0,
                    })

            # Trier par date decroissante et limiter
            history.sort(key=lambda x: x['date'], reverse=True)
            return history[:limit]

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_competition_history: {e}")
            return []

    @classmethod
    def get_grades_history(cls, practitioner) -> List[Dict]:
        """
        Recupere l'historique des grades.
        """
        try:
            from apps.grades.models import PractitionerGrade

            grades = PractitionerGrade.objects.filter(
                practitioner=practitioner
            ).select_related('grade', 'discipline').order_by('-date_obtained')

            history = []
            for pg in grades:
                history.append({
                    'id': pg.id,
                    'grade_name': pg.grade.name,
                    'grade_color': getattr(pg.grade, 'color', ''),
                    'grade_color_code': getattr(pg.grade, 'color_code', ''),
                    'discipline_name': pg.discipline.name if pg.discipline else '',
                    'date_obtained': pg.date_obtained.isoformat() if pg.date_obtained else None,
                    'date_display': pg.date_obtained.strftime('%d/%m/%Y') if pg.date_obtained else '',
                    'examiner': pg.awarded_by or '',
                    'location': pg.location or '',
                    'is_current': pg.is_current,
                })

            return history

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_grades_history: {e}")
            return []

    @staticmethod
    def _estimate_rank_from_points(points: int) -> int:
        """
        Estime un rang a partir des points (simplifie).
        Plus les points sont eleves, meilleur est le rang.
        """
        if points >= 500:
            return 1
        elif points >= 400:
            return 5
        elif points >= 300:
            return 10
        elif points >= 200:
            return 20
        elif points >= 100:
            return 30
        elif points >= 50:
            return 50
        elif points > 0:
            return 100
        else:
            return 0

    @staticmethod
    def _get_public_profile_setting(practitioner) -> bool:
        """Verifie si le profil public est active."""
        try:
            return getattr(practitioner, 'public_profile_enabled', False)
        except Exception:
            return False

    @staticmethod
    def _generate_public_profile_url(practitioner) -> str:
        """Genere l'URL du profil public."""
        try:
            from django.urls import reverse
            slug = f"{practitioner.first_name}-{practitioner.last_name}-{practitioner.id}".lower()
            return f"/athlete/{slug}"
        except Exception:
            return ""

    @classmethod
    def invalidate_cache(cls, practitioner_id: int):
        """Invalide le cache pour un pratiquant."""
        # Supprimer toutes les variantes de cache
        patterns = [
            f"{cls.CACHE_PREFIX}:{practitioner_id}:None:None",
            f"{cls.CACHE_PREFIX}:{practitioner_id}:*",
        ]
        for pattern in patterns:
            try:
                cache.delete(pattern)
            except Exception:
                pass

    @classmethod
    def get_years_with_results(cls, practitioner) -> List[int]:
        """
        Retourne les annees ou le pratiquant a des resultats.
        Utile pour les filtres.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            # Annees depuis CompetitionResult
            years_cr = set(CompetitionResult.objects.filter(
                practitioner=practitioner
            ).values_list(
                'competition__start_date__year', flat=True
            ).distinct())

            # Annees depuis CompetitionRanking
            years_rank = set(CompetitionRanking.objects.filter(
                practitioner=practitioner
            ).values_list(
                'competition__start_date__year', flat=True
            ).distinct())

            # Union des deux ensembles
            all_years = years_cr | years_rank
            return sorted([y for y in all_years if y], reverse=True)

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_years_with_results: {e}")
            return []

    @classmethod
    def get_disciplines_with_results(cls, practitioner) -> List[Dict]:
        """
        Retourne les disciplines ou le pratiquant a des resultats.
        Cherche dans CompetitionResult ET CompetitionRanking.
        """
        try:
            from apps.competitions.models.scoring_results import CompetitionResult
            from apps.competitions.models.technical_scoring import CompetitionRanking

            disciplines_dict = {}

            # Disciplines depuis CompetitionResult
            disciplines_cr = CompetitionResult.objects.filter(
                practitioner=practitioner,
                competition__discipline__isnull=False
            ).values(
                'competition__discipline__id',
                'competition__discipline__name'
            ).distinct()

            for d in disciplines_cr:
                disc_id = d['competition__discipline__id']
                if disc_id and disc_id not in disciplines_dict:
                    disciplines_dict[disc_id] = d['competition__discipline__name']

            # Disciplines depuis CompetitionRanking
            disciplines_rank = CompetitionRanking.objects.filter(
                practitioner=practitioner,
                competition__discipline__isnull=False
            ).values(
                'competition__discipline__id',
                'competition__discipline__name'
            ).distinct()

            for d in disciplines_rank:
                disc_id = d['competition__discipline__id']
                if disc_id and disc_id not in disciplines_dict:
                    disciplines_dict[disc_id] = d['competition__discipline__name']

            return [
                {'id': disc_id, 'name': disc_name}
                for disc_id, disc_name in disciplines_dict.items()
            ]

        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur get_disciplines_with_results: {e}")
            return []
