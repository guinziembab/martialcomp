# Generated migration for SSOToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api_auth', '0003_add_missing_tenant_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSOToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=128, unique=True, verbose_name='Token SSO')),
                ('redirect_url', models.CharField(blank=True, max_length=500, null=True, verbose_name='URL de redirection')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('expires_at', models.DateTimeField(verbose_name="Date d'expiration")),
                ('used', models.BooleanField(default=False, verbose_name='Utilisé')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name="Date d'utilisation")),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='User Agent')),
                ('tenant', models.CharField(blank=True, help_text='Le tenant auquel ce token SSO est associé', max_length=100, null=True, verbose_name='Tenant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sso_tokens', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Token SSO',
                'verbose_name_plural': 'Tokens SSO',
                'ordering': ['-created_at'],
            },
        ),
    ]
