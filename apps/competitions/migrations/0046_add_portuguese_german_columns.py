"""
Migration pour ajouter les colonnes de traduction portugaise (_pt) et
allemande (_de) aux modeles Competition, Discipline, TutorialSection et Tutorial.
Note: Club a deja les colonnes _pt et _de depuis une migration precedente.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0045_add_spanish_columns'),
    ]

    operations = [
        # =====================================================================
        # PORTUGAIS (_pt)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_pt',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_pt',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_pt',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_pt',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club: colonnes _pt deja presentes (migration precedente)
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_pt',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_pt',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_pt',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_pt',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_pt',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_pt',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
        # =====================================================================
        # ALLEMAND (_de)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_de',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_de',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_de',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_de',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club: colonnes _de deja presentes (migration precedente)
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_de',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_de',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_de',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_de',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_de',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_de',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]
