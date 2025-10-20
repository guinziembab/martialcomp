from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import pandas as pd
import json
from datetime import datetime
import logging
from ...models.practitioners import Practitioner

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def import_export_view(request):
    """Vue principale pour l'import/export"""
    # Log de debug
    logger.info(f"Import/Export view accessed by user: {request.user}")
    
    # Récupérer l'organisation - LOGIQUE AMÉLIORÉE
    organization = None
    
    # 1. Essayer via le profil utilisateur
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'organization'):
        organization = request.user.profile.organization
        logger.info(f"Organisation trouvée via profile: {organization}")
    
    # 2. Essayer via les rôles utilisateur
    elif hasattr(request.user, 'organizations'):
        organization = request.user.organizations.first()
        logger.info(f"Organisation trouvée via organizations: {organization}")
    
    # 3. Essayer via le club de l'utilisateur (NOUVEAU)
    if not organization and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club
        if club and club.organization:
            organization = club.organization
            logger.info(f"Organisation trouvée via club: {organization}")
    
    # 4. Dernière tentative : chercher un club où l'utilisateur est propriétaire
    if not organization:
        from apps.competitions.models.club import Club
        user_club = Club.objects.filter(owner=request.user).first()
        if user_club:
            if user_club.organization:
                organization = user_club.organization
                logger.info(f"Organisation trouvée via club propriétaire: {organization}")
            else:
                # NOUVEAU: Créer automatiquement une organisation pour le club
                logger.warning(f"Club {user_club.name} sans organisation - création automatique")
                from apps.organizations.models import Organization, OrganizationType
                
                org_name = f"{user_club.name} Organization"
                new_org, created = Organization.objects.get_or_create(
                    name=org_name,
                    defaults={
                        'organization_type': OrganizationType.CLUB,
                        'description': f"Organisation créée automatiquement pour {user_club.name}",
                        'country': user_club.country if hasattr(user_club, 'country') else '',
                    }
                )
                
                user_club.organization = new_org
                user_club.save()
                
                organization = new_org
                logger.info(f"Organisation {'créée' if created else 'trouvée'} et liée au club: {organization}")
                
                # Optionnel: lier aussi le profil utilisateur
                if hasattr(request.user, 'profile') and not request.user.profile.organization:
                    request.user.profile.organization = organization
                    request.user.profile.save()
                    logger.info(f"Profil utilisateur mis à jour avec l'organisation")
    
    if not organization:
        logger.error(f"Impossible de trouver ou créer une organisation pour l'utilisateur {request.user.id}")
        logger.info(f"User profile: {getattr(request.user, 'profile', 'None')}")
        logger.info(f"User organizations: {getattr(request.user, 'organizations', 'None')}")
        messages.error(request, "Impossible de déterminer votre organisation. Contactez l'administrateur.")
        return redirect('competitions:dashboard:club')
    
    context = {
        'page_title': _('Import/Export de données'),
        'section': 'import_export',
        'organization': organization
    }
    
    return render(request, 'competitions/club/import_export_v2.html', context)

