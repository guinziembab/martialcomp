# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0022_add_offline_qr_support'),
    ]

    operations = [
        migrations.AddField(
            model_name='practitionerqrcode',
            name='offline_profile_token',
            field=models.TextField(blank=True, null=True, verbose_name='Token de profil hors-ligne'),
        ),
        migrations.AddField(
            model_name='practitionerqrcode',
            name='offline_profile_generated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de génération du profil hors-ligne'),
        ),
        migrations.AddField(
            model_name='practitionerqrcode',
            name='offline_profile_qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/practitioners/profile/', verbose_name='Image QR Code du profil hors-ligne'),
        ),
    ]