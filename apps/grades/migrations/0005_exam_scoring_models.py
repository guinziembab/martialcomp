import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0036_default_organizational_roles'),
        ('grades', '0004_add_grade_alert_log_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamScoringModule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom du module')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scoring_modules', to='grades.gradeexam', verbose_name='Examen')),
                ('assigned_examiners', models.ManyToManyField(blank=True, related_name='exam_scoring_modules', to='competitions.practitioner', verbose_name='Examinateurs assignés')),
            ],
            options={
                'verbose_name': 'Module de notation',
                'verbose_name_plural': 'Modules de notation',
                'ordering': ['exam', 'order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ExamScoringCriterion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom du critère')),
                ('coefficient', models.DecimalField(decimal_places=2, default=1.0, max_digits=4, verbose_name='Coefficient')),
                ('max_score', models.DecimalField(decimal_places=1, default=10.0, max_digits=4, verbose_name='Score maximum')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='grades.examscoringmodule', verbose_name='Module')),
            ],
            options={
                'verbose_name': 'Critère de notation',
                'verbose_name_plural': 'Critères de notation',
                'ordering': ['module', 'order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ExamScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=1, max_digits=4, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Note')),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire')),
                ('scored_at', models.DateTimeField(auto_now=True, verbose_name='Noté le')),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_scores', to='grades.gradeexamregistration', verbose_name='Inscription')),
                ('criterion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='grades.examscoringcriterion', verbose_name='Critère')),
                ('examiner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_exam_scores', to='competitions.practitioner', verbose_name='Examinateur')),
            ],
            options={
                'verbose_name': "Note d'examen",
                'verbose_name_plural': "Notes d'examen",
                'ordering': ['registration', 'criterion'],
                'unique_together': {('registration', 'criterion', 'examiner')},
            },
        ),
    ]
