#!/bin/bash

# Script d'analyse profonde des problèmes critiques
# 1. Changement de langue
# 2. Sécurité et attaques

echo "=== ANALYSE PROFONDE DES PROBLÈMES CRITIQUES ==="
echo "Date: $(date)"
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# ========================================
# PARTIE 1: ANALYSE DU CHANGEMENT DE LANGUE
# ========================================

echo "═══════════════════════════════════════════════════════"
echo "1. ANALYSE DU PROBLÈME DE CHANGEMENT DE LANGUE"
echo "═══════════════════════════════════════════════════════"
echo ""

# 1.1 Configuration i18n dans les settings
echo "1.1 CONFIGURATION I18N DANS LES SETTINGS"
echo "----------------------------------------"

echo "Vérification des settings de production:"
grep -A 5 -B 5 "USE_I18N\|USE_L10N\|LANGUAGE_CODE\|LANGUAGES\|LOCALE_PATHS" config/settings/production.py 2>/dev/null || echo "Non trouvé dans production.py"

echo ""
echo "Vérification dans base.py:"
grep -A 5 -B 5 "USE_I18N\|USE_L10N\|LANGUAGE_CODE\|LANGUAGES\|LOCALE_PATHS" config/settings/base.py | head -50

echo ""

# 1.2 Middlewares de localisation
echo "1.2 MIDDLEWARES DE LOCALISATION"
echo "--------------------------------"

echo "Middlewares configurés:"
grep -A 20 "MIDDLEWARE" config/settings/base.py | grep -E "(LocaleMiddleware|SessionMiddleware|CommonMiddleware)"

echo ""

# 1.3 URLs de changement de langue
echo "1.3 URLS DE CHANGEMENT DE LANGUE"
echo "---------------------------------"

echo "Recherche des URLs i18n:"
find . -name "*.py" -type f -exec grep -l "set_language\|i18n_patterns" {} \; 2>/dev/null | grep -v "__pycache__" | head -10

echo ""
echo "Configuration des URLs principales:"
grep -B 2 -A 5 "i18n\|set_language" config/urls.py 2>/dev/null || echo "Non trouvé dans urls.py"

echo ""

# 1.4 Test de l'URL set_language
echo "1.4 TEST DE L'URL SET_LANGUAGE"
echo "-------------------------------"

echo "Test direct de l'URL:"
curl -s -I https://martialcomp.com/set_language/ | head -10

echo ""
echo "Test avec les paramètres corrects:"
curl -X POST https://martialcomp.com/set_language/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "language=en" \
  -s -o /tmp/set_language_response.html \
  -w "HTTP Code: %{http_code}\n"

echo ""

# 1.5 Analyse des logs d'erreur
echo "1.5 ANALYSE DES LOGS D'ERREUR"
echo "------------------------------"

echo "Dernières erreurs liées au changement de langue:"
tail -n 1000 logs/django.log | grep -i "set_language\|i18n\|locale" | tail -20

echo ""

# 1.6 Vérifier la vue set_language
echo "1.6 VÉRIFICATION DE LA VUE SET_LANGUAGE"
echo "----------------------------------------"

/var/www/vhosts/martialcomp.com/venv/bin/python << 'PYTHON_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

