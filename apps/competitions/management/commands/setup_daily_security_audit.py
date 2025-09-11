# -*- coding: utf-8 -*-
"""
Script pour configurer l'audit de sécurité quotidien automatique
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Configure l\'audit de sécurité quotidien automatique'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--crontab', 
            action='store_true', 
            help='Génère une entrée crontab pour l\'audit quotidien'
        )
        parser.add_argument(
            '--systemd', 
            action='store_true', 
            help='Génère des fichiers systemd pour l\'audit quotidien'
        )
    
    def handle(self, *args, **options):
        if options['crontab']:
            self.generate_crontab()
        elif options['systemd']:
            self.generate_systemd()
        else:
            self.show_instructions()
    
    def generate_crontab(self):
        """Génère une entrée crontab pour l'audit quotidien"""
        project_path = Path(settings.BASE_DIR)
        python_path = 'python3'  # ou le chemin vers votre environnement virtuel
        
        crontab_entry = f"""
# Audit de sécurité quotidien MartialComp - 2h du matin
0 2 * * * {python_path} {project_path}/manage.py check_platform_isolation --output={project_path}/logs/security_audit_$(date +\\%Y\\%m\\%d).json >> {project_path}/logs/security_audit.log 2>&1
"""
        
        self.stdout.write(self.style.SUCCESS('Entrée crontab générée:'))
        self.stdout.write(crontab_entry)
        
        self.stdout.write('\nPour l\'installer:')
        self.stdout.write('1. crontab -e')
        self.stdout.write('2. Coller l\'entrée ci-dessus')
        self.stdout.write('3. Sauvegarder et quitter')
        
        # Créer le répertoire des logs si nécessaire
        logs_dir = project_path / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\nRépertoire des logs créé: {logs_dir}')
    
    def generate_systemd(self):
        """Génère des fichiers systemd pour l'audit quotidien"""
        project_path = Path(settings.BASE_DIR)
        python_path = 'python3'  # ou le chemin vers votre environnement virtuel
        
        # Service file
        service_content = f"""[Unit]
Description=MartialComp Security Audit
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory={project_path}
ExecStart={python_path} {project_path}/manage.py check_platform_isolation --output={project_path}/logs/security_audit_%Y%m%d.json
StandardOutput=append:{project_path}/logs/security_audit.log
StandardError=append:{project_path}/logs/security_audit.log

[Install]
WantedBy=multi-user.target
"""
        
        # Timer file
        timer_content = """[Unit]
Description=Run MartialComp Security Audit daily
Requires=martialcomp-security-audit.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
"""
        
        self.stdout.write(self.style.SUCCESS('Fichiers systemd générés:'))
        
        self.stdout.write('\n--- /etc/systemd/system/martialcomp-security-audit.service ---')
        self.stdout.write(service_content)
        
        self.stdout.write('\n--- /etc/systemd/system/martialcomp-security-audit.timer ---')
        self.stdout.write(timer_content)
        
        self.stdout.write('\nPour l\'installer:')
        self.stdout.write('1. sudo cp les fichiers vers /etc/systemd/system/')
        self.stdout.write('2. sudo systemctl daemon-reload')
        self.stdout.write('3. sudo systemctl enable martialcomp-security-audit.timer')
        self.stdout.write('4. sudo systemctl start martialcomp-security-audit.timer')
        
        # Créer le répertoire des logs si nécessaire
        logs_dir = project_path / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'\nRépertoire des logs créé: {logs_dir}')
    
    def show_instructions(self):
        """Affiche les instructions générales"""
        self.stdout.write(self.style.SUCCESS('Configuration de l\'audit de sécurité quotidien'))
        self.stdout.write('='*60)
        
        self.stdout.write('\nOptions disponibles:')
        self.stdout.write('  --crontab   : Génère une entrée crontab')
        self.stdout.write('  --systemd   : Génère des fichiers systemd')
        
        self.stdout.write('\nExemples:')
        self.stdout.write('  python manage.py setup_daily_security_audit --crontab')
        self.stdout.write('  python manage.py setup_daily_security_audit --systemd')
        
        self.stdout.write('\nAudit manuel:')
        self.stdout.write('  python manage.py check_platform_isolation --output=rapport.json')
        
        self.stdout.write('\nSeuil de sécurité requis: 100%')
        self.stdout.write('Fréquence recommandée: Quotidienne à 2h du matin')