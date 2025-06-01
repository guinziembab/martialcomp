# Generated manually to fix related_name conflicts

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0003_rename_technical_performance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='technicalperformanceresult',
            name='practitioner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='technical_performance_results', to='competitions.practitioner', verbose_name='Pratiquant'),
        ),
        migrations.AlterField(
            model_name='technicalperformanceresult',
            name='competition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='technical_performance_results', to='competitions.competition', verbose_name='Compétition'),
        ),
        migrations.AlterField(
            model_name='technicalperformanceresult',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_results', to='competitions.competitioncategory', verbose_name='Catégorie'),
        ),
        migrations.AlterField(
            model_name='categoryranking',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_rankings', to='competitions.competitioncategory', verbose_name='Catégorie'),
        ),
        migrations.AlterField(
            model_name='categoryranking',
            name='competition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_rankings', to='competitions.competition', verbose_name='Compétition'),
        ),
    ]