"""
Service pour calculer les statistiques des membres par catégorie d'âge et genre.
Basé sur les catégories standard ADEPS/Fédérations sportives belges.
"""

from datetime import date
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _


def calculate_age(birth_date):
    """Calcule l'âge à partir de la date de naissance."""
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def get_age_category(age):
    """
    Retourne la catégorie d'âge basée sur les tranches standard.
    """
    if age is None:
        return 'unknown'
    if age < 6:
        return 'under_6'
    elif age <= 8:
        return '6_to_8'
    elif age <= 12:
        return '9_to_12'
    elif age <= 17:
        return '13_to_17'
    elif age <= 21:
        return '18_to_21'
    elif age <= 34:
        return '22_to_34'
    elif age <= 49:
        return '35_to_49'
    elif age <= 64:
        return '50_to_64'
    else:
        return '65_plus'


# Définition des catégories avec labels traduits
AGE_CATEGORIES = {
    'under_6': {
        'label_female': _("- de 6 ans (filles)"),
        'label_male': _("- de 6 ans (garçons)"),
        'min_age': 0,
        'max_age': 5,
        'order': 1,
    },
    '6_to_8': {
        'label_female': _("Filles de 6 à 8 ans"),
        'label_male': _("Garçons de 6 à 8 ans"),
        'min_age': 6,
        'max_age': 8,
        'order': 2,
    },
    '9_to_12': {
        'label_female': _("Filles de 9 à 12 ans"),
        'label_male': _("Garçons de 9 à 12 ans"),
        'min_age': 9,
        'max_age': 12,
        'order': 3,
    },
    '13_to_17': {
        'label_female': _("Femmes de 13 à 17 ans"),
        'label_male': _("Hommes de 13 à 17 ans"),
        'min_age': 13,
        'max_age': 17,
        'order': 4,
    },
    '18_to_21': {
        'label_female': _("Femmes de 18 à 21 ans"),
        'label_male': _("Hommes de 18 à 21 ans"),
        'min_age': 18,
        'max_age': 21,
        'order': 5,
    },
    '22_to_34': {
        'label_female': _("Femmes de 22 à 34 ans"),
        'label_male': _("Hommes de 22 à 34 ans"),
        'min_age': 22,
        'max_age': 34,
        'order': 6,
    },
    '35_to_49': {
        'label_female': _("Femmes de 35 à 49 ans"),
        'label_male': _("Hommes de 35 à 49 ans"),
        'min_age': 35,
        'max_age': 49,
        'order': 7,
    },
    '50_to_64': {
        'label_female': _("Femmes de 50 à 64 ans"),
        'label_male': _("Hommes de 50 à 64 ans"),
        'min_age': 50,
        'max_age': 64,
        'order': 8,
    },
    '65_plus': {
        'label_female': _("Femmes de 65 ans et plus"),
        'label_male': _("Hommes de 65 ans et plus"),
        'min_age': 65,
        'max_age': 999,
        'order': 9,
    },
}

# Qualifications encadrement
ENCADREMENT_QUALIFICATIONS = [
    ('sans_qualification', _("Sans qualification")),
    ('en_formation', _("En formation")),
    ('aei_aess', _("AEI - AESS")),
    ('animateur', _("Animateur")),
    ('adeps_ms_niveau_1', _("ADEPS MS niveau 1")),
    ('adeps_ms_niveau_2', _("ADEPS MS niveau 2")),
    ('adeps_ms_niveau_3_4', _("ADEPS MS niveau 3; 4")),
    ('autre_formation', _("Autre formation")),
]


