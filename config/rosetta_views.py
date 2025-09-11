"""
Custom Rosetta views with DeepL integration
"""
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.shortcuts import render
from config.translation_service import deepl_service
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class DeepLTranslationView(View):
    """API endpoint for DeepL translation suggestions"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            target_language = data.get('target_language', '')
            source_language = data.get('source_language', 'auto')
            
            if not text:
                return JsonResponse({
                    'error': 'No text provided',
                    'suggestion': ''
                }, status=400)
            
            if not deepl_service.is_available():
                return JsonResponse({
                    'error': 'DeepL service not available',
                    'suggestion': ''
                }, status=503)
            
            # Translate text
            translated_text = deepl_service.translate_text(
                text, 
                target_language, 
                source_language
            )
            
            return JsonResponse({
                'suggestion': translated_text,
                'source_language': source_language,
                'target_language': target_language,
                'original_text': text
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'suggestion': ''
            }, status=400)
        except Exception as e:
            logger.error(f"Translation API error: {e}")
            return JsonResponse({
                'error': 'Translation failed',
                'suggestion': ''
            }, status=500)

@staff_member_required
def deepl_status(request):
    """View to check DeepL service status and usage"""
    context = {
        'is_available': deepl_service.is_available(),
        'supported_languages': deepl_service.get_supported_languages(),
        'usage_info': deepl_service.get_usage_info(),
        'api_key_configured': bool(deepl_service.api_key)
    }
    
    return render(request, 'admin/deepl_status.html', context)

@staff_member_required
def batch_translate(request):
    """View for batch translation interface"""
    if request.method == 'POST':
        # Handle batch translation request
        target_language = request.POST.get('target_language')
        source_language = request.POST.get('source_language', 'auto')
        app_name = request.POST.get('app_name', '')
        
        # This would trigger the management command
        # For now, just show the form
        pass
    
    # Get available languages from Django settings
    from django.conf import settings
    available_languages = [code for code, name in settings.LANGUAGES]
    
    context = {
        'available_languages': available_languages,
        'deepl_available': deepl_service.is_available(),
        'usage_info': deepl_service.get_usage_info(),
    }
    
    return render(request, 'admin/batch_translate.html', context)