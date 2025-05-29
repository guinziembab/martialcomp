from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('finances', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountingCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('type', models.CharField(choices=[('income', 'Revenu'), ('expense', 'Dépense')], max_length=20, verbose_name='Type')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('code', models.CharField(blank=True, max_length=20, verbose_name='Code comptable')),
                ('organization_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'organisation")),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_system', models.BooleanField(default=False, verbose_name='Catégorie système')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('organization_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name="Type d'organisation")),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategories', to='finances.accountingcategory', verbose_name='Catégorie parente')),
            ],
            options={
                'verbose_name': 'Catégorie comptable',
                'verbose_name_plural': 'Catégories comptables',
                'ordering': ['name'],
                'indexes': [models.Index(fields=['type'], name='finances_ac_type_7a4cbc_idx'), models.Index(fields=['is_active'], name='finances_ac_is_acti_7f9a8a_idx')],
            },
        ),
        migrations.CreateModel(
            name='FinancialAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('type', models.CharField(choices=[('checking', 'Compte courant'), ('savings', "Compte d'épargne"), ('cash', 'Caisse'), ('credit', 'Carte de crédit'), ('other', 'Autre')], max_length=20, verbose_name='Type')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('opening_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Solde d'ouverture")),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Solde actuel')),
                ('reconciled_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Solde rapproché')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('last_reconciled', models.DateTimeField(blank=True, null=True, verbose_name='Dernière réconciliation')),
                ('owner_id', models.CharField(max_length=50, verbose_name='ID du propriétaire')),
                ('bank_name', models.CharField(blank=True, max_length=100, verbose_name='Nom de la banque')),
                ('account_number', models.CharField(blank=True, max_length=50, verbose_name='Numéro de compte')),
                ('iban', models.CharField(blank=True, max_length=34, verbose_name='IBAN')),
                ('bic', models.CharField(blank=True, max_length=11, verbose_name='BIC/SWIFT')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_default', models.BooleanField(default=False, verbose_name='Compte par défaut')),
                ('owner_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Type de propriétaire')),
            ],
            options={
                'verbose_name': 'Compte financier',
                'verbose_name_plural': 'Comptes financiers',
                'ordering': ['-is_default', 'name'],
                'indexes': [models.Index(fields=['is_active'], name='finances_fi_is_acti_5bfb32_idx'), models.Index(fields=['is_default'], name='finances_fi_is_defa_9ab08b_idx')],
            },
        ),
    ]