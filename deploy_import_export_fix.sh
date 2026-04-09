#!/bin/bash
# Script de déploiement - Correction Import/Export
# Date: 2025-11-21

set -e

echo "=========================================="
echo "  DEPLOIEMENT - FIX IMPORT/EXPORT"
echo "=========================================="

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups/$(date +%Y%m%d_%H%M%S)"

# Création du répertoire de backup
echo "[1/6] Création du backup..."
mkdir -p "$BACKUP_DIR"

# Backup des fichiers existants
cp "$PRODUCTION_PATH/apps/competitions/views/club/import_export.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$PRODUCTION_PATH/apps/competitions/urls/club.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$PRODUCTION_PATH/apps/competitions/templates/competitions/club/import_export.html" "$BACKUP_DIR/" 2>/dev/null || true

echo "[2/6] Mise à jour du fichier import_export.py..."
cat > "$PRODUCTION_PATH/apps/competitions/views/club/import_export.py" << 'PYEOF'
import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO

from apps.competitions.utils.permission_helpers import get_user_club
from apps.competitions.models import Practitioner, Discipline
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

def get_organization_from_club(club):
    """
    Extrait l'organisation depuis un club.
    """
    if hasattr(club, 'organization') and club.organization:
        return club.organization
    from apps.organizations.models import Organization
    if isinstance(club, Organization):
        return club
    return None

