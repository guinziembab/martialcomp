# competitions/views/federation/licences.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from competitions.models import Federation, License
from competitions.utils.decorators import federation_admin_required
from competitions.forms.licences import LicenseForm

@login_required
@federation_admin_required
def licences_list(request, federation_id):
    """Liste des licences de la fédération."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from organizations.models import Organization
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        from django.contrib import messages
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
    
    # Filtres
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    licences = License.objects.filter(organization=federation_org)
    
    if search_query:
        licences = licences.filter(
            Q(practitioner__first_name__icontains=search_query) |
            Q(practitioner__last_name__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )
    
    if status_filter:
        licences = licences.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(licences.order_by('-issue_date'), 20)
    page = request.GET.get('page')
    licences_page = paginator.get_page(page)
    
    context = {
        'federation': federation,
        'licences': licences_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'license_statuses': License.STATUS_CHOICES,
    }
    
    return render(request, 'competitions/federations/licences/list.html', context)

@login_required
@federation_admin_required
def licence_create(request, federation_id):
    """Créer une nouvelle licence."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from organizations.models import Organization
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
    
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            licence = form.save(commit=False)
            licence.organization = federation_org
            licence.save()
            messages.success(request, _("Licence créée avec succès."))
            return redirect('competitions:licences:list', federation_id=federation.id)
    else:
        form = LicenseForm()
    
    context = {
        'federation': federation,
        'form': form,
        'title': _('Créer une licence'),
    }
    
    return render(request, 'competitions/federations/licences/form.html', context)

@login_required
@federation_admin_required
def licence_edit(request, federation_id, licence_id):
    """Modifier une licence existante."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from organizations.models import Organization
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
    
    licence = get_object_or_404(License, id=licence_id, organization=federation_org)
    
    if request.method == 'POST':
        form = LicenseForm(request.POST, instance=licence)
        if form.is_valid():
            form.save()
            messages.success(request, _("Licence mise à jour avec succès."))
            return redirect('competitions:licences:list', federation_id=federation.id)
    else:
        form = LicenseForm(instance=licence)
    
    context = {
        'federation': federation,
        'licence': licence,
        'form': form,
        'title': _('Modifier une licence'),
    }
    
    return render(request, 'competitions/federations/licences/form.html', context)

@login_required
@federation_admin_required
def licence_delete(request, federation_id, licence_id):
    """Supprimer une licence."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from organizations.models import Organization
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
    
    licence = get_object_or_404(License, id=licence_id, organization=federation_org)
    
    if request.method == 'POST':
        licence.delete()
        messages.success(request, _("Licence supprimée avec succès."))
        return redirect('competitions:licences:list', federation_id=federation.id)
    
    context = {
        'federation': federation,
        'licence': licence,
    }
    
    return render(request, 'competitions/federations/licences/delete.html', context)