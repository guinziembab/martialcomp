from django.core.management.base import BaseCommand
from apps.competitions.models.notifications import Notification
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Nettoie les notifications expirées et anciennes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours après lesquels supprimer les notifications lues (défaut: 30)'
        )
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Supprimer seulement les notifications expirées'
        )

    def handle(self, *args, **options):
        """Nettoie les notifications expirées et anciennes"""
        
        self.stdout.write(self.style.SUCCESS("ðŸ§¹ NETTOYAGE DES NOTIFICATIONS"))
        self.stdout.write("=" * 50)
        
        # Statistiques avant nettoyage
        total_before = Notification.objects.count()
        expired_before = Notification.objects.filter(expires_at__lt=timezone.now()).count()
        old_read_before = Notification.objects.filter(
            is_read=True,
            created_at__lt=timezone.now() - timedelta(days=options['days'])
        ).count()
        
        self.stdout.write(f"ðŸ“Š AVANT NETTOYAGE:")
        self.stdout.write(f"   Total notifications: {total_before}")
        self.stdout.write(f"   Notifications expirées: {expired_before}")
        self.stdout.write(f"   Notifications lues anciennes (> {options['days']} jours): {old_read_before}")
        
        deleted_count = 0
        
        # Supprimer les notifications expirées
        if options['expired_only']:
            expired_notifications = Notification.objects.filter(expires_at__lt=timezone.now())
            deleted_expired = expired_notifications.count()
            expired_notifications.delete()
            deleted_count += deleted_expired
            self.stdout.write(f"âœ… {deleted_expired} notifications expirées supprimées")
        else:
            # Supprimer les notifications expirées
            expired_notifications = Notification.objects.filter(expires_at__lt=timezone.now())
            deleted_expired = expired_notifications.count()
            expired_notifications.delete()
            deleted_count += deleted_expired
            self.stdout.write(f"âœ… {deleted_expired} notifications expirées supprimées")
            
            # Supprimer les notifications lues anciennes
            old_read_notifications = Notification.objects.filter(
                is_read=True,
                created_at__lt=timezone.now() - timedelta(days=options['days'])
            )
            deleted_old_read = old_read_notifications.count()
            old_read_notifications.delete()
            deleted_count += deleted_old_read
            self.stdout.write(f"âœ… {deleted_old_read} notifications lues anciennes supprimées")
        
        # Statistiques après nettoyage
        total_after = Notification.objects.count()
        unread_after = Notification.objects.filter(is_read=False).count()
        
        self.stdout.write(f"\nðŸ“Š APRÃˆS NETTOYAGE:")
        self.stdout.write(f"   Total notifications: {total_after}")
        self.stdout.write(f"   Notifications non lues: {unread_after}")
        self.stdout.write(f"   Notifications supprimées: {deleted_count}")
        
        if deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(f"\nâœ… Nettoyage terminé avec succès!"))
            self.stdout.write(f"ðŸ§¹ {deleted_count} notifications supprimées")
        else:
            self.stdout.write(self.style.WARNING(f"\nâš ï¸ Aucune notification Ã  supprimer"))
        
        self.stdout.write("ðŸ”” Le système de notifications est maintenant optimisé.") 

