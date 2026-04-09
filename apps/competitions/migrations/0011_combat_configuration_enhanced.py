"""
Migration pour améliorer la configuration des combats
"""
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0010_standalonecategoryrankingsnapshot_and_more'),
    ]

    operations = [
        # Ajouter des champs pour mieux paramétrer les combats
        migrations.AddField(
            model_name='combatconfiguration',
            name='labels_points',
            field=models.JSONField(
                verbose_name='Labels des points',
                default=dict,
                help_text='Labels pour chaque valeur de point (ex: {"1": "Technique simple", "2": "Technique complexe"})'
            ),
        ),
        migrations.AddField(
            model_name='combatconfiguration',
            name='labels_penalites',
            field=models.JSONField(
                verbose_name='Labels des pénalités',
                default=dict,
                help_text='Labels pour chaque pénalité (ex: {"-0.5": "Avertissement", "-1": "Faute"})'
            ),
        ),
        migrations.AddField(
            model_name='combatconfiguration',
            name='cumul_points_equipe',
            field=models.BooleanField(
                verbose_name='Cumul des points en équipe',
                default=True,
                help_text='Si activé, les points des membres sont cumulés pour le score équipe'
            ),
        ),
        migrations.AddField(
            model_name='combatconfiguration',
            name='nb_combattants_equipe',
            field=models.PositiveSmallIntegerField(
                verbose_name='Nombre de combattants par équipe',
                default=1,
                help_text='1 pour individuel, 2-5 pour équipes'
            ),
        ),
        migrations.AddField(
            model_name='combatconfiguration',
            name='afficher_nom_equipe',
            field=models.BooleanField(
                verbose_name='Afficher le nom des équipes',
                default=True
            ),
        ),
        migrations.AddField(
            model_name='combatconfiguration',
            name='couleurs_interface',
            field=models.JSONField(
                verbose_name='Couleurs de l\'interface',
                default=dict,
                help_text='Personnalisation des couleurs (ex: {"rouge": "#DC3545", "blanc": "#F8F9FA"})'
            ),
        ),
        
        # Améliorer Combat pour mieux gérer les équipes
        migrations.AddField(
            model_name='combat',
            name='score_cumul_rouge',
            field=models.DecimalField(
                verbose_name='Score cumulé rouge',
                max_digits=6,
                decimal_places=2,
                default=0,
                help_text='Score total cumulé pour l\'équipe rouge'
            ),
        ),
        migrations.AddField(
            model_name='combat',
            name='score_cumul_blanc',
            field=models.DecimalField(
                verbose_name='Score cumulé blanc',
                max_digits=6,
                decimal_places=2,
                default=0,
                help_text='Score total cumulé pour l\'équipe blanche'
            ),
        ),
    ]