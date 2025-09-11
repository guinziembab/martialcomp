from django.core.management.base import BaseCommand
import os
import re
import json
from datetime import datetime
from pathlib import Path

class Command(BaseCommand):
    """Commande pour suivre le delta des traductions."""
    
    help = 'Suit les progrès de traduction avec système de delta'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--save-baseline',
            action='store_true',
            help='Sauvegarder l\'état actuel comme référence'
        )
        
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Comparer avec l\'état de référence'
        )
        
        parser.add_argument(
            '--file',
            type=str,
            help='Analyser un fichier spécifique'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('ðŸ“Š SUIVI DELTA DES TRADUCTIONS')
        )
        
        if options['save_baseline']:
            self.save_baseline()
        elif options['compare']:
            self.compare_with_baseline()
        elif options['file']:
            self.analyze_specific_file(options['file'])
        else:
            self.show_current_status()
    
    def analyze_translation_status(self):
        """Analyse l'état actuel des traductions."""
        
        template_dirs = [
            'competitions/templates',
            'grades/templates',
            'finances/templates',
            'shop/templates'
        ]
        
        total_stats = {
            'files_analyzed': 0,
            'french_text_total': 0,
            'translated_total': 0,
            'critical_files': [],
            'by_directory': {}
        }
        
        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            dir_stats = {
                'files': 0,
                'french_text': 0,
                'translated': 0,
                'coverage': 0,
                'files_detail': []
            }
            
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith('.html'):
                        file_path = os.path.join(root, file)
                        file_stats = self.analyze_file(file_path)
                        
                        if file_stats['french_count'] > 0:
                            dir_stats['files'] += 1
                            dir_stats['french_text'] += file_stats['french_count']
                            dir_stats['translated'] += file_stats['translated_count']
                            dir_stats['files_detail'].append(file_stats)
                            
                            total_stats['files_analyzed'] += 1
                            total_stats['french_text_total'] += file_stats['french_count']
                            total_stats['translated_total'] += file_stats['translated_count']
                            
                            # Identifier les fichiers critiques
                            if self.is_critical_file(file_path):
                                coverage = (file_stats['translated_count'] / file_stats['french_count'] * 100) if file_stats['french_count'] > 0 else 0
                                if coverage < 50:  # Moins de 50% traduit
                                    total_stats['critical_files'].append({
                                        'file': file_path,
                                        'coverage': coverage,
                                        'missing': file_stats['french_count'] - file_stats['translated_count']
                                    })
            
            if dir_stats['french_text'] > 0:
                dir_stats['coverage'] = (dir_stats['translated'] / dir_stats['french_text']) * 100
                total_stats['by_directory'][template_dir] = dir_stats
        
        # Calcul de la couverture globale
        total_stats['overall_coverage'] = (total_stats['translated_total'] / total_stats['french_text_total'] * 100) if total_stats['french_text_total'] > 0 else 0
        
        return total_stats
    
    def analyze_file(self, file_path):
        """Analyse un fichier spécifique."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return {'french_count': 0, 'translated_count': 0, 'file': file_path}
        
        # Patterns pour détecter le français
        french_patterns = [
            r'[>"\s]([A-ZÃ€ÃÃ‚ÃƒÃ„Ã…Ã†Ã‡ÃˆÃ‰ÃŠÃ‹ÃŒÃÃŽÃÃÃ‘Ã’Ã“Ã”Ã•Ã–][a-zA-ZÃ Ã¡Ã¢Ã£Ã¤Ã¥Ã¦çèéÃªÃ«Ã¬Ã­Ã®Ã¯Ã°Ã±Ã²Ã³Ã´ÃµÃ¶Ã¹ÃºÃ»Ã¼Ã½Ã¿\s]{8,})[<"\s]',
            r'placeholder="([^"]*[Ã Ã¡Ã¢Ã£Ã¤Ã¥Ã¦çèéÃªÃ«Ã¬Ã­Ã®Ã¯Ã°Ã±Ã²Ã³Ã´ÃµÃ¶Ã¹ÃºÃ»Ã¼Ã½Ã¿][^"]*)"',
            r'title="([^"]*[Ã Ã¡Ã¢Ã£Ã¤Ã¥Ã¦çèéÃªÃ«Ã¬Ã­Ã®Ã¯Ã°Ã±Ã²Ã³Ã´ÃµÃ¶Ã¹ÃºÃ»Ã¼Ã½Ã¿][^"]*)"',
        ]
        
        french_keywords = [
            'Tableau de bord', 'Gestion', 'Compétitions', 'Pratiquants', 'Clubs',
            'Ajouter', 'Modifier', 'Supprimer', 'Rechercher', 'Filtrer',
            'Connexion', 'Déconnexion', 'Fonctionnalités', 'Tarifs', 'Contact',
            'Accueil', 'Ã€ propos', 'Nom d\'utilisateur', 'Mot de passe'
        ]
        
        # Compter les textes français
        french_matches = set()
        
        for pattern in french_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            french_matches.update(matches)
        
        for keyword in french_keywords:
            if keyword in content and f'trans "{keyword}"' not in content:
                french_matches.add(keyword)
        
        # Compter les traductions
        trans_count = len(re.findall(r'\{%\s*trans\s+', content))
        translate_count = len(re.findall(r'\{%\s*translate\s+', content))
        
        return {
            'file': file_path,
            'french_count': len(french_matches),
            'translated_count': trans_count + translate_count,
            'french_samples': list(french_matches)[:5]
        }
    
    def is_critical_file(self, file_path):
        """Détermine si un fichier est critique."""
        critical_patterns = [
            'welcome.html',
            'dashboard',
            'login.html',
            'signup.html',
            'base.html'
        ]
        
        return any(pattern in file_path for pattern in critical_patterns)
    
    def save_baseline(self):
        """Sauvegarde l'état actuel comme référence."""
        stats = self.analyze_translation_status()
        
        baseline_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }
        
        baseline_file = 'translation_baseline.json'
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'ðŸ“ Référence sauvegardée: {baseline_file}')
        )
        self.stdout.write(
            f'   Couverture actuelle: {stats["overall_coverage"]:.1f}%'
        )
        self.stdout.write(
            f'   Fichiers critiques: {len(stats["critical_files"])}'
        )
    
    def compare_with_baseline(self):
        """Compare avec l'état de référence."""
        baseline_file = 'translation_baseline.json'
        
        if not os.path.exists(baseline_file):
            self.stdout.write(
                self.style.ERROR('âŒ Aucune référence trouvée. Utilisez --save-baseline d\'abord.')
            )
            return
        
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)
        
        current_stats = self.analyze_translation_status()
        baseline_stats = baseline_data['stats']
        
        # Calcul des deltas
        coverage_delta = current_stats['overall_coverage'] - baseline_stats['overall_coverage']
        translated_delta = current_stats['translated_total'] - baseline_stats['translated_total']
        
        self.stdout.write(
            self.style.SUCCESS(f'ðŸ“ˆ DELTA DEPUIS {baseline_data["timestamp"][:10]}')
        )
        self.stdout.write('=' * 50)
        
        if coverage_delta > 0:
            self.stdout.write(
                self.style.SUCCESS(f'âœ… Couverture: +{coverage_delta:.1f}% ({current_stats["overall_coverage"]:.1f}%)')
            )
        elif coverage_delta < 0:
            self.stdout.write(
                self.style.ERROR(f'âŒ Couverture: {coverage_delta:.1f}% ({current_stats["overall_coverage"]:.1f}%)')
            )
        else:
            self.stdout.write(f'âž– Couverture inchangée: {current_stats["overall_coverage"]:.1f}%')
        
        if translated_delta > 0:
            self.stdout.write(
                self.style.SUCCESS(f'âœ… Traductions ajoutées: +{translated_delta}')
            )
        elif translated_delta < 0:
            self.stdout.write(
                self.style.ERROR(f'âŒ Traductions perdues: {translated_delta}')
            )
        
        # Progrès par répertoire
        self.stdout.write('\nðŸ“‚ PROGRÃˆS PAR RÃ‰PERTOIRE:')
        for dir_name, current_dir_stats in current_stats['by_directory'].items():
            if dir_name in baseline_stats['by_directory']:
                baseline_dir_stats = baseline_stats['by_directory'][dir_name]
                dir_delta = current_dir_stats['coverage'] - baseline_dir_stats['coverage']
                
                if dir_delta > 0:
                    self.stdout.write(f'   âœ… {dir_name}: +{dir_delta:.1f}%')
                elif dir_delta < 0:
                    self.stdout.write(f'   âŒ {dir_name}: {dir_delta:.1f}%')
    
    def show_current_status(self):
        """Affiche l'état actuel."""
        stats = self.analyze_translation_status()
        
        self.stdout.write('ðŸ“Š Ã‰TAT ACTUEL DES TRADUCTIONS')
        self.stdout.write('=' * 40)
        self.stdout.write(f'Couverture globale: {stats["overall_coverage"]:.1f}%')
        self.stdout.write(f'Fichiers analysés: {stats["files_analyzed"]}')
        self.stdout.write(f'Textes français: {stats["french_text_total"]}')
        self.stdout.write(f'Textes traduits: {stats["translated_total"]}')
        
        if stats['critical_files']:
            self.stdout.write('\nðŸš¨ FICHIERS CRITIQUES Ã€ TRAITER:')
            for file_info in stats['critical_files'][:10]:
                self.stdout.write(
                    f'   â€¢ {os.path.basename(file_info["file"])}: '
                    f'{file_info["coverage"]:.1f}% '
                    f'(manque {file_info["missing"]} traductions)'
                )
        
        self.stdout.write('\nðŸ’¡ COMMANDES UTILES:')
        self.stdout.write('   python manage.py translation_delta --save-baseline')
        self.stdout.write('   python manage.py translation_delta --compare')
        self.stdout.write('   python manage.py translation_delta --file competitions/templates/competitions/welcome.html')
    
    def analyze_specific_file(self, file_path):
        """Analyse un fichier spécifique en détail."""
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'âŒ Fichier non trouvé: {file_path}')
            )
            return
        
        file_stats = self.analyze_file(file_path)
        coverage = (file_stats['translated_count'] / file_stats['french_count'] * 100) if file_stats['french_count'] > 0 else 0
        
        self.stdout.write(f'ðŸ“„ ANALYSE: {os.path.basename(file_path)}')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Couverture: {coverage:.1f}%')
        self.stdout.write(f'Textes français: {file_stats["french_count"]}')
        self.stdout.write(f'Traductions: {file_stats["translated_count"]}')
        self.stdout.write(f'Ã€ traduire: {file_stats["french_count"] - file_stats["translated_count"]}')
        
        if file_stats['french_samples']:
            self.stdout.write('\nðŸ“ EXEMPLES DE TEXTE FRANÃ‡AIS:')
            for sample in file_stats['french_samples']:
                if len(sample) > 60:
                    self.stdout.write(f'   â€¢ {sample[:60]}...')
                else:
                    self.stdout.write(f'   â€¢ {sample}')
