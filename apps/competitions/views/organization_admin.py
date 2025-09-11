from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, View
from django.shortcuts import render, get_object_or_404, redirect
from apps.competitions.models import Organization
from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@method_decorator(staff_member_required, name='dispatch')
class OrganizationAdminListView(ListView):
    model = Organization
    template_name = 'organizations/admin/organization_list.html'
    context_object_name = 'organizations'
    paginate_by = 20
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by('-created_at')

@method_decorator(staff_member_required, name='dispatch')
class OrganizationAdminDetailView(DetailView):
    model = Organization
    template_name = 'organizations/admin/organization_detail.html'
    context_object_name = 'organization'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qr_codes'] = generate_organization_qr_codes_set(self.object)
        return context

@method_decorator(staff_member_required, name='dispatch')
class RegenerateQRCodesView(View):
    def post(self, request, pk):
        org = get_object_or_404(Organization, pk=pk)
        generate_organization_qr_codes_set(org, force=True)
        return redirect('organization_admin_detail', pk=pk) 
