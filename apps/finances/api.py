from decimal import Decimal, InvalidOperation
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status


# =============================================================================
# CURRENCY API VIEWS (Multi-devise)
# =============================================================================

class CurrencyListView(APIView):
    """
    Liste des devises disponibles.

    GET /api/finances/currencies/

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
                    'symbol_position': currency.symbol_position,
                })

            return Response({
                'success': True,
                'count': len(data),
                'currencies': data,
            })

        except Exception as e:
            # Fallback: devises statiques
            static_currencies = [
                {'code': 'EUR', 'name': 'Euro', 'symbol': 'EUR', 'decimal_places': 2},
                {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'decimal_places': 2},
                {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'decimal_places': 2},
                {'code': 'XOF', 'name': 'CFA Franc BCEAO', 'symbol': 'FCFA', 'decimal_places': 0},
            ]
            return Response({
                'success': True,
                'count': len(static_currencies),
                'currencies': static_currencies,
                'fallback': True,
            })


class ExchangeRatesView(APIView):
    """
    Taux de change actuels.

    GET /api/finances/rates/
    GET /api/finances/rates/?base=USD

    Retourne les taux de change par rapport a une devise de base (defaut EUR).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        base = request.query_params.get('base', 'EUR').upper()

        try:
            from apps.finances.currency_service import get_rates

            base_used, rates, last_updated = get_rates(base)

            return Response({
                'success': True,
                'base': base_used,
                'last_updated': last_updated.isoformat() if last_updated else None,
                'rates': rates,
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'base': base,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrencyConvertView(APIView):
    """
    Conversion de devises.

    GET /api/finances/convert/?amount=100&from=USD&to=EUR
    POST /api/finances/convert/
    {
        "amount": 100,
        "from_currency": "USD",
        "to_currency": "EUR"
    }

    Convertit un montant d'une devise a une autre.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Conversion via parametres GET."""
        amount = request.query_params.get('amount')
        from_currency = request.query_params.get('from', 'EUR').upper()
        to_currency = request.query_params.get('to', 'EUR').upper()

        return self._convert(amount, from_currency, to_currency)

    def post(self, request):
        """Conversion via body JSON."""
        amount = request.data.get('amount')
        from_currency = request.data.get('from_currency', 'EUR').upper()
        to_currency = request.data.get('to_currency', 'EUR').upper()

        return self._convert(amount, from_currency, to_currency)

    def _convert(self, amount, from_currency, to_currency):
        """Logique de conversion commune."""
        # Validation du montant
        if amount is None:
            return Response({
                'success': False,
                'error': 'Le parametre "amount" est requis',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return Response({
                'success': False,
                'error': f'Montant invalide: {amount}',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validation des devises
        try:
            from apps.finances.currency_service import (
                convert_amount, format_currency, is_currency_supported
            )

            if not is_currency_supported(from_currency):
                return Response({
                    'success': False,
                    'error': f'Devise source non supportee: {from_currency}',
                }, status=status.HTTP_400_BAD_REQUEST)

            if not is_currency_supported(to_currency):
                return Response({
                    'success': False,
                    'error': f'Devise cible non supportee: {to_currency}',
                }, status=status.HTTP_400_BAD_REQUEST)

            # Conversion
            converted, rate = convert_amount(decimal_amount, from_currency, to_currency)

            # Formatage
            formatted_original = format_currency(decimal_amount, from_currency)
            formatted_converted = format_currency(converted, to_currency)

            return Response({
                'success': True,
                'original': {
                    'amount': float(decimal_amount),
                    'currency': from_currency,
                    'formatted': formatted_original,
                },
                'converted': {
                    'amount': float(converted),
                    'currency': to_currency,
                    'formatted': formatted_converted,
                },
                'rate': float(rate),
                'timestamp': timezone.now().isoformat(),
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        amount = request.query_params.get('amount')
        currency = request.query_params.get('currency', 'EUR').upper()
        include_symbol = request.query_params.get('include_symbol', 'true').lower() == 'true'

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
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return Response({
                'success': False,
                'error': f'Montant invalide: {amount}',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.finances.currency_service import format_currency

            formatted = format_currency(decimal_amount, currency, include_symbol)

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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserCurrencyPreferenceView(APIView):
    """
    Preference de devise utilisateur.

    GET /api/finances/user-currency/
    POST /api/finances/user-currency/
    {
        "currency": "USD"
    }

    Retourne ou modifie la devise preferee de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        """Recupere la devise preferee de l'utilisateur."""
        try:
            from apps.finances.currency_service import get_preferred_currency_for_request

            code, source = get_preferred_currency_for_request(request)

            return Response({
                'success': True,
                'currency': code,
                'source': source,
            })

        except Exception as e:
            return Response({
                'success': True,
                'currency': 'EUR',
                'source': 'default',
            })

    def post(self, request):
        """Definit la devise preferee de l'utilisateur."""
        currency = request.data.get('currency', '').upper()

        if not currency:
            return Response({
                'success': False,
                'error': 'Le parametre "currency" est requis',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.finances.currency_service import is_currency_supported

            if not is_currency_supported(currency):
                return Response({
                    'success': False,
                    'error': f'Devise non supportee: {currency}',
                }, status=status.HTTP_400_BAD_REQUEST)

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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(amounts, list):
            return Response({
                'success': False,
                'error': '"amounts" doit etre une liste de nombres',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.finances.currency_service import (
                convert_amount, format_currency, is_currency_supported
            )

            if not is_currency_supported(from_currency):
                return Response({
                    'success': False,
                    'error': f'Devise source non supportee: {from_currency}',
                }, status=status.HTTP_400_BAD_REQUEST)

            if not is_currency_supported(to_currency):
                return Response({
                    'success': False,
                    'error': f'Devise cible non supportee: {to_currency}',
                }, status=status.HTTP_400_BAD_REQUEST)

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
                        'formatted': format_currency(converted, to_currency),
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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# FINANCE DASHBOARD VIEW
# =============================================================================

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
    # Finance Dashboard
    path('dashboard/', FinanceDashboardView.as_view(), name='finances_dashboard_api'),

    # ==========================================================================
    # Currency API Endpoints (Multi-devise)
    # ==========================================================================

    # Liste des devises disponibles
    # GET /api/finances/currencies/
    path('currencies/', CurrencyListView.as_view(), name='currency_list_api'),

    # Taux de change actuels
    # GET /api/finances/rates/?base=EUR
    path('rates/', ExchangeRatesView.as_view(), name='exchange_rates_api'),

    # Conversion de devises
    # GET /api/finances/convert/?amount=100&from=USD&to=EUR
    # POST /api/finances/convert/
    path('convert/', CurrencyConvertView.as_view(), name='currency_convert_api'),

    # Formatage de montants
    # GET /api/finances/format/?amount=1234.56&currency=EUR
    # POST /api/finances/format/
    path('format/', CurrencyFormatView.as_view(), name='currency_format_api'),

    # Preference de devise utilisateur (authentifie)
    # GET/POST /api/finances/user-currency/
    path('user-currency/', UserCurrencyPreferenceView.as_view(), name='user_currency_api'),

    # Conversion en lot
    # POST /api/finances/bulk-convert/
    path('bulk-convert/', BulkConvertView.as_view(), name='bulk_convert_api'),
]
