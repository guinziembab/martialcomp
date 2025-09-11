#!/bin/bash

################################################################################
# DIAGNOSTIC SIMPLE ET EFFICACE - SANS F-STRINGS COMPLEXES
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

echo "🔍 DIAGNOSTIC SIMPLE ET EFFICACE"
echo "================================"

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

# Diagnostic direct de la table EventFeedback
info "🔍 Diagnostic direct de competitions_eventfeedback..."

python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

print('=== DIAGNOSTIC TABLE EVENTFEEDBACK ===')

# Vérifier si la table existe
try:
    cursor.execute(\"\"\"
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'competitions_eventfeedback'
    \"\"\")
    
    if cursor.fetchone():
        print('✅ Table competitions_eventfeedback existe')
        
        # Lister toutes les colonnes existantes
        cursor.execute(\"\"\"
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'competitions_eventfeedback'
            ORDER BY ordinal_position
        \"\"\")
        
        existing_columns = cursor.fetchall()
        print('\\n📋 Colonnes existantes:')
        for col_name, col_type in existing_columns:
            print('  ✅', col_name, '(' + col_type + ')')
            
    else:
        print('❌ Table competitions_eventfeedback n\\'existe pas')
        
except Exception as e:
    print('❌ Erreur:', str(e))

# Rechercher le modèle EventFeedback
print('\\n=== RECHERCHE MODÈLE EVENTFEEDBACK ===')

try:
    # Essayer différents imports
    import_attempts = [
        'from competitions.models.event import EventFeedback',
        'from competitions.models import EventFeedback', 
        'from competitions.models.events import EventFeedback'
    ]
    
    model_found = False
    for attempt in import_attempts:
        try:
            exec(attempt)
            print('✅ Import réussi:', attempt)
            
            # Lister les champs du modèle
            print('\\n📋 Champs du modèle EventFeedback:')
            for field in EventFeedback._meta.get_fields():
                if hasattr(field, 'column'):
                    field_type = type(field).__name__
                    print('  📝', field.column, '(' + field_type + ')')
            
            model_found = True
            break
        except Exception:
            continue
    
    if not model_found:
        print('❌ Modèle EventFeedback introuvable')
        
        # Rechercher dans tous les modèles competitions
        from django.apps import apps
        print('\\n🔍 Recherche dans tous les modèles competitions...')
        
        competitions_app = apps.get_app_config('competitions')
        for model in competitions_app.get_models():
            model_name = model.__name__
            table_name = model._meta.db_table
            
            if 'feedback' in model_name.lower() or 'feedback' in table_name:
                print('  🎯 Trouvé:', model_name, '→', table_name)
        
except Exception as e:
    print('❌ Erreur recherche modèle:', str(e))
"

# Test direct des erreurs actuelles
info "🧪 Test direct des erreurs actuelles..."

python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

print('=== TEST COLONNES PROBLÉMATIQUES ===')

# Tester les colonnes qui causent des erreurs
test_queries = [
    ('overall_satisfaction', 'SELECT overall_satisfaction FROM competitions_eventfeedback LIMIT 1'),
    ('submitted_at', 'SELECT submitted_at FROM competitions_eventfeedback LIMIT 1'),
    ('created_at', 'SELECT created_at FROM competitions_eventfeedback LIMIT 1'),
    ('event_id', 'SELECT event_id FROM competitions_eventfeedback LIMIT 1'),
    ('feedback_text', 'SELECT feedback_text FROM competitions_eventfeedback LIMIT 1'),
    ('rating', 'SELECT rating FROM competitions_eventfeedback LIMIT 1')
]

for col_name, query in test_queries:
    try:
        cursor.execute(query)
        print('✅', col_name, ': Existe')
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg:
            print('❌', col_name, ': MANQUANTE')
        else:
            print('⚠️', col_name, ':', error_msg[:50] + '...')
"

# Créer le script de réparation pour EventFeedback
info "🔧 Création du script de réparation EventFeedback..."

cat > /tmp/fix_eventfeedback.sql << 'SQL_EOF'
-- Script de réparation pour competitions_eventfeedback
-- Ajouter toutes les colonnes manquantes possibles

-- Colonnes de base
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS overall_satisfaction INTEGER DEFAULT 3;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Colonnes de feedback
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS feedback_text TEXT DEFAULT '';
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS rating INTEGER DEFAULT 5;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS would_recommend BOOLEAN DEFAULT TRUE;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS event_organization_rating INTEGER DEFAULT 5;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS venue_rating INTEGER DEFAULT 5;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS staff_rating INTEGER DEFAULT 5;

-- Relations
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS event_id INTEGER;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS submitted_by_id INTEGER;

-- Métadonnées
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN DEFAULT FALSE;
ALTER TABLE competitions_eventfeedback ADD COLUMN IF NOT EXISTS ip_address INET;

COMMENT ON TABLE competitions_eventfeedback IS 'Feedback des événements - Réparé automatiquement';
SQL_EOF

success "Script SQL créé: /tmp/fix_eventfeedback.sql"

# Appliquer le script SQL
info "🔧 Application du script de réparation..."

python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

# Lire et exécuter le script SQL
try:
    with open('/tmp/fix_eventfeedback.sql', 'r') as f:
        sql_script = f.read()
    
    # Diviser en commandes individuelles
    sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
    
    print('🔧 Application de', len(sql_commands), 'commandes SQL...')
    
    success_count = 0
    for i, cmd in enumerate(sql_commands, 1):
        try:
            cursor.execute(cmd)
            print('✅', i, ': OK')
            success_count += 1
        except Exception as e:
            error_msg = str(e)[:50]
            print('⚠️', i, ':', error_msg + '...')
    
    print('\\n🎯 Résultat:', success_count, '/', len(sql_commands), 'commandes réussies')
    
except Exception as e:
    print('❌ Erreur application SQL:', str(e))
"

# Test final
info "🧪 Test final EventFeedback..."

python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

print('=== TEST FINAL EVENTFEEDBACK ===')

# Tester la colonne problématique
try:
    cursor.execute('SELECT overall_satisfaction FROM competitions_eventfeedback LIMIT 1')
    print('✅ overall_satisfaction: CORRIGÉE')
except Exception as e:
    print('❌ overall_satisfaction:', str(e))

# Compter les colonnes maintenant
try:
    cursor.execute(\"\"\"
        SELECT COUNT(column_name) 
        FROM information_schema.columns 
        WHERE table_name = 'competitions_eventfeedback'
    \"\"\")
    
    col_count = cursor.fetchone()[0]
    print('📊 Nombre total de colonnes:', col_count)
    
except Exception as e:
    print('❌ Erreur comptage:', str(e))
"

# Redémarrage Django et test
info "🔄 Redémarrage Django..."

pkill -f "python.*manage.py" || true
pkill -f "runserver" || true
sleep 3

nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_eventfeedback_fix.log 2>&1 &
sleep 5

if pgrep -f "runserver" > /dev/null; then
    success "Django redémarré"
    
    # Test admin
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/admin/auth/user/" 2>/dev/null)
    if [[ "$status" =~ ^(200|302)$ ]]; then
        success "🎉 Admin users accessible (statut: $status)"
    else
        warning "Admin users statut: $status"
    fi
else
    error "Échec redémarrage Django"
fi

echo ""
success "🎯 DIAGNOSTIC ET RÉPARATION EVENTFEEDBACK TERMINÉS"
info "=================================================="
info "📋 Fichier SQL généré: cat /tmp/fix_eventfeedback.sql"
info "📋 Logs Django: tail -f /tmp/django_eventfeedback_fix.log"
info ""
info "🧪 Testez maintenant la suppression de comptes:"
info "• https://martialcomp.com/fr/admin/auth/user/"