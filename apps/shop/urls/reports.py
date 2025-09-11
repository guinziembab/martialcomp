from django.urls import path
from ..views import reports

app_name = 'reports'

urlpatterns = [
    # Club reports
    path('club/', reports.club_reports_dashboard, name='dashboard_reports'),
    path('club/products/', reports.club_report_products, name='dashboard_report_products'),
    path('club/categories/', reports.club_report_categories, name='dashboard_report_categories'),
    path('club/customers/', reports.club_report_customers, name='dashboard_report_customers'),
    path('club/export/<str:report_type>/', reports.club_export_report, name='dashboard_export_report'),
    
    # Federation reports
    path('federation/', reports.federation_reports_dashboard, name='federation_dashboard_reports'),
]