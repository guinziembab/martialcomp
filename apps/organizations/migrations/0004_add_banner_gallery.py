# Generated migration for banner and gallery
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_alter_organization_updated_at'),
    ]

    operations = [
        # Ajouter le champ banner à Organization
        migrations.AddField(
            model_name='organization',
            name='banner',
            field=models.ImageField(
                blank=True,
                help_text='Dimensions recommandées: 1920x600px. Max 3 Mo.',
                null=True,
                upload_to='organizations/banners/',
                verbose_name='Bannière'
            ),
        ),

        # Créer le modèle OrganizationGalleryImage
        migrations.CreateModel(
            name='OrganizationGalleryImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(
                    help_text='Formats acceptés: JPG, PNG, WebP. Max 2 Mo.',
                    upload_to='organizations/gallery/',
                    verbose_name='Image'
                )),
                ('description', models.CharField(
                    blank=True,
                    help_text='Description courte de l\'image',
                    max_length=255,
                    verbose_name='Description'
                )),
                ('alt_text', models.CharField(
                    blank=True,
                    help_text='Pour l\'accessibilité',
                    max_length=255,
                    verbose_name='Texte alternatif'
                )),
                ('order', models.PositiveIntegerField(
                    default=0,
                    verbose_name='Ordre d\'affichage'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gallery_images',
                    to='organizations.organization',
                    verbose_name='Organisation'
                )),
            ],
            options={
                'verbose_name': 'Image de galerie',
                'verbose_name_plural': 'Images de galerie',
                'ordering': ['order', 'created_at'],
            },
        ),

        # Ajouter l'index pour les performances
        migrations.AddIndex(
            model_name='organizationgalleryimage',
            index=models.Index(fields=['organization', 'order'], name='organizatio_organiz_idx'),
        ),
    ]