def calculate_member_statistics(practitioners_queryset):
    """
    Calcule les statistiques détaillées des membres par catégorie d'âge et genre.

    Args:
        practitioners_queryset: QuerySet de pratiquants

    Returns:
        dict: Statistiques structurées pour le template
    """
    from apps.competitions.models import Practitioner

    today = date.today()

    # Si le queryset est slicé, on doit récupérer les IDs et refaire un queryset filtrable
    # Ceci permet de gérer le cas où practitioners_queryset[:20] est passé
    try:
        # Tenter de compter directement (fonctionne si pas slicé)
        total_count = practitioners_queryset.count()
        # Vérifier si on peut filtrer
        practitioners_queryset.filter(pk__isnull=False)
        qs = practitioners_queryset
    except TypeError:
        # Si slicé, récupérer les IDs et créer un nouveau queryset
        ids = list(practitioners_queryset.values_list('id', flat=True))
        qs = Practitioner.objects.filter(id__in=ids)
        total_count = len(ids)

    # Initialiser les compteurs
    stats = {
        'total': total_count,
        'total_female': 0,
        'total_male': 0,
        'total_unknown_gender': 0,
        'categories': [],
        'encadrement': {
            'total': 0,
            'qualifications': []
        }
    }

    # Filtres pour les genres (supporter les deux formats)
    female_genders = ['F', 'female', 'Female', 'f']
    male_genders = ['M', 'male', 'Male', 'm']

    # Compter par genre avec filter direct (évite les doublons causés par les jointures)
    stats['total_female'] = qs.filter(gender__in=female_genders).count()
    stats['total_male'] = qs.filter(gender__in=male_genders).count()
    stats['total_unknown_gender'] = total_count - stats['total_female'] - stats['total_male']

    # Calculer les statistiques par catégorie d'âge et genre
    for cat_key, cat_info in sorted(AGE_CATEGORIES.items(), key=lambda x: x[1]['order']):
        min_age = cat_info['min_age']
        max_age = cat_info['max_age']

        # Calculer les dates de naissance correspondantes
        # Pour min_age ans: né avant today - min_age years
        # Pour max_age ans: né après today - (max_age + 1) years
        min_birth_date = date(today.year - max_age - 1, today.month, today.day)
        max_birth_date = date(today.year - min_age, today.month, today.day)

        # Filtrer par date de naissance (le champ est birth_date dans le modèle)
        age_filter = Q(birth_date__gt=min_birth_date, birth_date__lte=max_birth_date)

        # Compter femmes dans cette catégorie (supporter 'F' et 'female')
        female_count = qs.filter(
            age_filter,
            gender__in=female_genders
        ).count()

        # Compter hommes dans cette catégorie (supporter 'M' et 'male')
        male_count = qs.filter(
            age_filter,
            gender__in=male_genders
        ).count()

        # Ajouter la catégorie aux stats
        # Ne pas utiliser str() pour préserver la traduction lazy
        stats['categories'].append({
            'key': cat_key,
            'label_female': cat_info['label_female'],
            'label_male': cat_info['label_male'],
            'female_count': female_count,
            'male_count': male_count,
            'total': female_count + male_count,
            'order': cat_info['order'],
        })

    # Calculer les statistiques d'encadrement (si le champ existe)
    # Pour l'instant, on retourne des valeurs par défaut
    # TODO: Implémenter quand le modèle d'encadrement sera disponible
    # Ne pas utiliser str() pour préserver la traduction lazy
    stats['encadrement'] = {
        'total': 0,
        'qualifications': [
            {'label': label, 'count': 0}
            for _, label in ENCADREMENT_QUALIFICATIONS
        ]
    }

    return stats


def get_grade_distribution(practitioners_queryset):
    """
    Calcule la distribution par grade des pratiquants.

    Args:
        practitioners_queryset: QuerySet de pratiquants

    Returns:
        dict: Distribution avec pourcentages
    """
    from apps.competitions.models import Practitioner

    # Si le queryset est slicé, on doit récupérer les IDs et refaire un queryset filtrable
    try:
        total = practitioners_queryset.count()
        practitioners_queryset.filter(pk__isnull=False)
        qs = practitioners_queryset
    except TypeError:
        ids = list(practitioners_queryset.values_list('id', flat=True))
        qs = Practitioner.objects.filter(id__in=ids)
        total = len(ids)

    if total == 0:
        return {
            'beginners': {'count': 0, 'percentage': 0},
            'intermediates': {'count': 0, 'percentage': 0},
            'advanced': {'count': 0, 'percentage': 0},
        }

    # Essayer de récupérer les grades
    try:
        from apps.grades.models import PractitionerGrade

        # Compter les pratiquants avec grades
        practitioners_with_grades = qs.filter(
            practitioner_grades__isnull=False
        ).distinct()

        beginners = 0
        intermediates = 0
        advanced = 0

        for practitioner in practitioners_with_grades:
            # Récupérer le grade actuel
            current_grade = PractitionerGrade.objects.filter(
                practitioner=practitioner,
                is_active=True
            ).order_by('-obtained_date').first()

            if current_grade and current_grade.grade:
                grade_level = getattr(current_grade.grade, 'level', 0)
                if grade_level <= 3:
                    beginners += 1
                elif grade_level <= 6:
                    intermediates += 1
                else:
                    advanced += 1
            else:
                beginners += 1

        # Les pratiquants sans grade sont considérés comme débutants
        practitioners_without_grades = total - practitioners_with_grades.count()
        beginners += practitioners_without_grades

    except Exception:
        # Si pas de modèle de grade, tous sont débutants
        beginners = total
        intermediates = 0
        advanced = 0

    return {
        'beginners': {
            'count': beginners,
            'percentage': round(beginners * 100 / total) if total > 0 else 0
        },
        'intermediates': {
            'count': intermediates,
            'percentage': round(intermediates * 100 / total) if total > 0 else 0
        },
        'advanced': {
            'count': advanced,
            'percentage': round(advanced * 100 / total) if total > 0 else 0
        },
    }
