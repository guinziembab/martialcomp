from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q
from datetime import datetime

from .currency_service import (
    get_preferred_currency_for_request,
    get_rates,
    convert_amount,
    _get_request_organization,
)
from .drf_mixins import CurrencyAwareAPIView


class FinanceDashboardView(CurrencyAwareAPIView):
    """Minimal finance dashboard for mobile Phase 0.

    Returns placeholder KPIs with safe fallbacks.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        balance = 0.0
        revenue = 0.0
        expenses = 0.0
        invoices_pending = 0
        preferred_currency, currency_source = get_preferred_currency_for_request(request)

        # Organization context (best-effort)
        organization = None
        try:
            organization = _get_request_organization(request)
        except Exception:
            organization = None
        if organization is None:
            # Fallback: query param organizationId
            org_id = request.GET.get('organizationId') or request.GET.get('organization_id')
            if org_id:
                try:
                    from apps.organizations.models import Organization  # type: ignore
                    organization = Organization.objects.filter(pk=org_id).first()
                except Exception:
                    organization = None
        if organization is None:
            # Last resort: attribute on user (may not exist)
            organization = getattr(request.user, 'organization', None)

        # Pending invoices
        try:
            from apps.finances.models.invoices import Invoice  # type: ignore
            qs = get_organization_queryset(Invoice, self.request.user)
            # Optional: filter by organization if relation exists on Invoice
            if organization and hasattr(Invoice, 'organization'):
                qs = qs.filter(organization=organization)
            invoices_pending = qs.filter(status='pending').count()
        except Exception:
            invoices_pending = 0

        # Balances from FinancialAccount
        try:
            from apps.finances.models.accounts import FinancialAccount  # type: ignore
            if organization:
                ct = ContentType.objects.get_for_model(organization.__class__)
                owner_id = str(getattr(organization, 'id', ''))
                agg = (
                    FinancialAccount.objects
                    .filter(owner_content_type=ct, owner_id=owner_id)
                    .aggregate(total=Sum('current_balance'))
                )
                balance = float(agg['total'] or 0)
            else:
                agg = FinancialAccount.objects.aggregate(total=Sum('current_balance'))
                balance = float(agg['total'] or 0)
        except Exception:
            balance = 0.0

        # Revenue/Expenses from Transaction (validated sums)
        try:
            from apps.finances.models.transactions import Transaction  # type: ignore
            tx = Transaction.objects.filter(status='validated')
            # If transactions relate to organization via financial_account owner, limit by org accounts when possible
            if organization and hasattr(Transaction, 'financial_account'):
                from apps.finances.models.accounts import FinancialAccount  # type: ignore
                ct = ContentType.objects.get_for_model(organization.__class__)
                owner_id = str(getattr(organization, 'id', ''))
                org_accounts = FinancialAccount.objects.filter(owner_content_type=ct, owner_id=owner_id).values('pk')
                tx = tx.filter(Q(financial_account__in=org_accounts))

            rev = tx.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
            exp = tx.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
            revenue = float(rev)
            expenses = float(exp)
        except Exception:
            revenue = revenue or 0.0
            expenses = expenses or 0.0

        # Convert numeric KPIs to preferred currency if they are denominated in a different base (assumed EUR)
        # We assume stored values are in the account/transaction currency; for now convert from EUR for display.
        try:
            display_balance, _ = convert_amount(balance, 'EUR', preferred_currency)
            display_revenue, _ = convert_amount(revenue, 'EUR', preferred_currency)
            display_expenses, _ = convert_amount(expenses, 'EUR', preferred_currency)
        except Exception:
            display_balance, display_revenue, display_expenses = balance, revenue, expenses

        return Response({
            'balance': display_balance,
            'revenue': display_revenue,
            'expenses': display_expenses,
            'invoices_pending': invoices_pending,
            'currency': preferred_currency,
            'currency_source': currency_source,
        })


# Local URLConf to allow include('apps.finances.rest_api')
from django.urls import path  # noqa: E402

urlpatterns = [
    path('dashboard/', FinanceDashboardView.as_view(), name='finances_dashboard_api'),
]


class CurrencyPreferredView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        code, source = get_preferred_currency_for_request(request)
        return Response({
            'currency': code,
            'source': source,
        })


class CurrencyRatesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        base = request.GET.get('base')
        base_code, rates, updated_at = get_rates(base=base)
        return Response({
            'base': base_code,
            'rates': rates,
            'updated_at': updated_at.isoformat() + 'Z',
        })


class CurrencyConvertView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        try:
            amount = float(request.data.get('amount', 0))
            from_currency = str(request.data.get('from', 'EUR')).upper()
            to_currency = str(request.data.get('to', 'EUR')).upper()
            converted, rate = convert_amount(amount, from_currency, to_currency)
            return Response({
                'amount': amount,
                'from': from_currency,
                'to': to_currency,
                'converted': converted,
                'rate': rate,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)


# Add currency endpoints under finances namespace for simplicity
urlpatterns += [
    path('currency/preferred/', CurrencyPreferredView.as_view(), name='currency_preferred_api'),
    path('currency/rates/',     CurrencyRatesView.as_view(),     name='currency_rates_api'),
    path('currency/convert/',   CurrencyConvertView.as_view(),   name='currency_convert_api'),
]


# ==============================
# Payments listing (mobile v0)
# ==============================
from rest_framework import status as drf_status  # noqa: E402
from django.core.paginator import Paginator  # noqa: E402
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


def _map_transaction_status_to_payment_status(tx_status: str) -> str:
    mapping = {
        'validated': 'completed',
        'pending': 'pending',
        'refunded': 'refunded',
        'cancelled': 'cancelled',
        'rejected': 'failed',
    }
    return mapping.get(tx_status, 'pending')


class PaymentsListView(APIView):
    """Return a paginated list of payments based on Transaction model.

    Supports filters used by the mobile app via query params:
    - status: pending|completed|failed|cancelled|refunded
    - method: payment method id or type (best-effort)
    - dateFrom, dateTo: ISO date (YYYY-MM-DD)
    - amountMin, amountMax: numbers
    - query: full-text on description/reference
    - page, limit: pagination

    Also supports:
    - stats=true: returns aggregate stats
    - summary=true: returns totals summary
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from apps.finances.models.transactions import Transaction  # lazy import

        # Resolve organization context once (header, domain, or query param)
        organization = None
        try:
            organization = _get_request_organization(request)
        except Exception:
            organization = None
        if organization is None:
            org_id_param = request.GET.get('organizationId') or request.GET.get('organization_id')
            if org_id_param:
                try:
                    from apps.organizations.models import Organization  # type: ignore
                    organization = Organization.objects.filter(pk=org_id_param).first()
                except Exception:
                    organization = None

        def scope_by_org(qs):
            if not organization:
                return qs
            try:
                from apps.finances.models.accounts import FinancialAccount  # type: ignore
                ct = ContentType.objects.get_for_model(organization.__class__)
                owner_id = str(getattr(organization, 'id', ''))
                org_accounts = FinancialAccount.objects.filter(
                    owner_content_type=ct, owner_id=owner_id
                ).values('pk')
                return qs.filter(Q(financial_account__in=org_accounts))
            except Exception:
                return qs

        # Stats only
        if request.GET.get('stats') == 'true':
            qs = scope_by_org(get_organization_queryset(Transaction, self.request.user))
            try:
                total_amount = float(qs.aggregate(Sum('amount'))['amount__sum'] or 0)
            except Exception:
                total_amount = 0.0
            stats = {
                'totalPayments': qs.count(),
                'completedPayments': qs.filter(status='validated').count(),
                'pendingPayments': qs.filter(status='pending').count(),
                'failedPayments': qs.filter(status='rejected').count(),
                'totalAmount': total_amount,
                'averageAmount': float((total_amount / qs.count()) if qs.count() else 0),
                'currency': 'EUR',
            }
            return Response(stats)

        # Summary only
        if request.GET.get('summary') == 'true':
            qs = scope_by_org(get_organization_queryset(Transaction, self.request.user))
            try:
                total_amount = float(qs.aggregate(Sum('amount'))['amount__sum'] or 0)
            except Exception:
                total_amount = 0.0
            return Response({
                'total': qs.count(),
                'totalAmount': total_amount,
                'currency': 'EUR',
            })

        # Base queryset
        qs = scope_by_org(get_organization_queryset(Transaction, self.request.user).select_related('payment_method'))
        # Note: additional org_id param is no-op if organization was resolved; kept for compatibility

        # Filters
        status_param = request.GET.get('status')
        if status_param:
            # map reverse: payment status -> tx status
            reverse_status_map = {
                'completed': 'validated',
                'pending': 'pending',
                'refunded': 'refunded',
                'cancelled': 'cancelled',
                'failed': 'rejected',
            }
            tx_status = reverse_status_map.get(status_param)
            if tx_status:
                qs = qs.filter(status=tx_status)

        method_param = request.GET.get('method')
        if method_param:
            qs = qs.filter(
                Q(payment_method__id__iexact=method_param)
                | Q(payment_method__type__iexact=method_param)
            )

        type_param = request.GET.get('type')
        if type_param:
            # We do not have granular payment types; best-effort via transaction type
            if type_param == 'refund':
                qs = qs.filter(status='refunded')
            elif type_param in ('income', 'expense'):
                qs = qs.filter(type=type_param)

        date_from = request.GET.get('dateFrom') or request.GET.get('startDate') or request.GET.get('start_date')
        date_to = request.GET.get('dateTo') or request.GET.get('endDate') or request.GET.get('end_date')
        if date_from:
            try:
                qs = qs.filter(date__gte=date_from)
            except Exception:
                pass
        if date_to:
            try:
                qs = qs.filter(date__lte=date_to)
            except Exception:
                pass

        amount_min = request.GET.get('amountMin')
        amount_max = request.GET.get('amountMax')
        if amount_min:
            try:
                qs = qs.filter(amount__gte=float(amount_min))
            except Exception:
                pass
        if amount_max:
            try:
                qs = qs.filter(amount__lte=float(amount_max))
            except Exception:
                pass

        query = request.GET.get('query')
        if query:
            qs = qs.filter(Q(description__icontains=query) | Q(reference__icontains=query))

        # Pagination
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        try:
            limit = int(request.GET.get('limit', '20'))
        except ValueError:
            limit = 20

        paginator = Paginator(qs.order_by('-date_created'), limit)
        page_obj = paginator.get_page(page)

        def map_tx(tx):
            return {
                'id': str(tx.id),
                'amount': float(tx.amount),
                'currency': tx.currency or 'EUR',
                'status': _map_transaction_status_to_payment_status(tx.status),
                'type': 'other',
                'method': (getattr(tx.payment_method, 'type', None) or 'other'),
                'description': tx.description or '',
                'reference': tx.reference or '',
                'payer': getattr(getattr(tx, 'created_by', None), 'username', '') or '',
                'payee': '',
                'metadata': tx.metadata or {},
                'totalAmount': float(tx.amount),
                'createdAt': tx.date_created.isoformat().replace('+00:00', 'Z') if tx.date_created else None,
                'updatedAt': tx.date_updated.isoformat().replace('+00:00', 'Z') if tx.date_updated else None,
            }

        payments = [map_tx(tx) for tx in page_obj.object_list]

        try:
            total_amount_all = float(qs.aggregate(Sum('amount'))['amount__sum'] or 0)
        except Exception:
            total_amount_all = 0.0

        data = {
            'payments': payments,
            'total': qs.count(),
            'totalAmount': total_amount_all,
            'currency': 'EUR',
            'hasMore': page_obj.has_next(),
        }

        return Response(data, status=drf_status.HTTP_200_OK)


# Register the payments endpoint
urlpatterns += [
    path('payments/', PaymentsListView.as_view(), name='finances_payments_list'),
]
