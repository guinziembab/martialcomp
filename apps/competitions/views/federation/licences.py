from django.core.exceptions import PermissionDenied
# competitions/views/federation/licences.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.competitions.models import Federation, License
from apps.competitions.utils.decorators import federation_admin_required
from apps.competitions.forms.licences import LicenseForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def licences_list(request, federation_id):
    """Liste des licences de la fédération."""
    try:
        federation = get_object_or_404(Federation, id=federation_id)
        
        print(f"DEBUG: Federation found: {federation.name}")
        
        # Récupérer ou créer l'organisation de la fédération
        from apps.organizations.models import Organization
        if hasattr(federation, 'organization') and federation.organization:
            federation_org = federation.organization
            print(f"DEBUG: Using existing organization: {federation_org}")
        else:
            federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
            if not federation_org:
                print("DEBUG: No organization found, creating one automatically")
                # Créer automatiquement une organisation pour la fédération
                federation_org = Organization.objects.create(
                    name=federation.name,
                    organization_type='national_federation',
                    old_federation_id=federation.id,
                    is_active=True,
                    country=federation.country,
                    city=federation.city or '',
                    email=federation.contact_email or '',
                    description=f"Organisation automatically created for federation {federation.name}"
                )
                print(f"DEBUG: Created organization: {federation_org}")
                
                # Associer l'organisation à la fédération si possible
                if hasattr(federation, 'organization'):
                    federation.organization = federation_org
                    federation.save()
                    print("DEBUG: Associated organization to federation")
        
        print(f"DEBUG: Using organization: {federation_org}")
        
        # Récupérer les licences de l'organisation
        print(f"DEBUG: Looking for licences in organization: {federation_org.id}")
        licences = License.objects.filter(organization=federation_org)
        print(f"DEBUG: Found {licences.count()} licences")
        
        # Pagination simple pour debug
        context = {
            'federation': federation,
            'licences': licences[:20],  # Limiter à 20 pour debug
            'search_query': '',
            'status_filter': '',
            'license_statuses': License.STATUS_CHOICES,
        }
        
        return render(request, 'competitions/federations/licences/list.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error in licences_list: {str(e)}")
        from django.http import HttpResponse
        return HttpResponse(f"Debug error: {str(e)}")
        

@login_required
def licence_create(request, federation_id):
    """Créer une nouvelle licence."""
    try:
        print(f"DEBUG: licence_create called with federation_id={federation_id}")
        federation = get_object_or_404(Federation, id=federation_id)
        print(f"DEBUG: Federation found: {federation.name}")
        
        # Récupérer ou créer l'organisation de la fédération
        from apps.organizations.models import Organization
        if hasattr(federation, 'organization') and federation.organization:
            federation_org = federation.organization
            print(f"DEBUG: Using existing organization: {federation_org}")
        else:
            federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
            if not federation_org:
                print("DEBUG: No organization found, creating one automatically")
                # Créer automatiquement une organisation pour la fédération
                federation_org = Organization.objects.create(
                    name=federation.name,
                    organization_type='national_federation',
                    old_federation_id=federation.id,
                    is_active=True,
                    country=federation.country,
                    city=federation.city or '',
                    email=federation.contact_email or '',
                    description=f"Organisation automatically created for federation {federation.name}"
                )
                print(f"DEBUG: Created organization: {federation_org}")
                
                # Associer l'organisation à la fédération si possible
                if hasattr(federation, 'organization'):
                    federation.organization = federation_org
                    federation.save()
                    print("DEBUG: Associated organization to federation")
        
        print(f"DEBUG: Using organization: {federation_org}")
        
        print("DEBUG: Processing form")
        if request.method == 'POST':
            print("DEBUG: POST request")
            form = LicenseForm(request.POST)
            if form.is_valid():
                print("DEBUG: Form is valid")
                licence = form.save(commit=False)
                licence.organization = federation_org
                licence.save()
                messages.success(request, _("Licence créée avec succès."))
                return redirect('competitions:licences:list', federation_id=federation.id)
            else:
                print(f"DEBUG: Form errors: {form.errors}")
        else:
            print("DEBUG: GET request, creating empty form")
            form = LicenseForm()
        
        context = {
            'federation': federation,
            'form': form,
            'title': _('Créer une licence'),
        }
        
        print("DEBUG: Rendering template")
        return render(request, 'competitions/federations/licences/form.html', context)
        
    except Exception as e:
        print(f"DEBUG: Error in licence_create: {str(e)}")
        from django.http import HttpResponse
        return HttpResponse(f"Debug error in licence_create: {str(e)}")

@login_required
def licence_edit(request, federation_id, licence_id):
    """Modifier une licence existante."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from apps.organizations.models import Organization
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
            messages.success(request, _("Licence mise Ã  jour avec succès."))
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
def licence_delete(request, federation_id, licence_id):
    """Supprimer une licence."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    from apps.organizations.models import Organization
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

