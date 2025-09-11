# Guide d'Implémentation - Module Kanban Task Management

## Vue d'ensemble

Ce guide détaille l'implémentation du module `task_management` pour intégrer un système de gestion de tâches Kanban dans MartialComp. Le module s'intègre parfaitement avec l'architecture modulaire existante et exploite le système multi-tenant, les rôles utilisateurs et les feature flags.

## 1. Architecture du Module

### 1.1 Position dans l'architecture

```
MartialComp/
├── config/
├── competitions/          # Module principal
├── organizations/         # Gestion des organisations
├── grades/               # Système de grades
├── finances/             # Gestion financière
├── task_management/      # 🆕 Nouveau module Kanban
└── ...
```

### 1.2 Dépendances

- **Module principal** : `competitions` (modèles Practitioner, Competition)
- **Module organisation** : `organizations` (modèles Organization, OrganizationMember)
- **Core Django** : Authentification, permissions, multi-tenant

### 1.3 Feature Flag

Le module sera contrôlé par un feature flag configurable dans les packages d'abonnement :

- **Dojo Essentials** : ❌ Non disponible
- **Master's Circle** : ✅ Kanban basique (max 3 boards)
- **Grand Champion Suite** : ✅ Kanban complet (boards illimités + fonctionnalités avancées)

## 2. Structure du Module

### 2.1 Arborescence des fichiers

```
task_management/
├── __init__.py
├── apps.py
├── admin.py
├── forms.py
├── migrations/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   ├── boards.py
│   ├── tasks.py
│   ├── assignments.py
│   └── templates.py
├── views/
│   ├── __init__.py
│   ├── boards.py
│   ├── tasks.py
│   ├── kanban.py
│   └── api.py
├── templates/
│   └── task_management/
│       ├── base/
│       │   ├── kanban_base.html
│       │   └── task_sidebar.html
│       ├── boards/
│       │   ├── board_list.html
│       │   ├── board_detail.html
│       │   ├── board_form.html
│       │   └── board_settings.html
│       ├── tasks/
│       │   ├── task_detail.html
│       │   ├── task_form.html
│       │   └── task_comments.html
│       └── kanban/
│           ├── kanban_board.html
│           ├── kanban_card.html
│           └── kanban_column.html
├── static/
│   └── task_management/
│       ├── css/
│       │   ├── kanban.css
│       │   └── tasks.css
│       └── js/
│           ├── kanban-drag-drop.js
│           ├── task-management.js
│           └── real-time-updates.js
├── management/
│   └── commands/
│       ├── create_default_boards.py
│       └── cleanup_tasks.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_api.py
├── urls.py
├── utils.py
└── signals.py
```

## 3. Modèles de Données

### 3.1 Modèle Board (`models/boards.py`)

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember

User = get_user_model()

class BoardType(models.TextChoices):
    GENERAL = 'general', _('Général')
    COMPETITION = 'competition', _('Compétition')
    TRAINING = 'training', _('Entraînement')
    FEDERATION = 'federation', _('Fédération')
    CLUB = 'club', _('Club')

