#!/bin/bash
# Script de déploiement pour corriger l'erreur competition_management_dashboard

echo "=== Déploiement de la correction pour competition_management_dashboard ==="

# Créer le script Python de patch
cat > fix_competition_view.py << 'EOF'
import re

print("Lecture du fichier competitions.py...")
file_path = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/competitions.py'

# Backup
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

backup_path = file_path + '.backup_' + __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Backup créé: {backup_path}")

# Rechercher la fonction competition_management_dashboard
pattern = r'(@login_required\s+def competition_management_dashboard\(request\):.*?)(# Obtenir la date actuelle)'

def replacement(match):
    return '''@login_required
def competition_management_dashboard(request):
    """
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    """
    # Récupérer le club de l'utilisateur de manière sûre
    club = None
    club_organization = None
    
    # D'abord essayer via l'organisation du middleware
    if hasattr(request, 'user_organization') and request.user_organization:
        club_organization = request.user_organization
        # Trouver le club associé
        from apps.competitions.models import Club
        club = Club.objects.filter(
            organization=club_organization,
            owner=request.user
        ).first()
        if not club:
            # Si pas de club owned, prendre le premier de cette org
            club = Club.objects.filter(organization=club_organization).first()
    
    # Si pas trouvé, chercher directement par owner
    if not club:
        from apps.competitions.models import Club
        club = Club.objects.filter(owner=request.user).first()
        if club and hasattr(club, 'organization'):
            club_organization = club.organization
    
    # Vérifications avec return appropriés
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:club')
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:competitions')
    
    # Obtenir la date actuelle'''

# Appliquer le patch
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ Patch appliqué avec succès!")
else:
    print("⚠️  Le pattern exact n'a pas été trouvé. Tentative de remplacement alternatif...")
    
    # Méthode alternative: chercher et remplacer la section problématique
    old_section = """@login_required
def competition_management_dashboard(request):
    \"\"\"
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    \"\"\"
    club = request.club
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
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        try:
            messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
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
    # Récupérer le club de l'utilisateur de manière sûre
    club = None
    club_organization = None
    
    # D'abord essayer via l'organisation du middleware
    if hasattr(request, 'user_organization') and request.user_organization:
        club_organization = request.user_organization
        # Trouver le club associé
        from apps.competitions.models import Club
        club = Club.objects.filter(
            organization=club_organization,
            owner=request.user
        ).first()
        if not club:
            # Si pas de club owned, prendre le premier de cette org
            club = Club.objects.filter(organization=club_organization).first()
    
    # Si pas trouvé, chercher directement par owner
    if not club:
        from apps.competitions.models import Club
        club = Club.objects.filter(owner=request.user).first()
        if club and hasattr(club, 'organization'):
            club_organization = club.organization
    
    # Vérifications avec return appropriés
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:club')
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:competitions')"""
        
    if old_section in content:
        content = content.replace(old_section, new_section)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Patch appliqué avec succès (méthode alternative)!")
    else:
        print("❌ Impossible d'appliquer le patch automatiquement.")
        print("   Veuillez vérifier le fichier manuellement.")
EOF

# Se connecter au serveur et exécuter
ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Application du patch..."
/var/www/vhosts/martialcomp.com/venv/bin/python fix_competition_view.py

echo "Redémarrage du service..."
sudo systemctl restart martialcomp.service

echo "Vérification du statut..."
sudo systemctl status martialcomp.service | head -20

echo "=== Déploiement terminé ==="
ENDSSH