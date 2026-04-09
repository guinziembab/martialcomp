"""
Migration de données pour les affiliations existantes.
Crée des saisons par défaut et des périodes d'affiliation pour les affiliations actives.
"""
from django.db import migrations
from django.utils import timezone
from datetime import date
from decimal import Decimal


def migrate_existing_affiliations(apps, schema_editor):
    """
    Pour chaque affiliation active existante:
    1. Créer une saison par défaut si nécessaire pour la fédération
    2. Créer une AffiliationPeriod correspondante
    3. Lier via current_period
    """
    Organization = apps.get_model('organizations', 'Organization')
    Affiliation = apps.get_model('organizations', 'Affiliation')
    SportSeason = apps.get_model('organizations', 'SportSeason')
    AffiliationPeriod = apps.get_model('organizations', 'AffiliationPeriod')

    # Récupérer toutes les affiliations actives
    active_affiliations = Affiliation.objects.filter(is_active=True)

    # Grouper par fédération (parent_organization)
    federations_with_affiliations = set(
        active_affiliations.values_list('parent_organization_id', flat=True)
    )

    # Déterminer les dates de la saison courante
    today = timezone.now().date()
    # Si on est entre septembre et décembre, la saison est année-année+1
    # Sinon la saison est année-1-année
    if today.month >= 9:
        season_start_year = today.year
        season_end_year = today.year + 1
    else:
        season_start_year = today.year - 1
        season_end_year = today.year

    season_name = f"{season_start_year}-{season_end_year}"
    season_start = date(season_start_year, 9, 1)
    season_end = date(season_end_year, 8, 31)

    # Créer une saison par défaut pour chaque fédération
    season_map = {}  # federation_id -> season
    for fed_id in federations_with_affiliations:
        if fed_id is None:
            continue

        # Vérifier que l'organisation existe toujours
        if not Organization.objects.filter(id=fed_id).exists():
            continue

        # Vérifier si une saison existe déjà pour cette fédération
        existing_season = SportSeason.objects.filter(
            organization_id=fed_id,
            name=season_name
        ).first()

        if existing_season:
            season_map[fed_id] = existing_season
        else:
            # Créer la saison
            season = SportSeason.objects.create(
                organization_id=fed_id,
                name=season_name,
                start_date=season_start,
                end_date=season_end,
                renewal_reminder_days=30,
                is_current=True
            )
            season_map[fed_id] = season

    # Créer une AffiliationPeriod pour chaque affiliation active
    for affiliation in active_affiliations:
        if affiliation.parent_organization_id not in season_map:
            continue

        season = season_map[affiliation.parent_organization_id]

        # Vérifier si une période existe déjà
        existing_period = AffiliationPeriod.objects.filter(
            affiliation=affiliation,
            season=season
        ).first()

        if existing_period:
            # Mettre à jour current_period si nécessaire
            if affiliation.current_period_id != existing_period.id:
                affiliation.current_period = existing_period
                affiliation.save(update_fields=['current_period'])
            continue

        # Créer la période d'affiliation
        period = AffiliationPeriod.objects.create(
            affiliation=affiliation,
            season=season,
            status='active',  # Déjà active puisque l'affiliation est active
            amount=Decimal('0.00'),  # Montant inconnu pour les anciennes
            paid_amount=Decimal('0.00'),
            notes="Migration automatique depuis affiliations existantes"
        )

        # Lier la période à l'affiliation
        affiliation.current_period = period
        affiliation.save(update_fields=['current_period'])


def reverse_migration(apps, schema_editor):
    """
    Annule la migration en supprimant les périodes et saisons créées automatiquement.
    """
    AffiliationPeriod = apps.get_model('organizations', 'AffiliationPeriod')
    SportSeason = apps.get_model('organizations', 'SportSeason')
    Affiliation = apps.get_model('organizations', 'Affiliation')

    # Réinitialiser les current_period
    Affiliation.objects.filter(current_period__isnull=False).update(current_period=None)

    # Supprimer les périodes créées par la migration
    AffiliationPeriod.objects.filter(
        notes="Migration automatique depuis affiliations existantes"
    ).delete()

    # Note: On ne supprime pas les saisons car elles pourraient avoir été
    # modifiées ou utilisées pour d'autres données


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0008_seasonal_affiliations'),
    ]

    operations = [
        migrations.RunPython(
            migrate_existing_affiliations,
            reverse_code=reverse_migration
        ),
    ]
