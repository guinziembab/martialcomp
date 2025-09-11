from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from apps.competitions.models.organization_templates import OrganizationTemplate
import os
import zipfile
import tempfile
from datetime import datetime

class Command(BaseCommand):
    help = 'Exporte les templates d\'organisation en différents formats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization-id',
            type=int,
            help='ID de l\'organisation Ã  exporter'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['html', 'pdf', 'zip'],
            default='html',
            help='Format d\'export (html, pdf, zip)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exports',
            help='Répertoire de sortie'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Exporter tous les templates'
        )

    def handle(self, *args, **options):
        """Exporte les templates d'organisation"""
        
        self.stdout.write(self.style.SUCCESS("ðŸ“¤ EXPORT DES TEMPLATES D'ORGANISATION"))
        self.stdout.write("=" * 50)
        
        # Créer le répertoire de sortie
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Déterminer les templates Ã  exporter
        if options['all']:
            templates = OrganizationTemplate.objects.all()
            self.stdout.write(f"ðŸ“‹ Export de {templates.count()} templates")
        elif options['organization_id']:
            try:
                template = OrganizationTemplate.objects.get(organization_id=options['organization_id'])
                templates = [template]
                self.stdout.write(f"ðŸ“‹ Export du template de l'organisation {template.organization.name}")
            except OrganizationTemplate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"âŒ Template non trouvé pour l'organisation {options['organization_id']}"))
                return
        else:
            self.stdout.write(self.style.ERROR("âŒ Spécifiez --organization-id ou --all"))
            return
        
        export_format = options['format']
        exported_count = 0
        
        for template in templates:
            try:
                filename = self._export_template(template, export_format, output_dir)
                self.stdout.write(f"âœ… {template.organization.name}: {filename}")
                exported_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"âŒ Erreur pour {template.organization.name}: {str(e)}"))
        
        self.stdout.write(f"\nðŸ“Š Export terminé: {exported_count} fichiers créés dans {output_dir}/")
        self.stdout.write(self.style.SUCCESS("âœ… Export terminé avec succès!"))

    def _export_template(self, template, format_type, output_dir):
        """Exporte un template dans le format spécifié"""
        
        # Préparer les données du template
        context = {
            'organization': template.organization,
            'template': template,
            'theme_colors': template.get_theme_colors(),
            'videos': template.get_videos(),
            'images': template.get_images(),
            'social_links': template.get_social_links(),
            'custom_sections': template.get_custom_sections(),
            'widgets': template.get_widgets(),
        }
        
        # Générer le nom de fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        org_name = template.organization.name.replace(' ', '_').lower()
        
        if format_type == 'html':
            return self._export_html(template, context, output_dir, org_name, timestamp)
        elif format_type == 'pdf':
            return self._export_pdf(template, context, output_dir, org_name, timestamp)
        elif format_type == 'zip':
            return self._export_zip(template, context, output_dir, org_name, timestamp)
        
        return None

    def _export_html(self, template, context, output_dir, org_name, timestamp):
        """Exporte en HTML statique"""
        
        # Rendre le template HTML
        html_content = render_to_string('organizations/export/template_export.html', context)
        
        # Créer le fichier HTML
        filename = f"{org_name}_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename

    def _export_pdf(self, template, context, output_dir, org_name, timestamp):
        """Exporte en PDF"""
        
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string
            
            # Rendre le template HTML
            html_content = render_to_string('organizations/export/template_export.html', context)
            
            # Créer le PDF
            filename = f"{org_name}_{timestamp}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Générer le PDF avec WeasyPrint
            html = HTML(string=html_content)
            html.write_pdf(filepath)
            
            return filename
            
        except ImportError:
            self.stdout.write(self.style.WARNING("âš ï¸ WeasyPrint non installé. Installation: pip install weasyprint"))
            return None

    def _export_zip(self, template, context, output_dir, org_name, timestamp):
        """Exporte en archive ZIP avec tous les assets"""
        
        # Créer un répertoire temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Rendre le template HTML
            html_content = render_to_string('organizations/export/template_export.html', context)
            
            # Créer le fichier HTML dans le répertoire temporaire
            html_filename = f"index.html"
            html_filepath = os.path.join(temp_dir, html_filename)
            
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Créer le fichier ZIP
            zip_filename = f"{org_name}_{timestamp}.zip"
            zip_filepath = os.path.join(output_dir, zip_filename)
            
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Ajouter le fichier HTML
                zipf.write(html_filepath, html_filename)
                
                # Ajouter un fichier README
                readme_content = f"""
# Template exporté pour {template.organization.name}

Date d'export: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Format: HTML statique

## Utilisation
1. Décompressez l'archive
2. Ouvrez index.html dans votre navigateur
3. Le site est maintenant autonome

## Personnalisation
- Modifiez index.html pour changer le contenu
- Ajoutez vos propres images dans le dossier images/
- Personnalisez les styles dans le CSS intégré

## Support
Pour toute question, contactez l'équipe de développement.
                """
                
                zipf.writestr('README.md', readme_content.strip())
            
            return zip_filename 

