from django.db import migrations


class Migration(migrations.Migration):
    """
    Migration pour renommer plusieurs modèles afin de résoudre des conflits de noms.
    Les modèles suivants sont renommés pour éviter des conflits avec technical_scoring.py:
    - TechnicalPerformance -> TechnicalPerformanceResult
    - TechnicalScore -> TechnicalScoreResult
    - JudgeSubmissionStatus -> JudgeSubmissionStatusResult
    """

    dependencies = [
        ('competitions', '0002_initial'),  # Assurez-vous que cela correspond à votre dernière migration
    ]

    operations = [
        migrations.RenameModel(
            old_name='TechnicalPerformance',
            new_name='TechnicalPerformanceResult',
        ),
        migrations.RenameModel(
            old_name='TechnicalScore',
            new_name='TechnicalScoreResult',
        ),
        migrations.RenameModel(
            old_name='JudgeSubmissionStatus',
            new_name='JudgeSubmissionStatusResult',
        ),
    ]