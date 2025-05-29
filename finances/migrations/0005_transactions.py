from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finances', '0004_invoices'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('transaction_type', models.CharField(choices=[('income', 'Revenu'), ('expense', 'Dépense'), ('both', 'Les deux')], default='both', max_length=20, verbose_name='Type applicable')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='finances.transactioncategory', verbose_name='Catégorie parente')),
            ],
            options={
                'verbose_name': 'Catégorie de transaction',
                'verbose_name_plural': 'Catégories de transactions',
                'ordering': ['name'],
                'indexes': [models.Index(fields=['transaction_type'], name='finances_tr_transac_efd903_idx'), models.Index(fields=['active'], name='finances_tr_active_89ccbf_idx')],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reference', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('type', models.CharField(choices=[('income', 'Revenu'), ('expense', 'Dépense')], max_length=20, verbose_name='Type')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Date de la transaction')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('date_validated', models.DateTimeField(blank=True, null=True, verbose_name='Date de validation')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('validated', 'Validée'), ('rejected', 'Rejetée'), ('refunded', 'Remboursée'), ('cancelled', 'Annulée')], default='pending', max_length=20, verbose_name='Statut')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('source_object_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'entité source")),
                ('destination_object_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'entité destination")),
                ('receipt_file', models.FileField(blank=True, null=True, upload_to='finances/receipts/%Y/%m/', verbose_name='Reçu')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.transactioncategory', verbose_name='Catégorie')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('destination_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='destination_transactions', to='contenttypes.contenttype', verbose_name="Type d'entité destination")),
                ('financial_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='finances.financialaccount', verbose_name='Compte financier')),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.invoice', verbose_name='Facture associée')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.paymentmethod', verbose_name='Méthode de paiement')),
                ('source_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_transactions', to='contenttypes.contenttype', verbose_name="Type d'entité source")),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Mis à jour par')),
                ('validated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validated_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Validé par')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-date_created'],
                'indexes': [models.Index(fields=['status'], name='finances_tr_status_1a98cd_idx'), models.Index(fields=['type'], name='finances_tr_type_52095b_idx'), models.Index(fields=['date_created'], name='finances_tr_date_cr_86bb08_idx')],
            },
        ),
        migrations.CreateModel(
            name='TransactionAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='finances/attachments/%Y/%m/', verbose_name='Fichier')),
                ('filename', models.CharField(max_length=255, verbose_name='Nom du fichier')),
                ('file_type', models.CharField(blank=True, max_length=50, verbose_name='Type de fichier')),
                ('file_size', models.PositiveIntegerField(default=0, verbose_name='Taille du fichier')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Description')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de téléchargement')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='finances.transaction', verbose_name='Transaction')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_attachments', to=settings.AUTH_USER_MODEL, verbose_name='Téléchargé par')),
            ],
            options={
                'verbose_name': 'Pièce jointe de transaction',
                'verbose_name_plural': 'Pièces jointes de transactions',
                'ordering': ['-uploaded_at'],
            },
        ),
        # Add transaction field to PaymentAttempt model
        migrations.AddField(
            model_name='paymentattempt',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_attempts', to='finances.transaction', verbose_name='Transaction'),
        ),
    ]