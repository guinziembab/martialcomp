"""
Migration: Add pricing_tier field to Organization model.
Part of the 2-tier pricing refactoring (Free / Premium).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0015_add_additional_roles_to_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='pricing_tier',
            field=models.CharField(
                blank=True,
                choices=[('mature', 'Marché mature'), ('emergent', 'Marché émergent')],
                default='mature',
                help_text='Déterminé automatiquement à partir du pays',
                max_length=10,
                verbose_name='Tier tarifaire',
            ),
        ),
    ]
