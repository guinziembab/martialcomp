# -*- coding: utf-8 -*-
# Generated manually for adding archive fields to Event model

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0027_organizationqrcode_organizationqrcodescan_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Archivé'),
        ),
        migrations.AddField(
            model_name='event',
            name='archived_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Archivé le'),
        ),
    ]
