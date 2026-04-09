# -*- coding: utf-8 -*-
"""
Routage WebSocket pour Super Admin.
"""

from django.urls import re_path
from apps.superadmin.consumers import (
    SuperAdminConsumer,
    LogsStreamConsumer,
)

websocket_urlpatterns = [
    re_path(r'ws/superadmin/dashboard/$', SuperAdminConsumer.as_asgi()),
    re_path(r'ws/superadmin/logs/$', LogsStreamConsumer.as_asgi()),
]
