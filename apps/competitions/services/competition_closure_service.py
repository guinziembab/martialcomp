# -*- coding: utf-8 -*-
"""
Service de clôture de compétition.

Permet aux organisateurs de finaliser une compétition :
- Valider que la compétition peut être clôturée
- Générer les résultats finaux depuis les combats et performances techniques
- Mettre à jour le statut de la compétition

Date: 17 décembre 2025
"""

from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Tuple, List, Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class CompetitionClosureService:
    """
    Service pour la clôture des compétitions.

    Gère la finalisation d'une compétition, incluant:
    - Vérification des prérequis de clôture
    - Génération des résultats finaux
    - Mise à jour du statut
    """

    @classmethod
    def can_close(cls, competition) -> Tuple[bool, List[str]]:
        """
        Vérifie si une compétition peut être clôturée.

        Args:
            competition: L'objet Competition à vérifier

        Returns:
            Tuple (can_close: bool, warnings: List[str])
            - can_close: True si la compétition peut être clôturée
            - warnings: Liste des avertissements (catégories non terminées, combats en cours, etc.)
        """
        warnings = []

        # Vérifier le statut actuel
        if competition.status == 'completed':
            return False, [_("La compétition est déjà clôturée.")]

        if competition.status == 'cancelled':
            return False, [_("La compétition a été annulée.")]

        if competition.status == 'draft':
            warnings.append(_("La compétition est encore en brouillon."))

        # Vérifier les catégories non terminées
        from apps.competitions.models import CompetitionCategory
        categories = CompetitionCategory.objects.filter(competition=competition)
        incomplete_categories = categories.filter(is_completed=False)

        if incomplete_categories.exists():
            for cat in incomplete_categories[:5]:
                warnings.append(_("Catégorie '%(name)s' non terminée.") % {'name': cat.name})
            if incomplete_categories.count() > 5:
                warnings.append(_("... et %(count)d autres catégories non terminées.") % {
                    'count': incomplete_categories.count() - 5
                })

        # Vérifier les combats en cours
        from apps.competitions.models import Combat
        active_combats = Combat.objects.filter(
            competition=competition,
            status='en_cours'
        )

        if active_combats.exists():
            warnings.append(_("%(count)d combat(s) en cours.") % {'count': active_combats.count()})

        # Vérifier les combats planifiés non joués
        scheduled_combats = Combat.objects.filter(
            competition=competition,
            status='planifie'
        )

        if scheduled_combats.exists():
            warnings.append(_("%(count)d combat(s) planifié(s) non joué(s).") % {
                'count': scheduled_combats.count()
            })

        # On peut toujours clôturer si le statut n'est pas 'completed' ou 'cancelled'
        # Les avertissements sont informatifs
        can_close = competition.status not in ('completed', 'cancelled')

        return can_close, warnings

    @classmethod
    @transaction.atomic
    def close_competition(cls, competition, closed_by_user) -> Tuple[bool, List[str]]:
        """
        Clôture une compétition et génère les résultats finaux.

        Args:
            competition: L'objet Competition à clôturer
            closed_by_user: L'utilisateur qui effectue la clôture

        Returns:
            Tuple (success: bool, messages: List[str])
        """
        messages = []

        # Vérifier si on peut clôturer
        can_close, warnings = cls.can_close(competition)

        if not can_close:
            return False, warnings

        # Ajouter les avertissements aux messages
        messages.extend(warnings)

        try:
            # 1. Marquer toutes les catégories comme terminées
            categories_updated = cls._mark_categories_completed(competition)
            messages.append(_("%(count)d catégorie(s) marquée(s) comme terminée(s).") % {
                'count': categories_updated
            })

            # 2. Terminer les combats en cours (avec match nul)
            combats_ended = cls._end_active_combats(competition)
            if combats_ended > 0:
                messages.append(_("%(count)d combat(s) en cours terminé(s) (match nul).") % {
                    'count': combats_ended
                })

            # 3. Générer les résultats depuis les combats
            combat_results = cls._generate_results_from_combats(competition)
            messages.append(_("%(count)d résultat(s) de combat généré(s).") % {
                'count': combat_results
            })

            # 4. Générer les résultats depuis les performances techniques
            tech_results = cls._generate_results_from_performances(competition)
            messages.append(_("%(count)d résultat(s) technique(s) généré(s).") % {
                'count': tech_results
            })

            # 5. Désactiver les juges ad-hoc de cette compétition
            try:
                from apps.competitions.models.adhoc_judges import AdHocJudge
                adhoc_count = AdHocJudge.objects.filter(
                    competition=competition, status='active'
                ).update(status='completed')
                if adhoc_count:
                    messages.append(_("%(count)d juge(s) ad-hoc désactivé(s).") % {'count': adhoc_count})
            except ImportError:
                pass

            # 6. Mettre à jour le statut de la compétition
            competition.status = 'completed'
            competition.save(update_fields=['status'])

            messages.append(_("Compétition clôturée avec succès."))

            # Logger l'action
            logger.info(
                f"Competition {competition.id} ({competition.title}) closed by user {closed_by_user.id}"
            )

            return True, messages

        except Exception as e:
            logger.error(f"Error closing competition {competition.id}: {str(e)}")
            return False, [_("Erreur lors de la clôture: %(error)s") % {'error': str(e)}]

    @classmethod
    def _mark_categories_completed(cls, competition) -> int:
        """Marque toutes les catégories comme terminées."""
        from apps.competitions.models import CompetitionCategory

        updated = CompetitionCategory.objects.filter(
            competition=competition,
            is_completed=False
        ).update(is_completed=True)

        return updated

    @classmethod
    def _end_active_combats(cls, competition) -> int:
        """Termine les combats en cours avec un match nul."""
        from apps.competitions.models import Combat

        active_combats = Combat.objects.filter(
            competition=competition,
            status='en_cours'
        )

        count = 0
        for combat in active_combats:
            combat.status = 'termine'
            combat.est_nul = True
            combat.fin_combat = timezone.now()
            combat.save(update_fields=['status', 'est_nul', 'fin_combat'])
            count += 1

        return count

    @classmethod
    def _generate_results_from_combats(cls, competition) -> int:
        """
        Génère les CompetitionResult depuis les combats terminés.

        Pour chaque pratiquant ayant participé à des combats:
        - Compte victoires/défaites/nuls
        - Calcule les points marqués/encaissés
        - Crée ou met à jour le CompetitionResult
        """
        from apps.competitions.models import Combat, CompetitionResult, Practitioner

        # Récupérer tous les combats terminés individuels
        combats = Combat.objects.filter(
            competition=competition,
            status='termine',
            type_combat='individuel'
        ).select_related('pratiquant_rouge', 'pratiquant_blanc')

        # Calculer les stats par pratiquant
        practitioner_stats = {}

        for combat in combats:
            # Stats pour le pratiquant rouge
            if combat.pratiquant_rouge:
                pid = combat.pratiquant_rouge.id
                if pid not in practitioner_stats:
                    practitioner_stats[pid] = {
                        'practitioner': combat.pratiquant_rouge,
                        'combats': 0,
                        'victories': 0,
                        'defeats': 0,
                        'draws': 0,
                        'points_for': Decimal('0'),
                        'points_against': Decimal('0'),
                    }

                stats = practitioner_stats[pid]
                stats['combats'] += 1
                stats['points_for'] += combat.score_rouge or Decimal('0')
                stats['points_against'] += combat.score_blanc or Decimal('0')

                if combat.est_nul:
                    stats['draws'] += 1
                elif combat.vainqueur == 'rouge':
                    stats['victories'] += 1
                else:
                    stats['defeats'] += 1

            # Stats pour le pratiquant blanc
            if combat.pratiquant_blanc:
                pid = combat.pratiquant_blanc.id
                if pid not in practitioner_stats:
                    practitioner_stats[pid] = {
                        'practitioner': combat.pratiquant_blanc,
                        'combats': 0,
                        'victories': 0,
                        'defeats': 0,
                        'draws': 0,
                        'points_for': Decimal('0'),
                        'points_against': Decimal('0'),
                    }

                stats = practitioner_stats[pid]
                stats['combats'] += 1
                stats['points_for'] += combat.score_blanc or Decimal('0')
                stats['points_against'] += combat.score_rouge or Decimal('0')

                if combat.est_nul:
                    stats['draws'] += 1
                elif combat.vainqueur == 'blanc':
                    stats['victories'] += 1
                else:
                    stats['defeats'] += 1

        # Créer/mettre à jour les CompetitionResult
        results_created = 0

        for pid, stats in practitioner_stats.items():
            # Calculer le score (points)
            score = stats['points_for'] - stats['points_against']

            # Créer ou mettre à jour le résultat
            result, created = CompetitionResult.objects.update_or_create(
                competition=competition,
                practitioner=stats['practitioner'],
                category=None,  # Résultat global pour les combats
                defaults={
                    'score': score,
                    'date': competition.end_date or timezone.now().date(),
                    'notes': _(
                        "Combats: %(combats)d | V: %(v)d | D: %(d)d | N: %(n)d | "
                        "Points: %(pf)s - %(pa)s"
                    ) % {
                        'combats': stats['combats'],
                        'v': stats['victories'],
                        'd': stats['defeats'],
                        'n': stats['draws'],
                        'pf': stats['points_for'],
                        'pa': stats['points_against'],
                    }
                }
            )

            if created:
                results_created += 1

        return results_created

    @classmethod
    def _generate_results_from_performances(cls, competition) -> int:
        """
        Génère les CompetitionResult depuis les performances techniques.

        Pour chaque pratiquant ayant des résultats de performance:
        - Récupère le classement dans chaque catégorie
        - Attribue les médailles (top 3)
        - Crée ou met à jour le CompetitionResult
        """
        from apps.competitions.models import (
            RankingEntry, CategoryRanking, CompetitionResult
        )

        results_created = 0

        # Récupérer tous les classements finaux
        rankings = CategoryRanking.objects.filter(
            competition=competition
        ).select_related('category')

        for ranking in rankings:
            entries = RankingEntry.objects.filter(
                ranking=ranking
            ).select_related('practitioner')

            for entry in entries:
                # Déterminer la médaille
                medal = 'none'
                if entry.rank == 1:
                    medal = 'gold'
                elif entry.rank == 2:
                    medal = 'silver'
                elif entry.rank == 3:
                    medal = 'bronze'

                # Créer ou mettre à jour le résultat
                result, created = CompetitionResult.objects.update_or_create(
                    competition=competition,
                    practitioner=entry.practitioner,
                    category=ranking.category,
                    defaults={
                        'rank': entry.rank,
                        'score': entry.score,
                        'medal': medal,
                        'date': competition.end_date or timezone.now().date(),
                    }
                )

                if created:
                    results_created += 1

        return results_created

    @classmethod
    def get_combat_performance(
        cls,
        practitioner,
        competition=None
    ) -> Dict[str, Any]:
        """
        Récupère toutes les performances combat d'un pratiquant.

        Args:
            practitioner: Le pratiquant
            competition: Optionnel, filtrer par compétition

        Returns:
            Dict avec les listes de combats et les statistiques
        """
        from apps.competitions.models import Combat, MembreEquipe

        # Filtres de base
        filters_rouge = Q(pratiquant_rouge=practitioner, status='termine')
        filters_blanc = Q(pratiquant_blanc=practitioner, status='termine')

        if competition:
            filters_rouge &= Q(competition=competition)
            filters_blanc &= Q(competition=competition)

        # Combats individuels
        individual_combats = []

        # Combats en tant que rouge
        combats_rouge = Combat.objects.filter(
            filters_rouge,
            type_combat='individuel'
        ).select_related(
            'competition', 'pratiquant_blanc', 'poule__category'
        ).order_by('-fin_combat')

        for combat in combats_rouge:
            individual_combats.append({
                'id': combat.id,
                'competition': combat.competition.title,
                'competition_id': combat.competition.id,
                'date': combat.fin_combat,
                'opponent': combat.pratiquant_blanc.full_name if combat.pratiquant_blanc else _("Non défini"),
                'opponent_id': combat.pratiquant_blanc.id if combat.pratiquant_blanc else None,
                'score_for': float(combat.score_rouge or 0),
                'score_against': float(combat.score_blanc or 0),
                'is_winner': combat.vainqueur == 'rouge',
                'is_draw': combat.est_nul,
                'result': _("Victoire") if combat.vainqueur == 'rouge' else (_("Nul") if combat.est_nul else _("Défaite")),
                'category': combat.poule.category.name if combat.poule and combat.poule.category else None,
                'color': 'rouge',
            })

        # Combats en tant que blanc
        combats_blanc = Combat.objects.filter(
            filters_blanc,
            type_combat='individuel'
        ).select_related(
            'competition', 'pratiquant_rouge', 'poule__category'
        ).order_by('-fin_combat')

        for combat in combats_blanc:
            individual_combats.append({
                'id': combat.id,
                'competition': combat.competition.title,
                'competition_id': combat.competition.id,
                'date': combat.fin_combat,
                'opponent': combat.pratiquant_rouge.full_name if combat.pratiquant_rouge else _("Non défini"),
                'opponent_id': combat.pratiquant_rouge.id if combat.pratiquant_rouge else None,
                'score_for': float(combat.score_blanc or 0),
                'score_against': float(combat.score_rouge or 0),
                'is_winner': combat.vainqueur == 'blanc',
                'is_draw': combat.est_nul,
                'result': _("Victoire") if combat.vainqueur == 'blanc' else (_("Nul") if combat.est_nul else _("Défaite")),
                'category': combat.poule.category.name if combat.poule and combat.poule.category else None,
                'color': 'blanc',
            })

        # Trier par date décroissante
        individual_combats.sort(key=lambda x: x['date'] or timezone.now(), reverse=True)

        # Combats par équipe
        team_combats = []

        # Trouver les équipes du pratiquant
        memberships = MembreEquipe.objects.filter(
            pratiquant=practitioner
        ).select_related('equipe')

        for membership in memberships:
            equipe = membership.equipe

            # Combats de l'équipe en rouge
            equipe_rouge_filters = Q(equipe_rouge=equipe, status='termine', type_combat='equipe')
            if competition:
                equipe_rouge_filters &= Q(competition=competition)

            for combat in Combat.objects.filter(equipe_rouge_filters).select_related(
                'competition', 'equipe_blanc', 'poule__category'
            ):
                team_combats.append({
                    'id': combat.id,
                    'competition': combat.competition.title,
                    'competition_id': combat.competition.id,
                    'date': combat.fin_combat,
                    'team': equipe.nom,
                    'team_id': equipe.id,
                    'opponent_team': combat.equipe_blanc.nom if combat.equipe_blanc else _("Non défini"),
                    'opponent_team_id': combat.equipe_blanc.id if combat.equipe_blanc else None,
                    'score_for': float(combat.score_cumul_rouge or combat.score_rouge or 0),
                    'score_against': float(combat.score_cumul_blanc or combat.score_blanc or 0),
                    'is_winner': combat.vainqueur == 'rouge',
                    'is_draw': combat.est_nul,
                    'result': _("Victoire") if combat.vainqueur == 'rouge' else (_("Nul") if combat.est_nul else _("Défaite")),
                    'category': combat.poule.category.name if combat.poule and combat.poule.category else None,
                    'color': 'rouge',
                })

            # Combats de l'équipe en blanc
            equipe_blanc_filters = Q(equipe_blanc=equipe, status='termine', type_combat='equipe')
            if competition:
                equipe_blanc_filters &= Q(competition=competition)

            for combat in Combat.objects.filter(equipe_blanc_filters).select_related(
                'competition', 'equipe_rouge', 'poule__category'
            ):
                team_combats.append({
                    'id': combat.id,
                    'competition': combat.competition.title,
                    'competition_id': combat.competition.id,
                    'date': combat.fin_combat,
                    'team': equipe.nom,
                    'team_id': equipe.id,
                    'opponent_team': combat.equipe_rouge.nom if combat.equipe_rouge else _("Non défini"),
                    'opponent_team_id': combat.equipe_rouge.id if combat.equipe_rouge else None,
                    'score_for': float(combat.score_cumul_blanc or combat.score_blanc or 0),
                    'score_against': float(combat.score_cumul_rouge or combat.score_rouge or 0),
                    'is_winner': combat.vainqueur == 'blanc',
                    'is_draw': combat.est_nul,
                    'result': _("Victoire") if combat.vainqueur == 'blanc' else (_("Nul") if combat.est_nul else _("Défaite")),
                    'category': combat.poule.category.name if combat.poule and combat.poule.category else None,
                    'color': 'blanc',
                })

        # Trier par date décroissante et supprimer les doublons
        seen_ids = set()
        unique_team_combats = []
        for tc in sorted(team_combats, key=lambda x: x['date'] or timezone.now(), reverse=True):
            if tc['id'] not in seen_ids:
                seen_ids.add(tc['id'])
                unique_team_combats.append(tc)

        team_combats = unique_team_combats

        # Calculer les statistiques
        all_combats = individual_combats + team_combats

        total_combats = len(all_combats)
        victories = sum(1 for c in all_combats if c['is_winner'])
        defeats = sum(1 for c in all_combats if not c['is_winner'] and not c['is_draw'])
        draws = sum(1 for c in all_combats if c['is_draw'])
        points_scored = sum(c['score_for'] for c in all_combats)
        points_conceded = sum(c['score_against'] for c in all_combats)

        win_rate = round((victories / total_combats * 100), 1) if total_combats > 0 else 0

        return {
            'individual_combats': individual_combats,
            'team_combats': team_combats,
            'stats': {
                'total_combats': total_combats,
                'individual_count': len(individual_combats),
                'team_count': len(team_combats),
                'victories': victories,
                'defeats': defeats,
                'draws': draws,
                'win_rate': win_rate,
                'points_scored': round(points_scored, 2),
                'points_conceded': round(points_conceded, 2),
                'point_difference': round(points_scored - points_conceded, 2),
            }
        }
