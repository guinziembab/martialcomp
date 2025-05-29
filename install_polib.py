#!/usr/bin/env python3
"""
Script pour installer la bibliothèque polib,
qui facilite grandement la manipulation des fichiers .po et .mo
"""
import sys
import subprocess
import os

def main():
    """Fonction principale pour installer polib"""
    print("Installation de polib...")
    
    try:
        # Vérifier si polib est déjà installé
        try:
            import polib
            print("polib est déjà installé!")
            return True
        except ImportError:
            pass
        
        # Déterminer la commande pip à utiliser
        pip_cmd = None
        for cmd in ['pip', 'pip3', sys.executable + ' -m pip']:
            try:
                subprocess.run(cmd.split() + ['--version'], 
                               capture_output=True, 
                               check=True)
                pip_cmd = cmd
                break
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        if not pip_cmd:
            print("Erreur: Impossible de trouver pip. Veuillez installer pip manuellement.")
            return False
        
        # Installer polib
        print(f"Utilisation de {pip_cmd} pour installer polib...")
        try:
            result = subprocess.run(pip_cmd.split() + ['install', 'polib'],
                                   capture_output=True,
                                   text=True,
                                   check=True)
            print(result.stdout)
            print("polib a été installé avec succès!")
            
            # Vérifier que l'installation a réussi
            try:
                import polib
                print("Vérification de l'installation réussie.")
                return True
            except ImportError:
                print("Erreur: polib a été installé mais ne peut pas être importé.")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation: {e}")
            print(f"Sortie: {e.stderr}")
            
            # Essayer avec --user si nécessaire
            print("Tentative d'installation avec l'option --user...")
            try:
                result = subprocess.run(pip_cmd.split() + ['install', '--user', 'polib'],
                                      capture_output=True,
                                      text=True,
                                      check=True)
                print(result.stdout)
                print("polib a été installé avec succès (mode utilisateur)!")
                return True
            except subprocess.CalledProcessError as e2:
                print(f"Erreur lors de l'installation (mode utilisateur): {e2}")
                print(f"Sortie: {e2.stderr}")
                return False
    
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)