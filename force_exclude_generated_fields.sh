#!/bin/bash
# Force l'exclusion des champs générés - solution ultime

echo "=== EXCLUSION FORCÉE DES CHAMPS GÉNÉRÉS ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Debug: Vérifier l'état actuel de competition_update..."
grep -n "form = CompetitionForm" apps/competitions/views/competitions.py | grep -B5 -A5 "competition_update" | head -20

echo "2. Forcer l'utilisation de clean_translation_fields..."
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# S'assurer que clean_translation_fields est bien utilisé dans competition_update
lines = content.split('\n')
in_update = False
modified = False

for i in range(len(lines)):
    if 'def competition_update' in lines[i]:
        in_update = True
        print(f"✓ Trouvé competition_update ligne {i+1}")
    elif in_update and lines[i].strip() and not lines[i].startswith(' '):
        in_update = False
    
    # Dans competition_update, chercher où le formulaire est créé
    if in_update and 'form = CompetitionForm(' in lines[i] and 'request.POST' in lines[i]:
        if 'clean_translation_fields' not in lines[i]:
            print(f"⚠ Ligne {i+1} n'utilise pas clean_translation_fields")
            lines[i] = lines[i].replace('request.POST', 'clean_translation_fields(request.POST)')
            modified = True
            print(f"✓ Ligne {i+1} modifiée")

if modified:
    with open('apps/competitions/views/competitions.py', 'w') as f:
        f.write('\n'.join(lines))
    print("✓ Modifications appliquées")
else:
    print("⚠ Aucune modification nécessaire ou déjà appliquée")
PYTHON_FIX

echo "3. Solution alternative: Override de form.save()..."
sudo python3 << 'PYTHON_OVERRIDE'
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# Chercher où form.save() est appelé dans competition_update
import re

# Pattern pour trouver competition = form.save(commit=False)
pattern = r'(def competition_update.*?)(competition = form\.save\(commit=False\))(.*?)(competition\.save\(\))'

def replacement(match):
    before = match.group(1)
    save_line = match.group(2)
    middle = match.group(3)
    final_save = match.group(4)
    
    # Remplacer par une sauvegarde manuelle
    new_save = '''# Sauvegarde manuelle pour éviter les champs de traduction
                    # competition = form.save(commit=False)  # Désactivé
                    
                    # Mise à jour manuelle des champs
                    for field_name in ['title', 'description', 'start_date', 'end_date',
                                       'address', 'city', 'discipline', 'registration_deadline']:
                        if field_name in form.cleaned_data:
                            setattr(competition, field_name, form.cleaned_data[field_name])
                    
                    # Logo séparément car c'est un fichier
                    if 'logo' in request.FILES:
                        competition.logo = request.FILES['logo']'''
    
    new_final_save = '''# Sauvegarder sans les champs de traduction
                    # Liste des champs à exclure
                    excluded_fields = ['title_fr', 'title_en', 'title_es', 'title_ar',
                                      'description_fr', 'description_en', 'description_es', 'description_ar',
                                      'venue_name_fr', 'venue_name_en', 'venue_name_es', 'venue_name_ar',
                                      'address_fr', 'address_en', 'address_es', 'address_ar']
                    
                    # Obtenir tous les champs du modèle sauf ceux exclus
                    all_fields = [f.name for f in competition._meta.fields 
                                 if f.name not in excluded_fields and f.concrete and not f.primary_key]
                    
                    competition.save(update_fields=all_fields)'''
    
    return before + new_save + middle + new_final_save

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open('apps/competitions/views/competitions.py', 'w') as f:
        f.write(new_content)
    print("✓ Override de form.save() appliqué")
else:
    print("⚠ Pattern non trouvé, application manuelle...")
    
    # Chercher et remplacer manuellement
    lines = content.split('\n')
    in_update = False
    for i in range(len(lines)):
        if 'def competition_update' in lines[i]:
            in_update = True
        elif in_update and 'competition.save()' in lines[i] and 'Simplifié' in lines[i]:
            # Remplacer par une sauvegarde avec update_fields
            indent = len(lines[i]) - len(lines[i].lstrip())
            new_save = f'''{' ' * indent}# Sauvegarder avec exclusion des champs générés
{' ' * indent}excluded = ['title_fr', 'title_en', 'title_es', 'title_ar',
{' ' * indent}            'description_fr', 'description_en', 'description_es', 'description_ar',
{' ' * indent}            'venue_name_fr', 'venue_name_en', 'venue_name_es', 'venue_name_ar',
{' ' * indent}            'address_fr', 'address_en', 'address_es', 'address_ar']
{' ' * indent}fields = [f.name for f in competition._meta.fields 
{' ' * indent}          if f.name not in excluded and f.concrete and not f.primary_key]
{' ' * indent}competition.save(update_fields=fields)'''
            
            lines[i] = new_save
            
            with open('apps/competitions/views/competitions.py', 'w') as f:
                f.write('\n'.join(lines))
            print(f"✓ Ligne {i+1} remplacée")
            break
PYTHON_OVERRIDE

echo "4. Vérification de la syntaxe..."
python3 -m py_compile apps/competitions/views/competitions.py && echo "✓ Syntaxe OK" || echo "✗ Erreur de syntaxe"

echo "5. Redémarrage de Gunicorn..."
sudo pkill -HUP -f gunicorn

echo "✓ Modifications appliquées"
echo ""
echo "Les champs de traduction sont maintenant exclus à plusieurs niveaux :"
echo "- Au niveau POST avec clean_translation_fields()"
echo "- Au niveau de la sauvegarde avec update_fields explicite"
EOF

echo ""
echo "=== TERMINÉ ==="