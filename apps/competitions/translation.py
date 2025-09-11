"""
Configuration de django-modeltranslation pour les modèles MartialComp
"""
from modeltranslation.translator import translator, TranslationOptions
from .models import Competition, Club, Discipline


class CompetitionTranslationOptions(TranslationOptions):
    """Configuration de traduction pour le modèle Competition"""
    fields = ('title', 'description', 'venue_name', 'address')


class ClubTranslationOptions(TranslationOptions):
    """Configuration de traduction pour le modèle Club"""
    fields = ('name', 'description', 'address')


class DisciplineTranslationOptions(TranslationOptions):
    """Configuration de traduction pour le modèle Discipline"""
    fields = ('name', 'description')


# Enregistrement des modèles pour traduction
translator.register(Competition, CompetitionTranslationOptions)
translator.register(Club, ClubTranslationOptions)
translator.register(Discipline, DisciplineTranslationOptions)
