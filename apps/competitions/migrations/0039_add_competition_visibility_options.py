from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0038_practitioner_transfer'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='allow_online_registration',
            field=models.BooleanField(default=True, verbose_name='Autoriser les inscriptions en ligne'),
        ),
        migrations.AddField(
            model_name='competition',
            name='show_participants_list',
            field=models.BooleanField(default=False, verbose_name='Afficher la liste des participants'),
        ),
        migrations.AddField(
            model_name='competition',
            name='live_results',
            field=models.BooleanField(default=False, verbose_name='Résultats en temps réel'),
        ),
    ]