def import_practitioners_from_excel(file, organization):
    """
    Importe des pratiquants depuis un fichier Excel.
    """
    results = {
        'success': 0,
        'errors': [],
        'skipped': 0,
        'total': 0
    }

    try:
        file_content = file.read()
        file.seek(0)

        wb = openpyxl.load_workbook(BytesIO(file_content))
        ws = wb.active

        headers = [cell.value for cell in ws[1]]

        header_map = {}
        for idx, header in enumerate(headers, start=1):
            if header:
                normalized = str(header).strip().lower()
                header_map[normalized] = idx

        logger.info(f"En-têtes détectés: {header_map}")

        col_mapping = {}

        field_mappings = {
            'last_name': ['nom', 'lastname', 'last name', 'surname', 'family name'],
            'first_name': ['prénom', 'firstname', 'first name', 'prenom', 'given name'],
            'birth_date': ['date de naissance', 'date de naissance ', 'birthdate', 'birth date', 'date_naissance', 'dob'],
            'grade': ['grade', 'niveau', 'level', 'belt', 'ceinture'],
            'email': ['email', 'e-mail', 'mail', 'courriel'],
            'phone': ['téléphone', 'telephone', 'phone', 'tél', 'tel', 'mobile', 'portable'],
            'license_number': ['licence', 'license', 'numéro de licence', 'numero de licence', 'license number', 'numéro licence'],
        }

        for field_name, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in header_map:
                    col_mapping[field_name] = header_map[key]
                    break

        logger.info(f"Mapping des colonnes: {col_mapping}")

        for row_num in range(2, ws.max_row + 1):
            row = ws[row_num]

            row_values = [cell.value for cell in row if cell.value is not None and str(cell.value).strip()]
            if not row_values:
                continue

            results['total'] += 1

            try:
                data = {}
                for field, col_idx in col_mapping.items():
                    if col_idx and col_idx <= len(row):
                        cell_value = row[col_idx - 1].value
                        if cell_value is not None:
                            if isinstance(cell_value, str):
                                cell_value = cell_value.strip()
                                if cell_value:
                                    data[field] = cell_value
                            else:
                                data[field] = cell_value

                if 'first_name' not in data or 'last_name' not in data:
                    results['errors'].append({
                        'row': row_num,
                        'error': _("Nom ou prénom manquant")
                    })
                    results['skipped'] += 1
                    continue

                birth_date = None
                if 'birth_date' in data:
                    birth_date_value = data['birth_date']

                    if isinstance(birth_date_value, datetime):
                        birth_date = birth_date_value.date()
                    elif hasattr(birth_date_value, 'year'):
                        birth_date = birth_date_value
                    elif isinstance(birth_date_value, str):
                        birth_date_str = birth_date_value.strip()

                        date_formats = [
                            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y',
                            '%m-%d-%Y', '%Y/%m/%d', '%d.%m.%Y', '%m.%d.%Y',
                            '%Y.%m.%d', '%d %m %Y', '%Y %m %d',
                        ]

                        for date_format in date_formats:
                            try:
                                birth_date = datetime.strptime(birth_date_str, date_format).date()
                                break
                            except ValueError:
                                continue

                        if birth_date is None:
                            parts = birth_date_str.replace('/', '-').replace('.', '-').replace(' ', '-').split('-')
                            if len(parts) == 3:
                                try:
                                    year_idx = None
                                    for i, part in enumerate(parts):
                                        if len(part) == 4 and part.isdigit():
                                            year_idx = i
                                            break

                                    if year_idx is not None:
                                        year = int(parts[year_idx])
                                        other_parts = [int(p) for i, p in enumerate(parts) if i != year_idx]

                                        for month, day in [(other_parts[0], other_parts[1]), (other_parts[1], other_parts[0])]:
                                            if 1 <= month <= 12 and 1 <= day <= 31:
                                                try:
                                                    birth_date = datetime(year, month, day).date()
                                                    break
                                                except ValueError:
                                                    continue

                                    if birth_date is None and all(p.isdigit() for p in parts):
                                        part1, part2, part3 = int(parts[0]), int(parts[1]), int(parts[2])
                                        if part3 < 100:
                                            part3 = 2000 + part3 if part3 < 50 else 1900 + part3

                                        if part1 > 12:
                                            day, month, year = part1, part2, part3
                                            if 1 <= month <= 12 and 1 <= day <= 31:
                                                birth_date = datetime(year, month, day).date()
                                        elif part2 > 12:
                                            month, day, year = part1, part2, part3
                                            if 1 <= month <= 12 and 1 <= day <= 31:
                                                birth_date = datetime(year, month, day).date()
                                        else:
                                            day, month, year = part1, part2, part3
                                            if 1 <= month <= 12 and 1 <= day <= 31:
                                                try:
                                                    birth_date = datetime(year, month, day).date()
                                                except ValueError:
                                                    pass
                                except (ValueError, IndexError, AttributeError):
                                    pass

                        if birth_date is None:
                            results['errors'].append({
                                'row': row_num,
                                'error': _("Format de date invalide: {}").format(birth_date_value)
                            })
                            results['skipped'] += 1
                            continue
                    else:
                        results['errors'].append({
                            'row': row_num,
                            'error': _("Date de naissance invalide")
                        })
                        results['skipped'] += 1
                        continue
                else:
                    results['errors'].append({
                        'row': row_num,
                        'error': _("Date de naissance manquante")
                    })
                    results['skipped'] += 1
                    continue

                existing = Practitioner.objects.filter(
                    first_name__iexact=data['first_name'],
                    last_name__iexact=data['last_name'],
                    birth_date=birth_date,
                    organization=organization
                ).first()

                if existing:
                    results['errors'].append({
                        'row': row_num,
                        'error': _("Pratiquant déjà existant: {} {}").format(
                            data['first_name'], data['last_name']
                        )
                    })
                    results['skipped'] += 1
                    continue

                grade = None
                if 'grade' in data and data['grade']:
                    grade_text = str(data['grade']).strip()
                    if grade_text:
                        try:
                            from apps.grades.models import Grade
                            grade = Grade.objects.filter(name__iexact=grade_text).first()
                        except ImportError:
                            pass

                email = data.get('email')
                if email:
                    email = str(email).strip() or None
                else:
                    email = None

                phone = data.get('phone')
                if phone:
                    phone = str(phone).strip() or None
                else:
                    phone = None

                license_number = data.get('license_number', '').strip() if data.get('license_number') else ''

                practitioner = Practitioner.objects.create(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    birth_date=birth_date,
                    organization=organization,
                    email=email,
                    phone=phone,
                    license_number=license_number,
                    grade=grade,
                    status='active',
                    is_active=True
                )

                results['success'] += 1
                logger.info(f"Pratiquant créé: {practitioner.full_name}")

            except Exception as e:
                logger.error(f"Erreur ligne {row_num}: {str(e)}")
                results['errors'].append({'row': row_num, 'error': str(e)})
                results['skipped'] += 1
                continue

    except Exception as e:
        logger.error(f"Erreur lecture fichier: {str(e)}")
        results['errors'].append({'row': 0, 'error': _("Erreur lecture fichier: {}").format(str(e))})

    return results


