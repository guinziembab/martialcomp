"""
Migration pour ajouter les colonnes de traduction italienne (_it) aux modeles
Competition et Discipline.
Note: Club a deja les colonnes _it, Tutorial les a depuis 0043.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0043_tutorial_italian_columns'),
    ]

    operations = [
        # =================================================================
        # Competition: title_it, description_it, venue_name_it, address_it
        # =================================================================
        migrations.AddField(
            model_name='competition',
            name='title_it',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_it',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_it',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # =================================================================
        # Discipline: name_it, description_it
        # =================================================================
        migrations.AddField(
            model_name='discipline',
            name='name_it',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
    ]
