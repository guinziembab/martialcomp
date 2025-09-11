from django.urls import path
from apps.competitions.views.notifications import (
    notifications_list,
    notifications_api_list,
    mark_notification_read,
    mark_all_read,
    create_test_notifications
)

app_name = 'notifications'

urlpatterns = [
    path('', notifications_list, name='list'),
    path('api/', notifications_api_list, name='api_list'),
    path('mark-read/<int:notification_id>/', mark_notification_read, name='mark_read'),
    path('mark-all-read/', mark_all_read, name='mark_all_read'),
    path('create-test/', create_test_notifications, name='create_test'),
]

