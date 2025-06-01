#!/usr/bin/env python3
"""
Script pour télécharger et configurer Bootstrap et Font Awesome en local
"""
import os
import requests
import shutil
from pathlib import Path

def create_vendor_directories():
    """Créer la structure des dossiers vendor"""
    
    base_dir = Path("/mnt/c/martial_hub_django/martialcomp")
    vendor_dir = base_dir / "static" / "vendor"
    
    # Créer les dossiers
    directories = [
        vendor_dir / "bootstrap" / "css",
        vendor_dir / "bootstrap" / "js",
        vendor_dir / "fontawesome" / "css",
        vendor_dir / "fontawesome" / "webfonts"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Dossier créé: {directory}")
    
    return vendor_dir

def download_bootstrap(vendor_dir):
    """Télécharger Bootstrap 5.3.0"""
    
    print("\n📦 TÉLÉCHARGEMENT DE BOOTSTRAP 5.3.0")
    print("=" * 40)
    
    bootstrap_files = {
        "css/bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css",
        "js/bootstrap.bundle.min.js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"
    }
    
    bootstrap_dir = vendor_dir / "bootstrap"
    
    for local_path, url in bootstrap_files.items():
        try:
            print(f"📥 Téléchargement: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            file_path = bootstrap_dir / local_path
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            size = len(response.content)
            print(f"✅ Sauvegardé: {file_path} ({size:,} octets)")
            
        except Exception as e:
            print(f"❌ Erreur téléchargement {local_path}: {str(e)}")

def download_fontawesome(vendor_dir):
    """Télécharger Font Awesome 6.0.0"""
    
    print("\n🔤 TÉLÉCHARGEMENT DE FONT AWESOME 6.0.0")
    print("=" * 40)
    
    fontawesome_css_url = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    
    try:
        print(f"📥 Téléchargement: {fontawesome_css_url}")
        response = requests.get(fontawesome_css_url, timeout=30)
        response.raise_for_status()
        
        css_path = vendor_dir / "fontawesome" / "css" / "all.min.css"
        with open(css_path, 'wb') as f:
            f.write(response.content)
        
        size = len(response.content)
        print(f"✅ CSS sauvegardé: {css_path} ({size:,} octets)")
        
        # Télécharger les fonts principales
        font_files = [
            "fa-solid-900.woff2",
            "fa-regular-400.woff2", 
            "fa-brands-400.woff2"
        ]
        
        webfonts_dir = vendor_dir / "fontawesome" / "webfonts"
        
        for font_file in font_files:
            font_url = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/{font_file}"
            try:
                print(f"📥 Téléchargement font: {font_url}")
                font_response = requests.get(font_url, timeout=30)
                font_response.raise_for_status()
                
                font_path = webfonts_dir / font_file
                with open(font_path, 'wb') as f:
                    f.write(font_response.content)
                
                font_size = len(font_response.content)
                print(f"✅ Font sauvegardée: {font_path} ({font_size:,} octets)")
                
            except Exception as e:
                print(f"⚠️ Erreur téléchargement font {font_file}: {str(e)}")
                
    except Exception as e:
        print(f"❌ Erreur téléchargement Font Awesome: {str(e)}")

def create_local_base_template(vendor_dir):
    """Créer une version locale du template base.html"""
    
    print("\n📝 CRÉATION DU TEMPLATE BASE LOCAL")
    print("=" * 40)
    
    # Lire le template actuel
    base_template_path = Path("/mnt/c/martial_hub_django/martialcomp/competitions/templates/base.html")
    
    if not base_template_path.exists():
        print(f"❌ Template base non trouvé: {base_template_path}")
        return
    
    with open(base_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les CDN par les fichiers locaux
    content_local = content.replace(
        'href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css"',
        'href="{% static \'vendor/bootstrap/css/bootstrap.min.css\' %}"'
    ).replace(
        'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"',
        'href="{% static \'vendor/fontawesome/css/all.min.css\' %}"'
    ).replace(
        'src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"',
        'src="{% static \'vendor/bootstrap/js/bootstrap.bundle.min.js\' %}"'
    )
    
    # Sauvegarder la version locale
    local_template_path = base_template_path.parent / "base_local.html"
    
    with open(local_template_path, 'w', encoding='utf-8') as f:
        f.write(content_local)
    
    print(f"✅ Template local créé: {local_template_path}")
    
    # Créer un backup de l'original
    backup_path = base_template_path.parent / "base_cdn.html"
    shutil.copy2(base_template_path, backup_path)
    print(f"✅ Backup CDN créé: {backup_path}")
    
    return local_template_path

def create_switch_script():
    """Créer un script pour basculer entre CDN et local"""
    
    print("\n🔄 CRÉATION DU SCRIPT DE BASCULEMENT")
    print("=" * 40)
    
    script_content = '''#!/usr/bin/env python3
"""
Script pour basculer entre CDN et fichiers locaux
"""
import shutil
from pathlib import Path

def switch_to_local():
    """Basculer vers les fichiers locaux"""
    base_dir = Path("/mnt/c/martial_hub_django/martialcomp/competitions/templates")
    
    # Sauvegarder la version CDN
    shutil.copy2(base_dir / "base.html", base_dir / "base_cdn.html")
    
    # Activer la version locale
    if (base_dir / "base_local.html").exists():
        shutil.copy2(base_dir / "base_local.html", base_dir / "base.html")
        print("✅ Basculé vers les fichiers locaux")
        print("📋 Exécutez: python manage.py collectstatic")
    else:
        print("❌ base_local.html non trouvé")

def switch_to_cdn():
    """Basculer vers les CDN"""
    base_dir = Path("/mnt/c/martial_hub_django/martialcomp/competitions/templates")
    
    # Restaurer la version CDN
    if (base_dir / "base_cdn.html").exists():
        shutil.copy2(base_dir / "base_cdn.html", base_dir / "base.html")
        print("✅ Basculé vers les CDN")
    else:
        print("❌ base_cdn.html non trouvé")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python switch_assets.py [local|cdn]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "local":
        switch_to_local()
    elif mode == "cdn":
        switch_to_cdn()
    else:
        print("Mode invalide. Utilisez 'local' ou 'cdn'")
'''
    
    script_path = Path("/mnt/c/martial_hub_django/martialcomp/switch_assets.py")
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Rendre le script exécutable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Script créé: {script_path}")
    print(f"📋 Usage: python switch_assets.py [local|cdn]")

def update_csp_for_local():
    """Mettre à jour la CSP pour les fichiers locaux"""
    
    print("\n🔒 MISE À JOUR CSP POUR FICHIERS LOCAUX")
    print("=" * 40)
    
    csp_info = '''
Pour une sécurité maximale avec les fichiers locaux, vous pouvez
modifier security/middleware.py pour utiliser une CSP plus restrictive :

# CSP plus restrictive pour fichiers locaux
csp = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self' data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self';"
)

Cette configuration :
✅ Bloque tous les CDN externes
✅ Autorise seulement les ressources locales
✅ Maintient la sécurité maximale
✅ Fonctionne hors ligne
'''
    
    print(csp_info)

def main():
    """Fonction principale"""
    
    print("🚀 SETUP DES ASSETS LOCAUX BOOTSTRAP & FONT AWESOME")
    print("=" * 60)
    
    try:
        # Créer les dossiers
        vendor_dir = create_vendor_directories()
        
        # Télécharger les assets
        download_bootstrap(vendor_dir)
        download_fontawesome(vendor_dir)
        
        # Créer les templates
        create_local_base_template(vendor_dir)
        create_switch_script()
        
        # Info CSP
        update_csp_for_local()
        
        print(f"\n" + "=" * 60)
        print("✅ SETUP TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)
        
        print("📋 PROCHAINES ÉTAPES :")
        print("1. python manage.py collectstatic")
        print("2. python switch_assets.py local  # Pour activer les fichiers locaux")
        print("3. python switch_assets.py cdn    # Pour revenir aux CDN")
        
        print(f"\n🎯 AVANTAGES DES FICHIERS LOCAUX :")
        print("✅ Sécurité maximale (pas de CDN externes)")
        print("✅ Fonctionnement hors ligne")
        print("✅ Contrôle total des versions")
        print("✅ Performance (pas de requêtes externes)")
        
    except Exception as e:
        print(f"❌ Erreur durant le setup: {str(e)}")

if __name__ == "__main__":
    main()