# Generated migration for adding practitioner field to Transaction

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),
        ('finances', '0006_add_currency_to_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='practitioner',
            field=models.ForeignKey(
                blank=True,
                help_text='Pratiquant/membre du club associé à cette transaction',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions',
                to='competitions.practitioner',
                verbose_name='Membre associé'
            ),
        ),
    ]
