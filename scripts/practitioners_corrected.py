#!/usr/bin/env python3
"""
Version corrigée de competitions/views/club/practitioners.py
Avec toutes les corrections appliquées proprement
"""

# Je vais créer seulement la section corrigée de la méthode practitioner_form
# Voici le code corrigé pour la section problématique:

practitioner_form_corrected = '''
    if request.method == 'POST':
        # Créer le formulaire avec les données POST
        if practitioner:
            form = PractitionerForm(request.POST, request.FILES, instance=practitioner, request=request)
        else:
            form = PractitionerForm(request.POST, request.FILES, request=request)
        
        if form.is_valid():
            try:
                # Sauvegarder le pratiquant
                practitioner = form.save(commit=False)
                
                # CORRECTION: Vérifier que l'objet a été créé correctement
                if not practitioner:
                    messages.error(request, _("Erreur lors de la création du pratiquant. Veuillez vérifier les données saisies."))
                    return redirect("competitions:club:practitioners")
                
                # S'assurer que le pratiquant est associé à l'organisation
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if not club_organization:
                    messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
                    return redirect('competitions:dashboard')
                    
                if not practitioner.organization:
                    practitioner.organization = club_organization
                
                # Sauvegarder le pratiquant
                practitioner.save()
                
                # Sauvegarder les relations M2M (disciplines)
                form.save_m2m()
                
                if practitioner_id:
                    messages.success(request, _("Pratiquant mis à jour avec succès."))
                else:
                    messages.success(request, _("Pratiquant créé avec succès."))
                
                return redirect('competitions:club:practitioners')
                
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {0}").format(str(e)))
                logger.error(f"Erreur lors de la sauvegarde du pratiquant: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Log des erreurs pour debugging avec plus de détails
            logger.error(f"Erreurs du formulaire: {form.errors}")
            logger.error(f"Données POST reçues: {dict(request.POST)}")
            
    else:
        # Créer le formulaire pour GET
        if practitioner:
            form = PractitionerForm(instance=practitioner, request=request)
        else:
            form = PractitionerForm(request=request)
'''

print("Code corrigé généré avec les améliorations:")
print("1. ✅ Vérification if not practitioner")
print("2. ✅ Logs détaillés des erreurs")
print("3. ✅ Messages d'erreur appropriés")
print()
print("Pour appliquer manuellement:")
print("1. Éditer le fichier practitioners.py")
print("2. Remplacer la section POST par le code ci-dessus")
print("3. Redémarrer Django")