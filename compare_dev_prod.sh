#!/bin/bash
# Script pour comparer les bases de données développement et production

echo "📊 COMPARAISON DÉVELOPPEMENT vs PRODUCTION"
echo "=========================================="

# Fonction pour compter les tables
count_tables() {
    local env=$1
    local count
    
    if [ "$env" = "dev" ]; then
        echo "🔧 DÉVELOPPEMENT (Local):"
        cd /mnt/c/martial_hub_django/martialcomp
        count=$(python manage.py dbshell << EOF 2>/dev/null | grep -c "competitions_"
.tables
EOF
)
    else
        echo "🌐 PRODUCTION:"
        count="À exécuter sur le serveur"
    fi
    
    echo "   Nombre de tables 'competitions_': $count"
}

# Créer un script pour la production
cat > compare_production.py << 'EOF'
#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

print("\n📊 ANALYSE DE LA BASE DE DONNÉES PRODUCTION")
print("=" * 50)

with connection.cursor() as cursor:
    # Compter toutes les tables
    if connection.vendor == 'postgresql':
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    elif connection.vendor == 'mysql':
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
    else:
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    
    total_tables = cursor.fetchone()[0]
    print(f"Nombre total de tables: {total_tables}")
    
    # Tables competitions
    if connection.vendor == 'postgresql':
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'competitions_%'")
    elif connection.vendor == 'mysql':
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'competitions_%'")
    else:
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'competitions_%'")
    
    comp_tables = cursor.fetchone()[0]
    print(f"Tables 'competitions_': {comp_tables}")
    
    # Vérifier les tables ManyToMany critiques
    critical_m2m = [
        'competitions_practitioner_disciplines',
        'competitions_practitioner_secondary_disciplines',
        'competitions_practitioner_primary_discipline'
    ]
    
    print("\nTables ManyToMany critiques:")
    for table in critical_m2m:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} relations")
        except:
            print(f"❌ {table}: MANQUANTE!")
EOF

echo -e "\n📝 INSTRUCTIONS:"
echo "1. Sur le DÉVELOPPEMENT, exécuter:"
echo "   cd /mnt/c/martial_hub_django/martialcomp"
echo "   python check_migrations_alignment.py > dev_analysis.txt"
echo ""
echo "2. Sur la PRODUCTION, exécuter:"
echo "   cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "   python check_migrations_alignment.py > prod_analysis.txt"
echo "   python compare_production.py"
echo ""
echo "3. Comparer les résultats pour identifier les différences"

# Vérifier les migrations localement
echo -e "\n🔍 ÉTAT DES MIGRATIONS (Développement):"
cd /mnt/c/martial_hub_django/martialcomp
python manage.py showmigrations competitions | tail -20