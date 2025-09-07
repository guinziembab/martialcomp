"""
DeepL Translation Service Integration for Django Rosetta
"""
import deepl
from django.conf import settings
from django.utils.translation import get_language_from_request
import logging

logger = logging.getLogger(__name__)

class DeepLTranslationService:
    """Service for integrating DeepL with Django Rosetta"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'DEEPL_API_KEY', None)
        self.translator = None
        
        if self.api_key:
            try:
                self.translator = deepl.Translator(self.api_key)
                logger.info("DeepL translator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize DeepL translator: {e}")
        else:
            # Diminuer le bruit de logs si la clé n'est pas configurée
            logger.debug("DeepL API key not found; DeepL features disabled")
    
    def is_available(self):
        """Check if DeepL service is available"""
        return self.translator is not None
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        if not self.is_available():
            return []
        
        try:
            languages = self.translator.get_source_languages()
            return [lang.code.lower() for lang in languages]
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
    
    def translate_text(self, text, target_language, source_language='auto'):
        """
        Translate text using DeepL
        
        Args:
            text (str): Text to translate
            target_language (str): Target language code (e.g., 'fr', 'es')
            source_language (str): Source language code or 'auto' for auto-detection
            
        Returns:
            str: Translated text or original text if translation fails
        """
        if not self.is_available():
            logger.warning("DeepL service not available")
            return text
        
        if not text or not text.strip():
            return text
            
        try:
            # Map Django language codes to DeepL language codes
            target_lang = self._map_language_code(target_language)
            source_lang = None if source_language == 'auto' else self._map_language_code(source_language)
            
            result = self.translator.translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang
            )
            
            logger.info(f"Translated text from {source_language} to {target_language}")
            return result.text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    def translate_multiple(self, texts, target_language, source_language='auto'):
        """
        Translate multiple texts at once (more efficient for batch operations)
        
        Args:
            texts (list): List of texts to translate
            target_language (str): Target language code
            source_language (str): Source language code or 'auto'
            
        Returns:
            list: List of translated texts
        """
        if not self.is_available():
            logger.warning("DeepL service not available")
            return texts
        
        if not texts:
            return texts
            
        try:
            # Filter out empty texts
            non_empty_texts = [text for text in texts if text and text.strip()]
            if not non_empty_texts:
                return texts
                
            target_lang = self._map_language_code(target_language)
            source_lang = None if source_language == 'auto' else self._map_language_code(source_language)
            
            results = self.translator.translate_text(
                non_empty_texts,
                target_lang=target_lang,
                source_lang=source_lang
            )
            
            # Map results back to original list
            translated_texts = []
            result_index = 0
            
            for original_text in texts:
                if original_text and original_text.strip():
                    translated_texts.append(results[result_index].text)
                    result_index += 1
                else:
                    translated_texts.append(original_text)
            
            logger.info(f"Translated {len(non_empty_texts)} texts from {source_language} to {target_language}")
            return translated_texts
            
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            return texts
    
    def _map_language_code(self, language_code):
        """
        Map Django language codes to DeepL language codes
        
        Args:
            language_code (str): Django language code (e.g., 'en-us', 'fr')
            
        Returns:
            str: DeepL language code
        """
        # Map Django language codes to DeepL codes
        mapping = {
            'en': 'EN',
            'en-us': 'EN-US',
            'en-gb': 'EN-GB',
            'fr': 'FR',
            'es': 'ES',
            'de': 'DE',
            'it': 'IT',
            'pt': 'PT',
            'pt-br': 'PT-BR',
            'ru': 'RU',
            'ja': 'JA',
            'zh-hans': 'ZH',
            'zh-cn': 'ZH-CN',
            'zh-tw': 'ZH-TW',
            'ko': 'KO',
            'nl': 'NL',
            'pl': 'PL',
            'sv': 'SV',
            'da': 'DA',
            'no': 'NB',
            'fi': 'FI',
            'el': 'EL',
            'cs': 'CS',
            'sk': 'SK',
            'sl': 'SL',
            'et': 'ET',
            'lv': 'LV',
            'lt': 'LT',
            'hu': 'HU',
            'bg': 'BG',
            'ro': 'RO',
            'tr': 'TR',
            'uk': 'UK',
            'ar': 'AR',
        }
        
        # Get base language code (e.g., 'en' from 'en-us')
        base_code = language_code.lower().split('-')[0]
        
        # Return mapped code or try the full code
        return mapping.get(language_code.lower(), mapping.get(base_code, language_code.upper()))
    
    def get_usage_info(self):
        """Get current API usage information"""
        if not self.is_available():
            return None
            
        try:
            usage = self.translator.get_usage()
            return {
                'character_count': usage.character.count,
                'character_limit': usage.character.limit,
                'characters_remaining': usage.character.limit - usage.character.count if usage.character.limit else None,
                'usage_percentage': (usage.character.count / usage.character.limit * 100) if usage.character.limit else 0
            }
        except Exception as e:
            logger.error(f"Failed to get usage info: {e}")
            return None

# Global instance
deepl_service = DeepLTranslationService()