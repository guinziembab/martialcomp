#!/usr/bin/env python3
"""
Script de Traduction Automatique - Portugais
============================================
Traduit automatiquement les 5,406 chaînes manquantes en portugais
en utilisant DeepL API (500k caractères/mois gratuits)

Usage:
    python translate_portuguese.py --api-key YOUR_DEEPL_KEY
    python translate_portuguese.py --api-key YOUR_DEEPL_KEY --dry-run
    python translate_portuguese.py --report-only
"""

import argparse
import sys
from pathlib import Path

try:
    import polib
except ImportError:
    print("❌ Erreur: Module 'polib' manquant")
    print("\nInstallez avec:")
    print("  pip install polib")
    sys.exit(1)

try:
    import deepl
except ImportError:
    print("⚠️  Module 'deepl' non installé")
    print("Pour traduction automatique, installez:")
    print("  pip install deepl")
    print("\nMode rapport uniquement disponible.")
    deepl = None

class PortugueseTranslator:
    """Gestionnaire de traduction pour le portugais"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.translator = None
        self.po_file_path = Path('locale/pt/LC_MESSAGES/django.po')
        self.po = None
        
    def load_po_file(self):
        """Charge le fichier .po"""
        if not self.po_file_path.exists():
            print(f"❌ Fichier introuvable: {self.po_file_path}")
            return False
        
        try:
            self.po = polib.pofile(str(self.po_file_path))
            print(f"✅ Fichier .po chargé: {len(self.po)} entrées")
            return True
        except Exception as e:
            print(f"❌ Erreur lecture .po: {e}")
            return False
    
    def analyze(self):
        """Analyse le fichier et affiche les statistiques"""
        if not self.po:
            return
        
        total = len(self.po)
        translated = len([e for e in self.po if e.msgstr and e.msgstr != ''])
        untranslated = len([e for e in self.po if not e.msgstr or e.msgstr == ''])
        fuzzy = len(self.po.fuzzy_entries())
        
        print("\n" + "="*70)
        print("  ANALYSE DU PORTUGAIS (pt)")
        print("="*70)
        print(f"\n  Total de chaînes:     {total:,}")
        print(f"  ✅ Traduites:          {translated:,} ({translated*100//total}%)")
        print(f"  ❌ Non traduites:      {untranslated:,} ({untranslated*100//total}%)")
        print(f"  ⚠️  Fuzzy:              {fuzzy:,}")
        print(f"\n  {'='*66}")
        print(f"  TAUX DE COMPLÉTION: {translated*100//total}%")
        print(f"  {'='*66}\n")
        
        # Exemples de chaînes non traduites
        print("  Exemples de chaînes à traduire (10 premières):")
        print("  " + "-"*66)
        count = 0
        for entry in self.po:
            if (not entry.msgstr or entry.msgstr == '') and entry.msgid:
                count += 1
                msgid_short = entry.msgid[:60] + "..." if len(entry.msgid) > 60 else entry.msgid
                print(f"  {count}. {msgid_short}")
                if count >= 10:
                    break
        
        return {
            'total': total,
            'translated': translated,
            'untranslated': untranslated,
            'fuzzy': fuzzy,
            'percentage': translated*100//total
        }
    
    def init_deepl(self):
        """Initialise le client DeepL"""
        if not deepl:
            print("❌ Module deepl non installé")
            return False
        
        if not self.api_key:
            print("❌ Clé API DeepL requise")
            return False
        
        try:
            self.translator = deepl.Translator(self.api_key)
            usage = self.translator.get_usage()
            print(f"\n✅ DeepL connecté")
            print(f"   Usage: {usage.character.count:,} / {usage.character.limit:,} caractères")
            
            # Vérifier s'il reste assez de quota
            # Estimation: ~50 caractères par chaîne × 5,406 = ~270k caractères
            estimated_chars = 5406 * 50
            remaining = usage.character.limit - usage.character.count
            
            if remaining < estimated_chars:
                print(f"⚠️  Attention: Quota insuffisant")
                print(f"   Estimé nécessaire: {estimated_chars:,} caractères")
                print(f"   Quota restant: {remaining:,} caractères")
                return False
            else:
                print(f"✅ Quota suffisant ({remaining:,} caractères disponibles)")
            
            return True
        except Exception as e:
            print(f"❌ Erreur connexion DeepL: {e}")
            return False
    
    def translate_all(self, dry_run=False, limit=None):
        """Traduit toutes les chaînes manquantes"""
        if not self.translator:
            print("❌ Traducteur non initialisé")
            return False
        
        untranslated = [e for e in self.po if not e.msgstr or e.msgstr == '']
        total_to_translate = len(untranslated)
        
        if limit:
            untranslated = untranslated[:limit]
            print(f"\n⚠️  Mode limité: Traduction de {limit} chaînes (sur {total_to_translate})")
        
        print(f"\n{'='*70}")
        print(f"  TRADUCTION DE {len(untranslated)} CHAÎNES")
        print(f"{'='*70}\n")
        
        if dry_run:
            print("⚠️  MODE SIMULATION - Aucune modification ne sera sauvegardée\n")
        
        translated_count = 0
        error_count = 0
        
        for i, entry in enumerate(untranslated, 1):
            try:
                # Traduire avec DeepL
                result = self.translator.translate_text(
                    entry.msgid,
                    source_lang='FR',
                    target_lang='PT-PT',
                    preserve_formatting=True,
                    tag_handling='html'
                )
                
                if not dry_run:
                    entry.msgstr = str(result)
                
                translated_count += 1
                
                # Afficher progression tous les 100
                if i % 100 == 0:
                    print(f"  Progression: {i}/{len(untranslated)} ({i*100//len(untranslated)}%)")
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Afficher seulement les 5 premières erreurs
                    print(f"  ❌ Erreur [{i}]: {str(e)[:50]}...")
        
        print(f"\n{'='*70}")
        print(f"  RÉSULTATS")
        print(f"{'='*70}")
        print(f"  ✅ Traduites:  {translated_count}")
        print(f"  ❌ Erreurs:     {error_count}")
        print(f"{'='*70}\n")
        
        # Sauvegarder si pas en mode dry-run
        if not dry_run and translated_count > 0:
            try:
                self.po.save()
                print(f"✅ Fichier sauvegardé: {self.po_file_path}")
                print(f"\n⚠️  PROCHAINES ÉTAPES:")
                print(f"  1. Réviser les traductions avec Poedit Pro")
                print(f"  2. Compiler: python manage.py compilemessages -l pt")
                print(f"  3. Tester: http://localhost:8000/pt/")
            except Exception as e:
                print(f"❌ Erreur sauvegarde: {e}")
                return False
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Traduction automatique du portugais pour MartialComp'
    )
    parser.add_argument(
        '--api-key',
        help='Clé API DeepL (obtenir sur https://www.deepl.com/pro-api)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Générer uniquement le rapport (pas de traduction)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mode simulation (ne sauvegarde pas)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limiter le nombre de traductions (test)'
    )
    
    args = parser.parse_args()
    
    print("\n╔═══════════════════════════════════════════════════════════════════╗")
    print("║  TRADUCTION AUTOMATIQUE - PORTUGAIS (PT)                          ║")
    print("╚═══════════════════════════════════════════════════════════════════╝\n")
    
    # Créer le traducteur
    translator = PortugueseTranslator(api_key=args.api_key)
    
    # Charger le fichier .po
    if not translator.load_po_file():
        sys.exit(1)
    
    # Analyser
    stats = translator.analyze()
    
    # Mode rapport uniquement
    if args.report_only:
        print("\n✅ Rapport généré. Pour traduire, utilisez --api-key")
        print("\nObtenir une clé gratuite DeepL:")
        print("  1. Aller sur https://www.deepl.com/pro-api")
        print("  2. Créer un compte (gratuit)")
        print("  3. Copier la clé API")
        print("  4. python translate_portuguese.py --api-key VOTRE_CLE")
        return
    
    # Traduction
    if not args.api_key:
        print("\n❌ Erreur: --api-key requis pour la traduction")
        print("\nUtilisez --report-only pour voir uniquement le rapport")
        sys.exit(1)
    
    # Initialiser DeepL
    if not translator.init_deepl():
        sys.exit(1)
    
    # Confirmer avant traduction
    if not args.dry_run and stats['untranslated'] > 100:
        print(f"\n⚠️  ATTENTION: Vous allez traduire {stats['untranslated']} chaînes")
        print(f"   Cela consommera ~{stats['untranslated']*50:,} caractères de votre quota DeepL")
        response = input("\nContinuer? (oui/non): ")
        if response.lower() not in ['oui', 'yes', 'y', 'o']:
            print("❌ Annulé par l'utilisateur")
            return
    
    # Traduire
    translator.translate_all(dry_run=args.dry_run, limit=args.limit)

if __name__ == '__main__':
    main()
