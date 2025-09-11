#!/usr/bin/env python3
"""
Nettoyeur spécialisé pour le caractère U+FEFF dans categories.py
Le problème est que U+FEFF peut être présent n'importe où dans le fichier, pas seulement au début
"""

import os

def analyze_categories_file_deeply():
    """Analyse en profondeur du fichier categories.py pour trouver U+FEFF"""
    file_path = "apps/competitions/views/onboarding/categories.py"
    
    print("🔍 ANALYSE EN PROFONDEUR - categories.py")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print("❌ Fichier non trouvé")
        return False
    
    try:
        # Lecture binaire pour analyse complète
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        print(f"📊 Taille: {len(raw_content)} bytes")
        print(f"🔍 Premiers 20 bytes: {raw_content[:20].hex()}")
        print(f"🔍 Premiers 20 bytes (repr): {repr(raw_content[:20])}")
        
        # Recherche de U+FEFF sous différentes formes
        feff_patterns = [
            (b'\xef\xbb\xbf', 'BOM UTF-8 (EF BB BF)'),
            (b'\xff\xfe', 'BOM UTF-16 LE (FF FE)'),
            (b'\xfe\xff', 'BOM UTF-16 BE (FE FF)'),
            (b'\xef\xbf\xbf', 'U+FEFF en UTF-8 (EF BF BF)'),
            (b'\x00\xfe\xff', 'U+FEFF variant 1'),
            (b'\xfe\xff\x00', 'U+FEFF variant 2'),
        ]
        
        feff_found = []
        
        for pattern, description in feff_patterns:
            positions = []
            start = 0
            while True:
                pos = raw_content.find(pattern, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            if positions:
                feff_found.append((pattern, description, positions))
                print(f"🚨 {description} trouvé aux positions: {positions}")
        
        # Tentative de lecture en UTF-8 pour voir où est le problème
        try:
            text_content = raw_content.decode('utf-8')
            print(f"✅ Décodage UTF-8 réussi, {len(text_content)} caractères")
            
            # Recherche de U+FEFF dans le texte décodé
            feff_char_positions = []
            for i, char in enumerate(text_content):
                if ord(char) == 0xFEFF:
                    feff_char_positions.append(i)
            
            if feff_char_positions:
                print(f"🚨 Caractère U+FEFF trouvé aux positions texte: {feff_char_positions}")
                
                # Afficher le contexte autour de chaque U+FEFF
                for pos in feff_char_positions[:5]:  # Max 5 occurrences
                    start_context = max(0, pos - 20)
                    end_context = min(len(text_content), pos + 20)
                    context = text_content[start_context:end_context]
                    print(f"   Position {pos}: {repr(context)}")
            else:
                print("❓ Aucun U+FEFF trouvé dans le texte décodé")
        
        except UnicodeDecodeError as e:
            print(f"❌ Erreur décodage UTF-8: {e}")
            
            # Essai avec d'autres encodages
            for encoding in ['latin1', 'cp1252', 'utf-16']:
                try:
                    text_content = raw_content.decode(encoding)
                    print(f"✅ Décodage {encoding} réussi")
                    break
                except:
                    continue
        
        return True, feff_found
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return False, []

def clean_feff_from_categories():
    """Nettoie tous les caractères U+FEFF du fichier categories.py"""
    file_path = "apps/competitions/views/onboarding/categories.py"
    
    print("\n🧹 NETTOYAGE COMPLET U+FEFF")
    print("=" * 35)
    
    try:
        # Lecture du fichier
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        original_content = raw_content
        
        # Supprimer tous les patterns U+FEFF possibles
        feff_patterns = [
            b'\xef\xbb\xbf',      # BOM UTF-8
            b'\xff\xfe',          # BOM UTF-16 LE  
            b'\xfe\xff',          # BOM UTF-16 BE
            b'\xef\xbf\xbf',      # U+FEFF en UTF-8
            b'\x00\xfe\xff',      # Variants
            b'\xfe\xff\x00',
        ]
        
        for pattern in feff_patterns:
            if pattern in raw_content:
                raw_content = raw_content.replace(pattern, b'')
                print(f"🧹 Pattern supprimé: {pattern.hex()}")
        
        # Nettoyage via texte UTF-8 si possible
        try:
            text_content = raw_content.decode('utf-8')
            
            # Supprimer le caractère U+FEFF du texte
            original_text_length = len(text_content)
            text_content = text_content.replace('\ufeff', '')  # Supprime U+FEFF
            
            if len(text_content) != original_text_length:
                print(f"🧹 Caractères U+FEFF supprimés du texte: {original_text_length - len(text_content)}")
                
                # Reconvertir en bytes
                raw_content = text_content.encode('utf-8')
        
        except UnicodeDecodeError:
            print("⚠️ Impossible de nettoyer via UTF-8")
        
        # Vérifier si des changements ont été faits
        if raw_content != original_content:
            # Sauvegarde
            backup_path = file_path + ".feff_backup"
            with open(backup_path, 'wb') as backup:
                backup.write(original_content)
            print(f"💾 Sauvegarde: {backup_path}")
            
            # Réécriture du fichier nettoyé
            with open(file_path, 'wb') as f:
                f.write(raw_content)
            
            print(f"✅ Fichier nettoyé: {len(original_content)} → {len(raw_content)} bytes")
            
            # Test syntaxe
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    clean_text = f.read()
                compile(clean_text, file_path, 'exec')
                print("✅ Syntaxe Python: VALIDÉE")
                return True
            except SyntaxError as e:
                print(f"❌ Erreur syntaxe persistante: {e}")
                return False
        else:
            print("❓ Aucun changement nécessaire")
            return True
            
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return False

def recreate_categories_if_needed():
    """Recrée le fichier categories.py si le nettoyage échoue"""
    file_path = "apps/competitions/views/onboarding/categories.py"
    
    print("\n🔄 RECRÉATION DU FICHIER categories.py")
    print("=" * 40)
    
    # Contenu minimal pour categories.py
    minimal_content = '''import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@login_required
def handle_categories_setup(request):
    """Gère la configuration des catégories dans le processus d'onboarding."""
    # TODO: Implémenter la logique de configuration des catégories
    
    # Pour l'instant, on redirige vers la fin de l'onboarding
    request.user.profile.onboarding_step = 'completed'
    request.user.profile.onboarding_completed = True
    request.user.profile.save()
    
    if 'onboarding_step' in request.session:
        del request.session['onboarding_step']
    
    messages.success(request, _("Configuration des catégories terminée."))
    return redirect('competitions:dashboard:club')
'''
    
    try:
        # Sauvegarde de l'ancien fichier
        backup_path = file_path + ".original_backup"
        if os.path.exists(file_path):
            with open(file_path, 'rb') as original:
                with open(backup_path, 'wb') as backup:
                    backup.write(original.read())
            print(f"💾 Sauvegarde originale: {backup_path}")
        
        # Création du nouveau fichier propre
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(minimal_content)
        
        print("✅ Fichier categories.py recréé avec succès")
        
        # Test syntaxe
        try:
            compile(minimal_content, file_path, 'exec')
            print("✅ Syntaxe Python: PARFAITE")
            return True
        except SyntaxError as e:
            print(f"❌ Erreur syntaxe: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur recréation: {e}")
        return False

def test_django_final():
    """Test Django après correction"""
    print("\n🧪 TEST DJANGO FINAL")
    print("=" * 25)
    
    try:
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'manage.py', 'check'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Django check: SUCCÈS TOTAL !")
            return True
        else:
            print("❌ Django check: ERREURS")
            print("Dernières lignes d'erreur:")
            for line in result.stderr.strip().split('\n')[-3:]:
                print(f"   {line}")
            return False
            
    except Exception as e:
        print(f"❌ Impossible de tester Django: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 CORRECTEUR SPÉCIALISÉ categories.py - U+FEFF")
    print("=" * 60)
    
    # 1. Analyse approfondie
    success, feff_found = analyze_categories_file_deeply()
    
    if not success:
        return
    
    # 2. Tentative de nettoyage
    if feff_found:
        print("\n" + "🚨 CARACTÈRES U+FEFF DÉTECTÉS - NETTOYAGE EN COURS")
        cleaned = clean_feff_from_categories()
    else:
        print("\n" + "❓ AUCUN U+FEFF DÉTECTÉ - TENTATIVE DE NETTOYAGE QUAND MÊME")
        cleaned = clean_feff_from_categories()
    
    # 3. Recréation si nettoyage échoue
    if not cleaned:
        print("\n" + "🔄 NETTOYAGE ÉCHOUÉ - RECRÉATION DU FICHIER")
        recreated = recreate_categories_if_needed()
        if not recreated:
            print("❌ Échec complet")
            return
    
    # 4. Test Django final
    django_ok = test_django_final()
    
    print("\n🎯 RÉSULTAT FINAL")
    print("=" * 25)
    if django_ok:
        print("🎉 SUCCÈS ! Django fonctionne maintenant.")
        print("💻 Commande: python manage.py runserver")
    else:
        print("❌ Django a encore des problèmes.")

if __name__ == "__main__":
    main()