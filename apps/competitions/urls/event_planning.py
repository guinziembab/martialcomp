from django.urls import path
from apps.competitions.views.event_planning import poll_list, create_poll

app_name = 'event_planning'

urlpatterns = [
    # Liste des sondages
    path('polls/', poll_list, name='poll_list'),
    path('', poll_list, name='poll_list'),  # Alias
    
    # Créer un sondage
    path('polls/create/', create_poll, name='create_poll'),
]