@login_required
@ensure_csrf_cookie
def import_export_data(request):
    """Vue pour l'import/export de données du club"""

    if request.path.endswith('/ajax/') and request.method == 'POST':
        club = get_user_club(request)
        if not club:
            return JsonResponse({'success': False, 'error': _("Veuillez sélectionner un club valide.")}, status=400)

        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': _("Aucun fichier sélectionné.")}, status=400)

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name.lower()
        if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            return JsonResponse({'success': False, 'error': _("Format non supporté. Utilisez CSV ou Excel.")}, status=400)

        organization = get_organization_from_club(club)
        if not organization:
            return JsonResponse({'success': False, 'error': _("Aucune organisation associée.")}, status=400)

        results = import_practitioners_from_excel(uploaded_file, organization)

        if results['success'] > 0:
            return JsonResponse({
                'success': True,
                'message': _("{} pratiquants importés. {} erreurs.").format(results['success'], len(results['errors'])),
                'results': results
            })
        else:
            return JsonResponse({
                'success': False,
                'error': _("Aucun pratiquant importé. {} erreurs.").format(len(results['errors'])),
                'results': results
            }, status=400)

    club = get_user_club(request)
    organization = get_organization_from_club(club) if club else None

    if not club:
        messages.error(request, _("Aucun club associé à votre compte."))
        return render(request, 'competitions/club/import_export.html', {
            'page_title': _('Import/Export de données'),
            'section': 'import_export',
            'club': None
        })

    context = {
        'page_title': _('Import/Export de données'),
        'section': 'import_export',
        'club': club
    }

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if 'import' in request.POST and 'excel_file' in request.FILES:
            uploaded_file = request.FILES['excel_file']
            file_name = uploaded_file.name.lower()

            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, _("Format non supporté. Utilisez CSV ou Excel."))
            elif not organization:
                messages.error(request, _("Aucune organisation associée au club."))
            else:
                try:
                    with transaction.atomic():
                        results = import_practitioners_from_excel(uploaded_file, organization)

                        if results['success'] > 0:
                            messages.success(request, _("{} pratiquants importés avec succès.").format(results['success']))
                            if results['errors']:
                                messages.warning(request, _("{} lignes n'ont pas pu être importées.").format(len(results['errors'])))
                        else:
                            messages.error(request, _("Aucun pratiquant importé. {} erreurs.").format(len(results['errors'])))

                        context['import_results'] = results

                except Exception as e:
                    logger.error(f"Erreur importation: {str(e)}")
                    messages.error(request, _("Erreur: {}").format(str(e)))

    return render(request, 'competitions/club/import_export.html', context)


