from django.db import migrations, models
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClubQRCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('qr_type', models.CharField(choices=[('registration', 'Inscription directe'), ('activity', 'Suivi activité'), ('access', 'Accès rapide')], default='registration', max_length=20)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('qr_image', models.ImageField(blank=True, null=True, upload_to='qr_codes/clubs/')),
                ('qr_url', models.URLField(blank=True, max_length=500)),
                ('scan_count', models.PositiveIntegerField(default=0)),
                ('registration_count', models.PositiveIntegerField(default=0)),
                ('last_scan', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('club', models.ForeignKey(on_delete=models.CASCADE, related_name='qr_codes', to='competitions.club')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('club', 'qr_type')},
            },
        ),
        migrations.CreateModel(
            name='ClubQRScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('referrer', models.URLField(blank=True)),
                ('resulted_in_registration', models.BooleanField(default=False)),
                ('scanned_at', models.DateTimeField(auto_now_add=True)),
                ('qr_code', models.ForeignKey(on_delete=models.CASCADE, related_name='scans', to='competitions.clubqrcode')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='auth.user')),
                ('registration_user', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='qr_registrations', to='auth.user')),
            ],
            options={
                'ordering': ['-scanned_at'],
            },
        ),
    ]