class Board(models.Model):
    """
    Tableau Kanban principal
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    # Relations multi-tenant
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='boards',
        verbose_name=_("Organisation")
    )
    
    # Type et contexte
    board_type = models.CharField(
        _("Type de tableau"),
        max_length=20,
        choices=BoardType.choices,
        default=BoardType.GENERAL
    )
    
    # Relations optionnelles selon le contexte
    related_competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='boards',
        verbose_name=_("Compétition associée")
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_boards',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Configuration
    is_template = models.BooleanField(_("Est un template"), default=False)
    is_archived = models.BooleanField(_("Archivé"), default=False)
    color_theme = models.CharField(_("Thème de couleur"), max_length=20, default='blue')
    
    # Permissions d'accès
    is_public = models.BooleanField(_("Public dans l'organisation"), default=False)
    allowed_roles = models.JSONField(
        _("Rôles autorisés"),
        default=list,
        help_text=_("Liste des rôles d'organisation autorisés à accéder au board")
    )
    
    class Meta:
        verbose_name = _("Tableau Kanban")
        verbose_name_plural = _("Tableaux Kanban")
        ordering = ['-created_at']
        unique_together = ['organization', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def can_access(self, user):
        """Vérifie si un utilisateur peut accéder au board"""
        if not user.is_authenticated:
            return False
            
        # Propriétaire du board
        if self.created_by == user:
            return True
            
        # Membres de l'organisation avec les bons rôles
        try:
            membership = OrganizationMember.objects.get(
                user=user, 
                organization=self.organization,
                is_active=True
            )
            
            if self.is_public:
                return True
                
            if not self.allowed_roles:
                return membership.role in ['owner', 'admin']
                
            return membership.role in self.allowed_roles
            
        except OrganizationMember.DoesNotExist:
            return False

class Column(models.Model):
    """
    Colonnes du tableau Kanban
    """
    name = models.CharField(_("Nom"), max_length=100)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name=_("Tableau")
    )
    position = models.PositiveIntegerField(_("Position"))
    color = models.CharField(_("Couleur"), max_length=7, default='#6B7280')
    
    # Limites WIP (Work In Progress)
    wip_limit = models.PositiveIntegerField(
        _("Limite WIP"),
        null=True, blank=True,
        help_text=_("Nombre maximum de tâches dans cette colonne")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Colonne")
        verbose_name_plural = _("Colonnes")
        ordering = ['position']
        unique_together = ['board', 'position']
    
    def __str__(self):
        return f"{self.name} ({self.board.name})"
```

### 3.2 Modèle Task (`models/tasks.py`)

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from organizations.models import OrganizationMember

User = get_user_model()

class TaskPriority(models.TextChoices):
    LOW = 'low', _('Basse')
    MEDIUM = 'medium', _('Moyenne')
    HIGH = 'high', _('Haute')
    URGENT = 'urgent', _('Urgente')

class TaskStatus(models.TextChoices):
    TODO = 'todo', _('À faire')
    IN_PROGRESS = 'in_progress', _('En cours')
    IN_REVIEW = 'in_review', _('En révision')
    DONE = 'done', _('Terminé')
    BLOCKED = 'blocked', _('Bloqué')

class Task(models.Model):
    """
    Tâche Kanban
    """
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    # Relations
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Tableau")
    )
    column = models.ForeignKey(
        'Column',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Colonne")
    )
    
    # Assignation
    assignees = models.ManyToManyField(
        OrganizationMember,
        blank=True,
        related_name='assigned_tasks',
        verbose_name=_("Assignés")
    )
    
    # Propriétés de la tâche
    priority = models.CharField(
        _("Priorité"),
        max_length=10,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    status = models.CharField(
        _("Statut"),
        max_length=15,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO
    )
    
    # Dates
    due_date = models.DateTimeField(_("Date d'échéance"), null=True, blank=True)
    start_date = models.DateTimeField(_("Date de début"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Terminé le"), null=True, blank=True)
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Position dans la colonne
    position = models.PositiveIntegerField(_("Position"), default=0)
    
    # Estimation et temps
    estimated_hours = models.DecimalField(
        _("Heures estimées"),
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    time_spent = models.DecimalField(
        _("Temps passé"),
        max_digits=5, decimal_places=2,
        default=0
    )
    
    # Relations optionnelles
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subtasks',
        verbose_name=_("Tâche parent")
    )
    
    # Attachements et liens
    attachments = models.JSONField(
        _("Pièces jointes"),
        default=list,
        help_text=_("URLs des fichiers attachés")
    )
    
    class Meta:
        verbose_name = _("Tâche")
        verbose_name_plural = _("Tâches")
        ordering = ['position', 'created_at']
    
    def __str__(self):
        return f"{self.title} ({self.board.name})"
    
    @property
    def is_overdue(self):
        """Vérifie si la tâche est en retard"""
        if not self.due_date or self.status == TaskStatus.DONE:
            return False
        from django.utils import timezone
        return timezone.now() > self.due_date
    
    def get_progress_percentage(self):
        """Calcule le pourcentage de progression basé sur les sous-tâches"""
        subtasks = self.subtasks.all()
        if not subtasks:
            return 100 if self.status == TaskStatus.DONE else 0
            
        completed = subtasks.filter(status=TaskStatus.DONE).count()
        return (completed / subtasks.count()) * 100

class TaskComment(models.Model):
    """
    Commentaires sur les tâches
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Tâche")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Auteur")
    )
    content = models.TextField(_("Contenu"))
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.task.title}"
```

### 3.3 Modèle Template (`models/templates.py`)

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class BoardTemplate(models.Model):
    """
    Templates prédéfinis de boards Kanban
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    board_type = models.CharField(
        _("Type de tableau"),
        max_length=20,
        choices=BoardType.choices
    )
    
    # Configuration JSON du template
    columns_config = models.JSONField(
        _("Configuration des colonnes"),
        help_text=_("Configuration JSON des colonnes par défaut")
    )
    default_tasks = models.JSONField(
        _("Tâches par défaut"),
        default=list,
        help_text=_("Tâches prédéfinies à créer avec le template")
    )
    
    is_system_template = models.BooleanField(_("Template système"), default=False)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Template de tableau")
        verbose_name_plural = _("Templates de tableaux")
        ordering = ['name']
    
    def __str__(self):
        return self.name
```

