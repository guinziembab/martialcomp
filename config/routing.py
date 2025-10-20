"""
Routing principal pour WebSocket
"""
from django.urls import re_path, path

from apps.competitions import consumers

websocket_urlpatterns = [
    # WebSocket pour notation technique en temps réel
    re_path(r'ws/competition/(?P<competition_id>\d+)/technical/$', consumers.TechnicalScoringConsumer.as_asgi()),
    
    # WebSocket pour combat en temps réel
    re_path(r'ws/competition/(?P<competition_id>\d+)/combat/(?P<combat_id>\d+)/$', consumers.CombatConsumer.as_asgi()),
    
    # WebSocket pour dashboard live général
    re_path(r'ws/competition/(?P<competition_id>\d+)/dashboard/$', consumers.DashboardConsumer.as_asgi()),
]