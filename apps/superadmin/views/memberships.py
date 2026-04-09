# -*- coding: utf-8 -*-
"""
Vues de gestion des profils d'adhésion pour Super Admin.
"""

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.models import (
    MembershipProfile,
    EventPass,
    MembershipTransformation,
)
from apps.superadmin.forms import MembershipProfileForm


class MembershipListView(SuperAdminRequiredMixin, ListView):
    """
    Liste des profils d'adhésion.
    """

    model = MembershipProfile
    template_name = 'superadmin/memberships/list.html'
    context_object_name = 'profiles'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtres
        profile_type = self.request.GET.get('type')
        if profile_type:
            queryset = queryset.filter(profile_type=profile_type)

        is_active = self.request.GET.get('active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        is_global = self.request.GET.get('global')
        if is_global == 'true':
            queryset = queryset.filter(is_global=True)
        elif is_global == 'false':
            queryset = queryset.filter(is_global=False)

        # Recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Profils d\'adhésion')
        context['active_tab'] = 'memberships'

        # Stats
        context['total_profiles'] = MembershipProfile.objects.count()
        context['active_profiles'] = MembershipProfile.objects.filter(is_active=True).count()
        context['subscription_profiles'] = MembershipProfile.objects.filter(profile_type='subscription').count()
        context['event_profiles'] = MembershipProfile.objects.filter(profile_type='event').count()

        # Filtres actifs
        context['current_type'] = self.request.GET.get('type', '')
        context['current_active'] = self.request.GET.get('active', '')
        context['current_global'] = self.request.GET.get('global', '')
        context['search_query'] = self.request.GET.get('q', '')

        return context


class MembershipDetailView(SuperAdminRequiredMixin, DetailView):
    """
    Détail d'un profil d'adhésion.
    """

    model = MembershipProfile
    template_name = 'superadmin/memberships/detail.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.name
        context['active_tab'] = 'memberships'

        # Passes événement liés
        context['event_passes'] = EventPass.objects.filter(
            membership_profile=self.object
        ).order_by('-created_at')[:10]

        # Transformations impliquant ce profil
        context['transformations'] = MembershipTransformation.objects.filter(
            Q(from_profile=self.object) | Q(to_profile=self.object)
        ).order_by('-created_at')[:10]

        # Stats d'utilisation
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # TODO: Ajouter les vraies stats quand les modèles de souscription seront implémentés
        context['stats'] = {
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'new_this_week': 0,
            'new_this_month': 0,
            'revenue_mtd': 0,
        }

        return context


class MembershipCreateView(SuperAdminRequiredMixin, CreateView):
    """
    Création d'un nouveau profil d'adhésion.
    """

    model = MembershipProfile
    form_class = MembershipProfileForm
    template_name = 'superadmin/memberships/form.html'
    success_url = reverse_lazy('superadmin:membership_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Nouveau profil')
        context['active_tab'] = 'memberships'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Profil "{}" créé avec succès.').format(form.instance.name)
        )
        return super().form_valid(form)


class MembershipUpdateView(SuperAdminRequiredMixin, UpdateView):
    """
    Modification d'un profil d'adhésion.
    """

    model = MembershipProfile
    form_class = MembershipProfileForm
    template_name = 'superadmin/memberships/form.html'
    success_url = reverse_lazy('superadmin:membership_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Modifier {}').format(self.object.name)
        context['active_tab'] = 'memberships'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Profil "{}" modifié avec succès.').format(form.instance.name)
        )
        return super().form_valid(form)


class MembershipDeleteView(SuperAdminRequiredMixin, DeleteView):
    """
    Suppression d'un profil d'adhésion.
    """

    model = MembershipProfile
    template_name = 'superadmin/memberships/confirm_delete.html'
    success_url = reverse_lazy('superadmin:membership_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Supprimer {}').format(self.object.name)
        context['active_tab'] = 'memberships'

        # Vérifier les dépendances
        context['event_passes_count'] = EventPass.objects.filter(membership_profile=self.object).count()
        context['transformations_count'] = MembershipTransformation.objects.filter(
            Q(from_profile=self.object) | Q(to_profile=self.object)
        ).count()

        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(
            request,
            _('Profil "{}" supprimé avec succès.').format(obj.name)
        )
        return super().delete(request, *args, **kwargs)


class MembershipStatsView(SuperAdminRequiredMixin, TemplateView):
    """
    Statistiques des adhésions.
    """

    template_name = 'superadmin/memberships/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Statistiques adhésions')
        context['active_tab'] = 'memberships'

        # Stats par profil
        profiles_stats = []
        for profile in MembershipProfile.objects.filter(is_active=True):
            # TODO: Ajouter les vraies stats
            profiles_stats.append({
                'profile': profile,
                'total': 0,
                'active': 0,
                'revenue': 0,
                'trend': 0,
            })
        context['profiles_stats'] = profiles_stats

        # Transformations récentes
        context['recent_transformations'] = MembershipTransformation.objects.order_by(
            '-created_at'
        )[:20]

        # Stats globales
        context['global_stats'] = {
            'total_profiles': MembershipProfile.objects.count(),
            'total_subscriptions': 0,
            'total_revenue_mtd': 0,
            'conversion_rate': 0,
        }

        return context


class MembershipToggleView(SuperAdminRequiredMixin, TemplateView):
    """
    Toggle activation d'un profil (AJAX).
    """

    def post(self, request, pk):
        try:
            profile = MembershipProfile.objects.get(pk=pk)
            profile.is_active = not profile.is_active
            profile.save(update_fields=['is_active'])

            return JsonResponse({
                'success': True,
                'is_active': profile.is_active,
                'message': _('Profil {} avec succès.').format(
                    _('activé') if profile.is_active else _('désactivé')
                )
            })
        except MembershipProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Profil non trouvé.')
            }, status=404)


class MembershipDuplicateView(SuperAdminRequiredMixin, TemplateView):
    """
    Duplication d'un profil (AJAX).
    """

    def post(self, request, pk):
        try:
            original = MembershipProfile.objects.get(pk=pk)

            # Créer la copie
            copy = MembershipProfile.objects.create(
                name=f"{original.name} (copie)",
                slug=f"{original.slug}-copy-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                description=original.description,
                profile_type=original.profile_type,
                validity_type=original.validity_type,
                validity_duration=original.validity_duration,
                is_global=original.is_global,
                base_tier=original.base_tier,
                feature_overrides=original.feature_overrides.copy() if original.feature_overrides else {},
                pricing_model=original.pricing_model,
                price=original.price,
                currency=original.currency,
                max_participants=original.max_participants,
                requires_approval=original.requires_approval,
                is_active=False,
            )

            return JsonResponse({
                'success': True,
                'new_id': copy.pk,
                'new_name': copy.name,
                'message': _('Profil dupliqué avec succès.')
            })
        except MembershipProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Profil non trouvé.')
            }, status=404)
