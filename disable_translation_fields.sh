#!/bin/bash
# Solution ultime : désactiver les champs de traduction dans le formulaire

echo "=== DÉSACTIVATION DES CHAMPS DE TRADUCTION ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Inspection du problème..."
# Vérifier quels champs sont dans le formulaire
python3 << 'INSPECT'
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

try:
    django.setup()
    from apps.competitions.forms import CompetitionForm
    from apps.competitions.models import Competition
    
    # Lister tous les champs du modèle
    print("Champs du modèle Competition:")
    for field in Competition._meta.get_fields():
        if hasattr(field, 'name'):
            print(f"  - {field.name} (concrete: {getattr(field, 'concrete', 'N/A')})")
    
    # Lister les champs du formulaire
    form = CompetitionForm()
    print("\nChamps du formulaire CompetitionForm:")
    for name, field in form.fields.items():
        print(f"  - {name}")
        
except Exception as e:
    print(f"Erreur: {e}")
INSPECT

echo "2. Modification du formulaire pour exclure TOUS les champs traduits..."
sudo python3 << 'PYTHON_FORM'
with open('apps/competitions/forms/competitions.py', 'r') as f:
    content = f.read()

# Ajouter l'exclusion des champs traduits dans Meta
import re

# Chercher la classe Meta dans CompetitionForm
meta_pattern = r'(class Meta:.*?model = Competition.*?)(fields = \[.*?\])'

def replace_meta(match):
    before = match.group(1)
    fields = match.group(2)
    
    # Ajouter exclude après fields
    exclude_fields = '''fields = [
            'title', 'description', 'start_date', 'end_date', 
            'address', 'city', 'discipline', 'registration_deadline',
            'logo'
        ]
        # Exclure TOUS les champs de traduction générés
        exclude = ['title_fr', 'title_en', 'title_es', 'title_ar',
                   'description_fr', 'description_en', 'description_es', 'description_ar',
                   'venue_name_fr', 'venue_name_en', 'venue_name_es', 'venue_name_ar',
                   'address_fr', 'address_en', 'address_es', 'address_ar']'''
    
    return before + exclude_fields

new_content = re.sub(meta_pattern, replace_meta, content, flags=re.DOTALL)

# Si pas trouvé, chercher différemment
if new_content == content:
    lines = content.split('\n')
    for i in range(len(lines)):
        if 'class Meta:' in lines[i] and i < len(lines) - 5:
            # Chercher model = Competition
            for j in range(i, min(i + 10, len(lines))):
                if 'model = Competition' in lines[j]:
                    # Insérer exclude après fields
                    for k in range(j, min(j + 20, len(lines))):
                        if ']' in lines[k] and 'fields' in lines[k-1]:
                            # Insérer exclude après
                            indent = ' ' * 8
                            lines.insert(k + 1, indent + '# Exclure TOUS les champs de traduction')
                            lines.insert(k + 2, indent + 'exclude = ["title_fr", "title_en", "title_es", "title_ar",')
                            lines.insert(k + 3, indent + '           "description_fr", "description_en", "description_es", "description_ar",')
                            lines.insert(k + 4, indent + '           "venue_name_fr", "venue_name_en", "venue_name_es", "venue_name_ar",')
                            lines.insert(k + 5, indent + '           "address_fr", "address_en", "address_es", "address_ar"]')
                            new_content = '\n'.join(lines)
                            break
                    break
            break

if new_content != content:
    with open('apps/competitions/forms/competitions.py', 'w') as f:
        f.write(new_content)
    print("✓ Champs de traduction exclus du formulaire")
else:
    print("⚠ Pas de modification nécessaire")
PYTHON_FORM

echo "3. Solution alternative: Utilisation de la sauvegarde directe..."
sudo python3 << 'PYTHON_DIRECT'
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# Dans competition_update, remplacer form.save() par une sauvegarde manuelle
lines = content.split('\n')
in_update = False
for i in range(len(lines)):
    if 'def competition_update' in lines[i]:
        in_update = True
    elif in_update and lines[i].strip() and not lines[i].startswith(' '):
        in_update = False
    
    # Remplacer competition = form.save(commit=False)
    if in_update and 'competition = form.save(commit=False)' in lines[i]:
        indent = len(lines[i]) - len(lines[i].lstrip())
        new_code = f'''{' ' * indent}# Sauvegarde manuelle pour éviter les champs de traduction
{' ' * indent}# competition = form.save(commit=False)  # Désactivé
{' ' * indent}
{' ' * indent}# Mise à jour manuelle des champs
{' ' * indent}for field_name in ['title', 'description', 'start_date', 'end_date',
{' ' * indent}                   'address', 'city', 'discipline', 'registration_deadline']:
{' ' * indent}    if field_name in form.cleaned_data:
{' ' * indent}        setattr(competition, field_name, form.cleaned_data[field_name])
{' ' * indent}
{' ' * indent}# Logo séparément car c'est un fichier
{' ' * indent}if 'logo' in request.FILES:
{' ' * indent}    competition.logo = request.FILES['logo']'''
        
        lines[i] = new_code

# Sauvegarder
with open('apps/competitions/views/competitions.py', 'w') as f:
    f.write('\n'.join(lines))

print("✓ Sauvegarde manuelle implémentée")
PYTHON_DIRECT

echo "4. Création d'un signal pour nettoyer pre_save..."
cat > apps/competitions/signals_fix.py << 'SIGNALS'
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Competition

@receiver(pre_save, sender=Competition)
def clean_generated_fields(sender, instance, **kwargs):
    """
    Nettoie les champs générés avant la sauvegarde
    """
    if kwargs.get('update_fields'):
        # Liste des champs à exclure
        generated_fields = {'title_fr', 'title_en', 'title_es', 'title_ar',
                           'description_fr', 'description_en', 'description_es', 'description_ar',
                           'venue_name_fr', 'venue_name_en', 'venue_name_es', 'venue_name_ar',
                           'address_fr', 'address_en', 'address_es', 'address_ar'}
        
        # Filtrer update_fields
        kwargs['update_fields'] = [f for f in kwargs['update_fields'] 
                                  if f not in generated_fields]
SIGNALS

# Importer dans __init__.py
if ! grep -q "signals_fix" apps/competitions/__init__.py; then
    echo "from . import signals_fix" >> apps/competitions/__init__.py
fi

echo "5. Redémarrage..."
sudo pkill -f gunicorn
sleep 2

cd /var/www/vhosts/martialcomp.com
sudo -u www-data /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --log-level info \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --daemon \
    config.wsgi:application

echo "✓ Solutions multiples appliquées :"
echo "  1. Exclusion des champs dans le formulaire"
echo "  2. Sauvegarde manuelle des champs"
echo "  3. Signal pre_save pour nettoyer"
echo "  4. Triple protection contre les champs générés"
EOF

echo ""
echo "=== TERMINÉ ==="