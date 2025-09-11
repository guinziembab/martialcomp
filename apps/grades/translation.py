"""
Configuration de django-modeltranslation pour les modèles de grades
"""
from django.apps import apps
from modeltranslation.translator import register, TranslationOptions

def register_translations():
    """Enregistre les modèles pour la traduction de manière sécurisée."""
    try:
        # Vérifier que les modèles sont chargés
        if apps.is_installed('grades'):
            from .models import Grade, GradeCategory

            @register(Grade)
            class GradeTranslationOptions(TranslationOptions):
                fields = ('name', 'requirements_text')

            @register(GradeCategory)
            class GradeCategoryTranslationOptions(TranslationOptions):
                fields = ('name', 'description')

            print("âœ… Modèles Grade et GradeCategory enregistrés pour la traduction")
    except Exception as e:
        print(f"âŒ Erreur lors de l'enregistrement des modèles pour la traduction: {e}")

# Appeler la fonction d'enregistrement
register_translations()

