#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour réactiver les signaux qui créent automatiquement les QR codes
après avoir résolu les conflits
"""

import os
import sys
import django
import importlib

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models.signals import post_save
from competitions.models import Practitioner

def enable_qrcode_signals():
    """
    Réactive le signal qui crée automatiquement un QR code pour chaque nouveau pratiquant
    """
    try:
        # Recharger le module signals pour réactiver les signaux
        import competitions.signals
        importlib.reload(competitions.signals)
        
        print("Signal de création automatique de QR code réactivé avec succès.")
        
        # Supprimer le fichier indicateur
        if os.path.exists('qrcode_signal_disabled.txt'):
            os.remove('qrcode_signal_disabled.txt')
            print("Le fichier indicateur a été supprimé.")
        
    except Exception as e:
        print(f"Erreur lors de la réactivation du signal : {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        print("Réactivation du signal de création automatique de QR code...")
        success = enable_qrcode_signals()
        if success:
            print("\nRéactivation réussie! Les nouveaux pratiquants auront à nouveau des QR codes créés automatiquement.")
            print("Redémarrez le serveur Django pour appliquer les changements.")
        else:
            print("\nLa réactivation a échoué. Veuillez vérifier les erreurs ci-dessus.")
    except Exception as e:
        print(f"Une erreur est survenue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)