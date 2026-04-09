# -*- coding: utf-8 -*-
"""
Podium Order Service - Tri des catégories pour la cérémonie de remise des récompenses.
Ordonne les catégories par groupe d'âge (jeunes→adultes), grade, poids et genre.
"""
from django.db.models import F, Case, When, Value, IntegerField
from django.utils.translation import gettext_lazy as _

from apps.competitions.models import CompetitionCategory


class PodiumOrderService:
    """
    Service pour ordonner les catégories selon l'ordre protocolaire
    de la cérémonie de remise des récompenses.

    Ordre de priorité:
    1. Groupe d'âge (jeunes → adultes)
    2. Grade (débutants → avancés)
    3. Poids (légers → lourds)
    4. Genre (femmes → hommes → mixte)
    """

    # Mapping des groupes d'âge avec ordre de priorité
    AGE_GROUP_ORDER = {
        'poussins': 1,      # 6-7 ans
        'benjamins': 2,     # 8-9 ans
        'minimes': 3,       # 10-11 ans
        'cadets': 4,        # 12-14 ans
        'juniors': 5,       # 15-17 ans
        'seniors': 6,       # 18-34 ans
        'veterans': 7,      # 35+ ans
        'masters': 8,       # 40+ ans
    }

    # Ordre des genres pour le protocole
    GENDER_ORDER = {
        'female': 1,
        'male': 2,
        'mixed': 3,
    }

    # Mapping des grades avec ordre de priorité (ceintures)
    GRADE_ORDER = {
        # Ceintures débutants
        'blanche': 1,
        'white': 1,
        'jaune': 2,
        'yellow': 2,
        'orange': 3,
        'verte': 4,
        'green': 4,
        'bleue': 5,
        'blue': 5,
        'marron': 6,
        'brown': 6,
        # Ceintures noires
        'noire': 7,
        'black': 7,
        '1er dan': 8,
        '1st dan': 8,
        '2e dan': 9,
        '2nd dan': 9,
        '3e dan': 10,
        '3rd dan': 10,
        '4e dan': 11,
        '4th dan': 11,
        '5e dan': 12,
        '5th dan': 12,
    }

    @staticmethod
    def detect_age_group(category):
        """
        Détecte le groupe d'âge d'une catégorie basé sur min_age/max_age ou le nom.

        Args:
            category: CompetitionCategory instance

        Returns:
            str: nom du groupe d'âge détecté
        """
        # Essayer de détecter par l'âge
        if category.min_age is not None:
            if category.min_age <= 7:
                return 'poussins'
            elif category.min_age <= 9:
                return 'benjamins'
            elif category.min_age <= 11:
                return 'minimes'
            elif category.min_age <= 14:
                return 'cadets'
            elif category.min_age <= 17:
                return 'juniors'
            elif category.min_age <= 34:
                return 'seniors'
            elif category.min_age <= 40:
                return 'veterans'
            else:
                return 'masters'

        # Essayer de détecter par le nom
        name_lower = category.name.lower()
        for group in PodiumOrderService.AGE_GROUP_ORDER.keys():
            if group in name_lower:
                return group

        # Défaut: seniors
        return 'seniors'

    @staticmethod
    def detect_grade_level(category):
        """
        Détecte le niveau de grade d'une catégorie.

        Args:
            category: CompetitionCategory instance

        Returns:
            int: niveau de priorité du grade (1 = débutant)
        """
        # Vérifier min_grade
        if category.min_grade:
            grade_lower = category.min_grade.lower()
            for grade_name, order in PodiumOrderService.GRADE_ORDER.items():
                if grade_name in grade_lower:
                    return order

        # Vérifier le nom de la catégorie
        name_lower = category.name.lower()
        for grade_name, order in PodiumOrderService.GRADE_ORDER.items():
            if grade_name in name_lower:
                return order

        # Défaut: niveau intermédiaire
        return 5

    @staticmethod
    def detect_weight_order(category):
        """
        Détecte l'ordre de poids d'une catégorie.

        Args:
            category: CompetitionCategory instance

        Returns:
            float: poids pour le tri (légers en premier)
        """
        if category.min_weight is not None:
            return float(category.min_weight)

        if category.max_weight is not None:
            return float(category.max_weight)

        # Essayer de détecter par le nom (ex: "-60kg", "60-70kg")
        import re
        name = category.name
        weight_match = re.search(r'(\d+)\s*kg', name, re.IGNORECASE)
        if weight_match:
            return float(weight_match.group(1))

        # Défaut: poids moyen
        return 75.0

    @classmethod
    def get_category_sort_key(cls, category):
        """
        Génère une clé de tri pour une catégorie.

        Args:
            category: CompetitionCategory instance

        Returns:
            tuple: (age_order, grade_order, weight_order, gender_order)
        """
        age_group = cls.detect_age_group(category)
        age_order = cls.AGE_GROUP_ORDER.get(age_group, 6)

        grade_order = cls.detect_grade_level(category)
        weight_order = cls.detect_weight_order(category)
        gender_order = cls.GENDER_ORDER.get(category.gender, 3)

        return (age_order, grade_order, weight_order, gender_order)

    @classmethod
    def order_categories(cls, categories):
        """
        Ordonne une liste de catégories selon l'ordre protocolaire.

        Args:
            categories: QuerySet ou liste de CompetitionCategory

        Returns:
            list: catégories ordonnées
        """
        # Convertir en liste si nécessaire
        if hasattr(categories, 'all'):
            categories = list(categories.all())
        else:
            categories = list(categories)

        # Trier avec la clé de tri
        return sorted(categories, key=cls.get_category_sort_key)

    @classmethod
    def order_categories_for_competition(cls, competition):
        """
        Récupère et ordonne toutes les catégories d'une compétition.

        Args:
            competition: Competition instance

        Returns:
            list: catégories ordonnées avec métadonnées
        """
        categories = CompetitionCategory.objects.filter(
            competition=competition,
            is_completed=True  # Seulement les catégories terminées
        ).select_related('competition', 'competition_type')

        ordered = cls.order_categories(categories)

        # Ajouter des métadonnées pour l'affichage
        result = []
        for idx, cat in enumerate(ordered):
            result.append({
                'index': idx,
                'category': cat,
                'age_group': cls.detect_age_group(cat),
                'grade_level': cls.detect_grade_level(cat),
                'weight_order': cls.detect_weight_order(cat),
                'gender': cat.gender,
                'is_first': idx == 0,
                'is_last': idx == len(ordered) - 1,
            })

        return result

    @classmethod
    def get_all_categories_for_podium(cls, competition, include_pending=False):
        """
        Récupère toutes les catégories pour la cérémonie podium.

        Args:
            competition: Competition instance
            include_pending: inclure les catégories non terminées

        Returns:
            list: catégories ordonnées avec leurs résultats
        """
        filters = {'competition': competition}
        if not include_pending:
            filters['is_completed'] = True

        categories = CompetitionCategory.objects.filter(
            **filters
        ).select_related('competition', 'competition_type')

        ordered = cls.order_categories(categories)

        result = []
        for idx, cat in enumerate(ordered):
            cat_data = {
                'index': idx,
                'category': cat,
                'age_group': cls.detect_age_group(cat),
                'age_group_display': cls._get_age_group_display(cls.detect_age_group(cat)),
                'grade_level': cls.detect_grade_level(cat),
                'weight_order': cls.detect_weight_order(cat),
                'gender': cat.gender,
                'gender_display': cls._get_gender_display(cat.gender),
                'is_first': idx == 0,
                'is_last': idx == len(ordered) - 1,
                'total_count': len(ordered),
            }
            result.append(cat_data)

        return result

    @staticmethod
    def _get_age_group_display(age_group):
        """Retourne le nom d'affichage d'un groupe d'âge."""
        displays = {
            'poussins': _('Poussins'),
            'benjamins': _('Benjamins'),
            'minimes': _('Minimes'),
            'cadets': _('Cadets'),
            'juniors': _('Juniors'),
            'seniors': _('Seniors'),
            'veterans': _('Vétérans'),
            'masters': _('Masters'),
        }
        return displays.get(age_group, age_group.capitalize())

    @staticmethod
    def _get_gender_display(gender):
        """Retourne le nom d'affichage du genre."""
        displays = {
            'female': _('Féminin'),
            'male': _('Masculin'),
            'mixed': _('Mixte'),
        }
        return displays.get(gender, gender.capitalize())

    @classmethod
    def get_categories_grouped_by_age(cls, competition):
        """
        Groupe les catégories par groupe d'âge pour affichage en sections.

        Args:
            competition: Competition instance

        Returns:
            dict: {age_group: [categories]}
        """
        all_categories = cls.get_all_categories_for_podium(competition, include_pending=True)

        grouped = {}
        for cat_data in all_categories:
            age_group = cat_data['age_group']
            if age_group not in grouped:
                grouped[age_group] = {
                    'name': age_group,
                    'display': cat_data['age_group_display'],
                    'categories': []
                }
            grouped[age_group]['categories'].append(cat_data)

        # Trier les groupes selon l'ordre
        sorted_groups = sorted(
            grouped.values(),
            key=lambda g: cls.AGE_GROUP_ORDER.get(g['name'], 99)
        )

        return sorted_groups