## 4. Configuration et Feature Flags

### 4.1 Ajout du module dans `settings.py`

```python
INSTALLED_APPS = [
    # ...
    'competitions',
    'organizations',
    'grades',
    'task_management',  # 🆕 Nouveau module
    # ...
]

# Configuration spécifique au module
TASK_MANAGEMENT = {
    'MAX_BOARDS_PER_ORG': {
        'dojo_essentials': 0,
        'master_circle': 3,
        'grand_champion': 999
    },
    'MAX_TASKS_PER_BOARD': {
        'dojo_essentials': 0,
        'master_circle': 50,
        'grand_champion': 999
    },
    'ENABLE_TIME_TRACKING': {
        'dojo_essentials': False,
        'master_circle': True,
        'grand_champion': True
    },
    'ENABLE_TEMPLATES': {
        'dojo_essentials': False,
        'master_circle': False,
        'grand_champion': True
    }
}
```

### 4.2 Feature Flag dans la base

```python
# Migration pour créer le feature flag
from django.db import migrations

def create_task_management_feature(apps, schema_editor):
    FeatureFlag = apps.get_model('core', 'FeatureFlag')
    SubscriptionTier = apps.get_model('subscriptions', 'SubscriptionTier')
    
    # Créer le feature flag
    feature = FeatureFlag.objects.create(
        name='task_management',
        display_name='Gestion de Tâches Kanban',
        description='Système de gestion de tâches et projets avec interface Kanban',
        module='task_management',
        complexity='advanced',
        view_names='board_list,board_detail,task_detail,kanban_view',
        url_patterns='boards/,tasks/,kanban/',
        model_names='Board,Task,Column,TaskComment',
        is_active=True
    )
    
    # Associer aux tiers d'abonnement
    master_circle = SubscriptionTier.objects.get(name='master_circle')
    grand_champion = SubscriptionTier.objects.get(name='grand_champion')
    
    feature.subscription_tiers.add(master_circle, grand_champion)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        ('subscriptions', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_task_management_feature),
    ]
```

## 5. Vues et API

### 5.1 Vues principales (`views/boards.py`)

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from organizations.models import OrganizationMember
from ..models import Board, Column, Task
from ..forms import BoardForm, ColumnForm, TaskForm
from ..utils import check_board_access, get_user_organizations

@login_required
def board_list(request):
    """Liste des boards accessibles à l'utilisateur"""
    user_orgs = get_user_organizations(request.user)
    
    boards = Board.objects.filter(
        organization__in=user_orgs,
        is_archived=False
    ).select_related('organization', 'created_by').annotate(
        task_count=Count('tasks'),
        member_count=Count('tasks__assignees', distinct=True)
    )
    
    # Filtrage par type si spécifié
    board_type = request.GET.get('type')
    if board_type:
        boards = boards.filter(board_type=board_type)
    
    context = {
        'boards': boards,
        'board_types': Board.BoardType.choices,
        'current_type': board_type
    }
    return render(request, 'task_management/boards/board_list.html', context)

@login_required
def board_detail(request, board_id):
    """Détail d'un board avec ses colonnes et tâches"""
    board = get_object_or_404(Board, id=board_id)
    
    if not board.can_access(request.user):
        messages.error(request, _("Vous n'avez pas accès à ce tableau."))
        return redirect('task_management:board_list')
    
    columns = board.columns.all().prefetch_related(
        'tasks__assignees__user'
    )
    
    context = {
        'board': board,
        'columns': columns,
        'can_edit': check_board_access(request.user, board, 'edit')
    }
    return render(request, 'task_management/boards/board_detail.html', context)

