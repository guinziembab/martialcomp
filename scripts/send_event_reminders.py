#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour envoyer les rappels d'événements.
À exécuter via une tâche cron ou un job scheduler.

Exemple d'utilisation avec cron :
*/15 * * * * /path/to/venv/bin/python /path/to/martialcomp/scripts/send_event_reminders.py

Cela exécutera le script toutes les 15 minutes.
"""

import os
import sys
import django
import logging
import argparse
from datetime import datetime

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs/reminders.log'))
    ]
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path pour importer les modules Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importer les fonctions du service de rappel
from competitions.services.event_reminder_service import send_due_reminders, send_specific_reminder

def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(description='Envoie les rappels d\'événements.')
    parser.add_argument('--reminder-id', type=str, help='ID d\'un rappel spécifique à envoyer')
    parser.add_argument('--dry-run', action='store_true', help='Exécuter sans envoyer réellement les rappels')
    
    args = parser.parse_args()
    
    logger.info(f"Démarrage du script d'envoi de rappels à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        if args.reminder_id:
            # Envoyer un rappel spécifique
            logger.info(f"Envoi du rappel spécifique {args.reminder_id}")
            
            if args.dry_run:
                logger.info("Mode dry-run: les rappels ne seront pas réellement envoyés")
                from competitions.models.event import EventReminder
                try:
                    reminder = EventReminder.objects.get(id=args.reminder_id)
                    recipients = reminder.get_recipient_list()
                    logger.info(f"Le rappel {args.reminder_id} serait envoyé à {recipients.count()} destinataires")
                except Exception as e:
                    logger.error(f"Erreur lors de la vérification du rappel: {str(e)}")
            else:
                result = send_specific_reminder(args.reminder_id)
                if result['success']:
                    logger.info(f"Rappel {args.reminder_id} envoyé avec succès")
                else:
                    logger.error(f"Échec de l'envoi du rappel {args.reminder_id}: {result['message']}")
        else:
            # Envoyer tous les rappels dus
            logger.info("Envoi de tous les rappels dus")
            
            if args.dry_run:
                logger.info("Mode dry-run: les rappels ne seront pas réellement envoyés")
                from competitions.services.event_reminder_service import ReminderService
                reminders = ReminderService.get_due_reminders()
                logger.info(f"{reminders.count()} rappels seraient envoyés")
                for reminder in reminders:
                    recipients = reminder.get_recipient_list()
                    logger.info(f"- Rappel {reminder.id} ({reminder.title}) pour l'événement {reminder.event.title}: {recipients.count()} destinataires")
            else:
                results = send_due_reminders()
                logger.info(f"Résultats: {results['successful']} succès, {results['failed']} échecs sur {results['total']} rappels")
                
                # Journaliser les détails des échecs pour diagnostic
                if results['failed'] > 0:
                    for detail in results['details']:
                        if not detail['success']:
                            logger.error(f"Échec du rappel {detail['reminder_id']} pour l'événement {detail['event_title']}: {detail['message']}")
        
        logger.info(f"Script terminé à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du script: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())