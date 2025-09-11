"""Script pour activer/désactiver le router multitenant dans settings.py"""
import re
import sys

def toggle_router(enable=True):
    settings_path = 'config/settings.py'
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver DATABASE_ROUTERS
    pattern = r"(DATABASE_ROUTERS\s*=\s*\[[\s\S]*?\])"
    
    if enable:
        # Réactiver le router (enlever les commentaires)
        new_content = re.sub(r"#\s*(" + pattern + ")", r"\1", content)
    else:
        # Désactiver le router (ajouter des commentaires)
        new_content = re.sub(pattern, r"# \1", content)
    
    if new_content != content:
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Router {'activé' if enable else 'désactivé'}")
    else:
        print(f"Router déjà {'activé' if enable else 'désactivé'}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == 'disable':
            toggle_router(False)
        elif action == 'enable':
            toggle_router(True)
        else:
            print("Usage: python toggle_multitenant_router.py [enable|disable]")
    else:
        print("Usage: python toggle_multitenant_router.py [enable|disable]")