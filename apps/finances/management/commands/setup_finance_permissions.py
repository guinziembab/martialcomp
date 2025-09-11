from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.competitions.models.users import UserProfile


class Command(BaseCommand):
    help = 'Setup finance permissions for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to grant finance permissions to',
        )
        parser.add_argument(
            '--role',
            type=str,
            default='federation_admin',
            choices=['federation_admin', 'club_manager', 'coach'],
            help='Role to assign to the user (default: federation_admin)',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Apply role to all users without a role',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        role = options.get('role')
        all_users = options.get('all_users')

        if all_users:
            # Apply to all users without a role
            users_without_role = User.objects.filter(
                profile__isnull=True
            ) | User.objects.filter(
                profile__role__isnull=True
            ) | User.objects.filter(
                profile__role=''
            )
            
            count = 0
            for user in users_without_role:
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'âœ“ Set role "{role}" for user: {user.username}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nâœ… Updated {count} users with role "{role}"')
            )
            
        elif username:
            # Apply to specific user
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(user=user)
                old_role = profile.role
                profile.role = role
                profile.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'âœ… Updated user "{username}": {old_role or "No role"} â†’ {role}'
                    )
                )
                
                # Test permissions
                from apps.finances.utils import get_financial_permissions
                permissions = get_financial_permissions(user)
                
                self.stdout.write('\nðŸ“‹ Current finance permissions:')
                for perm, value in permissions.items():
                    status = 'âœ…' if value else 'âŒ'
                    self.stdout.write(f'  {status} {perm}: {value}')
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'âŒ User "{username}" not found')
                )
        else:
            self.stdout.write(
                self.style.ERROR('âŒ Please provide --username or --all-users')
            )
            
        # Show available commands
        self.stdout.write(
            self.style.WARNING(
                '\nðŸ’¡ Quick commands:\n'
                '  python3 manage.py setup_finance_permissions --username=admin --role=federation_admin\n'
                '  python3 manage.py setup_finance_permissions --all-users --role=coach\n'
            )
        )
