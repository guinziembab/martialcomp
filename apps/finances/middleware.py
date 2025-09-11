from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin
from .currency_service import get_preferred_currency_for_request


class CurrencyMiddleware(MiddlewareMixin):
    """
    Attach request.currency and request.currency_source to each request.
    """
    def process_request(self, request):
        try:
            code, source = get_preferred_currency_for_request(request)
            setattr(request, 'currency', code)
            setattr(request, 'currency_source', source)
        except Exception:
            setattr(request, 'currency', 'EUR')
            setattr(request, 'currency_source', 'default')
        return None
