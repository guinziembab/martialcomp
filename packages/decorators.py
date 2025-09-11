from functools import wraps
from django.http import HttpResponseForbidden

def require_feature(feature_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            org = getattr(request.user, 'organization', None)
            if not org:
                return HttpResponseForbidden("Aucune organisation associée.")
            org_package = getattr(org, 'organizationpackage_set', None)
            if not org_package or not org_package.filter(is_active=True).exists():
                return HttpResponseForbidden("Aucun package actif.")
            active_features = org_package.filter(is_active=True).first().active_features
            if feature_code not in active_features:
                return HttpResponseForbidden("Fonctionnalité non activée.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 