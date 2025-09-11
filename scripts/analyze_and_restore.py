#!/usr/bin/env python3
"""
Script pour analyser et restaurer les éléments cassés
"""

import os
import shutil
import subprocess
import time

def analyze_broken_files():
    """Analyse les fichiers cassés"""
    print("🔍 ANALYSE DES FICHIERS CASSÉS")
    print("=" * 40)
    
    # Fichiers critiques à vérifier
    critical_files = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
        'complete_translations.py',
        'smart_translate.py',
        'fix_languages.py',
        'check_languages.py',
    ]
    
    broken_files = []
    
    for file_path in critical_files:
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        if os.path.exists(prod_path):
            try:
                # Vérifier la syntaxe Python
                result = subprocess.run(['python3', '-m', 'py_compile', prod_path], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    broken_files.append(file_path)
                    print(f"❌ Fichier cassé: {file_path}")
                    print(f"   Erreur: {result.stderr.strip()}")
                else:
                    print(f"✅ Fichier OK: {file_path}")
            except Exception as e:
                broken_files.append(file_path)
                print(f"❌ Erreur de vérification: {file_path} - {e}")
        else:
            print(f"⚠️ Fichier manquant: {file_path}")
    
    return broken_files

def restore_critical_files():
    """Restaure les fichiers critiques depuis le développement"""
    print("\n🔄 RESTAURATION DES FICHIERS CRITIQUES")
    print("=" * 40)
    
    # Fichiers à restaurer depuis le développement
    files_to_restore = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
    ]
    
    restored_count = 0
    
    for file_path in files_to_restore:
        # Chemin du fichier de développement (depuis le répertoire scripts)
        dev_path = f"../{file_path}"
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        
        if os.path.exists(dev_path):
            try:
                # Créer une sauvegarde
                backup_path = f"{prod_path}.backup_before_restore"
                if os.path.exists(prod_path):
                    shutil.copy2(prod_path, backup_path)
                    print(f"📦 Sauvegarde: {file_path}")
                
                # Créer le répertoire de destination si nécessaire
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                
                # Copier le fichier de développement
                shutil.copy2(dev_path, prod_path)
                print(f"✅ Restauré: {file_path}")
                restored_count += 1
                
            except Exception as e:
                print(f"❌ Erreur avec {file_path}: {e}")
        else:
            print(f"⚠️ Fichier de développement non trouvé: {dev_path}")
    
    return restored_count

