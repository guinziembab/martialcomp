from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
"""
Vue d'urgence pour le dashboard coach - SANS ERREURS
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def coach_dashboard_emergency(request):
    """Dashboard coach d'urgence - Version ultra-simple sans erreurs"""
    
    logger.info(f"COACH DASHBOARD EMERGENCY - User: {request.user.username}")
    
    context = {
        'user': request.user,
        'page_title': 'Dashboard Coach (Mode d\'urgence)',
        'dashboard_type': 'coach',
        'username': request.user.username,
        'success_message': f'SUCCÈS ! {request.user.username} est maintenant sur le dashboard COACH !',
        'emergency_mode': True
    }
    
    # Template minimal HTML intégré pour éviter les erreurs de template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Coach - {request.user.username}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; }}
            .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 DASHBOARD COACH - MODE D'URGENCE</h1>
            <h2>Utilisateur: {request.user.username}</h2>
        </div>
        
        <div class="success">
            <h3>✅ SUCCÈS ! Le routage coach fonctionne maintenant !</h3>
            <p><strong>{request.user.username}</strong> est correctement dirigé vers le dashboard <strong>COACH</strong> !</p>
        </div>
        
        <div class="info">
            <h4>📋 Informations de debug:</h4>
            <ul>
                <li>Utilisateur: {request.user.username}</li>
                <li>URL actuelle: {request.path}</li>
                <li>Dashboard: COACH</li>
                <li>Mode: Urgence (sans template complexe)</li>
            </ul>
        </div>
        
        <div class="info">
            <h4>🔄 Prochaines étapes:</h4>
            <ol>
                <li>Le routage coach fonctionne maintenant</li>
                <li>Vous pouvez maintenant corriger le template coach.html</li>
                <li>Remplacer cette vue d'urgence par la vraie vue coach</li>
            </ol>
        </div>
        
        <div class="info">
            <p><a href="/competitions/dashboard/spectator/">🔗 Aller au dashboard spectator</a></p>
            <p><a href="/accounts/logout/">🚪 Se déconnecter</a></p>
        </div>
    </body>
    </html>
    """
    
    from django.http import HttpResponse
    return HttpResponse(html_content)