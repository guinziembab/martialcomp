"""
Migration pour ajouter les colonnes de traduction italienne aux modeles Tutorial
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0042_tutorial_models'),
    ]

    operations = [
        # TutorialSection: title_it
        migrations.AddField(
            model_name='tutorialsection',
            name='title_it',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial: title_it, steps_it, tip_it
        migrations.AddField(
            model_name='tutorial',
            name='title_it',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_it',
            field=models.TextField(blank=True, null=True, help_text='Liste JSON: ["Etape 1", "Etape 2", ...]', verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_it',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]
