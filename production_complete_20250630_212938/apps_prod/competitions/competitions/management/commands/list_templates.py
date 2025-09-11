from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Lists all template files in the project'

    def handle(self, *args, **options):
        template_extensions = ['.html', '.htm', '.django', '.jinja', '.jinja2']
        template_files = []
        
        # Répertoires à exclure
        exclude_dirs = ['.venv', 'env', 'node_modules', '__pycache__', '.git']
        
        # Start from the project root
        for root, dirs, files in os.walk('.'):
            # Modifier la liste dirs en place pour éviter de parcourir les répertoires exclus
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in template_extensions):
                    template_files.append(os.path.join(root, file))
        
        # Sort templates by path
        template_files.sort()
        
        # Write to file
        with open('templates_list.txt', 'w') as f:
            for template in template_files:
                f.write(f"{template}\n")
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(template_files)} templates. List saved to templates_list.txt'))