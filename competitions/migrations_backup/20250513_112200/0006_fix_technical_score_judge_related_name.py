# Generated manually to fix judge related_name conflict

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0005_migrate_technical_performance_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='technicalscoreresult',
            name='judge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='technical_score_results', to='auth.user', verbose_name='Juge'),
        ),
        migrations.AlterField(
            model_name='technicalscoreresult',
            name='criterion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_results', to='competitions.scoringcriterion', verbose_name='Critère'),
        ),
        migrations.AlterField(
            model_name='judgesubmissionstatusresult',
            name='judge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submission_status_results', to='auth.user', verbose_name='Juge'),
        ),
        migrations.AlterField(
            model_name='technicalscoreresult',
            name='performance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='technical_scores', to='competitions.technicalperformanceresult', verbose_name='Performance'),
        ),
    ]