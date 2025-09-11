"""
Vues pour la gestion de la sécurité multi-tenant.
"""
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.views import View
import os
import json
from datetime import datetime, timedelta

from apps.multitenant.mixins import TenantAwareViewMixin, TenantRequiredMixin, SuperAdminRequiredMixin
from apps.multitenant.models import Tenant
from apps.multitenant.security import SecurityAuditor, run_security_audit, TENANT_SECURITY_REPORT_PATH
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class SecurityDashboardView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    """
    Tableau de bord de sécurité multi-tenant.
    """
    template_name = 'multitenant/security/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les rapports d'audit récents
        reports = self._get_recent_reports()
        
        # Statistiques de sécurité
        security_stats = self._get_security_stats(reports)
        
        context.update({
            'reports': reports,
            'security_stats': security_stats,
            'tenants': Tenant.objects.filter(is_active=True),
            'last_audit': self._get_last_audit_date(),
            'security_score': self._calculate_security_score(security_stats),
        })
        
        return context
    
    def _get_recent_reports(self, limit=10):
        """Récupère les rapports d'audit les plus récents."""
        if not os.path.exists(TENANT_SECURITY_REPORT_PATH):
            return []
        
        # Lister tous les fichiers JSON dans le répertoire
        reports = []
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
            
            try:
                # Extraire les informations du nom de fichier
                parts = filename.replace('.json', '').split('_')
                
                # Vérifier si c'est un rapport global ou tenant
                is_global = 'global' in filename
                
                if is_global:
                    tenant = 'Tous les tenants'
                    date_parts = parts[-2:]
                else:
                    tenant = parts[2] if len(parts) > 2 else 'Inconnu'
                    date_parts = parts[-3:-1]
                
                # Analyser la date
                try:
                    date_str = '_'.join(date_parts)
                    report_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                except (ValueError, IndexError):
                    report_date = datetime.fromtimestamp(os.path.getctime(filepath))
                
                # Récupérer le statut depuis le fichier JSON
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        status = data.get('summary', {}).get('status', 'unknown')
                        violations = data.get('summary', {}).get('violations_found', 0)
                except (json.JSONDecodeError, IOError):
                    status = 'unknown'
                    violations = 0
                
                reports.append({
                    'filename': filename,
                    'filepath': filepath,
                    'tenant': tenant,
                    'date': report_date,
                    'status': status,
                    'violations': violations,
                    'is_global': is_global
                })
            except Exception as e:
                continue
        
        # Trier par date décroissante et limiter le nombre
        reports.sort(key=lambda x: x['date'], reverse=True)
        return reports[:limit]
    
    def _get_security_stats(self, reports):
        """Calcule les statistiques de sécurité Ã  partir des rapports."""
        stats = {
            'total_audits': len(reports),
            'passed_audits': sum(1 for r in reports if r['status'] == 'passed'),
            'failed_audits': sum(1 for r in reports if r['status'] == 'failed'),
            'total_violations': sum(r['violations'] for r in reports),
            'recent_violations': sum(r['violations'] for r in reports[:3]),
            'is_improving': False,
        }
        
        # Vérifier si la tendance s'améliore
        if len(reports) >= 2:
            older_violations = sum(r['violations'] for r in reports[len(reports)//2:])
            newer_violations = sum(r['violations'] for r in reports[:len(reports)//2])
            stats['is_improving'] = newer_violations < older_violations
        
        return stats
    
    def _get_last_audit_date(self):
        """Récupère la date du dernier audit."""
        reports = self._get_recent_reports(limit=1)
        return reports[0]['date'] if reports else None
    
    def _calculate_security_score(self, stats):
        """Calcule un score de sécurité de 0 Ã  100."""
        if not stats['total_audits']:
            return 0
        
        base_score = (stats['passed_audits'] / stats['total_audits']) * 100
        
        # Pénalités pour les violations
        if stats['total_violations'] > 0:
            penalty = min(50, stats['total_violations'] * 5)
            base_score = max(0, base_score - penalty)
        
        # Bonus pour l'amélioration
        if stats['is_improving']:
            base_score = min(100, base_score + 10)
        
        return int(base_score)


class SecurityReportListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    """
    Liste des rapports d'audit de sécurité.
    """
    template_name = 'multitenant/security/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        # Filtres
        tenant_filter = self.request.GET.get('tenant')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # Obtenir tous les rapports
        all_reports = self._get_all_reports()
        
        # Appliquer les filtres
        filtered_reports = all_reports
        
        if tenant_filter:
            filtered_reports = [r for r in filtered_reports if tenant_filter in r['tenant']]
        
        if status_filter:
            filtered_reports = [r for r in filtered_reports if r['status'] == status_filter]
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                filtered_reports = [r for r in filtered_reports if r['date'] >= date_from_obj]
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                filtered_reports = [r for r in filtered_reports if r['date'] <= date_to_obj]
            except ValueError:
                pass
        
        return filtered_reports
    
    def _get_all_reports(self):
        """Récupère tous les rapports d'audit."""
        if not os.path.exists(TENANT_SECURITY_REPORT_PATH):
            return []
        
        reports = []
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
            
            try:
                # Analyser le nom de fichier pour extraire les informations
                parts = filename.replace('.json', '').split('_')
                
                # Vérifier si c'est un rapport global ou tenant
                is_global = 'global' in filename
                
                if is_global:
                    tenant = 'Tous les tenants'
                    date_parts = parts[-2:]
                else:
                    tenant = parts[2] if len(parts) > 2 else 'Inconnu'
                    date_parts = parts[-3:-1]
                
                # Analyser la date
                try:
                    date_str = '_'.join(date_parts)
                    report_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                except (ValueError, IndexError):
                    report_date = datetime.fromtimestamp(os.path.getctime(filepath))
                
                # Récupérer le statut depuis le fichier JSON
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        status = data.get('summary', {}).get('status', 'unknown')
                        violations = data.get('summary', {}).get('violations_found', 0)
                        tests_run = data.get('summary', {}).get('tests_run', 0)
                except (json.JSONDecodeError, IOError):
                    status = 'unknown'
                    violations = 0
                    tests_run = 0
                
                reports.append({
                    'id': os.path.splitext(filename)[0],
                    'filename': filename,
                    'filepath': filepath,
                    'tenant': tenant,
                    'date': report_date,
                    'status': status,
                    'violations': violations,
                    'tests_run': tests_run,
                    'is_global': is_global
                })
            except Exception as e:
                continue
        
        # Trier par date décroissante
        reports.sort(key=lambda x: x['date'], reverse=True)
        return reports
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les filtres
        context['tenant_filter'] = self.request.GET.get('tenant', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Liste des tenants pour le filtre
        context['tenants'] = sorted(list(set(r['tenant'] for r in self._get_all_reports())))
        
        return context


class SecurityReportDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    """
    Détail d'un rapport d'audit de sécurité.
    """
    template_name = 'multitenant/security/report_detail.html'
    context_object_name = 'report'
    
    def get_object(self):
        """Récupère le rapport spécifié."""
        report_id = self.kwargs.get('report_id')
        
        # Chercher le fichier correspondant
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if filename.startswith(report_id) and filename.endswith('.json'):
                filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Extraire les informations du nom de fichier
                        parts = filename.replace('.json', '').split('_')
                        
                        # Vérifier si c'est un rapport global ou tenant
                        is_global = 'global' in filename
                        
                        if is_global:
                            tenant = 'Tous les tenants'
                            date_parts = parts[-2:]
                        else:
                            tenant = parts[2] if len(parts) > 2 else 'Inconnu'
                            date_parts = parts[-3:-1]
                        
                        # Analyser la date
                        try:
                            date_str = '_'.join(date_parts)
                            report_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        except (ValueError, IndexError):
                            report_date = datetime.fromtimestamp(os.path.getctime(filepath))
                        
                        return {
                            'id': os.path.splitext(filename)[0],
                            'filename': filename,
                            'filepath': filepath,
                            'tenant': tenant,
                            'date': report_date,
                            'data': data,
                            'is_global': is_global
                        }
                except (json.JSONDecodeError, IOError):
                    pass
        
        raise Http404("Rapport d'audit non trouvé")


class RunSecurityAuditView(LoginRequiredMixin, SuperAdminRequiredMixin, FormView):
    """
    Vue pour exécuter un audit de sécurité.
    """
    template_name = 'multitenant/security/run_audit.html'
    form_class = None  # Défini dynamiquement
    success_url = reverse_lazy('multitenant:security_dashboard')
    
    def get_form_class(self):
        """Définit dynamiquement le formulaire."""
        from django import forms
        
        class SecurityAuditForm(forms.Form):
            tenant = forms.ModelChoiceField(
                queryset=Tenant.objects.filter(is_active=True),
                required=False,
                label=_("Tenant Ã  auditer"),
                help_text=_("Laissez vide pour auditer tous les tenants")
            )
            
            # Tests Ã  exécuter
            TESTS = (
                ('cross_schema_access', _("Accès entre schémas")),
                ('middleware_isolation', _("Isolation du middleware")),
                ('cache_isolation', _("Isolation du cache")),
                ('file_access', _("Accès aux fichiers")),
                ('security_headers', _("En-tÃªtes de sécurité")),
                ('tenant_permissions', _("Permissions des tenants")),
            )
            
            tests_to_run = forms.MultipleChoiceField(
                choices=TESTS,
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=_("Tests Ã  exécuter"),
                help_text=_("Sélectionnez les tests Ã  exécuter. Laissez vide pour tous les exécuter.")
            )
        
        return SecurityAuditForm
    
    def form_valid(self, form):
        """Exécute l'audit de sécurité."""
        tenant = form.cleaned_data.get('tenant')
        tests_to_run = form.cleaned_data.get('tests_to_run')
        
        try:
            # Exécuter l'audit de sécurité
            if tenant:
                messages.info(
                    self.request, 
                    _("Audit de sécurité lancé pour le tenant: {}").format(tenant.name)
                )
                result = run_security_audit(tenant)
            else:
                messages.info(
                    self.request, 
                    _("Audit de sécurité global lancé pour tous les tenants")
                )
                result = run_security_audit()
            
            # Analyser le résultat
            if result['summary']['status'] == 'passed':
                messages.success(
                    self.request,
                    _("Audit de sécurité réussi: {} tests passés").format(
                        result['summary']['tests_run']
                    )
                )
            else:
                messages.warning(
                    self.request,
                    _("Audit de sécurité avec violations: {} violations trouvées").format(
                        result['summary']['violations_found']
                    )
                )
            
            # Rediriger vers la liste des rapports
            return redirect('multitenant:security_reports')
            
        except Exception as e:
            messages.error(
                self.request,
                _("Erreur lors de l'exécution de l'audit: {}").format(str(e))
            )
            return self.form_invalid(form)


class SecurityViolationsView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    """
    Vue pour afficher et analyser les violations de sécurité.
    """
    template_name = 'multitenant/security/violations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer toutes les violations des rapports récents
        violations = self._get_all_violations()
        
        # Regrouper par type et sévérité
        by_severity = {}
        by_tenant = {}
        by_type = {}
        
        for violation in violations:
            # Par sévérité
            severity = violation.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Par tenant
            tenant = violation.get('tenant', 'unknown')
            by_tenant[tenant] = by_tenant.get(tenant, 0) + 1
            
            # Par type (basé sur la description)
            description = violation.get('description', '')
            
            if 'schéma' in description:
                type_code = 'schema_isolation'
            elif 'middleware' in description:
                type_code = 'middleware'
            elif 'cache' in description:
                type_code = 'cache_isolation'
            elif 'fichier' in description:
                type_code = 'file_access'
            elif 'En-tÃªte' in description or 'header' in description:
                type_code = 'security_headers'
            elif 'permission' in description:
                type_code = 'permissions'
            else:
                type_code = 'other'
            
            by_type[type_code] = by_type.get(type_code, 0) + 1
        
        context.update({
            'violations': violations,
            'by_severity': by_severity,
            'by_tenant': by_tenant,
            'by_type': by_type,
            'total_violations': len(violations),
            'recent_reports': self._get_recent_reports(5),
        })
        
        return context
    
    def _get_all_violations(self):
        """Récupère toutes les violations de sécurité des rapports récents."""
        violations = []
        
        # Récupérer les rapports des 30 derniers jours
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
            file_date = datetime.fromtimestamp(os.path.getctime(filepath))
            
            if file_date < cutoff_date:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraire les violations
                    results = data.get('results', {})
                    
                    for test_name, test_result in results.items():
                        if 'violations' in test_result:
                            for violation in test_result['violations']:
                                # Ajouter des métadonnées du rapport
                                violation['report_file'] = filename
                                violation['report_date'] = file_date.isoformat()
                                violation['test_name'] = test_name
                                
                                violations.append(violation)
            except (json.JSONDecodeError, IOError):
                continue
        
        # Trier par date décroissante
        violations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return violations
    
    def _get_recent_reports(self, limit=5):
        """Récupère les rapports d'audit récents."""
        reports = []
        
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraire les informations du rapport
                    status = data.get('summary', {}).get('status', 'unknown')
                    violations = data.get('summary', {}).get('violations_found', 0)
                    timestamp = data.get('summary', {}).get('timestamp', None)
                    
                    if timestamp:
                        report_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        report_date = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    reports.append({
                        'filename': filename,
                        'date': report_date,
                        'status': status,
                        'violations': violations,
                    })
            except Exception:
                continue
        
        # Trier par date décroissante et limiter
        reports.sort(key=lambda x: x['date'], reverse=True)
        return reports[:limit]


class DownloadSecurityReportView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour télécharger un rapport de sécurité.
    """
    def get(self, request, *args, **kwargs):
        report_id = kwargs.get('report_id')
        
        # Chercher le fichier correspondant
        for filename in os.listdir(TENANT_SECURITY_REPORT_PATH):
            if filename.startswith(report_id) and filename.endswith('.json'):
                filepath = os.path.join(TENANT_SECURITY_REPORT_PATH, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        response = HttpResponse(content, content_type='application/json')
                        response['Content-Disposition'] = f'attachment; filename="{filename}"'
                        return response
                except IOError:
                    break
        
        raise Http404("Rapport d'audit non trouvé")

