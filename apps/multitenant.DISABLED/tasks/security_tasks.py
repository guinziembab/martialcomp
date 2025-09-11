"""
TÃ¢ches Celery pour les audits de sécurité multi-tenant.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

from apps.multitenant.security import run_security_audit, SecurityAuditor
from apps.multitenant.models import Tenant

logger = logging.getLogger(__name__)


@shared_task
def run_scheduled_security_audit(tenant_id=None):
    """
    Exécute un audit de sécurité planifié.
    
    Args:
        tenant_id: ID du tenant Ã  auditer (None pour un audit global)
    
    Returns:
        dict: Résultat de l'audit
    """
    try:
        if tenant_id:
            tenant = Tenant.objects.get(id=tenant_id)
            logger.info(f"Lancement de l'audit de sécurité pour le tenant: {tenant.name}")
            result = run_security_audit(tenant)
        else:
            logger.info("Lancement de l'audit de sécurité global")
            result = run_security_audit()
        
        # Envoyer une notification si des violations ont été trouvées
        if result['summary']['violations_found'] > 0:
            send_security_violation_alert.delay(result)
        
        logger.info("Audit de sécurité terminé avec succès")
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de l'audit de sécurité: {str(e)}")
        raise


@shared_task
def send_security_violation_alert(audit_result):
    """
    Envoie une alerte email pour les violations de sécurité.
    
    Args:
        audit_result: Résultat de l'audit contenant les violations
    """
    try:
        violations_count = audit_result['summary']['violations_found']
        is_global = 'tenants_audited' in audit_result
        
        subject = _("Alerte sécurité MartialComp: {} violations détectées").format(violations_count)
        
        # Construire le message
        message = _("Un audit de sécurité a détecté {} violations.\n\n").format(violations_count)
        
        if is_global:
            message += _("Type d'audit: Global (tous les tenants)\n")
            message += _("Tenants audités: {}\n").format(len(audit_result.get('tenants_audited', [])))
        else:
            tenant_name = audit_result.get('tenant_name', 'Inconnu')
            message += _("Type d'audit: Tenant spécifique\n")
            message += _("Tenant: {}\n").format(tenant_name)
        
        message += _("Date: {}\n\n").format(audit_result['summary']['timestamp'])
        
        # Détailler les violations par type
        message += _("Détail des violations:\n")
        for test_name, test_result in audit_result['results'].items():
            if 'violations' in test_result and test_result['violations']:
                message += f"\n{test_name}:\n"
                for violation in test_result['violations']:
                    message += f"  - {violation['description']} (Sévérité: {violation['severity']})\n"
        
        # Ajouter un lien vers le tableau de bord
        if hasattr(settings, 'BASE_URL'):
            dashboard_url = f"{settings.BASE_URL}/multitenant/admin/security/"
            message += f"\n\nConsultez le tableau de bord pour plus de détails: {dashboard_url}"
        
        # Envoyer l'email aux administrateurs
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin[1] for admin in settings.ADMINS],
            fail_silently=False,
        )
        
        logger.info(f"Alerte de sécurité envoyée pour {violations_count} violations")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte de sécurité: {str(e)}")
        raise


@shared_task
def check_tenant_security_compliance(tenant_id):
    """
    Vérifie la conformité de sécurité d'un tenant spécifique.
    
    Args:
        tenant_id: ID du tenant Ã  vérifier
    
    Returns:
        dict: Résultat de la vérification de conformité
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        auditor = SecurityAuditor()
        
        logger.info(f"Vérification de conformité pour le tenant: {tenant.name}")
        
        # Effectuer des tests de conformité spécifiques
        compliance_results = {
            'tenant_name': tenant.name,
            'tenant_id': str(tenant.id),
            'timestamp': auditor._get_timestamp(),
            'checks': []
        }
        
        # Vérifier l'isolation des données
        isolation_result = auditor.audit_cross_schema_access()
        compliance_results['checks'].append({
            'name': 'data_isolation',
            'passed': isolation_result['status'] == 'passed',
            'violations': isolation_result.get('violations', [])
        })
        
        # Vérifier les permissions
        permissions_result = auditor.audit_tenant_permissions()
        compliance_results['checks'].append({
            'name': 'permissions',
            'passed': permissions_result['status'] == 'passed',
            'violations': permissions_result.get('violations', [])
        })
        
        # Vérifier la sécurité des fichiers
        files_result = auditor.audit_file_access()
        compliance_results['checks'].append({
            'name': 'file_security',
            'passed': files_result['status'] == 'passed',
            'violations': files_result.get('violations', [])
        })
        
        # Calculer le score de conformité
        total_checks = len(compliance_results['checks'])
        passed_checks = sum(1 for check in compliance_results['checks'] if check['passed'])
        compliance_results['compliance_score'] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Mettre Ã  jour le statut de sécurité du tenant
        update_tenant_security_status.delay(tenant_id, compliance_results)
        
        logger.info(f"Vérification de conformité terminée pour {tenant.name}: {compliance_results['compliance_score']}%")
        
        return compliance_results
    
    except Tenant.DoesNotExist:
        logger.error(f"Tenant non trouvé: {tenant_id}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de conformité: {str(e)}")
        raise