@login_required
def download_import_template(request):
    """Génère et télécharge un modèle Excel pour l'import des pratiquants."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pratiquants"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    example_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    headers = [
        ('Nom', 20), ('Prénom', 20), ('Date de naissance', 20),
        ('Grade', 20), ('Email', 30), ('Numéro de licence', 20)
    ]

    for col_num, (header, width) in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width

    examples = [
        ['DUPONT', 'Jean', '15/03/1990', 'Ceinture noire', 'jean.dupont@email.com', 'LIC001'],
        ['MARTIN', 'Marie', '22/07/1985', 'Ceinture marron', 'marie.martin@email.com', 'LIC002'],
        ['BERNARD', 'Pierre', '10/01/2005', 'Ceinture orange', 'pierre.bernard@email.com', 'LIC003'],
    ]

    for row_num, example in enumerate(examples, 2):
        for col_num, value in enumerate(example, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.fill = example_fill
            cell.border = thin_border

    ws_instructions = wb.create_sheet(title="Instructions")
    instructions = [
        ("INSTRUCTIONS D'IMPORT", ""),
        ("", ""),
        ("Colonnes obligatoires:", ""),
        ("- Nom", "Le nom de famille du pratiquant"),
        ("- Prénom", "Le prénom du pratiquant"),
        ("- Date de naissance", "Format JJ/MM/AAAA ou AAAA-MM-JJ"),
        ("", ""),
        ("Colonnes optionnelles:", ""),
        ("- Grade", "Ex: Ceinture noire, Ceinture marron, 1er dan..."),
        ("- Email", "L'adresse email du pratiquant"),
        ("- Numéro de licence", "Le numéro de licence fédérale"),
        ("", ""),
        ("Notes importantes:", ""),
        ("1.", "Supprimez les exemples avant d'ajouter vos données"),
        ("2.", "Ne modifiez pas les noms des colonnes"),
        ("3.", "Les pratiquants existants seront ignorés"),
    ]

    for row_num, (col1, col2) in enumerate(instructions, 1):
        ws_instructions.cell(row=row_num, column=1, value=col1)
        ws_instructions.cell(row=row_num, column=2, value=col2)
        if row_num == 1:
            ws_instructions.cell(row=row_num, column=1).font = Font(bold=True, size=14)

    ws_instructions.column_dimensions['A'].width = 25
    ws_instructions.column_dimensions['B'].width = 50

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Modele_Import_Pratiquants.xlsx"'
    return response


@login_required
def export_practitioners(request):
    """Exporte tous les pratiquants du club en fichier Excel."""
    club = get_user_club(request)
    organization = get_organization_from_club(club) if club else None

    if not organization:
        messages.error(request, _("Aucune organisation associée à votre compte."))
        return render(request, 'competitions/club/import_export.html', {
            'page_title': _('Import/Export de données'),
            'section': 'import_export',
            'club': club
        })

    practitioners = Practitioner.objects.filter(
        organization=organization
    ).select_related('grade').order_by('last_name', 'first_name')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pratiquants"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    headers = [
        ('Nom', 20), ('Prénom', 20), ('Date de naissance', 18),
        ('Grade', 20), ('Email', 30), ('Téléphone', 18),
        ('Numéro de licence', 20), ('Statut', 12)
    ]

    for col_num, (header, width) in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width

    for row_num, p in enumerate(practitioners, 2):
        data = [
            p.last_name or '',
            p.first_name or '',
            p.birth_date.strftime('%d/%m/%Y') if p.birth_date else '',
            p.grade.name if p.grade else '',
            p.email or '',
            p.phone or '',
            p.license_number or '',
            'Actif' if p.is_active else 'Inactif'
        ]

        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = thin_border

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Pratiquants_{organization.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    logger.info(f"Export de {practitioners.count()} pratiquants pour {organization.name}")
    return response
PYEOF

echo "[3/6] Mise à jour des URLs..."
# Vérifier si les nouvelles URLs existent déjà
if ! grep -q "download_import_template" "$PRODUCTION_PATH/apps/competitions/urls/club.py"; then
    # Ajouter l'import
    sed -i "s/from apps.competitions.views.club.import_export import import_export_data/from apps.competitions.views.club.import_export import import_export_data, download_import_template, export_practitioners/" "$PRODUCTION_PATH/apps/competitions/urls/club.py"

    # Ajouter les URLs
    sed -i "/path('import-export\/ajax\/', import_export_data, name='import_export_ajax'),/a\\  path('import-export/template/', download_import_template, name='download_import_template'),\\n  path('import-export/export/', export_practitioners, name='export_practitioners')," "$PRODUCTION_PATH/apps/competitions/urls/club.py"
    echo "    URLs ajoutées"
else
    echo "    URLs déjà présentes"
fi

echo "[4/6] Mise à jour du template..."
# Remplacer le lien du modèle
sed -i 's|<a href="#" class="template-btn" download>|<a href="{% url '"'"'competitions:club:download_import_template'"'"' %}" class="template-btn">|g' "$PRODUCTION_PATH/apps/competitions/templates/competitions/club/import_export.html"

# Remplacer le bouton d'export (formulaire -> lien direct)
sed -i '/<form method="post" action="{% url '"'"'competitions:club:import_export'"'"' %}">/,/<\/form>/c\                    <a href="{% url '"'"'competitions:club:export_practitioners'"'"' %}" class="btn btn-primary btn-lg">\n                        <i class="fas fa-download me-2"><\/i>{% trans "Exporter en Excel" %}\n                    <\/a>' "$PRODUCTION_PATH/apps/competitions/templates/competitions/club/import_export.html" 2>/dev/null || true

echo "[5/6] Redémarrage de Gunicorn..."
pkill -f gunicorn || true
sleep 2

cd "$PRODUCTION_PATH"
export DJANGO_ENV=production
export DJANGO_SETTINGS_MODULE=config.settings

$VENV_PATH/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --daemon \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    config.wsgi:application

echo "[6/6] Vérification..."
sleep 3
GUNICORN_COUNT=$(ps aux | grep gunicorn | grep -v grep | wc -l)
echo "    Processus Gunicorn actifs: $GUNICORN_COUNT"

if [ "$GUNICORN_COUNT" -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "  DEPLOIEMENT REUSSI !"
    echo "=========================================="
    echo ""
    echo "Fonctionnalités ajoutées:"
    echo "  - Téléchargement du modèle Excel"
    echo "  - Export des pratiquants en Excel"
    echo "  - Import des pratiquants (déjà fonctionnel)"
    echo ""
    echo "Testez: https://martialcomp.com/fr/competitions/club/import-export/"
    echo ""
    echo "Backup créé dans: $BACKUP_DIR"
else
    echo ""
    echo "ERREUR: Gunicorn n'a pas démarré correctement!"
    echo "Consultez les logs: tail -f $PRODUCTION_PATH/logs/gunicorn_error.log"
    exit 1
fi
