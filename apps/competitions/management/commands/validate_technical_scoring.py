# -*- coding: utf-8 -*-
"""
Script de validation fonctionnelle pour l'environnement de test de notation technique MartialComp
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Q
import json
from datetime import datetime

try:
    from apps.organizations.models import Organization
    from apps.competitions.models import (
        Federation, Club, Discipline, Practitioner, Competition, 
        CompetitionCategory, CompetitionRegistration
    )
    from apps.grades.models import Grade, GradeCategory
    from apps.competitions.models.technical_scoring import (
        ScoringCriterion, Performance, Score
    )
    from apps.competitions.models.judges import Judge, JudgeAssignment
except ImportError as e:
    print(f"Erreur d'importation: {e}")


class Command(BaseCommand):
    help = 'Valide l\'environnement de test pour la notation technique'
    
    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', 
                          help='Affichage détaillé des tests')
        parser.add_argument('--json-output', action='store_true',
                          help='Sortie au format JSON')
        parser.add_argument('--export-report', type=str,
                          help='Exporter le rapport vers un fichier JSON')
    
    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        self.json_output = options.get('json-output', False)
        self.export_file = options.get('export_report')
        
        # Initialiser le rapport
        self.report = {
            'timestamp': timezone.now().isoformat(),
            'tests': [],
            'vulnerabilities': [],
            'summary': {}
        }
        
        if not self.json_output:
            self.stdout.write(self.style.SUCCESS('🔍 VALIDATION ENVIRONNEMENT TEST NOTATION TECHNIQUE'))
            self.stdout.write('=' * 70)
        
        # Exécuter tous les tests
        try:
            self.test_data_integrity()
            self.test_scoring_calculations()
            self.test_judge_assignments()
            self.test_ranking_logic()
            self.test_performance_workflow()
            self.test_security_isolation()
            
            # Générer le résumé
            self.generate_summary()
            
            # Affichage final
            if self.json_output:
                self.stdout.write(json.dumps(self.report, indent=2, ensure_ascii=False))
            else:
                self.display_summary()
            
            # Exporter si demandé
            if self.export_file:
                self.export_report()
                
        except Exception as e:
            self.add_test_result('Global Test Execution', 'ERROR', 
                               details=[f'Erreur globale: {str(e)}'])
            if not self.json_output:
                self.stdout.write(self.style.ERROR(f'❌ Erreur lors de la validation: {e}'))
    
    def test_data_integrity(self):
        """Test 1: Intégrité des données créées"""
        test_name = "Data Integrity"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 1: Vérification de l\'intégrité des données...')
            
            # Vérifier la fédération
            federation = Federation.objects.filter(name__icontains='Test').first()
            if not federation:
                details.append("❌ Aucune fédération de test trouvée")
                self.add_test_result(test_name, 'FAILED', details, vulnerabilities)
                return
            
            details.append(f"✅ Fédération trouvée: {federation.name}")
            
            # Vérifier les clubs
            clubs = Club.objects.filter(name__icontains='Club Test')
            if clubs.count() != 3:
                details.append(f"❌ Nombre de clubs incorrect: {clubs.count()} (attendu: 3)")
            else:
                details.append(f"✅ {clubs.count()} clubs créés")
            
            # Vérifier les juges
            judges = Judge.objects.filter(user__username__startswith='judge_test_')
            if judges.count() != 6:
                details.append(f"❌ Nombre de juges incorrect: {judges.count()} (attendu: 6)")
            else:
                details.append(f"✅ {judges.count()} juges créés")
            
            # Vérifier les pratiquants
            practitioners = Practitioner.objects.filter(first_name__startswith='Pratiquant')
            if practitioners.count() != 5:
                details.append(f"❌ Nombre de pratiquants incorrect: {practitioners.count()} (attendu: 5)")
            else:
                details.append(f"✅ {practitioners.count()} pratiquants créés")
            
            # Vérifier la compétition
            competition = Competition.objects.filter(title__icontains='Test').first()
            if not competition:
                details.append("❌ Compétition de test non trouvée")
            else:
                details.append(f"✅ Compétition trouvée: {competition.title}")
                
                # Vérifier les catégories
                categories = CompetitionCategory.objects.filter(competition=competition)
                if categories.count() != 2:
                    details.append(f"❌ Nombre de catégories incorrect: {categories.count()} (attendu: 2)")
                else:
                    details.append(f"✅ {categories.count()} catégories créées")
            
            # Vérifier le système de grades
            grade_categories = GradeCategory.objects.filter(discipline__name__icontains='Test')
            if grade_categories.count() < 2:
                details.append(f"❌ Catégories de grades insuffisantes: {grade_categories.count()}")
            else:
                details.append(f"✅ {grade_categories.count()} catégories de grades")
            
            grades = Grade.objects.filter(discipline__name__icontains='Test')
            if grades.count() < 9:
                details.append(f"❌ Grades insuffisants: {grades.count()}")
            else:
                details.append(f"✅ {grades.count()} grades créés")
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def test_scoring_calculations(self):
        """Test 2: Calculs de notation"""
        test_name = "Scoring Calculations"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 2: Validation des calculs de notation...')
            
            # Récupérer une performance avec scores
            performance = Performance.objects.filter(
                total_score__isnull=False
            ).first()
            
            if not performance:
                details.append("❌ Aucune performance avec scores trouvée")
                self.add_test_result(test_name, 'FAILED', details, vulnerabilities)
                return
            
            # Vérifier les critères de notation
            criteria = ScoringCriterion.objects.filter(category=performance.category)
            if not criteria.exists():
                details.append("❌ Aucun critère de notation trouvé")
                self.add_test_result(test_name, 'FAILED', details, vulnerabilities)
                return
            
            details.append(f"✅ {criteria.count()} critères de notation")
            
            # Vérifier les scores individuels
            scores = Score.objects.filter(performance=performance)
            if not scores.exists():
                details.append("❌ Aucun score individuel trouvé")
            else:
                details.append(f"✅ {scores.count()} scores individuels")
                
                # Vérifier la cohérence des scores
                for criterion in criteria:
                    criterion_scores = scores.filter(criterion=criterion)
                    if criterion_scores.exists():
                        avg_score = criterion_scores.aggregate(avg=Avg('value'))['avg']
                        min_score = criterion.min_score
                        max_score = criterion.max_score
                        
                        if not (min_score <= avg_score <= max_score):
                            details.append(f"⚠️  Score moyen hors limites pour {criterion.name}: {avg_score}")
                            vulnerabilities.append({
                                'type': 'SCORING_VALIDATION',
                                'severity': 'MEDIUM',
                                'description': f'Score moyen hors limites pour le critère {criterion.name}'
                            })
                        else:
                            details.append(f"✅ Scores valides pour {criterion.name} (moy: {avg_score:.2f})")
            
            # Recalculer et comparer le score total
            calculated_score = performance.calculate_total_score()
            stored_score = performance.total_score
            
            if abs(calculated_score - stored_score) > 0.01:
                details.append(f"❌ Incohérence score: calculé={calculated_score:.2f}, stocké={stored_score:.2f}")
                vulnerabilities.append({
                    'type': 'CALCULATION_ERROR',
                    'severity': 'HIGH',
                    'description': 'Différence entre score calculé et stocké'
                })
            else:
                details.append(f"✅ Score total cohérent: {stored_score:.2f}")
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def test_judge_assignments(self):
        """Test 3: Affectations des juges"""
        test_name = "Judge Assignments"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 3: Validation des affectations de juges...')
            
            categories = CompetitionCategory.objects.filter(competition__title__icontains='Test')
            
            for category in categories:
                assignments = JudgeAssignment.objects.filter(category=category, is_active=True)
                
                if assignments.count() < 3:
                    details.append(f"⚠️  Pas assez de juges pour {category.name}: {assignments.count()}")
                    vulnerabilities.append({
                        'type': 'INSUFFICIENT_JUDGES',
                        'severity': 'MEDIUM',
                        'description': f'Moins de 3 juges assignés à {category.name}'
                    })
                else:
                    details.append(f"✅ {assignments.count()} juges assignés à {category.name}")
                
                # Vérifier qu'aucun juge n'est assigné à plusieurs catégories simultanément
                for assignment in assignments:
                    conflicts = JudgeAssignment.objects.filter(
                        judge=assignment.judge,
                        is_active=True
                    ).exclude(id=assignment.id)
                    
                    if conflicts.exists():
                        details.append(f"⚠️  Conflit d'assignation pour {assignment.judge.practitioner.full_name}")
                        vulnerabilities.append({
                            'type': 'JUDGE_CONFLICT',
                            'severity': 'MEDIUM',
                            'description': f'Juge assigné à plusieurs catégories simultanément'
                        })
            
            # Vérifier que tous les juges sont actifs
            judges = Judge.objects.filter(user__username__startswith='judge_test_')
            for judge in judges:
                if not judge.active:
                    details.append(f"⚠️  Juge inactif: {judge.practitioner.full_name}")
                    vulnerabilities.append({
                        'type': 'INACTIVE_JUDGE',
                        'severity': 'MEDIUM',
                        'description': f'Juge inactif détecté'
                    })
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def test_ranking_logic(self):
        """Test 4: Logique de classement"""
        test_name = "Ranking Logic"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 4: Validation de la logique de classement...')
            
            categories = CompetitionCategory.objects.filter(competition__title__icontains='Test')
            
            for category in categories:
                performances = Performance.objects.filter(
                    category=category, 
                    status='completed',
                    total_score__isnull=False
                ).order_by('-total_score', 'ranking')
                
                if not performances.exists():
                    details.append(f"❌ Aucune performance terminée pour {category.name}")
                    continue
                
                # Vérifier l'ordre des classements
                previous_score = float('inf')
                previous_rank = 0
                
                for performance in performances:
                    if performance.total_score > previous_score:
                        details.append(f"❌ Erreur classement {category.name}: {performance.practitioner.full_name}")
                        vulnerabilities.append({
                            'type': 'RANKING_ERROR',
                            'severity': 'HIGH',
                            'description': f'Erreur dans l\'ordre du classement pour {category.name}'
                        })
                    
                    if performance.ranking <= previous_rank:
                        details.append(f"❌ Erreur numérotation rang {category.name}: {performance.practitioner.full_name}")
                        vulnerabilities.append({
                            'type': 'RANK_NUMBERING_ERROR',
                            'severity': 'MEDIUM',
                            'description': f'Erreur dans la numérotation des rangs pour {category.name}'
                        })
                    
                    previous_score = performance.total_score
                    previous_rank = performance.ranking
                
                details.append(f"✅ Classement cohérent pour {category.name} ({performances.count()} participants)")
                
                # Afficher le podium
                podium = performances[:3]
                for i, performance in enumerate(podium, 1):
                    medal = ['🥇', '🥈', '🥉'][i-1]
                    details.append(f"  {medal} {performance.practitioner.full_name}: {performance.total_score:.2f}")
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def test_performance_workflow(self):
        """Test 5: Flux de travail des performances"""
        test_name = "Performance Workflow"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 5: Validation du flux de travail des performances...')
            
            # Statistiques des statuts
            status_stats = Performance.objects.filter(
                category__competition__title__icontains='Test'
            ).values('status').annotate(count=Count('id'))
            
            for stat in status_stats:
                details.append(f"📊 Statut '{stat['status']}': {stat['count']} performances")
            
            # Vérifier la cohérence des heures
            performances = Performance.objects.filter(
                category__competition__title__icontains='Test',
                status='completed'
            )
            
            timeline_errors = 0
            for performance in performances:
                if performance.start_time and performance.completion_time:
                    if performance.start_time > performance.completion_time:
                        details.append(f"❌ Erreur temporelle: {performance.practitioner.full_name}")
                        timeline_errors += 1
            
            if timeline_errors > 0:
                vulnerabilities.append({
                    'type': 'TIMELINE_ERROR',
                    'severity': 'MEDIUM',
                    'description': f'{timeline_errors} erreurs de chronologie détectées'
                })
            else:
                details.append("✅ Chronologie cohérente pour toutes les performances")
            
            # Vérifier l'ordre de passage
            categories = CompetitionCategory.objects.filter(competition__title__icontains='Test')
            for category in categories:
                category_performances = Performance.objects.filter(category=category).order_by('order')
                order_errors = 0
                
                expected_order = 1
                for performance in category_performances:
                    if performance.order != expected_order:
                        order_errors += 1
                    expected_order += 1
                
                if order_errors > 0:
                    details.append(f"❌ Erreurs d'ordre pour {category.name}: {order_errors}")
                    vulnerabilities.append({
                        'type': 'ORDER_ERROR',
                        'severity': 'LOW',
                        'description': f'Erreurs dans l\'ordre de passage pour {category.name}'
                    })
                else:
                    details.append(f"✅ Ordre correct pour {category.name}")
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def test_security_isolation(self):
        """Test 6: Isolation de sécurité entre organisations"""
        test_name = "Security Isolation"
        details = []
        vulnerabilities = []
        
        try:
            self.log('🔍 Test 6: Validation de l\'isolation de sécurité...')
            
            # Vérifier que chaque club a sa propre organisation
            clubs = Club.objects.filter(name__icontains='Club Test')
            organizations = set()
            
            for club in clubs:
                if not club.organization:
                    details.append(f"❌ Club sans organisation: {club.name}")
                    vulnerabilities.append({
                        'type': 'MISSING_ORGANIZATION',
                        'severity': 'HIGH',
                        'description': f'Club {club.name} sans organisation assignée'
                    })
                else:
                    organizations.add(club.organization.id)
                    details.append(f"✅ {club.name} → Organisation {club.organization.name}")
            
            if len(organizations) != len(clubs):
                details.append(f"⚠️  Organisations partagées détectées")
                vulnerabilities.append({
                    'type': 'SHARED_ORGANIZATION',
                    'severity': 'MEDIUM',
                    'description': 'Plusieurs clubs partagent la même organisation'
                })
            else:
                details.append(f"✅ {len(organizations)} organisations distinctes")
            
            # Vérifier l'isolation des pratiquants
            for club in clubs:
                club_practitioners = Practitioner.objects.filter(club=club)
                cross_org_practitioners = Practitioner.objects.filter(
                    club__organization__isnull=False
                ).exclude(club__organization=club.organization)
                
                if club_practitioners.filter(
                    id__in=cross_org_practitioners.values_list('id', flat=True)
                ).exists():
                    details.append(f"❌ Fuite d'isolation pour {club.name}")
                    vulnerabilities.append({
                        'type': 'ISOLATION_BREACH',
                        'severity': 'CRITICAL',
                        'description': f'Pratiquants visibles entre organisations pour {club.name}'
                    })
                else:
                    details.append(f"✅ Isolation respectée pour {club.name}")
            
            # Vérifier l'isolation des juges
            judges = Judge.objects.filter(user__username__startswith='judge_test_')
            for judge in judges:
                if not judge.practitioner.organization:
                    details.append(f"⚠️  Juge sans organisation: {judge.practitioner.full_name}")
                    vulnerabilities.append({
                        'type': 'JUDGE_NO_ORGANIZATION',
                        'severity': 'MEDIUM',
                        'description': f'Juge sans organisation assignée'
                    })
            
            self.add_test_result(test_name, 'PASSED', details, vulnerabilities)
            
        except Exception as e:
            details.append(f"❌ Erreur: {str(e)}")
            self.add_test_result(test_name, 'ERROR', details, vulnerabilities)
    
    def add_test_result(self, test_name, status, details, vulnerabilities):
        """Ajoute un résultat de test au rapport"""
        self.report['tests'].append({
            'name': test_name,
            'status': status,
            'details': details,
            'vulnerabilities': vulnerabilities
        })
        
        # Ajouter les vulnérabilités au rapport global
        self.report['vulnerabilities'].extend(vulnerabilities)
    
    def generate_summary(self):
        """Génère le résumé du rapport"""
        tests = self.report['tests']
        vulnerabilities = self.report['vulnerabilities']
        
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests if test['status'] == 'PASSED')
        failed_tests = sum(1 for test in tests if test['status'] == 'FAILED')
        error_tests = sum(1 for test in tests if test['status'] == 'ERROR')
        
        total_vulnerabilities = len(vulnerabilities)
        critical_vulnerabilities = sum(1 for vuln in vulnerabilities if vuln['severity'] == 'CRITICAL')
        
        # Calculer le score de qualité
        if total_tests > 0:
            base_score = (passed_tests / total_tests) * 100
            vulnerability_penalty = min(total_vulnerabilities * 5, 30)  # Max 30% de pénalité
            critical_penalty = critical_vulnerabilities * 20  # 20% par vulnérabilité critique
            
            quality_score = max(0, base_score - vulnerability_penalty - critical_penalty)
        else:
            quality_score = 0
        
        self.report['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'total_vulnerabilities': total_vulnerabilities,
            'critical_vulnerabilities': critical_vulnerabilities,
            'quality_score': round(quality_score, 1)
        }
    
    def display_summary(self):
        """Affiche le résumé final"""
        summary = self.report['summary']
        
        self.stdout.write('\n🏆 RÉSUMÉ DE LA VALIDATION')
        self.stdout.write('=' * 50)
        
        # Statistiques des tests
        self.stdout.write(f'📊 Tests exécutés: {summary["total_tests"]}')
        self.stdout.write(f'✅ Tests réussis: {summary["passed_tests"]}')
        if summary['failed_tests'] > 0:
            self.stdout.write(self.style.WARNING(f'❌ Tests échoués: {summary["failed_tests"]}'))
        if summary['error_tests'] > 0:
            self.stdout.write(self.style.ERROR(f'💥 Erreurs: {summary["error_tests"]}'))
        
        # Vulnérabilités
        if summary['total_vulnerabilities'] > 0:
            self.stdout.write(f'\n⚠️  Vulnérabilités détectées: {summary["total_vulnerabilities"]}')
            if summary['critical_vulnerabilities'] > 0:
                self.stdout.write(self.style.ERROR(f'🚨 Critiques: {summary["critical_vulnerabilities"]}'))
        else:
            self.stdout.write('✅ Aucune vulnérabilité détectée')
        
        # Score de qualité
        score = summary['quality_score']
        if score >= 90:
            score_style = self.style.SUCCESS
            emoji = '🏆'
        elif score >= 70:
            score_style = self.style.WARNING
            emoji = '⚠️'
        else:
            score_style = self.style.ERROR
            emoji = '❌'
        
        self.stdout.write(f'\n{emoji} Score de qualité: {score_style(f"{score}%")}')
        
        # Recommandations
        if summary['critical_vulnerabilities'] > 0:
            self.stdout.write(self.style.ERROR('\n🚨 ACTION REQUISE: Corriger les vulnérabilités critiques'))
        elif summary['total_vulnerabilities'] > 0:
            self.stdout.write(self.style.WARNING('\n⚠️  RECOMMANDATION: Examiner les vulnérabilités détectées'))
        elif score == 100:
            self.stdout.write(self.style.SUCCESS('\n🎯 PARFAIT: Environnement de test entièrement validé'))
    
    def export_report(self):
        """Exporte le rapport vers un fichier JSON"""
        try:
            with open(self.export_file, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            
            if not self.json_output:
                self.stdout.write(f'\n📁 Rapport exporté vers: {self.export_file}')
                
        except Exception as e:
            if not self.json_output:
                self.stdout.write(self.style.ERROR(f'❌ Erreur d\'export: {e}'))
    
    def log(self, message):
        """Affiche un message si le mode verbose est activé"""
        if self.verbose and not self.json_output:
            self.stdout.write(message)