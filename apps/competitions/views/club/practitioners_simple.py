"""
Vue simplifiée pour résoudre les problèmes des pratiquants
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from datetime import date

from apps.competitions.models import Practitioner
from apps.competitions.forms import PractitionerForm

logger = logging.getLogger(__name__)

@login_required
def practitioner_detail_simple(request, pk):
    """Version simplifiée de practitioner_detail sans vérifications complexes"""
    try:
        # Récupérer simplement le pratiquant
        practitioner = get_object_or_404(Practitioner, pk=pk)
        
        # Calculer l'âge si possible
        if practitioner.birth_date:
            today = date.today()
            age = today.year - practitioner.birth_date.year - ((today.month, today.day) < (practitioner.birth_date.month, practitioner.birth_date.day))
            practitioner.computed_age = age
        else:
            practitioner.computed_age = None
            
        # Grade simple
        practitioner.computed_grade_display = practitioner.grade or ''
        
        context = {
            'practitioner': practitioner,
            'page_title': f"Profil de {practitioner.full_name}",
        }
        
        return render(request, 'competitions/club/practitioner_detail.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans practitioner_detail_simple: {str(e)}", exc_info=True)
        messages.error(request, _("Erreur lors du chargement du profil."))
        return redirect('competitions:club:practitioners')


@login_required  
def practitioner_update_simple(request, pk):
    """Version simplifiée de practitioner_update sans vérifications complexes"""
    try:
        # Récupérer simplement le pratiquant
        practitioner = get_object_or_404(Practitioner, pk=pk)
        
        if request.method == 'POST':
            form = PractitionerForm(request.POST, request.FILES, instance=practitioner)
            if form.is_valid():
                practitioner = form.save()
                messages.success(request, _(f"Le profil de {practitioner.full_name} a été mis à jour."))
                return redirect('competitions:club:practitioner_detail', pk=practitioner.pk)
        else:
            form = PractitionerForm(instance=practitioner)
        
        context = {
            'form': form,
            'practitioner': practitioner,
            'page_title': f"Modifier - {practitioner.full_name}",
            'is_edit': True,
            'submit_text': _("Enregistrer les modifications"),
        }
        
        return render(request, 'competitions/club/practitioner_form.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans practitioner_update_simple: {str(e)}", exc_info=True)
        messages.error(request, _(f"Erreur lors de la modification du pratiquant: {str(e)}"))
        return redirect('competitions:club:practitioners')