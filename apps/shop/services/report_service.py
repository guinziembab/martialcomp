import datetime
import calendar
from decimal import Decimal
from django.db.models import Sum, Count, Avg, F, Q, Window
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, ExtractYear
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models.order import Order, OrderItem
from ..models.payment import Payment


class ReportService:
    """
    Service for generating sales and analytics reports
    """
    
    @classmethod
    def get_sales_summary(cls, entity=None, start_date=None, end_date=None):
        """
        Get summary of sales for a given entity (club or federation) and date range
        
        Args:
            entity: Club or Federation object (optional)
            start_date: Start date for the report (optional)
            end_date: End date for the report (optional)
            
        Returns:
            Dictionary with sales summary data
        """
        # Base queryset
        orders_qs = Order.objects.filter(status__in=['paid', 'shipped', 'delivered'])
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                orders_qs = orders_qs.filter(club=entity)
            elif hasattr(entity, 'website'):  # Federation
                orders_qs = orders_qs.filter(federation=entity)
        
        # Filter by date
        if start_date:
            orders_qs = orders_qs.filter(created_at__gte=start_date)
        if end_date:
            # Include the entire end date by setting time to 23:59:59
            end_of_day = datetime.datetime.combine(end_date, datetime.time.max)
            orders_qs = orders_qs.filter(created_at__lte=end_of_day)
        
        # Calculate summary metrics
        total_orders = orders_qs.count()
        total_sales = orders_qs.aggregate(
            total=Sum('total', default=Decimal('0.00'))
        )['total']
        
        avg_order_value = Decimal('0.00')
        if total_orders > 0:
            avg_order_value = total_sales / total_orders
        
        # Get total items sold
        items_sold = OrderItem.objects.filter(order__in=orders_qs).aggregate(
            total=Sum('quantity', default=0)
        )['total']
        
        # Calculate discounts given
        total_discounts = orders_qs.aggregate(
            total=Sum('discount_amount', default=Decimal('0.00'))
        )['total']
        
        return {
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_sales_display': f"{total_sales} â‚¬",
            'avg_order_value': avg_order_value,
            'avg_order_value_display': f"{avg_order_value} â‚¬",
            'items_sold': items_sold,
            'total_discounts': total_discounts,
            'total_discounts_display': f"{total_discounts} â‚¬",
        }
    
    @classmethod
    def get_sales_over_time(cls, entity=None, period='daily', start_date=None, end_date=None):
        """
        Get sales data over time
        
        Args:
            entity: Club or Federation object (optional)
            period: 'daily', 'weekly', or 'monthly'
            start_date: Start date for the report (optional)
            end_date: End date for the report (optional)
            
        Returns:
            Dictionary with dates and corresponding sales data
        """
        # Set default dates if not provided
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            if period == 'daily':
                # Last 30 days by default
                start_date = end_date - datetime.timedelta(days=29)
            elif period == 'weekly':
                # Last 12 weeks by default
                start_date = end_date - datetime.timedelta(weeks=11)
            elif period == 'monthly':
                # Last 12 months by default
                start_date = end_date.replace(month=end_date.month - 11) if end_date.month > 11 else \
                            end_date.replace(year=end_date.year - 1, month=end_date.month + 1)
        
        # Base queryset
        orders_qs = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered'],
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                orders_qs = orders_qs.filter(club=entity)
            elif hasattr(entity, 'website'):  # Federation
                orders_qs = orders_qs.filter(federation=entity)
        
        # Group by date period
        date_trunc = TruncDate('created_at')
        if period == 'weekly':
            date_trunc = TruncWeek('created_at')
        elif period == 'monthly':
            date_trunc = TruncMonth('created_at')
        
        sales_data = orders_qs.annotate(
            date=date_trunc
        ).values('date').annotate(
            total_sales=Sum('total', default=Decimal('0.00')),
            order_count=Count('id')
        ).order_by('date')
        
        # Convert to format suitable for charts
        dates = []
        sales = []
        orders = []
        
        # Create a dictionary to hold data by date
        data_by_date = {item['date']: {
            'total_sales': item['total_sales'],
            'order_count': item['order_count']
        } for item in sales_data}
        
        # Fill in missing dates with zeros
        current_date = start_date
        while current_date <= end_date:
            if period == 'daily':
                date_key = current_date
                dates.append(current_date.strftime('%d/%m'))
                current_date += datetime.timedelta(days=1)
            elif period == 'weekly':
                # Get the first day of the week
                date_key = current_date - datetime.timedelta(days=current_date.weekday())
                dates.append(date_key.strftime('%d/%m'))
                current_date += datetime.timedelta(weeks=1)
            elif period == 'monthly':
                # Get the first day of the month
                date_key = current_date.replace(day=1)
                dates.append(date_key.strftime('%m/%Y'))
                # Move to the first day of the next month
                next_month = current_date.month + 1 if current_date.month < 12 else 1
                next_year = current_date.year if current_date.month < 12 else current_date.year + 1
                current_date = current_date.replace(year=next_year, month=next_month, day=1)
            
            # Add data or zeros
            if date_key in data_by_date:
                sales.append(float(data_by_date[date_key]['total_sales']))
                orders.append(data_by_date[date_key]['order_count'])
            else:
                sales.append(0)
                orders.append(0)
        
        return {
            'dates': dates,
            'sales': sales,
            'orders': orders
        }
    
    @classmethod
    def get_top_products(cls, entity=None, limit=10, start_date=None, end_date=None):
        """
        Get the top selling products
        
        Args:
            entity: Club or Federation object (optional)
            limit: Number of products to return
            start_date: Start date for the report (optional)
            end_date: End date for the report (optional)
            
        Returns:
            List of dictionaries with product data
        """
        # Base queryset for orders
        orders_qs = Order.objects.filter(status__in=['paid', 'shipped', 'delivered'])
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                orders_qs = orders_qs.filter(club=entity)
            elif hasattr(entity, 'website'):  # Federation
                orders_qs = orders_qs.filter(federation=entity)
        
        # Filter by date
        if start_date:
            orders_qs = orders_qs.filter(created_at__date__gte=start_date)
        if end_date:
            orders_qs = orders_qs.filter(created_at__date__lte=end_date)
        
        # Get OrderItems for these orders
        items_qs = OrderItem.objects.filter(order__in=orders_qs)
        
        # Group by product
        top_products = items_qs.values(
            'product_id', 'product_name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_quantity')[:limit]
        
        return list(top_products)
    
    @classmethod
    def get_sales_by_category(cls, entity=None, start_date=None, end_date=None):
        """
        Get sales data grouped by product category
        
        Args:
            entity: Club or Federation object (optional)
            start_date: Start date for the report (optional)
            end_date: End date for the report (optional)
            
        Returns:
            Dictionary with category data
        """
        # Base queryset for orders
        orders_qs = Order.objects.filter(status__in=['paid', 'shipped', 'delivered'])
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                orders_qs = orders_qs.filter(club=entity)
            elif hasattr(entity, 'website'):  # Federation
                orders_qs = orders_qs.filter(federation=entity)
        
        # Filter by date
        if start_date:
            orders_qs = orders_qs.filter(created_at__date__gte=start_date)
        if end_date:
            orders_qs = orders_qs.filter(created_at__date__lte=end_date)
        
        # Get OrderItems for these orders
        items_qs = OrderItem.objects.filter(order__in=orders_qs)
        
        # Group by category
        categories_data = items_qs.values(
            'category_id', 'category_name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_revenue')
        
        # Prepare data for charts
        category_names = []
        category_sales = []
        
        for category in categories_data:
            category_names.append(category['category_name'] or _('Sans catégorie'))
            category_sales.append(float(category['total_revenue']))
        
        return {
            'category_names': category_names,
            'category_sales': category_sales
        }
    
    @classmethod
    def get_payment_methods_breakdown(cls, entity=None, start_date=None, end_date=None):
        """
        Get breakdown of sales by payment method
        
        Args:
            entity: Club or Federation object (optional)
            start_date: Start date for the report (optional)
            end_date: End date for the report (optional)
            
        Returns:
            Dictionary with payment method data
        """
        # Base queryset for payments
        payments_qs = Payment.objects.filter(status='completed')
        
        # Join to orders and apply filters
        if entity or start_date or end_date:
            payments_qs = payments_qs.select_related('order')
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                payments_qs = payments_qs.filter(order__club=entity)
            elif hasattr(entity, 'website'):  # Federation
                payments_qs = payments_qs.filter(order__federation=entity)
        
        # Filter by date
        if start_date:
            payments_qs = payments_qs.filter(created_at__date__gte=start_date)
        if end_date:
            payments_qs = payments_qs.filter(created_at__date__lte=end_date)
        
        # Group by payment method
        payment_data = payments_qs.values(
            'payment_method__name', 'payment_method__payment_type'
        ).annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        # Prepare data
        method_names = []
        method_amounts = []
        method_counts = []
        
        for method in payment_data:
            method_names.append(method['payment_method__name'])
            method_amounts.append(float(method['total_amount']))
            method_counts.append(method['count'])
        
        return {
            'method_names': method_names,
            'method_amounts': method_amounts,
            'method_counts': method_counts
        }
    
    @classmethod
    def get_customer_retention(cls, entity=None, months=6):
        """
        Get customer retention data
        
        Args:
            entity: Club or Federation object (optional)
            months: Number of months to analyze
            
        Returns:
            Dictionary with retention data
        """
        today = timezone.now().date()
        
        # Calculate start date (first day of month, N months ago)
        first_month = today.replace(day=1)
        for _ in range(months - 1):
            # Go back one more month
            if first_month.month == 1:
                first_month = first_month.replace(year=first_month.year - 1, month=12)
            else:
                first_month = first_month.replace(month=first_month.month - 1)
        
        # Base queryset for orders
        orders_qs = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered'],
            created_at__date__gte=first_month
        )
        
        # Filter by entity
        if entity:
            if hasattr(entity, 'club_type'):  # Club
                orders_qs = orders_qs.filter(club=entity)
            elif hasattr(entity, 'website'):  # Federation
                orders_qs = orders_qs.filter(federation=entity)
        
        # Group by month and user
        new_customers_by_month = {}
        returning_customers_by_month = {}
        
        # Get all customers who have placed orders before the analysis period
        existing_customers = set(orders_qs.filter(
            created_at__date__lt=first_month
        ).values_list('user_id', flat=True))
        
        # Analyze each month
        current_month = first_month
        month_labels = []
        
        while current_month <= today.replace(day=1):
            month_label = current_month.strftime('%m/%Y')
            month_labels.append(month_label)
            
            # Get orders for this month
            month_end = cls._get_month_end(current_month)
            month_orders = orders_qs.filter(
                created_at__date__gte=current_month,
                created_at__date__lte=month_end
            )
            
            # Count distinct customers this month
            month_customers = set(month_orders.values_list('user_id', flat=True))
            
            # New customers = not in existing customers set
            new_customers = len(month_customers - existing_customers)
            new_customers_by_month[month_label] = new_customers
            
            # Returning customers = in existing customers set
            returning_customers = len(month_customers & existing_customers)
            returning_customers_by_month[month_label] = returning_customers
            
            # Update existing customers for next month
            existing_customers.update(month_customers)
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Prepare arrays for charting
        new_customers_data = [new_customers_by_month.get(month, 0) for month in month_labels]
        returning_customers_data = [returning_customers_by_month.get(month, 0) for month in month_labels]
        
        return {
            'months': month_labels,
            'new_customers': new_customers_data,
            'returning_customers': returning_customers_data
        }
    
    @staticmethod
    def _get_month_end(date):
        """Helper to get the last day of a month"""
        month_last_day = calendar.monthrange(date.year, date.month)[1]
        return date.replace(day=month_last_day)
