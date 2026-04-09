"""
Migration pour les modèles TutorialSection et Tutorial
avec champs modeltranslation (fr, en)
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0041_add_equipe_to_performance'),
    ]

    operations = [
        migrations.CreateModel(
            name='TutorialSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('title_fr', models.CharField(max_length=200, null=True, verbose_name='Titre')),
                ('title_en', models.CharField(max_length=200, null=True, verbose_name='Titre')),
                ('icon', models.CharField(default='fa-book', help_text='Classe FontAwesome, ex: fa-user-plus', max_length=50, verbose_name='Icone FontAwesome')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
            ],
            options={
                'verbose_name': 'Section de tutoriel',
                'verbose_name_plural': 'Sections de tutoriels',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Tutorial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(verbose_name='Numero')),
                ('title', models.CharField(max_length=300, verbose_name='Titre')),
                ('title_fr', models.CharField(max_length=300, null=True, verbose_name='Titre')),
                ('title_en', models.CharField(max_length=300, null=True, verbose_name='Titre')),
                ('audience', models.CharField(choices=[('all', 'Tous'), ('admin', 'Administrateur'), ('club', 'Club'), ('federation', 'Federation'), ('practitioner', 'Pratiquant'), ('judge', 'Juge'), ('coach', 'Entraineur')], default='all', max_length=20, verbose_name='Public cible')),
                ('format', models.CharField(choices=[('video', 'Video'), ('guide', 'Guide pas a pas'), ('interactive', 'Interactif')], default='guide', max_length=20, verbose_name='Format')),
                ('duration', models.CharField(blank=True, default='3 min', max_length=20, verbose_name='Duree')),
                ('steps', models.TextField(blank=True, help_text='Liste JSON: ["Etape 1", "Etape 2", ...]', verbose_name='Etapes (JSON)')),
                ('steps_fr', models.TextField(blank=True, help_text='Liste JSON: ["Etape 1", "Etape 2", ...]', null=True, verbose_name='Etapes (JSON)')),
                ('steps_en', models.TextField(blank=True, help_text='Liste JSON: ["Etape 1", "Etape 2", ...]', null=True, verbose_name='Etapes (JSON)')),
                ('tip', models.TextField(blank=True, verbose_name='Astuce')),
                ('tip_fr', models.TextField(blank=True, null=True, verbose_name='Astuce')),
                ('tip_en', models.TextField(blank=True, null=True, verbose_name='Astuce')),
                ('youtube_url', models.URLField(blank=True, help_text='URL YouTube (ex: https://youtube.com/watch?v=...)', verbose_name='Lien YouTube')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutorials', to='competitions.tutorialsection', verbose_name='Section')),
            ],
            options={
                'verbose_name': 'Tutoriel',
                'verbose_name_plural': 'Tutoriels',
                'ordering': ['section__order', 'order', 'number'],
                'unique_together': {('section', 'number')},
            },
        ),
    ]
