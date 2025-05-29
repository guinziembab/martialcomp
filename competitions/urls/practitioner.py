"""
URL configuration for practitioner functionality
"""
from django.urls import path, include
from competitions.views.practitioner_dashboard import (
    dashboard,
    profile,
    update_profile,
    activities,
    grades,
    grade_progress,
    competitions,
    competition_detail,
    memberships,
    statistics
)
from competitions.views.practitioner_extra import (
    practitioner_orders as order_list,
    practitioner_order_detail as order_detail,
    practitioner_notifications as notifications,
    practitioner_notification_mark_read as mark_notification_read,
    practitioner_notification_preferences as notification_preferences,
    practitioner_support as support_tickets,
    practitioner_create_ticket as create_ticket,
    practitioner_support_detail as ticket_detail,
    practitioner_events as event_list,
    practitioner_event_detail as event_detail,
    practitioner_event_register as event_register,
    practitioner_calendar as calendar_view
)
from competitions.views.practitioner_finance_simplified import (
    finance_dashboard,
    invoice_list,
    invoice_detail,
    payment_list,
    payment_detail,
    transaction_list,
    financial_report
)
from competitions.views.practitioner_training import (
    training_dashboard,
    training_schedule,
    make_reservation,
    cancel_reservation,
    attendance_history,
    program_list,
    program_detail,
    program_enroll,
    training_progress
)

app_name = 'practitioner'

urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),
    
    # Profile
    path('profile/', profile, name='profile'),
    path('profile/update/', update_profile, name='update_profile'),
    
    # Activities
    path('activities/', activities, name='activities'),
    
    # Grades
    path('grades/', grades, name='grades'),
    path('grades/progress/', grade_progress, name='grade_progress'),
    
    # Competitions
    path('competitions/', competitions, name='competitions'),
    path('competitions/<str:competition_id>/', competition_detail, name='competition_detail'),
    
    # Memberships
    path('memberships/', memberships, name='memberships'),
    
    # Statistics
    path('statistics/', statistics, name='statistics'),
    path('statistics/<int:year>/', statistics, name='statistics_year'),
    
    # Orders
    path('orders/', order_list, name='order_list'),
    path('orders/<str:order_id>/', order_detail, name='order_detail'),
    
    # Notifications
    path('notifications/', notifications, name='notifications'),
    path('notifications/read/<str:notification_id>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/preferences/', notification_preferences, name='notification_preferences'),
    
    # Support
    path('support/', support_tickets, name='support_tickets'),
    path('support/create/', create_ticket, name='create_ticket'),
    path('support/ticket/<str:ticket_id>/', ticket_detail, name='ticket_detail'),
    
    # Events
    path('events/', event_list, name='event_list'),
    path('events/<str:event_id>/', event_detail, name='event_detail'),
    path('events/<str:event_id>/register/', event_register, name='event_register'),
    
    # Calendar
    path('calendar/', calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', calendar_view, name='calendar_month'),
    
    # Finance
    path('finance/', finance_dashboard, name='finance_dashboard'),
    path('finance/invoices/', invoice_list, name='invoice_list'),
    path('finance/invoices/<str:invoice_id>/', invoice_detail, name='invoice_detail'),
    path('finance/payments/', payment_list, name='payment_list'),
    path('finance/payments/<str:payment_id>/', payment_detail, name='payment_detail'),
    path('finance/transactions/', transaction_list, name='transaction_list'),
    path('finance/reports/<int:year>/', financial_report, name='financial_report'),
    
    # Training
    path('training/', training_dashboard, name='training_dashboard'),
    path('training/schedule/', training_schedule, name='training_schedule'),
    path('training/schedule/<int:month>/<int:year>/', training_schedule, name='training_schedule_date'),
    path('training/reservation/<str:slot_id>/', make_reservation, name='make_reservation'),
    path('training/reservation/<str:reservation_id>/cancel/', cancel_reservation, name='cancel_reservation'),
    path('training/attendance/', attendance_history, name='attendance_history'),
    path('training/programs/', program_list, name='program_list'),
    path('training/programs/<str:program_id>/', program_detail, name='program_detail'),
    path('training/programs/<str:program_id>/enroll/', program_enroll, name='program_enroll'),
    path('training/progress/', training_progress, name='training_progress'),
]