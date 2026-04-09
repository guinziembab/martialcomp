from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from functools import wraps

from .models import Board, Task
from .utils import check_board_access


def task_management_required(view_func):
    """
    Decorator to check if user has access to task management feature
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not has_task_management_access(request.user):
            raise PermissionDenied("Accès au module de gestion de tâches requis")
        return view_func(request, *args, **kwargs)
    
    return wrapper


def board_access_required(permission_level='view'):
    """
    Decorator to check board access permissions
    
    Args:
        permission_level: 'view', 'edit', or 'admin'
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, board_id=None, *args, **kwargs):
            if not board_id:
                # Try to get board_id from kwargs
                board_id = kwargs.get('board_id')
            
            if not board_id:
                raise Http404("Board ID required")
            
            board = get_object_or_404(Board, id=board_id)
            
            if not check_board_access(request.user, board, permission_level):
                raise PermissionDenied(f"Permission {permission_level} required for this board")
            
            # Add board to kwargs for the view
            kwargs['board'] = board
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def task_edit_required(view_func):
    """
    Decorator to check task edit permissions
    """
    @wraps(view_func)
    def wrapper(request, task_id=None, *args, **kwargs):
        if not task_id:
            task_id = kwargs.get('task_id')
        
        if not task_id:
            raise Http404("Task ID required")
        
        task = get_object_or_404(Task, id=task_id)
        
        if not task.can_edit(request.user):
            raise PermissionDenied("Permission to edit this task required")
        
        kwargs['task'] = task
        return view_func(request, *args, **kwargs)
    
    return wrapper


class TaskManagementMixin(LoginRequiredMixin):
    """
    Mixin to check task management access for class-based views
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not has_task_management_access(request.user):
            raise PermissionDenied("Accès au module de gestion de tâches requis")
        return super().dispatch(request, *args, **kwargs)


class BoardAccessMixin(TaskManagementMixin):
    """
    Mixin to check board access permissions for class-based views
    """
    permission_level = 'view'  # Override in subclass
    
    def dispatch(self, request, *args, **kwargs):
        board_id = kwargs.get('board_id') or kwargs.get('pk')
        if board_id:
            self.board = get_object_or_404(Board, id=board_id)
            if not check_board_access(request.user, self.board, self.permission_level):
                raise PermissionDenied(f"Permission {self.permission_level} required")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'board'):
            context['board'] = self.board
            context['can_view'] = check_board_access(self.request.user, self.board, 'view')
            context['can_edit'] = check_board_access(self.request.user, self.board, 'edit')
            context['can_admin'] = check_board_access(self.request.user, self.board, 'admin')
        return context


def has_task_management_access(user):
    """
    Check if user has access to task management features
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superuser always has access
    if user.is_superuser:
        return True
    
    try:
        # Check if user has task management feature enabled
        return check_feature_flag(user, 'task_management')
    except:
        # Fallback to basic permission check
        return user.has_perm('task_management.view_board')


