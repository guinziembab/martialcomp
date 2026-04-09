#!/bin/bash
# Réécriture complète de la méthode save

echo "=== RÉÉCRITURE DE LA MÉTHODE SAVE ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Réécriture complète de la méthode save..."
sudo python3 << 'PYTHON_REWRITE'
import re

# Lire le fichier
with open('apps/competitions/models/competitions.py', 'r') as f:
    content = f.read()

# Trouver et remplacer toute la méthode save
# D'abord, trouver où elle commence
save_start = content.find('    def save(self')
if save_start == -1:
    print("✗ Méthode save non trouvée")
else:
    # Trouver où elle se termine (prochaine méthode ou fin de classe)
    # Chercher la prochaine méthode ou propriété au même niveau d'indentation
    next_method = content.find('\n    def ', save_start + 10)
    next_property = content.find('\n    class ', save_start + 10)
    next_class = content.find('\nclass ', save_start + 10)
    
    # Prendre le plus proche
    candidates = [x for x in [next_method, next_property, next_class] if x > 0]
    if candidates:
        save_end = min(candidates)
    else:
        save_end = len(content)
    
    # Nouvelle méthode save simple et correcte
    new_save_method = '''    def save(self, *args, **kwargs):
        """
        Override save to handle generated columns.
        Exclude translation fields from update_fields to avoid PostgreSQL errors.
        """
        if self.pk and 'update_fields' not in kwargs:
            # Si on met à jour un objet existant sans update_fields spécifique
            # On doit exclure les champs de traduction générés
            update_fields = []
            for field in self._meta.fields:
                field_name = field.name
                # Exclure les champs de traduction générés et autres champs spéciaux
                if not any([
                    field_name.endswith('_fr'),
                    field_name.endswith('_en'),
                    field_name.endswith('_es'),
                    field_name.endswith('_ar'),
                    field_name == 'id',
                    field.primary_key
                ]):
                    update_fields.append(field_name)
            
            kwargs['update_fields'] = update_fields
        
        return super().save(*args, **kwargs)
'''
    
    # Remplacer
    new_content = content[:save_start] + new_save_method + content[save_end:]
    
    # Écrire le fichier
    with open('apps/competitions/models/competitions.py', 'w') as f:
        f.write(new_content)
    
    print("✓ Méthode save réécrite correctement")
PYTHON_REWRITE

echo "2. Validation de la syntaxe..."
if python3 -m py_compile apps/competitions/models/competitions.py; then
    echo "✓ Syntaxe Python valide !"
else
    echo "✗ Erreur de syntaxe"
    python3 -c "import ast; ast.parse(open('apps/competitions/models/competitions.py').read())" 2>&1 | head -10
fi

echo "3. Redémarrage complet de Gunicorn..."
sudo pkill -9 -f gunicorn
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

echo "4. Vérification..."
sleep 4
if pgrep -f gunicorn > /dev/null; then
    echo "✓ Gunicorn fonctionne !"
    echo "✓ Processus Gunicorn:"
    ps aux | grep gunicorn | grep -v grep
    
    # Test final
    echo ""
    echo "5. Test du site..."
    curl -I http://127.0.0.1:8888/ 2>/dev/null | head -3
else
    echo "✗ Gunicorn n'a pas démarré"
    tail -5 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
fi

EOF

echo ""
echo "=== TERMINÉ ==="