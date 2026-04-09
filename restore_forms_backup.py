#!/usr/bin/env python
"""Restaurer la version de sauvegarde de forms.py"""

import shutil

print("=== RESTAURATION D'URGENCE ===")

# Restaurer depuis le backup avant mes modifications
forms_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/grades/forms.py'
backup_file = forms_file + '.backup_discipline'

try:
    shutil.copy2(backup_file, forms_file)
    print(f"✓ Fichier restauré depuis: {backup_file}")
    print("Le site devrait refonctionner après redémarrage.")
except FileNotFoundError:
    print(f"❌ Backup introuvable: {backup_file}")
    print("Tentative avec un autre backup...")
    
    # Essayer d'autres backups
    other_backups = [
        forms_file + '.backup',
        forms_file + '.bak',
        forms_file + '.orig'
    ]
    
    for backup in other_backups:
        try:
            shutil.copy2(backup, forms_file)
            print(f"✓ Fichier restauré depuis: {backup}")
            break
        except FileNotFoundError:
            continue
    else:
        print("❌ Aucun backup trouvé. Correction manuelle nécessaire.")