# Generated manually for streaming feature
# Migration: 0031_add_streaming_fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0030_add_eventoccurrence_missing_fields'),
    ]

    operations = [
        # =========================================================================
        # CHAMPS DE CONFIGURATION DU STREAMING
        # =========================================================================

        migrations.AddField(
            model_name='competition',
            name='stream_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Streaming activé',
                help_text='Activer l\'intégration du streaming pour cette compétition'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_platform',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                choices=[
                    ('youtube', 'YouTube'),
                    ('twitch', 'Twitch'),
                    ('facebook', 'Facebook Live'),
                    ('vimeo', 'Vimeo'),
                    ('dailymotion', 'Dailymotion'),
                    ('custom', 'URL personnalisée'),
                ],
                verbose_name='Plateforme de streaming',
                help_text='Sélectionner la plateforme utilisée pour le streaming'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_url',
            field=models.URLField(
                max_length=500,
                blank=True,
                null=True,
                verbose_name='URL du stream',
                help_text='URL complète du stream (ex: https://youtube.com/watch?v=xxxxx)'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_embed_url',
            field=models.URLField(
                max_length=500,
                blank=True,
                null=True,
                verbose_name='URL d\'intégration',
                help_text='URL d\'embed générée automatiquement'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_chat_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Chat du stream activé',
                help_text='Afficher le chat de la plateforme à côté du stream'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_chat_url',
            field=models.URLField(
                max_length=500,
                blank=True,
                null=True,
                verbose_name='URL du chat',
                help_text='URL d\'intégration du chat (optionnel)'
            ),
        ),

        # =========================================================================
        # CHAMPS D'ÉTAT DU STREAM
        # =========================================================================

        migrations.AddField(
            model_name='competition',
            name='is_live',
            field=models.BooleanField(
                default=False,
                verbose_name='En direct',
                help_text='Indique si le stream est actuellement en direct'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_started_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Début du stream'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_ended_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Fin du stream'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_viewer_count',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Nombre de spectateurs'
            ),
        ),

        # =========================================================================
        # CHAMPS REPLAY/ARCHIVE
        # =========================================================================

        migrations.AddField(
            model_name='competition',
            name='stream_replay_url',
            field=models.URLField(
                max_length=500,
                blank=True,
                null=True,
                verbose_name='URL du replay',
                help_text='URL de la vidéo enregistrée après la fin du stream'
            ),
        ),

        migrations.AddField(
            model_name='competition',
            name='stream_replay_available',
            field=models.BooleanField(
                default=False,
                verbose_name='Replay disponible'
            ),
        ),
    ]
