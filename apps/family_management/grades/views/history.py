from django.core.exceptions import PermissionDenied
"""
Module pour la gestion de l'historique des grades des pratiquants.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from apps.competitions.models import Practitioner
from apps.grades.models import PractitionerGrade
from apps.grades.utils import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def practitioner_grade_history(request, practitioner_id):
    """
    Affiche l'historique des grades d'un pratiquant spécifique.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
    
    # Récupérer l'historique des grades
    # Correction : 'obtained_date' -> 'date_obtained'
    grade_history = PractitionerGrade.objects.filter(
        practitioner=practitioner
    ).order_by('-date_obtained')
    
    # Récupérer les disciplines du pratiquant
    practitioner_disciplines = practitioner.disciplines.all()
    
    return render(request, 'grades/history.html', {
        'practitioner': practitioner,
        'grade_history': grade_history,
        'club': club,
        'disciplines': practitioner_disciplines,
    })

@login_required
def export_grade_history(request, practitioner_id, format='pdf'):
    """
    Exporte l'historique des grades d'un pratiquant au format PDF ou Excel.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le pratiquant
    practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=organization)
    
    # Récupérer l'historique des grades
    # Correction : 'obtained_date' -> 'date_obtained'
    grade_history = PractitionerGrade.objects.filter(
        practitioner=practitioner
    ).order_by('-date_obtained')
    
    if format == 'pdf':
        # Logique pour générer le PDF (utiliser une bibliothèque comme ReportLab ou WeasyPrint)
        try:
            from apps.grades.utils.pdf import generate_grade_history_pdf
            response = generate_grade_history_pdf(practitioner, grade_history)
            return response
        except ImportError:
            messages.warning(request, _("La génération de PDF n'est pas disponible."))
            return redirect('grades:practitioner_history', practitioner_id=practitioner_id)
    
    elif format == 'excel':
        # Logique pour générer un fichier Excel
        try:
            from apps.grades.utils.excel import generate_grade_history_excel
            response = generate_grade_history_excel(practitioner, grade_history)
            return response
        except ImportError:
            messages.warning(request, _("L'export Excel n'est pas disponible."))
            return redirect('grades:practitioner_history', practitioner_id=practitioner_id)
    
    else:
        messages.error(request, _("Format d'export non supporté."))
        return redirect('grades:practitioner_history', practitioner_id=practitioner_id)

