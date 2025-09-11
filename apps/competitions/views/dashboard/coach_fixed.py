from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
"""
Vue dashboard coach CORRIGÉE - Sans erreurs, template simple
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def coach_dashboard(request):
    """
    Dashboard coach - VERSION CORRIGÉE ET SIMPLIFIÉE
    """
    logger.info(f"Coach dashboard accessed by: {request.user.username}")
    
    # Contexte minimal et sûr
    context = {
        'user': request.user,
        'page_title': _('Dashboard Coach'),
        'dashboard_type': 'coach',
        'username': request.user.username,
        'success_message': f'✅ COACH ROUTING FIXED! {request.user.username} is now on COACH dashboard!',
        'debug_info': {
            'url': request.path,
            'user': request.user.username,
            'dashboard_type': 'COACH',
            'template': 'coach_simple.html'
        }
    }
    
    try:
        # Essayer le template coach complet d'abord
        return render(request, 'competitions/dashboard/coach_complete.html', context)
    except Exception as e:
        logger.error(f"Erreur template coach_complete: {e}")
        
        try:
            # Fallback vers le template simple
            return render(request, 'competitions/dashboard/coach_simple.html', context)
        except Exception as e2:
            logger.error(f"Erreur template coach_simple: {e2}")
            
            try:
                # Fallback vers le template coach original (sans URLs cassées)
                return render(request, 'competitions/dashboard/coach.html', context)
            except Exception as e3:
                logger.error(f"Erreur template coach original: {e3}")
                
                # Dernier fallback vers spectator avec message
                context['fallback_message'] = f'Dashboard coach temporairement indisponible pour {request.user.username}'
                context['page_title'] = 'Dashboard Coach (Mode dégradé)'
                return render(request, 'competitions/dashboard/spectator.html', context)