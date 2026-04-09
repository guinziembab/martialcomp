#!/usr/bin/env python
"""Script pour ajouter les vues API de gestion des types de compétitions"""

import os

print("=== Ajout des vues API pour la gestion des types ===\n")

# Contenu à ajouter dans le fichier api.py
api_content = '''

# === GESTION DES TYPES DE COMPETITIONS ===

@login_required
@require_POST
def create_competition_type(request, competition_id):
    """Créer un nouveau type de compétition pour une discipline"""
    from apps.competitions.models import Competition, CompetitionType
    
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions - adapter selon votre logique
    has_permission = False
    if request.user.is_superuser:
        has_permission = True
    elif hasattr(competition, 'organizing_federation') and competition.organizing_federation:
        if competition.organizing_federation.owner == request.user:
            has_permission = True
    elif hasattr(competition, 'organizing_organization') and competition.organizing_organization:
        # Vérifier si l'utilisateur est admin de l'organisation
        from apps.organizations.models import OrganizationMember
        if OrganizationMember.objects.filter(
            organization=competition.organizing_organization,
            user=request.user,
            role__in=['owner', 'admin']
        ).exists():
            has_permission = True
    
    if not has_permission:
        return JsonResponse({'success': False, 'error': 'Permissions insuffisantes'})
    
    try:
        # Créer le nouveau type
        competition_type = CompetitionType.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            discipline=competition.discipline,
            team_based=request.POST.get('team_based') == 'on',
            weight_category=request.POST.get('weight_category') == 'on',
            scoring_system=request.POST.get('scoring_system', 'technical')
        )
        
        # L'ajouter automatiquement à la compétition
        competition.types.add(competition_type)
        
        return JsonResponse({
            'success': True,
            'type_id': competition_type.id,
            'type_name': competition_type.name
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def remove_competition_type(request, competition_id, type_id):
    """Retirer un type de compétition d'une compétition"""
    from apps.competitions.models import Competition, CompetitionType
    
    competition = get_object_or_404(Competition, id=competition_id)
    competition_type = get_object_or_404(CompetitionType, id=type_id)
    
    # Vérifier les permissions
    has_permission = False
    if request.user.is_superuser:
        has_permission = True
    elif hasattr(competition, 'organizing_federation') and competition.organizing_federation:
        if competition.organizing_federation.owner == request.user:
            has_permission = True
    elif hasattr(competition, 'organizing_organization') and competition.organizing_organization:
        from apps.organizations.models import OrganizationMember
        if OrganizationMember.objects.filter(
            organization=competition.organizing_organization,
            user=request.user,
            role__in=['owner', 'admin']
        ).exists():
            has_permission = True
    
    if not has_permission:
        return JsonResponse({'success': False, 'error': 'Permissions insuffisantes'})
    
    try:
        # Retirer le type de la compétition (pas supprimer le type lui-même)
        competition.types.remove(competition_type)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
'''

# Fichier où ajouter les vues
api_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/api.py'

# Vérifier si le fichier existe
if os.path.exists(api_file):
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open(api_file + '.backup_types', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Backup créé: {api_file}.backup_types")
    
    # Ajouter le contenu si pas déjà présent
    if 'create_competition_type' not in content:
        content += api_content
        
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Vues API ajoutées")
    else:
        print("ℹ️  Les vues API existent déjà")
else:
    # Créer le fichier
    header = '''"""
Vues API pour les compétitions
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
'''
    
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(header + api_content)
    print(f"✓ Fichier API créé: {api_file}")

# Ajouter les URLs
urls_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls.py'

urls_to_add = '''
    # API pour la gestion des types de compétitions
    path('api/competition/<int:competition_id>/create-type/', 
         views.api.create_competition_type, 
         name='api_create_competition_type'),
    path('api/competition/<int:competition_id>/remove-type/<int:type_id>/', 
         views.api.remove_competition_type, 
         name='api_remove_competition_type'),
'''

print("\n📝 URLs à ajouter dans", urls_file)
print(urls_to_add)

print("\n✅ Vues API ajoutées avec succès!")