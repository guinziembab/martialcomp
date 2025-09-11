#!/usr/bin/env python3
"""
Script pour restaurer le fichier __init__.py original des modèles
"""

import os
import shutil

def restore_models_init():
    """Restaure le fichier __init__.py original des modèles"""
    print("🔧 RESTAURATION DU FICHIER __INIT__.PY DES MODÈLES")
    print("=" * 50)
    
    # Créer une sauvegarde du fichier actuel
    init_path = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py"
    backup_path = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py.backup_minimal"
    
    if os.path.exists(init_path):
        shutil.copy2(init_path, backup_path)
        print("📦 Sauvegarde du fichier minimal créée")
    
    # Contenu original du fichier __init__.py
    original_content = '''# -*- coding: utf-8 -*-
"""
Modèles de l'application competitions
"""

# Import des modèles principaux
from .users import User, Practitioner, Judge, Administrator
from .competitions import Competition, CompetitionType, CompetitionCategory
from .categories import Category, CategoryGrade
from .registrations import Registration, ParticipantCategoryRegistration
from .judging import JudgeCertification, CertificationRegistration
from .scoring import Scoring, TechnicalScoring, StandaloneScoring, UnifiedScoring
from .match import Match
from .schedule import Schedule, CategorySchedule, CompetitionSchedule
from .club_requests import ClubRequest, AffiliationRequest
from .administrators import FederationAdministrator, ClubAdministrator
from .support import Support
from .training import Training
from .event_planning import EventPlanning
from .coach_profile import CoachProfile
from .event import Event
from .combat import Combat
from .documents_old import DocumentCategory, Document, DocumentAccess, DocumentShare
from .qr_code import PractitionerQRCode, QRCodeScan

# Liste des modèles disponibles
__all__ = [
    'User', 'Practitioner', 'Judge', 'Administrator',
    'Competition', 'CompetitionType', 'CompetitionCategory',
    'Category', 'CategoryGrade',
    'Registration', 'ParticipantCategoryRegistration',
    'JudgeCertification', 'CertificationRegistration',
    'Scoring', 'TechnicalScoring', 'StandaloneScoring', 'UnifiedScoring',
    'Match',
    'Schedule', 'CategorySchedule', 'CompetitionSchedule',
    'ClubRequest', 'AffiliationRequest',
    'FederationAdministrator', 'ClubAdministrator',
    'Support',
    'Training',
    'EventPlanning',
    'CoachProfile',
    'Event',
    'Combat',
    'DocumentCategory', 'Document', 'DocumentAccess', 'DocumentShare',
    'PractitionerQRCode', 'QRCodeScan',
]
'''
    
    # Écrire le fichier original
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    print("✅ Fichier __init__.py restauré avec les imports complets")
    return True

def test_django_import():
    """Teste l'import Django après restauration"""
    print("\n🔍 TEST DE L'IMPORT DJANGO")
    print("=" * 30)
    
    import subprocess
    
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/python -c 'import config.wsgi; print(\"✅ Application Django importée avec succès\")'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Application Django OK")
            print(result.stdout)
            return True
        else:
            print("❌ Erreur d'import Django:")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - import Django")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def restart_gunicorn():
    """Redémarre gunicorn après restauration"""
    print("\n🔄 REDÉMARRAGE DE GUNICORN")
    print("=" * 30)
    
    import subprocess
    import time
    
    # Arrêter gunicorn
    subprocess.run(["pkill", "-f", "gunicorn"])
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application --daemon"
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        
        if ":8002" in check_result.stdout:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔧 RESTAURATION DES MODÈLES")
    print("=" * 50)
    
    # Restaurer le fichier __init__.py
    restore_ok = restore_models_init()
    
    if restore_ok:
        # Tester l'import Django
        django_ok = test_django_import()
        
        if django_ok:
            # Redémarrer gunicorn
            restart_ok = restart_gunicorn()
            
            if restart_ok:
                print("\n✅ RESTAURATION RÉUSSIE!")
                print("🌐 Gunicorn fonctionne sur le port 8002")
                print("🌐 Testez maintenant l'interface admin")
            else:
                print("\n⚠️ Modèles restaurés mais problème avec gunicorn")
        else:
            print("\n❌ Problème avec l'import Django après restauration")
    else:
        print("\n❌ ÉCHEC DE LA RESTAURATION") 
