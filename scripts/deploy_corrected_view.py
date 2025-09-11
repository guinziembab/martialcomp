#!/usr/bin/env python3
"""
Script pour appliquer la correction complète à la vue practitioners.py
Remplace la section POST avec toutes les corrections nécessaires
"""

import os
import shutil
from datetime import datetime

def apply_corrections():
    """Applique toutes les corrections à la vue"""
    
    print("🔧 APPLICATION DES CORRECTIONS À LA VUE PRACTITIONERS")
    print("=" * 60)
    
    target_file = "/opt/martialcomp/app/competitions/views/club/practitioners.py"
    backup_file = f"{target_file}.backup_corrected_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 1. Backup de sécurité
        print(f"📁 Création du backup: {backup_file}")
        shutil.copy2(target_file, backup_file)
        
        # 2. Lire le fichier actuel
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. Code corrigé pour la section POST
        corrected_post_section = '''    if request.method == 'POST':
        # Créer le formulaire avec les données POST
        if practitioner:
            form = PractitionerForm(request.POST, request.FILES, instance=practitioner, request=request)
        else:
            form = PractitionerForm(request.POST, request.FILES, request=request)
        
        if form.is_valid():
            try:
                # Sauvegarder le pratiquant
                practitioner = form.save(commit=False)
                
                # CORRECTION: Vérifier que l'objet a été créé correctement
                if not practitioner:
                    messages.error(request, _("Erreur lors de la création du pratiquant. Veuillez vérifier les données saisies."))
                    return redirect("competitions:club:practitioners")
                
                # S'assurer que le pratiquant est associé à l'organisation
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if not club_organization:
                    messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
                    return redirect('competitions:dashboard')
                    
                if not practitioner.organization:
                    practitioner.organization = club_organization
                
                # Sauvegarder le pratiquant
                practitioner.save()
                
                # Sauvegarder les relations M2M (disciplines)
                form.save_m2m()
                
                if practitioner_id:
                    messages.success(request, _("Pratiquant mis à jour avec succès."))
                else:
                    messages.success(request, _("Pratiquant créé avec succès."))
                
                return redirect('competitions:club:practitioners')
                
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {0}").format(str(e)))
                logger.error(f"Erreur lors de la sauvegarde du pratiquant: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Log des erreurs pour debugging avec plus de détails
            logger.error(f"Erreurs du formulaire: {form.errors}")
            logger.error(f"Données POST reçues: {dict(request.POST)}")'''
        
        # 4. Trouver et remplacer la section POST
        start_marker = "    if request.method == 'POST':"
        end_marker = "    else:\n        # Créer le formulaire pour GET"
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos == -1:
            print("❌ Marqueur de début non trouvé")
            return False
        
        if end_pos == -1:
            print("❌ Marqueur de fin non trouvé")
            return False
        
        # 5. Remplacer la section
        new_content = (
            content[:start_pos] + 
            corrected_post_section + "\n\n" +
            content[end_pos:]
        )
        
        # 6. Écrire le fichier corrigé
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Correction appliquée avec succès")
        
        # 7. Test de syntaxe Python
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', target_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Syntaxe Python validée")
            return True
        else:
            print(f"❌ Erreur de syntaxe: {result.stderr}")
            # Restaurer le backup
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'application: {e}")
        
        # Restaurer le backup en cas d'erreur
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré automatiquement")
        
        return False

def main():
    print("🚀 SCRIPT DE CORRECTION COMPLÈTE DE LA VUE")
    print("=" * 60)
    print("🎯 Objectif: Corriger la vue avec vérification None et logs détaillés")
    print()
    
    success = apply_corrections()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 CORRECTION APPLIQUÉE AVEC SUCCÈS!")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. 🔄 Redémarrer Django:")
        print("   sudo systemctl restart martialcomp")
        print("2. 🧪 Tester l'enregistrement d'un practitioner")
        print("3. 📋 Vérifier les logs détaillés:")
        print("   sudo journalctl -u martialcomp -f")
        
        print("\n🔍 CORRECTIONS APPLIQUÉES:")
        print("   - Vérification if not practitioner")
        print("   - Logs détaillés des erreurs de formulaire")
        print("   - Logs des données POST reçues")
        print("   - Messages d'erreur appropriés")
        
    else:
        print("❌ ÉCHEC DE LA CORRECTION")
        print("   Le fichier original a été restauré automatiquement")
    
    print(f"\n📁 Backup disponible: practitioners.py.backup_corrected_*")

if __name__ == "__main__":
    main()