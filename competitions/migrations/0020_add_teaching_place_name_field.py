# Generated manually for teaching_place_name
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0019_remove_coachprofile_teaching_place_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachprofile',
            name='teaching_place_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Nom de votre club, dojo ou lieu d\'enseignement principal',
                max_length=200,
                verbose_name='Lieu ou club d\'enseignement'
            ),
        ),
    ]