def create_minimal_init_file():
    """Crée un fichier __init__.py minimal"""
    print("\n🔧 Création d'un fichier __init__.py minimal...")
    
    minimal_content = '''# -*- coding: utf-8 -*-
"""
Modèles de l'application competitions - Version minimale
"""

# Import des modèles principaux
try:
    from .users import User, Practitioner, Judge, Administrator
except ImportError:
    User = Practitioner = Judge = Administrator = None

try:
    from .competitions import Competition, CompetitionType, CompetitionCategory
except ImportError:
    Competition = CompetitionType = CompetitionCategory = None

try:
    from .categories import Category, CategoryGrade
except ImportError:
    Category = CategoryGrade = None

try:
    from .registrations import Registration, ParticipantCategoryRegistration
except ImportError:
    Registration = ParticipantCategoryRegistration = None

try:
    from .judging import JudgeCertification, CertificationRegistration
except ImportError:
    JudgeCertification = CertificationRegistration = None

try:
    from .scoring import Scoring, TechnicalScoring, StandaloneScoring, UnifiedScoring
except ImportError:
    Scoring = TechnicalScoring = StandaloneScoring = UnifiedScoring = None

try:
    from .match import Match
except ImportError:
    Match = None

try:
    from .schedule import Schedule, CategorySchedule, CompetitionSchedule
except ImportError:
    Schedule = CategorySchedule = CompetitionSchedule = None

try:
    from .club_requests import ClubRequest, AffiliationRequest
except ImportError:
    ClubRequest = AffiliationRequest = None

try:
    from .administrators import FederationAdministrator, ClubAdministrator
except ImportError:
    FederationAdministrator = ClubAdministrator = None

try:
    from .support import Support
except ImportError:
    Support = None

try:
    from .training import Training
except ImportError:
    Training = None

try:
    from .event_planning import EventPlanning
except ImportError:
    EventPlanning = None

try:
    from .coach_profile import CoachProfile
except ImportError:
    CoachProfile = None

try:
    from .event import Event
except ImportError:
    Event = None

try:
    from .combat import Combat
except ImportError:
    Combat = None

try:
    from .documents_old import DocumentCategory, Document, DocumentAccess, DocumentShare
except ImportError:
    DocumentCategory = Document = DocumentAccess = DocumentShare = None

try:
    from .qr_code import PractitionerQRCode, QRCodeScan
except ImportError:
    PractitionerQRCode = QRCodeScan = None

# Liste des modèles disponibles (seulement ceux qui existent)
__all__ = []

if User is not None:
    __all__.extend(['User', 'Practitioner', 'Judge', 'Administrator'])

if Competition is not None:
    __all__.extend(['Competition', 'CompetitionType', 'CompetitionCategory'])

if Category is not None:
    __all__.extend(['Category', 'CategoryGrade'])

if Registration is not None:
    __all__.extend(['Registration', 'ParticipantCategoryRegistration'])

if JudgeCertification is not None:
    __all__.extend(['JudgeCertification', 'CertificationRegistration'])

if Scoring is not None:
    __all__.extend(['Scoring', 'TechnicalScoring', 'StandaloneScoring', 'UnifiedScoring'])

if Match is not None:
    __all__.append('Match')

if Schedule is not None:
    __all__.extend(['Schedule', 'CategorySchedule', 'CompetitionSchedule'])

if ClubRequest is not None:
    __all__.extend(['ClubRequest', 'AffiliationRequest'])

if FederationAdministrator is not None:
    __all__.extend(['FederationAdministrator', 'ClubAdministrator'])

if Support is not None:
    __all__.append('Support')

if Training is not None:
    __all__.append('Training')

if EventPlanning is not None:
    __all__.append('EventPlanning')

if CoachProfile is not None:
    __all__.append('CoachProfile')

if Event is not None:
    __all__.append('Event')

if Combat is not None:
    __all__.append('Combat')

if DocumentCategory is not None:
    __all__.extend(['DocumentCategory', 'Document', 'DocumentAccess', 'DocumentShare'])

if PractitionerQRCode is not None:
    __all__.extend(['PractitionerQRCode', 'QRCodeScan'])
'''
    
    # Écrire le fichier minimal
    init_file = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(minimal_content)
    
    print("✅ Fichier __init__.py minimal créé")
    return True

def restart_gunicorn():
    """Redémarre gunicorn"""
    print("\n🔄 Redémarrage de gunicorn...")
    
    # Arrêter gunicorn
    os.system("pkill -f gunicorn")
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon"
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_cmd = "netstat -tlnp | grep :8002"
        check_result = os.system(check_cmd)
        
        if check_result == 0:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔍 ANALYSE ET RESTAURATION CIBLÉE")
    print("=" * 50)
    
    # Analyser les fichiers cassés
    broken_files = analyze_broken_files()
    
    if broken_files:
        print(f"\n📋 FICHIERS À RESTAURER ({len(broken_files)}):")
        for file in broken_files:
            print(f"   - {file}")
        
        # Essayer de restaurer depuis le développement
        restored_count = restore_critical_files()
        
        if restored_count == 0:
            print("\n⚠️ Impossible de restaurer depuis le développement")
            print("🔧 Création d'un fichier minimal...")
            create_minimal_init_file()
        
        # Redémarrer gunicorn
        restart_ok = restart_gunicorn()
        
        if restart_ok:
            print("\n✅ RESTAURATION RÉUSSIE!")
            print("🌐 Testez maintenant l'interface admin")
        else:
            print("\n⚠️ Fichiers restaurés mais problème avec gunicorn")
    else:
        print("\n✅ Aucun fichier cassé détecté")
        print("🔧 Redémarrage de gunicorn...")
        restart_ok = restart_gunicorn()
        
        if restart_ok:
            print("✅ Gunicorn redémarré avec succès")
        else:
            print("❌ Problème avec gunicorn") 
