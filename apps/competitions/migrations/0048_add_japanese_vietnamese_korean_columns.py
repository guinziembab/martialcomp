"""
Migration pour ajouter les colonnes de traduction japonaise (_ja),
vietnamienne (_vi) et coreenne (_ko) aux modeles Competition, Club (vi uniquement),
Discipline, TutorialSection et Tutorial.
Note: Club a deja les colonnes _ja et _ko depuis une migration precedente.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0047_add_arabic_chinese_columns'),
    ]

    operations = [
        # =====================================================================
        # JAPONAIS (_ja)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_ja',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_ja',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_ja',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_ja',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club _ja: deja present
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_ja',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_ja',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_ja',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_ja',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_ja',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_ja',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
        # =====================================================================
        # VIETNAMIEN (_vi) - Club inclus car pas de colonnes existantes
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_vi',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_vi',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_vi',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_vi',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club _vi: pas encore present, on le cree
        migrations.AddField(
            model_name='club',
            name='name_vi',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='club',
            name='description_vi',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='club',
            name='address_vi',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_vi',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_vi',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_vi',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_vi',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_vi',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_vi',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
        # =====================================================================
        # COREEN (_ko)
        # =====================================================================
        # Competition
        migrations.AddField(
            model_name='competition',
            name='title_ko',
            field=models.CharField(max_length=255, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='competition',
            name='description_ko',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='competition',
            name='venue_name_ko',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Lieu'),
        ),
        migrations.AddField(
            model_name='competition',
            name='address_ko',
            field=models.CharField(max_length=255, blank=True, null=True, verbose_name='Adresse'),
        ),
        # Club _ko: deja present
        # Discipline
        migrations.AddField(
            model_name='discipline',
            name='name_ko',
            field=models.CharField(max_length=100, null=True, verbose_name='Nom'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='description_ko',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        # TutorialSection
        migrations.AddField(
            model_name='tutorialsection',
            name='title_ko',
            field=models.CharField(max_length=200, null=True, verbose_name='Titre'),
        ),
        # Tutorial
        migrations.AddField(
            model_name='tutorial',
            name='title_ko',
            field=models.CharField(max_length=300, null=True, verbose_name='Titre'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='steps_ko',
            field=models.TextField(blank=True, null=True, verbose_name='Etapes (JSON)'),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='tip_ko',
            field=models.TextField(blank=True, null=True, verbose_name='Astuce'),
        ),
    ]