"""
Script pour restaurer le fichier __init__.py original des modèles
"""

import os
import shutil

def restore_models_init():
    """Restaure le fichier __init__.py original des modèles"""
    print("🔧 RESTAURATION DU FICHIER __INIT__.PY DES MODÈLES")
    print("=" * 50)
    
    # Créer une sauvegarde du fichier actuel
    init_path = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py"
    backup_path = "/var/www/vhosts/martialcomp.com/httpdocs/competitions/models/__init__.py.backup_minimal"
    
    if os.path.exists(init_path):
        shutil.copy2(init_path, backup_path)
        print("📦 Sauvegarde du fichier minimal créée")
    
    # Contenu original du fichier __init__.py
    original_content = '''# -*- coding: utf-8 -*-
"""
Modèles de l'application competitions
"""

# Import des modèles principaux
from .users import User, Practitioner, Judge, Administrator
from .competitions import Competition, CompetitionType, CompetitionCategory
from .categories import Category, CategoryGrade
from .registrations import Registration, ParticipantCategoryRegistration
from .judging import JudgeCertification, CertificationRegistration
from .scoring import Scoring, TechnicalScoring, StandaloneScoring, UnifiedScoring
from .match import Match
from .schedule import Schedule, CategorySchedule, CompetitionSchedule
from .club_requests import ClubRequest, AffiliationRequest
from .administrators import FederationAdministrator, ClubAdministrator
from .support import Support
from .training import Training
from .event_planning import EventPlanning
from .coach_profile import CoachProfile
from .event import Event
from .combat import Combat
from .documents_old import DocumentCategory, Document, DocumentAccess, DocumentShare
from .qr_code import PractitionerQRCode, QRCodeScan

# Liste des modèles disponibles
__all__ = [
    'User', 'Practitioner', 'Judge', 'Administrator',
    'Competition', 'CompetitionType', 'CompetitionCategory',
    'Category', 'CategoryGrade',
    'Registration', 'ParticipantCategoryRegistration',
    'JudgeCertification', 'CertificationRegistration',
    'Scoring', 'TechnicalScoring', 'StandaloneScoring', 'UnifiedScoring',
    'Match',
    'Schedule', 'CategorySchedule', 'CompetitionSchedule',
    'ClubRequest', 'AffiliationRequest',
    'FederationAdministrator', 'ClubAdministrator',
    'Support',
    'Training',
    'EventPlanning',
    'CoachProfile',
    'Event',
    'Combat',
    'DocumentCategory', 'Document', 'DocumentAccess', 'DocumentShare',
    'PractitionerQRCode', 'QRCodeScan',
]
'''
    
    # Écrire le fichier original
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    print("✅ Fichier __init__.py restauré avec les imports complets")
    return True

def test_django_import():
    """Teste l'import Django après restauration"""
    print("\n🔍 TEST DE L'IMPORT DJANGO")
    print("=" * 30)
    
    import subprocess
    
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/python -c 'import config.wsgi; print(\"✅ Application Django importée avec succès\")'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Application Django OK")
            print(result.stdout)
            return True
        else:
            print("❌ Erreur d'import Django:")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - import Django")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def restart_gunicorn():
    """Redémarre gunicorn après restauration"""
    print("\n🔄 REDÉMARRAGE DE GUNICORN")
    print("=" * 30)
    
    import subprocess
    import time
    
    # Arrêter gunicorn
    subprocess.run(["pkill", "-f", "gunicorn"])
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application --daemon"
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        
        if ":8002" in check_result.stdout:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔧 RESTAURATION DES MODÈLES")
    print("=" * 50)
    
    # Restaurer le fichier __init__.py
    restore_ok = restore_models_init()
    
    if restore_ok:
        # Tester l'import Django
        django_ok = test_django_import()
        
        if django_ok:
            # Redémarrer gunicorn
            restart_ok = restart_gunicorn()
            
            if restart_ok:
                print("\n✅ RESTAURATION RÉUSSIE!")
                print("🌐 Gunicorn fonctionne sur le port 8002")
                print("🌐 Testez maintenant l'interface admin")
            else:
                print("\n⚠️ Modèles restaurés mais problème avec gunicorn")
        else:
            print("\n❌ Problème avec l'import Django après restauration")
    else:
        print("\n❌ ÉCHEC DE LA RESTAURATION") 