from django.core.exceptions import PermissionDenied
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path, include

from .api import (
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
    BoardViewSet, TaskViewSet, ColumnViewSet, 
    TaskCommentViewSet, BoardTemplateViewSet
)

# Main router
router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'templates', BoardTemplateViewSet, basename='template')

# Nested routers for board-specific resources
boards_router = routers.NestedDefaultRouter(router, r'boards', lookup='board')
boards_router.register(r'columns', ColumnViewSet, basename='board-columns')
boards_router.register(r'tasks', TaskViewSet, basename='board-tasks')

# Nested router for task-specific resources
tasks_router = routers.NestedDefaultRouter(router, r'tasks', lookup='task')
tasks_router.register(r'comments', TaskCommentViewSet, basename='task-comments')

app_name = 'task_management_api'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(boards_router.urls)),
    path('', include(tasks_router.urls)),
]