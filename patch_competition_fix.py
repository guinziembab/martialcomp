#!/usr/bin/env python
"""Patch pour corriger l'erreur dans competition_management_dashboard"""

import re

print("Lecture du fichier competitions.py...")
file_path = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/competitions.py'

# Backup
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

backup_path = file_path + '.backup_competition_fix'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Backup créé: {backup_path}")

# 1. D'abord corriger get_user_club_safe pour qu'elle retourne toujours un Club
old_get_user_club = """def get_user_club_safe(request):
    \"\"\"Récupère le club de l'utilisateur de façon sécurisée\"\"\"
    # Vérifier d'abord si request.club existe (via décorateur)
    if hasattr(request, 'club') and request.club:
        return request.club
    
    # Sinon chercher via UserProfile
    try:
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and profile.organization:
            return profile.organization
    except:
        pass
    
    # Fallback: chercher via ownership
    try:
        from apps.competitions.models import Club
        return Club.objects.filter(owner=request.user).first()
    except:
        pass
    
    return None"""

new_get_user_club = """def get_user_club_safe(request):
    \"\"\"Récupère le club de l'utilisateur de façon sécurisée - retourne toujours un Club\"\"\"
    # Vérifier d'abord si request.club existe (via décorateur)
    if hasattr(request, 'club') and request.club:
        from apps.competitions.models import Club
        # Si c'est déjà un Club, le retourner
        if isinstance(request.club, Club):
            return request.club
        # Si c'est une Organization, trouver le club associé
        else:
            club = Club.objects.filter(organization=request.club, owner=request.user).first()
            if not club:
                club = Club.objects.filter(organization=request.club).first()
            return club
    
    # Chercher via l'organisation du middleware
    if hasattr(request, 'user_organization') and request.user_organization:
        from apps.competitions.models import Club
        club = Club.objects.filter(organization=request.user_organization, owner=request.user).first()
        if not club:
            club = Club.objects.filter(organization=request.user_organization).first()
        if club:
            return club
    
    # Chercher via UserProfile
    try:
        from apps.competitions.models.users import UserProfile
        from apps.competitions.models import Club
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and profile.organization:
            club = Club.objects.filter(organization=profile.organization, owner=request.user).first()
            if not club:
                club = Club.objects.filter(organization=profile.organization).first()
            return club
    except:
        pass
    
    # Fallback: chercher via ownership directe
    try:
        from apps.competitions.models import Club
        return Club.objects.filter(owner=request.user).first()
    except:
        pass
    
    return None"""

# Appliquer le premier patch
if old_get_user_club in content:
    content = content.replace(old_get_user_club, new_get_user_club)
    print("✓ get_user_club_safe corrigée")
else:
    print("⚠️  get_user_club_safe: pattern exact non trouvé")

# 2. Maintenant corriger competition_management_dashboard
# Chercher la section problématique plus précisément
old_section = """@login_required
def competition_management_dashboard(request):
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
            messages.error(request, _(\"Vous devez être responsable de club pour accéder à cette page.\"))
        except:
            pass  # Ignorer si les messages ne fonctionnent pas
        return redirect('competitions:dashboard:club')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        try:
            messages.warning(request, _(\"Aucune organisation associée trouvée pour ce club.\"))
        except:
            pass  # Ignorer si les messages ne fonctionnent pas
        return redirect('competitions:club:competitions')"""

new_section = """@login_required
def competition_management_dashboard(request):
    \"\"\"
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    \"\"\"
    # Récupérer le club avec get_user_club_safe qui retourne maintenant toujours un Club
    club = get_user_club_safe(request)
    
    if not club:
        messages.error(request, _(\"Vous devez être responsable de club pour accéder à cette page.\"))
        return redirect('competitions:dashboard:club')
    
    # Vérifier si le club a une organisation associée
    club_organization = None
    if hasattr(club, 'organization'):
        club_organization = club.organization
    
    if not club_organization:
        messages.warning(request, _(\"Aucune organisation associée trouvée pour ce club.\"))
        return redirect('competitions:club:competitions')"""

# Appliquer le deuxième patch
if old_section in content:
    content = content.replace(old_section, new_section)
    print("✓ competition_management_dashboard corrigée")
else:
    print("⚠️  competition_management_dashboard: pattern exact non trouvé, essai alternatif...")
    # Essayer de corriger juste les lignes problématiques
    lines = content.split('\n')
    in_function = False
    modified = False
    
    for i, line in enumerate(lines):
        if 'def competition_management_dashboard(request):' in line:
            in_function = True
        elif in_function and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            in_function = False
            
        if in_function:
            # Remplacer la ligne problématique
            if 'club_organization = club.organization or getattr(club' in line:
                lines[i] = '    # Vérifier si le club a une organisation associée'
                lines.insert(i+1, '    club_organization = None')
                lines.insert(i+2, '    if hasattr(club, \'organization\'):')
                lines.insert(i+3, '        club_organization = club.organization')
                modified = True
                print("✓ Ligne problématique corrigée")
                break
    
    if modified:
        content = '\n'.join(lines)

# Sauvegarder
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Patch terminé!")
print("Les changements ont été appliqués à competitions.py")