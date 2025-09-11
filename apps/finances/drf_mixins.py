from __future__ import annotations

from typing import Any, Mapping
from rest_framework.views import APIView
from rest_framework.response import Response

from .currency_service import get_preferred_currency_for_request, convert_amount


class CurrencyAwareAPIView(APIView):
    """
    DRF APIView mixin that attaches a currency to responses and converts
    common financial keys for display purposes when possible.

    Behavior:
      - Ensures response.data has a 'currency' field when dict-like
      - Optionally converts known KPI keys from EUR -> preferred currency
    """

    kpi_keys_to_convert = {'balance', 'revenue', 'expenses', 'pending_amount', 'total_amount', 'total'}

    def finalize_response(self, request, response, *args, **kwargs):  # type: ignore[override]
        response = super().finalize_response(request, response, *args, **kwargs)
        try:
            # Only touch JSON-like dict payloads
            if isinstance(response, Response) and isinstance(response.data, Mapping):
                currency, _ = get_preferred_currency_for_request(request)
                payload: dict[str, Any] = dict(response.data)
                if 'currency' not in payload:
                    payload['currency'] = currency

                # Best-effort conversion of standard keys from EUR
                updated = False
                for key in self.kpi_keys_to_convert:
                    if key in payload:
                        try:
                            value = float(payload[key])
                            converted, _ = convert_amount(value, 'EUR', currency)
                            payload[key] = converted
                            updated = True
                        except Exception:
                            continue
                if updated or 'currency' in payload:
                    response.data = payload
        except Exception:
            # Never break responses because of currency decoration
            return response
        return response
