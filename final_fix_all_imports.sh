#!/bin/bash

echo "=== CORRECTION FINALE DE TOUS LES IMPORTS ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Trouver TOUS les fichiers avec des imports incorrects
echo "1. Recherche exhaustive des imports incorrects..."
echo "Fichiers à corriger :"
grep -r "from competitions\." apps/ --include="*.py" | grep -v "apps.competitions" | cut -d: -f1 | sort -u

# 2. Corriger tous les imports dans utils/decorators.py
echo ""
echo "2. Correction spécifique de decorators.py..."
if [ -f "apps/competitions/utils/decorators.py" ]; then
    cp apps/competitions/utils/decorators.py apps/competitions/utils/decorators.py.backup_$(date +%Y%m%d_%H%M%S)
    sed -i 's/from competitions\./from apps.competitions./g' apps/competitions/utils/decorators.py
    echo "✓ decorators.py corrigé"
fi

# 3. Corriger TOUS les fichiers Python dans apps/
echo ""
echo "3. Correction globale de tous les imports..."
find apps/ -name "*.py" -type f -exec grep -l "from competitions\." {} \; | while read file; do
    if ! grep -q "apps.competitions" "$file"; then
        echo "Correction de : $file"
        sed -i 's/from competitions\./from apps.competitions./g' "$file"
        sed -i 's/import competitions\./import apps.competitions./g' "$file"
    fi
done

# 4. Cas spéciaux : imports relatifs mal formés
echo ""
echo "4. Correction des imports relatifs..."
# Dans apps/competitions, les imports relatifs doivent être corrects
find apps/competitions -name "*.py" -exec sed -i 's/from competitions import/from apps.competitions import/g' {} \;

# 5. Vérifier qu'il n'y a plus d'imports problématiques
echo ""
echo "5. Vérification finale..."
REMAINING=$(grep -r "from competitions\." apps/ --include="*.py" | grep -v "apps.competitions" | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo "✓ Tous les imports ont été corrigés!"
else
    echo "⚠️  Il reste $REMAINING imports à corriger"
    grep -r "from competitions\." apps/ --include="*.py" | grep -v "apps.competitions" | head -5
fi

# 6. Test complet de l'application
echo ""
echo "6. Test complet de l'application..."
/var/www/vhosts/martialcomp.com/venv/bin/python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    import django
    django.setup()
    print('✓ Django chargé avec succès')
    
    # Test des migrations
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    call_command('showmigrations', '--plan', stdout=out)
    migrations_output = out.getvalue()
    if migrations_output:
        print('✓ Migrations accessibles')
    
    # Test WSGI
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print('✓ Application WSGI créée')
    
    # Test d'une vraie requête
    from django.test import Client
    client = Client(SERVER_NAME='martialcomp.com')
    response = client.get('/')
    print(f'✓ Test GET / : status={response.status_code}')
    
    if response.status_code in [200, 301, 302]:
        print('✅ L\\'application fonctionne correctement!')
    else:
        print(f'⚠️  Status inattendu : {response.status_code}')
    
except Exception as e:
    print(f'✗ Erreur : {e}')
    import traceback
    traceback.print_exc()
"

# 7. Appliquer les migrations
echo ""
echo "7. Application des migrations..."
/var/www/vhosts/martialcomp.com/venv/bin/python manage.py migrate --settings=config.settings.production --no-input || echo "Certaines migrations ont échoué"

# 8. Créer un superutilisateur par défaut si aucun n'existe
echo ""
echo "8. Vérification du superutilisateur..."
/var/www/vhosts/martialcomp.com/venv/bin/python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('⚠️  Aucun superutilisateur trouvé')
    print('Pour créer un superutilisateur :')
    print('python manage.py createsuperuser --settings=config.settings.production')
else:
    print('✓ Au moins un superutilisateur existe')
"

# 9. Redémarrer Apache une dernière fois
echo ""
echo "9. Redémarrage final d'Apache..."
systemctl restart apache2

echo ""
echo "=== TOUTES LES CORRECTIONS APPLIQUÉES ==="
echo ""
echo "Le site devrait maintenant fonctionner!"
echo ""
echo "Test : curl -I https://martialcomp.com"
echo ""
echo "Si vous voyez HTTP/2 200 ou 301, le site fonctionne!"
echo "Si vous voyez encore 500, vérifiez :"
echo "1. Les logs Passenger dans /var/log/apache2/error.log"
echo "2. Les logs Django dans logs/django.log"