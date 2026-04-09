"""
Service d'analyse de neutralité des juges.

Ce service calcule des indicateurs statistiques pour détecter les biais potentiels
dans les notations des juges :
- Biais club : favoritisme envers les pratiquants du même club
- Biais nationalité : favoritisme selon la nationalité
- Écart à la moyenne : tendance à noter plus sévèrement ou généreusement
- Dispersion : cohérence des notes (écart-type)
- Corrélation : concordance avec les autres juges
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from statistics import mean, stdev, variance
from collections import defaultdict

from django.db.models import Avg, Count, StdDev, Min, Max, F, Q
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass
class JudgeStats:
    """Statistiques d'un juge."""
    judge_id: int
    judge_name: str
    judge_club: Optional[str]
    judge_nationality: Optional[str]
    total_scores: int
    average_score: float
    std_deviation: float
    min_score: float
    max_score: float
    score_distribution: Dict[str, int]  # Répartition par tranches


@dataclass
class BiasIndicator:
    """Indicateur de biais."""
    value: float  # Valeur de l'écart
    severity: str  # 'neutral', 'low', 'medium', 'high'
    description: str
    sample_size: int  # Nombre d'échantillons


@dataclass
class JudgeNeutralityReport:
    """Rapport complet de neutralité d'un juge."""
    judge_id: int
    judge_name: str
    judge_club: Optional[str]
    judge_nationality: Optional[str]
    competition_id: int
    competition_name: str

    # Statistiques générales
    total_scores: int
    average_score: float
    std_deviation: float

    # Indicateurs de biais
    club_bias: BiasIndicator
    nationality_bias: BiasIndicator
    position_bias: BiasIndicator  # Sévère/Généreux
    correlation_score: float  # 0-100%

    # Distribution des notes
    score_distribution: Dict[str, int]

    # Score global de neutralité (0-100)
    neutrality_score: int

    # Alertes
    alerts: List[str]


