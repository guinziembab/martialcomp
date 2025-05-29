# Generated manually to add only missing customization fields

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('multitenant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='tenants/logos/', verbose_name='Logo'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='primary_color',
            field=models.CharField(default='#007bff', max_length=7, validators=[django.core.validators.RegexValidator(message='Entrez une couleur hexadécimale valide', regex='^#(?:[0-9a-fA-F]{3}){1,2}$')], verbose_name='Couleur principale'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='secondary_color',
            field=models.CharField(default='#6c757d', max_length=7, validators=[django.core.validators.RegexValidator(message='Entrez une couleur hexadécimale valide', regex='^#(?:[0-9a-fA-F]{3}){1,2}$')], verbose_name='Couleur secondaire'),
        ),
    ]
