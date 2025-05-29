"""
Commande Django pour planifier des audits de sécurité réguliers avec Celery beat.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Planifie des audits de sécurité réguliers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--frequency',
            choices=['daily', 'weekly', 'monthly'],
            default='weekly',
            help='Fréquence des audits (par défaut: hebdomadaire)',
        )
        parser.add_argument(
            '--hour',
            type=int,
            default=2,
            help='Heure d\'exécution (par défaut: 2h du matin)',
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='ID du tenant spécifique à auditer (laisser vide pour audit global)',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Désactiver les audits planifiés',
        )

    def handle(self, *args, **options):
        frequency = options['frequency']
        hour = options['hour']
        tenant_id = options.get('tenant')
        disable = options.get('disable', False)
        
        task_name = f"security_audit_{frequency}"
        if tenant_id:
            task_name += f"_tenant_{tenant_id}"
        
        # Si on veut désactiver
        if disable:
            try:
                task = PeriodicTask.objects.get(name=task_name)
                task.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Audits planifiés désactivés: {task_name}")
                )
            except PeriodicTask.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Aucune tâche planifiée trouvée: {task_name}")
                )
            return
        
        # Créer le planning selon la fréquence
        if frequency == 'daily':
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour=str(hour),
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            schedule_desc = f"Tous les jours à {hour}h00"
        elif frequency == 'weekly':
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour=str(hour),
                day_of_week='1',  # Lundi
                day_of_month='*',
                month_of_year='*',
            )
            schedule_desc = f"Tous les lundis à {hour}h00"
        else:  # monthly
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour=str(hour),
                day_of_week='*',
                day_of_month='1',  # Premier jour du mois
                month_of_year='*',
            )
            schedule_desc = f"Le 1er de chaque mois à {hour}h00"
        
        # Créer ou mettre à jour la tâche périodique
        task_kwargs = {
            'tenant_id': tenant_id
        } if tenant_id else {}
        
        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'multitenant.tasks.security_tasks.run_scheduled_security_audit',
                'crontab': schedule,
                'args': json.dumps([]),
                'kwargs': json.dumps(task_kwargs),
                'enabled': True,
                'description': f"Audit de sécurité {frequency} {'pour tenant ' + tenant_id if tenant_id else 'global'}",
            }
        )
        
        action = "créée" if created else "mise à jour"
        self.stdout.write(
            self.style.SUCCESS(
                f"Tâche d'audit {action}: {task_name}\n"
                f"Fréquence: {schedule_desc}\n"
                f"Type: {'Tenant spécifique' if tenant_id else 'Global'}"
            )
        )
        
        # Créer également une tâche de nettoyage mensuelle
        cleanup_task_name = "security_audit_cleanup"
        cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='1',
            month_of_year='*',
        )
        
        cleanup_task, cleanup_created = PeriodicTask.objects.update_or_create(
            name=cleanup_task_name,
            defaults={
                'task': 'multitenant.tasks.security_tasks.cleanup_old_security_reports',
                'crontab': cleanup_schedule,
                'args': json.dumps([30]),  # Garder 30 jours
                'kwargs': json.dumps({}),
                'enabled': True,
                'description': 'Nettoyage mensuel des anciens rapports de sécurité',
            }
        )
        
        if cleanup_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Tâche de nettoyage créée: {cleanup_task_name} (mensuelle)"
                )
            )