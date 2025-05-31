from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

from .models import Family, FamilyMember, FamilyEvent, FamilyPaymentGroup
from competitions.models import Practitioner, Competition
from .permissions import family_access_required
from .services import FamilyManagementService
from .calendar_service import FamilyCalendarService
from .notification_service import FamilyNotificationService


@login_required
def family_dashboard(request):
    """
    Vue principale du tableau de bord familial.
    Affiche une vue d'ensemble de toutes les familles gérées par l'utilisateur.
    """
    # Récupérer toutes les familles où l'utilisateur est responsable principal
    managed_families = Family.objects.filter(
        primary_responsible=request.user,
        is_active=True
    ).prefetch_related('members__practitioner')
    
    # Récupérer les familles où l'utilisateur est membre
    member_families = Family.objects.filter(
        members__user=request.user,
        members__is_active=True,
        is_active=True
    ).exclude(primary_responsible=request.user).distinct()
    
    context = {
        'managed_families': managed_families,
        'member_families': member_families,
        'total_managed_families': managed_families.count(),
        'total_member_families': member_families.count(),
    }
    
    return render(request, 'family_management/dashboard.html', context)


@login_required
def family_detail(request, family_id):
    """
    Vue détaillée d'une famille spécifique.
    Affiche tous les membres, événements, paiements, etc.
    """
    family = get_object_or_404(Family, id=family_id)
    
    # Vérifier les permissions
    if not _can_access_family(request.user, family):
        messages.error(request, _("Vous n'avez pas accès à cette famille."))
        return redirect('family_management:dashboard')
    
    # Récupérer les membres actifs
    members = family.members.filter(is_active=True).select_related(
        'practitioner', 'user'
    ).order_by('role', 'joined_at')
    
    # Récupérer les événements à venir (30 prochains jours)
    upcoming_events = _get_upcoming_family_events(family)
    
    # Récupérer les paiements en attente
    pending_payments = family.payment_groups.filter(is_paid=False)
    
    # Statistiques
    stats = _calculate_family_stats(family)
    
    context = {
        'family': family,
        'members': members,
        'upcoming_events': upcoming_events,
        'pending_payments': pending_payments,
        'stats': stats,
        'can_manage': _can_manage_family(request.user, family),
    }
    
    return render(request, 'family_management/family_detail.html', context)


@login_required
def family_calendar(request, family_id):
    """
    Vue du calendrier familial consolidé.
    Affiche tous les événements des membres de la famille.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_access_family(request.user, family):
        messages.error(request, _("Vous n'avez pas accès à cette famille."))
        return redirect('family_management:dashboard')
    
    # Récupérer les membres pour filtrage
    members = family.members.filter(
        is_active=True,
        share_calendar=True
    ).select_related('practitioner', 'user')
    
    # Filtres par membre
    selected_members = request.GET.getlist('members')
    if selected_members:
        members = members.filter(id__in=selected_members)
    
    context = {
        'family': family,
        'members': members,
        'selected_members': selected_members,
        'can_manage': _can_manage_family(request.user, family),
    }
    
    return render(request, 'family_management/family_calendar.html', context)


@login_required
def family_calendar_api(request, family_id):
    """
    API pour récupérer les événements du calendrier familial au format JSON.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_access_family(request.user, family):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Récupérer les paramètres de date
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Start and end dates required'}, status=400)
    
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    events = []
    
    # Événements familiaux
    family_events = FamilyEvent.objects.filter(
        family=family,
        start_date__gte=start_dt,
        start_date__lte=end_dt
    )
    
    for event in family_events:
        events.append({
            'id': f'family_{event.id}',
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat() if event.end_date else None,
            'color': '#007bff',  # Bleu pour les événements familiaux
            'extendedProps': {
                'type': 'family',
                'description': event.description,
                'location': event.location,
            }
        })
    
    # TODO: Ajouter les événements des compétitions, entraînements, etc.
    # des membres de la famille
    
    return JsonResponse(events, safe=False)


