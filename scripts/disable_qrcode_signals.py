#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour désactiver temporairement les signaux qui créent automatiquement les QR codes
pour éviter les conflits lors de l'ajout de pratiquants
"""

import os
import sys
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models.signals import post_save
from competitions.models import Practitioner
from competitions.signals import create_practitioner_qr_code

def disable_qrcode_signals():
    """
    Désactive le signal qui crée automatiquement un QR code pour chaque nouveau pratiquant
    """
    try:
        # Désactiver le signal
        post_save.disconnect(create_practitioner_qr_code, sender=Practitioner)
        print("Signal de création automatique de QR code désactivé avec succès.")
        print("Les nouveaux pratiquants peuvent maintenant être ajoutés sans création automatique de QR code.")
        
        # Créer un fichier indicateur pour montrer que le signal est désactivé
        with open('qrcode_signal_disabled.txt', 'w') as f:
            f.write("QR code signal disabled on " + django.utils.timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        print("\nNote importante : Pour réactiver le signal plus tard, exécutez le script 'enable_qrcode_signals.py'")
        
    except Exception as e:
        print(f"Erreur lors de la désactivation du signal : {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        print("Désactivation du signal de création automatique de QR code...")
        success = disable_qrcode_signals()
        if success:
            print("\nDésactivation réussie! Les pratiquants peuvent maintenant être ajoutés sans erreur de clé dupliquée.")
            print("Redémarrez le serveur Django pour appliquer les changements.")
        else:
            print("\nLa désactivation a échoué. Veuillez vérifier les erreurs ci-dessus.")
    except Exception as e:
        print(f"Une erreur est survenue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)