def check_feature_flag(user, feature_name):
    """
    Check if user has access to a specific feature
    
    This integrates with the subscription/feature flag system
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superuser bypass
    if user.is_superuser:
        return True
    
    try:
        # Try to use the existing feature flag system
        from apps.subscriptions.utils import user_has_feature
        return user_has_feature(user, feature_name)
    except ImportError:
        # Fallback implementation
        return check_subscription_tier_access(user, feature_name)


def check_subscription_tier_access(user, feature_name):
    """
    Fallback method to check subscription tier access
    """
    try:
        # Check if user is an external organizer (no organization membership)
        from apps.organizations.models import OrganizationMember
        memberships = OrganizationMember.objects.filter(
            user=user,
            is_active=True
        ).select_related('organization')
        
        # If user has no organization memberships, grant basic task management access
        # This covers external organizers and independent users
        if not memberships.exists():
            if feature_name == 'task_management':
                return True  # Grant basic access to external organizers
            else:
                return False  # Advanced features require organization membership
        
        for membership in memberships:
            org = membership.organization
            
            # Check organization's subscription tier
            if hasattr(org, 'subscription') and org.subscription:
                tier_name = getattr(org.subscription.tier, 'name', '').lower()
                
                # All features are available for all tiers (free + premium)
                return True
        
        return False
        
    except ImportError:
        # If no subscription system, default to basic access
        return True


def get_subscription_limits(user, organization=None):
    """
    Get subscription-based limits for task management features
    """
    try:
        from apps.organizations.models import OrganizationMember
        
        if organization:
            memberships = OrganizationMember.objects.filter(
                user=user,
                organization=organization,
                is_active=True
            )
        else:
            memberships = OrganizationMember.objects.filter(
                user=user,
                is_active=True
            ).select_related('organization')
        
        # Default limits
        limits = {
            'max_boards': 0,
            'max_tasks_per_board': 0,
            'enable_time_tracking': False,
            'enable_templates': False,
            'enable_api': False,
            'enable_export': False,
        }
        
        for membership in memberships:
            org = membership.organization
            
            if hasattr(org, 'subscription') and org.subscription:
                tier_name = getattr(org.subscription.tier, 'name', '').lower()
                
                # All tiers (free + premium) get full access
                limits.update({
                    'max_boards': 999,
                    'max_tasks_per_board': 999,
                    'enable_time_tracking': True,
                    'enable_templates': True,
                    'enable_api': True,
                    'enable_export': True,
                })
                
                break  # Use the first organization's limits
        
        return limits
        
    except ImportError:
        # Fallback to unlimited access
        return {
            'max_boards': 999,
            'max_tasks_per_board': 999,
            'enable_time_tracking': True,
            'enable_templates': True,
            'enable_api': True,
            'enable_export': True,
        }


def check_board_creation_limit(user, organization):
    """
    Check if user can create more boards in the organization
    """
    limits = get_subscription_limits(user, organization)
    current_count = Board.objects.filter(
        organization=organization,
        is_archived=False
    ).count()
    
    return current_count < limits['max_boards']


def check_task_creation_limit(board):
    """
    Check if more tasks can be created in the board
    """
    limits = get_subscription_limits(board.created_by, board.organization)
    current_count = board.tasks.count()
    
    return current_count < limits['max_tasks_per_board']


# Context processor for template access
def task_management_context(request):
    """
    Context processor to add task management permissions to all templates
    """
    if not request.user.is_authenticated:
        return {}
    
    return {
        'has_task_management': has_task_management_access(request.user),
        'task_management_limits': get_subscription_limits(request.user),
    }


# Template tags for permission checking
from django import template

register = template.Library()


@register.filter
def has_task_management(user):
    """Template filter to check task management access"""
    return has_task_management_access(user)


@register.filter
def can_access_board(user, board):
    """Template filter to check board access"""
    return board.can_access(user) if board else False


@register.filter
def can_edit_board(user, board):
    """Template filter to check board edit permission"""
    return board.can_edit(user) if board else False


@register.filter  
def can_edit_task(user, task):
    """Template filter to check task edit permission"""
    return task.can_edit(user) if task else False


@register.simple_tag
def board_access_level(user, board):
    """Template tag to get user's access level for board"""
    if not board or not user.is_authenticated:
        return 'none'
    
    if check_board_access(user, board, 'admin'):
        return 'admin'
    elif check_board_access(user, board, 'edit'):
        return 'edit'
    elif board.can_access(user):
        return 'view'
    else:
        return 'none'


@register.inclusion_tag('task_management/tags/feature_limit_warning.html')
def show_feature_limit_warning(user, feature, current_count=None):
    """Template tag to show feature limit warnings"""
    limits = get_subscription_limits(user)
    
    warning_data = {
        'show_warning': False,
        'feature': feature,
        'current_count': current_count,
        'limit': 0,
        'percentage': 0,
    }
    
    if feature == 'boards':
        limit = limits['max_boards']
        if limit > 0 and current_count is not None:
            warning_data.update({
                'show_warning': current_count >= limit * 0.8,  # Show at 80%
                'limit': limit,
                'percentage': (current_count / limit) * 100,
            })
    
    return warning_data