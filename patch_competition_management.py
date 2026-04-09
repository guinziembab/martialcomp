#!/usr/bin/env python
"""Patch pour corriger l'erreur dans competition_management_dashboard"""

import os
import sys

# Configuration Django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=== Patch pour competition_management_dashboard ===")

# Contenu du patch
patch_content = '''
import os
import sys

# Lire le fichier
file_path = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/competitions.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer la partie problématique
old_code = """def competition_management_dashboard(request):
    \"\"\"
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    \"\"\"
    club = get_user_club_safe(request)
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        # Si aucun club trouvé, essayer de créer ou rediriger vers une page appropriée
        try:
            messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        except:
            pass  # Ignorer si les messages ne fonctionnent pas
        return redirect('competitions:dashboard:club')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)"""

new_code = """def competition_management_dashboard(request):
    \"\"\"
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    \"\"\"
    # Récupérer le club et l'organisation de manière sûre
    club = None
    club_organization = None
    
    # D'abord essayer via l'organisation du middleware
    if hasattr(request, 'user_organization') and request.user_organization:
        club_organization = request.user_organization
        # Trouver le club associé
        from apps.competitions.models import Club as ClubModel
        club = ClubModel.objects.filter(
            organization=club_organization,
            owner=request.user
        ).first()
        if not club:
            # Si pas de club owned, prendre le premier de cette org
            club = ClubModel.objects.filter(organization=club_organization).first()
    
    # Si pas trouvé, chercher directement par owner
    if not club:
        from apps.competitions.models import Club as ClubModel
        club = ClubModel.objects.filter(owner=request.user).first()
        if club and hasattr(club, 'organization'):
            club_organization = club.organization
    
    # Vérifications avec return appropriés
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:club')
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:competitions')
    
    # Le reste du code continue normalement
    # club_organization est maintenant garanti d'être une Organization valide"""

# Appliquer le patch
if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Patch appliqué avec succès!")
else:
    print("⚠️  Le code exact n'a pas été trouvé. Vérification manuelle nécessaire.")
'''

# Sauvegarder le script de patch
with open('/tmp/apply_competition_patch.py', 'w') as f:
    f.write(patch_content)

print("\nPour appliquer le patch:")
print("1. ssh martialcomp-production")
print("2. cd /var/www/vhosts/martialcomp.com/httpdocs")
print("3. python /tmp/apply_competition_patch.py")
print("4. sudo systemctl restart martialcomp.service")