# Generated migration for role validation workflow
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0001_initial'),
        ('organizations', '0011_add_organization_video_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmember',
            name='membership_status',
            field=models.CharField(
                choices=[
                    ('pending', 'En attente de validation'),
                    ('approved', 'Approuvé'),
                    ('rejected', 'Refusé')
                ],
                default='approved',
                help_text="Statut de validation du rôle par un administrateur",
                max_length=20,
                verbose_name='Statut de validation'
            ),
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_memberships',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Approuvé par'
            ),
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Approuvé le'
            ),
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='rejection_reason',
            field=models.TextField(
                blank=True,
                verbose_name='Motif de refus'
            ),
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='practitioner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='organization_roles',
                to='competitions.practitioner',
                verbose_name='Pratiquant associé'
            ),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(
                fields=['organization', 'membership_status'],
                name='org_member_status_idx'
            ),
        ),
    ]
