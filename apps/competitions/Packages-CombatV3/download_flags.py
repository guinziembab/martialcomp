#!/usr/bin/env python3
"""
Script de téléchargement automatique des drapeaux
MartialComp - Interface de Combat V3

Usage:
    python download_flags.py [--output-dir ./static/images/flags]
    
Description:
    Télécharge automatiquement les drapeaux de tous les pays supportés
    depuis l'API flagcdn.com
"""

import os
import sys
import requests
import argparse
from pathlib import Path
from typing import List, Tuple
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

# Liste complète des codes pays ISO 3166-1 alpha-2
COUNTRIES = [
    # Europe
    ("FR", "France"),
    ("BE", "Belgium"),
    ("DE", "Germany"),
    ("IT", "Italy"),
    ("ES", "Spain"),
    ("GB", "United Kingdom"),
    ("NL", "Netherlands"),
    ("PT", "Portugal"),
    ("CH", "Switzerland"),
    ("AT", "Austria"),
    ("PL", "Poland"),
    ("CZ", "Czech Republic"),
    ("GR", "Greece"),
    ("SE", "Sweden"),
    ("NO", "Norway"),
    ("DK", "Denmark"),
    ("FI", "Finland"),
    ("IE", "Ireland"),
    ("RO", "Romania"),
    ("HU", "Hungary"),
    ("BG", "Bulgaria"),
    ("HR", "Croatia"),
    ("SI", "Slovenia"),
    ("SK", "Slovakia"),
    ("LT", "Lithuania"),
    ("LV", "Latvia"),
    ("EE", "Estonia"),
    
    # Amériques
    ("US", "United States"),
    ("CA", "Canada"),
    ("BR", "Brazil"),
    ("AR", "Argentina"),
    ("MX", "Mexico"),
    ("CL", "Chile"),
    ("CO", "Colombia"),
    ("PE", "Peru"),
    ("VE", "Venezuela"),
    ("EC", "Ecuador"),
    ("BO", "Bolivia"),
    ("PY", "Paraguay"),
    ("UY", "Uruguay"),
    ("CR", "Costa Rica"),
    ("PA", "Panama"),
    ("CU", "Cuba"),
    ("DO", "Dominican Republic"),
    
    # Asie
    ("CN", "China"),
    ("JP", "Japan"),
    ("KR", "South Korea"),
    ("IN", "India"),
    ("TH", "Thailand"),
    ("VN", "Vietnam"),
    ("ID", "Indonesia"),
    ("MY", "Malaysia"),
    ("SG", "Singapore"),
    ("PH", "Philippines"),
    ("PK", "Pakistan"),
    ("BD", "Bangladesh"),
    ("IR", "Iran"),
    ("IQ", "Iraq"),
    ("IL", "Israel"),
    ("SA", "Saudi Arabia"),
    ("AE", "UAE"),
    ("KW", "Kuwait"),
    ("QA", "Qatar"),
    ("JO", "Jordan"),
    ("LB", "Lebanon"),
    
    # Afrique
    ("ZA", "South Africa"),
    ("EG", "Egypt"),
    ("MA", "Morocco"),
    ("DZ", "Algeria"),
    ("TN", "Tunisia"),
    ("SN", "Senegal"),
    ("CI", "Ivory Coast"),
    ("KE", "Kenya"),
    ("NG", "Nigeria"),
    ("GH", "Ghana"),
    ("CM", "Cameroon"),
    ("ET", "Ethiopia"),
    ("UG", "Uganda"),
    ("TZ", "Tanzania"),
    
    # Océanie
    ("AU", "Australia"),
    ("NZ", "New Zealand"),
    ("FJ", "Fiji"),
    ("PG", "Papua New Guinea"),
]

# URLs des APIs de drapeaux
FLAG_APIS = {
    'flagcdn': 'https://flagcdn.com/256x192/{}.png',
    'countryflagsapi': 'https://countryflagsapi.com/png/{}',
    'flagpedia': 'https://flagpedia.net/data/flags/w580/{}.png',
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def print_progress(current: int, total: int, prefix: str = '', suffix: str = ''):
    """Affiche une barre de progression."""
    bar_length = 50
    filled = int(bar_length * current / total)
    bar = '█' * filled + '-' * (bar_length - filled)
    percent = f"{100 * current / total:.1f}"
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)
    if current == total:
        print()

