# -*- coding: utf-8 -*-
"""
Podium Display Service - Gestion de l'affichage cérémoniel du podium.
Récupère les résultats et prépare les données pour l'affichage progressif.
"""
from django.db.models import Count, Sum, Q, F
from django.utils.translation import gettext_lazy as _

from apps.competitions.models import Competition, CompetitionCategory
from apps.competitions.models.combat import Combat, Equipe, Poule
from apps.competitions.models.technical_scoring import CompetitionRanking
from apps.competitions.services.podium_order_service import PodiumOrderService
from apps.competitions.services.ranking_service import RankingService


class PodiumDisplayService:
    """
    Service pour préparer les données d'affichage cérémoniel du podium.

    Fonctionnalités:
    - Récupère les vainqueurs par catégorie (équipe ou individuel)
    - Prépare les données pour l'affichage progressif (3e → 2e → 1er)
    - Gère les ex-aequo
    - Support des compétitions techniques et combats
    """

    @staticmethod
    def _get_org_display_data(organization):
        """Extrait country_code et logo_url d'une Organisation."""
        if not organization:
            return {'country_code': '', 'logo_url': None}
        country = getattr(organization, 'country', '') or ''
        logo_url = None
        if hasattr(organization, 'logo') and organization.logo:
            try:
                logo_url = organization.logo.url
            except Exception:
                pass
        return {'country_code': country.upper()[:2], 'logo_url': logo_url}

    @staticmethod
    def _get_club_display_data(club):
        """Extrait country_code et logo_url d'un Club."""
        if not club:
            return {'country_code': '', 'logo_url': None}
        country = getattr(club, 'country', '') or ''
        logo_url = None
        if hasattr(club, 'logo') and club.logo:
            try:
                logo_url = club.logo.url
            except Exception:
                pass
        return {'country_code': country.upper()[:2], 'logo_url': logo_url}

    @classmethod
    def get_combat_category_results(cls, category):
        """
        Récupère les résultats d'une catégorie de type combat.
        Vérifie d'abord CompetitionRanking, puis les tables Combat comme fallback.

        Args:
            category: CompetitionCategory instance

        Returns:
            dict: Résultats avec podium (1er, 2e, 3e places)
        """
        # 1. D'abord vérifier si des résultats existent dans CompetitionRanking
        tech_rankings = CompetitionRanking.objects.filter(
            competition=category.competition,
            category=category
        ).select_related('practitioner', 'practitioner__organization').order_by('rank')

        if tech_rankings.exists():
            # Utiliser les résultats de CompetitionRanking
            results = []
            for ranking in tech_rankings:
                practitioner = ranking.practitioner
                photo_url = None
                if hasattr(practitioner, 'photo') and practitioner.photo:
                    photo_url = practitioner.photo.url
                grade_display = None
                if hasattr(practitioner, 'grade') and practitioner.grade:
                    grade_display = str(practitioner.grade)

                org_data = cls._get_org_display_data(practitioner.organization)
                results.append({
                    'type': 'individual',
                    'entity_id': practitioner.id,
                    'entity_name': practitioner.full_name,
                    'photo_url': photo_url,
                    'grade': grade_display or '',
                    'club_name': practitioner.organization.name if practitioner.organization else '',
                    'country_code': org_data['country_code'],
                    'logo_url': org_data['logo_url'],
                    'score': float(ranking.final_score),
                    'rank': ranking.rank,
                    'is_tie': ranking.is_tie,
                })

            return {
                'gold': [r for r in results if r['rank'] == 1],
                'silver': [r for r in results if r['rank'] == 2],
                'bronze': [r for r in results if r['rank'] == 3],
                'all_results': results,
            }

        # 2. Fallback: Déterminer le mode réel en analysant les combats existants
        # Le champ combat_mode peut être incorrect, on vérifie les données réelles
        has_individual = Combat.objects.filter(
            poule__category=category,
            type_combat='individuel'
        ).exists()
        has_team = Combat.objects.filter(
            poule__category=category,
            type_combat='equipe'
        ).exists()

        # Priorité aux combats individuels s'ils existent
        if has_individual and not has_team:
            return cls._get_individual_combat_results(category)
        elif has_team and not has_individual:
            return cls._get_team_combat_results(category)
        elif has_individual and has_team:
            # Mixte : combiner les deux
            individual_results = cls._get_individual_combat_results(category)
            team_results = cls._get_team_combat_results(category)
            # Retourner celui qui a le plus de résultats
            if len(individual_results.get('all_results', [])) >= len(team_results.get('all_results', [])):
                return individual_results
            return team_results
        else:
            # Aucun combat, retourner un podium vide
            return {'gold': [], 'silver': [], 'bronze': [], 'all_results': []}

    @classmethod
    def _get_team_combat_results(cls, category):
        """
        Calcule les résultats pour une catégorie combat en mode équipe.

        Returns:
            dict: {
                'gold': [équipes 1ères],
                'silver': [équipes 2èmes],
                'bronze': [équipes 3èmes],
                'all_results': [tous les résultats triés]
            }
        """
        # Récupérer toutes les poules de cette catégorie
        poules = Poule.objects.filter(category=category)

        # Récupérer toutes les équipes ayant participé
        equipes_participantes = set()
        for poule in poules:
            equipes_participantes.update(poule.equipes.filter(is_active=True))

        # Calculer le bilan de chaque équipe
        results = []
        for equipe in equipes_participantes:
            # Combats en rouge
            combats_rouge = Combat.objects.filter(
                poule__category=category,
                equipe_rouge=equipe,
                status='termine'
            )
            # Combats en blanc
            combats_blanc = Combat.objects.filter(
                poule__category=category,
                equipe_blanc=equipe,
                status='termine'
            )

            wins = 0
            losses = 0
            draws = 0
            total_score = 0

            for combat in combats_rouge:
                total_score += float(combat.score_rouge or 0)
                if combat.vainqueur == 'rouge':
                    wins += 1
                elif combat.vainqueur == 'blanc':
                    losses += 1
                else:
                    draws += 1

            for combat in combats_blanc:
                total_score += float(combat.score_blanc or 0)
                if combat.vainqueur == 'blanc':
                    wins += 1
                elif combat.vainqueur == 'rouge':
                    losses += 1
                else:
                    draws += 1

            total_combats = wins + losses + draws

            if total_combats > 0:
                club_data = cls._get_club_display_data(equipe.club if hasattr(equipe, 'club') else None)
                results.append({
                    'type': 'team',
                    'entity': equipe,
                    'entity_id': equipe.id,
                    'entity_name': equipe.nom,
                    'club_name': equipe.club.name if equipe.club else '',
                    'country_code': club_data['country_code'],
                    'logo_url': club_data['logo_url'],
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'total_combats': total_combats,
                    'total_score': total_score,
                    'win_ratio': wins / total_combats if total_combats > 0 else 0,
                    'members': cls._get_team_members_display(equipe),
                })

        # Trier: victoires (desc), puis ratio victoires (desc), puis score total (desc)
        results.sort(key=lambda x: (-x['wins'], -x['win_ratio'], -x['total_score']))

        # Attribuer les rangs
        return cls._assign_podium_ranks(results)

    @classmethod
    def _get_individual_combat_results(cls, category):
        """
        Calcule les résultats pour une catégorie combat en mode individuel.

        Returns:
            dict: Résultats avec podium
        """
        # Récupérer tous les combats terminés de la catégorie (individuel)
        combats = Combat.objects.filter(
            poule__category=category,
            type_combat='individuel',
            status='termine'
        )
        # Aussi inclure les combats individuels sans type_combat explicite
        if not combats.exists():
            combats = Combat.objects.filter(
                poule__category=category,
                status='termine'
            ).exclude(type_combat='equipe')

        # Récupérer tous les pratiquants ayant participé
        pratiquants_set = set()
        for combat in combats:
            if combat.pratiquant_rouge:
                pratiquants_set.add(combat.pratiquant_rouge)
            if combat.pratiquant_blanc:
                pratiquants_set.add(combat.pratiquant_blanc)

        results = []
        for pratiquant in pratiquants_set:
            combats_rouge = combats.filter(pratiquant_rouge=pratiquant)
            combats_blanc = combats.filter(pratiquant_blanc=pratiquant)

            wins = 0
            losses = 0
            draws = 0
            total_score = 0

            for combat in combats_rouge:
                total_score += float(combat.score_rouge or 0)
                if combat.vainqueur == 'rouge':
                    wins += 1
                elif combat.vainqueur == 'blanc':
                    losses += 1
                else:
                    # est_nul=True OU vainqueur=None → match nul
                    draws += 1

            for combat in combats_blanc:
                total_score += float(combat.score_blanc or 0)
                if combat.vainqueur == 'blanc':
                    wins += 1
                elif combat.vainqueur == 'rouge':
                    losses += 1
                else:
                    draws += 1

            total_combats = wins + losses + draws

            if total_combats > 0:
                org_data = cls._get_org_display_data(pratiquant.organization if hasattr(pratiquant, 'organization') else None)
                results.append({
                    'type': 'individual',
                    'entity': pratiquant,
                    'entity_id': pratiquant.id,
                    'entity_name': pratiquant.full_name,
                    'club_name': pratiquant.club.name if pratiquant.club else '',
                    'country_code': org_data['country_code'],
                    'logo_url': org_data['logo_url'],
                    'photo_url': pratiquant.photo.url if hasattr(pratiquant, 'photo') and pratiquant.photo else None,
                    'grade': str(pratiquant.grade) if hasattr(pratiquant, 'grade') and pratiquant.grade else '',
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'total_combats': total_combats,
                    'total_score': total_score,
                    'win_ratio': wins / total_combats if total_combats > 0 else 0,
                })

        results.sort(key=lambda x: (-x['wins'], -x['win_ratio'], -x['total_score']))
        return cls._assign_podium_ranks(results)

    @classmethod
    def get_technical_category_results(cls, category):
        """
        Récupère les résultats d'une catégorie technique (kata, quyền, etc.).
        Vérifie d'abord CompetitionRanking, puis RankingService comme fallback.

        Args:
            category: CompetitionCategory instance

        Returns:
            dict: Résultats avec podium
        """
        results = []

        # 1. D'abord essayer CompetitionRanking (système technique principal)
        tech_rankings = CompetitionRanking.objects.filter(
            competition=category.competition,
            category=category
        ).select_related('practitioner', 'practitioner__organization').order_by('rank')

        if tech_rankings.exists():
            for ranking in tech_rankings:
                practitioner = ranking.practitioner
                photo_url = None
                if hasattr(practitioner, 'photo') and practitioner.photo:
                    photo_url = practitioner.photo.url
                grade_display = None
                if hasattr(practitioner, 'grade') and practitioner.grade:
                    grade_display = str(practitioner.grade)

                org_data = cls._get_org_display_data(practitioner.organization)
                results.append({
                    'type': 'individual',
                    'entity_id': practitioner.id,
                    'entity_name': practitioner.full_name,
                    'photo_url': photo_url,
                    'grade': grade_display or '',
                    'club_name': practitioner.organization.name if practitioner.organization else '',
                    'country_code': org_data['country_code'],
                    'logo_url': org_data['logo_url'],
                    'score': float(ranking.final_score),
                    'rank': ranking.rank,
                    'is_tie': ranking.is_tie,
                })
        else:
            # 2. Fallback: Utiliser RankingService si CompetitionRanking est vide
            ranking_data = RankingService.calculate_final_ranking(category)

            for item in ranking_data:
                results.append({
                    'type': 'individual',
                    'entity_id': item['practitioner_id'],
                    'entity_name': item['practitioner_name'],
                    'photo_url': item.get('photo_url'),
                    'grade': item.get('grade', ''),
                    'club_name': '',
                    'country_code': '',
                    'logo_url': None,
                    'score': item['score'],
                    'rank': item.get('rank', 0),
                    'is_tie': item.get('is_tie', False),
                })

        # Construire le podium
        podium = {
            'gold': [r for r in results if r['rank'] == 1],
            'silver': [r for r in results if r['rank'] == 2],
            'bronze': [r for r in results if r['rank'] == 3],
            'all_results': results,
        }

        return podium

    @classmethod
    def _assign_podium_ranks(cls, sorted_results):
        """
        Attribue les rangs avec gestion des ex-aequo.

        Args:
            sorted_results: Liste triée par performance

        Returns:
            dict: Podium avec gold, silver, bronze et all_results
        """
        if not sorted_results:
            return {
                'gold': [],
                'silver': [],
                'bronze': [],
                'all_results': [],
            }

        # Attribuer les rangs
        current_rank = 1
        previous_key = None

        for i, result in enumerate(sorted_results):
            sort_key = (result.get('wins', 0), result.get('win_ratio', 0), result.get('total_score', 0))

            if previous_key is not None and sort_key == previous_key:
                result['rank'] = current_rank
                result['is_tie'] = True
                if i > 0 and not sorted_results[i-1].get('is_tie'):
                    sorted_results[i-1]['is_tie'] = True
            else:
                current_rank = i + 1
                result['rank'] = current_rank
                result['is_tie'] = False

            previous_key = sort_key

        # Construire le podium
        podium = {
            'gold': [r for r in sorted_results if r['rank'] == 1],
            'silver': [r for r in sorted_results if r['rank'] == 2],
            'bronze': [r for r in sorted_results if r['rank'] == 3],
            'all_results': sorted_results,
        }

        return podium

    @classmethod
    def _get_team_members_display(cls, equipe):
        """
        Récupère les membres d'une équipe pour l'affichage.

        Args:
            equipe: Equipe instance

        Returns:
            list: Liste des membres avec leurs infos
        """
        members = []
        for membership in equipe.memberships.select_related('pratiquant').order_by('est_remplacant', 'ordre'):
            member_data = {
                'id': membership.pratiquant.id,
                'name': membership.pratiquant.full_name,
                'is_substitute': membership.est_remplacant,
                'is_entente': membership.is_entente,
                'has_fought': membership.a_combattu,
            }
            if hasattr(membership.pratiquant, 'photo') and membership.pratiquant.photo:
                member_data['photo_url'] = membership.pratiquant.photo.url
            members.append(member_data)
        return members

    @classmethod
    def get_category_podium_data(cls, category):
        """
        Récupère les données complètes du podium pour une catégorie.

        Args:
            category: CompetitionCategory instance

        Returns:
            dict: Données formatées pour l'affichage cérémoniel
        """
        # Déterminer le type de catégorie
        comp_type = category.competition_type

        # Vérifier si c'est une catégorie combat ou technique
        is_combat = False
        if comp_type:
            type_name = comp_type.name.lower() if hasattr(comp_type, 'name') else ''
            is_combat = any(kw in type_name for kw in ['combat', 'kumite', 'sparring', 'fight'])

        if is_combat:
            results = cls.get_combat_category_results(category)
        else:
            results = cls.get_technical_category_results(category)

        # Ajouter les métadonnées de la catégorie
        return {
            'category_id': category.id,
            'category_name': category.name,
            'competition_type': comp_type.name if comp_type else '',
            'gender': category.gender,
            'gender_display': cls._get_gender_display(category.gender),
            'age_group': PodiumOrderService.detect_age_group(category),
            'is_combat': is_combat,
            'combat_mode': getattr(category, 'combat_mode', 'team'),
            'podium': results,
        }

    @classmethod
    def get_competition_ceremony_data(cls, competition, include_pending=False):
        """
        Récupère toutes les données pour la cérémonie de remise des prix.

        Args:
            competition: Competition instance
            include_pending: Inclure les catégories non terminées

        Returns:
            dict: Données complètes pour la cérémonie
        """
        # Récupérer les catégories ordonnées
        ordered_categories = PodiumOrderService.get_all_categories_for_podium(
            competition,
            include_pending=include_pending
        )

        ceremony_data = {
            'competition_id': competition.id,
            'competition_title': competition.title,
            'total_categories': len(ordered_categories),
            'categories': [],
        }

        idx = 0
        for cat_data in ordered_categories:
            category = cat_data['category']
            podium_data = cls.get_category_podium_data(category)

            # Exclure les catégories sans aucun résultat
            podium = podium_data.get('podium', {})
            has_results = (
                podium.get('gold') or
                podium.get('silver') or
                podium.get('bronze')
            )
            if not has_results:
                continue

            ceremony_data['categories'].append({
                'index': idx,
                'is_first': idx == 0,
                'is_last': False,  # sera corrigé après
                **podium_data,
            })
            idx += 1

        # Corriger is_last et total
        if ceremony_data['categories']:
            ceremony_data['categories'][-1]['is_last'] = True
        ceremony_data['total_categories'] = len(ceremony_data['categories'])

        return ceremony_data

    @classmethod
    def get_category_for_ceremony(cls, competition, category_index,
                                    comp_type_filter=''):
        """
        Récupère les données d'une catégorie spécifique pour la cérémonie.

        Args:
            competition: Competition instance
            category_index: Index de la catégorie dans l'ordre cérémoniel
            comp_type_filter: Filtre optionnel par type de compétition

        Returns:
            dict: Données de la catégorie avec navigation
        """
        ordered_categories = PodiumOrderService.get_all_categories_for_podium(
            competition,
            include_pending=True
        )

        if not ordered_categories:
            return None

        # Filtrer par type si demandé
        if comp_type_filter:
            ordered_categories = [
                cd for cd in ordered_categories
                if (cd['category'].competition_type and
                    cd['category'].competition_type.name == comp_type_filter)
            ]

        # Filtrer les catégories sans résultats
        filtered = []
        for cat_data in ordered_categories:
            category = cat_data['category']
            podium_data = cls.get_category_podium_data(category)
            p = podium_data.get('podium', {})
            if p.get('gold') or p.get('silver') or p.get('bronze'):
                filtered.append((cat_data, podium_data))

        if not filtered:
            return None

        # S'assurer que l'index est valide
        if category_index < 0:
            category_index = 0
        elif category_index >= len(filtered):
            category_index = len(filtered) - 1

        cat_data, podium_data = filtered[category_index]

        return {
            'index': category_index,
            'total': len(filtered),
            'is_first': category_index == 0,
            'is_last': category_index == len(filtered) - 1,
            'prev_index': category_index - 1 if category_index > 0 else None,
            'next_index': category_index + 1 if category_index < len(filtered) - 1 else None,
            **podium_data,
        }

    @staticmethod
    def _get_gender_display(gender):
        """Retourne le nom d'affichage du genre."""
        displays = {
            'female': _('Féminin'),
            'male': _('Masculin'),
            'mixed': _('Mixte'),
        }
        return displays.get(gender, gender.capitalize() if gender else '')

    @classmethod
    def format_podium_for_reveal(cls, podium):
        """
        Formate les données du podium pour l'animation de révélation.
        Ordre de révélation: 3e → 2e → 1er

        Args:
            podium: dict avec gold, silver, bronze

        Returns:
            list: Étapes de révélation ordonnées
        """
        reveal_steps = []

        # Étape 1: Bronze (3e place)
        if podium.get('bronze'):
            reveal_steps.append({
                'step': 1,
                'position': 3,
                'medal': 'bronze',
                'medal_emoji': '',
                'medal_color': '#CD7F32',
                'winners': podium['bronze'],
                'announcement': _('Troisième place'),
            })

        # Étape 2: Silver (2e place)
        if podium.get('silver'):
            reveal_steps.append({
                'step': 2,
                'position': 2,
                'medal': 'silver',
                'medal_emoji': '',
                'medal_color': '#C0C0C0',
                'winners': podium['silver'],
                'announcement': _('Deuxième place'),
            })

        # Étape 3: Gold (1re place) - avec confetti
        if podium.get('gold'):
            reveal_steps.append({
                'step': 3,
                'position': 1,
                'medal': 'gold',
                'medal_emoji': '',
                'medal_color': '#FFD700',
                'winners': podium['gold'],
                'announcement': _('Première place - Champion'),
                'trigger_celebration': True,
            })

        return reveal_steps
