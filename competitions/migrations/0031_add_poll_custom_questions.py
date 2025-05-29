# Generated manually for custom poll questions
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0030_alter_event_options_alter_eventparticipant_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PollQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question_text', models.CharField(max_length=500, verbose_name='Question')),
                ('question_type', models.CharField(choices=[('text', 'Texte libre'), ('choice', 'Choix multiple'), ('rating', 'Notation (1-5)'), ('yes_no', 'Oui/Non'), ('date', 'Date'), ('time', 'Heure'), ('number', 'Nombre')], default='text', max_length=20, verbose_name='Type de question')),
                ('choices', models.JSONField(blank=True, default=list, help_text='Liste des options pour les questions à choix multiple', verbose_name='Choix disponibles')),
                ('is_required', models.BooleanField(default=False, verbose_name='Obligatoire')),
                ('order', models.PositiveIntegerField(default=1, verbose_name='Ordre')),
                ('help_text', models.CharField(blank=True, max_length=200, verbose_name="Texte d'aide")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_questions', to='competitions.eventpoll', verbose_name='Sondage')),
            ],
            options={
                'verbose_name': 'Question personnalisée',
                'verbose_name_plural': 'Questions personnalisées',
                'ordering': ['order', 'created_at'],
                'unique_together': {('poll', 'order')},
            },
        ),
        migrations.CreateModel(
            name='PollQuestionResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('response_text', models.TextField(blank=True, verbose_name='Réponse texte')),
                ('response_number', models.FloatField(blank=True, null=True, verbose_name='Réponse numérique')),
                ('response_date', models.DateField(blank=True, null=True, verbose_name='Réponse date')),
                ('response_time', models.TimeField(blank=True, null=True, verbose_name='Réponse heure')),
                ('response_choice', models.CharField(blank=True, max_length=200, verbose_name='Choix sélectionné')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_question_responses', to='auth.user', verbose_name='Utilisateur')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='competitions.pollquestion', verbose_name='Question')),
            ],
            options={
                'verbose_name': 'Réponse à une question',
                'verbose_name_plural': 'Réponses aux questions',
                'ordering': ['-created_at'],
                'unique_together': {('question', 'user')},
            },
        ),
    ]