from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0021_alter_coachprofile_teaching_place_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='practitionerqrcode',
            name='offline_token',
            field=models.TextField(blank=True, null=True, verbose_name='Token hors-ligne'),
        ),
        migrations.AddField(
            model_name='practitionerqrcode',
            name='offline_token_generated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de génération du token hors-ligne'),
        ),
        migrations.AddField(
            model_name='practitionerqrcode',
            name='qr_offline_image',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/practitioners/offline/', verbose_name='Image QR Code (hors-ligne)'),
        ),
        migrations.AddField(
            model_name='qrcodescan',
            name='is_offline_scan',
            field=models.BooleanField(default=False, verbose_name='Scan effectué hors-ligne'),
        ),
        migrations.AddField(
            model_name='qrcodescan',
            name='offline_scan_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ID du scan hors-ligne'),
        ),
        migrations.AddField(
            model_name='qrcodescan',
            name='synced_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de synchronisation'),
        ),
    ]