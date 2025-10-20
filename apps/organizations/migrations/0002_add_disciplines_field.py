# Generated manually to resolve circular dependency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='disciplines',
            field=models.ManyToManyField(blank=True, related_name='organization_list', to='competitions.discipline', verbose_name='Disciplines'),
        ),
    ]