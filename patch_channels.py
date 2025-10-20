#!/usr/bin/env python3
"""
Patch temporaire pour contourner le problème de channels
"""

import os
import sys

# Lire les settings base
base_settings = 'config/settings/base.py'
dev_settings = 'config/settings/development.py'

def patch_file(filepath):
    """Commente toutes les références à channels dans un fichier"""
    print(f"\n📋 Patch de {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Backup
        with open(filepath + '.backup_channels', 'w') as f:
            f.writelines(lines)
        
        # Patch
        modified = False
        new_lines = []
        in_channels_block = False
        
        for line in lines:
            # Détecter INSTALLED_APPS
            if "'channels'," in line or '"channels",' in line:
                new_lines.append("    # 'channels',  # TEMPORAIREMENT DÉSACTIVÉ\n")
                modified = True
            elif "'daphne'," in line or '"daphne",' in line:
                new_lines.append("    # 'daphne',  # TEMPORAIREMENT DÉSACTIVÉ\n")
                modified = True
            elif "ASGI_APPLICATION" in line and not line.strip().startswith('#'):
                new_lines.append(f"# {line}")
                modified = True
            elif "CHANNEL_LAYERS" in line and not line.strip().startswith('#'):
                new_lines.append(f"# {line}")
                in_channels_block = True
                modified = True
            elif in_channels_block:
                # Continuer à commenter le bloc CHANNEL_LAYERS
                new_lines.append(f"# {line}")
                if line.strip() == "}":
                    in_channels_block = False
            else:
                new_lines.append(line)
        
        # Écrire le fichier patché
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        
        if modified:
            print(f"✅ {filepath} patché avec succès")
        else:
            print(f"ℹ️  Aucune modification nécessaire dans {filepath}")
        
        return modified
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 PATCH CHANNELS - Désactivation temporaire")
    print("=" * 60)
    
    # Patcher les deux fichiers
    patch_file(base_settings)
    patch_file(dev_settings)
    
    print("\n✅ Patch appliqué!")
    print("\nPour restaurer:")
    print(f"  mv {base_settings}.backup_channels {base_settings}")
    print(f"  mv {dev_settings}.backup_channels {dev_settings}")
    
    print("\n🚀 Vous pouvez maintenant démarrer le serveur:")
    print("   python3 manage.py runserver 0.0.0.0:8888")

if __name__ == "__main__":
    main()