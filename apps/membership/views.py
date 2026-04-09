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


def get_organization_for_membership(request):
    """
    Récupère l'organisation pour les fonctionnalités d'adhésion.
    Supporte:
    - organization_id passé en paramètre (ID de fédération, récupère son organization)
    - federation_id passé en paramètre
    - L'organisation de l'utilisateur via son profil

    Returns:
        tuple: (organization, federation) où federation peut être None
    """
    from apps.competitions.models import Federation
    from apps.organizations.models import Organization as OrgModel

    organization = None
    federation = None

    # Priorité 1: organization_id dans les paramètres GET (c'est l'ID de la fédération depuis le template)
    org_id = request.GET.get('organization_id') or request.POST.get('organization_id')
    if org_id:
        try:
            # C'est l'ID de la fédération, pas de l'organisation
            federation = Federation.objects.select_related('organization').get(id=org_id)
            logger.info(f"[Membership] Fédération trouvée: {federation.name} (id={federation.id})")

            if federation.organization:
                organization = federation.organization
                logger.info(f"[Membership] Organisation via FK: {organization.name} (id={organization.id})")
            else:
                # Si la fédération n'a pas d'organisation liée, essayer via as_organization
                organization = federation.as_organization
                if organization:
                    logger.info(f"[Membership] Organisation via as_organization: {organization.name} (id={organization.id})")
                else:
                    # Créer ou récupérer une organisation pour cette fédération
                    logger.warning(f"[Membership] Pas d'organisation liée pour fédération {federation.id}, création...")
                    organization = _create_organization_for_federation(federation)
        except Federation.DoesNotExist:
            logger.info(f"[Membership] Pas de fédération avec id={org_id}, essai comme ID organisation")
            # Essayer comme ID d'organisation directe
            try:
                organization = OrgModel.objects.get(id=org_id)
                logger.info(f"[Membership] Organisation directe trouvée: {organization.name}")
            except OrgModel.DoesNotExist:
                logger.warning(f"[Membership] Pas d'organisation avec id={org_id}")

    # Priorité 2: federation_id dans les paramètres
    if not organization:
        fed_id = request.GET.get('federation_id') or request.POST.get('federation_id')
        if fed_id:
            try:
                federation = Federation.objects.select_related('organization').get(id=fed_id)
                if federation.organization:
                    organization = federation.organization
                else:
                    organization = federation.as_organization
                    if not organization:
                        organization = _create_organization_for_federation(federation)
            except Federation.DoesNotExist:
                pass

    # Priorité 3: Organisation de l'utilisateur via son profil
    if not organization:
        organization = get_organization_queryset(OrgModel, request.user).first()

    return organization, federation


def _create_organization_for_federation(federation):
    """
    Crée ou récupère une organisation liée à une fédération.
    Si aucune n'existe, crée une nouvelle organisation.
    """
    from apps.organizations.models import Organization as OrgModel

    # Chercher d'abord si une organisation existe avec old_federation_id
    org = OrgModel.objects.filter(old_federation_id=federation.id).first()
    if org:
        # Mettre à jour la FK de la fédération pour les prochains appels
        if not federation.organization:
            federation.organization = org
            federation.save(update_fields=['organization'])
        logger.info(f"[Membership] Organisation existante trouvée via old_federation_id: {org.name}")
        return org

    # Sinon, créer une nouvelle organisation
    try:
        org = OrgModel.objects.create(
            name=federation.name,
            description=federation.description or '',
            organization_type='national_federation',
            is_active=federation.is_active,
            old_federation_id=federation.id,
            created_by=federation.owner,
        )
        # Lier la fédération à cette nouvelle organisation
        federation.organization = org
        federation.save(update_fields=['organization'])
        logger.info(f"[Membership] Nouvelle organisation créée pour fédération {federation.id}: {org.name}")
        return org
    except Exception as e:
        logger.error(f"[Membership] Erreur création organisation: {e}")
        return None


