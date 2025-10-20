#!/usr/bin/env python3
"""
Rapport de situation complet du serveur de production MartialComp
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class ProductionStatusReport:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "server": "martialcomp.com",
            "status": "unknown",
            "checks": {}
        }
    
    def run_command(self, cmd, description=""):
        """Exécute une commande et retourne le résultat"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "description": description
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout",
                "description": description
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "description": description
            }
    
    def check_system_info(self):
        """Vérifie les informations système"""
        print("🔍 Vérification des informations système...")
        
        checks = {
            "hostname": self.run_command("hostname", "Nom d'hôte"),
            "uptime": self.run_command("uptime", "Temps de fonctionnement"),
            "memory": self.run_command("free -h", "Utilisation mémoire"),
            "disk": self.run_command("df -h", "Espace disque"),
            "load": self.run_command("cat /proc/loadavg", "Charge système"),
        }
        
        self.report["checks"]["system"] = checks
        return checks
    
    def check_services(self):
        """Vérifie le statut des services"""
        print("🔍 Vérification des services...")
        
        services = ["apache2", "nginx", "redis", "postgresql"]
        checks = {}
        
        for service in services:
            status_cmd = f"systemctl is-active {service}"
            status_result = self.run_command(status_cmd, f"Statut {service}")
            
            # Vérifier aussi si le service est enabled
            enabled_cmd = f"systemctl is-enabled {service}"
            enabled_result = self.run_command(enabled_cmd, f"Service {service} activé")
            
            checks[service] = {
                "status": status_result,
                "enabled": enabled_result
            }
        
        self.report["checks"]["services"] = checks
        return checks
    
    def check_database(self):
        """Vérifie la base de données"""
        print("🔍 Vérification de la base de données...")
        
        checks = {}
        
        # Test de connexion Django
        django_db_cmd = """python3 manage.py shell --settings=config.settings.production -c "
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'PostgreSQL version: {version}')
    cursor.execute('SELECT COUNT(*) FROM django_migrations')
    migrations = cursor.fetchone()[0]
    print(f'Migrations appliquées: {migrations}')
except Exception as e:
    print(f'Erreur: {e}')
" """
        
        checks["django_connection"] = self.run_command(django_db_cmd, "Connexion Django DB")
        
        # Test direct PostgreSQL
        psql_cmd = "psql -h localhost -U martialcomp_user -d martialcomp_db -c 'SELECT version();'"
        checks["psql_connection"] = self.run_command(psql_cmd, "Connexion PostgreSQL directe")
        
        # Vérifier les migrations
        migrations_cmd = "python3 manage.py showmigrations --settings=config.settings.production | grep -E '^\\[ \\]' | wc -l"
        checks["pending_migrations"] = self.run_command(migrations_cmd, "Migrations en attente")
        
        self.report["checks"]["database"] = checks
        return checks
    
    def check_redis(self):
        """Vérifie Redis"""
        print("🔍 Vérification de Redis...")
        
        checks = {}
        
        # Test de connexion Redis
        redis_cmd = "redis-cli ping"
        checks["connection"] = self.run_command(redis_cmd, "Connexion Redis")
        
        # Informations Redis
        redis_info_cmd = "redis-cli info server | head -10"
        checks["info"] = self.run_command(redis_info_cmd, "Informations Redis")
        
        # Test Django cache
        django_cache_cmd = """python3 manage.py shell --settings=config.settings.production -c "
from django.core.cache import cache
try:
    cache.set('test_key', 'test_value', 60)
    result = cache.get('test_key')
    print(f'Cache test: {result}')
    cache.delete('test_key')
except Exception as e:
    print(f'Erreur cache: {e}')
" """
        checks["django_cache"] = self.run_command(django_cache_cmd, "Cache Django")
        
        self.report["checks"]["redis"] = checks
        return checks
    
    def check_web_server(self):
        """Vérifie le serveur web"""
        print("🔍 Vérification du serveur web...")
        
        checks = {}
        
        # Test Apache
        apache_cmd = "curl -I http://localhost/ 2>/dev/null | head -1"
        checks["apache_local"] = self.run_command(apache_cmd, "Apache local")
        
        # Test Nginx
        nginx_cmd = "curl -I http://localhost:8080/ 2>/dev/null | head -1"
        checks["nginx_local"] = self.run_command(nginx_cmd, "Nginx local")
        
        # Test externe
        external_cmd = "curl -I https://martialcomp.com/ 2>/dev/null | head -1"
        checks["external_access"] = self.run_command(external_cmd, "Accès externe")
        
        # Vérifier les logs d'erreur récents
        apache_logs_cmd = "tail -5 /var/log/apache2/error.log 2>/dev/null"
        checks["apache_logs"] = self.run_command(apache_logs_cmd, "Logs Apache récents")
        
        nginx_logs_cmd = "tail -5 /var/log/nginx/error.log 2>/dev/null"
        checks["nginx_logs"] = self.run_command(nginx_logs_cmd, "Logs Nginx récents")
        
        self.report["checks"]["web_server"] = checks
        return checks
    
    def check_django_app(self):
        """Vérifie l'application Django"""
        print("🔍 Vérification de l'application Django...")
        
        checks = {}
        
        # Test de configuration Django
        django_check_cmd = "python3 manage.py check --settings=config.settings.production"
        checks["django_check"] = self.run_command(django_check_cmd, "Vérification Django")
        
        # Test des fichiers statiques
        static_cmd = "ls -la /var/www/vhosts/martialcomp.com/httpdocs/static/ | head -5"
        checks["static_files"] = self.run_command(static_cmd, "Fichiers statiques")
        
        # Test des permissions
        permissions_cmd = "ls -la /var/www/vhosts/martialcomp.com/httpdocs/ | head -5"
        checks["permissions"] = self.run_command(permissions_cmd, "Permissions fichiers")
        
        # Test de l'environnement virtuel
        venv_cmd = "which python3 && python3 --version"
        checks["python_env"] = self.run_command(venv_cmd, "Environnement Python")
        
        self.report["checks"]["django_app"] = checks
        return checks
    
    def check_security(self):
        """Vérifie la sécurité"""
        print("🔍 Vérification de la sécurité...")
        
        checks = {}
        
        # Vérifier les certificats SSL
        ssl_cmd = "openssl s_client -connect martialcomp.com:443 -servername martialcomp.com < /dev/null 2>/dev/null | openssl x509 -noout -dates"
        checks["ssl_certificate"] = self.run_command(ssl_cmd, "Certificat SSL")
        
        # Vérifier les ports ouverts
        ports_cmd = "netstat -tlnp | grep -E ':(80|443|22|5432|6379)'"
        checks["open_ports"] = self.run_command(ports_cmd, "Ports ouverts")
        
        # Vérifier les processus suspects
        processes_cmd = "ps aux | grep -E '(python|apache|nginx|redis|postgres)' | head -10"
        checks["processes"] = self.run_command(processes_cmd, "Processus système")
        
        self.report["checks"]["security"] = checks
        return checks
    
    def generate_summary(self):
        """Génère un résumé du rapport"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DU RAPPORT DE SITUATION")
        print("=" * 70)
        
        total_checks = 0
        successful_checks = 0
        
        for category, checks in self.report["checks"].items():
            print(f"\n📋 {category.upper()}:")
            for check_name, check_result in checks.items():
                if isinstance(check_result, dict):
                    if check_result.get("success"):
                        status = "✅"
                        successful_checks += 1
                    else:
                        status = "❌"
                    total_checks += 1
                    print(f"  {status} {check_name}: {check_result.get('description', '')}")
                elif isinstance(check_result, dict) and "status" in check_result:
                    # Pour les services avec status et enabled
                    status_result = check_result["status"]
                    enabled_result = check_result["enabled"]
                    if status_result.get("success") and enabled_result.get("success"):
                        print(f"  ✅ {check_name}: Actif et activé")
                        successful_checks += 1
                    else:
                        print(f"  ❌ {check_name}: Problème détecté")
                    total_checks += 1
        
        # Déterminer le statut global
        if successful_checks == total_checks:
            self.report["status"] = "healthy"
            status_emoji = "🟢"
            status_text = "SAIN"
        elif successful_checks > total_checks * 0.7:
            self.report["status"] = "warning"
            status_emoji = "🟡"
            status_text = "ATTENTION"
        else:
            self.report["status"] = "critical"
            status_emoji = "🔴"
            status_text = "CRITIQUE"
        
        print(f"\n{status_emoji} STATUT GLOBAL: {status_text}")
        print(f"📈 Score: {successful_checks}/{total_checks} ({successful_checks/total_checks*100:.1f}%)")
        
        return self.report
    
    def save_report(self, filename="production_status_report.json"):
        """Sauvegarde le rapport en JSON"""
        report_file = Path(filename)
        report_file.write_text(json.dumps(self.report, indent=2, ensure_ascii=False))
        print(f"\n💾 Rapport sauvegardé: {filename}")
    
    def run_full_report(self):
        """Exécute un rapport complet"""
        print("🚀 RAPPORT DE SITUATION COMPLET - MARTIALCOMP PRODUCTION")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Serveur: martialcomp.com")
        print("=" * 70)
        
        # Exécuter toutes les vérifications
        self.check_system_info()
        self.check_services()
        self.check_database()
        self.check_redis()
        self.check_web_server()
        self.check_django_app()
        self.check_security()
        
        # Générer le résumé
        self.generate_summary()
        
        # Sauvegarder le rapport
        self.save_report()
        
        return self.report

def main():
    """Fonction principale"""
    reporter = ProductionStatusReport()
    report = reporter.run_full_report()
    
    print("\n🔗 Actions recommandées:")
    if report["status"] == "critical":
        print("  🚨 Exécutez le script de correction: python3 fix_production_issues.py")
    elif report["status"] == "warning":
        print("  ⚠️  Surveillez les problèmes détectés et corrigez-les")
    else:
        print("  ✅ Votre serveur fonctionne correctement!")

if __name__ == "__main__":
    main()