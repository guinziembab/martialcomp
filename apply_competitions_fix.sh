#!/bin/bash
# Script pour appliquer le fix sur competitions.py

echo "=== Application du fix pour competition_management_dashboard ==="

# Créer le script Python de patch
cat > /tmp/patch_competitions.py << 'EOF'
import re

# Lire le fichier
file_path = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/competitions.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
backup_path = file_path + '.backup_fix'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Backup créé: {backup_path}")

# Fix 1: Corriger get_user_club_safe
old_get_user_club = r'def get_user_club_safe\(request\):.*?(?=\n(?:def|class|@|\Z))'
new_get_user_club = '''def get_user_club_safe(request):
    """Récupère le club de l'utilisateur de façon sécurisée - retourne toujours un Club"""
    from apps.competitions.models import Club
    
    # Si request.club existe et est un Club
    if hasattr(request, 'club') and request.club:
        if isinstance(request.club, Club):
            return request.club
    
    # Chercher via l'organisation du middleware
    if hasattr(request, 'user_organization') and request.user_organization:
        club = Club.objects.filter(organization=request.user_organization, owner=request.user).first()
        if not club:
            club = Club.objects.filter(organization=request.user_organization).first()
        if club:
            return club
    
    # Chercher via UserProfile
    try:
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and profile.organization:
            club = Club.objects.filter(organization=profile.organization, owner=request.user).first()
            if not club:
                club = Club.objects.filter(organization=profile.organization).first()
            if club:
                return club
    except:
        pass
    
    # Fallback: ownership directe
    return Club.objects.filter(owner=request.user).first()
'''

content = re.sub(old_get_user_club, new_get_user_club, content, flags=re.DOTALL)

# Fix 2: Corriger le début de competition_management_dashboard
# Chercher depuis le début de la fonction jusqu'à "club_organization ="
old_pattern = r'(def competition_management_dashboard\(request\):.*?)(\n\s*#\s*Vérifier si le club.*?club_organization\s*=\s*club\.organization.*?)(?=\n)'

def replacement(match):
    func_def = match.group(1)
    return func_def + '''
    club = get_user_club_safe(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:club')
    
    # Vérifier si le club a une organisation associée
    club_organization = None
    if hasattr(club, 'organization'):
        club_organization = club.organization'''

content = re.sub(old_pattern, replacement, content, flags=re.DOTALL)

# Sauvegarder
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Patch appliqué avec succès!")
EOF

# Exécuter le patch
cd /var/www/vhosts/martialcomp.com/httpdocs
/var/www/vhosts/martialcomp.com/venv/bin/python /tmp/patch_competitions.py

# Redémarrer le service
echo "Redémarrage du service..."
sudo systemctl restart martialcomp.service

echo "=== Patch terminé ==="