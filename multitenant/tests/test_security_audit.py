"""
Tests unitaires pour le système d'audit de sécurité multi-tenant.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime

from multitenant.models import Tenant, Domain
from multitenant.security import SecurityAuditor, TenantSecurityMonitor, run_security_audit
from multitenant.middleware import TenantMiddleware


User = get_user_model()


class SecurityAuditorTestCase(TransactionTestCase):
    """Tests pour la classe SecurityAuditor."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        # Créer des tenants de test
        self.tenant1 = Tenant.objects.create(
            name="Test Tenant 1",
            slug="test-tenant-1",
            schema_name="test_tenant_1"
        )
        self.tenant2 = Tenant.objects.create(
            name="Test Tenant 2",
            slug="test-tenant-2",
            schema_name="test_tenant_2"
        )
        
        # Créer des domaines
        self.domain1 = Domain.objects.create(
            domain="tenant1.example.com",
            tenant=self.tenant1,
            is_primary=True
        )
        self.domain2 = Domain.objects.create(
            domain="tenant2.example.com",
            tenant=self.tenant2,
            is_primary=True
        )
        
        # Créer l'auditeur
        self.auditor = SecurityAuditor()
    
    def test_audit_cross_schema_access(self):
        """Test de l'audit d'accès entre schémas."""
        with patch('multitenant.security.connection') as mock_conn:
            # Simuler une connexion sans violation
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.execute.return_value = None
            
            result = self.auditor.audit_cross_schema_access()
            
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(len(result['violations']), 0)
    
    def test_audit_middleware_isolation(self):
        """Test de l'audit d'isolation du middleware."""
        with patch('multitenant.security.get_current_tenant') as mock_get_tenant:
            mock_get_tenant.return_value = self.tenant1
            
            result = self.auditor.audit_middleware_isolation()
            
            self.assertEqual(result['status'], 'passed')
            self.assertIn('checks', result)
    
    def test_audit_cache_isolation(self):
        """Test de l'audit d'isolation du cache."""
        # Définir des clés de cache de test
        cache.set('tenant:1:key', 'value1')
        cache.set('tenant:2:key', 'value2')
        cache.set('global:key', 'global_value')
        
        result = self.auditor.audit_cache_isolation()
        
        # Nettoyer le cache
        cache.clear()
        
        self.assertIn('status', result)
        self.assertIn('checks', result)
    
    def test_audit_file_access(self):
        """Test de l'audit d'accès aux fichiers."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('os.listdir') as mock_listdir:
                mock_listdir.return_value = ['file1.pdf', 'file2.jpg']
                
                result = self.auditor.audit_file_access()
                
                self.assertIn('status', result)
                self.assertIn('checks', result)
    
    def test_audit_security_headers(self):
        """Test de l'audit des en-têtes de sécurité."""
        with patch('requests.get') as mock_get:
            # Simuler une réponse avec des en-têtes de sécurité
            mock_response = MagicMock()
            mock_response.headers = {
                'Strict-Transport-Security': 'max-age=31536000',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'Content-Security-Policy': "default-src 'self'",
                'X-XSS-Protection': '1; mode=block'
            }
            mock_get.return_value = mock_response
            
            result = self.auditor.audit_security_headers()
            
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(len(result['violations']), 0)
    
    def test_audit_tenant_permissions(self):
        """Test de l'audit des permissions des tenants."""
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        with patch('multitenant.security.get_user_model') as mock_user_model:
            mock_user_model.return_value.objects.all.return_value = [user]
            
            result = self.auditor.audit_tenant_permissions()
            
            self.assertIn('status', result)
            self.assertIn('checks', result)


class TenantSecurityMonitorTestCase(TestCase):
    """Tests pour la classe TenantSecurityMonitor."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.tenant = Tenant.objects.create(
            name="Monitor Test Tenant",
            slug="monitor-test",
            schema_name="monitor_test"
        )
        self.monitor = TenantSecurityMonitor(self.tenant)
    
    def test_monitor_tenant_activity(self):
        """Test du monitoring d'activité d'un tenant."""
        result = self.monitor.monitor_tenant_activity()
        
        self.assertIn('tenant_id', result)
        self.assertIn('timestamp', result)
        self.assertIn('metrics', result)
    
    def test_check_suspicious_activity(self):
        """Test de la détection d'activité suspecte."""
        result = self.monitor.check_suspicious_activity()
        
        self.assertIn('status', result)
        self.assertIn('suspicious_activities', result)
    
    def test_analyze_access_patterns(self):
        """Test de l'analyse des patterns d'accès."""
        result = self.monitor.analyze_access_patterns()
        
        self.assertIn('access_patterns', result)
        self.assertIn('anomalies', result)