@login_required
@require_http_methods(["POST"])
def create_board(request):
    """Création d'un nouveau board"""
    form = BoardForm(request.POST)
    
    if form.is_valid():
        board = form.save(commit=False)
        board.created_by = request.user
        board.save()
        
        # Créer les colonnes par défaut
        default_columns = [
            {'name': _('À faire'), 'position': 1, 'color': '#EF4444'},
            {'name': _('En cours'), 'position': 2, 'color': '#F59E0B'},
            {'name': _('En révision'), 'position': 3, 'color': '#3B82F6'},
            {'name': _('Terminé'), 'position': 4, 'color': '#10B981'}
        ]
        
        for col_data in default_columns:
            Column.objects.create(board=board, **col_data)
        
        messages.success(request, _("Tableau créé avec succès."))
        return redirect('task_management:board_detail', board_id=board.id)
    
    return JsonResponse({'errors': form.errors}, status=400)
```

### 5.2 API REST (`views/api.py`)

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from ..models import Board, Task, Column
from ..serializers import BoardSerializer, TaskSerializer, ColumnSerializer
from ..permissions import BoardAccessPermission

class BoardViewSet(viewsets.ModelViewSet):
    """API ViewSet pour les boards"""
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, BoardAccessPermission]
    
    def get_queryset(self):
        user_orgs = get_user_organizations(self.request.user)
        return Board.objects.filter(
            organization__in=user_orgs,
            is_archived=False
        ).select_related('organization', 'created_by')
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive un board"""
        board = self.get_object()
        board.is_archived = True
        board.save()
        return Response({'status': 'archived'})
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export du board en JSON"""
        board = self.get_object()
        data = {
            'board': BoardSerializer(board).data,
            'columns': ColumnSerializer(board.columns.all(), many=True).data,
            'tasks': TaskSerializer(board.tasks.all(), many=True).data
        }
        return Response(data)

class TaskViewSet(viewsets.ModelViewSet):
    """API ViewSet pour les tâches"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, BoardAccessPermission]
    
    def get_queryset(self):
        board_id = self.request.query_params.get('board')
        if board_id:
            return Task.objects.filter(board_id=board_id)
        return Task.objects.none()
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Déplacement d'une tâche entre colonnes"""
        task = self.get_object()
        new_column_id = request.data.get('column_id')
        new_position = request.data.get('position', 0)
        
        if not new_column_id:
            return Response(
                {'error': 'column_id required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_column = Column.objects.get(id=new_column_id, board=task.board)
        except Column.DoesNotExist:
            return Response(
                {'error': 'Invalid column'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Réorganiser les positions dans l'ancienne colonne
            Task.objects.filter(
                column=task.column,
                position__gt=task.position
            ).update(position=models.F('position') - 1)
            
            # Réorganiser les positions dans la nouvelle colonne
            Task.objects.filter(
                column=new_column,
                position__gte=new_position
            ).update(position=models.F('position') + 1)
            
            # Déplacer la tâche
            task.column = new_column
            task.position = new_position
            task.save()
        
        return Response(TaskSerializer(task).data)
```

## 6. Templates et Interface

### 6.1 Template principal Kanban (`templates/task_management/kanban/kanban_board.html`)

