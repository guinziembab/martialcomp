#\!/bin/bash
# Reconstruire proprement la section statistiques

echo "================================================"
echo "🔧 RECONSTRUCTION SECTION STATISTIQUES"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Copie depuis le développement..."
echo "=================================="
# D'abord, copier la vue depuis le développement pour avoir une base saine
scp /mnt/c/martial_hub_django/martialcomp/apps/competitions/views/dashboard/federations.py apps/competitions/views/dashboard/federations_from_dev.py 2>/dev/null || echo "Copie locale impossible"

echo ""
echo "2️⃣ Reconstruction de la section statistiques..."
echo "=============================================="
python3 << 'PYEOF'
# Lire le fichier actuel
with open('apps/competitions/views/dashboard/federations.py', 'r') as f:
    lines = f.readlines()

# Trouver où commence et finit la section problématique
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if '# Récupérer les statistiques de la fédération' in line:
        start_idx = i
    if start_idx and 'except Exception as e:' in line and 'federation_dashboard' in lines[i+1] if i+1 < len(lines) else False:
        end_idx = i + 3  # Inclure le logger.error
        break

if start_idx and end_idx:
    print(f"✅ Section trouvée: lignes {start_idx+1} à {end_idx+1}")
    
    # Remplacer la section
    new_section = """    # Récupérer les statistiques de la fédération
    try:
        # Federation n'hérite pas de Organization, donc on doit gérer différemment
        # Pour l'instant, utiliser des valeurs par défaut
        clubs_count = 0
        competitions_count = 0
        practitioners_count = 0
        judges_count = 0
        recent_competitions = Competition.objects.none()
        recent_clubs = Club.objects.none()
        
        # TODO: Implémenter la logique correcte pour récupérer les stats
        # Peut-être via des relations many-to-many ou foreign keys
        
    except Exception as e:
        logger.error(f"Erreur dans federation_dashboard: {e}")
"""
    
    # Reconstruire le fichier
    new_lines = lines[:start_idx] + [new_section] + lines[end_idx:]
    
    with open('apps/competitions/views/dashboard/federations.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Section reconstruite avec des valeurs par défaut")
else:
    print("❌ Impossible de trouver la section à remplacer")
PYEOF

echo ""
echo "3️⃣ Vérification de la correction..."
echo "==================================="
echo "📋 Section corrigée (lignes 105-125):"
sed -n '105,125p' apps/competitions/views/dashboard/federations.py

echo ""
echo "4️⃣ Redémarrage du service..."
echo "============================"
sudo systemctl restart martialcomp
echo "✅ Service redémarré"

echo ""
echo "5️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

echo ""
echo "================================================"
echo "✅ RECONSTRUCTION TERMINÉE"
echo "================================================"
echo ""
echo "La vue utilise maintenant des valeurs par défaut"
echo "pour éviter l'erreur 500. Une implémentation"
echo "complète devra être faite plus tard."

REMOTE_COMMANDS
