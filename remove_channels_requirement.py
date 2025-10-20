#!/usr/bin/env python
"""
Script pour retirer temporairement la dépendance à channels
pour permettre les tests du patch onboarding
"""

import os

# Fichier settings development
settings_file = 'config/settings/development.py'

print("=" * 60)
print("🔧 PATCH TEMPORAIRE - Retrait de channels")
print("=" * 60)

try:
    # Lire le fichier
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Chercher channels dans INSTALLED_APPS
    if "'channels'," in content or '"channels",' in content:
        # Commenter la ligne channels
        content = content.replace("'channels',", "# 'channels',  # TEMPORAIREMENT DÉSACTIVÉ")
        content = content.replace('"channels",', '# "channels",  # TEMPORAIREMENT DÉSACTIVÉ')
        
        # Sauvegarder
        with open(settings_file + '.backup', 'w') as f:
            f.write(content)
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ 'channels' commenté dans INSTALLED_APPS")
        print(f"✅ Backup créé: {settings_file}.backup")
    else:
        print("⚠️  'channels' non trouvé dans INSTALLED_APPS")
    
    # Vérifier aussi daphne
    if "'daphne'," in content or '"daphne",' in content:
        content = content.replace("'daphne',", "# 'daphne',  # TEMPORAIREMENT DÉSACTIVÉ")
        content = content.replace('"daphne",', '# "daphne",  # TEMPORAIREMENT DÉSACTIVÉ')
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ 'daphne' également commenté")
    
    # Vérifier ASGI_APPLICATION
    if "ASGI_APPLICATION" in content and not "# ASGI_APPLICATION" in content:
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if "ASGI_APPLICATION" in line and not line.strip().startswith('#'):
                new_lines.append(f"# {line}  # TEMPORAIREMENT DÉSACTIVÉ")
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ ASGI_APPLICATION commenté")
    
    # Vérifier CHANNEL_LAYERS
    if "CHANNEL_LAYERS" in content:
        lines = content.split('\n')
        new_lines = []
        in_channel_layers = False
        bracket_count = 0
        
        for line in lines:
            if "CHANNEL_LAYERS" in line and not line.strip().startswith('#'):
                in_channel_layers = True
                new_lines.append(f"# {line}  # TEMPORAIREMENT DÉSACTIVÉ")
                if '{' in line:
                    bracket_count += line.count('{')
            elif in_channel_layers:
                new_lines.append(f"# {line}")
                bracket_count += line.count('{')
                bracket_count -= line.count('}')
                if bracket_count == 0:
                    in_channel_layers = False
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ CHANNEL_LAYERS commenté")
    
    print("\n✅ Patch appliqué avec succès!")
    print("ℹ️  Pour restaurer: mv config/settings/development.py.backup config/settings/development.py")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()