# Generated migration file

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0010_competitionresult'),
        ('multitenant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='is_migrated',
            field=models.BooleanField(default=False, verbose_name='Migré vers multi-tenant'),
        ),
        migrations.AddField(
            model_name='club',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='original_clubs',
                to='multitenant.tenant',
                verbose_name='Tenant'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='migration_date',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Date de migration'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='country',
            field=models.CharField(
                blank=True,
                default='FR',
                max_length=2,
                verbose_name='Code pays'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='timezone',
            field=models.CharField(
                blank=True,
                default='Europe/Paris',
                max_length=50,
                verbose_name='Fuseau horaire'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='currency',
            field=models.CharField(
                blank=True,
                default='EUR',
                max_length=3,
                verbose_name='Devise'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='email',
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name='Email principal'
            ),
        ),
        migrations.AddField(
            model_name='club',
            name='phone',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='Téléphone principal'
            ),
        ),
    ]