@shared_task
def update_tenant_security_status(tenant_id, compliance_results):
    """
    Met Ã  jour le statut de sécurité d'un tenant.
    
    Args:
        tenant_id: ID du tenant
        compliance_results: Résultats de la vérification de conformité
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        score = compliance_results['compliance_score']
        
        # Déterminer le statut basé sur le score
        if score >= 90:
            security_status = 'ok'
        elif score >= 70:
            security_status = 'warning'
        else:
            security_status = 'critical'
        
        # Mettre Ã  jour le tenant (ajouter ces champs au modèle si nécessaire)
        # tenant.security_status = security_status
        # tenant.last_security_audit = timezone.now()
        # tenant.save()
        
        logger.info(f"Statut de sécurité mis Ã  jour pour {tenant.name}: {security_status} ({score}%)")
        
        # Si le statut est critique, envoyer une alerte
        if security_status == 'critical':
            send_critical_security_alert.delay(tenant_id, compliance_results)
    
    except Tenant.DoesNotExist:
        logger.error(f"Tenant non trouvé: {tenant_id}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise Ã  jour du statut de sécurité: {str(e)}")
        raise


@shared_task
def send_critical_security_alert(tenant_id, compliance_results):
    """
    Envoie une alerte pour un tenant avec un statut de sécurité critique.
    
    Args:
        tenant_id: ID du tenant
        compliance_results: Résultats de la vérification de conformité
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        subject = _("ALERTE CRITIQUE: Problème de sécurité pour le tenant {}").format(tenant.name)
        
        message = _("Le tenant {} présente des problèmes de sécurité critiques.\n\n").format(tenant.name)
        message += _("Score de conformité: {}%\n\n").format(compliance_results['compliance_score'])
        
        message += _("Violations détectées:\n")
        for check in compliance_results['checks']:
            if not check['passed']:
                message += f"\n{check['name']}:\n"
                for violation in check.get('violations', []):
                    message += f"  - {violation.get('description', 'Violation inconnue')}\n"
        
        message += _("\n\nAction requise: Veuillez examiner et corriger ces problèmes immédiatement.")
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin[1] for admin in settings.ADMINS],
            fail_silently=False,
        )
        
        logger.warning(f"Alerte critique envoyée pour le tenant: {tenant.name}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte critique: {str(e)}")
        raise


@shared_task
def cleanup_old_security_reports(days=30):
    """
    Nettoie les anciens rapports de sécurité.
    
    Args:
        days: Nombre de jours Ã  conserver (par défaut 30)
    """
    try:
        from datetime import datetime, timedelta
        import os
        from apps.multitenant.security import TENANT_SECURITY_REPORT_PATH
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        if os.path.exists(TENANT_SECURITY_REPORT_PATH):
            for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
                filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
                
                # Vérifier la date de création du fichier
                file_date = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_date < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
                    logger.info(f"Rapport supprimé: {filename}")
        
        logger.info(f"Nettoyage terminé: {removed_count} rapports supprimés")
        return removed_count
    
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des rapports: {str(e)}")
        raise