```html
{% extends 'base.html' %}
{% load i18n static %}

{% block title %}{{ board.name }} - {% trans "Tableau Kanban" %}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'task_management/css/kanban.css' %}">
{% endblock %}

{% block content %}
<div class="kanban-container">
    <div class="kanban-header">
        <div class="board-info">
            <h1>{{ board.name }}</h1>
            <p class="board-description">{{ board.description }}</p>
        </div>
        <div class="board-actions">
            {% if can_edit %}
                <button class="btn btn-primary" data-toggle="modal" data-target="#addTaskModal">
                    <i class="fas fa-plus"></i> {% trans "Nouvelle tâche" %}
                </button>
                <button class="btn btn-secondary" data-toggle="modal" data-target="#boardSettingsModal">
                    <i class="fas fa-cog"></i> {% trans "Paramètres" %}
                </button>
            {% endif %}
        </div>
    </div>

    <div class="kanban-board" id="kanban-board">
        {% for column in columns %}
            <div class="kanban-column" data-column-id="{{ column.id }}">
                <div class="column-header" style="border-color: {{ column.color }};">
                    <h3>{{ column.name }}</h3>
                    <span class="task-count">{{ column.tasks.count }}</span>
                    {% if column.wip_limit %}
                        <span class="wip-limit {% if column.tasks.count >= column.wip_limit %}wip-exceeded{% endif %}">
                            / {{ column.wip_limit }}
                        </span>
                    {% endif %}
                </div>
                
                <div class="column-tasks" data-column-id="{{ column.id }}">
                    {% for task in column.tasks.all %}
                        {% include 'task_management/kanban/kanban_card.html' with task=task %}
                    {% endfor %}
                </div>
                
                {% if can_edit %}
                    <div class="add-task-button">
                        <button class="btn-add-task" data-column-id="{{ column.id }}">
                            <i class="fas fa-plus"></i> {% trans "Ajouter une tâche" %}
                        </button>
                    </div>
                {% endif %}
            </div>
        {% endfor %}
    </div>
</div>

<!-- Modales pour l'édition -->
{% include 'task_management/modals/add_task_modal.html' %}
{% include 'task_management/modals/board_settings_modal.html' %}
{% endblock %}

{% block extra_js %}
<script src="{% static 'task_management/js/kanban-drag-drop.js' %}"></script>
<script src="{% static 'task_management/js/task-management.js' %}"></script>
<script>
    // Configuration JavaScript
    window.kanbanConfig = {
        boardId: {{ board.id }},
        canEdit: {{ can_edit|yesno:"true,false" }},
        csrfToken: '{{ csrf_token }}',
        urls: {
            moveTask: '{% url "api:task-move" pk=0 %}'.replace('0', ''),
            updateTask: '{% url "api:task-detail" pk=0 %}'.replace('0', ''),
            createTask: '{% url "api:task-list" %}'
        }
    };
</script>
{% endblock %}
```

### 6.2 Carte de tâche (`templates/task_management/kanban/kanban_card.html`)

```html
{% load i18n %}

<div class="kanban-card" data-task-id="{{ task.id }}" draggable="true">
    <div class="card-header">
        <div class="task-priority priority-{{ task.priority }}">
            {% if task.priority == 'urgent' %}
                <i class="fas fa-exclamation-triangle"></i>
            {% elif task.priority == 'high' %}
                <i class="fas fa-arrow-up"></i>
            {% endif %}
        </div>
        <div class="task-actions">
            <button class="btn-card-action" onclick="openTaskDetail({{ task.id }})">
                <i class="fas fa-expand-alt"></i>
            </button>
        </div>
    </div>
    
    <div class="card-content">
        <h4 class="task-title">{{ task.title }}</h4>
        {% if task.description %}
            <p class="task-description">{{ task.description|truncatewords:15 }}</p>
        {% endif %}
    </div>
    
    <div class="card-footer">
        <div class="task-meta">
            {% if task.due_date %}
                <span class="due-date {% if task.is_overdue %}overdue{% endif %}">
                    <i class="fas fa-calendar-alt"></i>
                    {{ task.due_date|date:"M d" }}
                </span>
            {% endif %}
            
            {% if task.subtasks.exists %}
                <span class="subtasks">
                    <i class="fas fa-list"></i>
                    {{ task.subtasks.filter:status='done'|length }}/{{ task.subtasks.count }}
                </span>
            {% endif %}
            
            {% if task.comments.exists %}
                <span class="comments">
                    <i class="fas fa-comment"></i>
                    {{ task.comments.count }}
                </span>
            {% endif %}
        </div>
        
        <div class="task-assignees">
            {% for assignment in task.assignees.all|slice:":3" %}
                <div class="assignee-avatar" title="{{ assignment.user.get_full_name }}">
                    {% if assignment.user.profile.avatar %}
                        <img src="{{ assignment.user.profile.avatar.url }}" alt="{{ assignment.user.get_full_name }}">
                    {% else %}
                        <div class="avatar-placeholder">
                            {{ assignment.user.first_name|first }}{{ assignment.user.last_name|first }}
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
            {% if task.assignees.count > 3 %}
                <div class="assignee-more">+{{ task.assignees.count|add:"-3" }}</div>
            {% endif %}
        </div>
    </div>
</div>
```

## 7. JavaScript et Interactions

### 7.1 Drag & Drop (`static/task_management/js/kanban-drag-drop.js`)

