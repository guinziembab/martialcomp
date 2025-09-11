"""
Template tags pour les traductions spécifiques à la gestion des tâches
"""
from django import template
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def task_status_choices():
    """Retourne les choix de statuts des tâches pour JavaScript"""
    choices = [
        ('todo', _('À faire')),
        ('in_progress', _('En cours')),
        ('in_review', _('En révision')),
        ('done', _('Terminé')),
        ('blocked', _('Bloqué')),
    ]
    return mark_safe(json.dumps(choices))


@register.simple_tag
def task_priority_choices():
    """Retourne les choix de priorités des tâches pour JavaScript"""
    choices = [
        ('low', _('Basse')),
        ('medium', _('Moyenne')),
        ('high', _('Haute')),
        ('urgent', _('Urgente')),
    ]
    return mark_safe(json.dumps(choices))


@register.simple_tag
def board_type_choices():
    """Retourne les choix de types de tableaux pour JavaScript"""
    choices = [
        ('general', _('Général')),
        ('club', _('Club')),
        ('training', _('Entraînement')),
        ('competition', _('Compétition')),
        ('federation', _('Fédération')),
        ('event', _('Événement')),
    ]
    return mark_safe(json.dumps(choices))


@register.filter
def task_time_display(hours):
    """Formate l'affichage du temps en français"""
    if not hours:
        return _('Non défini')
    
    if hours == 1:
        return _('1 heure')
    else:
        return _('%(hours)s heures') % {'hours': hours}


@register.filter
def relative_time_display(days_diff):
    """Affiche une date relative en français"""
    if days_diff == 0:
        return _('Aujourd\'hui')
    elif days_diff == 1:
        return _('Demain')
    elif days_diff == -1:
        return _('Hier')
    elif days_diff > 0:
        if days_diff == 1:
            return _('Dans 1 jour')
        else:
            return _('Dans %(days)s jours') % {'days': days_diff}
    else:
        abs_days = abs(days_diff)
        if abs_days == 1:
            return _('Il y a 1 jour')
        else:
            return _('Il y a %(days)s jours') % {'days': abs_days}


@register.simple_tag
def js_translations():
    """Retourne toutes les traductions nécessaires pour JavaScript"""
    translations = {
        # Messages de base
        'loading': str(_('Chargement...')),
        'error': str(_('Erreur')),
        'success': str(_('Succès')),
        'confirm': str(_('Confirmer')),
        'cancel': str(_('Annuler')),
        'delete': str(_('Supprimer')),
        'edit': str(_('Modifier')),
        'save': str(_('Enregistrer')),
        'close': str(_('Fermer')),
        
        # Actions spécifiques aux tâches
        'addTask': str(_('Ajouter une tâche')),
        'editTask': str(_('Modifier la tâche')),
        'deleteTask': str(_('Supprimer la tâche')),
        'moveTask': str(_('Déplacer la tâche')),
        'taskMoved': str(_('Tâche déplacée avec succès')),
        'taskCreated': str(_('Tâche créée avec succès')),
        'taskDeleted': str(_('Tâche supprimée avec succès')),
        'taskUpdated': str(_('Tâche mise à jour avec succès')),
        
        # Messages d'erreur
        'saveError': str(_('Erreur lors de la sauvegarde')),
        'networkError': str(_('Erreur de connexion réseau')),
        'permissionDenied': str(_('Permission refusée')),
        'invalidData': str(_('Données invalides')),
        'wipLimitExceeded': str(_('Limite WIP dépassée')),
        
        # Confirmations
        'confirmDeleteTask': str(_('Êtes-vous sûr de vouloir supprimer cette tâche ?')),
        'confirmDeleteBoard': str(_('Êtes-vous sûr de vouloir supprimer ce tableau ?')),
        
        # Divers
        'pleaseWait': str(_('Veuillez patienter...')),
        'noChanges': str(_('Aucune modification détectée')),
        'boardUpdated': str(_('Tableau mis à jour avec succès')),
        'allTasks': str(_('Toutes les tâches')),
        'myTasks': str(_('Mes tâches')),
        'overdueTasks': str(_('Tâches en retard')),
        'completedTasks': str(_('Tâches terminées')),
        
        # Temps relatif
        'today': str(_('Aujourd\'hui')),
        'tomorrow': str(_('Demain')),
        'yesterday': str(_('Hier')),
        'daysLate': str(_('jours de retard')),
        'daysLeft': str(_('jours restants')),
        
        # Statuts
        'todo': str(_('À faire')),
        'inProgress': str(_('En cours')),
        'inReview': str(_('En révision')),
        'done': str(_('Terminé')),
        'blocked': str(_('Bloqué')),
        
        # Priorités
        'low': str(_('Basse')),
        'medium': str(_('Moyenne')),
        'high': str(_('Haute')),
        'urgent': str(_('Urgente')),
        
        # Éléments UI
        'noResults': str(_('Aucun résultat')),
        'searchPlaceholder': str(_('Rechercher...')),
        'filterBy': str(_('Filtrer par')),
        'sortBy': str(_('Trier par')),
        'viewAll': str(_('Voir tout')),
        'showMore': str(_('Afficher plus')),
        'showLess': str(_('Afficher moins')),
    }
    
    return mark_safe(json.dumps(translations))