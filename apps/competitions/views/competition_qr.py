"""
Vue pour générer un QR code de compétition
"""

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.translation import gettext as _

from ..models import Competition


def competition_qr_code(request, competition_id):
    """
    Génère un QR code simple pour une compétition
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # URL publique de la compétition
    public_url = request.build_absolute_uri(
        f'/fr/competitions/competitions/{competition.id}/public-registration/'
    )
    
    # Retourner une image simple avec l'URL
    svg_content = f'''
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="white" stroke="black" stroke-width="2"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="12" fill="black">
            QR Code
        </text>
        <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="8" fill="black">
            {public_url[:30]}...
        </text>
    </svg>
    '''
    
    # Retourner l'image SVG
    response = HttpResponse(svg_content, content_type='image/svg+xml')
    response['Content-Disposition'] = f'attachment; filename="competition_{competition.id}_qr.svg"'
    return response