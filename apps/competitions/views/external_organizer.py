from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import csv
import json


@login_required
def external_organizer_participants(request):
    """
    Vue pour la gestion des participants par l'organisateur externe.
    """
    # TODO: Implémenter la logique pour récupérer les participants des compétitions organisées
    participants = []
    
    context = {
        'participants': participants,
        'total_participants': len(participants),
    }
    
    return render(request, 'competitions/external_organizer/participants.html', context)


@login_required
def external_organizer_results(request):
    """
    Vue pour la gestion des résultats par l'organisateur externe.
    """
    # TODO: Implémenter la logique pour récupérer les résultats des compétitions organisées
    results = []
    competitions = []
    
    context = {
        'results': results,
        'competitions': competitions,
    }
    
    return render(request, 'competitions/external_organizer/results.html', context)


@login_required
def external_organizer_reports(request):
    """
    Vue pour les rapports et statistiques de l'organisateur externe.
    """
    # TODO: Implémenter la logique pour générer les rapports
    stats = {
        'total_competitions': 0,
        'total_participants': 0,
        'total_matches': 0,
        'completed_competitions': 0,
    }
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'competitions/external_organizer/reports.html', context)


@login_required
def external_organizer_profile(request):
    """
    Vue pour la gestion du profil de l'organisateur externe.
    """
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'competitions/external_organizer/profile.html', context)


@login_required
def external_organizer_support(request):
    """
    Vue pour le support de l'organisateur externe.
    """
    # TODO: Implémenter la logique pour gérer les tickets de support
    tickets = []
    
    context = {
        'tickets': tickets,
    }
    
    return render(request, 'competitions/external_organizer/support.html', context)


@login_required
def external_organizer_add_participant(request):
    """
    Vue pour ajouter un participant individuel.
    """
    if request.method == 'POST':
        # TODO: Traitement du formulaire d'ajout de participant
        try:
            # Récupération des données du formulaire
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            birth_date = request.POST.get('birth_date')
            competition_id = request.POST.get('competition')
            category_id = request.POST.get('category')
            
            # TODO: Validation et création du participant
            # participant = Participant.objects.create(...)
            
            messages.success(request, _("Participant ajouté avec succès."))
            return redirect('competitions:external_organizer:participants')
            
        except ValidationError as e:
            messages.error(request, _("Erreur lors de l'ajout du participant: {}").format(e))
        except Exception as e:
            messages.error(request, _("Une erreur s'est produite: {}").format(e))
    
    # TODO: Récupérer les compétitions et catégories pour le formulaire
    competitions = []  # Competition.objects.filter(organizer=request.user)
    categories = []    # get_organization_queryset(Category, self.request.user)
    
    context = {
        'competitions': competitions,
        'categories': categories,
    }
    
    return render(request, 'competitions/external_organizer/add_participant.html', context)


@login_required
def external_organizer_bulk_add_participants(request):
    """
    Vue pour ajouter des participants en masse via CSV.
    """
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, _("Le fichier doit être au format CSV."))
                return redirect('competitions:external_organizer:bulk_add_participants')
            
            try:
                # Lecture du fichier CSV
                file_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(file_data.splitlines())
                
                participants_added = 0
                errors = []
                
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # TODO: Validation et création des participants en masse
                        # participant = Participant.objects.create(
                        #     first_name=row.get('prenom', '').strip(),
                        #     last_name=row.get('nom', '').strip(),
                        #     email=row.get('email', '').strip(),
                        #     phone=row.get('telephone', '').strip(),
                        #     birth_date=row.get('date_naissance'),
                        #     competition_id=row.get('competition_id'),
                        #     category_id=row.get('category_id'),
                        # )
                        participants_added += 1
                        
                    except Exception as e:
                        errors.append(_("Ligne {}: {}").format(row_num, str(e)))
                
                if participants_added > 0:
                    messages.success(request, _(f"{participants_added} participants ajoutés avec succès."))
                
                if errors:
                    error_message = _("Erreurs rencontrées:") + "\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        error_message += f"\n... et {len(errors) - 5} autres erreurs."
                    messages.warning(request, error_message)
                
                return redirect('competitions:external_organizer:participants')
                
            except Exception as e:
                messages.error(request, _("Erreur lors de la lecture du fichier: {}").format(e))
    
    # TODO: Récupérer les compétitions pour le formulaire
    competitions = []  # Competition.objects.filter(organizer=request.user)
    
    context = {
        'competitions': competitions,
    }
    
    return render(request, 'competitions/external_organizer/bulk_add_participants.html', context)


@login_required
def external_organizer_edit_participant(request, participant_id):
    """
    Vue pour modifier un participant.
    """
    # TODO: Récupérer le participant
    # participant = get_object_or_404(Participant, id=participant_id, competition__organizer=request.user)
    
    if request.method == 'POST':
        try:
            # TODO: Mise à jour du participant
            # participant.first_name = request.POST.get('first_name')
            # participant.last_name = request.POST.get('last_name')
            # participant.email = request.POST.get('email')
            # participant.phone = request.POST.get('phone')
            # participant.birth_date = request.POST.get('birth_date')
            # participant.save()
            
            messages.success(request, _("Participant modifié avec succès."))
            return redirect('competitions:external_organizer:participants')
            
        except Exception as e:
            messages.error(request, _("Erreur lors de la modification: {}").format(e))
    
    # TODO: Récupérer les données pour le formulaire
    competitions = []  # Competition.objects.filter(organizer=request.user)
    categories = []    # get_organization_queryset(Category, self.request.user)
    
    context = {
        'participant_id': participant_id,
        # 'participant': participant,
        'competitions': competitions,
        'categories': categories,
    }
    
    return render(request, 'competitions/external_organizer/edit_participant.html', context)


@login_required
def external_organizer_delete_participant(request, participant_id):
    """
    Vue pour supprimer un participant.
    """
    if request.method == 'POST':
        try:
            # TODO: Supprimer le participant
            # participant = get_object_or_404(Participant, id=participant_id, competition__organizer=request.user)
            # participant.delete()
            
            messages.success(request, _("Participant supprimé avec succès."))
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            messages.error(request, _("Erreur lors de la suppression: {}").format(e))
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'})


@login_required
def external_organizer_export_participants(request):
    """
    Vue pour exporter la liste des participants au format CSV.
    """
    try:
        # TODO: Récupérer les participants de l'organisateur
        # participants = Participant.objects.filter(competition__organizer=request.user)
        
        # Création de la réponse CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="participants.csv"'
        
        writer = csv.writer(response)
        
        # En-têtes CSV
        writer.writerow([
            'Prénom', 'Nom', 'Email', 'Téléphone', 'Date de naissance',
            'Compétition', 'Catégorie', 'Statut', 'Date d\'inscription'
        ])
        
        # TODO: Écrire les données des participants
        # for participant in participants:
        #     writer.writerow([
        #         participant.first_name,
        #         participant.last_name,
        #         participant.email,
        #         participant.phone,
        #         participant.birth_date,
        #         participant.competition.name,
        #         participant.category.name if participant.category else '',
        #         participant.get_status_display(),
        #         participant.created_at.strftime('%d/%m/%Y %H:%M')
        #     ])
        
        return response
        
    except Exception as e:
        messages.error(request, _("Erreur lors de l'export: {}").format(e))
        return redirect('competitions:external_organizer:participants')