#!/usr/bin/env python
import os
import sys
import subprocess

print("=== REDÉMARRAGE COMPLET DE L'APPLICATION ===")

# Vider tous les caches Python
print("🧹 Nettoyage des caches Python...")
os.system("find . -name '*.pyc' -delete")
os.system("find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true")

# Collecter les fichiers statiques
print("📦 Collecte des fichiers statiques...")
os.system("python manage.py collectstatic --noinput --clear")

# Redémarrer les services
print("🔄 Redémarrage des services...")
os.system("systemctl restart martialcomp")
os.system("systemctl restart nginx")

# Attendre que les services démarrent
print("⏳ Attente du démarrage des services...")
import time
time.sleep(5)

# Vérifier l'état des services
print("📊 État des services:")
os.system("systemctl status martialcomp --no-pager")
os.system("systemctl status nginx --no-pager")

print("\n✅ Redémarrage terminé!")
print("🌐 Testez maintenant: https://martialcomp.com/fr/admin/") 