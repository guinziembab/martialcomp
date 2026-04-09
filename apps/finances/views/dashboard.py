from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

from ..models.transactions import Transaction
from ..models.invoices import Invoice
from ..models.accounts import FinancialAccount
from ..utils import get_financial_permissions
from ..utils.permissions import finance_dashboard_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class FinancialDashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord financier principal."""
    template_name = 'finances/dashboard/index.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérification personnalisée pour autoriser les rÃ´les spécifiques
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Les superusers et staff peuvent toujours accéder
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        
        # Permission explicite dans Django
        if request.user.has_perm('finances.view_dashboard'):
            return super().dispatch(request, *args, **kwargs)
            
        # Vérifier les rÃ´les utilisateur
        if hasattr(request.user, 'userprofile'):
            # Autoriser les rÃ´les administratifs
            allowed_roles = ['federation_admin', 'club_admin', 'club_owner', 'club_manager', 'coach']
            if request.user.userprofile.role in allowed_roles:
                return super().dispatch(request, *args, **kwargs)

        # Vérifier via OrganizationMember (rôle principal ou additionnel)
        try:
            from apps.organizations.models import OrganizationMember, MembershipStatus
            finance_roles = {'owner', 'admin', 'manager', 'treasurer', 'accountant'}
            members = OrganizationMember.objects.filter(
                user=request.user,
                is_active=True,
                membership_status=MembershipStatus.APPROVED
            )
            for m in members:
                if m.role in finance_roles:
                    return super().dispatch(request, *args, **kwargs)
                additional = getattr(m, 'additional_roles', None) or []
                if finance_roles.intersection(additional):
                    return super().dispatch(request, *args, **kwargs)
        except Exception:
            pass

        # Rediriger vers la page d'accueil si aucune permission
        from django.contrib import messages
        from django.utils.translation import gettext_lazy as _
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder au tableau de bord financier."))
        return redirect('welcome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        context['permissions'] = permissions

        # Devise affichage - utiliser le service multi-devise
        try:
            from ..currency_service import get_preferred_currency_for_request
            currency_code, _ = get_preferred_currency_for_request(self.request)
        except Exception:
            currency_code = 'EUR'
        context['currency_code'] = currency_code
        context['currency'] = currency_code  # Compatibilite
        
        # Détecter le rôle utilisateur pour adapter l'interface
        user_role = None
        if hasattr(self.request.user, 'userprofile'):
            user_role = self.request.user.userprofile.role
        context['user_role'] = user_role
        context['is_coach'] = user_role == 'coach'
        
        # Périodes pour les statistiques
        today = timezone.now().date()

        # Période par défaut: toutes les transactions (cohérence avec dashboard club)
        start_date = None
        end_date = today

        # Changer la période selon les paramètres
        period = self.request.GET.get('period', 'all')
        if period == 'all':
            start_date = None  # Pas de filtre de date
        elif period == '7days':
            start_date = today - timedelta(days=7)
        elif period == '30days':
            start_date = today - timedelta(days=30)
        elif period == '90days':
            start_date = today - timedelta(days=90)
        elif period == 'ytd':
            start_date = date(today.year, 1, 1)
        elif period == 'month':
            start_date = date(today.year, today.month, 1)
        elif period == 'prev_month':
            last_month = today - relativedelta(months=1)
            start_date = date(last_month.year, last_month.month, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
        elif period == 'custom':
            try:
                start_date = timezone.datetime.strptime(
                    self.request.GET.get('start_date', ''), 
                    '%Y-%m-%d'
                ).date()
                end_date = timezone.datetime.strptime(
                    self.request.GET.get('end_date', ''), 
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                # En cas d'erreur, revenir Ã  la période par défaut
                pass
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['period'] = period

        # Statistiques des transactions
        if start_date:
            transactions = Transaction.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            )
        else:
            # Pas de filtre de date - toutes les transactions
            transactions = Transaction.objects.all()

        # Détecter l'organisation (club/fédération) et limiter aux comptes de l'organisation
        organization = None
        try:
            from ..currency_service import _get_request_organization
            organization = _get_request_organization(self.request)
        except Exception:
            organization = None

        if organization:
            ct = ContentType.objects.get_for_model(organization.__class__)
            owner_id = str(getattr(organization, 'id', ''))
            org_account_ids = FinancialAccount.objects.filter(
                owner_content_type=ct,
                owner_id=owner_id
            ).values('pk')
            transactions = transactions.filter(Q(financial_account__in=org_account_ids))

        # Filtrer selon les permissions (créateur/validateur)
        if not permissions.get('can_view_all_transactions', False):
            # Si filtré par organisation, on autorise toutes les transactions de l'organisation
            if not organization:
                transactions = transactions.filter(
                    Q(created_by=self.request.user) |
                    Q(validated_by=self.request.user) |
                    Q(updated_by=self.request.user)
                )
        
        # Résumés financiers
        incomes = transactions.filter(type='income')
        expenses = transactions.filter(type='expense')
        
        context['total_income'] = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_expense'] = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        context['net_result'] = context['total_income'] - context['total_expense']
        
        # Statistiques des transactions par statut
        status_counts = transactions.values('status').annotate(count=Count('id'))
        context['status_stats'] = {
            status['status']: status['count'] 
            for status in status_counts
        }
        
        # Transactions récentes
        context['recent_transactions'] = transactions.order_by('-date', '-date_created')[:10]
        
        # Statistiques des factures
        if start_date:
            invoices = Invoice.objects.filter(
                issued_date__gte=start_date,
                issued_date__lte=end_date
            )
        else:
            # Pas de filtre de date - toutes les factures
            invoices = Invoice.objects.all()
        if organization:
            ct = ContentType.objects.get_for_model(organization.__class__)
            org_id = str(getattr(organization, 'id', ''))
            invoices = invoices.filter(
                Q(issuer_content_type=ct, issuer_object_id=org_id) |
                Q(recipient_content_type=ct, recipient_object_id=org_id)
            )
        
        context['invoice_count'] = invoices.count()
        context['invoice_total'] = invoices.aggregate(Sum('total'))['total__sum'] or 0
        context['paid_invoices'] = invoices.filter(status='paid').count()
        context['unpaid_invoices'] = invoices.filter(status='unpaid').count()
        
        # Factures récentes
        context['recent_invoices'] = invoices.order_by('-issued_date', '-created_at')[:10]
        
        # Résumé des comptes financiers
        if permissions.get('can_view_accounts', False):
            accounts = FinancialAccount.objects.filter(is_active=True)
            if organization:
                ct = ContentType.objects.get_for_model(organization.__class__)
                owner_id = str(getattr(organization, 'id', ''))
                accounts = accounts.filter(owner_content_type=ct, owner_id=owner_id)
            context['financial_accounts'] = accounts
            context['total_balance'] = sum(account.current_balance for account in accounts)
        
        # Données pour les graphiques
        if permissions.get('can_view_reports', False) and start_date:
            # Graphique des revenus vs dépenses par jour (seulement si une période est définie)
            time_series_data = self._get_time_series_data(start_date, end_date)
            context['time_series_data'] = time_series_data
            
            # Graphique des revenus et dépenses par catégorie
            category_data = self._get_category_data(start_date, end_date)
            context['category_data'] = category_data
        
        return context
    
    def _get_time_series_data(self, start_date, end_date):
        """Prépare les données pour le graphique temporel des revenus vs dépenses."""
        # Nombre de jours dans la période
        days = (end_date - start_date).days + 1
        
        # Si la période est longue, agréger par semaine ou mois
        grouping = 'day'  # Par défaut, grouper par jour
        if days > 90:
            grouping = 'month'
        elif days > 30:
            grouping = 'week'
            
        # RequÃªte et formatage des données selon le groupement
        if grouping == 'day':
            # Agrégation par jour
            income_data = Transaction.objects.filter(
                type='income',
                date__gte=start_date,
                date__lte=end_date
            ).values('date').annotate(total=Sum('amount')).order_by('date')
            
            expense_data = Transaction.objects.filter(
                type='expense',
                date__gte=start_date,
                date__lte=end_date
            ).values('date').annotate(total=Sum('amount')).order_by('date')
            
            # Conversion en format pour le graphique
            income_series = {item['date'].strftime('%Y-%m-%d'): item['total'] for item in income_data}
            expense_series = {item['date'].strftime('%Y-%m-%d'): item['total'] for item in expense_data}
            
            # Créer une liste de toutes les dates dans la période
            date_labels = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                          for i in range(days)]
        else:
            # Pour les périodes plus longues, implémenter une logique d'agrégation par semaine/mois
            # Cette logique dépendra de votre ORM et de votre SGBD
            # Exemple simplifié:
            income_series = {}
            expense_series = {}
            date_labels = []
            # Logique d'agrégation...
        
        # Compléter les séries avec des zéros pour les dates sans données
        for date_str in date_labels:
            if date_str not in income_series:
                income_series[date_str] = 0
            if date_str not in expense_series:
                expense_series[date_str] = 0
                
        # Préparer les séries finales pour le graphique
        income_values = [income_series.get(date_str, 0) for date_str in date_labels]
        expense_values = [expense_series.get(date_str, 0) for date_str in date_labels]
        
        return {
            'labels': date_labels,
            'income': income_values,
            'expense': expense_values,
            'grouping': grouping
        }
    
    def _get_category_data(self, start_date, end_date):
        """Prépare les données pour le graphique des catégories."""
        # Revenus par catégorie
        income_by_category = Transaction.objects.filter(
            type='income',
            date__gte=start_date,
            date__lte=end_date,
            category__isnull=False
        ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
        
        # Dépenses par catégorie
        expense_by_category = Transaction.objects.filter(
            type='expense',
            date__gte=start_date,
            date__lte=end_date,
            category__isnull=False
        ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
        
        # Limiter Ã  un nombre raisonnable de catégories pour le graphique
        income_categories = list(income_by_category[:10])
        expense_categories = list(expense_by_category[:10])
        
        return {
            'income': income_categories,
            'expense': expense_categories
        }


class FinancialReportView(LoginRequiredMixin, TemplateView):
    """Vue pour les rapports financiers."""
    template_name = 'finances/reports/index.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérification personnalisée pour autoriser les rÃ´les spécifiques
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Les superusers et staff peuvent toujours accéder
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        
        # Permission explicite dans Django
        if request.user.has_perm('finances.view_reports'):
            return super().dispatch(request, *args, **kwargs)
            
        # Vérifier les rÃ´les utilisateur
        if hasattr(request.user, 'userprofile'):
            # Autoriser les rÃ´les administratifs pour les rapports
            allowed_roles = ['federation_admin', 'club_admin', 'club_owner', 'club_manager', 'coach']
            if request.user.userprofile.role in allowed_roles:
                return super().dispatch(request, *args, **kwargs)
        
        # Rediriger vers le tableau de bord si aucune permission
        from django.contrib import messages
        from django.utils.translation import gettext_lazy as _
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder aux rapports financiers."))
        return redirect('finances:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        # Forcer la permission de voir les rapports car nous avons déjÃ  vérifié l'accès
        permissions['can_view_reports'] = True
            
        context['permissions'] = permissions
        
        # Type de rapport
        report_type = self.request.GET.get('type', 'income_expense')
        context['report_type'] = report_type
        
        # Périodes pour le rapport
        today = timezone.now().date()
        
        # Période par défaut: mois en cours
        start_date = date(today.year, today.month, 1)
        end_date = today
        
        # Changer la période selon les paramètres
        period = self.request.GET.get('period', 'month')
        if period == '30days':
            start_date = today - timedelta(days=30)
        elif period == '90days':
            start_date = today - timedelta(days=90)
        elif period == 'ytd':
            start_date = date(today.year, 1, 1)
        elif period == 'prev_month':
            last_month = today - relativedelta(months=1)
            start_date = date(last_month.year, last_month.month, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
        elif period == 'year':
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        elif period == 'prev_year':
            start_date = date(today.year-1, 1, 1)
            end_date = date(today.year-1, 12, 31)
        elif period == 'custom':
            try:
                start_date = timezone.datetime.strptime(
                    self.request.GET.get('start_date', ''), 
                    '%Y-%m-%d'
                ).date()
                end_date = timezone.datetime.strptime(
                    self.request.GET.get('end_date', ''), 
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                # En cas d'erreur, revenir Ã  la période par défaut
                pass
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['period'] = period
        
        # Générer le rapport selon le type
        if report_type == 'income_expense':
            context.update(self._generate_income_expense_report(start_date, end_date))
        elif report_type == 'balance_sheet':
            context.update(self._generate_balance_sheet(end_date))
        elif report_type == 'cash_flow':
            context.update(self._generate_cash_flow_report(start_date, end_date))
        elif report_type == 'invoices':
            context.update(self._generate_invoice_report(start_date, end_date))
            
        return context
    
    def _generate_income_expense_report(self, start_date, end_date):
        """Génère un rapport de revenus et dépenses."""
        # Transactions dans la période
        transactions = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Revenus par catégorie
        income_by_category = transactions.filter(
            type='income'
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Dépenses par catégorie
        expense_by_category = transactions.filter(
            type='expense'
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Totaux
        total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        net_result = total_income - total_expense
        
        return {
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_result': net_result
        }
    
    def _generate_balance_sheet(self, end_date):
        """Génère un bilan financier Ã  une date donnée."""
        # Comptes financiers
        accounts = FinancialAccount.objects.filter(is_active=True)
        
        # Actifs
        assets = accounts.filter(
            account_type__in=['cash', 'bank', 'investment', 'receivable']
        )
        
        # Passifs
        liabilities = accounts.filter(
            account_type__in=['payable', 'loan', 'credit']
        )
        
        # Capitaux propres
        equity = accounts.filter(
            account_type='equity'
        )
        
        # Totaux
        total_assets = sum(account.balance for account in assets)
        total_liabilities = sum(account.balance for account in liabilities)
        total_equity = sum(account.balance for account in equity)
        
        # Vérification de l'équilibre
        balance_check = total_assets - (total_liabilities + total_equity)
        
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'balance_check': balance_check
        }
    
    def _generate_cash_flow_report(self, start_date, end_date):
        """Génère un rapport de flux de trésorerie."""
        # Comptes liquides (caisse, banque)
        cash_accounts = FinancialAccount.objects.filter(
            type__in=['cash', 'bank'],
            is_active=True
        )
        
        # Entrées de trésorerie
        cash_inflows = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            financial_account__type__in=['cash', 'bank'],
            type='income'
        )
        
        # Sorties de trésorerie
        cash_outflows = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            financial_account__type__in=['cash', 'bank'],
            type='expense'
        )
        
        # Solde initial et final
        initial_balance = sum(account.get_balance_at_date(start_date - timedelta(days=1)) 
                             for account in cash_accounts)
        final_balance = sum(account.balance for account in cash_accounts)
        
        # Flux nets
        total_inflows = cash_inflows.aggregate(Sum('amount'))['amount__sum'] or 0
        total_outflows = cash_outflows.aggregate(Sum('amount'))['amount__sum'] or 0
        net_cash_flow = total_inflows - total_outflows
        
        # Détail par catégorie
        inflows_by_category = cash_inflows.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        outflows_by_category = cash_outflows.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        return {
            'cash_accounts': cash_accounts,
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_inflows': total_inflows,
            'total_outflows': total_outflows,
            'net_cash_flow': net_cash_flow,
            'inflows_by_category': inflows_by_category,
            'outflows_by_category': outflows_by_category
        }
    
    def _generate_invoice_report(self, start_date, end_date):
        """Génère un rapport sur les factures."""
        # Factures dans la période
        invoices = Invoice.objects.filter(
            issued_date__gte=start_date,
            issued_date__lte=end_date
        )
        
        # Statistiques générales
        invoice_count = invoices.count()
        total_amount = invoices.aggregate(Sum('total'))['total__sum'] or 0
        paid_count = invoices.filter(status='paid').count()
        paid_amount = invoices.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0
        unpaid_count = invoices.filter(status='unpaid').count()
        unpaid_amount = invoices.filter(status='unpaid').aggregate(Sum('total'))['total__sum'] or 0
        
        # Taux de paiement
        payment_rate = (paid_count / invoice_count * 100) if invoice_count > 0 else 0
        
        # Ã‚ge moyen des factures impayées
        today = timezone.now().date()
        unpaid_invoices = invoices.filter(status='unpaid')
        total_age_days = sum((today - invoice.issued_date).days for invoice in unpaid_invoices)
        avg_age = total_age_days / unpaid_count if unpaid_count > 0 else 0
        
        # Répartition des factures par tranche d'Ã¢ge
        age_ranges = {
            '0_30': unpaid_invoices.filter(issued_date__gte=today-timedelta(days=30)).count(),
            '31_60': unpaid_invoices.filter(issued_date__lt=today-timedelta(days=30), 
                                          issued_date__gte=today-timedelta(days=60)).count(),
            '61_90': unpaid_invoices.filter(issued_date__lt=today-timedelta(days=60), 
                                          issued_date__gte=today-timedelta(days=90)).count(),
            'over_90': unpaid_invoices.filter(issued_date__lt=today-timedelta(days=90)).count(),
        }
        
        return {
            'invoice_count': invoice_count,
            'total_amount': total_amount,
            'paid_count': paid_count,
            'paid_amount': paid_amount,
            'unpaid_count': unpaid_count,
            'unpaid_amount': unpaid_amount,
            'payment_rate': payment_rate,
            'avg_age': avg_age,
            'age_ranges': age_ranges,
            'unpaid_invoices': unpaid_invoices
        }
