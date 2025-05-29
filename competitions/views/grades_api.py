"""
API pour la gestion des grades dans le système - Fichier de redirection.
Ce fichier redirige les anciennes vues vers la nouvelle application grades.
"""
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET

import logging

# Configurer le logger
logger = logging.getLogger(__name__)

@login_required
@require_POST
def get_grades_by_disciplines(request):
    """
    Redirection vers la nouvelle API dans l'application grades.
    """
    logger.info("Redirection de l'ancienne API get_grades_by_disciplines vers la nouvelle application")
    return HttpResponseRedirect(reverse('grades:api:get_grades_by_disciplines'))

@login_required
@require_GET
def get_grades_by_discipline(request, discipline_id):
    """
    Redirection vers la nouvelle API dans l'application grades.
    """
    logger.info(f"Redirection de l'ancienne API get_grades_by_discipline pour discipline {discipline_id} vers la nouvelle application")
    return HttpResponseRedirect(reverse('grades:api:get_grades_by_discipline', kwargs={'discipline_id': discipline_id}))

@login_required
@require_POST
def create_grade_for_discipline(request):
    """
    Redirection vers la nouvelle API dans l'application grades.
    """
    logger.info("Redirection de l'ancienne API create_grade_for_discipline vers la nouvelle application")
    return HttpResponseRedirect(reverse('grades:api:create_grade_for_discipline'))