class JudgeNeutralityService:
    """Service d'analyse de neutralité des juges."""

    # Seuils de détection des biais
    CLUB_BIAS_THRESHOLD_LOW = 0.3
    CLUB_BIAS_THRESHOLD_MEDIUM = 0.5
    CLUB_BIAS_THRESHOLD_HIGH = 0.8

    NATIONALITY_BIAS_THRESHOLD_LOW = 0.2
    NATIONALITY_BIAS_THRESHOLD_MEDIUM = 0.4
    NATIONALITY_BIAS_THRESHOLD_HIGH = 0.6

    POSITION_BIAS_THRESHOLD_LOW = 0.2
    POSITION_BIAS_THRESHOLD_MEDIUM = 0.4
    POSITION_BIAS_THRESHOLD_HIGH = 0.6

    def __init__(self):
        self._cache = {}

    def analyze_judge_for_competition(
        self,
        judge_user_id: int,
        competition_id: int
    ) -> Optional[JudgeNeutralityReport]:
        """
        Analyse complète de la neutralité d'un juge pour une compétition.
        """
        from apps.competitions.models import Competition
        from apps.competitions.models.technical_scoring import Score, Performance

        try:
            competition = Competition.objects.get(id=competition_id)
        except Competition.DoesNotExist:
            logger.error(f"Competition {competition_id} not found")
            return None

        try:
            judge_user = User.objects.get(id=judge_user_id)
        except User.DoesNotExist:
            logger.error(f"User {judge_user_id} not found")
            return None

        # Récupérer les informations du juge
        judge_info = self._get_judge_info(judge_user)

        # Récupérer tous les scores du juge pour cette compétition
        scores_data = self._get_judge_scores_for_competition(
            judge_user_id, competition_id
        )

        if not scores_data:
            return None

        # Calculer les statistiques de base
        basic_stats = self._calculate_basic_stats(scores_data)

        # Calculer les indicateurs de biais
        club_bias = self._calculate_club_bias(
            judge_user_id, competition_id, judge_info.get('club_id')
        )

        nationality_bias = self._calculate_nationality_bias(
            judge_user_id, competition_id, judge_info.get('nationality')
        )

        position_bias = self._calculate_position_bias(
            judge_user_id, competition_id
        )

        correlation = self._calculate_correlation_with_others(
            judge_user_id, competition_id
        )

        # Calculer la distribution des notes
        distribution = self._calculate_score_distribution(scores_data)

        # Calculer le score global de neutralité
        neutrality_score = self._calculate_neutrality_score(
            club_bias, nationality_bias, position_bias, correlation
        )

        # Générer les alertes
        alerts = self._generate_alerts(
            club_bias, nationality_bias, position_bias, correlation
        )

        return JudgeNeutralityReport(
            judge_id=judge_user_id,
            judge_name=judge_info.get('name', 'Inconnu'),
            judge_club=judge_info.get('club_name'),
            judge_nationality=judge_info.get('nationality'),
            competition_id=competition_id,
            competition_name=competition.title,
            total_scores=basic_stats['count'],
            average_score=basic_stats['average'],
            std_deviation=basic_stats['std_dev'],
            club_bias=club_bias,
            nationality_bias=nationality_bias,
            position_bias=position_bias,
            correlation_score=correlation,
            score_distribution=distribution,
            neutrality_score=neutrality_score,
            alerts=alerts
        )

    def analyze_all_judges_for_competition(
        self,
        competition_id: int
    ) -> List[JudgeNeutralityReport]:
        """
        Analyse tous les juges d'une compétition.
        """
        from apps.competitions.models.technical_scoring import Score

        # Récupérer tous les juges qui ont noté dans cette compétition
        judge_ids = Score.objects.filter(
            performance__category__competition_id=competition_id
        ).values_list('judge__user_id', flat=True).distinct()

        # Fallback: chercher dans TechnicalScore si Score est vide
        if not judge_ids:
            try:
                from apps.competitions.models.technical_scoring import TechnicalScore
                judge_ids = TechnicalScore.objects.filter(
                    performance__category__competition_id=competition_id
                ).values_list('judge_id', flat=True).distinct()
            except Exception:
                pass

        reports = []
        for judge_id in judge_ids:
            if judge_id:
                report = self.analyze_judge_for_competition(judge_id, competition_id)
                if report:
                    reports.append(report)

        # Trier par score de neutralité (du plus bas au plus haut)
        reports.sort(key=lambda r: r.neutrality_score)

        return reports

    def get_competition_summary(self, competition_id) -> Dict[str, Any]:
        """
        Résumé de neutralité pour une compétition entière.

        Args:
            competition_id: Peut être un int (ID) ou un objet Competition
        """
        # Accepter un objet Competition ou un ID
        from apps.competitions.models import Competition
        if isinstance(competition_id, Competition):
            competition_id = competition_id.id

        reports = self.analyze_all_judges_for_competition(competition_id)

        if not reports:
            return {
                'competition_id': competition_id,
                'total_judges': 0,
                'average_neutrality': 0,
                'judges_with_alerts': 0,
                'reports': []
            }

        return {
            'competition_id': competition_id,
            'total_judges': len(reports),
            'average_neutrality': mean([r.neutrality_score for r in reports]),
            'judges_with_alerts': sum(1 for r in reports if r.alerts),
            'high_risk_judges': [r for r in reports if r.neutrality_score < 60],
            'medium_risk_judges': [r for r in reports if 60 <= r.neutrality_score < 80],
            'low_risk_judges': [r for r in reports if r.neutrality_score >= 80],
            'reports': reports
        }

    def _get_judge_info(self, judge_user: User) -> Dict[str, Any]:
        """Récupère les informations du juge."""
        info = {
            'name': judge_user.get_full_name() or judge_user.username,
            'club_id': None,
            'club_name': None,
            'nationality': None
        }

        # Chercher le practitioner associé
        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=judge_user).first()
            if practitioner:
                info['nationality'] = practitioner.nationality
                if practitioner.organization:
                    info['club_id'] = practitioner.organization_id
                    info['club_name'] = practitioner.organization.name
        except Exception as e:
            logger.warning(f"Error getting judge info: {e}")

        return info

    def _get_judge_scores_for_competition(
        self,
        judge_user_id: int,
        competition_id: int
    ) -> List[Dict]:
        """Récupère tous les scores d'un juge pour une compétition."""
        from apps.competitions.models.technical_scoring import Score, TechnicalScore

        scores_data = []

        # Essayer d'abord avec Score (via Judge model)
        try:
            from apps.competitions.models.judges import Judge
            judge = Judge.objects.filter(user_id=judge_user_id).first()
            if judge:
                scores = Score.objects.filter(
                    judge=judge,
                    performance__category__competition_id=competition_id
                ).select_related(
                    'performance__practitioner',
                    'performance__category',
                    'criterion'
                )

                for score in scores:
                    practitioner = score.performance.practitioner
                    scores_data.append({
                        'score_id': score.id,
                        'value': float(score.value),
                        'practitioner_id': practitioner.id,
                        'practitioner_club_id': practitioner.organization_id,
                        'practitioner_nationality': practitioner.nationality,
                        'category_id': score.performance.category_id,
                        'criterion_name': score.criterion.name if score.criterion else None
                    })
        except Exception as e:
            logger.warning(f"Error fetching Score data: {e}")

        # Essayer aussi avec TechnicalScore (via User directement)
        try:
            tech_scores = TechnicalScore.objects.filter(
                judge_id=judge_user_id,
                performance__category__competition_id=competition_id
            ).select_related(
                'performance__practitioner',
                'performance__category',
                'criterion'
            )

            for score in tech_scores:
                practitioner = score.performance.practitioner
                scores_data.append({
                    'score_id': score.id,
                    'value': float(score.value),
                    'practitioner_id': practitioner.id,
                    'practitioner_club_id': practitioner.organization_id,
                    'practitioner_nationality': practitioner.nationality,
                    'category_id': score.performance.category_id,
                    'criterion_name': score.criterion.name if score.criterion else None
                })
        except Exception as e:
            logger.warning(f"Error fetching TechnicalScore data: {e}")

        return scores_data

    def _calculate_basic_stats(self, scores_data: List[Dict]) -> Dict[str, float]:
        """Calcule les statistiques de base."""
        if not scores_data:
            return {'count': 0, 'average': 0, 'std_dev': 0, 'min': 0, 'max': 0}

        values = [s['value'] for s in scores_data]

        return {
            'count': len(values),
            'average': round(mean(values), 2),
            'std_dev': round(stdev(values), 2) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values)
        }

    def _calculate_club_bias(
        self,
        judge_user_id: int,
        competition_id: int,
        judge_club_id: Optional[int]
    ) -> BiasIndicator:
        """
        Calcule le biais club.
        Compare les notes données aux pratiquants du même club vs les autres.
        """
        if not judge_club_id:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Club du juge inconnu",
                sample_size=0
            )

        scores_data = self._get_judge_scores_for_competition(
            judge_user_id, competition_id
        )

        if not scores_data:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Aucune donnée",
                sample_size=0
            )

        # Séparer les scores par appartenance au club
        same_club_scores = [
            s['value'] for s in scores_data
            if s['practitioner_club_id'] == judge_club_id
        ]
        other_club_scores = [
            s['value'] for s in scores_data
            if s['practitioner_club_id'] != judge_club_id
        ]

        if not same_club_scores or not other_club_scores:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Pas assez de données comparatives",
                sample_size=len(scores_data)
            )

        # Calculer l'écart
        avg_same = mean(same_club_scores)
        avg_other = mean(other_club_scores)
        bias_value = round(avg_same - avg_other, 2)

        # Déterminer la sévérité
        abs_bias = abs(bias_value)
        if abs_bias < self.CLUB_BIAS_THRESHOLD_LOW:
            severity = 'neutral'
            description = "Pas de biais détecté"
        elif abs_bias < self.CLUB_BIAS_THRESHOLD_MEDIUM:
            severity = 'low'
            description = f"Léger {'favoritisme' if bias_value > 0 else 'défavoritisme'} club"
        elif abs_bias < self.CLUB_BIAS_THRESHOLD_HIGH:
            severity = 'medium'
            description = f"{'Favoritisme' if bias_value > 0 else 'Défavoritisme'} club modéré"
        else:
            severity = 'high'
            description = f"{'Favoritisme' if bias_value > 0 else 'Défavoritisme'} club significatif"

        return BiasIndicator(
            value=bias_value,
            severity=severity,
            description=description,
            sample_size=len(same_club_scores) + len(other_club_scores)
        )

    def _calculate_nationality_bias(
        self,
        judge_user_id: int,
        competition_id: int,
        judge_nationality: Optional[str]
    ) -> BiasIndicator:
        """
        Calcule le biais nationalité.
        Compare les notes données aux pratiquants de même nationalité vs les autres.
        """
        if not judge_nationality:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Nationalité du juge inconnue",
                sample_size=0
            )

        scores_data = self._get_judge_scores_for_competition(
            judge_user_id, competition_id
        )

        if not scores_data:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Aucune donnée",
                sample_size=0
            )

        # Séparer les scores par nationalité
        same_nat_scores = [
            s['value'] for s in scores_data
            if s['practitioner_nationality'] and
               s['practitioner_nationality'].upper() == judge_nationality.upper()
        ]
        other_nat_scores = [
            s['value'] for s in scores_data
            if s['practitioner_nationality'] and
               s['practitioner_nationality'].upper() != judge_nationality.upper()
        ]

        if not same_nat_scores or not other_nat_scores:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Pas assez de données comparatives",
                sample_size=len(scores_data)
            )

        # Calculer l'écart
        avg_same = mean(same_nat_scores)
        avg_other = mean(other_nat_scores)
        bias_value = round(avg_same - avg_other, 2)

        # Déterminer la sévérité
        abs_bias = abs(bias_value)
        if abs_bias < self.NATIONALITY_BIAS_THRESHOLD_LOW:
            severity = 'neutral'
            description = "Pas de biais détecté"
        elif abs_bias < self.NATIONALITY_BIAS_THRESHOLD_MEDIUM:
            severity = 'low'
            description = f"Léger {'favoritisme' if bias_value > 0 else 'défavoritisme'} nationalité"
        elif abs_bias < self.NATIONALITY_BIAS_THRESHOLD_HIGH:
            severity = 'medium'
            description = f"{'Favoritisme' if bias_value > 0 else 'Défavoritisme'} nationalité modéré"
        else:
            severity = 'high'
            description = f"{'Favoritisme' if bias_value > 0 else 'Défavoritisme'} nationalité significatif"

        return BiasIndicator(
            value=bias_value,
            severity=severity,
            description=description,
            sample_size=len(same_nat_scores) + len(other_nat_scores)
        )

    def _calculate_position_bias(
        self,
        judge_user_id: int,
        competition_id: int
    ) -> BiasIndicator:
        """
        Calcule l'écart à la moyenne des autres juges.
        Détermine si le juge est systématiquement sévère ou généreux.
        """
        from apps.competitions.models.technical_scoring import Score, TechnicalScore

        # Récupérer la moyenne de ce juge
        scores_data = self._get_judge_scores_for_competition(
            judge_user_id, competition_id
        )

        if not scores_data:
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Aucune donnée",
                sample_size=0
            )

        judge_avg = mean([s['value'] for s in scores_data])

        # Calculer la moyenne globale de tous les juges pour cette compétition
        try:
            all_scores = []

            # Scores via Score model
            try:
                scores = Score.objects.filter(
                    performance__category__competition_id=competition_id
                ).values_list('value', flat=True)
                all_scores.extend([float(v) for v in scores])
            except Exception:
                pass

            # Scores via TechnicalScore model
            try:
                tech_scores = TechnicalScore.objects.filter(
                    performance__category__competition_id=competition_id
                ).values_list('value', flat=True)
                all_scores.extend([float(v) for v in tech_scores])
            except Exception:
                pass

            if not all_scores:
                return BiasIndicator(
                    value=0,
                    severity='neutral',
                    description="Pas de données comparatives",
                    sample_size=len(scores_data)
                )

            global_avg = mean(all_scores)
            bias_value = round(judge_avg - global_avg, 2)

        except Exception as e:
            logger.error(f"Error calculating position bias: {e}")
            return BiasIndicator(
                value=0,
                severity='neutral',
                description="Erreur de calcul",
                sample_size=0
            )

        # Déterminer la sévérité
        abs_bias = abs(bias_value)
        if abs_bias < self.POSITION_BIAS_THRESHOLD_LOW:
            severity = 'neutral'
            description = "Dans la moyenne"
        elif abs_bias < self.POSITION_BIAS_THRESHOLD_MEDIUM:
            severity = 'low'
            description = f"Légèrement {'généreux' if bias_value > 0 else 'sévère'}"
        elif abs_bias < self.POSITION_BIAS_THRESHOLD_HIGH:
            severity = 'medium'
            description = f"{'Généreux' if bias_value > 0 else 'Sévère'}"
        else:
            severity = 'high'
            description = f"Très {'généreux' if bias_value > 0 else 'sévère'}"

        return BiasIndicator(
            value=bias_value,
            severity=severity,
            description=description,
            sample_size=len(scores_data)
        )

    def _calculate_correlation_with_others(
        self,
        judge_user_id: int,
        competition_id: int
    ) -> float:
        """
        Calcule la corrélation entre les notes de ce juge et la moyenne des autres.
        Retourne un pourcentage de concordance (0-100).
        """
        from apps.competitions.models.technical_scoring import Score, TechnicalScore

        try:
            # Récupérer les performances notées par ce juge
            scores_data = self._get_judge_scores_for_competition(
                judge_user_id, competition_id
            )

            if len(scores_data) < 3:
                return 100.0  # Pas assez de données

            # Pour chaque performance, comparer avec la moyenne des autres juges
            correlations = []

            for score in scores_data:
                judge_score = score['value']
                practitioner_id = score['practitioner_id']
                category_id = score['category_id']

                # Moyenne des autres juges pour le même pratiquant/catégorie
                other_scores = []

                try:
                    scores = Score.objects.filter(
                        performance__practitioner_id=practitioner_id,
                        performance__category_id=category_id
                    ).exclude(
                        judge__user_id=judge_user_id
                    ).values_list('value', flat=True)
                    other_scores.extend([float(v) for v in scores])
                except Exception:
                    pass

                try:
                    tech_scores = TechnicalScore.objects.filter(
                        performance__practitioner_id=practitioner_id,
                        performance__category_id=category_id
                    ).exclude(
                        judge_id=judge_user_id
                    ).values_list('value', flat=True)
                    other_scores.extend([float(v) for v in tech_scores])
                except Exception:
                    pass

                if other_scores:
                    other_avg = mean(other_scores)
                    # Calculer l'écart absolu
                    diff = abs(judge_score - other_avg)
                    # Convertir en score de concordance (max 10 points d'écart = 0%)
                    concordance = max(0, 100 - (diff * 20))
                    correlations.append(concordance)

            if correlations:
                return round(mean(correlations), 1)

            return 100.0

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 100.0

    def _calculate_score_distribution(
        self,
        scores_data: List[Dict]
    ) -> Dict[str, int]:
        """Calcule la distribution des notes par tranches."""
        distribution = {
            '0-2': 0,
            '2-3': 0,
            '3-4': 0,
            '4-5': 0,
            '5-6': 0,
            '6-7': 0,
            '7-8': 0,
            '8-9': 0,
            '9-10': 0
        }

        for score in scores_data:
            value = score['value']
            if value < 2:
                distribution['0-2'] += 1
            elif value < 3:
                distribution['2-3'] += 1
            elif value < 4:
                distribution['3-4'] += 1
            elif value < 5:
                distribution['4-5'] += 1
            elif value < 6:
                distribution['5-6'] += 1
            elif value < 7:
                distribution['6-7'] += 1
            elif value < 8:
                distribution['7-8'] += 1
            elif value < 9:
                distribution['8-9'] += 1
            else:
                distribution['9-10'] += 1

        return distribution

    def _calculate_neutrality_score(
        self,
        club_bias: BiasIndicator,
        nationality_bias: BiasIndicator,
        position_bias: BiasIndicator,
        correlation: float
    ) -> int:
        """
        Calcule un score global de neutralité de 0 à 100.
        100 = parfaitement neutre, 0 = fortement biaisé
        """
        score = 100

        # Pénalités pour biais club (poids: 30%)
        severity_penalties = {'neutral': 0, 'low': 10, 'medium': 20, 'high': 30}
        score -= severity_penalties.get(club_bias.severity, 0)

        # Pénalités pour biais nationalité (poids: 25%)
        nat_penalties = {'neutral': 0, 'low': 8, 'medium': 16, 'high': 25}
        score -= nat_penalties.get(nationality_bias.severity, 0)

        # Pénalités pour position (poids: 20%)
        pos_penalties = {'neutral': 0, 'low': 5, 'medium': 12, 'high': 20}
        score -= pos_penalties.get(position_bias.severity, 0)

        # Bonus/malus corrélation (poids: 25%)
        # correlation est déjà entre 0 et 100
        correlation_contribution = (correlation - 50) / 2  # -25 à +25
        score += correlation_contribution

        return max(0, min(100, int(score)))

    def _generate_alerts(
        self,
        club_bias: BiasIndicator,
        nationality_bias: BiasIndicator,
        position_bias: BiasIndicator,
        correlation: float
    ) -> List[str]:
        """Génère les alertes basées sur les indicateurs."""
        alerts = []

        if club_bias.severity in ('medium', 'high'):
            alerts.append(
                f"Biais club détecté: {club_bias.description} "
                f"({club_bias.value:+.2f} pts)"
            )

        if nationality_bias.severity in ('medium', 'high'):
            alerts.append(
                f"Biais nationalité détecté: {nationality_bias.description} "
                f"({nationality_bias.value:+.2f} pts)"
            )

        if position_bias.severity == 'high':
            alerts.append(
                f"Position extrême: {position_bias.description} "
                f"({position_bias.value:+.2f} pts par rapport à la moyenne)"
            )

        if correlation < 60:
            alerts.append(
                f"Faible concordance avec les autres juges ({correlation:.0f}%)"
            )

        return alerts


# Instance singleton pour utilisation facile
judge_neutrality_service = JudgeNeutralityService()
