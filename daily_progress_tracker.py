#!/usr/bin/env python3
"""
Script de suivi quotidien de la progression vers 100% de conformité
"""
import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

class ProgressTracker:
    def __init__(self):
        self.start_date = datetime(2025, 10, 13)
        self.target_date = datetime(2025, 11, 3)
        self.current_conformity = 85
        
        # Tâches par phase avec poids de conformité
        self.tasks = {
            'PHASE 1 - CRITIQUE': {
                'websocket_infrastructure': {'status': 'pending', 'weight': 3, 'days': 2},
                'websocket_consumers': {'status': 'pending', 'weight': 3, 'days': 2},
                'fix_competitions_exam': {'status': 'pending', 'weight': 1, 'days': 1},
                'judge_interface_complete': {'status': 'pending', 'weight': 2, 'days': 2},
            },
            'PHASE 2 - TESTS': {
                'test_suite_complete': {'status': 'pending', 'weight': 3, 'days': 3},
                'api_documentation': {'status': 'pending', 'weight': 1, 'days': 2},
                'monitoring_setup': {'status': 'pending', 'weight': 1, 'days': 2},
            },
            'PHASE 3 - OPTIMISATION': {
                'performance_optimization': {'status': 'pending', 'weight': 1, 'days': 2},
                'security_audit': {'status': 'pending', 'weight': 2, 'days': 2},
                'backup_strategy': {'status': 'pending', 'weight': 1, 'days': 1},
            },
            'PHASE 4 - PRODUCTION': {
                'ci_cd_pipeline': {'status': 'pending', 'weight': 1, 'days': 1},
                'deployment_scripts': {'status': 'pending', 'weight': 1, 'days': 1},
                'load_testing': {'status': 'pending', 'weight': 1, 'days': 1},
                'production_checklist': {'status': 'pending', 'weight': 1, 'days': 1},
            }
        }
    
    def calculate_progress(self):
        """Calcule la progression globale"""
        total_weight = 0
        completed_weight = 0
        
        for phase, tasks in self.tasks.items():
            for task_name, task_info in tasks.items():
                total_weight += task_info['weight']
                if task_info['status'] == 'completed':
                    completed_weight += task_info['weight']
        
        # Progression depuis 85%
        max_progress = 100 - self.current_conformity  # 15%
        progress_made = (completed_weight / total_weight) * max_progress
        
        return self.current_conformity + progress_made
    
    def days_remaining(self):
        """Calcule les jours restants"""
        today = datetime.now()
        return (self.target_date - today).days
    
    def generate_report(self):
        """Génère le rapport de progression"""
        progress = self.calculate_progress()
        days_left = self.days_remaining()
        
        print("=" * 60)
        print(f"📊 RAPPORT DE PROGRESSION - {datetime.now().strftime('%d/%m/%Y')}")
        print("=" * 60)
        print(f"\n🎯 Conformité actuelle: {progress:.1f}%")
        print(f"📅 Jours restants: {days_left}")
        print(f"🏁 Date cible: {self.target_date.strftime('%d/%m/%Y')}")
        
        print("\n📋 STATUT PAR PHASE:\n")
        
        for phase, tasks in self.tasks.items():
            completed = sum(1 for t in tasks.values() if t['status'] == 'completed')
            total = len(tasks)
            phase_progress = (completed / total) * 100 if total > 0 else 0
            
            print(f"{phase}: {completed}/{total} ({phase_progress:.0f}%)")
            
            for task_name, task_info in tasks.items():
                status_icon = "✅" if task_info['status'] == 'completed' else "⏳" if task_info['status'] == 'in_progress' else "📌"
                print(f"  {status_icon} {task_name.replace('_', ' ').title()} ({task_info['days']}j)")
        
        # Recommandations
        print("\n💡 RECOMMANDATIONS:")
        if days_left < 7:
            print("⚠️  ATTENTION: Moins d'une semaine restante!")
            print("   - Focalisez sur les tâches critiques uniquement")
            print("   - Reportez les optimisations non-essentielles")
        elif progress < 90:
            print("🔄 Accélérer sur les tâches WebSocket et Tests")
            print("   - Considérez de l'aide externe si nécessaire")
        else:
            print("✅ Bonne progression! Continuez ainsi.")
        
        # Tâches du jour suggérées
        print("\n📅 TÂCHES SUGGÉRÉES AUJOURD'HUI:")
        pending_tasks = []
        for phase, tasks in self.tasks.items():
            for task_name, task_info in tasks.items():
                if task_info['status'] == 'pending':
                    pending_tasks.append((phase, task_name, task_info))
        
        if pending_tasks:
            # Prioriser par phase
            for i, (phase, task_name, task_info) in enumerate(pending_tasks[:3]):
                print(f"  {i+1}. {task_name.replace('_', ' ').title()} ({phase})")
        
        print("\n" + "=" * 60)
        
        # Sauvegarder le rapport
        self.save_report(progress, days_left)
    
    def save_report(self, progress, days_left):
        """Sauvegarde le rapport dans un fichier"""
        report_dir = "progress_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        filename = os.path.join(report_dir, f"progress_{datetime.now().strftime('%Y%m%d')}.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Conformité: {progress:.1f}%\n")
            f.write(f"Jours restants: {days_left}\n")
            f.write(f"Status: {'ON TRACK' if progress >= 90 else 'ATTENTION REQUISE'}\n")
    
    def update_task_status(self, task_name, new_status):
        """Met à jour le statut d'une tâche"""
        for phase, tasks in self.tasks.items():
            if task_name in tasks:
                tasks[task_name]['status'] = new_status
                print(f"✅ Tâche '{task_name}' mise à jour: {new_status}")
                return True
        print(f"❌ Tâche '{task_name}' non trouvée")
        return False

if __name__ == "__main__":
    tracker = ProgressTracker()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "update" and len(sys.argv) == 4:
            # Usage: python daily_progress_tracker.py update task_name status
            tracker.update_task_status(sys.argv[2], sys.argv[3])
    
    tracker.generate_report()