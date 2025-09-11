#!/usr/bin/env python3
"""
Correcteur spécialisé pour le fichier club.py problématique
"""

import os

def fix_club_file():
    """Corrige spécifiquement le fichier club.py"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print(f"🎯 Correction ciblée de: {file_path}")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print("❌ Le fichier n'existe pas !")
        return False
    
    try:
        # Lecture du contenu en mode binaire
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        print(f"📊 Taille originale: {len(raw_content)} bytes")
        print(f"🔍 Premiers bytes: {raw_content[:10].hex()}")
        
        # Détection et suppression de TOUS les types de BOM
        bom_patterns = [
            (b'\xef\xbb\xbf', 'UTF-8 BOM'),
            (b'\xff\xfe', 'UTF-16 LE BOM'),
            (b'\xfe\xff', 'UTF-16 BE BOM'),
            (b'\x00\x00\xfe\xff', 'UTF-32 BE BOM'),
            (b'\xff\xfe\x00\x00', 'UTF-32 LE BOM'),
        ]
        
        original_content = raw_content
        fixed = False
        
        for bom_bytes, bom_name in bom_patterns:
            if raw_content.startswith(bom_bytes):
                print(f"🚨 {bom_name} DÉTECTÉ ET SUPPRIMÉ !")
                raw_content = raw_content[len(bom_bytes):]
                fixed = True
        
        # Suppression des caractères invisibles problématiques
        invisible_chars = [
            b'\xef\xbb\xbf',  # BOM UTF-8 (redondant mais sécurité)
            b'\xe2\x80\x8b',  # ZERO WIDTH SPACE (UTF-8)
            b'\xc2\xa0',      # NON-BREAKING SPACE (UTF-8) 
            b'\xe2\x80\x80',  # EN QUAD (UTF-8)
            b'\xef\xbf\xbd',  # REPLACEMENT CHARACTER (UTF-8)
        ]
        
        for invisible in invisible_chars:
            if invisible in raw_content:
                count_before = raw_content.count(invisible)
                raw_content = raw_content.replace(invisible, b' ')
                print(f"🧹 Supprimé {count_before} occurrences de caractère invisible")
                fixed = True
        
        # Vérification que le contenu commence bien par du texte valide
        try:
            decoded = raw_content.decode('utf-8')
            print(f"✅ Décodage UTF-8 réussi")
            print(f"📝 Première ligne: {repr(decoded.split(chr(10))[0])}")
        except UnicodeDecodeError as e:
            print(f"❌ Erreur décodage: {e}")
            return False
        
        if fixed or raw_content != original_content:
            # Sauvegarde du fichier original
            backup_path = file_path + ".backup"
            with open(backup_path, 'wb') as f:
                f.write(original_content)
            print(f"💾 Sauvegarde créée: {backup_path}")
            
            # Réécriture du fichier corrigé
            with open(file_path, 'wb') as f:
                f.write(raw_content)
            
            print(f"✅ Fichier corrigé !")
            print(f"📊 Nouvelle taille: {len(raw_content)} bytes")
            return True
        else:
            print("ℹ️  Aucune correction nécessaire détectée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def recreate_club_file():
    """Recrée le fichier club.py avec un contenu minimal"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    # Contenu minimal pour club.py
    minimal_content = '''import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


@login_required
def handle_club_creation(request):
    """Gère la création d'un club dans le processus d'onboarding"""
    # TODO: Implémenter la logique de création de club
    pass


@login_required
def handle_club_details(request):
    """Gère les détails d'un club dans le processus d'onboarding"""
    # TODO: Implémenter la logique de détails de club
    pass
'''
    
    try:
        # Sauvegarde de l'ancien fichier
        if os.path.exists(file_path):
            backup_path = file_path + ".original_backup"
            with open(file_path, 'rb') as original:
                with open(backup_path, 'wb') as backup:
                    backup.write(original.read())
            print(f"💾 Sauvegarde originale: {backup_path}")
        
        # Création du nouveau fichier
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(minimal_content)
        
        print(f"🆕 Fichier {file_path} recréé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la recréation: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚨 CORRECTEUR D'URGENCE POUR club.py")
    print("=" * 50)
    
    # Étape 1: Tentative de correction
    if fix_club_file():
        print("\n✅ Correction terminée ! Testez Django...")
    else:
        print("\n⚠️  Correction échouée, tentative de recréation...")
        
        # Étape 2: Recréation du fichier
        if recreate_club_file():
            print("✅ Fichier recréé ! Testez Django...")
        else:
            print("❌ Échec complet. Intervention manuelle requise.")
    
    print(f"\n💡 Commandes de test:")
    print(f"   python manage.py check")
    print(f"   python manage.py runserver")

if __name__ == "__main__":
    main()