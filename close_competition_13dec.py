#!/usr/bin/env python
"""
Script de clôture de compétition - À exécuter sur le serveur de production.
Usage: python manage.py shell < close_competition_13dec.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from apps.competitions.models import Competition, Combat, CompetitionResult, CompetitionCategory

# Trouver la compétition du 13 décembre (ajuster l'ID si nécessaire)
print("=" * 60)
print("CLOTURE DE COMPETITION - Script de correction")
print("=" * 60)

# Lister les compétitions récentes
competitions = Competition.objects.filter(
    start_date__gte='2024-12-01'
).order_by('-start_date')

print("\nCompétitions récentes:")
for c in competitions:
    print(f"  ID={c.id} | {c.title} | {c.start_date} | Status: {c.status}")

# Trouver la compétition de décembre en pending/ongoing
competition = Competition.objects.filter(
    start_date__month=12,
    start_date__year=2024,
    status__in=['pending', 'ongoing', 'published']
).order_by('-start_date').first()

if not competition:
    print("\nAucune compétition à clôturer trouvée.")
    sys.exit(0)

print(f"\n>>> Compétition à clôturer: {competition.title} (ID={competition.id})")
print(f"    Date: {competition.start_date}")
print(f"    Statut actuel: {competition.status}")

# Demander confirmation
confirm = input("\nConfirmer la clôture? (oui/non): ")
if confirm.lower() != 'oui':
    print("Annulé.")
    sys.exit(0)

with transaction.atomic():
    # 1. Marquer toutes les catégories comme terminées
    categories_updated = CompetitionCategory.objects.filter(
        competition=competition,
        is_completed=False
    ).update(is_completed=True)
    print(f"\n[1/4] {categories_updated} catégorie(s) marquée(s) comme terminée(s)")

    # 2. Terminer les combats en cours
    active_combats = Combat.objects.filter(
        competition=competition,
        status='en_cours'
    )
    combats_ended = 0
    for combat in active_combats:
        combat.status = 'termine'
        combat.est_nul = True
        combat.fin_combat = timezone.now()
        combat.save()
        combats_ended += 1
    print(f"[2/4] {combats_ended} combat(s) en cours terminé(s)")

    # 3. Générer les résultats depuis les combats
    combats = Combat.objects.filter(
        competition=competition,
        status='termine',
        type_combat='individuel'
    ).select_related('pratiquant_rouge', 'pratiquant_blanc')

    practitioner_stats = {}

    for combat in combats:
        # Stats pour le pratiquant rouge
        if combat.pratiquant_rouge:
            pid = combat.pratiquant_rouge.id
            if pid not in practitioner_stats:
                practitioner_stats[pid] = {
                    'practitioner': combat.pratiquant_rouge,
                    'combats': 0, 'victories': 0, 'defeats': 0, 'draws': 0,
                    'points_for': Decimal('0'), 'points_against': Decimal('0'),
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
                    'combats': 0, 'victories': 0, 'defeats': 0, 'draws': 0,
                    'points_for': Decimal('0'), 'points_against': Decimal('0'),
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

    # Créer les CompetitionResult
    results_created = 0
    for pid, stats in practitioner_stats.items():
        score = stats['points_for'] - stats['points_against']
        result, created = CompetitionResult.objects.update_or_create(
            competition=competition,
            practitioner=stats['practitioner'],
            category=None,
            defaults={
                'score': score,
                'date': competition.end_date or timezone.now().date(),
                'notes': f"Combats: {stats['combats']} | V: {stats['victories']} | D: {stats['defeats']} | N: {stats['draws']}"
            }
        )
        if created:
            results_created += 1

    print(f"[3/4] {results_created} résultat(s) créé(s) pour {len(practitioner_stats)} pratiquant(s)")

    # 4. Mettre à jour le statut
    competition.status = 'completed'
    competition.save(update_fields=['status'])
    print(f"[4/4] Statut mis à jour: {competition.status}")

print("\n" + "=" * 60)
print("CLOTURE TERMINEE AVEC SUCCES!")
print("=" * 60)
print(f"\nCompétition: {competition.title}")
print(f"Nouveau statut: {competition.status}")
print(f"Résultats générés: {results_created}")
print("\nLes pratiquants peuvent maintenant voir leurs résultats.")
