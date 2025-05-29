from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('finances', '0001_accounts'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipFee',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('organization_id', models.CharField(max_length=50, verbose_name="ID de l'organisation")),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('period', models.CharField(choices=[('yearly', 'Annuelle'), ('seasonal', 'Saisonnière'), ('semester', 'Semestrielle'), ('quarterly', 'Trimestrielle'), ('monthly', 'Mensuelle'), ('one_time', 'Unique')], default='yearly', max_length=20, verbose_name='Période')),
                ('start_date', models.DateField(verbose_name='Date de début')),
                ('end_date', models.DateField(verbose_name='Date de fin')),
                ('grace_period_days', models.PositiveIntegerField(default=30, verbose_name='Période de grâce (jours)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_prorated', models.BooleanField(default=False, verbose_name='Au prorata')),
                ('member_type', models.CharField(blank=True, max_length=50, verbose_name='Type de membre')),
                ('age_min', models.PositiveIntegerField(blank=True, null=True, verbose_name='Âge minimum')),
                ('age_max', models.PositiveIntegerField(blank=True, null=True, verbose_name='Âge maximum')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('accounting_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.accountingcategory', verbose_name='Catégorie comptable')),
                ('organization_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name="Type d'organisation")),
            ],
            options={
                'verbose_name': 'Cotisation',
                'verbose_name_plural': 'Cotisations',
                'ordering': ['name'],
                'indexes': [models.Index(fields=['is_active'], name='finances_me_is_acti_3ba9d9_idx'), models.Index(fields=['start_date'], name='finances_me_start_d_6c2a6e_idx'), models.Index(fields=['end_date'], name='finances_me_end_dat_c647b3_idx')],
            },
        ),
    ]