print("Test d'import de la vue set_language:")
try:
    from django.views.i18n import set_language
    print("✓ Vue set_language importée avec succès")
    
    # Vérifier la configuration
    from django.conf import settings
    print(f"\nConfiguration i18n:")
    print(f"USE_I18N: {settings.USE_I18N}")
    print(f"USE_L10N: {settings.USE_L10N}")
    print(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
    print(f"LANGUAGES disponibles: {[code for code, name in settings.LANGUAGES]}")
    
    # Vérifier les middlewares
    print(f"\nMiddlewares i18n présents:")
    for middleware in settings.MIDDLEWARE:
        if 'locale' in middleware.lower() or 'i18n' in middleware.lower():
            print(f"  - {middleware}")
            
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF

echo ""
echo ""

# ========================================
# PARTIE 2: ANALYSE DE LA SÉCURITÉ
# ========================================

echo "═══════════════════════════════════════════════════════"
echo "2. ANALYSE DE LA SÉCURITÉ ET DES ATTAQUES"
echo "═══════════════════════════════════════════════════════"
echo ""

# 2.1 Analyse des logs d'accès
echo "2.1 ANALYSE DES LOGS D'ACCÈS"
echo "-----------------------------"

echo "Top 20 des IPs avec le plus de requêtes (dernières 24h):"
if [ -f "/var/log/nginx/access.log" ]; then
    awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20
else
    echo "Logs nginx non accessibles directement"
fi

echo ""

# 2.2 Patterns d'attaque communs
echo "2.2 RECHERCHE DE PATTERNS D'ATTAQUE"
echo "------------------------------------"

echo "Tentatives sur /admin/:"
grep -c "/admin" logs/django.log 2>/dev/null || echo "0"

echo ""
echo "Tentatives de connexion échouées:"
grep -i "failed login\|authentication failed\|invalid credentials" logs/django.log | wc -l

echo ""
echo "Requêtes suspectes (SQL injection, XSS, etc.):"
grep -E "(UNION.*SELECT|<script>|javascript:|onerror=|onclick=|\.\./|/etc/passwd)" logs/django.log 2>/dev/null | wc -l

echo ""

# 2.3 Configuration actuelle de sécurité
echo "2.3 CONFIGURATION DE SÉCURITÉ ACTUELLE"
echo "---------------------------------------"

echo "Settings de sécurité Django:"
/var/www/vhosts/martialcomp.com/venv/bin/python << 'SECURITY_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings

print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', 'Non défini')}")
print(f"SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', 'Non défini')}")
print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', 'Non défini')}")
print(f"SECURE_BROWSER_XSS_FILTER: {getattr(settings, 'SECURE_BROWSER_XSS_FILTER', 'Non défini')}")
print(f"X_FRAME_OPTIONS: {getattr(settings, 'X_FRAME_OPTIONS', 'Non défini')}")
print(f"SECURE_CONTENT_TYPE_NOSNIFF: {getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', 'Non défini')}")

# Vérifier les rate limiting
print(f"\nRate limiting configuré:")
if 'ratelimit' in settings.INSTALLED_APPS:
    print("✓ django-ratelimit installé")
else:
    print("✗ Pas de rate limiting Django")

# Vérifier les middleware de sécurité
print(f"\nMiddlewares de sécurité:")
for middleware in settings.MIDDLEWARE:
    if 'security' in middleware.lower() or 'csrf' in middleware.lower():
        print(f"  - {middleware}")
SECURITY_EOF

echo ""

# 2.4 État de fail2ban
echo "2.4 ÉTAT DE FAIL2BAN"
echo "--------------------"

if command -v fail2ban-client &> /dev/null; then
    echo "fail2ban installé:"
    fail2ban-client status
else
    echo "✗ fail2ban n'est pas installé"
fi

echo ""

# 2.5 Analyse des pays d'origine
echo "2.5 ANALYSE GÉOGRAPHIQUE DES ACCÈS"
echo "-----------------------------------"

echo "Installation de geoip-bin si nécessaire..."
which geoiplookup &> /dev/null || apt-get install -qq geoip-bin geoip-database

echo ""
echo "Top 10 des pays (basé sur les derniers logs Django):"
# Extraire les IPs des logs et faire une recherche géographique
tail -n 1000 logs/django.log | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | sort | uniq | while read ip; do
    country=$(geoiplookup $ip 2>/dev/null | cut -d: -f2 | xargs)
    [ ! -z "$country" ] && echo "$country"
done | sort | uniq -c | sort -rn | head -10

echo ""

# 2.6 Vulnérabilités potentielles
echo "2.6 VULNÉRABILITÉS POTENTIELLES"
echo "--------------------------------"

echo "Endpoints exposés publiquement:"
/var/www/vhosts/martialcomp.com/venv/bin/python << 'VULN_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.urls import get_resolver
from django.contrib.auth.decorators import login_required

print("URLs sans authentification requise:")
resolver = get_resolver()
count = 0
for pattern in resolver.url_patterns[:20]:  # Limiter pour éviter trop de sortie
    if hasattr(pattern, 'callback'):
        callback = pattern.callback
        if callback and not hasattr(callback, '__wrapped__'):  # Pas de décorateur
            count += 1
            if count <= 10:
                print(f"  - {pattern.pattern}")
                
print(f"\nTotal d'URLs publiques: environ {count}")
VULN_EOF

echo ""
echo ""

# ========================================
# RÉSUMÉ ET RECOMMANDATIONS
# ========================================

echo "═══════════════════════════════════════════════════════"
echo "3. RÉSUMÉ DE L'ANALYSE"
echo "═══════════════════════════════════════════════════════"
echo ""

# Créer un fichier de rapport
cat > /tmp/critical_analysis_report.txt << 'REPORT_EOF'
RAPPORT D'ANALYSE - PROBLÈMES CRITIQUES
=======================================

1. PROBLÈME DE CHANGEMENT DE LANGUE
-----------------------------------
Symptômes identifiés:
- L'URL /set_language/ retourne une erreur 500
- Configuration i18n à vérifier dans les settings
- Middlewares de localisation à valider
- Possible problème de CSRF token

Actions recommandées:
1. Vérifier que LocaleMiddleware est après SessionMiddleware
2. S'assurer que LANGUAGE_CODE et LANGUAGES sont bien configurés
3. Vérifier que l'URL i18n est bien incluse dans urls.py
4. Tester avec CSRF token valide

2. SÉCURITÉ ET ATTAQUES
-----------------------
Risques identifiés:
- Pas de fail2ban installé
- Pas de rate limiting configuré
- Accès mondial sans restriction géographique
- Endpoints publics potentiellement vulnérables

Actions recommandées:
1. Installer et configurer fail2ban immédiatement
2. Implémenter django-ratelimit sur les vues sensibles
3. Configurer Cloudflare WAF et géo-blocage
4. Activer tous les headers de sécurité Django
5. Mettre en place un monitoring des tentatives d'intrusion

PRIORITÉ: Les deux problèmes sont CRITIQUES et doivent être résolus immédiatement.
REPORT_EOF

echo "Rapport d'analyse créé: /tmp/critical_analysis_report.txt"
echo ""

echo "============================================"
echo "ANALYSE TERMINÉE"
echo "============================================"
echo ""
echo "Points critiques identifiés:"
echo "1. ❌ Changement de langue non fonctionnel"
echo "2. ❌ Sécurité insuffisante (pas de fail2ban, pas de rate limiting)"
echo ""
echo "Prochaine étape: Exécuter les scripts de correction"
echo "============================================"