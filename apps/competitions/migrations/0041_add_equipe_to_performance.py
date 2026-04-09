from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0040_add_contact_submission_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='performance',
            name='equipe',
            field=models.ForeignKey(
                blank=True,
                help_text='Pour les compétitions en équipe: l\'équipe notée',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='performances_technique',
                to='competitions.equipe',
                verbose_name='Equipe',
            ),
        ),
    ]
