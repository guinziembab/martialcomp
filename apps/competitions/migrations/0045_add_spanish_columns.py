"""
Migration pour ajouter les colonnes de traduction espagnole (_es) aux modeles
Competition, Discipline, TutorialSection et Tutorial.
Note: Club a deja les colonnes _es depuis une migration precedente.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0044_add_italian_to_all_translated_models'),
    ]

    operations = [
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_es',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_es',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_es',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_es',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club: colonnes _es deja presentes (migration precedente)
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_es',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_es',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_es',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_es',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_es',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_es',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]
