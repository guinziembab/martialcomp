#!/bin/bash

################################################################################
# DIAGNOSTIC COMPLET - IDENTIFIER TOUS LES PROBLÈMES DE STRUCTURE DB
################################################################################

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

echo "🔍 DIAGNOSTIC COMPLET BASE DE DONNÉES"
echo "===================================="

# Vérifier les chemins
if [ ! -d "$PRODUCTION_PATH" ]; then
    error "Chemin production non trouvé: $PRODUCTION_PATH"
fi

cd "$PRODUCTION_PATH" || error "Impossible d'accéder à $PRODUCTION_PATH"

# Activer l'environnement virtuel
info "🔧 Activation de l'environnement virtuel..."
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    success "Environnement virtuel activé"
else
    error "Environnement virtuel non trouvé: $VENV_PATH"
fi

# Diagnostic ultra-poussé des modèles Django vs tables PostgreSQL
info "🔍 DIAGNOSTIC ULTRA-POUSSÉ - MODÈLES vs BASE DE DONNÉES"

python manage.py shell -c "
import os
import django
from django.db import connection
from django.apps import apps
from django.core.management.color import no_style

def analyze_model_vs_database():
    print('=' * 80)
    print('🔍 ANALYSE COMPLÈTE MODÈLES DJANGO vs POSTGRESQL')
    print('=' * 80)
    
    cursor = connection.cursor()
    
    # Obtenir toutes les tables PostgreSQL
    cursor.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'competitions_%'
        ORDER BY table_name
    \"\"\")
    
    postgres_tables = [row[0] for row in cursor.fetchall()]
    print(f'\\n📋 Tables PostgreSQL competitions ({len(postgres_tables)}):')
    for table in postgres_tables[:10]:
        print(f'  • {table}')
    if len(postgres_tables) > 10:
        print(f'  ... et {len(postgres_tables) - 10} autres')
    
    # Analyser chaque modèle Django
    competitions_app = apps.get_app_config('competitions')
    django_models = competitions_app.get_models()
    
    print(f'\\n📋 Modèles Django competitions ({len(django_models)}):')
    
    major_issues = []
    
    for model in django_models:
        model_name = model.__name__
        table_name = model._meta.db_table
        
        print(f'\\n🔍 Modèle: {model_name} → Table: {table_name}')
        
        # Vérifier si la table existe
        if table_name not in postgres_tables:
            print(f'  ❌ TABLE MANQUANTE: {table_name}')
            major_issues.append(f'TABLE_MISSING: {table_name}')
            continue
        
        # Obtenir les colonnes PostgreSQL pour cette table
        cursor.execute(\"\"\"
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        \"\"\", [table_name])
        
        postgres_columns = {row[0]: {'type': row[1], 'nullable': row[2], 'default': row[3]} 
                          for row in cursor.fetchall()}
        
        # Obtenir les champs Django pour ce modèle
        django_fields = {}
        for field in model._meta.get_fields():
            if hasattr(field, 'column'):
                django_fields[field.column] = {
                    'type': type(field).__name__,
                    'null': getattr(field, 'null', False),
                    'default': getattr(field, 'default', None)
                }
        
        # Comparer les colonnes
        missing_columns = []
        for django_col, django_info in django_fields.items():
            if django_col not in postgres_columns:
                missing_columns.append(django_col)
                print(f'  ❌ COLONNE MANQUANTE: {django_col} ({django_info[\"type\"]})')
        
        extra_columns = []
        for pg_col in postgres_columns:
            if pg_col not in django_fields and pg_col != 'id':
                extra_columns.append(pg_col)
                print(f'  ⚠️ COLONNE EXTRA: {pg_col}')
        
        if missing_columns:
            major_issues.append(f'MISSING_COLUMNS_{table_name}: {', '.join(missing_columns)}')
        
        if not missing_columns and not extra_columns:
            print(f'  ✅ Structure OK')
    
    print('\\n' + '=' * 80)
    print('🎯 RÉSUMÉ DES PROBLÈMES MAJEURS')
    print('=' * 80)
    
    if major_issues:
        for issue in major_issues:
            print(f'❌ {issue}')
    else:
        print('✅ Aucun problème majeur détecté')
    
    return major_issues

# Exécuter l'analyse
major_issues = analyze_model_vs_database()

# Focus spécial sur EventFeedback
print('\\n' + '=' * 80)
print('🔍 FOCUS SPÉCIAL: EventFeedback')
print('=' * 80)

try:
    from competitions.models.event import EventFeedback
    print('✅ Import EventFeedback: OK')
    
    # Analyser les champs
    print('\\n📋 Champs Django EventFeedback:')
    for field in EventFeedback._meta.get_fields():
        if hasattr(field, 'column'):
            print(f'  • {field.column} ({type(field).__name__})')
            
except Exception as e:
    print(f'❌ Erreur import EventFeedback: {e}')
    
    # Essayer de trouver EventFeedback ailleurs
    print('\\n🔍 Recherche EventFeedback dans tous les modèles...')
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            if 'EventFeedback' in str(model) or 'eventfeedback' in model._meta.db_table:
                print(f'  🎯 Trouvé: {model} → {model._meta.db_table}')

# Vérifier la table competitions_eventfeedback directement
cursor = connection.cursor()
print('\\n🔍 Structure PostgreSQL competitions_eventfeedback:')
try:
    cursor.execute(\"\"\"
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'competitions_eventfeedback' 
        ORDER BY ordinal_position
    \"\"\")
    
    columns = cursor.fetchall()
    if columns:
        for col_name, col_type, nullable in columns:
            print(f'  • {col_name} ({col_type}, nullable: {nullable})')
    else:
        print('  ❌ Table competitions_eventfeedback introuvable')
        
except Exception as e:
    print(f'  ❌ Erreur PostgreSQL: {e}')

print('\\n' + '=' * 80)
print('🎯 RECOMMANDATIONS')
print('=' * 80)

if len(major_issues) > 10:
    print('❌ PROBLÈME SYSTÉMIQUE: Plus de 10 problèmes détectés')
    print('💡 RECOMMANDATION: Réinitialisation complète des migrations')
elif major_issues:
    print('⚠️ PROBLÈMES LOCALISÉS: Corrections ciblées possibles')
    print('💡 RECOMMANDATION: Création manuelle des colonnes manquantes')
else:
    print('✅ STRUCTURE CORRECTE: Problème probablement dans les migrations')
    print('💡 RECOMMANDATION: Vérifier les fichiers de migration')
" > /tmp/diagnostic_complet.log 2>&1

cat /tmp/diagnostic_complet.log

# Créer un script de réparation basé sur le diagnostic
info "🔧 Génération automatique du script de réparation..."

# Extraire les problèmes du diagnostic et créer les commandes SQL
python manage.py shell -c "
import re

# Lire le diagnostic
try:
    with open('/tmp/diagnostic_complet.log', 'r') as f:
        diagnostic = f.read()
    
    # Extraire les colonnes manquantes
    missing_pattern = r'❌ COLONNE MANQUANTE: (\w+) \((\w+)\)'
    missing_columns = re.findall(missing_pattern, diagnostic)
    
    print('🔧 GÉNÉRATION SCRIPT DE RÉPARATION AUTOMATIQUE')
    print('=' * 50)
    
    if missing_columns:
        print('\\nCommandes SQL à exécuter:')
        
        # Générer les commandes SQL appropriées
        sql_commands = []
        
        for col_name, col_type in missing_columns:
            if 'eventfeedback' in diagnostic.lower():
                table = 'competitions_eventfeedback'
            elif 'technicalscoreresult' in diagnostic.lower():
                table = 'competitions_technicalscoreresult'
            else:
                table = 'competitions_unknown'
            
            # Mapper les types Django vers PostgreSQL
            if col_type in ['CharField', 'TextField']:
                pg_type = 'TEXT'
            elif col_type in ['DateTimeField']:
                pg_type = 'TIMESTAMP WITH TIME ZONE'
            elif col_type in ['BooleanField']:
                pg_type = 'BOOLEAN'
            elif col_type in ['IntegerField', 'PositiveIntegerField']:
                pg_type = 'INTEGER'
            elif col_type in ['DecimalField']:
                pg_type = 'DECIMAL'
            else:
                pg_type = 'TEXT'  # Par défaut
            
            sql_cmd = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {pg_type};'
            sql_commands.append(sql_cmd)
            print(f'  {sql_cmd}')
        
        print(f'\\n✅ {len(sql_commands)} commandes SQL générées')
    else:
        print('⚠️ Aucune colonne manquante détectée dans le diagnostic')
        
except Exception as e:
    print(f'❌ Erreur génération script: {e}')
" > /tmp/script_reparation_auto.log 2>&1

cat /tmp/script_reparation_auto.log

echo ""
success "🎯 DIAGNOSTIC COMPLET TERMINÉ"
info "============================"
info "📋 Fichiers générés:"
info "• Diagnostic complet: cat /tmp/diagnostic_complet.log"
info "• Script réparation: cat /tmp/script_reparation_auto.log"
info ""
warning "⚠️ Analysez les résultats pour comprendre l'étendue du problème"
info "Si plus de 10 problèmes → Réinitialisation migrations recommandée"
info "Si moins de 10 problèmes → Réparation ciblée possible"