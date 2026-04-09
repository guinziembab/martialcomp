# Generated manually for OrganizationVideoLink model
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0010_add_metadata_to_organization'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationVideoLink',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('youtube_url', models.URLField(
                    help_text='URL complète de la vidéo YouTube',
                    verbose_name='URL YouTube'
                )),
                ('title', models.CharField(
                    help_text='Titre de la vidéo',
                    max_length=255,
                    verbose_name='Titre'
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Description de la vidéo',
                    verbose_name='Description'
                )),
                ('thumbnail_url', models.URLField(
                    blank=True,
                    help_text='Générée automatiquement depuis YouTube',
                    verbose_name='URL de la miniature'
                )),
                ('video_id', models.CharField(
                    blank=True,
                    help_text="Extrait automatiquement de l'URL",
                    max_length=20,
                    verbose_name='ID YouTube'
                )),
                ('order', models.PositiveIntegerField(
                    default=0,
                    verbose_name="Ordre d'affichage"
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    verbose_name='Active'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Mis à jour le'
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='video_links',
                    to='organizations.organization',
                    verbose_name='Organisation'
                )),
            ],
            options={
                'verbose_name': 'Lien vidéo',
                'verbose_name_plural': 'Liens vidéos',
                'ordering': ['order', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='organizationvideolink',
            index=models.Index(
                fields=['organization', 'order'],
                name='organizatio_organiz_video_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='organizationvideolink',
            index=models.Index(
                fields=['organization', 'is_active'],
                name='organizatio_organiz_active_idx'
            ),
        ),
    ]
