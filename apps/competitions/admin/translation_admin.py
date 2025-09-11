from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import JsonResponse
from django.core.management import call_command
from django.utils.translation import gettext_lazy as _
from apps.competitions.models import import MultilingualAI
import json
import logging

logger = logging.getLogger(__name__)

class TranslationManagementAdmin(admin.ModelAdmin):
    """Interface d'administration pour la gestion des traductions IA."""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('translation-dashboard/', self.admin_site.admin_view(self.translation_dashboard_view), name='translation_dashboard'),
            path('detect-language/', self.admin_site.admin_view(self.detect_language_view), name='detect_language'),
            path('translate-content/', self.admin_site.admin_view(self.translate_content_view), name='translate_content'),
            path('batch-translate/', self.admin_site.admin_view(self.batch_translate_view), name='batch_translate'),
            path('translation-stats/', self.admin_site.admin_view(self.translation_stats_view), name='translation_stats'),
        ]
        return custom_urls + urls
    
    def translation_dashboard_view(self, request):
        """Tableau de bord principal pour la gestion des traductions."""
        multilingual_ai = MultilingualAI()
        
        context = {
            'title': 'Gestion des Traductions IA',
            'opts': self.model._meta,
            'supported_languages': multilingual_ai.supported_languages,
            'translation_stats': multilingual_ai.get_translation_statistics(),
            'has_change_permission': True,
        }
        
        # Récupérer les statistiques de contenu
        try:
            from apps.competitions.models import Practitioner, Club, Discipline
            
            context['content_stats'] = {
                'practitioners': Practitioner.objects.count(),
                'clubs': Club.objects.count(),
                'disciplines': Discipline.objects.count(),
            }
            
            # Analyser la langue dominante du contenu existant
            sample_texts = []
            
            # Ã‰chantillon de pratiquants
            for p in Practitioner.objects.filter(bio__isnull=False).exclude(bio='')[:10]:
                if p.bio:
                    sample_texts.append(p.bio)
            
            # Ã‰chantillon de clubs
            for c in Club.objects.filter(description__isnull=False).exclude(description='')[:10]:
                if c.description:
                    sample_texts.append(c.description)
            
            if sample_texts:
                detected_lang = multilingual_ai.detect_user_language_preference(sample_texts)
                context['detected_primary_language'] = detected_lang
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            context['content_stats'] = {}
        
        return render(request, 'admin/translation_dashboard.html', context)
    
    def detect_language_view(self, request):
        """API pour détecter la langue d'un texte."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if not text.strip():
                return JsonResponse({'error': 'Texte vide'}, status=400)
            
            multilingual_ai = MultilingualAI()
            detected_lang, confidence = multilingual_ai.detect_language(text)
            
            result = {
                'detected_language': detected_lang,
                'confidence': confidence,
                'language_name': multilingual_ai.supported_languages.get(detected_lang, 'Inconnue') if detected_lang else 'Inconnue',
                'success': detected_lang is not None
            }
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            logger.error(f"Erreur lors de la détection: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def translate_content_view(self, request):
        """API pour traduire du contenu."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            target_language = data.get('target_language', '')
            source_language = data.get('source_language')
            
            if not text.strip():
                return JsonResponse({'error': 'Texte vide'}, status=400)
            
            if not target_language:
                return JsonResponse({'error': 'Langue cible requise'}, status=400)
            
            multilingual_ai = MultilingualAI()
            
            # Détecter la langue source si non fournie
            if not source_language:
                detected_lang, confidence = multilingual_ai.detect_language(text)
                if detected_lang and confidence > 0.7:
                    source_language = detected_lang
                else:
                    return JsonResponse({
                        'error': 'Impossible de détecter la langue source',
                        'detected_confidence': confidence
                    }, status=400)
            
            # Traduire
            translated_text = multilingual_ai.auto_translate(text, target_language, source_language)
            
            if not translated_text:
                return JsonResponse({'error': 'Ã‰chec de la traduction'}, status=500)
            
            # Valider la qualité
            quality_scores = multilingual_ai.validate_translation_quality(text, translated_text, target_language)
            
            result = {
                'original_text': text,
                'translated_text': translated_text,
                'source_language': source_language,
                'target_language': target_language,
                'quality_scores': quality_scores,
                'success': True
            }
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            logger.error(f"Erreur lors de la traduction: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def batch_translate_view(self, request):
        """Vue pour la traduction en lot."""
        if request.method == 'POST':
            try:
                target_language = request.POST.get('target_language')
                model_name = request.POST.get('model', 'all')
                field_name = request.POST.get('field')
                dry_run = request.POST.get('dry_run') == 'on'
                force = request.POST.get('force') == 'on'
                
                if not target_language:
                    messages.error(request, "Langue cible requise")
                    return redirect('admin:translation_dashboard')
                
                # Lancer la commande de traduction
                try:
                    call_command(
                        'auto_translate',
                        target_language=target_language,
                        model=model_name,
                        field=field_name if field_name else None,
                        dry_run=dry_run,
                        force=force,
                        batch_size=50
                    )
                    
                    action = "simulée" if dry_run else "effectuée"
                    messages.success(request, f"Traduction en lot {action} avec succès vers {target_language}")
                    
                except Exception as e:
                    messages.error(request, f"Erreur lors de la traduction: {str(e)}")
                
                return redirect('admin:translation_dashboard')
                
            except Exception as e:
                messages.error(request, f"Erreur: {str(e)}")
                return redirect('admin:translation_dashboard')
        
        # GET request - afficher le formulaire
        multilingual_ai = MultilingualAI()
        
        context = {
            'title': 'Traduction en Lot',
            'opts': self.model._meta,
            'supported_languages': multilingual_ai.supported_languages,
            'model_choices': [
                ('all', 'Tous les modèles'),
                ('practitioner', 'Pratiquants'),
                ('club', 'Clubs'),
                ('discipline', 'Disciplines'),
            ],
            'field_choices': {
                'practitioner': [
                    ('bio', 'Biographie'),
                    ('teaching_philosophy', 'Philosophie d\'enseignement'),
                    ('specializations', 'Spécialisations'),
                ],
                'club': [
                    ('description', 'Description'),
                    ('history', 'Histoire'),
                    ('mission', 'Mission'),
                ],
                'discipline': [
                    ('description', 'Description'),
                    ('rules', 'Règles'),
                    ('history', 'Histoire'),
                ]
            }
        }
        
        return render(request, 'admin/batch_translate.html', context)
    
    def translation_stats_view(self, request):
        """API pour récupérer les statistiques de traduction."""
        try:
            multilingual_ai = MultilingualAI()
            
            # Statistiques générales
            general_stats = multilingual_ai.get_translation_statistics()
            
            # Analyser le contenu existant
            from apps.competitions.models import Practitioner, Club, Discipline
            
            content_analysis = {}
            
            # Analyser les pratiquants
            practitioners_with_bio = Practitioner.objects.filter(bio__isnull=False).exclude(bio='')
            if practitioners_with_bio.exists():
                sample_bios = [p.bio for p in practitioners_with_bio[:20]]
                detected_lang = multilingual_ai.detect_user_language_preference(sample_bios)
                content_analysis['practitioners'] = {
                    'total': Practitioner.objects.count(),
                    'with_bio': practitioners_with_bio.count(),
                    'detected_language': detected_lang
                }
            
            # Analyser les clubs
            clubs_with_desc = Club.objects.filter(description__isnull=False).exclude(description='')
            if clubs_with_desc.exists():
                sample_descriptions = [c.description for c in clubs_with_desc[:20]]
                detected_lang = multilingual_ai.detect_user_language_preference(sample_descriptions)
                content_analysis['clubs'] = {
                    'total': Club.objects.count(),
                    'with_description': clubs_with_desc.count(),
                    'detected_language': detected_lang
                }
            
            # Vérifier les traductions existantes
            translation_coverage = {}
            for lang_code, lang_name in multilingual_ai.supported_languages.items():
                coverage = {}
                
                # Couverture pratiquants
                practitioners_translated = Practitioner.objects.filter(**{f'bio_{lang_code}__isnull': False}).exclude(**{f'bio_{lang_code}': ''})
                coverage['practitioners'] = {
                    'translated': practitioners_translated.count(),
                    'total_with_content': practitioners_with_bio.count(),
                    'percentage': (practitioners_translated.count() / practitioners_with_bio.count() * 100) if practitioners_with_bio.count() > 0 else 0
                }
                
                # Couverture clubs
                clubs_translated = Club.objects.filter(**{f'description_{lang_code}__isnull': False}).exclude(**{f'description_{lang_code}': ''})
                coverage['clubs'] = {
                    'translated': clubs_translated.count(),
                    'total_with_content': clubs_with_desc.count(),
                    'percentage': (clubs_translated.count() / clubs_with_desc.count() * 100) if clubs_with_desc.count() > 0 else 0
                }
                
                translation_coverage[lang_code] = coverage
            
            result = {
                'general_stats': general_stats,
                'content_analysis': content_analysis,
                'translation_coverage': translation_coverage,
                'success': True
            }
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return JsonResponse({'error': str(e)}, status=500)



