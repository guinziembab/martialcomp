from django import template
from django.utils.translation import gettext_lazy as _
from ..permissions import (
    has_task_management_access, check_board_access, 
    get_subscription_limits, check_feature_flag
)

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


@register.filter
def has_feature(user, feature_name):
    """Template filter to check feature flag access"""
    return check_feature_flag(user, feature_name)


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


@register.simple_tag
def get_user_limits(user, organization=None):
    """Template tag to get subscription limits"""
    return get_subscription_limits(user, organization)


@register.inclusion_tag('task_management/tags/feature_limit_warning.html')
def show_feature_limit_warning(user, feature, current_count=None, organization=None):
    """Template tag to show feature limit warnings"""
    limits = get_subscription_limits(user, organization)
    
    warning_data = {
        'show_warning': False,
        'feature': feature,
        'current_count': current_count,
        'limit': 0,
        'percentage': 0,
        'tier_upgrade_needed': False,
    }
    
    if feature == 'boards':
        limit = limits['max_boards']
        if limit > 0 and current_count is not None:
            percentage = (current_count / limit) * 100
            warning_data.update({
                'show_warning': percentage >= 80,  # Show at 80%
                'limit': limit,
                'percentage': percentage,
                'tier_upgrade_needed': current_count >= limit,
            })
    elif feature == 'tasks':
        limit = limits['max_tasks_per_board']
        if limit > 0 and current_count is not None:
            percentage = (current_count / limit) * 100
            warning_data.update({
                'show_warning': percentage >= 80,
                'limit': limit,
                'percentage': percentage,
                'tier_upgrade_needed': current_count >= limit,
            })
    
    return warning_data


@register.simple_tag
def board_creation_allowed(user, organization):
    """Check if user can create more boards"""
    from ..permissions import check_board_creation_limit
    return check_board_creation_limit(user, organization)


@register.simple_tag
def task_creation_allowed(board):
    """Check if more tasks can be created in board"""
    from ..permissions import check_task_creation_limit
    return check_task_creation_limit(board)


@register.inclusion_tag('task_management/tags/subscription_badge.html')
def show_subscription_badge(user, organization=None):
    """Show subscription tier badge"""
    limits = get_subscription_limits(user, organization)
    
    # Determine tier based on limits
    if limits['max_boards'] == 0:
        tier = 'free'
        tier_display = str(_('Gratuit'))
        tier_class = 'secondary'
    else:
        tier = 'premium'
        tier_display = str(_('Premium'))
        tier_class = 'success'
    
    return {
        'tier': tier,
        'tier_display': tier_display,
        'tier_class': tier_class,
        'limits': limits,
    }