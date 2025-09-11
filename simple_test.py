#!/usr/bin/env python
"""
Test simple pour vérifier task_management sans problèmes de logging
"""
import os
import sys
import django
from pathlib import Path

# Configuration du projet Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

print("🧪 Test Simple Task Management")
print("=" * 40)

try:
    django.setup()
    print("✅ Django initialisé avec succès")
except Exception as e:
    print(f"❌ Erreur Django : {e}")
    sys.exit(1)

# Test 1: Import des modèles
try:
    from apps.task_management.models import Board, Task, Column
    print("✅ Import des modèles : OK")
except ImportError as e:
    print(f"❌ Import des modèles : {e}")

# Test 2: Vérifier INSTALLED_APPS
try:
    from django.conf import settings
    if 'apps.task_management' in settings.INSTALLED_APPS:
        print("✅ INSTALLED_APPS : OK")
    else:
        print("❌ INSTALLED_APPS : task_management manquant")
except Exception as e:
    print(f"❌ INSTALLED_APPS : {e}")

# Test 3: Test URL
try:
    from django.urls import reverse
    url = reverse('task_management:board_list')
    print(f"✅ URL task_management : {url}")
except Exception as e:
    print(f"❌ URL task_management : {e}")

# Test 4: Test base de données
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'task_management_%' LIMIT 1")
        result = cursor.fetchone()
    if result:
        print("✅ Tables task_management : créées")
    else:
        print("❌ Tables task_management : manquantes")
except Exception as e:
    print(f"⚠️ Test DB : {e}")

# Test 5: Dashboard utils
try:
    from apps.task_management.dashboard_utils import get_dashboard_task_data
    print("✅ Dashboard utils : importés")
except Exception as e:
    print(f"❌ Dashboard utils : {e}")

print("\n🎯 Test terminé !")
print("💡 Si tous les tests passent, lancez : python manage.py runserver")