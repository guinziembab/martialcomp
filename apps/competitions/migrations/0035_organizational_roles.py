# Generated migration for organizational roles system
# Social Auth and Organizational Roles implementation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0034_add_absence_declaration'),
    ]

    operations = [
        # Create OrganizationalRole model
        migrations.CreateModel(
            name='OrganizationalRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Code')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('permissions', models.JSONField(default=list, verbose_name='Permissions')),
                ('hierarchy_level', models.PositiveIntegerField(default=0, help_text='Niveau hiérarchique (0 = le plus haut)', verbose_name='Niveau hiérarchique')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Rôle organisationnel',
                'verbose_name_plural': 'Rôles organisationnels',
                'ordering': ['hierarchy_level', 'name'],
            },
        ),
        # Create ClubMember model
        migrations.CreateModel(
            name='ClubMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('active', 'Actif'), ('suspended', 'Suspendu'), ('inactive', 'Inactif')], default='active', max_length=20, verbose_name='Statut')),
                ('custom_permissions', models.JSONField(blank=True, default=list, help_text='Permissions supplémentaires spécifiques à ce membre', verbose_name='Permissions personnalisées')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='Date adhésion')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('additional_roles', models.ManyToManyField(blank=True, related_name='additional_club_members', to='competitions.organizationalrole', verbose_name='Rôles additionnels')),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='club_role_assignments_made', to=settings.AUTH_USER_MODEL, verbose_name='Assigné par')),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_members', to='competitions.club', verbose_name='Club')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='club_members', to='competitions.organizationalrole', verbose_name='Rôle')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='club_memberships', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Membre du club',
                'verbose_name_plural': 'Membres du club',
                'ordering': ['-joined_at'],
                'unique_together': {('user', 'club')},
            },
        ),
        # Create FederationMember model
        migrations.CreateModel(
            name='FederationMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('active', 'Actif'), ('suspended', 'Suspendu'), ('inactive', 'Inactif')], default='active', max_length=20, verbose_name='Statut')),
                ('custom_permissions', models.JSONField(blank=True, default=list, help_text='Permissions supplémentaires spécifiques', verbose_name='Permissions personnalisées')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='Date adhésion')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('additional_roles', models.ManyToManyField(blank=True, related_name='additional_federation_members', to='competitions.organizationalrole', verbose_name='Rôles additionnels')),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='federation_role_assignments_made', to=settings.AUTH_USER_MODEL, verbose_name='Assigné par')),
                ('federation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_members', to='competitions.federation', verbose_name='Fédération')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='federation_members', to='competitions.organizationalrole', verbose_name='Rôle')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='federation_memberships', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Membre de la fédération',
                'verbose_name_plural': 'Membres de la fédération',
                'ordering': ['-joined_at'],
                'unique_together': {('user', 'federation')},
            },
        ),
        # Create MemberRoleHistory model
        migrations.CreateModel(
            name='MemberRoleHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('assigned', 'Assigné'), ('removed', 'Retiré'), ('modified', 'Modifié')], max_length=20, verbose_name='Action')),
                ('old_role', models.CharField(blank=True, max_length=100, null=True, verbose_name='Ancien rôle')),
                ('new_role', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nouveau rôle')),
                ('reason', models.TextField(blank=True, verbose_name='Raison')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='role_changes_made', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
                ('club_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='role_history', to='competitions.clubmember', verbose_name='Membre club')),
                ('federation_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='role_history', to='competitions.federationmember', verbose_name='Membre fédération')),
            ],
            options={
                'verbose_name': 'Historique des rôles',
                'verbose_name_plural': 'Historiques des rôles',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for performance
        migrations.AddIndex(
            model_name='clubmember',
            index=models.Index(fields=['user', 'club', 'status'], name='club_member_user_club_idx'),
        ),
        migrations.AddIndex(
            model_name='federationmember',
            index=models.Index(fields=['user', 'federation', 'status'], name='fed_member_user_fed_idx'),
        ),
    ]
