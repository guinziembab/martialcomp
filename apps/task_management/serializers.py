from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Board, Column, Task, TaskComment, TaskAssignment, BoardTemplate

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in task management context"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'full_name', 'email']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization information"""
    
    class Meta:
        model = None  # Will be set dynamically
        fields = ['id', 'name', 'organization_type']
        read_only_fields = ['id', 'name', 'organization_type']


class ColumnSerializer(serializers.ModelSerializer):
    """Serializer for board columns"""
    task_count = serializers.IntegerField(read_only=True)
    wip_status = serializers.CharField(read_only=True)
    is_over_wip_limit = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Column
        fields = [
            'id', 'name', 'position', 'color', 'wip_limit', 
            'is_done_column', 'created_at', 'task_count', 
            'wip_status', 'is_over_wip_limit'
        ]
        read_only_fields = ['id', 'created_at', 'task_count', 'wip_status', 'is_over_wip_limit']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['task_count'] = instance.task_count
        data['wip_status'] = instance.get_wip_status()
        data['is_over_wip_limit'] = instance.is_over_wip_limit
        return data


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for task assignments"""
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True)
    assigned_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'assignee', 'assignee_id', 'assigned_by', 'role', 
            'assigned_at', 'is_active', 'notify_on_updates', 
            'notify_on_comments', 'notify_on_due_date'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at']


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments"""
    author = UserSerializer(read_only=True)
    is_reply = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskComment
        fields = [
            'id', 'content', 'author', 'created_at', 'updated_at', 
            'is_edited', 'parent_comment', 'is_reply', 'can_edit'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_edited']
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_edit(request.user)


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks"""
    created_by = UserSerializer(read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)
    assignments = TaskAssignmentSerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    subtasks = serializers.SerializerMethodField()
    
    # Computed fields
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    assignee_count = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    priority_color = serializers.CharField(source='get_priority_color', read_only=True)
    status_color = serializers.CharField(source='get_status_color', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'board', 'column', 'column_name', 
            'board_name', 'priority', 'status', 'due_date', 'start_date', 
            'completed_at', 'created_by', 'created_at', 'updated_at', 
            'position', 'estimated_hours', 'time_spent', 'parent_task', 
            'attachments', 'labels', 'custom_fields', 'assignments', 
            'comments', 'subtasks', 'is_overdue', 'days_until_due', 
            'progress_percentage', 'assignee_count', 'can_edit',
            'priority_color', 'status_color'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'completed_at',
            'column_name', 'board_name', 'is_overdue', 'days_until_due',
            'assignee_count', 'can_edit', 'priority_color', 'status_color'
        ]
    
    def get_subtasks(self, obj):
        if obj.subtasks.exists():
            return TaskSerializer(
                obj.subtasks.all(), 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_edit(request.user)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_overdue'] = instance.is_overdue
        data['days_until_due'] = instance.days_until_due
        data['assignee_count'] = instance.assignee_count
        return data


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for task creation and updates"""
    assignee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'column', 'priority', 'status',
            'due_date', 'start_date', 'estimated_hours', 'labels',
            'parent_task', 'assignee_ids'
        ]
    
    def create(self, validated_data):
        assignee_ids = validated_data.pop('assignee_ids', [])
        task = super().create(validated_data)
        
        # Create assignments
        for assignee_id in assignee_ids:
            try:
                assignee = User.objects.get(id=assignee_id)
                TaskAssignment.objects.create(
                    task=task,
                    assignee=assignee,
                    assigned_by=self.context['request'].user,
                    role=TaskAssignment.AssignmentRole.ASSIGNEE
                )
            except User.DoesNotExist:
                pass
        
        return task
    
    def update(self, instance, validated_data):
        assignee_ids = validated_data.pop('assignee_ids', None)
        task = super().update(instance, validated_data)
        
        # Update assignments if provided
        if assignee_ids is not None:
            # Remove old assignments
            task.assignments.all().delete()
            
            # Create new assignments
            for assignee_id in assignee_ids:
                try:
                    assignee = User.objects.get(id=assignee_id)
                    TaskAssignment.objects.create(
                        task=task,
                        assignee=assignee,
                        assigned_by=self.context['request'].user,
                        role=TaskAssignment.AssignmentRole.ASSIGNEE
                    )
                except User.DoesNotExist:
                    pass
        
        return task


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards"""
    organization = OrganizationSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    columns = ColumnSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    
    # Computed fields
    task_count = serializers.IntegerField(read_only=True)
    completed_task_count = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    can_access = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = Board
        fields = [
            'id', 'name', 'description', 'organization', 'board_type',
            'related_competition', 'created_by', 'created_at', 'updated_at',
            'is_template', 'is_archived', 'color_theme', 'is_public',
            'allowed_roles', 'enable_time_tracking', 'enable_comments',
            'enable_attachments', 'columns', 'tasks', 'task_count',
            'completed_task_count', 'progress_percentage', 'can_access',
            'can_edit', 'can_admin'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'task_count',
            'completed_task_count', 'progress_percentage', 'can_access',
            'can_edit', 'can_admin'
        ]
    
    def get_progress_percentage(self, obj):
        return obj.progress_percentage
    
    def get_can_access(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_access(request.user)
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_edit(request.user)
    
    def get_can_admin(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        from .utils import check_board_access
        return check_board_access(request.user, obj, 'admin')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['task_count'] = instance.task_count
        data['completed_task_count'] = instance.completed_task_count
        return data


class BoardCreateUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for board creation and updates"""
    
    class Meta:
        model = Board
        fields = [
            'name', 'description', 'organization', 'board_type',
            'related_competition', 'is_public', 'allowed_roles',
            'color_theme', 'enable_time_tracking', 'enable_comments',
            'enable_attachments'
        ]
    
    def validate(self, data):
        # Validate competition relation for competition boards
        if data.get('board_type') == 'competition' and not data.get('related_competition'):
            raise serializers.ValidationError({
                'related_competition': 'Une compétition doit être sélectionnée pour ce type de tableau.'
            })
        
        return data


class BoardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for board templates"""
    created_by = UserSerializer(read_only=True)
    default_columns = serializers.SerializerMethodField()
    default_tasks_list = serializers.SerializerMethodField()
    
    class Meta:
        model = BoardTemplate
        fields = [
            'id', 'name', 'description', 'board_type', 'columns_config',
            'default_tasks', 'is_system_template', 'is_public', 'created_by',
            'created_at', 'updated_at', 'usage_count', 'color_scheme',
            'icon', 'default_columns', 'default_tasks_list'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'usage_count',
            'default_columns', 'default_tasks_list'
        ]
    
    def get_default_columns(self, obj):
        return obj.get_default_columns()
    
    def get_default_tasks_list(self, obj):
        return obj.get_default_tasks()


class TaskMoveSerializer(serializers.Serializer):
    """Serializer for task movement operations"""
    column_id = serializers.IntegerField()
    position = serializers.IntegerField(required=False, default=0)
    
    def validate_column_id(self):
        column_id = self.validated_data['column_id']
        task = self.context['task']
        
        try:
            column = Column.objects.get(id=column_id, board=task.board)
            return column_id
        except Column.DoesNotExist:
            raise serializers.ValidationError("Colonne invalide pour ce tableau.")


class BoardStatsSerializer(serializers.Serializer):
    """Serializer for board statistics"""
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_completion_time = serializers.DurationField(allow_null=True)
    tasks_by_priority = serializers.DictField()
    tasks_by_status = serializers.DictField()


class KanbanBoardSerializer(serializers.Serializer):
    """Specialized serializer for Kanban board view"""
    board = BoardSerializer(read_only=True)
    columns = serializers.SerializerMethodField()
    filters_applied = serializers.DictField(read_only=True)
    
    def get_columns(self, obj):
        """Return columns with filtered tasks"""
        board = obj['board']
        filters = obj.get('filters', {})
        
        columns_data = []
        for column in board.columns.all().order_by('position'):
            tasks = column.tasks.all()
            
            # Apply filters
            if filters.get('status'):
                tasks = tasks.filter(status=filters['status'])
            if filters.get('priority'):
                tasks = tasks.filter(priority=filters['priority'])
            if filters.get('assignee'):
                tasks = tasks.filter(assignments__assignee_id=filters['assignee'])
            if filters.get('overdue'):
                from django.utils import timezone
                tasks = tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['todo', 'in_progress', 'in_review']
                )
            
            column_data = ColumnSerializer(column).data
            column_data['tasks'] = TaskSerializer(
                tasks.order_by('position', 'created_at'),
                many=True,
                context=self.context
            ).data
            column_data['filtered_task_count'] = tasks.count()
            
            columns_data.append(column_data)
        
        return columns_data


# Set organization model dynamically if available
try:
    from apps.organizations.models import Organization
    OrganizationSerializer.Meta.model = Organization
except ImportError:
    pass