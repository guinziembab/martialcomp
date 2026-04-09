"""
Migration pour ajouter les colonnes de traduction arabe (_ar) et
chinoise (_zh) aux modeles Competition, Discipline, TutorialSection et Tutorial.
Note: Club a deja les colonnes _ar et _zh depuis une migration precedente.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0046_add_portuguese_german_columns'),
    ]

    operations = [
        # =====================================================================
        # ARABE (_ar)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_ar',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_ar',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_ar',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_ar',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club: colonnes _ar deja presentes (migration precedente)
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_ar',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_ar',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_ar',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_ar',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_ar',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_ar',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
        # =====================================================================
        # CHINOIS (_zh)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_zh',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_zh',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_zh',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_zh',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club: colonnes _zh deja presentes (migration precedente)
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_zh',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_zh',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_zh',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_zh',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_zh',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_zh',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]
