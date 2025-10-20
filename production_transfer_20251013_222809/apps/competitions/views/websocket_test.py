"""
Vue de test pour WebSocket
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# @login_required  # Temporairement désactivé pour les tests
def websocket_test_view(request):
    """
    Vue pour tester la fonctionnalité WebSocket
    """
    context = {
        'page_title': 'Test WebSocket',
    }
    return render(request, 'competitions/websocket_test.html', context)