@login_required
@require_POST
def import_practitioners_ajax(request):
    """Import AJAX des pratiquants"""
    try:
        # Log détaillé
        logger.info(f"Import AJAX started by user: {request.user}")
        logger.info(f"Files received: {list(request.FILES.keys())}")
        
        # Récupérer l'organisation - LOGIQUE AMÉLIORÉE
        organization = None
        
        # 1. Essayer via le profil utilisateur
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'organization'):
            organization = request.user.profile.organization
            logger.info(f"[AJAX] Organisation trouvée via profile: {organization}")
        
        # 2. Essayer via les rôles utilisateur
        elif hasattr(request.user, 'organizations'):
            organization = request.user.organizations.first()
            logger.info(f"[AJAX] Organisation trouvée via organizations: {organization}")
        
        # 3. Essayer via le club de l'utilisateur (NOUVEAU)
        if not organization and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
            club = request.user.profile.club
            if club and club.organization:
                organization = club.organization
                logger.info(f"[AJAX] Organisation trouvée via club: {organization}")
        
        # 4. Dernière tentative : chercher un club où l'utilisateur est propriétaire
        if not organization:
            from apps.competitions.models.club import Club
            user_club = Club.objects.filter(owner=request.user).first()
            if user_club:
                if user_club.organization:
                    organization = user_club.organization
                    logger.info(f"[AJAX] Organisation trouvée via club propriétaire: {organization}")
                else:
                    # NOUVEAU: Créer automatiquement une organisation pour le club
                    logger.warning(f"[AJAX] Club {user_club.name} sans organisation - création automatique")
                    from apps.organizations.models import Organization, OrganizationType
                    
                    org_name = f"{user_club.name} Organization"
                    new_org, created = Organization.objects.get_or_create(
                        name=org_name,
                        defaults={
                            'organization_type': OrganizationType.CLUB,
                            'description': f"Organisation créée automatiquement pour {user_club.name}",
                            'country': user_club.country if hasattr(user_club, 'country') else '',
                        }
                    )
                    
                    user_club.organization = new_org
                    user_club.save()
                    
                    organization = new_org
                    logger.info(f"[AJAX] Organisation {'créée' if created else 'trouvée'} et liée au club: {organization}")
                    
                    # Optionnel: lier aussi le profil utilisateur
                    if hasattr(request.user, 'profile') and not request.user.profile.organization:
                        request.user.profile.organization = organization
                        request.user.profile.save()
                        logger.info(f"[AJAX] Profil utilisateur mis à jour avec l'organisation")
        
        if not organization:
            logger.error(f"[AJAX] Impossible de trouver ou créer une organisation pour l'utilisateur {request.user.id}")
            return JsonResponse({
                'success': False,
                'error': 'Impossible de déterminer votre organisation. Contactez l\'administrateur.'
            })
        
        # Récupérer le fichier
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({
                'success': False,
                'error': 'Aucun fichier sélectionné'
            })
        
        logger.info(f"Processing file: {file.name} (size: {file.size} bytes)")
        
        # Lire le fichier selon son extension
        try:
            if file.name.endswith('.csv'):
                # Lire le contenu du fichier une seule fois
                file_content = file.read()
                logger.info(f"File content size: {len(file_content)} bytes")
                
                # Afficher les premiers bytes pour debug
                if len(file_content) > 0:
                    logger.info(f"First 100 bytes: {file_content[:100]}")
                
                # Essayer plusieurs encodages et séparateurs
                encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
                separators = [';', ',', '\t', '|']
                df = None
                
                for encoding in encodings:
                    for separator in separators:
                        try:
                            # Utiliser io.BytesIO pour créer un fichier-like object
                            import io
                            df = pd.read_csv(io.BytesIO(file_content), encoding=encoding, sep=separator)
                            
                            # Vérifier que le DataFrame a des données valides
                            if len(df.columns) > 1 and len(df) > 0:
                                logger.info(f"CSV read successfully with encoding: {encoding}, separator: '{separator}'")
                                logger.info(f"DataFrame shape: {df.shape}")
                                logger.info(f"Columns: {list(df.columns)}")
                                break
                        except Exception as e:
                            logger.debug(f"Failed with {encoding}/{separator}: {str(e)}")
                            continue
                    
                    if df is not None and len(df.columns) > 1:
                        break
                            
                if df is None or len(df.columns) <= 1:
                    # Dernière tentative : essayer de détecter automatiquement
                    try:
                        import chardet
                        detected = chardet.detect(file_content)
                        encoding = detected['encoding'] or 'utf-8'
                        logger.info(f"Detected encoding: {encoding}")
                        df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                    except:
                        raise Exception("Impossible de lire le fichier CSV. Vérifiez le format et l'encodage.")
                    
            else:
                # Pour Excel, lire aussi le contenu une fois
                file_content = file.read()
                import io
                df = pd.read_excel(io.BytesIO(file_content))
                logger.info("Excel file read successfully")
                logger.info(f"DataFrame shape: {df.shape}")
                logger.info(f"Columns: {list(df.columns)}")
        
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la lecture du fichier: {str(e)}'
            })
        
        # Détecter et corriger les headers si nécessaire
        logger.info(f"Initial columns: {list(df.columns)}")
        
        if all(col.startswith('Unnamed:') for col in df.columns):
            # Chercher la ligne contenant les headers
            for i, row in df.iterrows():
                row_values = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip()]
                if any(keyword in str(val).lower() for val in row_values for keyword in ['nom', 'prénom', 'prenom', 'date']):
                    # Cette ligne contient probablement les headers
                    new_columns = []
                    for val in row.values:
                        if pd.notna(val) and str(val).strip():
                            new_columns.append(str(val).strip())
                        else:
                            new_columns.append(f'col_{len(new_columns)}')
                    df.columns = new_columns
                    df = df.iloc[i+1:].reset_index(drop=True)
                    logger.info(f"Headers found at row {i}: {new_columns}")
                    break
        
        # Nettoyer les colonnes
        df.columns = [col.strip() for col in df.columns]
        logger.info(f"Final columns: {list(df.columns)}")
        
        # Mapper les colonnes
        column_mapping = {
            'first_name': None,
            'last_name': None,
            'birth_date': None,
            'email': None
        }
        
        for col in df.columns:
            col_lower = col.lower()
            if 'prénom' in col_lower or 'prenom' in col_lower:
                column_mapping['first_name'] = col
            elif 'nom' in col_lower and 'prenom' not in col_lower and 'prénom' not in col_lower:
                column_mapping['last_name'] = col
            elif 'date' in col_lower and 'naissance' in col_lower:
                column_mapping['birth_date'] = col
            elif 'mail' in col_lower or 'email' in col_lower:
                column_mapping['email'] = col
        
        logger.info(f"Column mapping: {column_mapping}")
        
        # Vérifier que les colonnes essentielles sont présentes
        if not all([column_mapping['first_name'], column_mapping['last_name'], column_mapping['birth_date']]):
            missing = []
            if not column_mapping['first_name']:
                missing.append('Prénom')
            if not column_mapping['last_name']:
                missing.append('Nom')
            if not column_mapping['birth_date']:
                missing.append('Date de naissance')
            
            return JsonResponse({
                'success': False,
                'error': f"Colonnes manquantes: {', '.join(missing)}. Colonnes trouvées: {', '.join(df.columns)}"
            })
        
        # Traiter les données
        results = {
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
        
        for index, row in df.iterrows():
            try:
                # Extraire les données
                first_name = str(row.get(column_mapping['first_name'], '')).strip()
                last_name = str(row.get(column_mapping['last_name'], '')).strip()
                birth_date_str = str(row.get(column_mapping['birth_date'], '')).strip()
                email = str(row.get(column_mapping['email'], '')).strip() if column_mapping['email'] else ''
                
                # Ignorer les lignes vides
                if not first_name or not last_name or not birth_date_str or birth_date_str == 'nan':
                    results['skipped'] += 1
                    continue
                
                # Parser la date
                birth_date = None
                date_formats = [
                    '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d',
                    '%d.%m.%Y', '%Y.%m.%d', '%d %m %Y', '%Y %m %d'
                ]
                
                for fmt in date_formats:
                    try:
                        birth_date = datetime.strptime(birth_date_str, fmt).date()
                        break
                    except:
                        continue
                
                if not birth_date:
                    results['errors'].append(f"Ligne {index + 2}: Date invalide '{birth_date_str}'")
                    continue
                
                # Nettoyer l'email
                if email == 'nan' or email == 'NaN' or not email:
                    email = None
                
                # Créer ou mettre à jour le pratiquant
                # IMPORTANT: Chercher d'abord dans la même organisation
                practitioner = Practitioner.objects.filter(
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    organization=organization
                ).first()
                
                if not practitioner:
                    # Si pas trouvé dans cette organisation, créer nouveau
                    practitioner = Practitioner.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        birth_date=birth_date,
                        organization=organization,
                        email=email,
                        status='active'
                    )
                    created = True
                    logger.info(f"Created practitioner: {first_name} {last_name} for org {organization.name}")
                else:
                    created = False
                    # Optionnel : mettre à jour l'email si vide
                    if email and not practitioner.email:
                        practitioner.email = email
                        practitioner.save()
                        logger.info(f"Updated email for practitioner: {first_name} {last_name}")
                
                if created:
                    results['imported'] += 1
                    logger.info(f"Created practitioner: {first_name} {last_name}")
                else:
                    results['skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Ligne {index + 2}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Résumé
        summary = f"Import terminé: {results['imported']} pratiquants importés"
        if results['skipped'] > 0:
            summary += f", {results['skipped']} déjà existants"
        if results['errors']:
            summary += f", {len(results['errors'])} erreurs"
        
        logger.info(summary)
        
        return JsonResponse({
            'success': True,
            'message': summary,
            'details': results
        })
        
    except Exception as e:
        logger.error(f"Import error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def export_practitioners_excel(request):
    """Export des pratiquants en Excel"""
    try:
        # Récupérer l'organisation
        organization = None
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'organization'):
            organization = request.user.profile.organization
        elif hasattr(request.user, 'organizations'):
            organization = request.user.organizations.first()
            
        if not organization:
            messages.error(request, "Aucune organisation trouvée")
            return redirect('competitions:club:import_export')
        
        # Récupérer les pratiquants
        practitioners = Practitioner.objects.filter(organization=organization)
        
        # Créer le DataFrame
        data = []
        for p in practitioners:
            data.append({
                'Prénom': p.first_name,
                'Nom': p.last_name,
                'Date de naissance': p.birth_date.strftime('%d/%m/%Y') if p.birth_date else '',
                'Email': p.email or '',
                'Grade': p.grade_text or '',
                'Numéro de licence': p.license_number or '',
                'Statut': p.get_status_display()
            })
        
        df = pd.DataFrame(data)
        
        # Créer la réponse Excel
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="pratiquants_{organization.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        # Écrire le fichier Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Pratiquants', index=False)
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Pratiquants']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        logger.info(f"Exported {len(data)} practitioners for {organization.name}")
        return response
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}", exc_info=True)
        messages.error(request, f"Erreur lors de l'export: {str(e)}")
        return redirect('competitions:club:import_export')