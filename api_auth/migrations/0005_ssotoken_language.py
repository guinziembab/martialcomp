from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_auth', '0004_ssotoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='ssotoken',
            name='language',
            field=models.CharField(
                blank=True,
                help_text='Code langue sélectionné dans l\'app mobile (ex: fr, en, de)',
                max_length=10,
                null=True,
                verbose_name='Langue',
            ),
        ),
    ]
