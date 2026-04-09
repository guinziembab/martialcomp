#!/usr/bin/env python
"""
Script pour marquer comme "Terminé" toutes les performances qui ont été notées.

Exécuter sur le serveur de production:
    cd /var/www/vhosts/martialcomp.com/httpdocs
    source /var/www/vhosts/martialcomp.com/venv/bin/activate
    export DJANGO_SETTINGS_MODULE=config.settings.production
    python scripts/mark_scored_performances_completed.py
"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.db.models import Count
from django.utils import timezone


def mark_scored_performances_completed():
    """
    Marque toutes les performances qui ont au moins un score comme 'completed'.
    """
    from apps.competitions.models.technical_scoring import Performance, Score

    print("=" * 60)
    print("MISE À JOUR DES STATUTS DES PERFORMANCES")
    print("=" * 60)
    print()

    # Récupérer les performances qui ont des scores mais ne sont pas encore "completed"
    performances_with_scores = Performance.objects.annotate(
        score_count=Count('scores')
    ).filter(
        score_count__gt=0
    ).exclude(
        status='completed'
    )

    total_to_update = performances_with_scores.count()
    print(f"Performances avec scores mais pas 'completed': {total_to_update}")

    if total_to_update == 0:
        print("Aucune performance à mettre à jour.")
        return

    # Afficher un aperçu avant mise à jour
    print()
    print("Aperçu des performances à mettre à jour:")
    print("-" * 60)

    by_status = {}
    for perf in performances_with_scores[:20]:  # Limiter l'aperçu
        status = perf.status
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1

    for status, count in by_status.items():
        print(f"  - Statut '{status}': {count} performances")

    if total_to_update > 20:
        print(f"  ... et {total_to_update - 20} autres")

    print()

    # Demander confirmation
    response = input(f"Voulez-vous mettre à jour {total_to_update} performances en 'completed'? (oui/non): ")

    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Opération annulée.")
        return

    # Mise à jour en masse
    updated = performances_with_scores.update(
        status='completed',
        completion_time=timezone.now()
    )

    print()
    print(f"✓ {updated} performances mises à jour en 'completed'")
    print()

    # Statistiques finales
    print("Statistiques finales:")
    print("-" * 60)

    total_performances = Performance.objects.count()
    completed = Performance.objects.filter(status='completed').count()
    scheduled = Performance.objects.filter(status='scheduled').count()

    print(f"  - Total performances: {total_performances}")
    print(f"  - Terminées (completed): {completed}")
    print(f"  - Programmées (scheduled): {scheduled}")

    print()
    print("=" * 60)
    print("TERMINÉ")
    print("=" * 60)


def mark_scored_performances_completed_auto():
    """
    Version automatique sans confirmation (pour scripts).
    """
    from apps.competitions.models.technical_scoring import Performance
    from django.db.models import Count

    performances_with_scores = Performance.objects.annotate(
        score_count=Count('scores')
    ).filter(
        score_count__gt=0
    ).exclude(
        status='completed'
    )

    updated = performances_with_scores.update(
        status='completed',
        completion_time=timezone.now()
    )

    print(f"✓ {updated} performances mises à jour en 'completed'")
    return updated


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Marquer les performances notées comme terminées')
    parser.add_argument('--auto', action='store_true', help='Mode automatique sans confirmation')
    args = parser.parse_args()

    if args.auto:
        mark_scored_performances_completed_auto()
    else:
        mark_scored_performances_completed()
