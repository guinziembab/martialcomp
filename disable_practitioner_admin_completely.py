#!/usr/bin/env python3
"""
Script pour désactiver complètement l'admin Practitioner
"""
import os
import sys

# Trouver le bon Python
python_paths = [
    '/var/www/vhosts/martialcomp.com/venv/bin/python3',
    '/usr/bin/python3',
    'python3'
]

for python_path in python_paths:
    if os.path.exists(python_path):
        print(f"Utilisation de Python: {python_path}")
        os.execv(python_path, [python_path] + sys.argv)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.contrib import admin
from apps.competitions.models import Practitioner

print("🚨 DÉSACTIVATION COMPLÈTE DE L'ADMIN PRACTITIONER")
print("=" * 60)

# 1. Désenregistrer Practitioner
try:
    admin.site.unregister(Practitioner)
    print("✅ Practitioner désenregistré avec succès")
except admin.sites.NotRegistered:
    print("⚠️  Practitioner n'était pas enregistré")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 2. Vérifier
if Practitioner not in admin.site._registry:
    print("✅ CONFIRMÉ: Practitioner n'est plus dans l'admin")
else:
    print("❌ ATTENTION: Practitioner est toujours dans l'admin!")

print("\n📝 L'admin Practitioner est maintenant désactivé.")
print("   Vous pouvez accéder aux autres sections de l'admin sans erreur.")