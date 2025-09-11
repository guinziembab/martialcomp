"""
Commande de validation pour s'assurer que tous les templates sont prêts pour la traduction
"""
from django.core.management.base import BaseCommand
from django.template import Template, Context
import os
import re
import glob


class Command(BaseCommand):
    help = 'Valide que tous les templates sont prêts pour la traduction internationale'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tente de corriger automatiquement les problèmes détectés'
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        
        # Chemins vers les templates
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'templates',
            'task_management'
        )
        
        issues = []
        fixed = []
        
        # Rechercher tous les fichiers HTML
        html_files = glob.glob(os.path.join(template_dir, '**', '*.html'), recursive=True)
        
        for html_file in html_files:
            file_issues = self.validate_template_file(html_file)
            if file_issues:
                issues.extend(file_issues)
                
                if fix_mode:
                    fixed_count = self.fix_template_file(html_file, file_issues)
                    if fixed_count > 0:
                        fixed.append(f"{html_file}: {fixed_count} corrections appliquées")
        
        # Afficher les résultats
        if not issues:
            self.stdout.write(
                self.style.SUCCESS('✅ Tous les templates sont correctement préparés pour la traduction!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {len(issues)} problèmes détectés dans les templates:')
            )
            for issue in issues:
                self.stdout.write(f"  - {issue}")
                
        if fixed:
            self.stdout.write(
                self.style.SUCCESS(f'\n🔧 {len(fixed)} fichiers corrigés:')
            )
            for fix in fixed:
                self.stdout.write(f"  - {fix}")
        
        # Vérifier les fichiers JavaScript
        js_issues = self.validate_js_files(template_dir)
        if js_issues:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Problèmes JavaScript détectés:')
            )
            for issue in js_issues:
                self.stdout.write(f"  - {issue}")

    def validate_template_file(self, filepath):
        """Valide un fichier de template individuel"""
        issues = []
        relative_path = os.path.relpath(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            issues.append(f"{relative_path}: Erreur de lecture - {e}")
            return issues
        
        # Vérifier la présence de {% load i18n %}
        if '{% trans ' in content or '{% blocktrans ' in content:
            if '{% load i18n %}' not in content:
                issues.append(f"{relative_path}: Utilise des balises de traduction mais manque {% load i18n %}")
        
        # Chercher les chaînes hardcodées en français (patterns communs)
        french_patterns = [
            r'>\s*[A-Z][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý\s]+\s*<',  # Texte entre balises
            r'placeholder="[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý\s]*"',  # Placeholders
            r'title="[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý\s]*"',  # Titres
        ]
        
        for pattern in french_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # Éviter les faux positifs (variables, tags Django, etc.)
                if not any(marker in match for marker in ['{{', '{%', 'var ', 'function', 'class=']):
                    # Vérifier si c'est probablement du français
                    if self.is_likely_french(match.strip('><"\'')):
                        issues.append(f"{relative_path}: Texte potentiellement non traduit - '{match.strip()}'")
        
        # Chercher les chaînes JavaScript non traduites
        js_patterns = [
            r'alert\s*\(\s*["\'][^"\']+["\']\s*\)',
            r'confirm\s*\(\s*["\'][^"\']+["\']\s*\)',
            r'console\.log\s*\(\s*["\'][^"\']+["\']\s*\)',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                issues.append(f"{relative_path}: JavaScript non traduit - {match}")
        
        return issues

    def is_likely_french(self, text):
        """Détermine si un texte est probablement en français"""
        if len(text) < 3:
            return False
            
        # Mots français communs qui ne devraient pas être hardcodés
        french_words = [
            'ajouter', 'modifier', 'supprimer', 'enregistrer', 'annuler',
            'créer', 'nouveau', 'tableau', 'tâche', 'tâches',
            'chargement', 'erreur', 'succès', 'confirmer',
            'général', 'club', 'entraînement', 'compétition',
            'aujourd', 'demain', 'hier', 'retard',
            'description', 'commentaire', 'assigné', 'priorité'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in french_words)

    def validate_js_files(self, template_dir):
        """Valide les fichiers JavaScript intégrés"""
        issues = []
        
        # Chercher les fichiers avec du JavaScript
        html_files = glob.glob(os.path.join(template_dir, '**', '*.html'), recursive=True)
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extraire le contenu JavaScript
                js_content = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
                
                for js in js_content:
                    # Chercher les chaînes hardcodées
                    string_matches = re.findall(r'["\'][^"\']*["\']', js)
                    for match in string_matches:
                        text = match.strip('"\'')
                        if self.is_likely_french(text) and len(text) > 2:
                            # Vérifier si c'est déjà dans les traductions
                            if 'window.taskManagementConfig.i18n.' not in js:
                                issues.append(f"{os.path.relpath(html_file)}: JS hardcodé - {match}")
                            
            except Exception as e:
                issues.append(f"{os.path.relpath(html_file)}: Erreur validation JS - {e}")
                
        return issues

    def fix_template_file(self, filepath, issues):
        """Tente de corriger automatiquement les problèmes"""
        fixed_count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Ajouter {% load i18n %} si nécessaire
            if '{% trans ' in content or '{% blocktrans ' in content:
                if '{% load i18n %}' not in content:
                    # Chercher la première ligne {% extends %} ou {% load %}
                    lines = content.split('\n')
                    insert_line = 0
                    
                    for i, line in enumerate(lines):
                        if '{% extends ' in line:
                            insert_line = i + 1
                            break
                        elif '{% load ' in line:
                            insert_line = i + 1
                    
                    lines.insert(insert_line, '{% load i18n %}')
                    content = '\n'.join(lines)
                    fixed_count += 1
            
            # Sauvegarder si des modifications ont été apportées
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erreur lors de la correction de {filepath}: {e}")
            )
            
        return fixed_count