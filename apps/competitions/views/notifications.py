from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from ..models.notifications import Notification
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def notifications_list(request):
    """Page complète des notifications avec filtres"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Filtres
    notification_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'current_type': notification_type,
        'current_status': status,
    }
    
    return render(request, 'competitions/notifications/list.html', context)

@login_required
def notifications_api_list(request):
    """API pour récupérer les notifications récentes"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:7]
    
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'action_url': notification.action_url,
            'css_class': notification.css_class,
            'icon_class': notification.icon_class,
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        user=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({'success': True})

@login_required
@require_POST
def mark_all_read(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    messages.success(request, _('Toutes les notifications ont été marquées comme lues.'))
    return JsonResponse({'success': True})

def create_notification(user, title, message, notification_type='info', priority='standard', action_url=None, action_text=None):
    """Fonction utilitaire pour créer une notification"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url,
        action_text=action_text
    )

@login_required
def notifications_count(request):
    """API pour obtenir le nombre de notifications non lues"""
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({
        'success': True,
        'count': unread_count
    })

@login_required
def create_test_notifications(request):
    """Vue temporaire pour créer des notifications de test"""
    if request.method == 'POST':
        # Créer quelques notifications de test
        notifications_data = [
            {
                'title': 'Bienvenue sur MartialComp',
                'message': 'Votre compte a été configuré avec succès.',
                'notification_type': 'success'
            },
            {
                'title': 'Nouvelle compétition disponible',
                'message': 'Une nouvelle compétition de karaté est ouverte aux inscriptions.',
                'notification_type': 'info',
                'action_url': '/competitions/competitions/'
            },
            {
                'title': 'Action requise',
                'message': 'Veuillez compléter votre profil club.',
                'notification_type': 'warning'
            },
            {
                'title': 'Système de notifications amélioré',
                'message': 'Le nouveau système de notifications est maintenant actif avec cloche et badge dynamique.',
                'notification_type': 'info'
            },
            {
                'title': 'Test de notification critique',
                'message': 'Ceci est un test de notification avec priorité critique.',
                'notification_type': 'error',
                'priority': 'critical'
            }
        ]
        
        for notif_data in notifications_data:
            create_notification(
                user=request.user,
                title=notif_data['title'],
                message=notif_data['message'],
                notification_type=notif_data['notification_type'],
                priority=notif_data.get('priority', 'standard'),
                action_url=notif_data.get('action_url')
            )
        
        messages.success(request, 'Notifications de test créées avec succès!')
        return redirect('competitions:dashboard:club')
    
    return render(request, 'competitions/notifications/create_test.html')

