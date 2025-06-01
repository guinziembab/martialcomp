#!/usr/bin/env python
"""Test simple sous Windows pour démarrer le serveur Django"""

import os
import sys
import subprocess
from pathlib import Path

print("=== Test Simple Django ===")

# S'assurer d'être dans le bon répertoire
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
print(f"Working directory: {os.getcwd()}")

# Vérifier la base de données
db_path = BASE_DIR / 'db.sqlite3'
if db_path.exists():
    size = db_path.stat().st_size
    print(f"✅ Database exists: {db_path} ({size} bytes)")
else:
    print(f"❌ Database missing: {db_path}")
    sys.exit(1)

# Test 1: Vérifier Django avec settings_minimal
print("\n=== Test 1: Django Setup ===")
try:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_minimal'
    
    # Test import Django
    import django
    print(f"✅ Django version: {django.get_version()}")
    
    # Setup Django
    django.setup()
    print("✅ Django setup successful")
    
    # Test database access
    from django.contrib.auth.models import User
    user_count = User.objects.count()
    print(f"✅ Database access: {user_count} users")
    
except Exception as e:
    print(f"❌ Django test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Démarrer le serveur de façon interactive
print("\n=== Test 2: Starting Server ===")
print("Starting Django server with settings_minimal...")
print("If successful, open http://127.0.0.1:8000/ in your browser")
print("Press Ctrl+C to stop the server")

try:
    # Utiliser subprocess pour démarrer le serveur
    cmd = [sys.executable, 'manage.py', 'runserver', '--settings=config.settings_minimal', '127.0.0.1:8000']
    
    # Afficher la commande
    print(f"Command: {' '.join(cmd)}")
    
    # Démarrer le serveur
    subprocess.run(cmd, cwd=BASE_DIR)
    
except KeyboardInterrupt:
    print("\n✅ Server stopped by user")
except Exception as e:
    print(f"❌ Server error: {e}")

print("=== Test Completed ===")