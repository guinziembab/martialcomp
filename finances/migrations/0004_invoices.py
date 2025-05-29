from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finances', '0003_payments'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('number', models.CharField(blank=True, max_length=50, unique=True, verbose_name='Numéro de facture')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('issued_date', models.DateField(default=django.utils.timezone.now, verbose_name="Date d'émission")),
                ('due_date', models.DateField(verbose_name="Date d'échéance")),
                ('paid_date', models.DateField(blank=True, null=True, verbose_name='Date de paiement')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Sous-total HT')),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant TVA')),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Total TTC')),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant payé')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('status', models.CharField(choices=[('draft', 'Brouillon'), ('issued', 'Émise'), ('paid', 'Payée'), ('partially_paid', 'Partiellement payée'), ('overdue', 'En retard'), ('cancelled', 'Annulée')], default='draft', max_length=20, verbose_name='Statut')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('terms', models.TextField(blank=True, verbose_name='Conditions')),
                ('issuer_object_id', models.CharField(max_length=50, verbose_name="ID de l'émetteur")),
                ('recipient_object_id', models.CharField(max_length=50, verbose_name='ID du destinataire')),
                ('related_object_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'entité liée")),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='finances/invoices/%Y/%m/', verbose_name='Fichier PDF')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_invoices', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('issuer_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issued_invoices', to='contenttypes.contenttype', verbose_name="Type d'émetteur")),
                ('recipient_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_invoices', to='contenttypes.contenttype', verbose_name='Type de destinataire')),
                ('related_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_invoices', to='contenttypes.contenttype', verbose_name="Type d'entité liée")),
            ],
            options={
                'verbose_name': 'Facture',
                'verbose_name_plural': 'Factures',
                'ordering': ['-issued_date', '-number'],
                'indexes': [models.Index(fields=['status'], name='finances_in_status_9f76e8_idx'), models.Index(fields=['issued_date'], name='finances_in_issued__5c6290_idx'), models.Index(fields=['due_date'], name='finances_in_due_dat_6c5923_idx')],
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=255, verbose_name='Description')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Quantité')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix unitaire HT')),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Taux de TVA (%)')),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant TVA')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Sous-total HT')),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Total TTC')),
                ('reference', models.CharField(blank=True, max_length=50, verbose_name='Référence')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('item_object_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'élément")),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.accountingcategory', verbose_name='Catégorie comptable')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='finances.invoice', verbose_name='Facture')),
                ('item_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype', verbose_name="Type d'élément")),
            ],
            options={
                'verbose_name': 'Élément de facture',
                'verbose_name_plural': 'Éléments de facture',
                'ordering': ['order', 'id'],
            },
        ),
    ]