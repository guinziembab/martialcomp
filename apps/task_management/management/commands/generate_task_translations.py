"""
Commande de gestion Django pour générer les fichiers de traduction pour la gestion des tâches
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
import os
import json


class Command(BaseCommand):
    help = 'Génère les fichiers de traduction pour le module de gestion des tâches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lang',
            type=str,
            default='en',
            help='Code de langue pour la traduction (par défaut: en)'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'po'],
            default='json',
            help='Format de sortie (json ou po)'
        )

    def handle(self, *args, **options):
        lang_code = options['lang']
        output_format = options['format']
        
        # Dictionnaire des traductions français -> langue cible
        translations = {
            # Interface utilisateur de base
            'Gestion de Tâches': 'Task Management',
            'Accueil': 'Home',
            'Tableau de bord': 'Dashboard',
            'Mes Tableaux Kanban': 'My Kanban Boards',
            'Gérez vos projets et tâches avec des tableaux Kanban collaboratifs': 'Manage your projects and tasks with collaborative Kanban boards',
            'Nouveau Tableau': 'New Board',
            'Créer un tableau': 'Create Board',
            
            # Actions
            'Rechercher...': 'Search...',
            'Filtrer': 'Filter',
            'Modifier': 'Edit',
            'Supprimer': 'Delete',
            'Archiver': 'Archive',
            'Désarchiver': 'Unarchive',
            'Confirmer': 'Confirm',
            'Annuler': 'Cancel',
            'Enregistrer': 'Save',
            'Fermer': 'Close',
            'Chargement...': 'Loading...',
            'Erreur': 'Error',
            'Succès': 'Success',
            
            # Navigation et pagination
            'Plus récents': 'Most Recent',
            'Plus anciens': 'Oldest',
            'Nom (A-Z)': 'Name (A-Z)',
            'Nom (Z-A)': 'Name (Z-A)',
            'Plus de tâches': 'More Tasks',
            'Première': 'First',
            'Précédente': 'Previous', 
            'Suivante': 'Next',
            'Dernière': 'Last',
            
            # Statuts des tâches
            'À faire': 'To Do',
            'En cours': 'In Progress',
            'En révision': 'In Review',
            'Terminé': 'Done',
            'Bloqué': 'Blocked',
            
            # Priorités
            'Basse': 'Low',
            'Moyenne': 'Medium',
            'Haute': 'High',
            'Urgente': 'Urgent',
            
            # Types de tableaux
            'Général': 'General',
            'Club': 'Club',
            'Entraînement': 'Training',
            'Compétition': 'Competition',
            'Fédération': 'Federation',
            'Événement': 'Event',
            
            # Tâches
            'Tâches': 'Tasks',
            'Mes Tâches': 'My Tasks',
            'Nouvelle tâche': 'New Task',
            'Ajouter une tâche': 'Add Task',
            'Modifier la tâche': 'Edit Task',
            'Supprimer la tâche': 'Delete Task',
            'Détails de la tâche': 'Task Details',
            'Vue Kanban': 'Kanban View',
            'Détails': 'Details',
            'Voir détails': 'View Details',
            'Titre de la tâche...': 'Task title...',
            
            # Informations sur les tâches
            'Description': 'Description',
            'Étiquettes': 'Labels',
            'Sous-tâches': 'Subtasks',
            'Commentaires': 'Comments',
            'Assignés': 'Assignees',
            'Non assigné': 'Unassigned',
            'Date d\'échéance': 'Due Date',
            'Date de début': 'Start Date',
            'Non définie': 'Not set',
            'Créé par': 'Created by',
            'Dernière modification': 'Last modified',
            'Tâches liées': 'Related Tasks',
            'Échéance': 'Due Date',
            'En retard': 'Overdue',
            'Terminées': 'Completed',
            'Progression': 'Progress',
            
            # Temps et dates
            'Aujourd\'hui': 'Today',
            'Demain': 'Tomorrow',
            'Hier': 'Yesterday',
            'retard': 'late',
            'Suivi du temps': 'Time Tracking',
            'Estimé': 'Estimated',
            'Passé': 'Spent',
            'Non défini': 'Not set',
            '1 heure': '1 hour',
            'heures': 'hours',
            
            # Messages de confirmation
            'Êtes-vous sûr de vouloir supprimer cette tâche ?': 'Are you sure you want to delete this task?',
            'Êtes-vous sûr de vouloir supprimer ce tableau ?': 'Are you sure you want to delete this board?',
            'Cette action est irréversible.': 'This action is irreversible.',
            
            # Messages de succès et erreur
            'Tâche créée avec succès': 'Task created successfully',
            'Tâche mise à jour avec succès': 'Task updated successfully',
            'Tâche supprimée avec succès': 'Task deleted successfully',
            'Tâche déplacée avec succès': 'Task moved successfully',
            'Tableau mis à jour avec succès': 'Board updated successfully',
            'Erreur lors de la sauvegarde': 'Save error',
            'Erreur de connexion réseau': 'Network connection error',
            'Permission refusée': 'Permission denied',
            'Données invalides': 'Invalid data',
            'Limite WIP dépassée': 'WIP limit exceeded',
            
            # Interface utilisateur
            'Aucun tableau trouvé': 'No boards found',
            'Aucun tableau ne correspond à votre recherche.': 'No boards match your search.',
            'Commencez par créer votre premier tableau Kanban.': 'Start by creating your first Kanban board.',
            'Créer mon premier tableau': 'Create my first board',
            'Aucune tâche assignée': 'No assigned tasks',
            'Vous n\'avez actuellement aucune tâche assignée.': 'You currently have no assigned tasks.',
            'Voir les tableaux': 'View boards',
            'Aucun commentaire pour le moment': 'No comments yet',
            'Ajouter': 'Add',
            'Ajouter le commentaire': 'Add comment',
            'modifié': 'edited',
            
            # Filtres et recherche
            'Tous les statuts': 'All statuses',
            'Toutes priorités': 'All priorities',
            'Tous les assignés': 'All assignees',
            'En retard uniquement': 'Overdue only',
            'Effacer': 'Clear',
            'Actualiser': 'Refresh',
            
            # Navigation et organisation
            'Retour au tableau': 'Back to board',
            'Plein écran': 'Fullscreen',
            'Détails du tableau': 'Board details',
            'Public dans l\'organisation': 'Public in organization',
            'Accès restreint': 'Restricted access',
            'Navigation des pages': 'Page navigation',
            
            # Limites et abonnements
            'Fonctionnalité Premium': 'Premium Feature',
            'Les tableaux Kanban sont disponibles avec Master\'s Circle et Grand Champion.': 'Kanban boards are available with Master\'s Circle and Grand Champion.',
            'Fonctionnalité non disponible': 'Feature not available',
            'La gestion de tâches n\'est pas incluse dans votre abonnement actuel.': 'Task management is not included in your current subscription.',
            'Mettre à niveau': 'Upgrade',
            'Dojo Essentials': 'Dojo Essentials',
            'Master\'s Circle': 'Master\'s Circle',
            'Grand Champion': 'Grand Champion',
            'Limite atteinte': 'Limit reached',
            'Limite bientôt atteinte': 'Limit almost reached',
            'Tableaux maximum': 'Maximum boards',
            'Tâches par tableau': 'Tasks per board',
            'Suivi du temps activé': 'Time tracking enabled',
            'Templates activés': 'Templates enabled',
            'API activée': 'API enabled',
            
            # Formulaires et édition
            'Modification rapide': 'Quick edit',
            'Titre': 'Title',
            'Statut': 'Status',
            'Priorité': 'Priority',
            'Séparez par des virgules': 'Separate with commas',
            'Exemple: urgent, important, bug': 'Example: urgent, important, bug',
            'Confirmer la suppression': 'Confirm deletion',
            'Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.': 'Are you sure you want to delete this item? This action is irreversible.',
            
            # Éléments Kanban spécifiques
            'Limite WIP': 'WIP Limit',
            'dans': 'in',
            'Et': 'And',
            'autres': 'others',
            'Veuillez patienter...': 'Please wait...',
            'Aucune modification détectée': 'No changes detected',
            'Le tableau a été mis à jour par d\'autres utilisateurs.': 'The board has been updated by other users.',
        }
        
        if output_format == 'json':
            self.generate_json_file(translations, lang_code)
        elif output_format == 'po':
            self.generate_po_file(translations, lang_code)
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Fichiers de traduction générés avec succès pour {lang_code} au format {output_format}'
            )
        )

    def generate_json_file(self, translations, lang_code):
        """Génère un fichier JSON avec les traductions"""
        filename = f'task_management_{lang_code}.json'
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
            
        self.stdout.write(f'Fichier JSON généré: {filepath}')

    def generate_po_file(self, translations, lang_code):
        """Génère un fichier PO avec les traductions"""
        filename = f'task_management_{lang_code}.po'
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('# Task Management Translation File\n')
            f.write(f'# Language: {lang_code}\n')
            f.write('# Generated automatically\n\n')
            
            f.write('msgid ""\n')
            f.write('msgstr ""\n')
            f.write(f'"Language: {lang_code}\\n"\n')
            f.write('"MIME-Version: 1.0\\n"\n')
            f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n\n')
            
            for french, translation in translations.items():
                f.write(f'msgid "{french}"\n')
                f.write(f'msgstr "{translation}"\n\n')
                
        self.stdout.write(f'Fichier PO généré: {filepath}')