# -*- coding: utf-8 -*-
from django.urls import path
from competitions.views import event_surveys

urlpatterns = [
    # Liste et CRUD pour les sondages
    path('', event_surveys.survey_list, name='survey_list'),
    path('create/', event_surveys.create_survey, name='create_survey'),
    path('<uuid:event_id>/create/', event_surveys.create_survey, name='create_event_survey'),
    path('<uuid:survey_id>/', event_surveys.survey_detail, name='survey_detail'),
    path('<uuid:survey_id>/edit/', event_surveys.edit_survey, name='edit_survey'),
    path('<uuid:survey_id>/toggle/', event_surveys.toggle_survey_status, name='toggle_survey_status'),
    path('<uuid:survey_id>/delete/', event_surveys.delete_survey, name='delete_survey'),
    
    # Réponses aux sondages
    path('response/<uuid:response_id>/', event_surveys.response_detail, name='response_detail'),
    
    # Résultats des sondages
    path('<uuid:survey_id>/results/', event_surveys.survey_results, name='survey_results'),
]