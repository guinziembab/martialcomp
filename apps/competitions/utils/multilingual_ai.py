import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import get_language, activate
import re

# Imports conditionnels pour éviter les erreurs si les bibliothèques ne sont pas installées
try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning("langdetect non disponible - détection de langue désactivée")

try:
    from deep_translator import GoogleTranslator, BingTranslator, LibreTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logging.warning("deep-translator non disponible - traduction automatique désactivée")

logger = logging.getLogger(__name__)

class MultilingualAI:
    """Service IA pour la détection automatique de langue et la traduction."""
    
    def __init__(self):
        # Langues supportées par MartialComp
        self.supported_languages = {
            'fr': 'Français',
            'en': 'English', 
            'es': 'EspaÃ±ol',
            'de': 'Deutsch',
            'it': 'Italiano',
            'ar': 'Ø§Ù„Ø¹Ø±Ø¨ÙŠØ©'
        }
        
        # Mapping des codes de langue
        self.language_mapping = {
            'fr': 'fr',
            'en': 'en', 
            'es': 'es',
            'de': 'de',
            'it': 'it',
            'ar': 'ar',
            'ca': 'es',  # Catalan -> Espagnol
            'pt': 'es',  # Portugais -> Espagnol
            'nl': 'de',  # Néerlandais -> Allemand
        }
        
        # Cache des traductions pour éviter les appels répétés
        self.translation_cache_timeout = 86400  # 24 heures
        
        # Services de traduction par ordre de préférence
        self.translator_services = [
            'google',
            'bing', 
            'libre'
        ]
        
        # Mots-clés spécifiques aux arts martiaux par langue
        self.martial_arts_keywords = {
            'fr': [
                'karaté', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
                'ceinture', 'grade', 'dan', 'kyu', 'dojo', 'sensei', 'maÃ®tre',
                'combat', 'compétition', 'entraÃ®nement', 'technique', 'kata'
            ],
            'en': [
                'karate', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
                'belt', 'grade', 'dan', 'kyu', 'dojo', 'sensei', 'master',
                'fight', 'competition', 'training', 'technique', 'kata'
            ],
            'es': [
                'karate', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
                'cinturÃ³n', 'grado', 'dan', 'kyu', 'dojo', 'sensei', 'maestro',
                'combate', 'competiciÃ³n', 'entrenamiento', 'técnica', 'kata'
            ],
            'de': [
                'karate', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
                'gÃ¼rtel', 'grad', 'dan', 'kyu', 'dojo', 'sensei', 'meister',
                'kampf', 'wettkampf', 'training', 'technik', 'kata'
            ],
            'it': [
                'karate', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
                'cintura', 'grado', 'dan', 'kyu', 'dojo', 'sensei', 'maestro',
                'combattimento', 'competizione', 'allenamento', 'tecnica', 'kata'
            ]
        }
    
    def detect_language(self, text: str, confidence_threshold: float = 0.8) -> Tuple[Optional[str], float]:
        """
        Détecte la langue d'un texte avec IA.
        
        Args:
            text: Texte Ã  analyser
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Tuple (code_langue, score_confiance) ou (None, 0.0) si échec
        """
        if not LANGDETECT_AVAILABLE:
            return None, 0.0
        
        if not text or len(text.strip()) < 3:
            return None, 0.0
        
        # Nettoyer le texte
        cleaned_text = self._clean_text_for_detection(text)
        
        try:
            # Détecter avec scores de confiance
            language_probs = detect_langs(cleaned_text)
            
            if not language_probs:
                return None, 0.0
            
            # Prendre la langue avec la plus haute probabilité
            best_lang = language_probs[0]
            detected_lang = best_lang.lang
            confidence = best_lang.prob
            
            # Mapper vers les langues supportées
            mapped_lang = self.language_mapping.get(detected_lang, detected_lang)
            
            # Vérifier si la langue est supportée
            if mapped_lang not in self.supported_languages:
                return None, 0.0
            
            # Bonus de confiance pour les mots-clés d'arts martiaux
            if mapped_lang in self.martial_arts_keywords:
                martial_keywords = self.martial_arts_keywords[mapped_lang]
                keyword_matches = sum(1 for keyword in martial_keywords if keyword.lower() in cleaned_text.lower())
                
                if keyword_matches > 0:
                    # Augmenter la confiance basée sur les mots-clés spécifiques
                    keyword_bonus = min(keyword_matches * 0.1, 0.3)
                    confidence = min(confidence + keyword_bonus, 1.0)
            
            # Vérifier le seuil de confiance
            if confidence >= confidence_threshold:
                return mapped_lang, confidence
            else:
                return None, confidence
                
        except LangDetectException as e:
            logger.warning(f"Erreur de détection de langue: {e}")
            return None, 0.0
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la détection: {e}")
            return None, 0.0
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Nettoie le texte pour améliorer la détection de langue."""
        # Supprimer les URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Supprimer les emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Supprimer les numéros de téléphone
        text = re.sub(r'[\+]?[\d\s\-\(\)\.]{8,}', '', text)
        
        # Supprimer les caractères spéciaux en gardant les accents
        text = re.sub(r'[^\w\s\Ã€-Ã¿]', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def auto_translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> Optional[str]:
        """
        Traduit automatiquement un texte vers la langue cible.
        
        Args:
            text: Texte Ã  traduire
            target_language: Code de langue cible (ex: 'fr', 'en')
            source_language: Code de langue source (détection auto si None)
            
        Returns:
            Texte traduit ou None si échec
        """
        if not TRANSLATOR_AVAILABLE:
            logger.warning("Services de traduction non disponibles")
            return None
        
        if not text or not text.strip():
            return text
        
        # Vérifier si la langue cible est supportée
        if target_language not in self.supported_languages:
            logger.warning(f"Langue cible non supportée: {target_language}")
            return None
        
        # Détecter la langue source si non fournie
        if not source_language:
            detected_lang, confidence = self.detect_language(text)
            if detected_lang and confidence > 0.7:
                source_language = detected_lang
            else:
                logger.warning("Impossible de détecter la langue source")
                return None
        
        # Ne pas traduire si déjÃ  dans la bonne langue
        if source_language == target_language:
            return text
        
        # Vérifier le cache
        cache_key = f"translation_{hash(text)}_{source_language}_{target_language}"
        cached_translation = cache.get(cache_key)
        if cached_translation:
            return cached_translation
        
        # Essayer les différents services de traduction
        translation = None
        for service in self.translator_services:
            try:
                translation = self._translate_with_service(text, source_language, target_language, service)
                if translation:
                    break
            except Exception as e:
                logger.warning(f"Ã‰chec traduction avec {service}: {e}")
                continue
        
        # Mettre en cache si succès
        if translation:
            cache.set(cache_key, translation, self.translation_cache_timeout)
            
        return translation
    
    def _translate_with_service(self, text: str, source_lang: str, target_lang: str, service: str) -> Optional[str]:
        """Traduit avec un service spécifique."""
        try:
            if service == 'google':
                translator = GoogleTranslator(source=source_lang, target=target_lang)
            elif service == 'bing':
                translator = BingTranslator(source=source_lang, target=target_lang)
            elif service == 'libre':
                translator = LibreTranslator(source=source_lang, target=target_lang)
            else:
                return None
            
            # Diviser les textes longs en chunks
            if len(text) > 4000:
                chunks = self._split_text_for_translation(text)
                translated_chunks = []
                
                for chunk in chunks:
                    translated_chunk = translator.translate(chunk)
                    if translated_chunk:
                        translated_chunks.append(translated_chunk)
                    else:
                        return None
                
                return ' '.join(translated_chunks)
            else:
                return translator.translate(text)
                
        except Exception as e:
            logger.error(f"Erreur de traduction avec {service}: {e}")
            return None
    
    def _split_text_for_translation(self, text: str, max_chunk_size: int = 4000) -> List[str]:
        """Divise un texte long en chunks pour la traduction."""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Si ajouter cette phrase dépasse la limite
            if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Phrase trop longue, la forcer
                    chunks.append(sentence)
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def bulk_translate_content(self, content_dict: Dict[str, str], target_language: str) -> Dict[str, str]:
        """
        Traduit en lot un dictionnaire de contenus.
        
        Args:
            content_dict: Dictionnaire {clé: texte}
            target_language: Langue cible
            
        Returns:
            Dictionnaire traduit
        """
        translated_content = {}
        
        for key, text in content_dict.items():
            if not text or not isinstance(text, str):
                translated_content[key] = text
                continue
            
            translated_text = self.auto_translate(text, target_language)
            translated_content[key] = translated_text if translated_text else text
        
        return translated_content
    
    def detect_user_language_preference(self, user_texts: List[str]) -> Optional[str]:
        """
        Détecte la langue préférée d'un utilisateur basée sur ses textes.
        
        Args:
            user_texts: Liste des textes de l'utilisateur
            
        Returns:
            Code de langue détecté ou None
        """
        if not user_texts:
            return None
        
        # Combiner tous les textes
        combined_text = ' '.join(filter(None, user_texts))
        
        if len(combined_text.strip()) < 10:
            return None
        
        # Détecter la langue
        detected_lang, confidence = self.detect_language(combined_text, confidence_threshold=0.6)
        
        if detected_lang and confidence > 0.6:
            return detected_lang
        
        return None
    
    def get_translation_statistics(self) -> Dict[str, int]:
        """Retourne des statistiques sur les traductions."""
        # Cette méthode pourrait Ãªtre étendue pour tracker les traductions
        return {
            'languages_supported': len(self.supported_languages),
            'translation_services': len(self.translator_services),
            'langdetect_available': LANGDETECT_AVAILABLE,
            'translator_available': TRANSLATOR_AVAILABLE
        }
    
    def validate_translation_quality(self, original: str, translated: str, target_lang: str) -> Dict[str, float]:
        """
        Valide la qualité d'une traduction (basique).
        
        Returns:
            Dictionnaire avec scores de qualité
        """
        scores = {
            'length_ratio': 0.0,
            'keyword_preservation': 0.0,
            'overall_quality': 0.0
        }
        
        if not original or not translated:
            return scores
        
        # Score basé sur la longueur (les traductions ne devraient pas Ãªtre trop différentes)
        length_ratio = len(translated) / len(original)
        if 0.5 <= length_ratio <= 2.0:
            scores['length_ratio'] = 1.0 - abs(1.0 - length_ratio)
        
        # Préservation des mots-clés d'arts martiaux
        if target_lang in self.martial_arts_keywords:
            original_keywords = set()
            translated_keywords = set()
            
            # Mots-clés dans l'original
            for keyword in self.martial_arts_keywords.get('en', []):  # Utiliser anglais comme référence
                if keyword.lower() in original.lower():
                    original_keywords.add(keyword)
            
            # Mots-clés dans la traduction
            for keyword in self.martial_arts_keywords[target_lang]:
                if keyword.lower() in translated.lower():
                    translated_keywords.add(keyword)
            
            # Score de préservation
            if original_keywords:
                preserved_ratio = len(translated_keywords) / len(original_keywords)
                scores['keyword_preservation'] = min(preserved_ratio, 1.0)
            else:
                scores['keyword_preservation'] = 1.0
        
        # Score global
        scores['overall_quality'] = (scores['length_ratio'] + scores['keyword_preservation']) / 2
        
        return scores