```javascript
class KanbanDragDrop {
    constructor(boardElement, config) {
        this.board = boardElement;
        this.config = config;
        this.draggedTask = null;
        this.init();
    }
    
    init() {
        this.setupDragAndDrop();
        this.setupEventListeners();
    }
    
    setupDragAndDrop() {
        // Configurer les éléments draggables
        this.board.querySelectorAll('.kanban-card').forEach(card => {
            card.addEventListener('dragstart', this.handleDragStart.bind(this));
            card.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
        
        // Configurer les zones de drop
        this.board.querySelectorAll('.column-tasks').forEach(column => {
            column.addEventListener('dragover', this.handleDragOver.bind(this));
            column.addEventListener('drop', this.handleDrop.bind(this));
            column.addEventListener('dragenter', this.handleDragEnter.bind(this));
            column.addEventListener('dragleave', this.handleDragLeave.bind(this));
        });
    }
    
    handleDragStart(e) {
        if (!this.config.canEdit) {
            e.preventDefault();
            return;
        }
        
        this.draggedTask = e.target;
        this.draggedTask.classList.add('dragging');
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
    }
    
    handleDragEnd(e) {
        if (this.draggedTask) {
            this.draggedTask.classList.remove('dragging');
            this.draggedTask = null;
        }
        
        // Nettoyer les indicateurs visuels
        this.board.querySelectorAll('.column-tasks').forEach(column => {
            column.classList.remove('drag-over');
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const column = e.currentTarget;
        const afterElement = this.getDragAfterElement(column, e.clientY);
        
        if (afterElement == null) {
            column.appendChild(this.createDropIndicator());
        } else {
            column.insertBefore(this.createDropIndicator(), afterElement);
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        
        if (!this.draggedTask) return;
        
        const column = e.currentTarget;
        const columnId = column.dataset.columnId;
        const taskId = this.draggedTask.dataset.taskId;
        
        // Calculer la nouvelle position
        const afterElement = this.getDragAfterElement(column, e.clientY);
        let newPosition = 0;
        
        if (afterElement) {
            const tasks = Array.from(column.querySelectorAll('.kanban-card'));
            newPosition = tasks.indexOf(afterElement);
        } else {
            newPosition = column.querySelectorAll('.kanban-card').length;
        }
        
        // Effectuer le déplacement via API
        this.moveTask(taskId, columnId, newPosition);
        
        // Nettoyer les indicateurs
        this.removeDropIndicators();
    }
    
    async moveTask(taskId, columnId, position) {
        try {
            const response = await fetch(
                `${this.config.urls.moveTask}${taskId}/move/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.config.csrfToken,
                    },
                    body: JSON.stringify({
                        column_id: columnId,
                        position: position
                    })
                }
            );
            
            if (!response.ok) {
                throw new Error('Erreur lors du déplacement de la tâche');
            }
            
            const data = await response.json();
            this.updateTaskUI(data);
            
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible de déplacer la tâche');
            // Reverter le déplacement visuel
            location.reload();
        }
    }
    
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.kanban-card:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    createDropIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'drop-indicator';
        return indicator;
    }
    
    removeDropIndicators() {
        this.board.querySelectorAll('.drop-indicator').forEach(indicator => {
            indicator.remove();
        });
    }
    
    showError(message) {
        // Implémenter l'affichage d'erreur selon votre système de notifications
        alert(message);
    }
    
    updateTaskUI(taskData) {
        // Mettre à jour l'interface avec les nouvelles données de la tâche
        const taskElement = this.board.querySelector(`[data-task-id="${taskData.id}"]`);
        if (taskElement) {
            // Mettre à jour les données si nécessaire
            taskElement.dataset.columnId = taskData.column;
        }
    }
}

