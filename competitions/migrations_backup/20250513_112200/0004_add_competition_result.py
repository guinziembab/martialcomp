from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):
    """
    Migration pour ajouter le modèle CompetitionResult.
    """

    dependencies = [
        ('competitions', '0003_rename_technical_performance'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetitionResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Classement')),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Score')),
                ('medal', models.CharField(blank=True, choices=[('gold', 'Or'), ('silver', 'Argent'), ('bronze', 'Bronze'), ('none', 'Aucune')], default='none', max_length=20, verbose_name='Médaille')),
                ('date', models.DateField(default=timezone.now, verbose_name='Date')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results', to='competitions.competitioncategory', verbose_name='Catégorie')),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='competitions.competition', verbose_name='Compétition')),
                ('practitioner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competition_results', to='competitions.practitioner', verbose_name='Pratiquant')),
            ],
            options={
                'verbose_name': 'Résultat de compétition',
                'verbose_name_plural': 'Résultats de compétition',
                'ordering': ['competition', 'category', 'rank'],
                'unique_together': {('competition', 'category', 'practitioner')},
            },
        ),
    ]