# Generated migration for team fusion feature
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0011_combat_configuration_enhanced'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipe',
            name='type_equipe',
            field=models.CharField(
                choices=[('mono_club', 'Mono-club'), ('multi_club', 'Multi-clubs (fusion)')],
                default='mono_club',
                max_length=20,
                verbose_name="Type d'equipe"
            ),
        ),
        migrations.AddField(
            model_name='equipe',
            name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('pending_fusion', 'Fusion en attente'), ('fusion_complete', 'Fusion completee')],
                default='active',
                max_length=20,
                verbose_name='Statut'
            ),
        ),
        migrations.AddField(
            model_name='equipe',
            name='clubs_partenaires',
            field=models.ManyToManyField(
                blank=True,
                related_name='equipes_partenaires',
                to='competitions.Club',
                verbose_name='Clubs partenaires'
            ),
        ),
        migrations.AddField(
            model_name='equipe',
            name='equipe_parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='equipes_fusionnees',
                to='competitions.equipe',
                verbose_name='Equipe parente (fusion)'
            ),
        ),
        migrations.AddField(
            model_name='equipe',
            name='min_membres',
            field=models.PositiveSmallIntegerField(default=3, verbose_name='Minimum de membres'),
        ),
        migrations.AddField(
            model_name='equipe',
            name='max_membres',
            field=models.PositiveSmallIntegerField(default=5, verbose_name='Maximum de membres'),
        ),
        migrations.AddField(
            model_name='equipe',
            name='demande_fusion_message',
            field=models.TextField(blank=True, verbose_name='Message de demande de fusion'),
        ),
        migrations.AddField(
            model_name='equipe',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),
        migrations.AlterField(
            model_name='equipe',
            name='club',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='equipes_combat',
                to='competitions.club',
                verbose_name='Club principal'
            ),
        ),
    ]
