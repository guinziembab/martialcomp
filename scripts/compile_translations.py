#!/usr/bin/env python3
"""
Script de compilation manuelle des traductions
"""
import os
import subprocess
import polib

def compile_po_file(po_path):
    """Compile un fichier PO en MO"""
    try:
        po = polib.pofile(po_path)
        mo_path = po_path.replace('.po', '.mo')
        po.save_as_mofile(mo_path)
        return True
    except Exception as e:
        print(f"Erreur compilation {po_path}: {e}")
        return False

def main():
    """Compile tous les fichiers PO"""
    print("🔨 COMPILATION DES TRADUCTIONS")
    print("=" * 40)
    
    compiled_count = 0
    error_count = 0
    
    # Parcourir tous les fichiers PO
    for root, dirs, files in os.walk('locale'):
        for file in files:
            if file.endswith('.po'):
                po_path = os.path.join(root, file)
                print(f"Compilation: {po_path}")
                
                if compile_po_file(po_path):
                    compiled_count += 1
                    print(f"  ✅ Succès")
                else:
                    error_count += 1
                    print(f"  ❌ Erreur")
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"  ✅ Compilés: {compiled_count}")
    print(f"  ❌ Erreurs: {error_count}")

if __name__ == '__main__':
    main()