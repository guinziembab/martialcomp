from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class GradesListView(APIView):
    """Minimal grades API for mobile Phase 0.

    Returns a synthetic list of grades and the current grade of the user when available.
    Safe fallbacks ensure 200 even if models are missing or relations are not wired.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        grades = []
        current_grade = None

        # Try to load real grades if the app models are present
        try:
            from apps.grades.models import Grade  # type: ignore
            # Filtrage par organisation -> disciplines autorisées
            try:
                from apps.finances.currency_service import _get_request_organization  # type: ignore
                org = _get_request_organization(request)
            except Exception:
                org = None
            # Grade n'a pas de champ organization direct, utiliser discipline
            if org is not None and hasattr(org, 'disciplines'):
                allowed = list(org.disciplines.values_list('id', flat=True))
                if allowed:
                    qs = Grade.objects.filter(discipline_id__in=allowed)
                else:
                    qs = Grade.objects.none()
            else:
                # Fallback via isolation par discipline
                try:
                    from apps.core.isolation import get_organization_queryset
                    disciplines = get_organization_queryset(
                        getattr(__import__('apps.competitions.models', fromlist=['Discipline']), 'Discipline'),
                        request.user
                    )
                    qs = Grade.objects.filter(discipline__in=disciplines)
                except Exception:
                    qs = Grade.objects.all()
            for g in qs.order_by('level')[:100]:
                grades.append({
                    'id': getattr(g, 'id', None),
                    'name': getattr(g, 'name', None),
                    'level': getattr(g, 'level', None),
                    'color': getattr(g, 'color', None),
                    'discipline': getattr(getattr(g, 'discipline', None), 'name', None),
                })
        except Exception:
            # Return a tiny placeholder set if models are unavailable
            grades = [
                {'id': 'g1', 'name': 'Ceinture Blanche', 'level': 1, 'color': '#FFFFFF', 'discipline': 'Général'},
                {'id': 'g2', 'name': 'Ceinture Jaune', 'level': 2, 'color': '#FFFF00', 'discipline': 'Général'},
            ]

        # Try to infer current grade for the authenticated user (best-effort)
        try:
            from apps.grades.models import PractitionerGrade  # type: ignore
            # Heuristic: if a relation to practitioner exists on the user, use it; otherwise skip
            practitioner = getattr(request.user, 'practitioner', None)
            if practitioner is not None:
                pg = (
                    PractitionerGrade.objects
                    .filter(practitioner=practitioner)
                    .order_by('-date_obtained')
                    .first()
                )
                if pg and getattr(pg, 'grade', None):
                    g = pg.grade
                    current_grade = {
                        'id': getattr(g, 'id', None),
                        'name': getattr(g, 'name', None),
                        'level': getattr(g, 'level', None),
                        'color': getattr(g, 'color', None),
                    }
        except Exception:
            current_grade = None

        return Response({
            'grades': grades,
            'current_grade': current_grade,
        })


# Local URLConf to allow include('apps.grades.api')
from django.urls import path  # noqa: E402
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

urlpatterns = [
    path('', GradesListView.as_view(), name='grades_list_api'),
]
