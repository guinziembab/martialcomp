# -*- coding: utf-8 -*-
"""
Vues pour le système d'adhésion MartialComp v2.0
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
import logging

from .models import (
    MembershipPackage, MembershipSubscription, OnlineMembershipForm,
    MembershipFormSubmission, MembershipWorkflow, MembershipAlert
)
from .services import MembershipService, MembershipAnalyticsService
from apps.core.isolation import get_organization_queryset
from apps.competitions.models import Organization, Practitioner

logger = logging.getLogger(__name__)


@login_required
def membership_dashboard(request):
    """
    Tableau de bord principal du système d'adhésion
    """
    try:
        # Récupérer l'organisation de l'utilisateur
        organization = get_organization_queryset(Organization, request.user).first()
        if not organization:
            messages.warning(request, _("Aucune organisation associée trouvée."))
            return redirect('competitions:dashboard:home')
        
        # Statistiques d'adhésion
        membership_stats = MembershipService.get_membership_stats(organization)
        
        # Souscriptions récentes
        recent_subscriptions = MembershipSubscription.objects.filter(
            package__organization=organization
        ).select_related('practitioner', 'package').order_by('-created_at')[:10]
        
        # Alertes non résolues
        alerts = MembershipAlert.objects.filter(
            subscription__package__organization=organization,
            is_resolved=False
        ).order_by('-created_at')[:5]
        
        # Packages actifs
        active_packages = MembershipPackage.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('sort_order', 'name')
        
        context = {
            'organization': organization,
            'membership_stats': membership_stats,
            'recent_subscriptions': recent_subscriptions,
            'alerts': alerts,
            'active_packages': active_packages,
            'page_title': _('Tableau de bord Adhésions'),
        }
        
        return render(request, 'membership/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans membership_dashboard: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors du chargement du tableau de bord."))
        return redirect('competitions:dashboard:home')


@login_required
def package_list(request):
    """
    Liste des packages d'adhésion
    """
    organization = get_organization_queryset(Organization, request.user).first()
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        return redirect('membership:dashboard')
    
    packages = MembershipPackage.objects.filter(
        organization=organization
    ).order_by('sort_order', 'name')
    
    context = {
        'packages': packages,
        'organization': organization,
        'page_title': _('Packages d\'adhésion'),
    }
    
    return render(request, 'membership/packages/list.html', context)


@login_required
def subscription_list(request):
    """
    Liste des souscriptions d'adhésion
    """
    organization = get_organization_queryset(Organization, request.user).first()
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        return redirect('membership:dashboard')
    
    subscriptions = MembershipSubscription.objects.filter(
        package__organization=organization
    ).select_related('practitioner', 'package').order_by('-created_at')
    
    # Filtrage
    status_filter = request.GET.get('status')
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(subscriptions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'organization': organization,
        'status_filter': status_filter,
        'page_title': _('Souscriptions d\'adhésion'),
    }
    
    return render(request, 'membership/subscriptions/list.html', context)


@login_required
def subscription_detail(request, pk):
    """
    Détail d'une souscription d'adhésion
    """
    subscription = get_object_or_404(
        MembershipSubscription.objects.select_related('practitioner', 'package'),
        pk=pk
    )
    
    # Vérifier les permissions d'accès
    organization = get_organization_queryset(Organization, request.user).first()
    if subscription.package.organization != organization:
        messages.error(request, _("Accès non autorisé à cette souscription."))
        return redirect('membership:subscription_list')
    
    context = {
        'subscription': subscription,
        'page_title': _('Détail de la souscription'),
    }
    
    return render(request, 'membership/subscriptions/detail.html', context)


def public_form(request, slug):
    """
    Formulaire d'adhésion public
    """
    form = get_object_or_404(
        OnlineMembershipForm.objects.prefetch_related('available_packages'),
        slug=slug,
        is_active=True,
        is_public=True
    )
    
    context = {
        'form': form,
        'packages': form.available_packages.filter(is_active=True),
        'page_title': form.title,
    }
    
    return render(request, 'membership/forms/public_form.html', context)


def form_submit(request, slug):
    """
    Soumission d'un formulaire d'adhésion public
    """
    if request.method != 'POST':
        return redirect('membership:public_form', slug=slug)
    
    form = get_object_or_404(
        OnlineMembershipForm,
        slug=slug,
        is_active=True,
        is_public=True
    )
    
    try:
        with transaction.atomic():
            # Récupérer les données du formulaire
            selected_package_id = request.POST.get('package')
            selected_package = get_object_or_404(
                form.available_packages.filter(is_active=True),
                id=selected_package_id
            )
            
            # Créer la soumission
            submission = MembershipFormSubmission.objects.create(
                form=form,
                selected_package=selected_package,
                email=request.POST.get('email'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                phone=request.POST.get('phone', ''),
                date_of_birth=request.POST.get('date_of_birth'),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                form_data={
                    'experience_level': request.POST.get('experience_level', ''),
                    'medical_conditions': request.POST.get('medical_conditions', ''),
                    'additional_notes': request.POST.get('additional_notes', ''),
                }
            )
            
            messages.success(
                request,
                _("Votre demande d'adhésion a été soumise avec succès. "
                  "Vous recevrez une confirmation par email.")
            )
            
            return render(request, 'membership/forms/success.html', {
                'form': form,
                'submission': submission
            })
    
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du formulaire {slug}: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la soumission."))
        return redirect('membership:public_form', slug=slug)


@login_required
def analytics_dashboard(request):
    """
    Tableau de bord d'analytics des adhésions
    """
    organization = get_organization_queryset(Organization, request.user).first()
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        return redirect('membership:dashboard')
    
    # Analytics avancées
    retention_data = MembershipAnalyticsService.get_retention_rate(organization)
    popular_packages = MembershipAnalyticsService.get_popular_packages(organization)
    revenue_trend = MembershipAnalyticsService.get_revenue_trend(organization, 12)
    
    context = {
        'organization': organization,
        'retention_data': retention_data,
        'popular_packages': popular_packages,
        'revenue_trend': revenue_trend,
        'page_title': _('Analytics Adhésions'),
    }
    
    return render(request, 'membership/analytics/dashboard.html', context)


# Vues de gestion des packages
@login_required
def package_create(request):
    """
    Créer un nouveau package d'adhésion
    """
    organization = get_organization_queryset(Organization, request.user).first()
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        return redirect('membership:package_list')
    
    if request.method == 'POST':
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(request.POST, organization=organization)
        if form.is_valid():
            package = form.save()
            messages.success(request, _("Package '{}' créé avec succès.").format(package.name))
            return redirect('membership:package_list')
    else:
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': _('Créer un package d\'adhésion'),
    }
    
    return render(request, 'membership/packages/create.html', context)

@login_required 
def package_edit(request, pk):
    """
    Modifier un package d'adhésion existant
    """
    organization = get_organization_queryset(Organization, request.user).first()
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        return redirect('membership:package_list')
    
    package = get_object_or_404(MembershipPackage, pk=pk, organization=organization)
    
    if request.method == 'POST':
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(request.POST, instance=package, organization=organization)
        if form.is_valid():
            package = form.save()
            messages.success(request, _("Package '{}' modifié avec succès.").format(package.name))
            return redirect('membership:package_list')
    else:
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(instance=package, organization=organization)
    
    context = {
        'form': form,
        'package': package,
        'organization': organization,
        'page_title': _('Modifier le package'),
    }
    
    return render(request, 'membership/packages/edit.html', context)

@login_required
def package_delete(request, pk):
    messages.info(request, _("Suppression de package - Fonctionnalité en développement"))
    return redirect('membership:package_list')

@login_required
def subscription_create(request):
    messages.info(request, _("Création de souscription - Fonctionnalité en développement"))
    return redirect('membership:subscription_list')

@login_required
def subscription_edit(request, pk):
    messages.info(request, _("Édition de souscription - Fonctionnalité en développement"))
    return redirect('membership:subscription_list')

@login_required
def subscription_renew(request, pk):
    messages.info(request, _("Renouvellement - Fonctionnalité en développement"))
    return redirect('membership:subscription_detail', pk=pk)

@login_required
def subscription_cancel(request, pk):
    messages.info(request, _("Annulation - Fonctionnalité en développement"))
    return redirect('membership:subscription_detail', pk=pk)

@login_required
def form_list(request):
    messages.info(request, _("Gestion des formulaires - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def form_create(request):
    messages.info(request, _("Création de formulaire - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def form_edit(request, pk):
    messages.info(request, _("Édition de formulaire - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def submission_list(request):
    messages.info(request, _("Liste des soumissions - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def submission_detail(request, pk):
    messages.info(request, _("Détail de soumission - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def submission_process(request, pk):
    messages.info(request, _("Traitement de soumission - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def workflow_list(request):
    messages.info(request, _("Gestion des workflows - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def workflow_create(request):
    messages.info(request, _("Création de workflow - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def workflow_edit(request, pk):
    messages.info(request, _("Édition de workflow - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def workflow_test(request, pk):
    messages.info(request, _("Test de workflow - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def alert_list(request):
    messages.info(request, _("Liste des alertes - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def alert_resolve(request, pk):
    messages.info(request, _("Résolution d'alerte - Fonctionnalité en développement"))
    return redirect('membership:dashboard')

@login_required
def analytics_export(request):
    messages.info(request, _("Export analytics - Fonctionnalité en développement"))
    return redirect('membership:analytics')