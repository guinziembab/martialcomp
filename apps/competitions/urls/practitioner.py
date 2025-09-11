from django.urls import path
from apps.competitions.views.practitioner_dashboard import dashboard
from apps.competitions.views.practitioner_extra import (
    practitioner_events, practitioner_calendar, practitioner_notifications, practitioner_support,
    practitioner_create_ticket, practitioner_support_detail, practitioner_notification_mark_read,
    practitioner_event_detail, practitioner_event_register, practitioner_calendar_api
)
from apps.competitions.views.practitioner_finance import (
    practitioner_finance_dashboard, practitioner_invoices, practitioner_invoice_detail, 
    practitioner_payments, practitioner_transactions
)
from apps.competitions.views.practitioner_training import (
    training_dashboard, practitioner_training_schedule,
    attendance_history, program_list, training_progress, 
    make_reservation, cancel_reservation, program_detail, 
    program_enroll, practitioner_training_calendar_api
)

app_name = 'practitioner'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', dashboard, name='dashboard'),
    path('', dashboard, name='dashboard'),  # Alias
    
    # Ã‰vénements et calendrier
    path('events/', practitioner_events, name='events'),
    path('events/<int:event_id>/', practitioner_event_detail, name='event_detail'),
    path('events/<int:event_id>/register/', practitioner_event_register, name='event_register'),
    path('calendar/', practitioner_calendar, name='calendar'),
    path('calendar/<int:year>/<int:month>/', practitioner_calendar, name='calendar_month'),
    path('calendar/api/', practitioner_calendar_api, name='calendar_api'),
    
    # Notifications
    path('notifications/', practitioner_notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', practitioner_notification_mark_read, name='mark_notification_read'),
    
    # Finance
    path('finance/', practitioner_finance_dashboard, name='finance_dashboard'),
    path('finance/invoices/', practitioner_invoices, name='invoice_list'),
    path('finance/invoices/<int:invoice_id>/', practitioner_invoice_detail, name='invoice_detail'),
    path('finance/payments/', practitioner_payments, name='payment_list'),
    path('finance/transactions/', practitioner_transactions, name='transaction_list'),
    
    # EntraÃ®nement
    path('training/', training_dashboard, name='training_dashboard'),
    path('training/schedule/', practitioner_training_schedule, name='training_schedule'),
    path('training/attendance/', attendance_history, name='attendance_history'),
    path('training/programs/', program_list, name='program_list'), 
    path('training/progress/', training_progress, name='training_progress'),
    path('training/reserve/<int:slot_id>/', make_reservation, name='make_reservation'),
    path('training/cancel/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
    path('training/program/<int:program_id>/', program_detail, name='program_detail'),
    path('training/enroll/<int:program_id>/', program_enroll, name='program_enroll'),
    path('training/calendar-api/', practitioner_training_calendar_api, name='training_calendar_api'),
    
    # Support tickets
    path('support/tickets/', practitioner_support, name='support_tickets'),
    path('support/create/', practitioner_create_ticket, name='create_ticket'),
    path('support/ticket/<int:ticket_id>/', practitioner_support_detail, name='ticket_detail'),
]

