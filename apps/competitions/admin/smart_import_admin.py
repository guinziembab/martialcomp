from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import json
import pandas as pd
from typing import Dict, Any

from apps.grades.models import import read_file, detect_file_format
from apps.grades.models import import IntelligentColumnMapper
from apps.grades.models import import DataValidator
from apps.competitions.models import import PractitionerDeduplicator

class SmartImportAdmin(admin.ModelAdmin):
    """Interface d'administration pour l'import intelligent."""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('smart-import/', self.admin_site.admin_view(self.smart_import_view), name='smart_import'),
            path('analyze-file/', self.admin_site.admin_view(self.analyze_file_view), name='analyze_file'),
            path('validate-mapping/', self.admin_site.admin_view(self.validate_mapping_view), name='validate_mapping'),
            path('detect-duplicates/', self.admin_site.admin_view(self.detect_duplicates_view), name='detect_duplicates'),
            path('merge-duplicates/', self.admin_site.admin_view(self.merge_duplicates_view), name='merge_duplicates'),
        ]
        return custom_urls + urls
    
    def smart_import_view(self, request):
        """Vue principale pour l'import intelligent."""
        context = {
            'title': 'Import Intelligent de Données',
            'opts': self.model._meta,
            'has_change_permission': True,
        }
        
        if request.method == 'POST' and request.FILES.get('import_file'):
            try:
                # Sauvegarder le fichier temporairement
                uploaded_file = request.FILES['import_file']
                file_path = default_storage.save(f'temp_imports/{uploaded_file.name}', ContentFile(uploaded_file.read()))
                full_path = default_storage.path(file_path)
                
                # Analyser le fichier
                analysis_result = self.analyze_file(full_path)
                
                # Stocker les résultats en session
                request.session['import_analysis'] = analysis_result
                request.session['import_file_path'] = full_path
                
                context['analysis'] = analysis_result
                context['step'] = 'mapping'
                
            except Exception as e:
                messages.error(request, f"Erreur lors de l'analyse du fichier: {str(e)}")
                context['step'] = 'upload'
        else:
            context['step'] = 'upload'
        
        return render(request, 'admin/smart_import.html', context)
    
    def analyze_file_view(self, request):
        """API pour analyser un fichier."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            file_path = request.session.get('import_file_path')
            if not file_path or not os.path.exists(file_path):
                return JsonResponse({'error': 'Fichier non trouvé'}, status=404)
            
            analysis = self.analyze_file(file_path)
            return JsonResponse(analysis)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def validate_mapping_view(self, request):
        """API pour valider le mapping des colonnes."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            # Récupérer le mapping depuis la requÃªte
            mapping_data = json.loads(request.body)
            column_mapping = mapping_data.get('mapping', {})
            
            file_path = request.session.get('import_file_path')
            if not file_path or not os.path.exists(file_path):
                return JsonResponse({'error': 'Fichier non trouvé'}, status=404)
            
            # Lire et valider les données
            df = read_file(file_path)
            validator = DataValidator()
            validation_result = validator.validate_dataframe(df, column_mapping)
            
            # Stocker les résultats en session
            request.session['validation_result'] = validation_result
            request.session['column_mapping'] = column_mapping
            
            return JsonResponse(validation_result)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def detect_duplicates_view(self, request):
        """API pour détecter les doublons."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            file_path = request.session.get('import_file_path')
            column_mapping = request.session.get('column_mapping')
            
            if not file_path or not column_mapping:
                return JsonResponse({'error': 'Données manquantes'}, status=400)
            
            # Lire les données
            df = read_file(file_path)
            
            # Renommer les colonnes selon le mapping
            df_mapped = df.rename(columns={v: k for k, v in column_mapping.items()})
            
            # Détecter les doublons
            deduplicator = PractitionerDeduplicator()
            duplicates = deduplicator.find_duplicates_semantic(df_mapped, threshold=0.85)
            
            # Générer les suggestions de fusion
            suggestions = deduplicator.generate_merge_suggestions(duplicates)
            
            # Stocker en session
            request.session['duplicates'] = duplicates
            request.session['merge_suggestions'] = suggestions
            
            return JsonResponse({
                'duplicates_count': len(duplicates),
                'total_duplicated_records': sum(len(group['records']) for group in duplicates),
                'suggestions': suggestions[:10],  # Limiter pour l'affichage
                'auto_merge_count': sum(1 for s in suggestions if s['auto_merge_safe'])
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def merge_duplicates_view(self, request):
        """API pour fusionner les doublons."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            merge_data = json.loads(request.body)
            merge_decisions = merge_data.get('decisions', [])
            
            suggestions = request.session.get('merge_suggestions', [])
            deduplicator = PractitionerDeduplicator()
            
            merged_records = []
            for decision in merge_decisions:
                group_id = decision['group_id']
                action = decision['action']  # 'merge', 'keep_separate', 'manual'
                
                # Trouver la suggestion correspondante
                suggestion = next((s for s in suggestions if s['group_id'] == group_id), None)
                if not suggestion:
                    continue
                
                if action == 'merge':
                    # Fusionner automatiquement
                    merged = deduplicator.merge_duplicates({
                        'records': [suggestion['suggested_master']] + suggestion['duplicates']
                    }, merge_strategy='most_complete')
                    merged_records.append(merged)
                elif action == 'keep_separate':
                    # Garder tous les enregistrements séparés
                    merged_records.extend([suggestion['suggested_master']] + suggestion['duplicates'])
            
            # Stocker les enregistrements finaux
            request.session['final_records'] = merged_records
            
            return JsonResponse({
                'success': True,
                'merged_count': len(merged_records),
                'message': f'{len(merged_records)} enregistrements prÃªts pour l\'import'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyse complète d'un fichier."""
        try:
            # Détecter le format
            file_format = detect_file_format(file_path)
            
            # Lire le fichier
            df = read_file(file_path)
            
            # Analyser les colonnes
            mapper = IntelligentColumnMapper()
            mapping_suggestions = mapper.suggest_mappings(df)
            
            # Statistiques de base
            stats = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'null_counts': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.astype(str).to_dict()
            }
            
            # Ã‰chantillon de données
            sample_data = df.head(5).to_dict(orient='records')
            
            return {
                'file_format': file_format,
                'file_size': os.path.getsize(file_path),
                'statistics': stats,
                'mapping_suggestions': mapping_suggestions,
                'sample_data': sample_data,
                'columns': list(df.columns),
                'success': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Enregistrer l'admin personnalisé
class DuplicateResolutionAdmin(admin.ModelAdmin):
    """Interface pour gérer la résolution des doublons."""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('duplicate-management/', self.admin_site.admin_view(self.duplicate_management_view), name='duplicate_management'),
            path('resolve-duplicate/', self.admin_site.admin_view(self.resolve_duplicate_view), name='resolve_duplicate'),
        ]
        return custom_urls + urls
    
    def duplicate_management_view(self, request):
        """Vue de gestion des doublons existants."""
        # Cette vue permettrait de gérer les doublons détectés dans la base existante
        context = {
            'title': 'Gestion des Doublons',
            'opts': self.model._meta,
        }
        
        if request.method == 'POST':
            # Lancer la détection de doublons sur la base existante
            try:
                from apps.competitions.models import Practitioner
                
                # Récupérer tous les pratiquants
                practitioners = Practitioner.objects.all().values(
                    'id', 'first_name', 'last_name', 'email', 'phone', 'birth_date'
                )
                df = pd.DataFrame(practitioners)
                
                if not df.empty:
                    deduplicator = PractitionerDeduplicator()
                    duplicates = deduplicator.find_duplicates_semantic(df)
                    context['duplicates'] = duplicates
                    context['duplicates_count'] = len(duplicates)
                else:
                    context['message'] = 'Aucun pratiquant trouvé dans la base de données'
                    
            except Exception as e:
                messages.error(request, f"Erreur lors de la détection: {str(e)}")
        
        return render(request, 'admin/duplicate_management.html', context)
    
    def resolve_duplicate_view(self, request):
        """API pour résoudre un doublon spécifique."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            resolution_data = json.loads(request.body)
            # Logique de résolution des doublons ici
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