@login_required
def family_members_management(request, family_id):
    """
    Vue pour gérer les membres d'une famille.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_manage_family(request.user, family):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette famille."))
        return redirect('family_management:family_detail', family_id=family_id)
    
    members = family.members.all().select_related('practitioner', 'user').order_by('role', 'joined_at')
    
    # Récupérer les pratiquants disponibles pour ajout
    existing_practitioners = members.values_list('practitioner_id', flat=True)
    available_practitioners = Practitioner.objects.filter(
        organization=family.organization
    ).exclude(id__in=existing_practitioners)
    
    context = {
        'family': family,
        'members': members,
        'available_practitioners': available_practitioners,
    }
    
    return render(request, 'family_management/members_management.html', context)


@login_required
def add_family_member(request, family_id):
    """
    Ajouter un nouveau membre à une famille.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_manage_family(request.user, family):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        practitioner_id = request.POST.get('practitioner_id')
        role = request.POST.get('role', 'child')
        
        if not practitioner_id:
            return JsonResponse({'error': 'Practitioner ID required'}, status=400)
        
        try:
            practitioner = Practitioner.objects.get(id=practitioner_id)
            
            # Vérifier que le pratiquant n'est pas déjà membre de cette famille
            if FamilyMember.objects.filter(family=family, practitioner=practitioner).exists():
                return JsonResponse({'error': 'Ce pratiquant est déjà membre de cette famille'}, status=400)
            
            # Créer le membre
            member = FamilyMember.objects.create(
                family=family,
                practitioner=practitioner,
                user=practitioner.user,
                role=role
            )
            
            messages.success(request, _("Membre ajouté avec succès à la famille."))
            return JsonResponse({'success': True, 'member_id': member.id})
            
        except Practitioner.DoesNotExist:
            return JsonResponse({'error': 'Practitioner not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def family_payments(request, family_id):
    """
    Vue pour gérer les paiements familiaux.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_access_family(request.user, family):
        messages.error(request, _("Vous n'avez pas accès à cette famille."))
        return redirect('family_management:dashboard')
    
    # Récupérer tous les groupes de paiements
    payment_groups = family.payment_groups.all().order_by('-created_at')
    
    # Paginer les résultats
    paginator = Paginator(payment_groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculer les totaux
    total_pending = payment_groups.filter(is_paid=False).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_paid = payment_groups.filter(is_paid=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'family': family,
        'page_obj': page_obj,
        'total_pending': total_pending,
        'total_paid': total_paid,
        'can_manage': _can_manage_family(request.user, family),
    }
    
    return render(request, 'family_management/family_payments.html', context)


# Fonctions utilitaires

def _can_access_family(user, family):
    """
    Vérifie si un utilisateur peut accéder à une famille.
    """
    # Responsable principal
    if family.primary_responsible == user:
        return True
    
    # Membre de la famille
    if family.members.filter(user=user, is_active=True).exists():
        return True
    
    # Admin ou staff
    if user.is_staff or user.is_superuser:
        return True
    
    return False


def _can_manage_family(user, family):
    """
    Vérifie si un utilisateur peut gérer une famille.
    """
    # Responsable principal
    if family.primary_responsible == user:
        return True
    
    # Membre avec permissions de gestion
    member = family.members.filter(user=user, is_active=True).first()
    if member and member.has_permission('manage_family'):
        return True
    
    # Admin ou staff
    if user.is_staff or user.is_superuser:
        return True
    
    return False


def _get_upcoming_family_events(family, days=30):
    """
    Récupère les événements à venir pour une famille.
    """
    end_date = timezone.now() + timedelta(days=days)
    
    return FamilyEvent.objects.filter(
        family=family,
        start_date__gte=timezone.now(),
        start_date__lte=end_date
    ).order_by('start_date')[:5]


def _calculate_family_stats(family):
    """
    Calcule les statistiques d'une famille.
    """
    members = family.members.filter(is_active=True)
    practitioners = [m.practitioner for m in members if m.practitioner and m.practitioner.status == 'active']
    
    stats = {
        'total_members': members.count(),
        'total_practitioners': len(practitioners),
        'total_children': members.filter(role='child').count(),
        'total_parents': members.filter(role__in=['parent', 'guardian']).count(),
        'pending_payments': family.payment_groups.filter(is_paid=False).count(),
        'upcoming_events': _get_upcoming_family_events(family).count(),
    }
    
    return stats


# === NOUVELLES VUES POUR CALENDRIER ET NOTIFICATIONS ===

@login_required
@family_access_required
def family_calendar(request, family_id):
    """
    Vue du calendrier familial consolidé.
    """
    family = get_object_or_404(Family, id=family_id)
    
    context = {
        'family': family,
        'can_manage': _can_manage_family(request.user, family),
    }
    
    return render(request, 'family_management/family_calendar.html', context)


@login_required
@family_access_required
def family_calendar_api(request, family_id):
    """
    API pour récupérer les données du calendrier familial.
    """
    family = get_object_or_404(Family, id=family_id)
    
    # Paramètres de la requête
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    member_filters = request.GET.get('members', 'all')
    
    try:
        # Parser les dates
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '')).date()
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '')).date()
        
        # Parser les filtres de membres
        if member_filters != 'all':
            member_filters = [int(x) for x in member_filters.split(',') if x.isdigit()]
        else:
            member_filters = None
        
        # Utiliser le service de calendrier
        calendar_service = FamilyCalendarService(family)
        calendar_data = calendar_service.get_consolidated_calendar(
            start_date=start_date,
            end_date=end_date,
            member_filters=member_filters
        )
        
        # Formater les événements pour FullCalendar
        events = []
        for date_key, day_events in calendar_data['events_by_date'].items():
            for event in day_events:
                events.append({
                    'id': event['id'],
                    'title': event['title'],
                    'start_date': event['start_date'].isoformat() if hasattr(event['start_date'], 'isoformat') else str(event['start_date']),
                    'start_time': str(event['start_time']) if event['start_time'] else None,
                    'end_date': event['end_date'].isoformat() if event['end_date'] and hasattr(event['end_date'], 'isoformat') else str(event['end_date']) if event['end_date'] else None,
                    'end_time': str(event['end_time']) if event['end_time'] else None,
                    'description': event['description'],
                    'location': event['location'],
                    'type': event['type'],
                    'color': event['color'],
                    'icon': event['icon'],
                    'can_edit': event['can_edit'],
                    'concerned_members': event.get('concerned_members', []),
                    'participating_members': event.get('participating_members', [])
                })
        
        return JsonResponse({
            'success': True,
            'events': events,
            'metadata': calendar_data['metadata']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@family_access_required
@require_http_methods(["POST", "DELETE"])
def create_family_event(request, family_id):
    """
    Créer ou supprimer un événement familial.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_manage_family(request.user, family):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            location = request.POST.get('location', '')
            is_private = request.POST.get('is_private') == 'on'
            concerned_members = request.POST.getlist('concerned_members')
            
            if not title or not start_date:
                return JsonResponse({
                    'success': False,
                    'error': 'Titre et date de début requis'
                }, status=400)
            
            # Parser les dates
            start_datetime = datetime.fromisoformat(start_date)
            end_datetime = None
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
            
            # Créer l'événement
            event = FamilyEvent.objects.create(
                family=family,
                title=title,
                description=description,
                start_date=start_datetime,
                end_date=end_datetime,
                location=location,
                is_private=is_private,
                created_by=request.user
            )
            
            # Ajouter les membres concernés
            if concerned_members:
                members = FamilyMember.objects.filter(
                    family=family,
                    id__in=concerned_members
                )
                event.concerned_members.set(members)
            
            # Envoyer une notification
            notification_service = FamilyNotificationService(family)
            notification_service.notify_event_reminder(event, hours_before=24)
            
            return JsonResponse({
                'success': True,
                'event_id': event.id,
                'message': 'Événement créé avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    elif request.method == 'DELETE':
        try:
            # Récupérer l'ID de l'événement à supprimer
            data = json.loads(request.body)
            event_id = data.get('event_id')
            
            if not event_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID d\'événement requis'
                }, status=400)
            
            # Récupérer et supprimer l'événement
            event = get_object_or_404(FamilyEvent, id=event_id.split('_')[-1], family=family)
            event.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Événement supprimé avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
@family_access_required
def family_notifications_center(request, family_id):
    """
    Centre de gestion des notifications familiales.
    """
    family = get_object_or_404(Family, id=family_id)
    
    context = {
        'family': family,
        'can_manage': _can_manage_family(request.user, family),
    }
    
    return render(request, 'family_management/notifications_center.html', context)


@login_required
@family_access_required
@require_http_methods(["POST"])
def send_family_notification(request, family_id):
    """
    Envoyer une notification à la famille.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_manage_family(request.user, family):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        # Récupérer les paramètres
        notification_type = request.POST.get('type')
        message = request.POST.get('message')
        recipients = request.POST.getlist('recipients')
        channels = request.POST.getlist('channels')
        
        if not notification_type or not message:
            return JsonResponse({
                'success': False,
                'error': 'Type et message requis'
            }, status=400)
        
        # Préparer le contexte
        context = {
            'custom_message': message,
            'sender': request.user.get_full_name()
        }
        
        # Envoyer la notification
        notification_service = FamilyNotificationService(family)
        result = notification_service.send_family_notification(
            notification_type=notification_type,
            context=context,
            recipients=recipients if recipients else None,
            channels=channels if channels else ['email', 'in_app']
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@family_access_required
def family_weekly_summary(request, family_id):
    """
    Générer et envoyer le résumé hebdomadaire.
    """
    family = get_object_or_404(Family, id=family_id)
    
    if not _can_manage_family(request.user, family):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        notification_service = FamilyNotificationService(family)
        result = notification_service.send_weekly_summary()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@family_access_required
def family_availability_check(request, family_id):
    """
    Vérifier la disponibilité des membres pour une date.
    """
    family = get_object_or_404(Family, id=family_id)
    
    target_date = request.GET.get('date')
    if not target_date:
        return JsonResponse({
            'success': False,
            'error': 'Date requise'
        }, status=400)
    
    try:
        # Parser la date
        target_date = datetime.fromisoformat(target_date).date()
        
        # Utiliser le service de calendrier
        calendar_service = FamilyCalendarService(family)
        availability = calendar_service.get_member_availability(target_date)
        
        return JsonResponse({
            'success': True,
            'date': target_date.isoformat(),
            'availability': availability
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@family_access_required
def suggest_optimal_time(request, family_id):
    """
    Suggérer le meilleur créneau pour un événement familial.
    """
    family = get_object_or_404(Family, id=family_id)
    
    target_date = request.GET.get('date')
    duration = int(request.GET.get('duration', 60))  # minutes
    
    if not target_date:
        return JsonResponse({
            'success': False,
            'error': 'Date requise'
        }, status=400)
    
    try:
        # Parser la date
        target_date = datetime.fromisoformat(target_date).date()
        
        # Utiliser le service de calendrier
        calendar_service = FamilyCalendarService(family)
        suggestions = calendar_service.suggest_optimal_time(target_date, duration)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)