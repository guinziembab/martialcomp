"""
Service d'eligibilite de grade pour les pratiquants.
Prompt 5 - Calcule l'eligibilite au passage de grade suivant.

Ce service fournit:
- Calcul de l'eligibilite basee sur temps, age, et exigences
- Cache Redis avec TTL de 24h
- Verification en masse pour plusieurs pratiquants
- Invalidation du cache lors des changements de grade
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
import logging
import json

from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, gettext
from django.db.models import Q
from django.urls import reverse

logger = logging.getLogger(__name__)

# Cache configuration
ELIGIBILITY_CACHE_PREFIX = 'grade_eligibility_'
ELIGIBILITY_CACHE_TTL = 86400  # 24 hours


@dataclass
class RequirementStatus:
    """Status d'une exigence de grade."""
    requirement_id: int
    name: str
    description: str
    is_mandatory: bool
    is_met: bool
    current_value: Optional[str] = None
    required_value: Optional[str] = None
    blocking_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour serialisation."""
        return asdict(self)


@dataclass
class EligibilityResult:
    """Resultat du calcul d'eligibilite."""
    practitioner_id: int
    discipline_id: int
    is_eligible: bool
    eligibility_date: Optional[date]
    days_remaining: int
    progress_percentage: float  # 0-100
    blocking_reasons: List[str] = field(default_factory=list)
    requirements_status: List[RequirementStatus] = field(default_factory=list)
    current_grade: Optional[Dict[str, Any]] = None
    next_grade: Optional[Dict[str, Any]] = None
    available_exams: List[Dict[str, Any]] = field(default_factory=list)
    status: str = 'in_progress'  # 'in_progress', 'eligible', 'blocked', 'no_next_grade'

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour serialisation/cache."""
        result = asdict(self)
        # Convertir la date en string ISO
        if result['eligibility_date']:
            result['eligibility_date'] = result['eligibility_date'].isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EligibilityResult':
        """Reconstruit depuis un dictionnaire (pour le cache)."""
        # Convertir la date ISO en objet date
        if data.get('eligibility_date'):
            data['eligibility_date'] = date.fromisoformat(data['eligibility_date'])

        # Reconstruire les RequirementStatus
        if data.get('requirements_status'):
            data['requirements_status'] = [
                RequirementStatus(**req) if isinstance(req, dict) else req
                for req in data['requirements_status']
            ]

        return cls(**data)


class GradeEligibilityService:
    """
    Service pour calculer l'eligibilite au passage de grade.

    Usage:
        result = GradeEligibilityService.check_eligibility(practitioner)
        if result.is_eligible:
            # Afficher bouton inscription examen
        else:
            # Afficher progression et jours restants
    """

    @classmethod
    def check_eligibility(cls, practitioner, discipline=None) -> EligibilityResult:
        """
        Verifie l'eligibilite d'un pratiquant pour le grade suivant.

        Args:
            practitioner: Instance de Practitioner
            discipline: Instance de Discipline (optionnel, utilise primary_discipline si non fourni)

        Returns:
            EligibilityResult avec tous les details
        """
        from apps.grades.models import Grade, PractitionerGrade, GradeRequirement, GradeExam

        # Determiner la discipline
        if discipline is None:
            discipline = practitioner.primary_discipline

        # Si toujours pas de discipline, essayer via les relations ManyToMany ou PractitionerDiscipline
        if discipline is None:
            # Essayer via disciplines ManyToMany
            if hasattr(practitioner, 'disciplines') and practitioner.disciplines.exists():
                discipline = practitioner.disciplines.first()

        if discipline is None:
            # Essayer via PractitionerDiscipline
            try:
                from apps.grades.models import PractitionerDiscipline
                practitioner_discipline = PractitionerDiscipline.objects.filter(
                    practitioner=practitioner
                ).select_related('discipline').first()
                if practitioner_discipline:
                    discipline = practitioner_discipline.discipline
            except Exception:
                pass

        if discipline is None:
            # Pas de discipline, retourner resultat vide
            return EligibilityResult(
                practitioner_id=practitioner.id,
                discipline_id=0,
                is_eligible=False,
                eligibility_date=None,
                days_remaining=0,
                progress_percentage=0,
                status='no_next_grade',
                blocking_reasons=[gettext("Aucune discipline assignee")]
            )

        # Verifier le cache
        cached = cls.get_cached_eligibility(practitioner.id, discipline.id)
        if cached:
            return cached

        # Recuperer le grade actuel
        current_practitioner_grade = PractitionerGrade.objects.filter(
            practitioner=practitioner,
            discipline=discipline,
            is_current=True
        ).select_related('grade').first()

        if not current_practitioner_grade:
            # Pas de grade actuel
            return cls._create_no_grade_result(practitioner, discipline)

        current_grade = current_practitioner_grade.grade
        next_grade = current_grade.next_grade

        if not next_grade:
            # Grade maximum atteint
            result = EligibilityResult(
                practitioner_id=practitioner.id,
                discipline_id=discipline.id,
                is_eligible=False,
                eligibility_date=None,
                days_remaining=0,
                progress_percentage=100,
                status='no_next_grade',
                current_grade=cls._serialize_grade(current_grade),
                next_grade=None
            )
            cls.set_cached_eligibility(result)
            return result

        # Calculer la progression et l'eligibilite
        blocking_reasons = []
        requirements_status = []

        # 1. Verifier le temps dans le grade actuel
        time_progress, time_days_remaining, time_eligibility_date = cls._calculate_time_progress(
            current_practitioner_grade.date_obtained,
            next_grade.min_time_in_previous_grade
        )

        if time_days_remaining > 0:
            blocking_reasons.append(
                gettext("Temps minimum dans le grade actuel: %(days)d jours restants") % {'days': time_days_remaining}
            )

        # 2. Verifier l'age minimum
        age_met, age_reason = cls._check_age_requirement(practitioner, next_grade)
        if not age_met and age_reason:
            blocking_reasons.append(age_reason)

        # 3. Verifier les exigences specifiques du grade
        grade_requirements = cls._check_grade_requirements(practitioner, next_grade)
        requirements_status.extend(grade_requirements)

        # Ajouter les raisons de blocage des exigences obligatoires non remplies
        for req in grade_requirements:
            if req.is_mandatory and not req.is_met and req.blocking_reason:
                blocking_reasons.append(req.blocking_reason)

        # 4. Recuperer les examens disponibles
        available_exams = cls._get_available_exams(practitioner, next_grade, discipline)

        # Determiner le statut final
        is_eligible = len(blocking_reasons) == 0 and time_progress >= 100

        if is_eligible:
            status = 'eligible'
        elif blocking_reasons:
            status = 'blocked'
        else:
            status = 'in_progress'

        # Creer le resultat
        result = EligibilityResult(
            practitioner_id=practitioner.id,
            discipline_id=discipline.id,
            is_eligible=is_eligible,
            eligibility_date=time_eligibility_date if time_progress >= 100 else None,
            days_remaining=time_days_remaining,
            progress_percentage=min(time_progress, 100),
            blocking_reasons=blocking_reasons,
            requirements_status=requirements_status,
            current_grade=cls._serialize_grade(current_grade),
            next_grade=cls._serialize_grade(next_grade),
            available_exams=available_exams,
            status=status
        )

        # Mettre en cache
        cls.set_cached_eligibility(result)

        return result

    @classmethod
    def _create_no_grade_result(cls, practitioner, discipline) -> EligibilityResult:
        """Cree un resultat pour un pratiquant sans grade."""
        from apps.grades.models import Grade

        # Chercher le premier grade de la discipline
        first_grade = Grade.objects.filter(
            discipline=discipline,
            is_active=True
        ).order_by('level').first()

        return EligibilityResult(
            practitioner_id=practitioner.id,
            discipline_id=discipline.id,
            is_eligible=True if first_grade else False,
            eligibility_date=timezone.now().date(),
            days_remaining=0,
            progress_percentage=0,
            status='eligible' if first_grade else 'no_next_grade',
            current_grade=None,
            next_grade=cls._serialize_grade(first_grade) if first_grade else None,
            blocking_reasons=[] if first_grade else [gettext("Aucun grade disponible pour cette discipline")]
        )

    @classmethod
    def _calculate_time_progress(cls, grade_date: date, min_time_months: int) -> tuple:
        """
        Calcule la progression temporelle vers l'eligibilite.

        Args:
            grade_date: Date d'obtention du grade actuel
            min_time_months: Temps minimum requis en mois

        Returns:
            tuple (progress_percentage, days_remaining, eligibility_date)
        """
        if min_time_months <= 0:
            return (100.0, 0, grade_date)

        today = timezone.now().date()
        days_since_grade = (today - grade_date).days
        required_days = min_time_months * 30  # Approximation

        if days_since_grade >= required_days:
            eligibility_date = grade_date + timedelta(days=required_days)
            return (100.0, 0, eligibility_date)
        else:
            progress = (days_since_grade / required_days) * 100
            days_remaining = required_days - days_since_grade
            eligibility_date = today + timedelta(days=days_remaining)
            return (round(progress, 1), days_remaining, eligibility_date)

    @classmethod
    def _check_age_requirement(cls, practitioner, next_grade) -> tuple:
        """
        Verifie l'exigence d'age minimum.

        Returns:
            tuple (is_met: bool, reason: str or None)
        """
        if next_grade.min_age <= 0:
            return (True, None)

        practitioner_age = practitioner.age

        if practitioner_age >= next_grade.min_age:
            return (True, None)
        else:
            years_to_wait = next_grade.min_age - practitioner_age
            reason = gettext("Age minimum requis: %(min_age)d ans (actuellement %(current_age)d ans)") % {
                'min_age': next_grade.min_age,
                'current_age': practitioner_age
            }
            return (False, reason)

    @classmethod
    def _check_grade_requirements(cls, practitioner, next_grade) -> List[RequirementStatus]:
        """
        Verifie toutes les exigences specifiques du grade.

        Returns:
            Liste de RequirementStatus
        """
        from apps.grades.models import GradeRequirement

        requirements = GradeRequirement.objects.filter(
            grade=next_grade
        ).order_by('order')

        statuses = []

        for req in requirements:
            # Verifier l'exigence d'age specifique
            if req.min_age > 0:
                is_met = practitioner.age >= req.min_age
                status = RequirementStatus(
                    requirement_id=req.id,
                    name=req.name,
                    description=req.description,
                    is_mandatory=req.is_mandatory,
                    is_met=is_met,
                    current_value=str(practitioner.age),
                    required_value=str(req.min_age),
                    blocking_reason=None if is_met else gettext("Age minimum: %(age)d ans") % {'age': req.min_age}
                )
                statuses.append(status)

            # Verifier les points requis (si applicable)
            elif req.required_points > 0:
                # TODO: Implementer le systeme de points si necessaire
                status = RequirementStatus(
                    requirement_id=req.id,
                    name=req.name,
                    description=req.description,
                    is_mandatory=req.is_mandatory,
                    is_met=False,  # A implementer
                    current_value="0",
                    required_value=str(req.required_points),
                    blocking_reason=gettext("Points requis: %(points)d") % {'points': req.required_points}
                )
                statuses.append(status)

            # Exigence textuelle generique
            else:
                # Par defaut, on considere que l'exigence n'est pas automatiquement verifiable
                status = RequirementStatus(
                    requirement_id=req.id,
                    name=req.name,
                    description=req.description,
                    is_mandatory=req.is_mandatory,
                    is_met=True,  # Non verifiable automatiquement, on assume OK
                    current_value=None,
                    required_value=None,
                    blocking_reason=None
                )
                statuses.append(status)

        return statuses

    @classmethod
    def _get_available_exams(cls, practitioner, next_grade, discipline) -> List[Dict[str, Any]]:
        """
        Recupere les examens disponibles pour le grade cible.

        Returns:
            Liste de dictionnaires avec les infos des examens
        """
        from apps.grades.models import GradeExam, GradeExamRegistration

        today = timezone.now().date()

        # Trouver les examens a venir pour ce grade
        exams = GradeExam.objects.filter(
            available_grades=next_grade,
            discipline=discipline,
            status='scheduled',
            date__gte=today
        ).order_by('date')[:3]  # Limiter aux 3 prochains

        # Verifier les inscriptions existantes
        existing_registrations = GradeExamRegistration.objects.filter(
            practitioner=practitioner,
            exam__in=exams
        ).values_list('exam_id', flat=True)

        exam_list = []
        for exam in exams:
            is_registered = exam.id in existing_registrations
            registration_open = exam.is_registration_open

            exam_dict = {
                'id': exam.id,
                'title': exam.title,
                'date': exam.date.isoformat(),
                'date_display': exam.date.strftime('%d/%m/%Y'),
                'location': exam.location,
                'registration_deadline': exam.registration_deadline.isoformat(),
                'registration_deadline_display': exam.registration_deadline.strftime('%d/%m/%Y'),
                'fee': float(exam.fee) if exam.fee else 0,
                'registration_open': registration_open and not is_registered,
                'is_registered': is_registered,
                'spots_remaining': exam.max_participants - exam.count_registered(),
            }

            # Ajouter l'URL d'inscription si disponible
            try:
                exam_dict['registration_url'] = reverse('grades:exam_register', kwargs={'exam_id': exam.id})
            except Exception:
                exam_dict['registration_url'] = '#'

            exam_list.append(exam_dict)

        return exam_list

    @classmethod
    def _serialize_grade(cls, grade) -> Optional[Dict[str, Any]]:
        """Serialise un grade pour le resultat."""
        if not grade:
            return None

        return {
            'id': grade.id,
            'name': grade.name,
            'level': grade.level,
            'color': grade.color,
            'color_code': grade.color_code or grade.get_display_color(),
            'is_dan_grade': grade.is_dan_grade,
            'image_url': grade.image_url,
            'initials': grade.initials,
            'min_age': grade.min_age,
            'min_time_in_previous_grade': grade.min_time_in_previous_grade,
        }

    # ===== GESTION DU CACHE =====

    @classmethod
    def _get_cache_key(cls, practitioner_id: int, discipline_id: int) -> str:
        """Genere la cle de cache."""
        return f"{ELIGIBILITY_CACHE_PREFIX}{practitioner_id}_{discipline_id}"

    @classmethod
    def get_cached_eligibility(cls, practitioner_id: int, discipline_id: int) -> Optional[EligibilityResult]:
        """Recupere l'eligibilite depuis le cache Redis."""
        try:
            cache_key = cls._get_cache_key(practitioner_id, discipline_id)
            cached_data = cache.get(cache_key)

            if cached_data:
                return EligibilityResult.from_dict(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Erreur lecture cache eligibilite: {e}")
            return None

    @classmethod
    def set_cached_eligibility(cls, result: EligibilityResult) -> None:
        """Stocke l'eligibilite dans le cache Redis."""
        try:
            cache_key = cls._get_cache_key(result.practitioner_id, result.discipline_id)
            cache.set(cache_key, result.to_dict(), ELIGIBILITY_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Erreur ecriture cache eligibilite: {e}")

    @classmethod
    def invalidate_cache(cls, practitioner_id: int, discipline_id: int = None) -> None:
        """
        Invalide le cache d'eligibilite pour un pratiquant.

        Args:
            practitioner_id: ID du pratiquant
            discipline_id: ID de la discipline (optionnel, invalide toutes les disciplines si None)
        """
        try:
            if discipline_id:
                cache_key = cls._get_cache_key(practitioner_id, discipline_id)
                cache.delete(cache_key)
                logger.debug(f"Cache eligibilite invalide: {cache_key}")
            else:
                # Invalider toutes les disciplines pour ce pratiquant
                # Note: Redis pattern delete n'est pas supporte par le backend Django par defaut
                # On pourrait utiliser redis-py directement si necessaire
                pattern = f"{ELIGIBILITY_CACHE_PREFIX}{practitioner_id}_*"
                logger.debug(f"Tentative d'invalidation pattern: {pattern}")

                # Solution alternative: invalider les disciplines connues du pratiquant
                from apps.competitions.models import Practitioner
                try:
                    practitioner = Practitioner.objects.get(id=practitioner_id)
                    disciplines = practitioner.disciplines.all()
                    for discipline in disciplines:
                        cache_key = cls._get_cache_key(practitioner_id, discipline.id)
                        cache.delete(cache_key)

                    # Aussi invalider la discipline principale
                    if practitioner.primary_discipline:
                        cache_key = cls._get_cache_key(practitioner_id, practitioner.primary_discipline.id)
                        cache.delete(cache_key)
                except Practitioner.DoesNotExist:
                    pass

        except Exception as e:
            logger.error(f"Erreur invalidation cache eligibilite: {e}")

    # ===== VERIFICATION EN MASSE =====

    @classmethod
    def bulk_check_eligibility(cls, practitioners, discipline=None) -> List[EligibilityResult]:
        """
        Verifie l'eligibilite pour plusieurs pratiquants.

        Args:
            practitioners: QuerySet ou liste de Practitioner
            discipline: Instance de Discipline (optionnel)

        Returns:
            Liste de EligibilityResult
        """
        results = []

        for practitioner in practitioners:
            try:
                result = cls.check_eligibility(practitioner, discipline)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur check eligibilite pour practitioner {practitioner.id}: {e}")
                # Ajouter un resultat d'erreur
                results.append(EligibilityResult(
                    practitioner_id=practitioner.id,
                    discipline_id=discipline.id if discipline else 0,
                    is_eligible=False,
                    eligibility_date=None,
                    days_remaining=0,
                    progress_percentage=0,
                    status='blocked',
                    blocking_reasons=[gettext("Erreur lors du calcul d'eligibilite")]
                ))

        return results

    # ===== METHODES UTILITAIRES =====

    @classmethod
    def get_practitioners_eligible_for_grade(cls, grade, discipline=None) -> List[int]:
        """
        Trouve tous les pratiquants eligibles pour un grade donne.
        Utile pour les notifications.

        Returns:
            Liste des IDs de pratiquants eligibles
        """
        from apps.grades.models import PractitionerGrade

        # Trouver le grade precedent
        previous_grade = grade.previous_grade
        if not previous_grade:
            return []

        # Trouver les pratiquants avec ce grade
        practitioner_grades = PractitionerGrade.objects.filter(
            grade=previous_grade,
            is_current=True
        ).select_related('practitioner')

        if discipline:
            practitioner_grades = practitioner_grades.filter(discipline=discipline)

        eligible_ids = []
        for pg in practitioner_grades:
            try:
                result = cls.check_eligibility(pg.practitioner, pg.discipline)
                if result.is_eligible:
                    eligible_ids.append(pg.practitioner.id)
            except Exception as e:
                logger.error(f"Erreur verification eligibilite: {e}")

        return eligible_ids
