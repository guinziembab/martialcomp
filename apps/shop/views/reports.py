from django.core.exceptions import PermissionDenied
import datetime
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from apps.competitions.utils.decorators import club_required, federation_required
from ..services.report_service import ReportService
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
@club_required
def club_reports_dashboard(request):
    """
    Dashboard view for club sales reports
    """
    # Get date range from query params
    today = timezone.now().date()
    
    # Default to last 30 days
    end_date = today
    start_date = end_date - datetime.timedelta(days=29)
    
    # Check query params
    period = request.GET.get('period', '30')
    if period == '7':
        start_date = end_date - datetime.timedelta(days=6)
    elif period == '90':
        start_date = end_date - datetime.timedelta(days=89)
    elif period == 'month':
        start_date = end_date.replace(day=1)
    elif period == 'year':
        start_date = end_date.replace(month=1, day=1)
    elif period == 'custom':
        try:
            start_date = datetime.datetime.strptime(
                request.GET.get('start_date', ''), '%Y-%m-%d'
            ).date()
            end_date = datetime.datetime.strptime(
                request.GET.get('end_date', ''), '%Y-%m-%d'
            ).date()
        except ValueError:
            # Invalid date format, fall back to default
            pass
    
    # Get reports data
    sales_summary = ReportService.get_sales_summary(
        entity=request.club, 
        start_date=start_date,
        end_date=end_date
    )
    
    sales_over_time = ReportService.get_sales_over_time(
        entity=request.club,
        period='daily' if (end_date - start_date).days <= 31 else 'weekly',
        start_date=start_date,
        end_date=end_date
    )
    
    top_products = ReportService.get_top_products(
        entity=request.club,
        limit=5,
        start_date=start_date,
        end_date=end_date
    )
    
    sales_by_category = ReportService.get_sales_by_category(
        entity=request.club,
        start_date=start_date,
        end_date=end_date
    )
    
    payment_methods = ReportService.get_payment_methods_breakdown(
        entity=request.club,
        start_date=start_date,
        end_date=end_date
    )
    
    # Prepare context
    context = {
        'sales_summary': sales_summary,
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'active_tab': 'reports',
        
        # Chart data
        'chart_labels': json.dumps(sales_over_time['dates']),
        'sales_data': json.dumps(sales_over_time['sales']),
        'orders_data': json.dumps(sales_over_time['orders']),
        
        'category_labels': json.dumps(sales_by_category['category_names']),
        'category_data': json.dumps(sales_by_category['category_sales']),
        
        'payment_method_labels': json.dumps(payment_methods['method_names']),
        'payment_method_data': json.dumps(payment_methods['method_amounts']),
    }
    
    return render(request, 'shop/dashboard/reports/dashboard.html', context)


@login_required
@club_required
def club_report_products(request):
    """
    Detailed product sales report for clubs
    """
    # Get date range from query params
    today = timezone.now().date()
    end_date = today
    start_date = end_date - datetime.timedelta(days=29)  # Default to last 30 days
    
    # Check query params for custom date range
    if 'start_date' in request.GET and 'end_date' in request.GET:
        try:
            start_date = datetime.datetime.strptime(
                request.GET.get('start_date', ''), '%Y-%m-%d'
            ).date()
            end_date = datetime.datetime.strptime(
                request.GET.get('end_date', ''), '%Y-%m-%d'
            ).date()
        except ValueError:
            # Invalid date format, fall back to default
            pass
    
    # Get top products with more details
    top_products = ReportService.get_top_products(
        entity=request.club,
        limit=50,  # Show more products in the detailed report
        start_date=start_date,
        end_date=end_date
    )
    
    context = {
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
        'active_tab': 'reports',
    }
    
    return render(request, 'shop/dashboard/reports/products.html', context)


@login_required
@club_required
def club_report_categories(request):
    """
    Detailed category sales report for clubs
    """
    # Get date range from query params
    today = timezone.now().date()
    end_date = today
    start_date = end_date - datetime.timedelta(days=29)  # Default to last 30 days
    
    # Check query params for custom date range
    if 'start_date' in request.GET and 'end_date' in request.GET:
        try:
            start_date = datetime.datetime.strptime(
                request.GET.get('start_date', ''), '%Y-%m-%d'
            ).date()
            end_date = datetime.datetime.strptime(
                request.GET.get('end_date', ''), '%Y-%m-%d'
            ).date()
        except ValueError:
            # Invalid date format, fall back to default
            pass
    
    # Get sales by category
    sales_by_category = ReportService.get_sales_by_category(
        entity=request.club,
        start_date=start_date,
        end_date=end_date
    )
    
    context = {
        'category_names': sales_by_category['category_names'],
        'category_sales': sales_by_category['category_sales'],
        'start_date': start_date,
        'end_date': end_date,
        'active_tab': 'reports',
        
        # Chart data
        'category_labels': json.dumps(sales_by_category['category_names']),
        'category_data': json.dumps(sales_by_category['category_sales']),
    }
    
    return render(request, 'shop/dashboard/reports/categories.html', context)