// Initialisation du drag & drop
document.addEventListener('DOMContentLoaded', function() {
    const kanbanBoard = document.getElementById('kanban-board');
    if (kanbanBoard && window.kanbanConfig) {
        new KanbanDragDrop(kanbanBoard, window.kanbanConfig);
    }
});
```

## 8. Tests

### 8.1 Tests des modèles (`tests/test_models.py`)

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember
from task_management.models import Board, Column, Task

User = get_user_model()

class BoardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            organization_type='club'
        )
        self.membership = OrganizationMember.objects.create(
            user=self.user,
            organization=self.organization,
            role='admin'
        )
    
    def test_board_creation(self):
        """Test la création d'un board"""
        board = Board.objects.create(
            name='Test Board',
            description='Test Description',
            organization=self.organization,
            created_by=self.user,
            board_type='general'
        )
        
        self.assertEqual(board.name, 'Test Board')
        self.assertEqual(board.organization, self.organization)
        self.assertEqual(board.created_by, self.user)
    
    def test_board_access_permissions(self):
        """Test les permissions d'accès au board"""
        board = Board.objects.create(
            name='Test Board',
            organization=self.organization,
            created_by=self.user,
            is_public=True
        )
        
        # Le créateur doit avoir accès
        self.assertTrue(board.can_access(self.user))
        
        # Un membre de l'organisation doit avoir accès au board public
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        OrganizationMember.objects.create(
            user=other_user,
            organization=self.organization,
            role='member'
        )
        self.assertTrue(board.can_access(other_user))
        
        # Un utilisateur externe ne doit pas avoir accès
        external_user = User.objects.create_user(
            username='external',
            email='external@example.com',
            password='testpass123'
        )
        self.assertFalse(board.can_access(external_user))

class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            organization_type='club'
        )
        self.board = Board.objects.create(
            name='Test Board',
            organization=self.organization,
            created_by=self.user
        )
        self.column = Column.objects.create(
            name='To Do',
            board=self.board,
            position=1
        )
    
    def test_task_creation(self):
        """Test la création d'une tâche"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            board=self.board,
            column=self.column,
            created_by=self.user,
            priority='medium'
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.board, self.board)
        self.assertEqual(task.column, self.column)
        self.assertEqual(task.priority, 'medium')
    
    def test_task_progress_calculation(self):
        """Test le calcul de progression avec sous-tâches"""
        parent_task = Task.objects.create(
            title='Parent Task',
            board=self.board,
            column=self.column,
            created_by=self.user
        )
        
        # Créer 3 sous-tâches
        subtask1 = Task.objects.create(
            title='Subtask 1',
            board=self.board,
            column=self.column,
            parent_task=parent_task,
            status='done'
        )
        subtask2 = Task.objects.create(
            title='Subtask 2',
            board=self.board,
            column=self.column,
            parent_task=parent_task,
            status='in_progress'
        )
        subtask3 = Task.objects.create(
            title='Subtask 3',
            board=self.board,
            column=self.column,
            parent_task=parent_task,
            status='done'
        )
        
        # 2 tâches terminées sur 3 = 66.67%
        progress = parent_task.get_progress_percentage()
        self.assertAlmostEqual(progress, 66.67, places=1)
```

## 9. Commandes de Management

### 9.1 Création de boards par défaut (`management/commands/create_default_boards.py`)

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization
from task_management.models import Board, Column, BoardTemplate

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des boards par défaut pour les organisations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--org-type',
            type=str,
            help='Type d\'organisation (club, federation, etc.)',
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Template à utiliser',
        )
    
    def handle(self, *args, **options):
        org_type = options.get('org_type')
        template_name = options.get('template')
        
        organizations = Organization.objects.all()
        if org_type:
            organizations = organizations.filter(organization_type=org_type)
        
        created_count = 0
        
        for org in organizations:
            # Vérifier si l'organisation a déjà des boards
            if org.boards.exists():
                continue
            
            admin_user = org.members.filter(role='owner').first()
            if not admin_user:
                admin_user = org.members.filter(role='admin').first()
            
            if not admin_user:
                self.stdout.write(
                    self.style.WARNING(
                        f'Aucun administrateur trouvé pour {org.name}'
                    )
                )
                continue
            
            # Créer le board par défaut
            if template_name:
                template = BoardTemplate.objects.filter(name=template_name).first()
                board = self.create_board_from_template(org, admin_user.user, template)
            else:
                board = self.create_default_board(org, admin_user.user)
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Board créé pour {org.name}: {board.name}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Total: {created_count} boards créés'
            )
        )
    
    def create_default_board(self, organization, user):
        """Crée un board par défaut simple"""
        board = Board.objects.create(
            name=f'Tableau Principal - {organization.name}',
            description='Tableau de gestion générale',
            organization=organization,
            created_by=user,
            board_type='general',
            is_public=True
        )
        
        # Créer les colonnes par défaut
        columns_data = [
            {'name': 'À faire', 'position': 1, 'color': '#EF4444'},
            {'name': 'En cours', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En révision', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Terminé', 'position': 4, 'color': '#10B981'}
        ]
        
        for col_data in columns_data:
            Column.objects.create(board=board, **col_data)
        
        return board
    
    def create_board_from_template(self, organization, user, template):
        """Crée un board à partir d'un template"""
        if not template:
            return self.create_default_board(organization, user)
        
        board = Board.objects.create(
            name=f'{template.name} - {organization.name}',
            description=template.description,
            organization=organization,
            created_by=user,
            board_type=template.board_type,
            is_public=True
        )
        
        # Créer les colonnes depuis le template
        for col_data in template.columns_config:
            Column.objects.create(board=board, **col_data)
        
        return board
