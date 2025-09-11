from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class FinanceDashboardView(APIView):
    """Minimal finance dashboard for mobile Phase 0.

    Returns placeholder KPIs with safe fallbacks.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        balance = 0
        revenue = 0
        expenses = 0
        invoices_pending = 0

        # Best-effort: attempt to compute simple KPIs if models exist
        try:
            from apps.finances.models.invoices import Invoice  # type: ignore
            invoices_pending = Invoice.objects.filter(status='pending').count()
        except Exception:
            pass

        try:
            from apps.finances.models.transactions import Transaction  # type: ignore
            revenue = Transaction.objects.filter(amount__gt=0).count()
            expenses = Transaction.objects.filter(amount__lt=0).count()
        except Exception:
            pass

        return Response({
            'balance': balance,
            'revenue': revenue,
            'expenses': expenses,
            'invoices_pending': invoices_pending,
        })


# Local URLConf to allow include('apps.finances.api')
from django.urls import path  # noqa: E402
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

urlpatterns = [
    path('dashboard/', FinanceDashboardView.as_view(), name='finances_dashboard_api'),
]