@login_required
def membership_dashboard(request):
    """
    Tableau de bord principal du système d'adhésion
    """
    try:
        # Récupérer l'organisation (supporte federation_id et organization_id)
        organization, federation = get_organization_for_membership(request)
        if not organization:
            messages.warning(request, _("Aucune organisation associée trouvée."))
            # Rediriger vers le dashboard de la fédération si on vient de là
            if federation:
                return redirect('competitions:dashboard:federation', federation_id=federation.id)
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
            'federation': federation,
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
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
        return redirect('membership:dashboard')

    packages = MembershipPackage.objects.filter(
        organization=organization
    ).order_by('sort_order', 'name')

    context = {
        'packages': packages,
        'organization': organization,
        'federation': federation,
        'page_title': _('Packages d\'adhésion'),
    }

    return render(request, 'membership/packages/list.html', context)


@login_required
def subscription_list(request):
    """
    Liste des souscriptions d'adhésion
    """
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
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
        'federation': federation,
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
    organization, federation = get_organization_for_membership(request)
    if organization and subscription.package.organization != organization:
        messages.error(request, _("Accès non autorisé à cette souscription."))
        return redirect('membership:subscription_list')

    context = {
        'subscription': subscription,
        'federation': federation,
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
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
        return redirect('membership:dashboard')

    # Analytics avancées
    retention_data = MembershipAnalyticsService.get_retention_rate(organization)
    popular_packages = MembershipAnalyticsService.get_popular_packages(organization)
    revenue_trend = MembershipAnalyticsService.get_revenue_trend(organization, 12)

    context = {
        'organization': organization,
        'federation': federation,
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
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
        return redirect('membership:package_list')

    if request.method == 'POST':
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(request.POST, organization=organization)
        if form.is_valid():
            package = form.save()
            messages.success(
                request,
                _("Package '{}' créé avec succès.").format(package.name)
            )
            # Rediriger avec le bon paramètre
            if federation:
                return redirect(f"/fr/membership/packages/?organization_id={federation.id}")
            return redirect('membership:package_list')
    else:
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(organization=organization)

    context = {
        'form': form,
        'organization': organization,
        'federation': federation,
        'page_title': _('Créer un package d\'adhésion'),
    }

    return render(request, 'membership/packages/create.html', context)


@login_required
def package_edit(request, pk):
    """
    Modifier un package d'adhésion existant
    """
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
        return redirect('membership:package_list')

    package = get_object_or_404(MembershipPackage, pk=pk, organization=organization)

    if request.method == 'POST':
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(
            request.POST, instance=package, organization=organization
        )
        if form.is_valid():
            package = form.save()
            messages.success(
                request,
                _("Package '{}' modifié avec succès.").format(package.name)
            )
            return redirect('membership:package_list')
    else:
        from .forms import MembershipPackageForm
        form = MembershipPackageForm(instance=package, organization=organization)

    context = {
        'form': form,
        'package': package,
        'organization': organization,
        'federation': federation,
        'page_title': _('Modifier le package'),
    }

    return render(request, 'membership/packages/edit.html', context)

@login_required
def package_delete(request, pk):
    messages.info(request, _("Suppression de package - Fonctionnalité en développement"))
    return redirect('membership:package_list')

@login_required
def subscription_create(request):
    """
    Créer une nouvelle souscription d'adhésion
    """
    organization, federation = get_organization_for_membership(request)
    if not organization:
        messages.warning(request, _("Aucune organisation associée trouvée."))
        if federation:
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
        return redirect('membership:subscription_list')

    if request.method == 'POST':
        from .forms import MembershipSubscriptionForm
        form = MembershipSubscriptionForm(request.POST, organization=organization)
        if form.is_valid():
            subscription = form.save()
            messages.success(
                request,
                _("Souscription créée avec succès pour {}.").format(
                    subscription.practitioner.full_name if subscription.practitioner else _("le pratiquant")
                )
            )
            # Rediriger vers la liste avec le bon paramètre
            if federation:
                return redirect(f"/fr/membership/subscriptions/?organization_id={federation.id}")
            return redirect('membership:subscription_list')
    else:
        from .forms import MembershipSubscriptionForm
        form = MembershipSubscriptionForm(organization=organization)

    context = {
        'form': form,
        'organization': organization,
        'federation': federation,
        'page_title': _('Nouvelle souscription'),
    }

    return render(request, 'membership/subscriptions/create.html', context)

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