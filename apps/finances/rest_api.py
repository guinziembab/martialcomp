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
                # No organization - return 0 for data isolation
                balance = 0.0
        except Exception:
            balance = 0.0

        # Revenue/Expenses from Transaction (validated sums)
        try:
            from apps.finances.models.transactions import Transaction  # type: ignore
            # Only show data if organization is set - data isolation
            if organization:
                tx = Transaction.objects.filter(status='validated')
                # If transactions relate to organization via financial_account owner, limit by org accounts
                if hasattr(Transaction, 'financial_account'):
                    from apps.finances.models.accounts import FinancialAccount  # type: ignore
                    ct = ContentType.objects.get_for_model(organization.__class__)
                    owner_id = str(getattr(organization, 'id', ''))
                    org_accounts = FinancialAccount.objects.filter(owner_content_type=ct, owner_id=owner_id).values('pk')
                    tx = tx.filter(Q(financial_account__in=org_accounts))

                rev = tx.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
                exp = tx.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
                revenue = float(rev)
                expenses = float(exp)
            else:
                # No organization - return 0 for data isolation
                revenue = 0.0
                expenses = 0.0
        except Exception:
            revenue = 0.0
            expenses = 0.0

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


# =============================================================================
# EXTENDED CURRENCY API ENDPOINTS (Multi-devise Phase 4)
# =============================================================================

from decimal import Decimal, InvalidOperation  # noqa: E402
from rest_framework.permissions import AllowAny  # noqa: E402
from rest_framework import status as http_status  # noqa: E402
from django.utils import timezone  # noqa: E402

from .currency_service import (  # noqa: E402
    format_currency as fmt_currency,
    is_currency_supported,
    get_available_currencies as get_all_currencies,
)


class CurrencyListView(APIView):
    """
    Liste des devises disponibles.

    GET /api/finances/currencies/
    GET /api/v1/finances/currencies/

    Retourne la liste des devises actives avec leurs informations.
    Accessible sans authentification pour permettre l'affichage public.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            from apps.finances.models import Currency

            currencies = Currency.objects.filter(is_active=True).order_by('code')

            data = []
            for currency in currencies:
                data.append({
                    'code': currency.code,
                    'name': currency.name,
                    'symbol': currency.symbol,
                    'decimal_places': currency.decimal_places,
                    'symbol_position': getattr(currency, 'symbol_position', 'after'),
                })

            return Response({
                'success': True,
                'count': len(data),
                'currencies': data,
            })

        except Exception:
            # Fallback: devises statiques
            static_currencies = get_all_currencies()
            return Response({
                'success': True,
                'count': len(static_currencies),
                'currencies': [
                    {'code': c, 'name': c, 'symbol': c, 'decimal_places': 2}
                    for c in static_currencies
                ],
                'fallback': True,
            })


class CurrencyFormatView(APIView):
    """
    Formatage de montants selon les conventions de devise.

    GET /api/finances/format/?amount=1234.56&currency=EUR
    POST /api/finances/format/
    {
        "amount": 1234.56,
        "currency": "EUR",
        "include_symbol": true
    }

    Retourne le montant formate selon les conventions de la devise.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Formatage via parametres GET."""
        amount = request.GET.get('amount')
        currency = request.GET.get('currency', 'EUR').upper()
        include_symbol = request.GET.get('include_symbol', 'true').lower() == 'true'

        return self._format(amount, currency, include_symbol)

    def post(self, request):
        """Formatage via body JSON."""
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'EUR').upper()
        include_symbol = request.data.get('include_symbol', True)

        return self._format(amount, currency, include_symbol)

    def _format(self, amount, currency, include_symbol):
        """Logique de formatage commune."""
        if amount is None:
            return Response({
                'success': False,
                'error': 'Le parametre "amount" est requis',
            }, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return Response({
                'success': False,
                'error': f'Montant invalide: {amount}',
            }, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            formatted = fmt_currency(decimal_amount, currency, include_symbol)

            return Response({
                'success': True,
                'amount': float(decimal_amount),
                'currency': currency,
                'formatted': formatted,
                'include_symbol': include_symbol,
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkConvertView(APIView):
    """
    Conversion en lot de plusieurs montants.

    POST /api/finances/bulk-convert/
    {
        "amounts": [100, 200, 300],
        "from_currency": "USD",
        "to_currency": "EUR"
    }

    Convertit plusieurs montants en une seule requete.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        amounts = request.data.get('amounts', [])
        from_currency = request.data.get('from_currency', 'EUR').upper()
        to_currency = request.data.get('to_currency', 'EUR').upper()

        if not amounts:
            return Response({
                'success': False,
                'error': 'Le parametre "amounts" est requis et doit etre une liste',
            }, status=http_status.HTTP_400_BAD_REQUEST)

        if not isinstance(amounts, list):
            return Response({
                'success': False,
                'error': '"amounts" doit etre une liste de nombres',
            }, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            if not is_currency_supported(from_currency):
                return Response({
                    'success': False,
                    'error': f'Devise source non supportee: {from_currency}',
                }, status=http_status.HTTP_400_BAD_REQUEST)

            if not is_currency_supported(to_currency):
                return Response({
                    'success': False,
                    'error': f'Devise cible non supportee: {to_currency}',
                }, status=http_status.HTTP_400_BAD_REQUEST)

            results = []
            rate_used = None

            for i, amount in enumerate(amounts):
                try:
                    decimal_amount = Decimal(str(amount))
                    converted, rate = convert_amount(decimal_amount, from_currency, to_currency)
                    rate_used = rate

                    results.append({
                        'index': i,
                        'original': float(decimal_amount),
                        'converted': float(converted),
                        'formatted': fmt_currency(converted, to_currency),
                    })
                except (InvalidOperation, ValueError):
                    results.append({
                        'index': i,
                        'error': f'Montant invalide: {amount}',
                    })

            return Response({
                'success': True,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': float(rate_used) if rate_used else None,
                'count': len(results),
                'results': results,
                'timestamp': timezone.now().isoformat(),
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrencyPreferenceUpdateView(APIView):
    """
    Mise a jour de la preference de devise utilisateur.

    POST /api/finances/currency/set-preferred/
    {
        "currency": "USD"
    }

    Definit la devise preferee de l'utilisateur authentifie.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        """Definit la devise preferee de l'utilisateur."""
        currency = request.data.get('currency', '').upper()

        if not currency:
            return Response({
                'success': False,
                'error': 'Le parametre "currency" est requis',
            }, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            if not is_currency_supported(currency):
                return Response({
                    'success': False,
                    'error': f'Devise non supportee: {currency}',
                }, status=http_status.HTTP_400_BAD_REQUEST)

            # Stocker en session
            request.session['preferred_currency'] = currency

            # Stocker dans le profil utilisateur si disponible
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'preferred_currency'):
                request.user.profile.preferred_currency = currency
                request.user.profile.save(update_fields=['preferred_currency'])

            return Response({
                'success': True,
                'currency': currency,
                'message': f'Devise preferee mise a jour: {currency}',
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


# Register extended currency endpoints
urlpatterns += [
    # Liste des devises disponibles
    path('currencies/', CurrencyListView.as_view(), name='currency_list_api'),

    # Formatage de montants
    path('format/', CurrencyFormatView.as_view(), name='currency_format_api'),

    # Conversion en lot
    path('bulk-convert/', BulkConvertView.as_view(), name='bulk_convert_api'),

    # Mise a jour preference de devise
    path('currency/set-preferred/', CurrencyPreferenceUpdateView.as_view(), name='currency_set_preferred_api'),
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