def download_flag(country_code: str, output_path: Path, api: str = 'flagcdn') -> Tuple[bool, str]:
    """
    Télécharge le drapeau d'un pays.
    
    Args:
        country_code: Code ISO du pays (ex: FR, BE)
        output_path: Chemin de sortie pour le fichier
        api: API à utiliser ('flagcdn', 'countryflagsapi', 'flagpedia')
    
    Returns:
        Tuple (success, message)
    """
    try:
        # Construire l'URL
        url = FLAG_APIS[api].format(country_code.lower())
        
        # Télécharger
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Sauvegarder
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True, f"✅ {country_code}"
        
    except requests.exceptions.RequestException as e:
        return False, f"❌ {country_code}: {str(e)}"
    except Exception as e:
        return False, f"❌ {country_code}: Erreur inattendue - {str(e)}"

def create_default_flag(output_path: Path, size: Tuple[int, int] = (256, 192)):
    """
    Crée un drapeau par défaut (carré gris).
    
    Args:
        output_path: Chemin de sortie
        size: Dimensions (largeur, hauteur)
    """
    try:
        from PIL import Image
        
        # Créer une image grise
        img = Image.new('RGB', size, color='#6c757d')
        
        # Ajouter un texte "?"
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Essayer de charger une police
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            # Dessiner le "?"
            text = "?"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
            draw.text(position, text, fill='white', font=font)
        except:
            pass  # Si le texte échoue, on garde juste le carré gris
        
        # Sauvegarder
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, 'PNG')
        
        return True, "✅ Drapeau par défaut créé"
        
    except ImportError:
        return False, "❌ Pillow non installé. Installez-le avec: pip install Pillow"
    except Exception as e:
        return False, f"❌ Erreur création drapeau par défaut: {str(e)}"

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale."""
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description='Télécharge les drapeaux pour MartialComp'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./static/images/flags',
        help='Répertoire de sortie (défaut: ./static/images/flags)'
    )
    parser.add_argument(
        '--api',
        type=str,
        choices=list(FLAG_APIS.keys()),
        default='flagcdn',
        help='API à utiliser pour le téléchargement'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force le téléchargement même si le fichier existe'
    )
    parser.add_argument(
        '--create-default',
        action='store_true',
        help='Crée un drapeau par défaut'
    )
    
    args = parser.parse_args()
    
    # Créer le répertoire de sortie
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🏁 TÉLÉCHARGEMENT DES DRAPEAUX")
    print("=" * 70)
    print(f"Répertoire de sortie: {output_dir}")
    print(f"API utilisée: {args.api}")
    print(f"Nombre de pays: {len(COUNTRIES)}")
    print()
    
    # Statistiques
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Télécharger tous les drapeaux
    for i, (code, name) in enumerate(COUNTRIES, 1):
        output_path = output_dir / f"{code}.png"
        
        # Vérifier si le fichier existe déjà
        if output_path.exists() and not args.force:
            skipped_count += 1
            print_progress(i, len(COUNTRIES), 
                          prefix='Téléchargement', 
                          suffix=f'⏭️  {code} (déjà existant)')
            time.sleep(0.1)  # Pour voir la progression
            continue
        
        # Télécharger
        success, message = download_flag(code, output_path, args.api)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
            print(f"\n{message}")
        
        # Afficher la progression
        print_progress(i, len(COUNTRIES), 
                      prefix='Téléchargement', 
                      suffix=f'{code} - {name}')
        
        # Petite pause pour ne pas surcharger l'API
        time.sleep(0.2)
    
    print()
    
    # Créer le drapeau par défaut si demandé
    if args.create_default:
        print("\nCréation du drapeau par défaut...")
        default_path = output_dir / "default.png"
        success, message = create_default_flag(default_path)
        print(message)
    
    # Afficher le résumé
    print()
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"✅ Téléchargés avec succès: {success_count}")
    print(f"❌ Échecs: {failed_count}")
    print(f"⏭️  Ignorés (déjà existants): {skipped_count}")
    print(f"📁 Total de fichiers: {success_count + skipped_count}")
    print()
    
    # Lister les fichiers téléchargés
    flags = list(output_dir.glob("*.png"))
    print(f"Drapeaux disponibles: {len(flags)}")
    print(f"Emplacement: {output_dir.absolute()}")
    
    # Calculer la taille totale
    total_size = sum(f.stat().st_size for f in flags)
    print(f"Taille totale: {total_size / 1024:.1f} KB")
    
    print()
    print("=" * 70)
    print("✅ TERMINÉ !")
    print("=" * 70)
    
    # Code de sortie
    sys.exit(0 if failed_count == 0 else 1)

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Téléchargement interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {str(e)}")
        sys.exit(1)
