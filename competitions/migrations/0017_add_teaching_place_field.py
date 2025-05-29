# Generated manually
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0016_alter_coachachievement_achievement_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachprofile',
            name='teaching_place',
            field=models.CharField(
                blank=True, 
                default='',
                help_text='Nom de votre club, dojo ou lieu d\'enseignement principal',
                max_length=200, 
                verbose_name='Lieu d\'enseignement principal'
            ),
        ),
    ]
