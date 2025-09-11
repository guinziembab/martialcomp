from django.urls import path, include
from . import views

app_name = 'task_management'

urlpatterns = [
    # Board URLs
    path('', views.board_list, name='board_list'),
    path('boards/', views.board_list, name='board_list'),
    path('boards/create/', views.board_create, name='board_create'),
    path('boards/create-from-template/<int:template_id>/', views.board_create_from_template, name='board_create_from_template'),
    path('boards/<int:board_id>/', views.board_detail, name='board_detail'),
    path('boards/<int:board_id>/edit/', views.board_edit, name='board_edit'),
    path('boards/<int:board_id>/archive/', views.board_archive, name='board_archive'),
    path('boards/<int:board_id>/delete/', views.board_delete, name='board_delete'),
    path('boards/<int:board_id>/export/', views.board_export, name='board_export'),
    
    # Column management
    path('boards/<int:board_id>/columns/', views.board_columns, name='board_columns'),
    path('boards/<int:board_id>/columns/update-positions/', views.column_update_position, name='column_update_position'),
    path('boards/<int:board_id>/columns/<int:column_id>/delete/', views.column_delete, name='column_delete'),
    
    # Kanban interface
    path('boards/<int:board_id>/kanban/', views.kanban_view, name='kanban_view'),
    path('boards/<int:board_id>/kanban/fullscreen/', views.kanban_fullscreen, name='kanban_fullscreen'),
    path('boards/<int:board_id>/kanban/move-task/', views.kanban_move_task, name='kanban_move_task'),
    path('boards/<int:board_id>/kanban/stats/', views.kanban_board_stats, name='kanban_board_stats'),
    path('boards/<int:board_id>/kanban/auto-refresh/', views.kanban_auto_refresh, name='kanban_auto_refresh'),
    path('boards/<int:board_id>/columns/<int:column_id>/wip/', views.kanban_update_column_wip, name='kanban_update_column_wip'),
    
    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/my-tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/quick-create/', views.task_quick_create, name='task_quick_create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/move/', views.task_move, name='task_move'),
    path('tasks/<int:task_id>/status/', views.task_update_status, name='task_update_status'),
    path('tasks/<int:task_id>/priority/', views.task_update_priority, name='task_update_priority'),
    path('tasks/<int:task_id>/comment/', views.task_add_comment, name='task_add_comment'),
    path('tasks/<int:task_id>/card/', views.kanban_task_card, name='kanban_task_card'),
]