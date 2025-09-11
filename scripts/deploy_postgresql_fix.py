#!/usr/bin/env python3
"""
SOLUTION DIRECTE POUR PRODUCTION POSTGRESQL
Script autonome pour corriger tous les problèmes de colonnes manquantes
"""

import subprocess
import sys
import os

def run_command(cmd, description=""):
    """Execute a command and return success status"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - ERROR: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def main():
    print("🚀 CORRECTION POSTGRESQL PRODUCTION")
    print("=" * 50)
    
    # Copy files to production server
    production_commands = [
        # Copy SQL fix file
        "scp fix_postgresql_production.sql root@martialcomp.com:/tmp/",
        
        # Execute the fix on production
        """ssh root@martialcomp.com '
            cd /var/www/vhosts/martialcomp.com/httpdocs
            source venv/bin/activate
            
            echo "📋 Applying PostgreSQL fixes..."
            
            # Apply the SQL fixes directly
            python3 manage.py dbshell < /tmp/fix_postgresql_production.sql
            
            echo "🧪 Testing critical tables..."
            python3 manage.py shell -c "
from django.db import connection
cursor = connection.cursor()

# Test all the previously problematic columns
test_queries = [
    ('TechnicalScoreResult.comments', 'SELECT comments FROM competitions_technicalscoreresult LIMIT 1'),
    ('TechnicalScoreResult.is_training_score', 'SELECT is_training_score FROM competitions_technicalscoreresult LIMIT 1'),
    ('JudgeSubmissionStatusResult.is_submitted', 'SELECT is_submitted FROM competitions_judgesubmissionstatusresult LIMIT 1'),
    ('EventFeedback.overall_satisfaction', 'SELECT overall_satisfaction FROM competitions_eventfeedback LIMIT 1'),
    ('PollQuestionResponse.response_number', 'SELECT response_number FROM competitions_pollquestionresponse LIMIT 1'),
]

all_ok = True
for test_name, query in test_queries:
    try:
        cursor.execute(query)
        print(f'✅ {test_name}: OK')
    except Exception as e:
        print(f'❌ {test_name}: {str(e)[:50]}...')
        all_ok = False

if all_ok:
    print('\\n🎉 TOUTES LES COLONNES PROBLÉMATIQUES SONT MAINTENANT CORRECTES')
else:
    print('\\n⚠️ Certaines colonnes ont encore des problèmes')
"
            
            echo "🔄 Restarting Django..."
            pkill -f "python.*manage.py" || true
            sleep 3
            nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_fix.log 2>&1 &
            sleep 5
            
            echo "🧪 Testing admin interface..."
            status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/admin/auth/user/" 2>/dev/null)
            if [[ "$status" =~ ^(200|302)$ ]]; then
                echo "✅ Admin interface working (status: $status)"
            else
                echo "⚠️ Admin interface status: $status"
                tail -10 /tmp/django_fix.log
            fi
        '"""
    ]
    
    success_count = 0
    for i, cmd in enumerate(production_commands, 1):
        if run_command(cmd, f"Step {i}/{len(production_commands)}"):
            success_count += 1
    
    print(f"\n🎯 RESULTS: {success_count}/{len(production_commands)} steps successful")
    
    if success_count == len(production_commands):
        print("🎉 POSTGRESQL PRODUCTION FIX COMPLETED SUCCESSFULLY!")
        print("🔗 Test: https://martialcomp.com/fr/admin/auth/user/")
    else:
        print("⚠️ Some steps failed. Check the output above.")

if __name__ == "__main__":
    main()