"""
Script pour analyser et restaurer les éléments cassés
"""

import os
import shutil
import subprocess
import time

def analyze_broken_files():
    """Analyse les fichiers cassés"""
    print("🔍 ANALYSE DES FICHIERS CASSÉS")
    print("=" * 40)
    
    # Fichiers critiques à vérifier
    critical_files = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
        'complete_translations.py',
        'smart_translate.py',
        'fix_languages.py',
        'check_languages.py',
    ]
    
    broken_files = []
    
    for file_path in critical_files:
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        if os.path.exists(prod_path):
            try:
                # Vérifier la syntaxe Python
                result = subprocess.run(['python3', '-m', 'py_compile', prod_path], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    broken_files.append(file_path)
                    print(f"❌ Fichier cassé: {file_path}")
                    print(f"   Erreur: {result.stderr.strip()}")
                else:
                    print(f"✅ Fichier OK: {file_path}")
            except Exception as e:
                broken_files.append(file_path)
                print(f"❌ Erreur de vérification: {file_path} - {e}")
        else:
            print(f"⚠️ Fichier manquant: {file_path}")
    
    return broken_files

def restore_critical_files():
    """Restaure les fichiers critiques depuis le développement"""
    print("\n🔄 RESTAURATION DES FICHIERS CRITIQUES")
    print("=" * 40)
    
    # Fichiers à restaurer depuis le développement
    files_to_restore = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
    ]
    
    restored_count = 0
    
    for file_path in files_to_restore:
        # Chemin du fichier de développement (depuis le répertoire scripts)
        dev_path = f"../{file_path}"
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        
        if os.path.exists(dev_path):
            try:
                # Créer une sauvegarde
                backup_path = f"{prod_path}.backup_before_restore"
                if os.path.exists(prod_path):
                    shutil.copy2(prod_path, backup_path)
                    print(f"📦 Sauvegarde: {file_path}")
                
                # Créer le répertoire de destination si nécessaire
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                
                # Copier le fichier de développement
                shutil.copy2(dev_path, prod_path)
                print(f"✅ Restauré: {file_path}")
                restored_count += 1
                
            except Exception as e:
                print(f"❌ Erreur avec {file_path}: {e}")
        else:
            print(f"⚠️ Fichier de développement non trouvé: {dev_path}")
    
    return restored_count

