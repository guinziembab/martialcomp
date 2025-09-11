from django.db import models
from django.utils.translation import gettext_lazy as _
from .boards import BoardType


class BoardTemplate(models.Model):
    """
    Board Templates for quick board creation
    Predefined board layouts for common use cases
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    board_type = models.CharField(
        _("Type de tableau"),
        max_length=20,
        choices=BoardType.choices
    )
    
    # Template configuration
    columns_config = models.JSONField(
        _("Configuration des colonnes"),
        help_text=_("Configuration JSON des colonnes par défaut")
    )
    default_tasks = models.JSONField(
        _("Tâches par défaut"),
        default=list,
        help_text=_("Tâches prédéfinies à créer avec le template")
    )
    
    # Template metadata
    is_system_template = models.BooleanField(_("Template système"), default=False)
    is_public = models.BooleanField(_("Public"), default=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Usage statistics
    usage_count = models.PositiveIntegerField(_("Nombre d'utilisations"), default=0)
    
    # Template settings
    color_scheme = models.CharField(_("Schéma de couleurs"), max_length=20, default='default')
    icon = models.CharField(_("Icône"), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _("Template de tableau")
        verbose_name_plural = _("Templates de tableaux")
        ordering = ['-is_system_template', 'name']
        indexes = [
            models.Index(fields=['board_type', 'is_public']),
            models.Index(fields=['is_system_template']),
        ]
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    @classmethod
    def get_system_templates(cls):
        """Get all system templates"""
        return cls.objects.filter(is_system_template=True, is_public=True)
    
    @classmethod
    def get_templates_for_type(cls, board_type):
        """Get templates for specific board type"""
        return cls.objects.filter(
            board_type=board_type,
            is_public=True
        ).order_by('-is_system_template', 'name')
    
    def get_default_columns(self):
        """Get default columns configuration"""
        if not self.columns_config:
            return []
        
        # Ensure proper structure
        columns = []
        for i, col_config in enumerate(self.columns_config):
            column = {
                'name': col_config.get('name', f'Colonne {i+1}'),
                'position': col_config.get('position', i+1),
                'color': col_config.get('color', '#6B7280'),
                'wip_limit': col_config.get('wip_limit'),
                'is_done_column': col_config.get('is_done_column', False),
            }
            columns.append(column)
        
        return columns
    
    def get_default_tasks(self):
        """Get default tasks configuration"""
        if not self.default_tasks:
            return []
        
        tasks = []
        for task_config in self.default_tasks:
            task = {
                'title': task_config.get('title', 'Nouvelle tâche'),
                'description': task_config.get('description', ''),
                'column_position': task_config.get('column_position', 1),
                'priority': task_config.get('priority', 'medium'),
                'labels': task_config.get('labels', []),
            }
            tasks.append(task)
        
        return tasks


# System templates data
SYSTEM_TEMPLATES = [
    {
        'name': 'Tableau Kanban Basique',
        'description': 'Un tableau Kanban simple avec les colonnes essentielles',
        'board_type': BoardType.GENERAL,
        'columns_config': [
            {'name': 'À faire', 'position': 1, 'color': '#EF4444'},
            {'name': 'En cours', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En révision', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Terminé', 'position': 4, 'color': '#10B981', 'is_done_column': True}
        ],
        'icon': 'fas fa-columns'
    },
    {
        'name': 'Gestion de Compétition',
        'description': 'Template pour la gestion d\'événements de compétition',
        'board_type': BoardType.COMPETITION,
        'columns_config': [
            {'name': 'Planification', 'position': 1, 'color': '#8B5CF6'},
            {'name': 'Préparation', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En cours', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Suivi post-événement', 'position': 4, 'color': '#06B6D4'},
            {'name': 'Clôturé', 'position': 5, 'color': '#10B981', 'is_done_column': True}
        ],
        'default_tasks': [
            {'title': 'Réserver le lieu', 'column_position': 1, 'priority': 'high'},
            {'title': 'Inscription des participants', 'column_position': 1, 'priority': 'high'},
            {'title': 'Préparation du matériel', 'column_position': 1, 'priority': 'medium'},
            {'title': 'Communication événement', 'column_position': 1, 'priority': 'medium'},
        ],
        'icon': 'fas fa-trophy'
    },
    {
        'name': 'Gestion d\'Entraînement',
        'description': 'Template pour la planification des sessions d\'entraînement',
        'board_type': BoardType.TRAINING,
        'columns_config': [
            {'name': 'Idées', 'position': 1, 'color': '#8B5CF6'},
            {'name': 'Planifié', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En préparation', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Réalisé', 'position': 4, 'color': '#10B981', 'is_done_column': True}
        ],
        'default_tasks': [
            {'title': 'Définir les objectifs de la session', 'column_position': 1, 'priority': 'high'},
            {'title': 'Préparer les exercices', 'column_position': 1, 'priority': 'medium'},
            {'title': 'Vérifier le matériel', 'column_position': 1, 'priority': 'medium'},
        ],
        'icon': 'fas fa-dumbbell'
    },
    {
        'name': 'Gestion de Club',
        'description': 'Template pour la gestion administrative d\'un club',
        'board_type': BoardType.CLUB,
        'columns_config': [
            {'name': 'À traiter', 'position': 1, 'color': '#EF4444'},
            {'name': 'En cours', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En attente de validation', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Validé', 'position': 4, 'color': '#10B981', 'is_done_column': True}
        ],
        'default_tasks': [
            {'title': 'Renouvellement des licences', 'column_position': 1, 'priority': 'high'},
            {'title': 'Organisation événement club', 'column_position': 1, 'priority': 'medium'},
            {'title': 'Mise à jour site web', 'column_position': 1, 'priority': 'low'},
        ],
        'icon': 'fas fa-users'
    }
]