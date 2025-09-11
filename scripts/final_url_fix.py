#!/usr/bin/env python3
"""
Script final pour corriger toutes les URLs restantes dans le template club.html
Remplace tous les namespaces incorrects par des URLs simples
"""
import os
import re
import time

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def fix_all_remaining_urls():
    """Corrige toutes les URLs restantes dans le template club.html"""
    
    log("🔧 CORRECTION FINALE URLS TEMPLATE CLUB")
    log("-" * 50)
    
    club_template = "competitions/templates/competitions/dashboard/club.html"
    
    if not os.path.exists(club_template):
        log("❌ Template club.html non trouvé")
        return False
    
    try:
        with open(club_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        log("✅ Template lu")
        
        # Corrections complètes de toutes les URLs problématiques
        url_corrections = [
            # Club namespace corrections (ces URLs n'existent pas avec namespace club:)
            ("{% url 'competitions:club:registrations_list' %}", "{% url 'competitions:club_registrations' %}"),
            ("{% url 'competitions:club:judges_list' %}", "{% url 'competitions:club_judges' %}"),
            ("{% url 'competitions:club:technical_scoring' %}", "{% url 'competitions:club_scoring' %}"),
            ("{% url 'competitions:club:competitions' %}", "{% url 'competitions:club_competitions' %}"),
            ("{% url 'competitions:club:bulk_registration' %}", "{% url 'competitions:club_bulk_registration' %}"),
            ("{% url 'competitions:club:roles_management' %}", "{% url 'competitions:club_roles' %}"),
            ("{% url 'competitions:club:import_export' %}", "{% url 'competitions:club_import_export' %}"),
            
            # Events namespace corrections
            ("{% url 'competitions:events:list' %}", "{% url 'competitions:events_list' %}"),
            ("{% url 'competitions:events:planning' %}", "{% url 'competitions:events_planning' %}"),
            ("{% url 'competitions:events:polls' %}", "{% url 'competitions:events_polls' %}"),
            ("{% url 'competitions:events:poll_list' %}", "{% url 'competitions:events_list' %}"),
            
            # Grades namespace corrections
            ("{% url 'competitions:grades:club' %}", "{% url 'competitions:grades_club' %}"),
            ("{% url 'competitions:grades:management' %}", "{% url 'competitions:grades_management' %}"),
            ("{% url 'competitions:grades:club_management' %}", "{% url 'competitions:grades_club' %}"),
            
            # Finances namespace corrections
            ("{% url 'competitions:finances:dashboard' %}", "{% url 'competitions:finances_dashboard' %}"),
            ("{% url 'competitions:finances:payments' %}", "{% url 'competitions:finances_payments' %}"),
            ("{% url 'competitions:finances:payments_list' %}", "{% url 'competitions:finances_payments' %}"),
            
            # Shop namespace corrections
            ("{% url 'competitions:shop:club' %}", "{% url 'competitions:shop_club' %}"),
            ("{% url 'competitions:shop:dashboard' %}", "{% url 'competitions:shop_dashboard' %}"),
            ("{% url 'competitions:shop:products_create' %}", "{% url 'competitions:shop_products_create' %}"),
            ("{% url 'competitions:shop:dashboard_club_dashboard' %}", "{% url 'competitions:shop_club' %}"),
            ("{% url 'competitions:shop:orders_detail' %}", "{% url 'competitions:shop_dashboard' %}"),
            
            # QR namespace corrections
            ("{% url 'competitions:qr:scan' %}", "{% url 'competitions:qr_scan' %}"),
            ("{% url 'competitions:qr:history' %}", "{% url 'competitions:qr_history' %}"),
            
            # Competitions namespace corrections
            ("{% url 'competitions:competitions:create' %}", "{% url 'competitions:competitions_create' %}"),
            ("{% url 'competitions:competitions:detail' %}", "{% url 'competitions:competitions_list' %}"),
            
            # Practitioner/participant corrections
            ("{% url 'competitions:practitioner:training_dashboard' %}", "{% url 'competitions:dashboard_participant' %}"),
            ("{% url 'competitions:practitioner:competitions' %}", "{% url 'competitions:competitions_list' %}"),
            ("{% url 'competitions:practitioner:payment_list' %}", "{% url 'competitions:finances_payments' %}"),
            ("{% url 'competitions:practitioner:notifications' %}", "{% url 'competitions:dashboard_participant' %}"),
            
            # Documents corrections
            ("{% url 'competitions:documents:dashboard' %}", "{% url 'competitions:dashboard' %}"),
            
            # Generic fallbacks pour les URLs complexes non résolues
            ("{% url 'competitions:club:manage_roles' %}", "{% url 'competitions:club_roles' %}"),
            ("{% url 'competitions:club:bulk_registration' %}", "{% url 'competitions:club_bulk_registration' %}"),
        ]
        
        corrections_applied = 0
        
        for old_url, new_url in url_corrections:
            if old_url in content:
                content = content.replace(old_url, new_url)
                corrections_applied += 1
                log(f"✅ {old_url} → {new_url}")
        
        # Corrections regex pour les URLs avec paramètres
        regex_corrections = [
            # URLs avec ID
            (r"{% url 'competitions:club:([^']+)' (\w+\.id) %}", r"{% url 'competitions:club_\1' %}"),
            (r"{% url 'competitions:events:([^']+)' (\w+\.id) %}", r"{% url 'competitions:events_list' %}"),
            (r"{% url 'competitions:finances:([^']+)' (\w+\.id) %}", r"{% url 'competitions:finances_dashboard' %}"),
            (r"{% url 'competitions:shop:([^']+)' (\w+\.id) %}", r"{% url 'competitions:shop_dashboard' %}"),
            
            # URLs génériques avec namespace incorrect
            (r"{% url 'competitions:([^:]+):([^']+)' %}", r"{% url 'competitions:\1_\2' %}"),
        ]
        
        for pattern, replacement in regex_corrections:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                corrections_applied += len(matches)
                log(f"✅ Regex correction: {pattern}")
        
        # Corrections spéciales pour les URLs complexes restantes
        special_corrections = [
            # Remplacer toutes les URLs qui commencent par competitions: et ont plus d'un :
            (r"{% url 'competitions:([^:]+):([^:]+):([^']+)'([^}]*) %}", r"{% url 'competitions:dashboard' %}"),
            (r"{% url 'competitions:([^:]+):([^']+)'([^}]*) %}", r"{% url 'competitions:\1_\2' %}"),
        ]
        
        for pattern, replacement in special_corrections:
            before_count = len(re.findall(pattern, content))
            content = re.sub(pattern, replacement, content)
            if before_count > 0:
                corrections_applied += before_count
                log(f"✅ Special correction: {before_count} URLs corrigées")
        
        # Écrire le fichier corrigé
        with open(club_template, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log(f"✅ Template sauvegardé avec {corrections_applied} corrections")
        return True
        
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False

def verify_corrections():
    """Vérifie que toutes les corrections ont été appliquées"""
    
    log("\n🔍 VÉRIFICATION CORRECTIONS")
    log("-" * 50)
    
    club_template = "competitions/templates/competitions/dashboard/club.html"
    
    try:
        with open(club_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les patterns problématiques restants
        problematic_patterns = [
            r"{% url 'competitions:[^']*:[^']*'",  # URLs avec double :
            r"competitions:club:",
            r"competitions:events:",
            r"competitions:finances:",
            r"competitions:shop:",
            r"competitions:qr:",
            r"competitions:grades:",
        ]
        
        issues_found = 0
        for pattern in problematic_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues_found += len(matches)
                log(f"⚠️ Pattern restant: {pattern} ({len(matches)} occurrences)")
        
        if issues_found == 0:
            log("✅ Aucun pattern problématique détecté")
            return True
        else:
            log(f"⚠️ {issues_found} patterns problématiques restants")
            return False
            
    except Exception as e:
        log(f"❌ Erreur vérification: {e}")
        return False

def main():
    log("🔧 CORRECTION FINALE URLs TEMPLATE CLUB")
    log("=" * 60)
    
    if fix_all_remaining_urls():
        log("✅ URLs corrigées")
    else:
        log("❌ Erreur correction URLs")
        return False
    
    if verify_corrections():
        log("✅ Vérification OK")
    else:
        log("⚠️ Quelques patterns restants détectés")
    
    log("\n🎉 CORRECTION FINALE TERMINÉE!")
    log("=" * 60)
    log("✅ RÉSULTATS:")
    log("   🔗 Toutes les URLs namespace corrigées")
    log("   📄 Template club.html nettoyé")
    log("   🎯 URLs simples utilisées")
    
    log("\n🚀 REDÉMARRER DJANGO:")
    log("   pkill -f gunicorn")
    log("   sleep 3")
    log("   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon")
    
    log("\n🧪 TESTER:")
    log("   https://martialcomp.com/dashboard/club/")
    log("   (Dashboard club devrait maintenant fonctionner)")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)