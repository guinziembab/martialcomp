from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from apps.organizations.models import Organization
from apps.organizations.models import OrganizationMember, OrganizationRole
from django.shortcuts import get_object_or_404


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Segmenter: si l'utilisateur a une organisation, la mettre en tête et limiter si souhaité
        # Déterminer l'organisation principale de l'utilisateur via membership actif
        user_org = None
        try:
            membership = OrganizationMember.objects.filter(user=request.user, is_active=True).select_related('organization').first()
            if membership:
                user_org = membership.organization.id
        except Exception:
            pass
        if user_org:
            orgs = Organization.objects.filter(id=user_org)
        else:
            orgs = Organization.objects.none()
        data = [{ 'id': o.id, 'name': getattr(o, 'name', ''), 'logo_url': getattr(o, 'logo_url', None) } for o in orgs[:50]]
        return Response({'organizations': data, 'user_organization': user_org})


class OrganizationDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response({'organization': None, 'members_count': 0, 'active_competitions': 0, 'recent_events': [], 'grades_distribution': {}, 'currency': 'EUR' })
        payload = {
            'organization': {
                'id': org.id,
                'name': getattr(org, 'name', ''),
                'logo_url': getattr(org, 'logo_url', None),
            },
            'members_count': getattr(org, 'members', []).count() if hasattr(org, 'members') else 0,
            'active_competitions': getattr(org, 'competitions', []).filter(status='active').count() if hasattr(org, 'competitions') else 0,
            'recent_events': [],
            'grades_distribution': {},
            'currency': None,
        }
        # Best-effort currency from country mapping
        try:
            from apps.finances.currency_service import COUNTRY_TO_CURRENCY
            country = getattr(org, 'country', '') or ''
            code = COUNTRY_TO_CURRENCY.get(country) or COUNTRY_TO_CURRENCY.get(str(country).upper()) or 'EUR'
            payload['currency'] = code
        except Exception:
            payload['currency'] = 'EUR'
        return Response(payload)


class OrganizationJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organization_id: int):
        org = get_object_or_404(Organization, pk=organization_id)
        member, created = OrganizationMember.objects.get_or_create(
            user=request.user,
            organization=org,
            defaults={
                'role': OrganizationRole.MEMBER,
                'is_active': True,
            },
        )
        if not created and not member.is_active:
            member.is_active = True
            member.save(update_fields=['is_active'])
        data = {
            'organization': {'id': org.id, 'name': org.name},
            'member': {
                'id': member.id,
                'role': member.role,
                'is_active': member.is_active,
            }
        }
        return Response({'success': True, **data})


class MembersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retourne les membres (utilisateurs/pratiquants) de l'organisation courante."""
        results = []
        org = None
        # 1) org via query param (prioritaire pour usage AJAX explicite)
        org_id_param = request.GET.get('org_id')
        if org_id_param:
            try:
                org = Organization.objects.filter(pk=org_id_param).first()
            except Exception:
                org = None
        # 2) org via header explicite
        if org is None:
            try:
                org_id_hdr = request.headers.get('X-Organization-ID') or request.META.get('HTTP_X_ORGANIZATION_ID')
                if org_id_hdr:
                    org = Organization.objects.filter(pk=org_id_hdr).first()
            except Exception:
                org = None
        # 3) org via helper _get_request_organization
        if org is None:
            try:
                from apps.finances.currency_service import _get_request_organization  # type: ignore
                org = _get_request_organization(request)
            except Exception:
                org = None
        # 4) fallback: première organisation du user via OrganizationMember
        if org is None:
            try:
                membership = OrganizationMember.objects.filter(user=request.user, is_active=True).select_related('organization').first()
                if membership:
                    org = membership.organization
            except Exception:
                org = None

        # Membres d'organisation (utilisateurs)
        try:
            if org is not None:
                from .models import OrganizationMember  # type: ignore
                qs = OrganizationMember.objects.filter(organization=org, is_active=True).select_related('user')
                for m in qs:
                    user = getattr(m, 'user', None)
                    if user:
                        results.append({
                            'id': getattr(user, 'id', None),
                            'name': (getattr(user, 'get_full_name', lambda: '')() or user.username),
                            'full_name': getattr(user, 'get_full_name', lambda: '')(),
                            'email': getattr(user, 'email', ''),
                            'type': 'user',
                        })
        except Exception:
            pass

        # Pratiquants (si disponibles)
        try:
            if org is not None:
                from apps.competitions.models.practitioners import Practitioner  # type: ignore
                pqs = Practitioner.objects.filter(organization=org)
                for p in pqs:
                    results.append({
                        'id': getattr(getattr(p, 'user', None), 'id', None),
                        'name': (f"{getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}".strip() or getattr(p, 'display_name', '')),
                        'full_name': f"{getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}".strip(),
                        'email': getattr(getattr(p, 'user', None), 'email', ''),
                        'type': 'practitioner',
                    })
        except Exception:
            pass

        # Éviter les doublons par (type,name,email)
        seen = set()
        deduped = []
        for r in results:
            key = (r.get('type'), r.get('name'), r.get('email'))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        return Response({'results': deduped})
"""
Points d'API pour les organisations.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import Organization, OrganizationMember
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
@require_GET
def api_get_organizations(request):
    """API pour récupérer les organisations."""
    # Paramètres de filtrage
    org_type = request.GET.get('type')
    search_query = request.GET.get('q')
    
    # Construire la requÃªte
    queryset = Organization.objects.filter(is_active=True)
    
    if org_type:
        queryset = queryset.filter(organization_type=org_type)
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(short_name__icontains=search_query)
        )
    
    # Limiter le nombre de résultats
    limit = int(request.GET.get('limit', 20))
    queryset = queryset[:limit]
    
    # Construire la réponse
    organizations = []
    for org in queryset:
        organizations.append({
            'id': org.id,
            'name': org.name,
            'short_name': org.short_name,
            'type': org.organization_type,
            'type_display': org.get_organization_type_display(),
            'country': org.country,
            'city': org.city,
        })
    
    return JsonResponse({'organizations': organizations})


@login_required
@require_GET
def api_get_user_organizations(request):
    """API pour récupérer les organisations de l'utilisateur."""
    # Récupérer les organisations dont l'utilisateur est membre
    memberships = OrganizationMember.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization')
    
    # Construire la réponse
    organizations = []
    for membership in memberships:
        org = membership.organization
        organizations.append({
            'id': org.id,
            'name': org.name,
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'type': org.organization_type,
            'type_display': org.get_organization_type_display(),
            'can_edit': membership.can_edit_organization,
            'can_manage_members': membership.can_manage_members,
            'can_manage_competitions': membership.can_manage_competitions,
        })
    
    return JsonResponse({'organizations': organizations})
