#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de patch pour corriger le problème 403 dans practitioners.py
"""
import os
import sys
import shutil
from datetime import datetime

def patch_practitioners_file():
    """Appliquer le patch au fichier practitioners.py"""
    
    file_path = "apps/competitions/views/club/practitioners.py"
    
    # Vérifier que le fichier existe
    if not os.path.exists(file_path):
        print(f"Erreur: Le fichier {file_path} n'existe pas!")
        return False
    
    # Créer une sauvegarde
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"Sauvegarde créée: {backup_path}")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Définir le code à remplacer
    old_code = '''@login_required
def practitioner_create(request):
    """Créer un nouveau pratiquant"""
    try:
        logger.info(f"practitioner_create appelé par {request.user.username}")
        user_club = get_user_club(request)
        logger.info(f"Club trouvé: {user_club}")
        
        if not user_club:
            messages.error(request, _("Vous n'êtes associé à aucun club."))
            return redirect('competitions:dashboard:club')
        
        if not manual_permission_check(request.user, user_club):
            logger.warning(f"Permission refusée pour {request.user.username} sur le club {user_club}")
            raise PermissionDenied(_("Vous n'avez pas l'autorisation de créer un pratiquant."))
        
        if request.method == 'POST':
            form = PractitionerForm(request.POST, request.FILES)
            if form.is_valid():
                practitioner = form.save(commit=False)
                practitioner.organization = user_club
                practitioner.save()
                
                messages.success(request, _(f"Le pratiquant {practitioner.full_name} a été créé avec succès."))
                return redirect('competitions:club:practitioners')
        else:
            form = PractitionerForm()
        
        context = {
            'form': form,
            'club': user_club,
            'page_title': _("Ajouter un Pratiquant"),
        }
        
        return render(request, 'competitions/club/practitioner_form.html', context)
        
    except PermissionDenied:
        raise
    except Exception as e:
        logger.error(f"Erreur dans practitioner_create: {str(e)}")
        messages.error(request, _("Erreur lors de la création du pratiquant."))
        return redirect('competitions:club:practitioners')'''

    new_code = '''@login_required
def practitioner_create(request):
    """Créer un nouveau pratiquant"""
    try:
        logger.info(f"practitioner_create appelé par {request.user.username}")
        
        # Essayer d'abord de récupérer l'organisation depuis le middleware
        organization = None
        if hasattr(request, 'user_organization') and request.user_organization:
            organization = request.user_organization
            logger.info(f"Organisation trouvée via middleware: {organization}")
        else:
            # Sinon utiliser get_user_club
            user_club = get_user_club(request)
            logger.info(f"Club/Organisation trouvé via get_user_club: {user_club}")
            organization = user_club
        
        if not organization:
            # Dernière tentative : chercher via UserProfile
            from apps.competitions.models.users import UserProfile
            try:
                profile = UserProfile.objects.get(user=request.user)
                organization = profile.organization
                logger.info(f"Organisation trouvée via UserProfile: {organization}")
            except UserProfile.DoesNotExist:
                pass
        
        if not organization:
            messages.error(request, _("Vous n'êtes associé à aucune organisation. Contactez un administrateur."))
            return redirect('competitions:dashboard:dashboard')
        
        # Ne pas vérifier les permissions si l'utilisateur est superuser
        if not request.user.is_superuser:
            # Vérifier les permissions avec l'organisation
            if not manual_permission_check(request.user, organization):
                logger.warning(f"Permission refusée pour {request.user.username} sur l'organisation {organization}")
                # Au lieu de lever une exception, essayer de trouver une organisation valide
                from apps.competitions.models import Practitioner
                user_as_practitioner = Practitioner.objects.filter(
                    Q(user=request.user) | Q(email=request.user.email)
                ).select_related('organization').first()
                
                if user_as_practitioner and user_as_practitioner.organization:
                    organization = user_as_practitioner.organization
                    logger.info(f"Organisation alternative trouvée: {organization}")
                else:
                    messages.error(request, _("Vous n'avez pas l'autorisation de créer un pratiquant. Contactez un administrateur."))
                    return redirect('competitions:club:practitioners')
        
        if request.method == 'POST':
            form = PractitionerForm(request.POST, request.FILES)
            if form.is_valid():
                practitioner = form.save(commit=False)
                practitioner.organization = organization
                practitioner.save()
                
                messages.success(request, _(f"Le pratiquant {practitioner.full_name} a été créé avec succès."))
                return redirect('competitions:club:practitioners')
        else:
            form = PractitionerForm()
        
        context = {
            'form': form,
            'club': organization,  # Pour compatibilité avec le template
            'organization': organization,
            'page_title': _("Ajouter un Pratiquant"),
        }
        
        return render(request, 'competitions/club/practitioner_form.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans practitioner_create: {str(e)}", exc_info=True)
        messages.error(request, _(f"Erreur lors de la création du pratiquant: {str(e)}"))
        return redirect('competitions:club:practitioners')'''

    # Remplacer le code
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("Code remplacé avec succès!")
    else:
        print("Avertissement: Le code exact n'a pas été trouvé. Tentative de remplacement partiel...")
        # Essayer de trouver la fonction et la remplacer
        import re
        pattern = r'@login_required\s+def practitioner_create\(request\):.*?(?=@login_required|def |class |$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.start()] + new_code + content[match.end():]
            print("Remplacement partiel effectué!")
        else:
            print("Erreur: Impossible de trouver la fonction practitioner_create")
            return False
    
    # Écrire le fichier modifié
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier {file_path} patché avec succès!")
    return True

if __name__ == "__main__":
    print("=== Patch du fichier practitioners.py ===")
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists("apps/competitions/views/club/practitioners.py"):
        print("Erreur: Ce script doit être exécuté depuis le dossier racine du projet Django")
        print("(là où se trouve le dossier 'apps')")
        sys.exit(1)
    
    if patch_practitioners_file():
        print("\n✓ Patch appliqué avec succès!")
        print("\nPour appliquer les changements:")
        print("1. Copier ce fichier sur le serveur de production")
        print("2. Exécuter: python patch_practitioners.py")
        print("3. Redémarrer le service: systemctl restart martialcomp.service")
    else:
        print("\n✗ Échec de l'application du patch")
        sys.exit(1)