```

## 10. Intégration et Déploiement

### 10.1 URLs principales (`urls.py`)

```python
from django.urls import path, include
from . import views

app_name = 'task_management'

urlpatterns = [
    # Boards
    path('boards/', views.board_list, name='board_list'),
    path('boards/<int:board_id>/', views.board_detail, name='board_detail'),
    path('boards/create/', views.create_board, name='create_board'),
    path('boards/<int:board_id>/settings/', views.board_settings, name='board_settings'),
    
    # Kanban interface
    path('kanban/<int:board_id>/', views.kanban_view, name='kanban_view'),
    
    # Tasks
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/create/', views.create_task, name='create_task'),
    
    # API
    path('api/', include('task_management.api.urls')),
]
```

### 10.2 Intégration dans le menu principal

```html
<!-- Dans le template de navigation principal -->
{% load i18n feature_flags %}

{% if user.is_authenticated %}
    {% has_feature 'task_management' user as has_kanban %}
    {% if has_kanban %}
        <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="kanbanDropdown" role="button" data-toggle="dropdown">
                <i class="fas fa-tasks"></i> {% trans "Gestion de Tâches" %}
            </a>
            <div class="dropdown-menu">
                <a class="dropdown-item" href="{% url 'task_management:board_list' %}">
                    <i class="fas fa-columns"></i> {% trans "Mes Tableaux" %}
                </a>
                <a class="dropdown-item" href="{% url 'task_management:create_board' %}">
                    <i class="fas fa-plus"></i> {% trans "Nouveau Tableau" %}
                </a>
                <div class="dropdown-divider"></div>
                <a class="dropdown-item" href="{% url 'task_management:board_list' %}?type=competition">
                    <i class="fas fa-trophy"></i> {% trans "Compétitions" %}
                </a>
                <a class="dropdown-item" href="{% url 'task_management:board_list' %}?type=training">
                    <i class="fas fa-dumbbell"></i> {% trans "Entraînements" %}
                </a>
            </div>
        </li>
    {% endif %}
{% endif %}
```

## 11. Configuration de Production

### 11.1 Variables d'environnement

```bash
# .env
TASK_MANAGEMENT_ENABLED=True
TASK_MANAGEMENT_MAX_BOARDS_PER_ORG=10
TASK_MANAGEMENT_ENABLE_NOTIFICATIONS=True
TASK_MANAGEMENT_WEBSOCKET_URL=ws://localhost:8001/ws/
```

### 11.2 Optimisations de performance

```python
# settings/production.py

# Cache pour les boards fréquemment consultés
CACHES['task_boards'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'TIMEOUT': 300,  # 5 minutes
}

# Signaux pour l'invalidation du cache
@receiver(post_save, sender=Board)
def invalidate_board_cache(sender, instance, **kwargs):
    cache_key = f'board_{instance.id}_detail'
    cache.delete(cache_key)
```

## 12. Prochaines Étapes

### 12.1 Phase 1 - Implémentation de base (Semaines 1-3)
1. Création des modèles de base
2. Interface Kanban simple
3. CRUD des boards et tâches
4. Système de permissions

### 12.2 Phase 2 - Fonctionnalités avancées (Semaines 4-6)
1. Drag & Drop fonctionnel
2. API REST complète
3. Templates de boards
4. Intégration avec les compétitions

### 12.3 Phase 3 - Optimisations (Semaines 7-8)
1. Notifications en temps réel
2. Rapports et analytics
3. Export/Import de données
4. Tests complets

Ce guide fournit une base solide pour l'implémentation du module Kanban dans MartialComp, en respectant l'architecture existante et en s'intégrant parfaitement avec les autres modules de la plateforme.
