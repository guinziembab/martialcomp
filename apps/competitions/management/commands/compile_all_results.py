# -*- coding: utf-8 -*-
"""
Commande Django pour compiler tous les résultats d'une compétition
et mettre à jour les podiums (technique + combat).

Usage:
    python manage.py compile_all_results <competition_id>
    python manage.py compile_all_results <competition_id> --dry-run
    python manage.py compile_all_results <competition_id> --verbose
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.competitions.models import Competition, CompetitionCategory
from apps.competitions.models.technical_scoring import (
    TechnicalPerformance, TechnicalScore, ScoringCriterion, CompetitionRanking
)
from apps.competitions.models.scoring_results import (
    CategoryRanking, RankingEntry, PodiumEntry
)
from apps.competitions.models.combat import Combat, Poule, Equipe
from apps.competitions.services.podium_display_service import PodiumDisplayService


class Command(BaseCommand):
    help = 'Compile tous les résultats d\'une compétition et génère les podiums'

    def add_arguments(self, parser):
        parser.add_argument(
            'competition_id',
            type=int,
            help='ID de la compétition'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans modifier la base de données'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails de chaque opération'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le recalcul même si les résultats existent déjà'
        )

    def handle(self, *args, **options):
        competition_id = options['competition_id']
        dry_run = options['dry_run']
        verbose = options['verbose']
        force = options['force']

        # Récupérer la compétition
        try:
            competition = Competition.objects.get(pk=competition_id)
        except Competition.DoesNotExist:
            raise CommandError(f'Compétition avec ID {competition_id} non trouvée')

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'COMPILATION DES RÉSULTATS\n'
            f'Compétition: {competition.title}\n'
            f'Date: {competition.start_date}\n'
            f'{"="*60}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN: Aucune modification ne sera effectuée\n'))

        # Récupérer toutes les catégories
        categories = CompetitionCategory.objects.filter(competition=competition)
        total_categories = categories.count()

        self.stdout.write(f'Catégories trouvées: {total_categories}\n')

        # Statistiques
        stats = {
            'technical_calculated': 0,
            'technical_skipped': 0,
            'combat_calculated': 0,
            'combat_skipped': 0,
            'podiums_generated': 0,
            'errors': []
        }

        # Traiter chaque catégorie
        for i, category in enumerate(categories, 1):
            self.stdout.write(f'\n[{i}/{total_categories}] {category.name}')

            try:
                # Détecter le type de catégorie
                is_combat = self._is_combat_category(category)

                if is_combat:
                    if verbose:
                        self.stdout.write(self.style.HTTP_INFO('  → Type: COMBAT'))
                    result = self._process_combat_category(category, dry_run, verbose, force)
                    if result:
                        stats['combat_calculated'] += 1
                    else:
                        stats['combat_skipped'] += 1
                else:
                    if verbose:
                        self.stdout.write(self.style.HTTP_INFO('  → Type: TECHNIQUE'))
                    result = self._process_technical_category(category, dry_run, verbose, force)
                    if result:
                        stats['technical_calculated'] += 1
                    else:
                        stats['technical_skipped'] += 1

                # Générer le podium
                if result and not dry_run:
                    podium_result = self._generate_podium(category, verbose)
                    if podium_result:
                        stats['podiums_generated'] += 1

            except Exception as e:
                error_msg = f'{category.name}: {str(e)}'
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ✗ Erreur: {str(e)}'))

        # Afficher le résumé
        self._print_summary(stats, dry_run)

    def _is_combat_category(self, category):
        """Détermine si une catégorie est de type combat."""
        # Vérifier par le nom
        combat_keywords = ['combat', 'kumite', 'sparring', 'fighting', 'doi khang']
        name_lower = category.name.lower()
        if any(kw in name_lower for kw in combat_keywords):
            return True

        # Vérifier si des combats existent pour cette catégorie
        has_combats = Combat.objects.filter(poule__category=category).exists()
        if has_combats:
            return True

        # Vérifier si des poules existent
        has_poules = Poule.objects.filter(category=category).exists()
        if has_poules:
            return True

        return False

    def _process_technical_category(self, category, dry_run, verbose, force):
        """Traite une catégorie de type technique (kata, quyền, etc.)."""
        # Vérifier si des performances existent
        performances = TechnicalPerformance.objects.filter(
            category=category,
            status='completed'
        )

        perf_count = performances.count()
        if perf_count == 0:
            if verbose:
                self.stdout.write(self.style.WARNING('  → Aucune performance complétée'))
            return False

        if verbose:
            self.stdout.write(f'  → {perf_count} performances complétées')

        # Vérifier si des résultats existent déjà
        existing_rankings = CompetitionRanking.objects.filter(
            competition=category.competition,
            category=category
        ).exists()

        if existing_rankings and not force:
            if verbose:
                self.stdout.write(self.style.WARNING('  → Classement existant (utilisez --force pour recalculer)'))
            return False

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'  ✓ [DRY-RUN] Calculerait {perf_count} résultats'))
            return True

        # Calculer les résultats
        with transaction.atomic():
            # Supprimer les anciens classements si on force
            if force:
                CompetitionRanking.objects.filter(
                    competition=category.competition,
                    category=category
                ).delete()

            # Calculer les scores et créer les classements
            rankings = []
            for performance in performances:
                final_score = performance.calculate_final_score()
                if final_score is not None:
                    rankings.append({
                        'performance': performance,
                        'practitioner': performance.practitioner,
                        'score': final_score
                    })

            # Trier par score décroissant
            rankings.sort(key=lambda x: -x['score'])

            # Créer les entrées de classement
            current_rank = 0
            previous_score = None
            for i, ranking_data in enumerate(rankings):
                # Gérer les ex-aequo
                if ranking_data['score'] != previous_score:
                    current_rank = i + 1
                    previous_score = ranking_data['score']

                CompetitionRanking.objects.create(
                    competition=category.competition,
                    category=category,
                    practitioner=ranking_data['practitioner'],
                    rank=current_rank,
                    final_score=ranking_data['score'],
                    is_tie=(i > 0 and rankings[i-1]['score'] == ranking_data['score'])
                )

            self.stdout.write(self.style.SUCCESS(f'  ✓ {len(rankings)} classements créés'))
            return True

    def _process_combat_category(self, category, dry_run, verbose, force):
        """Traite une catégorie de type combat."""
        # Vérifier si des combats terminés existent
        combats = Combat.objects.filter(
            poule__category=category,
            status='termine'
        )

        combat_count = combats.count()
        if combat_count == 0:
            if verbose:
                self.stdout.write(self.style.WARNING('  → Aucun combat terminé'))
            return False

        if verbose:
            self.stdout.write(f'  → {combat_count} combats terminés')

        # Vérifier si un classement existe déjà
        existing_ranking = CategoryRanking.objects.filter(category=category).exists()

        if existing_ranking and not force:
            if verbose:
                self.stdout.write(self.style.WARNING('  → Classement existant (utilisez --force pour recalculer)'))
            return False

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'  ✓ [DRY-RUN] Calculerait les résultats de {combat_count} combats'))
            return True

        # Calculer les résultats via le service
        with transaction.atomic():
            # Supprimer l'ancien classement si on force
            if force:
                CategoryRanking.objects.filter(category=category).delete()

            # Obtenir les résultats via le service
            results = PodiumDisplayService.get_combat_category_results(category)

            if not results.get('all_results'):
                self.stdout.write(self.style.WARNING('  → Aucun résultat calculable'))
                return False

            # Créer le CategoryRanking
            ranking = CategoryRanking.objects.create(
                category=category,
                is_published=False,
                is_final=True,
                generated_at=timezone.now()
            )

            # Créer les RankingEntry pour chaque résultat
            for i, result in enumerate(results['all_results']):
                # Pour les combats en équipe, on n'a pas de practitioner directement
                # On stocke dans des notes ou on gère différemment
                if result.get('type') == 'team':
                    # Pour les équipes, on pourrait créer une entrée par membre
                    if verbose:
                        self.stdout.write(f'    → Équipe: {result["entity_name"]} - Rang {result.get("rank", i+1)}')
                else:
                    practitioner = result.get('practitioner')
                    if practitioner:
                        RankingEntry.objects.create(
                            ranking=ranking,
                            practitioner=practitioner,
                            rank=result.get('rank', i + 1),
                            score=result.get('total_score', 0),
                            is_tie=result.get('is_tie', False)
                        )

            self.stdout.write(self.style.SUCCESS(f'  ✓ Classement combat créé ({len(results["all_results"])} participants)'))
            return True

    def _generate_podium(self, category, verbose):
        """Génère le podium pour une catégorie."""
        try:
            # Obtenir le podium via la méthode existante
            podium = PodiumEntry.get_podium_for_category(category)

            gold_count = len(podium.get('gold', []))
            silver_count = len(podium.get('silver', []))
            bronze_count = len(podium.get('bronze', []))

            total = gold_count + silver_count + bronze_count

            if total > 0:
                if verbose:
                    self.stdout.write(f'  → Podium: 🥇 {gold_count} | 🥈 {silver_count} | 🥉 {bronze_count}')
                return True
            else:
                if verbose:
                    self.stdout.write(self.style.WARNING('  → Pas assez de données pour le podium'))
                return False

        except Exception as e:
            if verbose:
                self.stdout.write(self.style.WARNING(f'  → Erreur podium: {str(e)}'))
            return False

    def _print_summary(self, stats, dry_run):
        """Affiche le résumé des opérations."""
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'RÉSUMÉ\n'
            f'{"="*60}'
        ))

        mode = "[DRY-RUN] " if dry_run else ""

        self.stdout.write(f'\n{mode}Catégories TECHNIQUES:')
        self.stdout.write(f'  • Calculées: {stats["technical_calculated"]}')
        self.stdout.write(f'  • Ignorées: {stats["technical_skipped"]}')

        self.stdout.write(f'\n{mode}Catégories COMBAT:')
        self.stdout.write(f'  • Calculées: {stats["combat_calculated"]}')
        self.stdout.write(f'  • Ignorées: {stats["combat_skipped"]}')

        if not dry_run:
            self.stdout.write(f'\n{mode}Podiums générés: {stats["podiums_generated"]}')

        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'\nErreurs ({len(stats["errors"])}):'))
            for error in stats['errors']:
                self.stdout.write(self.style.ERROR(f'  • {error}'))

        total_processed = stats['technical_calculated'] + stats['combat_calculated']
        self.stdout.write(self.style.SUCCESS(f'\n✓ Total traité: {total_processed} catégories\n'))
