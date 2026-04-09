#!/usr/bin/env python3
"""
Script pour mettre à jour le fichier PO anglais
en excluant les dossiers problématiques
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Mettre à jour le fichier PO anglais"""
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    # Dossiers à ignorer
    ignore_patterns = [
        "Backup_Prod.bak",
        "Debug.bak", 
        "BIG FIXING COMPT",
        "production_complete*",
        "production_transfer*",
        "backups",
        "venv*",
        "archive",
        "mobile*",
        "node_modules",
        "*.pyc",
        "__pycache__",
        ".git",
    ]
    
    print("🔄 Mise à jour du fichier PO anglais...")
    print("=" * 50)
    
    # Construire la commande
    cmd = [
        "python3", "manage.py", "makemessages",
        "-l", "en",
        "--no-obsolete",
        "--no-wrap",
    ]
    
    # Ajouter les patterns d'ignore
    for pattern in ignore_patterns:
        cmd.extend(["--ignore", pattern])
    
    print(f"📝 Commande: {' '.join(cmd)}")
    print()
    
    # Exécuter la commande
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=base_dir
        )
        
        # Afficher la sortie
        if result.stdout:
            # Filtrer les erreurs UnicodeDecodeError et CommandError
            lines = result.stdout.split('\n')
            for line in lines:
                if 'UnicodeDecodeError' not in line and 'CommandError' not in line:
                    if line.strip():
                        print(line)
        
        if result.stderr:
            # Filtrer les erreurs UnicodeDecodeError
            lines = result.stderr.split('\n')
            for line in lines:
                if 'UnicodeDecodeError' not in line and 'CommandError' not in line:
                    if line.strip() and 'invalid' not in line.lower():
                        print(f"⚠️  {line}", file=sys.stderr)
        
        # Vérifier si le fichier PO a été mis à jour
        po_file = base_dir / "locale" / "en" / "LC_MESSAGES" / "django.po"
        if po_file.exists():
            stat = po_file.stat()
            print()
            print("=" * 50)
            print(f"✅ Fichier PO trouvé: {po_file}")
            print(f"   Taille: {stat.st_size:,} octets")
            print(f"   Modifié: {stat.st_mtime}")
            print()
            print("✅ Mise à jour du fichier PO anglais terminée!")
            return 0
        else:
            print()
            print("❌ Fichier PO non trouvé!")
            return 1
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