class SecurityAuditIntegrationTestCase(TransactionTestCase):
    """Tests d'intégration pour le système d'audit de sécurité."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.tenant = Tenant.objects.create(
            name="Integration Test Tenant",
            slug="integration-test",
            schema_name="integration_test"
        )
        
        # Créer un répertoire temporaire pour les rapports
        self.test_report_path = '/tmp/test_security_reports'
        os.makedirs(self.test_report_path, exist_ok=True)
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Supprimer les fichiers de rapport de test
        import shutil
        if os.path.exists(self.test_report_path):
            shutil.rmtree(self.test_report_path)
    
    @patch('multitenant.security.TENANT_SECURITY_REPORT_PATH', '/tmp/test_security_reports')
    def test_run_security_audit_single_tenant(self):
        """Test de l'exécution d'un audit pour un seul tenant."""
        result = run_security_audit(self.tenant)
        
        self.assertIn('summary', result)
        self.assertIn('results', result)
        self.assertIn('timestamp', result)
        self.assertEqual(result['summary']['status'], 'passed')
    
    @patch('multitenant.security.TENANT_SECURITY_REPORT_PATH', '/tmp/test_security_reports')
    def test_run_security_audit_all_tenants(self):
        """Test de l'exécution d'un audit global."""
        # Créer un second tenant
        tenant2 = Tenant.objects.create(
            name="Second Test Tenant",
            slug="second-test",
            schema_name="second_test"
        )
        
        result = run_security_audit()
        
        self.assertIn('summary', result)
        self.assertIn('tenants_audited', result)
        self.assertGreaterEqual(len(result['tenants_audited']), 2)
    
    @patch('multitenant.security.TENANT_SECURITY_REPORT_PATH', '/tmp/test_security_reports')
    def test_security_report_generation(self):
        """Test de la génération de rapports de sécurité."""
        result = run_security_audit(self.tenant)
        
        # Vérifier qu'un fichier de rapport a été créé
        report_files = os.listdir(self.test_report_path)
        self.assertTrue(any('security_audit' in f for f in report_files))
        
        # Vérifier le contenu du rapport
        report_file = next(f for f in report_files if 'security_audit' in f)
        report_path = os.path.join(self.test_report_path, report_file)
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        self.assertIn('summary', report_data)
        self.assertIn('results', report_data)
    
    def test_audit_with_violations(self):
        """Test d'un audit avec des violations détectées."""
        with patch.object(SecurityAuditor, 'audit_security_headers') as mock_headers:
            # Simuler des violations d'en-têtes
            mock_headers.return_value = {
                'status': 'failed',
                'violations': [{
                    'type': 'missing_header',
                    'severity': 'high',
                    'description': 'En-tête Strict-Transport-Security manquant',
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            result = run_security_audit(self.tenant)
            
            self.assertEqual(result['summary']['status'], 'failed')
            self.assertGreater(result['summary']['violations_found'], 0)


class SecurityCommandTestCase(TestCase):
    """Tests pour les commandes de gestion de sécurité."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.tenant = Tenant.objects.create(
            name="Command Test Tenant",
            slug="command-test",
            schema_name="command_test"
        )
    
    def test_run_security_audit_command(self):
        """Test de la commande run_security_audit."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('run_security_audit', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Audit de sécurité', output)
    
    def test_security_check_command(self):
        """Test de la commande security_check."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('security_check', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Vérification', output)


class SecurityTasksTestCase(TestCase):
    """Tests pour les tâches Celery de sécurité."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.tenant = Tenant.objects.create(
            name="Task Test Tenant",
            slug="task-test",
            schema_name="task_test"
        )
    
    @patch('multitenant.tasks.security_tasks.run_security_audit')
    def test_run_scheduled_security_audit_task(self):
        """Test de la tâche d'audit planifié."""
        from multitenant.tasks.security_tasks import run_scheduled_security_audit
        
        mock_result = {
            'summary': {
                'status': 'passed',
                'violations_found': 0,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        with patch('multitenant.tasks.security_tasks.run_security_audit') as mock_audit:
            mock_audit.return_value = mock_result
            
            result = run_scheduled_security_audit()
            
            self.assertEqual(result['summary']['status'], 'passed')
    
    @patch('django.core.mail.send_mail')
    def test_send_security_violation_alert(self):
        """Test de l'envoi d'alertes de violation."""
        from multitenant.tasks.security_tasks import send_security_violation_alert
        
        audit_result = {
            'summary': {
                'violations_found': 2,
                'timestamp': datetime.now().isoformat()
            },
            'results': {
                'test1': {
                    'violations': [{
                        'description': 'Test violation',
                        'severity': 'high'
                    }]
                }
            }
        }
        
        send_security_violation_alert(audit_result)
        
        # Vérifier que l'email a été envoyé
        from django.core.mail import send_mail
        send_mail.assert_called_once()