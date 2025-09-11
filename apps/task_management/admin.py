from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Board, Column, Task, TaskComment, 
    TaskAssignment, BoardTemplate
)


class ColumnInline(admin.TabularInline):
    """Inline admin for board columns"""
    model = Column
    extra = 0
    fields = ['name', 'position', 'color', 'wip_limit', 'is_done_column']
    ordering = ['position']


class TaskInline(admin.TabularInline):
    """Inline admin for board tasks"""
    model = Task
    extra = 0
    fields = ['title', 'column', 'status', 'priority', 'due_date']
    readonly_fields = ['created_at']
    ordering = ['column__position', 'position']


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin interface for Board model"""
    list_display = [
        'name', 'organization', 'board_type', 'task_count_display', 
        'is_public', 'is_archived', 'created_at'
    ]
    list_filter = [
        'board_type', 'is_public', 'is_archived', 
        'organization', 'created_at'
    ]
    search_fields = ['name', 'description', 'organization__name']
    readonly_fields = ['created_at', 'updated_at', 'task_count_display', 'progress_display']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'description', 'board_type', 'color_theme')
        }),
        (_('Organisation'), {
            'fields': ('organization', 'related_competition')
        }),
        (_('Paramètres'), {
            'fields': (
                'is_public', 'is_archived', 'is_template',
                'allowed_roles', 'enable_time_tracking', 
                'enable_comments', 'enable_attachments'
            )
        }),
        (_('Métadonnées'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('task_count_display', 'progress_display'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ColumnInline, TaskInline]
    
    def task_count_display(self, obj):
        """Display task count with link"""
        count = obj.task_count
        if count > 0:
            url = reverse('admin:task_management_task_changelist') + f'?board__id__exact={obj.id}'
            return format_html('<a href="{}">{} tâches</a>', url, count)
        return '0 tâches'
    task_count_display.short_description = _('Nombre de tâches')
    
    def progress_display(self, obj):
        """Display progress bar"""
        progress = obj.progress_percentage
        color = 'success' if progress == 100 else 'info' if progress > 50 else 'warning'
        return format_html(
            '<div class="progress" style="width: 100px;">'
            '<div class="progress-bar bg-{}" style="width: {}%">{:.1f}%</div>'
            '</div>',
            color, progress, progress
        )
    progress_display.short_description = _('Progression')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'created_by', 'related_competition'
        ).prefetch_related('tasks')


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """Admin interface for Column model"""
    list_display = ['name', 'board', 'position', 'color_display', 'wip_status', 'task_count']
    list_filter = ['board', 'is_done_column']
    search_fields = ['name', 'board__name']
    ordering = ['board', 'position']
    
    def color_display(self, obj):
        """Display color as a colored square"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; '
            'border: 1px solid #ddd; display: inline-block;"></div> {}',
            obj.color, obj.color
        )
    color_display.short_description = _('Couleur')
    
    def wip_status(self, obj):
        """Display WIP status"""
        if not obj.wip_limit:
            return '-'
        
        status = obj.get_wip_status()
        colors = {
            'under_limit': 'success',
            'at_limit': 'warning', 
            'over_limit': 'danger'
        }
        color = colors.get(status, 'secondary')
        
        return format_html(
            '<span class="badge badge-{}">{}/{}</span>',
            color, obj.task_count, obj.wip_limit
        )
    wip_status.short_description = _('WIP')


class TaskAssignmentInline(admin.TabularInline):
    """Inline admin for task assignments"""
    model = TaskAssignment
    extra = 0
    fields = ['assignee', 'role', 'assigned_by', 'is_active']


class TaskCommentInline(admin.TabularInline):
    """Inline admin for task comments"""
    model = TaskComment
    extra = 0
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model"""
    list_display = [
        'title', 'board', 'column', 'status_display', 'priority_display',
        'assignee_display', 'due_date', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'board__organization', 'board', 
        'column', 'due_date', 'created_at'
    ]
    search_fields = ['title', 'description', 'board__name']
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at', 
        'progress_display', 'is_overdue'
    ]
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('title', 'description', 'board', 'column')
        }),
        (_('Statut et priorité'), {
            'fields': ('status', 'priority', 'position')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'due_date', 'completed_at')
        }),
        (_('Suivi du temps'), {
            'fields': ('estimated_hours', 'time_spent'),
            'classes': ('collapse',)
        }),
        (_('Hiérarchie'), {
            'fields': ('parent_task',),
            'classes': ('collapse',)
        }),
        (_('Données additionnelles'), {
            'fields': ('labels', 'attachments', 'custom_fields'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TaskAssignmentInline, TaskCommentInline]
    
    def status_display(self, obj):
        """Display status with color"""
        color = obj.get_status_color()
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('Statut')
    
    def priority_display(self, obj):
        """Display priority with color"""
        color = obj.get_priority_color()
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = _('Priorité')
    
    def assignee_display(self, obj):
        """Display assignees"""
        assignees = obj.get_assignees()
        if not assignees:
            return '-'
        
        if len(assignees) == 1:
            return assignees[0].get_full_name()
        else:
            return f"{assignees[0].get_full_name()} +{len(assignees)-1}"
    assignee_display.short_description = _('Assignés')
    
    def progress_display(self, obj):
        """Display progress if has subtasks"""
        if not obj.has_subtasks:
            return '-'
        
        progress = obj.get_progress_percentage()
        return format_html('{}%', progress)
    progress_display.short_description = _('Progression')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'board', 'column', 'created_by', 'parent_task'
        ).prefetch_related('assignments__assignee')


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin interface for TaskComment model"""
    list_display = ['task', 'author', 'content_preview', 'created_at', 'is_edited']
    list_filter = ['created_at', 'is_edited', 'task__board']
    search_fields = ['content', 'task__title', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'is_edited']
    
    def content_preview(self, obj):
        """Show content preview"""
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
    content_preview.short_description = _('Contenu')


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for TaskAssignment model"""
    list_display = ['task', 'assignee', 'role', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['role', 'is_active', 'assigned_at', 'task__board']
    search_fields = ['task__title', 'assignee__username', 'assignee__first_name', 'assignee__last_name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'task', 'assignee', 'assigned_by'
        )


@admin.register(BoardTemplate)
class BoardTemplateAdmin(admin.ModelAdmin):
    """Admin interface for BoardTemplate model"""
    list_display = [
        'name', 'board_type', 'is_system_template', 
        'is_public', 'usage_count', 'created_at'
    ]
    list_filter = ['board_type', 'is_system_template', 'is_public']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'description', 'board_type', 'icon')
        }),
        (_('Configuration'), {
            'fields': ('columns_config', 'default_tasks', 'color_scheme')
        }),
        (_('Paramètres'), {
            'fields': ('is_system_template', 'is_public')
        }),
        (_('Métadonnées'), {
            'fields': ('created_by', 'usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# Admin site customization
admin.site.site_header = "MartialComp - Gestion de Tâches"
admin.site.site_title = "Task Management"
admin.site.index_title = "Administration du module de gestion de tâches"