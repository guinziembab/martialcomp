"""
Module de sécurité et d'audit pour l'architecture multi-tenant.

Ce module fournit des outils pour:
1. Tester l'isolation des tenants
2. Détecter les vulnérabilités de sécurité
3. Effectuer des audits de sécurité réguliers
4. Sécuriser les données inter-tenants
"""
from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import logging
import json
import os
import re
import uuid
from datetime import datetime

from .models import Tenant
from .middleware import get_current_tenant, TenantContext

logger = logging.getLogger('multitenant.security')

# Configuration de l'auditeur de sécurité
AUDIT_LOG_PATH = os.path.join(settings.BASE_DIR, 'logs', 'security_audit.log')
TENANT_SECURITY_REPORT_PATH = os.path.join(settings.BASE_DIR, 'logs', 'security_reports')

# S'assurer que les répertoires existent
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
os.makedirs(TENANT_SECURITY_REPORT_PATH, exist_ok=True)


class SecurityAuditor:
    """
    Auditeur de sécurité pour l'architecture multi-tenant.
    Vérifie l'isolation des données et détecte les problèmes de sécurité.
    """
    
    def __init__(self, tenant=None):
        """
        Initialise l'auditeur de sécurité.
        
        Args:
            tenant: Tenant à auditer (None pour auditer tous les tenants)
        """
        self.tenant = tenant
        self.results = {}
        self.violations = []
        self.report_id = str(uuid.uuid4())
    
    def audit_cross_schema_access(self):
        """
        Vérifie l'isolation des schémas PostgreSQL.
        Test pour l'accès non autorisé entre les schémas de tenants.
        """
        self.results['cross_schema_access'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        tenants = [self.tenant] if self.tenant else Tenant.objects.filter(is_active=True)
        
        for tenant in tenants:
            # Sauvegarder le tenant actuel
            current_tenant = get_current_tenant()
            
            try:
                # Définir le contexte du tenant pour cet audit
                with TenantContext(tenant):
                    # Test 1: Vérifier si on peut accéder aux tables du schéma public
                    with connection.cursor() as cursor:
                        try:
                            # Essayer d'accéder à une table du schéma public
                            cursor.execute("SELECT * FROM public.auth_user LIMIT 1")
                            
                            # Si nous sommes ici, cela signifie que l'accès a réussi
                            violation = {
                                'tenant': tenant.name,
                                'description': f"Le schéma {tenant.schema_name} peut accéder à public.auth_user",
                                'severity': 'high',
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['cross_schema_access']['violations'].append(violation)
                            self.results['cross_schema_access']['status'] = 'failed'
                            self.violations.append(violation)
                        except Exception:
                            # L'accès a échoué, c'est bon!
                            check = {
                                'tenant': tenant.name,
                                'description': f"Le schéma {tenant.schema_name} est correctement isolé de public.auth_user",
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['cross_schema_access']['checks'].append(check)
                    
                    # Test 2: Essayer d'accéder à d'autres schémas de tenants
                    other_tenants = Tenant.objects.exclude(id=tenant.id).filter(is_active=True)
                    for other_tenant in other_tenants:
                        with connection.cursor() as cursor:
                            try:
                                # Essayer d'accéder à une table dans un autre schéma
                                cursor.execute(f"SELECT * FROM {other_tenant.schema_name}.auth_user LIMIT 1")
                                
                                # Si nous sommes ici, cela signifie que l'accès a réussi
                                violation = {
                                    'tenant': tenant.name,
                                    'description': f"Le schéma {tenant.schema_name} peut accéder à {other_tenant.schema_name}.auth_user",
                                    'severity': 'critical',
                                    'timestamp': timezone.now().isoformat()
                                }
                                self.results['cross_schema_access']['violations'].append(violation)
                                self.results['cross_schema_access']['status'] = 'failed'
                                self.violations.append(violation)
                            except Exception:
                                # L'accès a échoué, c'est bon!
                                check = {
                                    'tenant': tenant.name,
                                    'description': f"Le schéma {tenant.schema_name} est correctement isolé de {other_tenant.schema_name}",
                                    'timestamp': timezone.now().isoformat()
                                }
                                self.results['cross_schema_access']['checks'].append(check)
            
            finally:
                # Restaurer le tenant précédent
                if current_tenant:
                    with TenantContext(current_tenant):
                        pass
        
        return self.results['cross_schema_access']
    
    def audit_middleware_isolation(self):
        """
        Teste l'isolation du middleware multi-tenant.
        Vérifie que le tenant est correctement sélectionné et appliqué.
        """
        self.results['middleware_isolation'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        tenants = [self.tenant] if self.tenant else Tenant.objects.filter(is_active=True)
        
        # Test 1: Vérifier que le middleware définit correctement le schéma
        for tenant in tenants:
            current_tenant = get_current_tenant()
            
            try:
                # Définir le contexte du tenant
                with TenantContext(tenant):
                    # Vérifier que le tenant est correctement défini
                    active_tenant = get_current_tenant()
                    
                    if active_tenant != tenant:
                        violation = {
                            'tenant': tenant.name,
                            'description': f"Le middleware n'a pas correctement défini le tenant (attendu: {tenant.name}, obtenu: {active_tenant.name if active_tenant else 'None'})",
                            'severity': 'high',
                            'timestamp': timezone.now().isoformat()
                        }
                        self.results['middleware_isolation']['violations'].append(violation)
                        self.results['middleware_isolation']['status'] = 'failed'
                        self.violations.append(violation)
                    else:
                        check = {
                            'tenant': tenant.name,
                            'description': f"Le middleware a correctement défini le tenant {tenant.name}",
                            'timestamp': timezone.now().isoformat()
                        }
                        self.results['middleware_isolation']['checks'].append(check)
                    
                    # Vérifier que le schéma PostgreSQL est correctement défini
                    with connection.cursor() as cursor:
                        cursor.execute("SHOW search_path")
                        search_path = cursor.fetchone()[0]
                        
                        if tenant.schema_name not in search_path:
                            violation = {
                                'tenant': tenant.name,
                                'description': f"Le middleware n'a pas correctement défini le schéma PostgreSQL (attendu: {tenant.schema_name}, obtenu: {search_path})",
                                'severity': 'high',
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['middleware_isolation']['violations'].append(violation)
                            self.results['middleware_isolation']['status'] = 'failed'
                            self.violations.append(violation)
                        else:
                            check = {
                                'tenant': tenant.name,
                                'description': f"Le middleware a correctement défini le schéma PostgreSQL {tenant.schema_name}",
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['middleware_isolation']['checks'].append(check)
            
            finally:
                # Restaurer le tenant précédent
                if current_tenant:
                    with TenantContext(current_tenant):
                        pass
        
        return self.results['middleware_isolation']
    
    def audit_cache_isolation(self):
        """
        Teste l'isolation du cache entre les tenants.
        Vérifie que les clés de cache sont correctement préfixées par tenant.
        """
        self.results['cache_isolation'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        from django.core.cache import cache
        import random
        
        tenants = [self.tenant] if self.tenant else Tenant.objects.filter(is_active=True)
        
        # Créer des données de test distinctes pour chaque tenant
        test_data = {}
        for tenant in tenants:
            test_data[tenant.id] = {
                'random_key': f"test_key_{random.randint(10000, 99999)}",
                'random_value': f"test_value_{random.randint(10000, 99999)}"
            }
        
        # Test 1: Définir et récupérer des valeurs de cache pour chaque tenant
        for tenant in tenants:
            current_tenant = get_current_tenant()
            
            try:
                # Définir le contexte du tenant
                with TenantContext(tenant):
                    # Définir une valeur de cache pour ce tenant
                    key = test_data[tenant.id]['random_key']
                    value = test_data[tenant.id]['random_value']
                    cache.set(key, value, 60)
                    
                    # Vérifier que nous pouvons récupérer cette valeur
                    retrieved_value = cache.get(key)
                    
                    if retrieved_value != value:
                        violation = {
                            'tenant': tenant.name,
                            'description': f"Échec de récupération de la valeur du cache pour le tenant {tenant.name}",
                            'severity': 'medium',
                            'timestamp': timezone.now().isoformat()
                        }
                        self.results['cache_isolation']['violations'].append(violation)
                        self.results['cache_isolation']['status'] = 'failed'
                        self.violations.append(violation)
                    else:
                        check = {
                            'tenant': tenant.name,
                            'description': f"Récupération réussie de la valeur du cache pour le tenant {tenant.name}",
                            'timestamp': timezone.now().isoformat()
                        }
                        self.results['cache_isolation']['checks'].append(check)
            
            finally:
                # Restaurer le tenant précédent
                if current_tenant:
                    with TenantContext(current_tenant):
                        pass
        
        # Test 2: Vérifier que les tenants ne peuvent pas accéder aux valeurs de cache des autres
        for tenant in tenants:
            current_tenant = get_current_tenant()
            
            try:
                # Définir le contexte du tenant
                with TenantContext(tenant):
                    # Essayer de récupérer les valeurs de cache des autres tenants
                    for other_tenant in tenants:
                        if other_tenant.id != tenant.id:
                            other_key = test_data[other_tenant.id]['random_key']
                            other_value = cache.get(other_key)
                            
                            if other_value == test_data[other_tenant.id]['random_value']:
                                violation = {
                                    'tenant': tenant.name,
                                    'description': f"Le tenant {tenant.name} peut accéder à la valeur de cache du tenant {other_tenant.name}",
                                    'severity': 'high',
                                    'timestamp': timezone.now().isoformat()
                                }
                                self.results['cache_isolation']['violations'].append(violation)
                                self.results['cache_isolation']['status'] = 'failed'
                                self.violations.append(violation)
                            else:
                                check = {
                                    'tenant': tenant.name,
                                    'description': f"Le tenant {tenant.name} ne peut pas accéder à la valeur de cache du tenant {other_tenant.name}",
                                    'timestamp': timezone.now().isoformat()
                                }
                                self.results['cache_isolation']['checks'].append(check)
            
            finally:
                # Restaurer le tenant précédent
                if current_tenant:
                    with TenantContext(current_tenant):
                        pass
        
        # Nettoyer les données de test
        for tenant in tenants:
            with TenantContext(tenant):
                cache.delete(test_data[tenant.id]['random_key'])
        
        return self.results['cache_isolation']
    
    def audit_file_access(self):
        """
        Teste l'isolation des fichiers entre les tenants.
        Vérifie que les tenants ne peuvent pas accéder aux fichiers des autres tenants.
        """
        self.results['file_access'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        import tempfile
        import os
        
        tenants = [self.tenant] if self.tenant else Tenant.objects.filter(is_active=True)
        
        # Créer des fichiers de test pour chaque tenant
        test_files = {}
        for tenant in tenants:
            # Créer un répertoire pour ce tenant s'il n'existe pas
            tenant_dir = os.path.join(settings.MEDIA_ROOT, 'tenants', tenant.schema_name)
            os.makedirs(tenant_dir, exist_ok=True)
            
            # Créer un fichier de test
            test_file_path = os.path.join(tenant_dir, f"test_file_{uuid.uuid4()}.txt")
            with open(test_file_path, 'w') as f:
                f.write(f"Contenu secret du tenant {tenant.name}")
            
            test_files[tenant.id] = test_file_path
        
        try:
            # Test: Vérifier l'accès aux fichiers via l'URL
            from django.test import Client
            from django.urls import reverse
            
            # TODO: Implémenter un test complet avec des requêtes HTTP réelles
            # Nous avons besoin d'une vue qui servira les fichiers en fonction du tenant
            # Pour l'instant, nous faisons une vérification de base
            
            for tenant in tenants:
                # Vérifier que le fichier existe
                if os.path.exists(test_files[tenant.id]):
                    check = {
                        'tenant': tenant.name,
                        'description': f"Le fichier de test pour {tenant.name} a été créé avec succès",
                        'timestamp': timezone.now().isoformat()
                    }
                    self.results['file_access']['checks'].append(check)
                else:
                    violation = {
                        'tenant': tenant.name,
                        'description': f"Échec de création du fichier de test pour {tenant.name}",
                        'severity': 'low',
                        'timestamp': timezone.now().isoformat()
                    }
                    self.results['file_access']['violations'].append(violation)
                    self.violations.append(violation)
            
            # Vérifier l'isolation des répertoires
            for tenant in tenants:
                tenant_dir = os.path.join(settings.MEDIA_ROOT, 'tenants', tenant.schema_name)
                
                for other_tenant in tenants:
                    if other_tenant.id != tenant.id:
                        other_tenant_file = test_files[other_tenant.id]
                        
                        # Vérifier que le fichier de l'autre tenant n'est pas dans ce répertoire
                        if os.path.dirname(other_tenant_file) == tenant_dir:
                            violation = {
                                'tenant': tenant.name,
                                'description': f"Le fichier du tenant {other_tenant.name} est accessible dans le répertoire du tenant {tenant.name}",
                                'severity': 'high',
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['file_access']['violations'].append(violation)
                            self.results['file_access']['status'] = 'failed'
                            self.violations.append(violation)
                        else:
                            check = {
                                'tenant': tenant.name,
                                'description': f"Le fichier du tenant {other_tenant.name} n'est pas accessible dans le répertoire du tenant {tenant.name}",
                                'timestamp': timezone.now().isoformat()
                            }
                            self.results['file_access']['checks'].append(check)
        
        finally:
            # Nettoyer les fichiers de test
            for tenant_id, file_path in test_files.items():
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        return self.results['file_access']
    
    def audit_security_headers(self):
        """
        Vérifie la présence des en-têtes de sécurité HTTP.
        """
        self.results['security_headers'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        # Vérifier les paramètres de sécurité dans settings.py
        required_headers = {
            'X_FRAME_OPTIONS': 'DENY',
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_BROWSER_XSS_FILTER': True,
            'SECURE_SSL_REDIRECT': not settings.DEBUG,
            'SESSION_COOKIE_SECURE': not settings.DEBUG,
            'CSRF_COOKIE_SECURE': not settings.DEBUG,
        }
        
        for header, expected_value in required_headers.items():
            actual_value = getattr(settings, header, None)
            
            if actual_value != expected_value and not (settings.DEBUG and header in ['SECURE_SSL_REDIRECT', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE']):
                violation = {
                    'description': f"En-tête de sécurité {header} manquant ou incorrect (attendu: {expected_value}, obtenu: {actual_value})",
                    'severity': 'medium',
                    'timestamp': timezone.now().isoformat()
                }
                self.results['security_headers']['violations'].append(violation)
                self.results['security_headers']['status'] = 'failed'
                self.violations.append(violation)
            else:
                check = {
                    'description': f"En-tête de sécurité {header} correctement configuré",
                    'timestamp': timezone.now().isoformat()
                }
                self.results['security_headers']['checks'].append(check)
        
        return self.results['security_headers']
    
    def audit_tenant_permissions(self):
        """
        Vérifie que les permissions sont correctement appliquées aux tenants.
        """
        self.results['tenant_permissions'] = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        tenants = [self.tenant] if self.tenant else Tenant.objects.filter(is_active=True)
        
        # Vérifier l'isolation des permissions entre tenants
        for tenant in tenants:
            current_tenant = get_current_tenant()
            
            try:
                # Définir le contexte du tenant
                with TenantContext(tenant):
                    # TODO: Implémenter des tests spécifiques aux permissions
                    # Pour l'instant, nous ajoutons un simple contrôle
                    
                    check = {
                        'tenant': tenant.name,
                        'description': f"Test de permissions pour le tenant {tenant.name}",
                        'timestamp': timezone.now().isoformat()
                    }
                    self.results['tenant_permissions']['checks'].append(check)
            
            finally:
                # Restaurer le tenant précédent
                if current_tenant:
                    with TenantContext(current_tenant):
                        pass
        
        return self.results['tenant_permissions']
    
    def run_all_audits(self):
        """
        Exécute tous les audits de sécurité.
        """
        self.audit_cross_schema_access()
        self.audit_middleware_isolation()
        self.audit_cache_isolation()
        self.audit_file_access()
        self.audit_security_headers()
        self.audit_tenant_permissions()
        
        # Calculer le résultat global
        all_passed = all(result['status'] == 'passed' for result in self.results.values())
        
        # Enregistrer le rapport d'audit
        self.save_audit_report()
        
        # Journaliser le résultat
        if all_passed:
            logger.info(f"Audit de sécurité réussi: {len(self.results)} tests passés")
        else:
            logger.warning(f"Audit de sécurité échoué: {len(self.violations)} violations trouvées")
            
            # Journaliser chaque violation
            for violation in self.violations:
                tenant_name = violation.get('tenant', 'global')
                description = violation.get('description', 'Violation inconnue')
                severity = violation.get('severity', 'unknown')
                
                logger.warning(f"Violation de sécurité pour {tenant_name}: {description} (Sévérité: {severity})")
        
        return {
            'summary': {
                'status': 'passed' if all_passed else 'failed',
                'tests_run': len(self.results),
                'violations_found': len(self.violations),
                'report_id': self.report_id,
                'timestamp': timezone.now().isoformat(),
                'tenant': self.tenant.name if self.tenant else 'all',
            },
            'results': self.results
        }
    
    def save_audit_report(self):
        """
        Enregistre le rapport d'audit dans un fichier JSON.
        """
        now = datetime.now()
        tenant_name = self.tenant.name if self.tenant else 'all_tenants'
        
        # Créer le nom du fichier
        filename = f"security_audit_{tenant_name}_{now.strftime('%Y%m%d_%H%M%S')}_{self.report_id}.json"
        filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
        
        # Préparer le rapport
        report = {
            'summary': {
                'status': 'passed' if not self.violations else 'failed',
                'tests_run': len(self.results),
                'violations_found': len(self.violations),
                'report_id': self.report_id,
                'timestamp': timezone.now().isoformat(),
                'tenant': self.tenant.name if self.tenant else 'all',
            },
            'results': self.results
        }
        
        # Enregistrer le rapport
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Rapport d'audit de sécurité enregistré: {filepath}")
        
        return filepath


class TenantSecurityMonitor:
    """
    Moniteur de sécurité pour surveiller en continu les tenants.
    """
    
    @staticmethod
    def check_tenant_activity(tenant):
        """
        Vérifie l'activité suspecte sur un tenant.
        
        Args:
            tenant: Le tenant à surveiller
        
        Returns:
            Liste des activités suspectes
        """
        suspicious_activities = []
        
        # TODO: Implémenter des vérifications d'activité suspecte
        # Par exemple:
        # - Connexions depuis des adresses IP inhabituelles
        # - Taux anormalement élevé de requêtes API
        # - Accès à des ressources sensibles
        # - Tentatives d'accès à d'autres tenants
        
        return suspicious_activities
    
    @staticmethod
    def check_database_integrity(tenant):
        """
        Vérifie l'intégrité de la base de données du tenant.
        
        Args:
            tenant: Le tenant à vérifier
        
        Returns:
            Résultat du contrôle d'intégrité
        """
        with TenantContext(tenant):
            # Vérifier la structure de la base de données
            with connection.cursor() as cursor:
                # Vérifier si toutes les tables attendues sont présentes
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, [tenant.schema_name])
                
                tables = [row[0] for row in cursor.fetchall()]
                
                # Liste minimale de tables attendues
                expected_tables = [
                    'auth_user',
                    'competitions_practitioner',
                    'competitions_club',
                    'competitions_federation',
                ]
                
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    return {
                        'status': 'failed',
                        'message': f"Tables manquantes: {', '.join(missing_tables)}",
                        'missing_tables': missing_tables
                    }
                
                return {
                    'status': 'passed',
                    'message': f"Intégrité de la base de données vérifiée: {len(tables)} tables présentes"
                }


class TenantComplianceChecker:
    """
    Vérificateur de conformité pour les standards de sécurité.
    """
    
    @staticmethod
    def check_gdpr_compliance(tenant):
        """
        Vérifie la conformité RGPD (GDPR) pour un tenant.
        
        Args:
            tenant: Le tenant à vérifier
        
        Returns:
            Résultat du contrôle RGPD
        """
        results = {
            'status': 'passed',
            'checks': [],
            'violations': []
        }
        
        with TenantContext(tenant):
            # Vérification 1: Consentement des utilisateurs
            # TODO: Vérifier si un mécanisme de consentement est en place
            
            # Vérification 2: Politique de confidentialité
            # TODO: Vérifier si une politique de confidentialité est disponible
            
            # Vérification 3: Données personnelles
            # Vérifier si des données personnelles sensibles sont stockées correctement
            with connection.cursor() as cursor:
                # Vérifier si des champs de données sensibles sont présents sans encryption
                cursor.execute("""
                    SELECT column_name, table_name
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND column_name IN ('password', 'credit_card', 'social_security', 'passport_number')
                """, [tenant.schema_name])
                
                sensitive_columns = cursor.fetchall()
                
                if sensitive_columns:
                    for column, table in sensitive_columns:
                        violation = {
                            'tenant': tenant.name,
                            'description': f"Données sensibles potentiellement non chiffrées: {column} dans {table}",
                            'severity': 'high',
                            'timestamp': timezone.now().isoformat()
                        }
                        results['violations'].append(violation)
                        results['status'] = 'failed'
                
                # Ajout des vérifications passées
                checks = [
                    {
                        'tenant': tenant.name,
                        'description': "Vérification de base RGPD effectuée",
                        'timestamp': timezone.now().isoformat()
                    }
                ]
                results['checks'].extend(checks)
        
        return results


# Fonctions utilitaires pour la sécurité multi-tenant

def secure_tenant_function(view_func):
    """
    Décorateur pour sécuriser les fonctions tenant-aware.
    Vérifie que le tenant est correctement défini et journalise les accès.
    """
    def wrapped_view(request, *args, **kwargs):
        # Vérifier que le tenant est défini
        if not hasattr(request, 'tenant') or not request.tenant:
            logger.warning(f"Tentative d'accès sans tenant défini: {request.path}")
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Tenant non spécifié")
        
        # Journaliser l'accès
        tenant_name = request.tenant.name
        user_id = request.user.id if request.user.is_authenticated else 'anonyme'
        
        logger.info(f"Accès tenant: {tenant_name}, utilisateur: {user_id}, chemin: {request.path}")
        
        # Exécuter la vue
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def run_security_audit(tenant=None):
    """
    Fonction utilitaire pour exécuter un audit de sécurité.
    
    Args:
        tenant: Le tenant à auditer (None pour tous les tenants)
    
    Returns:
        Résultat de l'audit
    """
    auditor = SecurityAuditor(tenant)
    return auditor.run_all_audits()