# Generated manually for seasonal affiliations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0007_add_bilateral_affiliation_fields'),
        ('finances', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Create SportSeason model
        migrations.CreateModel(
            name='SportSeason',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('name', models.CharField(
                    help_text='Ex: 2024-2025',
                    max_length=20,
                    verbose_name='Nom de la saison'
                )),
                ('start_date', models.DateField(verbose_name='Date de début')),
                ('end_date', models.DateField(verbose_name='Date de fin')),
                ('renewal_reminder_days', models.PositiveIntegerField(
                    default=30,
                    help_text='Nombre de jours avant la fin de saison pour envoyer les rappels de renouvellement',
                    verbose_name='Jours avant rappel'
                )),
                ('is_current', models.BooleanField(
                    default=False,
                    help_text='Marquer comme saison active',
                    verbose_name='Saison courante'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Mis à jour le'
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seasons',
                    to='organizations.organization',
                    verbose_name='Organisation'
                )),
            ],
            options={
                'verbose_name': 'Saison sportive',
                'verbose_name_plural': 'Saisons sportives',
                'ordering': ['-start_date'],
            },
        ),
        migrations.AddIndex(
            model_name='sportseason',
            index=models.Index(
                fields=['organization', 'is_current'],
                name='organizatio_organiz_season_curr_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='sportseason',
            index=models.Index(
                fields=['start_date', 'end_date'],
                name='organizatio_start_end_date_idx'
            ),
        ),
        migrations.AddConstraint(
            model_name='sportseason',
            constraint=models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_organization_season'
            ),
        ),

        # 2. Create AffiliationFeeConfiguration model
        migrations.CreateModel(
            name='AffiliationFeeConfiguration',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('affiliation_type', models.CharField(
                    choices=[
                        ('member', 'Membre'),
                        ('partner', 'Partenaire'),
                        ('technical', 'Affiliation technique'),
                        ('administrative', 'Affiliation administrative')
                    ],
                    max_length=30,
                    verbose_name="Type d'affiliation"
                )),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text="Montant HT de l'affiliation",
                    max_digits=10,
                    verbose_name='Montant'
                )),
                ('tax_rate', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    help_text='Taux de TVA en pourcentage (ex: 20.00)',
                    max_digits=5,
                    verbose_name='Taux de TVA'
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Description des avantages inclus',
                    verbose_name='Description'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    verbose_name='Actif'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Mis à jour le'
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='affiliation_fees',
                    to='organizations.organization',
                    verbose_name='Organisation'
                )),
                ('season', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fee_configurations',
                    to='organizations.sportseason',
                    verbose_name='Saison'
                )),
            ],
            options={
                'verbose_name': 'Configuration tarif affiliation',
                'verbose_name_plural': 'Configurations tarifs affiliation',
                'ordering': ['season', 'affiliation_type'],
            },
        ),
        migrations.AddConstraint(
            model_name='affiliationfeeconfiguration',
            constraint=models.UniqueConstraint(
                fields=['organization', 'season', 'affiliation_type'],
                name='unique_org_season_affiliation_type'
            ),
        ),

        # 3. Create AffiliationPeriod model
        migrations.CreateModel(
            name='AffiliationPeriod',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending_payment', 'En attente de paiement'),
                        ('active', 'Active'),
                        ('expired', 'Expirée'),
                        ('cancelled', 'Annulée')
                    ],
                    default='pending_payment',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text="Montant de l'affiliation pour cette période",
                    max_digits=10,
                    verbose_name='Montant'
                )),
                ('paid_amount', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=10,
                    verbose_name='Montant payé'
                )),
                ('payment_date', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Date de paiement'
                )),
                ('notes', models.TextField(
                    blank=True,
                    verbose_name='Notes'
                )),
                ('last_reminder_sent', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Dernier rappel envoyé',
                    help_text='Date du dernier rappel de renouvellement envoyé'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Mis à jour le'
                )),
                ('affiliation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='periods',
                    to='organizations.affiliation',
                    verbose_name='Affiliation'
                )),
                ('season', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='affiliation_periods',
                    to='organizations.sportseason',
                    verbose_name='Saison'
                )),
                ('invoice', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='affiliation_periods',
                    to='finances.invoice',
                    verbose_name='Facture'
                )),
                ('renewed_from', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='renewals',
                    to='organizations.affiliationperiod',
                    verbose_name='Renouvelé depuis'
                )),
            ],
            options={
                'verbose_name': "Période d'affiliation",
                'verbose_name_plural': "Périodes d'affiliation",
                'ordering': ['-season__start_date'],
            },
        ),
        migrations.AddIndex(
            model_name='affiliationperiod',
            index=models.Index(
                fields=['affiliation', 'status'],
                name='organizatio_affil_period_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='affiliationperiod',
            index=models.Index(
                fields=['season', 'status'],
                name='organizatio_season_status_idx'
            ),
        ),
        migrations.AddConstraint(
            model_name='affiliationperiod',
            constraint=models.UniqueConstraint(
                fields=['affiliation', 'season'],
                name='unique_affiliation_season'
            ),
        ),

        # 4. Create AffiliationRenewalRequest model
        migrations.CreateModel(
            name='AffiliationRenewalRequest',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('requested_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Demandé le'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente'),
                        ('approved', 'Approuvée'),
                        ('rejected', 'Refusée')
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('processed_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Traité le'
                )),
                ('rejection_reason', models.TextField(
                    blank=True,
                    verbose_name='Motif de refus'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Mis à jour le'
                )),
                ('affiliation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='renewal_requests',
                    to='organizations.affiliation',
                    verbose_name='Affiliation'
                )),
                ('from_period', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='renewal_requests_from',
                    to='organizations.affiliationperiod',
                    verbose_name='Période précédente'
                )),
                ('to_season', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='renewal_requests',
                    to='organizations.sportseason',
                    verbose_name='Nouvelle saison'
                )),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='affiliation_renewal_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Demandé par'
                )),
                ('processed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='processed_renewal_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Traité par'
                )),
                ('created_period', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_from_request',
                    to='organizations.affiliationperiod',
                    verbose_name='Période créée'
                )),
            ],
            options={
                'verbose_name': 'Demande de renouvellement',
                'verbose_name_plural': 'Demandes de renouvellement',
                'ordering': ['-requested_at'],
            },
        ),
        migrations.AddIndex(
            model_name='affiliationrenewalrequest',
            index=models.Index(
                fields=['affiliation', 'status'],
                name='organizatio_renewal_req_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='affiliationrenewalrequest',
            index=models.Index(
                fields=['to_season', 'status'],
                name='organizatio_to_season_status_idx'
            ),
        ),

        # 5. Add current_period field to Affiliation
        migrations.AddField(
            model_name='affiliation',
            name='current_period',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='organizations.affiliationperiod',
                verbose_name='Période courante'
            ),
        ),
    ]
