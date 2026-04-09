# Generated manually for theme colors
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_add_banner_gallery'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='primary_color',
            field=models.CharField(
                default='#8b5cf6',
                help_text='Code couleur hexadécimal (ex: #8b5cf6)',
                max_length=7,
                verbose_name='Couleur principale'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='secondary_color',
            field=models.CharField(
                default='#a78bfa',
                help_text='Code couleur hexadécimal (ex: #a78bfa)',
                max_length=7,
                verbose_name='Couleur secondaire'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='accent_color',
            field=models.CharField(
                default='#d4af37',
                help_text="Code couleur hexadécimal (ex: #d4af37)",
                max_length=7,
                verbose_name="Couleur d'accent"
            ),
        ),
    ]
