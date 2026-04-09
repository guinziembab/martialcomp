# Generated migration for adding category and description fields to Poule

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0023_add_is_completed_to_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='poule',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='poules',
                to='competitions.competitioncategory',
                verbose_name='Catégorie'
            ),
        ),
        migrations.AddField(
            model_name='poule',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description'),
        ),
        migrations.AlterModelOptions(
            name='poule',
            options={'ordering': ['competition', 'category', 'phase', 'numero'], 'verbose_name': 'Poule', 'verbose_name_plural': 'Poules'},
        ),
        migrations.AlterUniqueTogether(
            name='poule',
            unique_together=set(),
        ),
    ]
