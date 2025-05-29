from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('multitenant', '0005_pricing_models'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TenantSubscription',
            new_name='LegacyTenantSubscription',
        ),
        migrations.AlterModelOptions(
            name='legacytenantsubscription',
            options={'ordering': ['-created_at'], 'verbose_name': 'Abonnement tenant (legacy)', 'verbose_name_plural': 'Abonnements tenant (legacy)'},
        ),
        migrations.AlterField(
            model_name='legacytenantsubscription',
            name='tenant',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='legacy_subscription', to='multitenant.tenant', verbose_name='Tenant'),
        ),
    ]