# -*- coding: utf-8 -*-
"""
WebSocket Consumers de l'application Super Admin.
"""

from apps.superadmin.consumers.realtime import (
    MetricsConsumer,
    MapConsumer,
    LogsConsumer,
)

__all__ = [
    'MetricsConsumer',
    'MapConsumer',
    'LogsConsumer',
]
