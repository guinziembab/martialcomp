from django.db import migrations

class Migration(migrations.Migration):
    """
    Cette migration corrige les incohérences entre les tables SQL créées avec RunSQL
    et les modèles Django pour le système de notation autonome.
    """

    dependencies = [
        ('competitions', '0005_combat_actioncombat_combatconfiguration_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL - Renomme la table avec le nom correct pour le snapshot
            """
            -- Rename StandaloneRankingSnapshotEntry table to match Django model
            ALTER TABLE IF EXISTS competitions_standalonerankingnapshotentry 
            RENAME TO competitions_standalonerankingsnapshotentry;
            """,
            
            # Reverse SQL - Revient au nom original
            """
            ALTER TABLE IF EXISTS competitions_standalonerankingsnapshotentry 
            RENAME TO competitions_standalonerankingnapshotentry;
            """
        ),
        migrations.RunSQL(
            # Forward SQL - Utilisé uniquement pour indiquer que la migration est terminée
            """
            -- Migration completed successfully
            SELECT 1;
            """,
            
            # Reverse SQL - Rien à faire en cas d'annulation
            """
            SELECT 1;
            """
        ),
    ]