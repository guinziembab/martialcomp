# Generated manually for PostgreSQL production - add is_training_score field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0004_practitioner_family_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='technicalscoreresult',
            name='is_training_score',
            field=models.BooleanField(
                default=False, 
                help_text='Si True, le score est donné par un juge en formation et ne compte pas dans le résultat', 
                verbose_name="Score d'entraînement"
            ),
        ),
    ]