from django.urls import path, include
from apps.competitions.views.dashboard import (
    dashboard,
    admin_dashboard,
    club_dashboard,
    referee_dashboard,
    participant_dashboard,
    spectator_dashboard,
    dashboard_pro,
    manager_dashboard,
    federation_dashboard,
    combat_dashboard,
    coach_multidiscipline_dashboard,
    coach_dashboard,
)
# Import de la vue manquante
from apps.competitions.views.dashboard.coach_multidiscipline import coach_students_view
from apps.competitions.views.dashboard.external_organizer import dashboard_external_organizer
from apps.competitions.models import Federation
from django.contrib import messages
from django.shortcuts import redirect

app_name = 'dashboard'

def federation_dashboard_index(request):
    """Vue d'index pour /dashboard/federation/ : redirige vers la fédération administrée ou la liste."""
    user = request.user
    federation = Federation.objects.filter(owner=user).first() or Federation.objects.filter(administrators__user=user).first()
    if federation:
        from django.urls import reverse
        return redirect(reverse('competitions:federations:federation_dashboard', kwargs={'federation_id': federation.id}))
    else:
        messages.info(request, "Vous n'Ãªtes associé Ã  aucune fédération. Créez-en une pour commencer.")
        from django.urls import reverse
        return redirect(reverse('competitions:federations:list'))

urlpatterns = [
    path('', dashboard, name='home'),
    path('index/', dashboard, name='index'),  # Alias pour compatibilité
    path('admin/', admin_dashboard, name='admin'),
    path('club/', club_dashboard, name='club'),
    path('referee/', referee_dashboard, name='referee'),
    path('participant/', participant_dashboard, name='participant'),
    path('spectator/', spectator_dashboard, name='spectator'),
    path('pro/', dashboard_pro, name='pro'),
    path('manager/', manager_dashboard, name='manager'),
    path('federation/', federation_dashboard_index, name='federation'),
    path('combat/', combat_dashboard, name='combat'),
    path('coach/', coach_dashboard, name='coach'),  # Nouvelle vue coach
    path('coach-multidiscipline/', coach_multidiscipline_dashboard, name='coach_multidiscipline'),
    path('coach/students/', coach_students_view, name='coach_students'),
    path('external_organizer/', dashboard_external_organizer, name='external_organizer'),
    # Intégration du module de notation technique
    path('technical-scoring/', include('competitions.technical_scoring')),
]

