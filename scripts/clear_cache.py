#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour vider le cache Django (remplacement pour clear_cache management command)
"""
import os
import shutil

# Définir le répertoire des fichiers temporaires Django
cache_dir = os.path.join('temp', 'django_cache')
if os.path.exists(cache_dir):
    try:
        shutil.rmtree(cache_dir)
        print(f"✓ Cache supprimé: {cache_dir}")
    except Exception as e:
        print(f"Erreur lors de la suppression du cache: {e}")
else:
    print(f"Répertoire de cache introuvable: {cache_dir}")

# Supprimer les fichiers .pyc dans le dossier competitions
competitions_dir = 'competitions'
pyc_count = 0
if os.path.exists(competitions_dir):
    for root, dirs, files in os.walk(competitions_dir):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    pyc_count += 1
                except Exception as e:
                    print(f"Erreur lors de la suppression de {file}: {e}")
    
    print(f"✓ {pyc_count} fichiers .pyc supprimés")
else:
    print(f"Répertoire introuvable: {competitions_dir}")

print("Cache vidé avec succès. Veuillez redémarrer complètement votre serveur Django.")