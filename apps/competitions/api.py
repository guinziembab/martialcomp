from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from apps.competitions.models.competitions import Competition
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class CompetitionListView(APIView, OrganizationIsolationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Isolation par organisation
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Filtrer les compétitions par organisation de l'utilisateur
        qs = get_organization_queryset(Competition, request.user)
        
        # Filtres supplémentaires
        if hasattr(Competition, 'is_published'):
            qs = qs.filter(is_published=True)
        if hasattr(Competition, 'start_date'):
            qs = qs.filter(start_date__gte=timezone.now()).order_by('start_date')
        
        competitions = [
            {
                'id': c.id,
                'name': getattr(c, 'name', ''),
                'start_date': getattr(c, 'start_date', None),
                'location': getattr(c, 'location', ''),
            }
            for c in qs[:10]
        ]
        user_regs = []
        # TODO: map registrations if model available
        return Response({'upcoming_competitions': competitions, 'user_registrations': user_regs})

from django.urls import path

urlpatterns = [
    path('upcoming/', CompetitionListView.as_view(), name='competitions_upcoming'),
]