def create_minimal_init_file():
    """Crée un fichier __init__.py minimal"""
    print("\n🔧 Création d'un fichier __init__.py minimal...")
    
    minimal_content = '''# -*- coding: utf-8 -*-
"""
Modèles de l'application competitions - Version minimale
"""

# Import des modèles principaux
try:
    from .users import User, Practitioner, Judge, Administrator
except ImportError:
    User = Practitioner = Judge = Administrator = None

try:
    from .competitions import Competition, CompetitionType, CompetitionCategory
except ImportError:
    Competition = CompetitionType = CompetitionCategory = None

try:
    from .categories import Category, CategoryGrade
except ImportError:
    Category = CategoryGrade = None

try:
    from .registrations import Registration, ParticipantCategoryRegistration
except ImportError:
    Registration = ParticipantCategoryRegistration = None

try:
    from .judging import JudgeCertification, CertificationRegistration
except ImportError:
    JudgeCertification = CertificationRegistration = None

try:
    from .scoring import Scoring, TechnicalScoring, StandaloneScoring, UnifiedScoring
except ImportError:
    Scoring = TechnicalScoring = StandaloneScoring = UnifiedScoring = None

try:
    from .match import Match
except ImportError:
    Match = None

try:
    from .schedule import Schedule, CategorySchedule, CompetitionSchedule
except ImportError:
    Schedule = CategorySchedule = CompetitionSchedule = None

try:
    from .club_requests import ClubRequest, AffiliationRequest
except ImportError:
    ClubRequest = AffiliationRequest = None

try:
    from .administrators import FederationAdministrator, ClubAdministrator
except ImportError:
    FederationAdministrator = ClubAdministrator = None

try:
    from .support import Support
except ImportError:
    Support = None

try:
    from .training import Training
except ImportError:
    Training = None

try:
    from .event_planning import EventPlanning
except ImportError:
    EventPlanning = None

try:
    from .coach_profile import CoachProfile
except ImportError:
    CoachProfile = None

try:
    from .event import Event
except ImportError:
    Event = None

try:
    from .combat import Combat
except ImportError:
    Combat = None

try:
    from .documents_old import DocumentCategory, Document, DocumentAccess, DocumentShare
except ImportError:
    DocumentCategory = Document = DocumentAccess = DocumentShare = None

try:
    from .qr_code import PractitionerQRCode, QRCodeScan
except ImportError:
    PractitionerQRCode = QRCodeScan = None

# Liste des modèles disponibles (seulement ceux qui existent)
__all__ = []

if User is not None:
    __all__.extend(['User', 'Practitioner', 'Judge', 'Administrator'])

if Competition is not None:
    __all__.extend(['Competition', 'CompetitionType', 'CompetitionCategory'])

if Category is not None:
    __all__.extend(['Category', 'CategoryGrade'])

if Registration is not None:
    __all__.extend(['Registration', 'ParticipantCategoryRegistration'])

if JudgeCertification is not None:
    __all__.extend(['JudgeCertification', 'CertificationRegistration'])

if Scoring is not None:
    __all__.extend(['Scoring', 'TechnicalScoring', 'StandaloneScoring', 'UnifiedScoring'])

if Match is not None:
    __all__.append('Match')

if Schedule is not None:
    __all__.extend(['Schedule', 'CategorySchedule', 'CompetitionSchedule'])

if ClubRequest is not None:
    __all__.extend(['ClubRequest', 'AffiliationRequest'])

if FederationAdministrator is not None:
    __all__.extend(['FederationAdministrator', 'ClubAdministrator'])

if Support is not None:
    __all__.append('Support')

if Training is not None:
    __all__.append('Training')

if EventPlanning is not None:
    __all__.append('EventPlanning')

if CoachProfile is not None:
    __all__.append('CoachProfile')

if Event is not None:
    __all__.append('Event')

if Combat is not None:
    __all__.append('Combat')

if DocumentCategory is not None:
    __all__.extend(['DocumentCategory', 'Document', 'DocumentAccess', 'DocumentShare'])

if PractitionerQRCode is not None:
    __all__.extend(['PractitionerQRCode', 'QRCodeScan'])
'''
    
    # Écrire le fichier minimal
    init_file = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(minimal_content)
    
    print("✅ Fichier __init__.py minimal créé")
    return True

def restart_gunicorn():
    """Redémarre gunicorn"""
    print("\n🔄 Redémarrage de gunicorn...")
    
    # Arrêter gunicorn
    os.system("pkill -f gunicorn")
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon"
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_cmd = "netstat -tlnp | grep :8002"
        check_result = os.system(check_cmd)
        
        if check_result == 0:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔍 ANALYSE ET RESTAURATION CIBLÉE")
    print("=" * 50)
    
    # Analyser les fichiers cassés
    broken_files = analyze_broken_files()
    
    if broken_files:
        print(f"\n📋 FICHIERS À RESTAURER ({len(broken_files)}):")
        for file in broken_files:
            print(f"   - {file}")
        
        # Essayer de restaurer depuis le développement
        restored_count = restore_critical_files()
        
        if restored_count == 0:
            print("\n⚠️ Impossible de restaurer depuis le développement")
            print("🔧 Création d'un fichier minimal...")
            create_minimal_init_file()
        
        # Redémarrer gunicorn
        restart_ok = restart_gunicorn()
        
        if restart_ok:
            print("\n✅ RESTAURATION RÉUSSIE!")
            print("🌐 Testez maintenant l'interface admin")
        else:
            print("\n⚠️ Fichiers restaurés mais problème avec gunicorn")
    else:
        print("\n✅ Aucun fichier cassé détecté")
        print("🔧 Redémarrage de gunicorn...")
        restart_ok = restart_gunicorn()
        
        if restart_ok:
            print("✅ Gunicorn redémarré avec succès")
        else:
            print("❌ Problème avec gunicorn") 