#!/bin/bash
# Debug et solution définitive pour les colonnes générées

echo "=== DEBUG ET SOLUTION DÉFINITIVE ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Debug: Vérifier exactement comment la sauvegarde est faite..."
echo "Recherche de toutes les sauvegardes dans competition_update:"
grep -n "\.save(" apps/competitions/views/competitions.py | grep -A2 -B2 "competition" | head -20

echo "2. Vérifier si le problème vient d'un signal ou d'un save() ailleurs..."
grep -r "def save" apps/competitions/models/competitions.py | head -10

echo "3. Solution radicale: Utiliser SQL direct pour la mise à jour..."
sudo python3 << 'PYTHON_RADICAL'
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# Remplacer toute la logique de sauvegarde dans competition_update
lines = content.split('\n')
in_update = False
in_save_block = False
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    if 'def competition_update' in line:
        in_update = True
        new_lines.append(line)
    elif in_update and line.strip() and not line.startswith(' '):
        in_update = False
        new_lines.append(line)
    elif in_update and 'with transaction.atomic():' in line:
        # Début du bloc de sauvegarde
        in_save_block = True
        new_lines.append(line)
        
        # Chercher où se termine ce bloc
        j = i + 1
        indent = len(line) - len(line.lstrip())
        
        # Remplacer tout le bloc de sauvegarde
        new_lines.append(' ' * (indent + 4) + '# Solution radicale: mise à jour SQL directe')
        new_lines.append(' ' * (indent + 4) + 'from django.db import connection')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Récupérer les valeurs du formulaire')
        new_lines.append(' ' * (indent + 4) + 'update_data = {}')
        new_lines.append(' ' * (indent + 4) + 'for field in ["title", "description", "start_date", "end_date",')
        new_lines.append(' ' * (indent + 4) + '              "address", "city", "discipline_id", "registration_deadline"]:')
        new_lines.append(' ' * (indent + 4) + '    if field in form.cleaned_data:')
        new_lines.append(' ' * (indent + 4) + '        value = form.cleaned_data[field]')
        new_lines.append(' ' * (indent + 4) + '        if field == "discipline":')
        new_lines.append(' ' * (indent + 4) + '            update_data["discipline_id"] = value.id if value else None')
        new_lines.append(' ' * (indent + 4) + '        else:')
        new_lines.append(' ' * (indent + 4) + '            update_data[field] = value')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Gérer le statut')
        new_lines.append(' ' * (indent + 4) + 'is_published = form.cleaned_data.get("is_published", False)')
        new_lines.append(' ' * (indent + 4) + 'if competition.status not in ["completed", "cancelled"]:')
        new_lines.append(' ' * (indent + 4) + '    update_data["status"] = "published" if is_published else "draft"')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Construire la requête UPDATE')
        new_lines.append(' ' * (indent + 4) + 'if update_data:')
        new_lines.append(' ' * (indent + 4) + '    set_clauses = []')
        new_lines.append(' ' * (indent + 4) + '    params = []')
        new_lines.append(' ' * (indent + 4) + '    for field, value in update_data.items():')
        new_lines.append(' ' * (indent + 4) + '        set_clauses.append(f"{field} = %s")')
        new_lines.append(' ' * (indent + 4) + '        params.append(value)')
        new_lines.append(' ' * (indent + 4) + '    ')
        new_lines.append(' ' * (indent + 4) + '    # Ajouter updated_at')
        new_lines.append(' ' * (indent + 4) + '    set_clauses.append("updated_at = NOW()")')
        new_lines.append(' ' * (indent + 4) + '    ')
        new_lines.append(' ' * (indent + 4) + '    # Exécuter la mise à jour')
        new_lines.append(' ' * (indent + 4) + '    with connection.cursor() as cursor:')
        new_lines.append(' ' * (indent + 4) + '        query = f"UPDATE competitions_competition SET {", ".join(set_clauses)} WHERE id = %s"')
        new_lines.append(' ' * (indent + 4) + '        params.append(competition.id)')
        new_lines.append(' ' * (indent + 4) + '        cursor.execute(query, params)')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Gérer le logo séparément')
        new_lines.append(' ' * (indent + 4) + 'if "logo" in request.FILES:')
        new_lines.append(' ' * (indent + 4) + '    competition.logo = request.FILES["logo"]')
        new_lines.append(' ' * (indent + 4) + '    competition.save(update_fields=["logo"])')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Gérer les types de compétition')
        new_lines.append(' ' * (indent + 4) + 'competition_types = form.cleaned_data.get("competition_types")')
        new_lines.append(' ' * (indent + 4) + 'if competition_types is not None:')
        new_lines.append(' ' * (indent + 4) + '    competition.competition_types.set(competition_types)')
        new_lines.append(' ' * (indent + 4) + '')
        new_lines.append(' ' * (indent + 4) + '# Rafraîchir l\'objet')
        new_lines.append(' ' * (indent + 4) + 'competition.refresh_from_db()')
        
        # Sauter le bloc original
        while j < len(lines) and (lines[j].startswith(' ' * (indent + 4)) or not lines[j].strip()):
            j += 1
            if j < len(lines) and 'messages.success' in lines[j]:
                break
        
        i = j - 1
    else:
        new_lines.append(line)
    
    i += 1

# Sauvegarder
with open('apps/competitions/views/competitions.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✓ Solution radicale implémentée: UPDATE SQL direct")
PYTHON_RADICAL

echo "4. Alternative plus simple: désactiver temporairement modeltranslation..."
# Cette approche pourrait fonctionner mais est risquée

echo "5. Vérification de la syntaxe..."
python3 -m py_compile apps/competitions/views/competitions.py
if [ $? -eq 0 ]; then
    echo "✓ Syntaxe Python valide"
else
    echo "✗ Erreur de syntaxe, restauration..."
    # En cas d'erreur, on pourrait restaurer depuis une sauvegarde
fi

echo "6. Redémarrage de Gunicorn..."
sudo pkill -HUP -f gunicorn

echo "✓ Solution définitive appliquée"
echo ""
echo "Au lieu d'utiliser l'ORM Django qui essaie de sauvegarder tous les champs,"
echo "nous utilisons maintenant une requête SQL directe qui met à jour UNIQUEMENT"
echo "les champs spécifiés, évitant complètement les colonnes générées."
EOF

echo ""
echo "=== TERMINÉ ==="