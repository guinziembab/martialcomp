"""
Migration pour ajouter les colonnes de traduction pour les 7 langues restantes:
russe (_ru), norvegien (_no), hindi (_hi), swahili (_sw), amharique (_am),
zoulou (_zu), yoruba (_yo).
Note: Club a deja les colonnes pour no, hi, sw, am, zu, yo mais PAS ru.
"""
from django.db import migrations, models


def _competition_fields(lang):
    """Generate AddField operations for Competition model."""
    return [
        migrations.AddField(
            model_name='competition', name=f'title_{lang}',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition', name=f'description_{lang}',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition', name=f'venue_name_{lang}',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition', name=f'address_{lang}',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
    ]


def _club_fields(lang):
    """Generate AddField operations for Club model."""
    return [
        migrations.AddField(
            model_name='club', name=f'name_{lang}',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='club', name=f'description_{lang}',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='club', name=f'address_{lang}',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
    ]


def _discipline_fields(lang):
    """Generate AddField operations for Discipline model."""
    return [
        migrations.AddField(
            model_name='discipline', name=f'name_{lang}',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline', name=f'description_{lang}',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
    ]


def _tutorial_fields(lang):
    """Generate AddField operations for TutorialSection + Tutorial models."""
    return [
        migrations.AddField(
            model_name='tutorialsection', name=f'title_{lang}',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial', name=f'title_{lang}',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial', name=f'steps_{lang}',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial', name=f'tip_{lang}',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0048_add_japanese_vietnamese_korean_columns'),
    ]

    operations = []

    # Languages where Club already has columns (skip Club)
    for _lang in ('no', 'hi', 'sw', 'am', 'zu', 'yo'):
        operations += _competition_fields(_lang)
        # Club: colonnes deja presentes
        operations += _discipline_fields(_lang)
        operations += _tutorial_fields(_lang)

    # Russian: Club does NOT have columns yet
    operations += _competition_fields('ru')
    operations += _club_fields('ru')
    operations += _discipline_fields('ru')
    operations += _tutorial_fields('ru')
