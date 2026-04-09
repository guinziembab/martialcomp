#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de nettoyage des données de test d'une compétition.

Efface :
- CompetitionRanking (classements/résultats)
- TechnicalScore (notes des juges)
- TechnicalPerformance (performances/passages)

NE touche PAS :
- La compétition elle-même
- Les catégories
- Les inscriptions (CompetitionRegistration)
- Les pratiquants

Usage:
    python manage.py shell < scripts/clean_test_competition_data.py

    Ou en production via SSH:
    ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && python manage.py shell < scripts/clean_test_competition_data.py"
"""

import os
import sys
import django

# Configuration Django si nécessaire
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

from django.db import transaction

# ============================================
# CONFIGURATION - MODIFIER L'ID DE LA COMPETITION
# ============================================
COMPETITION_ID = 4  # ID de la compétition de test à nettoyer
DRY_RUN = False     # True = simulation, False = suppression réelle
# ============================================

def clean_competition_data(competition_id, dry_run=True):
    """
    Nettoie toutes les données de notation/résultats d'une compétition.

    Args:
        competition_id: ID de la compétition
        dry_run: Si True, affiche ce qui serait supprimé sans supprimer
    """
    from apps.competitions.models import Competition
    from apps.competitions.models.technical_scoring import (
        CompetitionRanking, TechnicalPerformance, TechnicalScore
    )

    print("=" * 60)
    print("NETTOYAGE DES DONNEES DE TEST")
    print("=" * 60)
    print()

    # Vérifier que la compétition existe
    try:
        competition = Competition.objects.get(pk=competition_id)
        print(f"Competition: {competition.title} (ID: {competition_id})")
        print()
    except Competition.DoesNotExist:
        print(f"ERREUR: La compétition ID {competition_id} n'existe pas!")
        return

    # Compter les éléments à supprimer
    rankings_count = CompetitionRanking.objects.filter(
        competition_id=competition_id
    ).count()

    scores_count = TechnicalScore.objects.filter(
        performance__category__competition_id=competition_id
    ).count()

    performances_count = TechnicalPerformance.objects.filter(
        category__competition_id=competition_id
    ).count()

    print("Elements a supprimer:")
    print(f"  - CompetitionRanking (résultats/palmarès): {rankings_count}")
    print(f"  - TechnicalScore (notes des juges):       {scores_count}")
    print(f"  - TechnicalPerformance (passages):        {performances_count}")
    print()

    total = rankings_count + scores_count + performances_count

    if total == 0:
        print("Aucune donnée à supprimer. La compétition est déjà vide.")
        return

    if dry_run:
        print("MODE SIMULATION (dry_run=True)")
        print("Aucune donnée n'a été supprimée.")
        print()
        print("Pour supprimer réellement, modifiez DRY_RUN = False dans le script")
        return

    # Suppression réelle
    print("SUPPRESSION EN COURS...")
    print()

    with transaction.atomic():
        # 1. Supprimer les classements (résultats)
        deleted_rankings = CompetitionRanking.objects.filter(
            competition_id=competition_id
        ).delete()
        print(f"  OK CompetitionRanking supprimés: {deleted_rankings[0]}")

        # 2. Supprimer les scores (doit être fait avant les performances)
        deleted_scores = TechnicalScore.objects.filter(
            performance__category__competition_id=competition_id
        ).delete()
        print(f"  OK TechnicalScore supprimés: {deleted_scores[0]}")

        # 3. Supprimer les performances
        deleted_performances = TechnicalPerformance.objects.filter(
            category__competition_id=competition_id
        ).delete()
        print(f"  OK TechnicalPerformance supprimés: {deleted_performances[0]}")

    print()
    print("=" * 60)
    print("NETTOYAGE TERMINE")
    print("=" * 60)
    print()
    print("Les palmarès des pratiquants seront automatiquement")
    print("mis à jour (les médailles disparaîtront).")
    print()
    print("Les éléments conservés:")
    print("  - La compétition")
    print("  - Les catégories")
    print("  - Les inscriptions")
    print("  - Les pratiquants")


if __name__ == '__main__':
    clean_competition_data(COMPETITION_ID, dry_run=DRY_RUN)
else:
    # Exécuté via manage.py shell
    clean_competition_data(COMPETITION_ID, dry_run=DRY_RUN)