@login_required
@club_required
def club_report_customers(request):
    """
    Customer analysis report for clubs
    """
    # Get retention data
    customer_retention = ReportService.get_customer_retention(
        entity=request.club,
        months=6  # Analyze last 6 months
    )
    
    context = {
        'active_tab': 'reports',
        'months': customer_retention['months'],
        'new_customers': customer_retention['new_customers'],
        'returning_customers': customer_retention['returning_customers'],
        
        # Chart data
        'months_labels': json.dumps(customer_retention['months']),
        'new_customers_data': json.dumps(customer_retention['new_customers']),
        'returning_customers_data': json.dumps(customer_retention['returning_customers']),
    }
    
    return render(request, 'shop/dashboard/reports/customers.html', context)


@login_required
@club_required
def club_export_report(request, report_type):
    """
    Export report data as CSV
    """
    # Get date range from query params
    today = timezone.now().date()
    end_date = today
    start_date = end_date - datetime.timedelta(days=29)  # Default to last 30 days
    
    # Check query params for custom date range
    if 'start_date' in request.GET and 'end_date' in request.GET:
        try:
            start_date = datetime.datetime.strptime(
                request.GET.get('start_date', ''), '%Y-%m-%d'
            ).date()
            end_date = datetime.datetime.strptime(
                request.GET.get('end_date', ''), '%Y-%m-%d'
            ).date()
        except ValueError:
            # Invalid date format, fall back to default
            pass
    
    # Prepare CSV content based on report type
    if report_type == 'products':
        top_products = ReportService.get_top_products(
            entity=request.club,
            limit=1000,  # No practical limit for CSV export
            start_date=start_date,
            end_date=end_date
        )
        
        csv_content = "ID Produit,Nom du produit,Quantité vendue,Chiffre d'affaires\n"
        for product in top_products:
            csv_content += f"{product['product_id']},{product['product_name']},{product['total_quantity']},{product['total_revenue']}\n"
        
        filename = f"produits_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    
    elif report_type == 'categories':
        sales_by_category = ReportService.get_sales_by_category(
            entity=request.club,
            start_date=start_date,
            end_date=end_date
        )
        
        csv_content = "Catégorie,Chiffre d'affaires\n"
        for i, category in enumerate(sales_by_category['category_names']):
            csv_content += f"{category},{sales_by_category['category_sales'][i]}\n"
        
        filename = f"categories_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    
    else:
        return HttpResponse("Type de rapport invalide", status=400)
    
    # Create response with CSV content
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# Federation report views (similar to club views but for federations)

@login_required
@federation_required
def federation_reports_dashboard(request):
    """
    Dashboard view for federation sales reports
    """
    # Get date range from query params
    today = timezone.now().date()
    
    # Default to last 30 days
    end_date = today
    start_date = end_date - datetime.timedelta(days=29)
    
    # Check query params
    period = request.GET.get('period', '30')
    if period == '7':
        start_date = end_date - datetime.timedelta(days=6)
    elif period == '90':
        start_date = end_date - datetime.timedelta(days=89)
    elif period == 'month':
        start_date = end_date.replace(day=1)
    elif period == 'year':
        start_date = end_date.replace(month=1, day=1)
    elif period == 'custom':
        try:
            start_date = datetime.datetime.strptime(
                request.GET.get('start_date', ''), '%Y-%m-%d'
            ).date()
            end_date = datetime.datetime.strptime(
                request.GET.get('end_date', ''), '%Y-%m-%d'
            ).date()
        except ValueError:
            # Invalid date format, fall back to default
            pass
    
    # Get reports data
    sales_summary = ReportService.get_sales_summary(
        entity=request.federation, 
        start_date=start_date,
        end_date=end_date
    )
    
    sales_over_time = ReportService.get_sales_over_time(
        entity=request.federation,
        period='daily' if (end_date - start_date).days <= 31 else 'weekly',
        start_date=start_date,
        end_date=end_date
    )
    
    top_products = ReportService.get_top_products(
        entity=request.federation,
        limit=5,
        start_date=start_date,
        end_date=end_date
    )
    
    sales_by_category = ReportService.get_sales_by_category(
        entity=request.federation,
        start_date=start_date,
        end_date=end_date
    )
    
    payment_methods = ReportService.get_payment_methods_breakdown(
        entity=request.federation,
        start_date=start_date,
        end_date=end_date
    )
    
    # Prepare context
    context = {
        'sales_summary': sales_summary,
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'active_tab': 'reports',
        
        # Chart data
        'chart_labels': json.dumps(sales_over_time['dates']),
        'sales_data': json.dumps(sales_over_time['sales']),
        'orders_data': json.dumps(sales_over_time['orders']),
        
        'category_labels': json.dumps(sales_by_category['category_names']),
        'category_data': json.dumps(sales_by_category['category_sales']),
        
        'payment_method_labels': json.dumps(payment_methods['method_names']),
        'payment_method_data': json.dumps(payment_methods['method_amounts']),
    }
    
    return render(request, 'shop/dashboard/reports/dashboard.html', context)

