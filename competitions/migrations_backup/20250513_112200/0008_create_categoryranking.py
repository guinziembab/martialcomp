# Generated manually to create CategoryRanking model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0007_merge_20250513_1045'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryRanking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_published', models.BooleanField(default=False, help_text='Si True, le classement est visible par le public', verbose_name='Publié')),
                ('is_final', models.BooleanField(default=False, help_text="Si True, le classement est considéré comme définitif", verbose_name='Final')),
                ('generated_at', models.DateTimeField(auto_now=True, verbose_name='Généré le')),
                ('published_at', models.DateTimeField(blank=True, null=True, verbose_name='Publié le')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_rankings', to='competitions.competitioncategory', verbose_name='Catégorie')),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_rankings', to='competitions.competition', verbose_name='Compétition')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_rankings', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'Classement de catégorie',
                'verbose_name_plural': 'Classements de catégories',
                'unique_together': {('category', 'competition')},
            },
        ),
        migrations.CreateModel(
            name='RankingEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveSmallIntegerField(verbose_name='Rang')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Score')),
                ('is_tie', models.BooleanField(default=False, verbose_name='Ex-æquo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('performance', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ranking_entries', to='competitions.technicalperformanceresult', verbose_name='Performance')),
                ('practitioner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ranking_entries', to='competitions.practitioner', verbose_name='Pratiquant')),
                ('ranking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='competitions.categoryranking', verbose_name='Classement')),
            ],
            options={
                'verbose_name': 'Entrée de classement',
                'verbose_name_plural': 'Entrées de classement',
                'ordering': ['rank', '-score'],
                'unique_together': {('ranking', 'practitioner')},
            },
        ),
    ]