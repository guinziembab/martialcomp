from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

# PHASE 1 SECURITY: Import helpers de filtrage par discipline
from apps.competitions.utils.permission_helpers import (
    get_user_disciplines,
    filter_queryset_by_user_disciplines
)

logger = logging.getLogger('discipline_isolation')


def _get_practitioner_discipline_ids(user):
    """
    Get discipline IDs accessible to a user, with fallback to practitioner's disciplines.
    This avoids the issue where get_user_disciplines() returns empty for regular practitioners
    who don't own/manage an organization.
    """
    from apps.competitions.models import Discipline

    if user.is_superuser:
        return None  # None means "all disciplines"

    # Try standard helper first
    accessible = get_user_disciplines(user)
    if accessible.exists():
        return set(accessible.values_list('id', flat=True))

    # Fallback: get disciplines from practitioner profile
    discipline_ids = set()
    try:
        from apps.competitions.models import Practitioner, PractitionerDiscipline
        practitioners = Practitioner.objects.filter(user=user)
        for p in practitioners:
            # From PractitionerDiscipline table
            discipline_ids.update(
                PractitionerDiscipline.objects.filter(
                    practitioner=p
                ).values_list('discipline_id', flat=True)
            )
            # From M2M disciplines field
            if hasattr(p, 'disciplines'):
                discipline_ids.update(p.disciplines.values_list('id', flat=True))
            # From primary_discipline
            if hasattr(p, 'primary_discipline_id') and p.primary_discipline_id:
                discipline_ids.add(p.primary_discipline_id)
            # From organization disciplines
            if not discipline_ids and p.organization and hasattr(p.organization, 'disciplines'):
                discipline_ids.update(
                    p.organization.disciplines.values_list('id', flat=True)
                )
    except Exception as e:
        logger.error(f"_get_practitioner_discipline_ids error: {e}")

    # Last fallback: get disciplines from PractitionerGrade
    if not discipline_ids:
        try:
            from apps.grades.models import PractitionerGrade
            from apps.competitions.models import Practitioner
            practitioners = Practitioner.objects.filter(user=user)
            grade_disc_ids = PractitionerGrade.objects.filter(
                practitioner__in=practitioners
            ).values_list('grade__discipline_id', flat=True).distinct()
            discipline_ids.update(d for d in grade_disc_ids if d)
        except Exception:
            pass

    return discipline_ids if discipline_ids else set()


class GradesListView(APIView):
    """
    Grades API for mobile.
    Returns grades filtered by the user's accessible disciplines.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        grades = []
        current_grade = None

        try:
            from apps.grades.models import Grade, PractitionerGrade
            from apps.competitions.models import Practitioner

            user = request.user
            discipline_ids = _get_practitioner_discipline_ids(user)

            if discipline_ids is None:
                # Superuser - all grades
                qs = Grade.objects.filter(is_active=True)
            elif discipline_ids:
                qs = Grade.objects.filter(discipline_id__in=discipline_ids, is_active=True)
            else:
                qs = Grade.objects.none()

            for g in qs.select_related('discipline').order_by('discipline__name', 'level')[:100]:
                grades.append({
                    'id': g.id,
                    'name': g.name,
                    'level': g.level,
                    'color': getattr(g, 'color', None),
                    'discipline': g.discipline.name if g.discipline else None,
                    'discipline_id': g.discipline_id,
                })

            # Get current grade for authenticated user
            practitioner = Practitioner.objects.filter(user=user).first()
            if practitioner:
                pg = (
                    PractitionerGrade.objects
                    .filter(practitioner=practitioner)
                    .select_related('grade')
                    .order_by('-date_obtained')
                    .first()
                )
                if pg and pg.grade:
                    current_grade = {
                        'id': pg.grade.id,
                        'name': pg.grade.name,
                        'level': pg.grade.level,
                        'color': getattr(pg.grade, 'color', None),
                    }
        except Exception as e:
            logger.error(f"GradesListView error: {e}")
            grades = []

        return Response({
            'grades': grades,
            'current_grade': current_grade,
        })


class GradeCategoriesView(APIView):
    """
    API endpoint for grade categories.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        categories = []
        discipline_id = request.GET.get('discipline')

        try:
            from apps.grades.models import GradeCategory

            user = request.user
            disc_ids = _get_practitioner_discipline_ids(user)

            if disc_ids is None:
                qs = GradeCategory.objects.filter(is_active=True)
            elif disc_ids:
                qs = GradeCategory.objects.filter(discipline_id__in=disc_ids, is_active=True)
            else:
                qs = GradeCategory.objects.none()

            if discipline_id:
                qs = qs.filter(discipline_id=discipline_id)

            for cat in qs.select_related('discipline').order_by('order', 'name')[:50]:
                categories.append({
                    'id': cat.id,
                    'name': cat.name,
                    'description': getattr(cat, 'description', ''),
                    'order': getattr(cat, 'order', 0),
                    'discipline_id': cat.discipline_id,
                    'discipline_name': cat.discipline.name if cat.discipline else '',
                })
        except Exception as e:
            logger.error(f"GradeCategoriesView error: {e}")

        return Response({
            'categories': categories,
            'count': len(categories),
        })


class GradeExamsView(APIView):
    """
    API endpoint for grade exams.
    Returns upcoming grade exams filtered by user's disciplines.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        exams = []
        discipline_id = request.GET.get('discipline')
        status = request.GET.get('status')

        try:
            from apps.grades.models import GradeExam
            from django.utils import timezone

            user = request.user
            now = timezone.now()
            disc_ids = _get_practitioner_discipline_ids(user)

            if disc_ids is None:
                qs = GradeExam.objects.all()
            elif disc_ids:
                qs = GradeExam.objects.filter(discipline_id__in=disc_ids)
            else:
                qs = GradeExam.objects.none()

            if discipline_id:
                qs = qs.filter(discipline_id=discipline_id)

            # GradeExam model uses 'date' field (not 'exam_date')
            if status == 'upcoming':
                qs = qs.filter(date__gte=now.date())
            elif status == 'past':
                qs = qs.filter(date__lt=now.date())

            for exam in qs.select_related('discipline').order_by('date')[:50]:
                # Check if current user is registered
                is_registered = False
                try:
                    from apps.competitions.models import Practitioner
                    practitioner = Practitioner.objects.filter(user=user).first()
                    if practitioner:
                        is_registered = exam.registrations.filter(
                            practitioner=practitioner
                        ).exists()
                except Exception:
                    pass

                exams.append({
                    'id': exam.id,
                    # GradeExam uses 'title' (not 'name')
                    'name': exam.title or f'Examen #{exam.id}',
                    'title': exam.title or f'Examen #{exam.id}',
                    # GradeExam uses 'date' (not 'exam_date')
                    'exam_date': exam.date.isoformat() if exam.date else None,
                    'date': exam.date.isoformat() if exam.date else None,
                    'location': getattr(exam, 'location', '') or '',
                    'discipline_id': exam.discipline_id,
                    'discipline_name': exam.discipline.name if exam.discipline else '',
                    'status': getattr(exam, 'status', 'scheduled'),
                    'max_participants': getattr(exam, 'max_participants', None),
                    'registration_deadline': exam.registration_deadline.isoformat() if getattr(exam, 'registration_deadline', None) else None,
                    'fee': str(exam.fee) if getattr(exam, 'fee', None) else None,
                    'is_registered': is_registered,
                })
        except Exception as e:
            logger.error(f"GradeExamsView error: {e}")
            import traceback
            traceback.print_exc()

        return Response({
            'exams': exams,
            'count': len(exams),
        })


class PractitionerGradesView(APIView):
    """
    API endpoint for practitioner's complete grade information.
    Returns current grades, next grades, progression, history and upcoming exams.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from django.utils import timezone

        user = request.user
        current_grades = []
        next_grades = []
        progression = []
        grade_history = []
        upcoming_exams = []

        try:
            from apps.grades.models import Grade, PractitionerGrade, GradeExam
            from apps.competitions.models import Practitioner

            # Get practitioner for current user
            practitioner = Practitioner.objects.filter(user=user).select_related('organization').first()
            if not practitioner:
                return Response({
                    'current_grades': [],
                    'next_grades': [],
                    'progression': [],
                    'grade_history': [],
                    'upcoming_exams': [],
                    'message': 'Aucun profil pratiquant trouvé'
                })

            # Get all practitioner grades
            practitioner_grades = PractitionerGrade.objects.filter(
                practitioner=practitioner
            ).select_related('grade', 'grade__discipline').order_by('-date_obtained')

            # Build current grades list (one per discipline, most recent)
            seen_disciplines = set()
            for pg in practitioner_grades:
                if pg.grade and pg.grade.discipline_id not in seen_disciplines:
                    seen_disciplines.add(pg.grade.discipline_id)
                    grade = pg.grade

                    # Calculate progression to next grade
                    next_grade = None
                    progress_percent = 0
                    is_eligible = False

                    try:
                        next_grade_obj = Grade.objects.filter(
                            discipline=grade.discipline,
                            level__gt=grade.level,
                            is_active=True
                        ).order_by('level').first()

                        if next_grade_obj:
                            next_grade = {
                                'id': next_grade_obj.id,
                                'name': next_grade_obj.name,
                                'level': next_grade_obj.level,
                                'color': getattr(next_grade_obj, 'color', '#CCCCCC'),
                            }

                            min_months = getattr(next_grade_obj, 'minimum_months_at_grade', 0) or 0
                            if min_months > 0 and pg.date_obtained:
                                from datetime import date
                                months_at_grade = (date.today() - pg.date_obtained).days / 30.0
                                progress_percent = min(100, int((months_at_grade / min_months) * 100))
                                is_eligible = months_at_grade >= min_months
                            else:
                                progress_percent = 100
                                is_eligible = True
                        else:
                            # Max grade reached
                            progress_percent = 100
                            is_eligible = True
                    except Exception as e:
                        logger.error(f"Error calculating next grade: {e}")

                    current_grade_data = {
                        'id': grade.id,
                        'name': grade.name,
                        'level': grade.level,
                        'color': getattr(grade, 'color', '#FFFFFF'),
                        'discipline_id': grade.discipline_id,
                        'discipline_name': grade.discipline.name if grade.discipline else '',
                        'date_obtained': pg.date_obtained.isoformat() if pg.date_obtained else None,
                        'certificate_number': getattr(pg, 'certificate_number', ''),
                    }
                    current_grades.append(current_grade_data)

                    if next_grade:
                        next_grades.append(next_grade)

                    progression.append({
                        'discipline_id': grade.discipline_id,
                        'discipline_name': grade.discipline.name if grade.discipline else '',
                        'current_grade': current_grade_data,
                        'next_grade': next_grade,
                        'progress_percent': progress_percent,
                        'is_eligible': is_eligible,
                        'status': 'ELIGIBLE' if is_eligible else 'EN PROGRESSION',
                    })

            # Build grade history
            for pg in practitioner_grades:
                if pg.grade:
                    grade_history.append({
                        'id': pg.id,
                        'grade_id': pg.grade.id,
                        'grade_name': pg.grade.name,
                        'grade_level': pg.grade.level,
                        'grade_color': getattr(pg.grade, 'color', '#FFFFFF'),
                        'discipline_name': pg.grade.discipline.name if pg.grade.discipline else '',
                        'date_obtained': pg.date_obtained.isoformat() if pg.date_obtained else None,
                        'certificate_number': getattr(pg, 'certificate_number', ''),
                        'examiner_name': getattr(pg, 'examiner_name', ''),
                        'notes': getattr(pg, 'notes', ''),
                    })

            # Get upcoming exams for practitioner's disciplines
            # GradeExam uses 'date' field (not 'exam_date') and 'title' (not 'name')
            try:
                now = timezone.now()
                disciplines_ids = list(seen_disciplines)

                if disciplines_ids:
                    exam_qs = GradeExam.objects.filter(
                        discipline_id__in=disciplines_ids,
                        date__gte=now.date()
                    ).select_related('discipline').order_by('date')[:10]

                    for exam in exam_qs:
                        # Check if registered
                        is_registered = exam.registrations.filter(
                            practitioner=practitioner
                        ).exists()

                        upcoming_exams.append({
                            'id': exam.id,
                            'name': exam.title or f'Examen de grade',
                            'title': exam.title or f'Examen de grade',
                            'exam_date': exam.date.isoformat() if exam.date else None,
                            'date': exam.date.isoformat() if exam.date else None,
                            'location': getattr(exam, 'location', '') or '',
                            'discipline_id': exam.discipline_id,
                            'discipline_name': exam.discipline.name if exam.discipline else '',
                            'status': getattr(exam, 'status', 'scheduled'),
                            'registration_open': getattr(exam, 'registration_open', True),
                            'is_registered': is_registered,
                        })
            except Exception as e:
                logger.error(f"Error loading upcoming exams: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            logger.error(f"PractitionerGradesView error: {e}")
            return Response({
                'current_grades': [],
                'next_grades': [],
                'progression': [],
                'grade_history': [],
                'upcoming_exams': [],
                'error': str(e)
            })

        return Response({
            'current_grades': current_grades,
            'next_grades': next_grades,
            'progression': progression,
            'grade_history': grade_history,
            'upcoming_exams': upcoming_exams,
            'count': {
                'current': len(current_grades),
                'history': len(grade_history),
                'exams': len(upcoming_exams),
            }
        })


# ============================================================
# CLUB MANAGEMENT API ENDPOINTS
# ============================================================

def _get_user_organization(user):
    """Get the organization for a club manager user."""
    from apps.competitions.utils.permission_helpers import get_user_organization
    org = get_user_organization(user)
    if org:
        return org
    # Fallback: try via Club model
    try:
        from apps.competitions.models import Club
        club = Club.objects.filter(
            models.Q(owner=user) | models.Q(managers=user)
        ).first()
        if club:
            return getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    except Exception:
        pass
    return None


def _is_club_manager(user):
    """Check if the user is a club manager or admin."""
    if user.is_superuser or user.is_staff:
        return True
    try:
        from apps.competitions.models import Club
        from django.db import models as dm
        return Club.objects.filter(
            dm.Q(owner=user) | dm.Q(managers=user)
        ).exists()
    except Exception:
        return False


class ExamManagementView(APIView):
    """
    API endpoint for exam management (CRUD) for club managers.
    GET: List exams with stats and registrations count
    POST: Create a new exam
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from apps.grades.models import GradeExam
        from django.utils import timezone

        user = request.user
        now = timezone.now()
        disc_ids = _get_practitioner_discipline_ids(user)

        if disc_ids is None:
            qs = GradeExam.objects.all()
        elif disc_ids:
            qs = GradeExam.objects.filter(discipline_id__in=disc_ids)
        else:
            qs = GradeExam.objects.none()

        # Filters
        discipline_id = request.GET.get('discipline')
        status_filter = request.GET.get('status')
        search = request.GET.get('search', '').strip()

        if discipline_id:
            qs = qs.filter(discipline_id=discipline_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search) |
                Q(discipline__name__icontains=search)
            )

        # Stats
        all_exams = GradeExam.objects.filter(discipline_id__in=disc_ids) if disc_ids else GradeExam.objects.all() if disc_ids is None else GradeExam.objects.none()
        stats = {
            'total': all_exams.count(),
            'upcoming': all_exams.filter(date__gte=now.date(), status__in=['scheduled', 'in_progress']).count(),
            'past': all_exams.filter(status='completed').count(),
            'cancelled': all_exams.filter(status='cancelled').count(),
        }

        # Build exam list
        exams = []
        for exam in qs.select_related('discipline').order_by('-date')[:50]:
            reg_count = exam.registrations.count()
            exams.append({
                'id': exam.id,
                'title': exam.title or f'Examen #{exam.id}',
                'date': exam.date.isoformat() if exam.date else None,
                'location': exam.location or '',
                'discipline_id': exam.discipline_id,
                'discipline_name': exam.discipline.name if exam.discipline else '',
                'status': exam.status,
                'max_participants': exam.max_participants,
                'registration_count': reg_count,
                'registration_deadline': exam.registration_deadline.isoformat() if exam.registration_deadline else None,
                'examiners': exam.examiners or '',
                'fee': str(exam.fee) if exam.fee else '0',
                'is_registration_open': exam.is_registration_open,
                'description': exam.description or '',
                'notes': exam.notes or '',
            })

        # Get disciplines for filter dropdown
        from apps.competitions.models import Discipline
        if disc_ids is None:
            disciplines = list(Discipline.objects.values('id', 'name').order_by('name'))
        elif disc_ids:
            disciplines = list(Discipline.objects.filter(id__in=disc_ids).values('id', 'name').order_by('name'))
        else:
            disciplines = []

        return Response({
            'exams': exams,
            'stats': stats,
            'disciplines': disciplines,
            'count': len(exams),
        })

    def post(self, request):
        """Create a new exam."""
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExam, Grade
        from apps.competitions.models import Discipline
        import json

        data = request.data
        try:
            discipline = Discipline.objects.get(id=data.get('discipline_id'))
            exam = GradeExam.objects.create(
                title=data.get('title', ''),
                description=data.get('description', ''),
                date=data.get('date'),
                location=data.get('location', ''),
                discipline=discipline,
                max_participants=int(data.get('max_participants', 50)),
                registration_deadline=data.get('registration_deadline'),
                examiners=data.get('examiners', ''),
                fee=data.get('fee', 0),
                status='scheduled',
                notes=data.get('notes', ''),
            )
            # Set available grades if provided
            grade_ids = data.get('available_grade_ids', [])
            if grade_ids:
                grades = Grade.objects.filter(id__in=grade_ids, discipline=discipline)
                exam.available_grades.set(grades)

            return Response({
                'id': exam.id,
                'title': exam.title,
                'message': 'Examen créé avec succès',
            }, status=201)
        except Discipline.DoesNotExist:
            return Response({'error': 'Discipline non trouvée'}, status=400)
        except Exception as e:
            logger.error(f"ExamManagementView POST error: {e}")
            return Response({'error': str(e)}, status=400)


class ExamDetailManagementView(APIView):
    """
    API endpoint for single exam management.
    GET: Exam detail with registrations
    PUT: Update exam
    DELETE: Delete exam
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, exam_id):
        from apps.grades.models import GradeExam

        try:
            exam = GradeExam.objects.select_related('discipline').get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Examen non trouvé'}, status=404)

        # Get registrations
        registrations = []
        for reg in exam.registrations.select_related('practitioner', 'target_grade').order_by('registration_date'):
            photo_url = None
            try:
                if reg.practitioner and reg.practitioner.photo:
                    photo_url = reg.practitioner.photo.url
            except Exception:
                pass
            registrations.append({
                'id': reg.id,
                'practitioner_id': reg.practitioner_id,
                'practitioner_name': reg.practitioner.full_name if reg.practitioner else '',
                'practitioner_photo': photo_url,
                'target_grade_id': reg.target_grade_id,
                'target_grade_name': reg.target_grade.name if reg.target_grade else '',
                'registration_date': reg.registration_date.isoformat() if reg.registration_date else None,
                'status': reg.status,
                'payment_confirmed': reg.payment_confirmed,
                'score': str(reg.score) if reg.score else None,
                'examiner_notes': reg.examiner_notes or '',
                'certificate_issued': reg.certificate_issued,
            })

        # Get available grades
        available_grades = []
        for g in exam.available_grades.all().order_by('level'):
            available_grades.append({
                'id': g.id,
                'name': g.name,
                'level': g.level,
                'color': g.color or '',
            })

        return Response({
            'id': exam.id,
            'title': exam.title or '',
            'description': exam.description or '',
            'date': exam.date.isoformat() if exam.date else None,
            'location': exam.location or '',
            'discipline_id': exam.discipline_id,
            'discipline_name': exam.discipline.name if exam.discipline else '',
            'status': exam.status,
            'max_participants': exam.max_participants,
            'registration_deadline': exam.registration_deadline.isoformat() if exam.registration_deadline else None,
            'examiners': exam.examiners or '',
            'fee': str(exam.fee) if exam.fee else '0',
            'notes': exam.notes or '',
            'is_registration_open': exam.is_registration_open,
            'registration_count': len(registrations),
            'registrations': registrations,
            'available_grades': available_grades,
            'stats': {
                'total': len(registrations),
                'pending': sum(1 for r in registrations if r['status'] == 'pending'),
                'approved': sum(1 for r in registrations if r['status'] == 'approved'),
                'passed': sum(1 for r in registrations if r['status'] == 'passed'),
                'failed': sum(1 for r in registrations if r['status'] == 'failed'),
                'absent': sum(1 for r in registrations if r['status'] == 'absent'),
            },
        })

    def put(self, request, exam_id):
        """Update an exam."""
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExam, Grade

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Examen non trouvé'}, status=404)

        data = request.data
        if 'title' in data:
            exam.title = data['title']
        if 'description' in data:
            exam.description = data['description']
        if 'date' in data:
            exam.date = data['date']
        if 'location' in data:
            exam.location = data['location']
        if 'max_participants' in data:
            exam.max_participants = int(data['max_participants'])
        if 'registration_deadline' in data:
            exam.registration_deadline = data['registration_deadline']
        if 'examiners' in data:
            exam.examiners = data['examiners']
        if 'fee' in data:
            exam.fee = data['fee']
        if 'status' in data:
            exam.status = data['status']
        if 'notes' in data:
            exam.notes = data['notes']

        try:
            exam.save()

            # Update available grades if provided
            grade_ids = data.get('available_grade_ids')
            if grade_ids is not None:
                grades = Grade.objects.filter(id__in=grade_ids, discipline=exam.discipline)
                exam.available_grades.set(grades)

            return Response({
                'id': exam.id,
                'message': 'Examen mis à jour avec succès',
            })
        except Exception as e:
            logger.error(f"ExamDetailManagementView PUT error: {e}")
            return Response({'error': str(e)}, status=400)

    def delete(self, request, exam_id):
        """Delete an exam (only if no registrations)."""
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExam

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Examen non trouvé'}, status=404)

        if exam.registrations.exists():
            return Response({
                'error': 'Impossible de supprimer un examen avec des inscriptions. Annulez-le plutôt.'
            }, status=400)

        exam.delete()
        return Response({'message': 'Examen supprimé avec succès'})


class ExamRegisterPractitionerView(APIView):
    """
    API endpoint to register a practitioner for an exam.
    POST: Register practitioner
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, exam_id):
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExam, GradeExamRegistration, Grade
        from apps.competitions.models import Practitioner

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Examen non trouvé'}, status=404)

        if not exam.is_registration_open:
            return Response({'error': 'Les inscriptions sont fermées pour cet examen'}, status=400)

        data = request.data
        practitioner_id = data.get('practitioner_id')
        target_grade_id = data.get('target_grade_id')

        if not practitioner_id or not target_grade_id:
            return Response({'error': 'practitioner_id et target_grade_id requis'}, status=400)

        try:
            practitioner = Practitioner.objects.get(id=practitioner_id)
            target_grade = Grade.objects.get(id=target_grade_id)
        except Practitioner.DoesNotExist:
            return Response({'error': 'Pratiquant non trouvé'}, status=404)
        except Grade.DoesNotExist:
            return Response({'error': 'Grade non trouvé'}, status=404)

        # Check if already registered
        if GradeExamRegistration.objects.filter(exam=exam, practitioner=practitioner).exists():
            return Response({'error': 'Ce pratiquant est déjà inscrit à cet examen'}, status=400)

        try:
            registration = GradeExamRegistration.objects.create(
                exam=exam,
                practitioner=practitioner,
                target_grade=target_grade,
                status='pending',
            )
            return Response({
                'id': registration.id,
                'practitioner_name': practitioner.full_name,
                'target_grade_name': target_grade.name,
                'message': 'Inscription enregistrée avec succès',
            }, status=201)
        except Exception as e:
            logger.error(f"ExamRegisterPractitionerView error: {e}")
            return Response({'error': str(e)}, status=400)


class ExamRegistrationStatusView(APIView):
    """
    API endpoint to update registration status.
    PUT: Update status (approve, reject, pass, fail, absent)
    DELETE: Cancel/remove registration
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def put(self, request, registration_id):
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExamRegistration, PractitionerGrade
        from django.utils import timezone

        try:
            registration = GradeExamRegistration.objects.select_related(
                'practitioner', 'target_grade', 'target_grade__discipline', 'exam'
            ).get(id=registration_id)
        except GradeExamRegistration.DoesNotExist:
            return Response({'error': 'Inscription non trouvée'}, status=404)

        data = request.data
        new_status = data.get('status')
        valid_statuses = dict(GradeExamRegistration.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response({'error': f'Statut invalide. Valeurs: {list(valid_statuses)}'}, status=400)

        registration.status = new_status
        if 'score' in data and data['score']:
            registration.score = data['score']
        if 'examiner_notes' in data:
            registration.examiner_notes = data['examiner_notes']

        # If passed, auto-create PractitionerGrade
        if new_status == 'passed' and registration.target_grade:
            if not PractitionerGrade.objects.filter(
                practitioner=registration.practitioner,
                grade=registration.target_grade,
                date_obtained=registration.exam.date or timezone.now().date()
            ).exists():
                PractitionerGrade.objects.create(
                    practitioner=registration.practitioner,
                    grade=registration.target_grade,
                    discipline=registration.target_grade.discipline,
                    date_obtained=registration.exam.date or timezone.now().date(),
                    awarded_by=registration.exam.examiners or '',
                    location=registration.exam.location or '',
                    is_current=True,
                )
                # Deactivate other current grades for same discipline
                PractitionerGrade.objects.filter(
                    practitioner=registration.practitioner,
                    discipline=registration.target_grade.discipline,
                    is_current=True
                ).exclude(grade=registration.target_grade).update(is_current=False)
                registration.certificate_issued = True

        registration.save()
        return Response({
            'id': registration.id,
            'status': registration.status,
            'message': 'Statut mis à jour avec succès',
        })

    def delete(self, request, registration_id):
        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        from apps.grades.models import GradeExamRegistration

        try:
            registration = GradeExamRegistration.objects.get(id=registration_id)
        except GradeExamRegistration.DoesNotExist:
            return Response({'error': 'Inscription non trouvée'}, status=404)

        registration.delete()
        return Response({'message': 'Inscription annulée avec succès'})


class ClubPractitionersForExamView(APIView):
    """
    API endpoint to list practitioners available for exam registration.
    Returns practitioners from the user's organization.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, exam_id=None):
        from apps.competitions.models import Practitioner
        from apps.grades.models import GradeExam

        user = request.user
        org = _get_user_organization(user)

        practitioners_qs = Practitioner.objects.all()
        if org:
            practitioners_qs = practitioners_qs.filter(organization=org)
        elif not user.is_superuser:
            practitioners_qs = Practitioner.objects.none()

        # If exam_id provided, exclude already registered practitioners
        registered_ids = set()
        if exam_id:
            try:
                exam = GradeExam.objects.get(id=exam_id)
                registered_ids = set(
                    exam.registrations.values_list('practitioner_id', flat=True)
                )
            except GradeExam.DoesNotExist:
                pass

        search = request.GET.get('search', '').strip()
        if search:
            from django.db.models import Q
            practitioners_qs = practitioners_qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        result = []
        for p in practitioners_qs.order_by('last_name', 'first_name')[:100]:
            photo_url = None
            try:
                if p.photo:
                    photo_url = p.photo.url
            except Exception:
                pass
            result.append({
                'id': p.id,
                'full_name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'birth_date': p.birth_date.isoformat() if p.birth_date else None,
                'is_registered': p.id in registered_ids,
                'photo_url': photo_url,
            })

        return Response({
            'practitioners': result,
            'count': len(result),
        })


class AvailableGradesForExamView(APIView):
    """
    API endpoint to get available grades for an exam's discipline.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from apps.grades.models import Grade

        discipline_id = request.GET.get('discipline_id')
        if not discipline_id:
            return Response({'grades': [], 'error': 'discipline_id requis'}, status=400)

        grades = Grade.objects.filter(
            discipline_id=discipline_id, is_active=True
        ).order_by('level')

        result = []
        for g in grades:
            result.append({
                'id': g.id,
                'name': g.name,
                'level': g.level,
                'color': g.color or '',
                'color_code': g.color_code or '',
                'is_dan_grade': g.is_dan_grade,
            })

        return Response({
            'grades': result,
            'count': len(result),
        })


# ========================
# SCORING API ENDPOINTS
# ========================

class ExamScoringDataView(APIView):
    """
    GET: Returns full scoring data for an exam (modules, criteria, candidates, scores).
    Used by both the examiner sheet and the scoring dashboard.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, exam_id):
        from apps.grades.models import GradeExam, ExamScoringModule, ExamScore
        from apps.competitions.models import Practitioner

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Exam not found'}, status=404)

        user = request.user

        # Find examiner's practitioner profile
        examiner_practitioner = None
        try:
            examiner_practitioner = Practitioner.objects.filter(user=user).first()
        except Exception:
            pass

        # Get modules with criteria
        modules_data = []
        all_modules = exam.scoring_modules.prefetch_related('criteria', 'assigned_examiners').order_by('order')

        for module in all_modules:
            examiner_ids = list(module.assigned_examiners.values_list('id', flat=True))
            is_assigned = (
                examiner_practitioner and examiner_practitioner.id in examiner_ids
            ) or user.is_superuser or user.is_staff

            criteria_data = []
            for criterion in module.criteria.order_by('order'):
                criteria_data.append({
                    'id': criterion.id,
                    'name': criterion.name,
                    'coefficient': str(criterion.coefficient),
                    'max_score': str(criterion.max_score),
                    'order': criterion.order,
                    'description': criterion.description or '',
                })

            modules_data.append({
                'id': module.id,
                'name': module.name,
                'order': module.order,
                'is_assigned': is_assigned,
                'criteria': criteria_data,
                'examiner_count': len(examiner_ids),
            })

        # Get candidates (registrations)
        registrations = exam.registrations.filter(
            status__in=['approved', 'pending', 'passed', 'failed']
        ).select_related('practitioner', 'target_grade')

        candidates = []
        for reg in registrations:
            photo_url = None
            try:
                if reg.practitioner.photo:
                    photo_url = reg.practitioner.photo.url
            except Exception:
                pass
            candidates.append({
                'registration_id': reg.id,
                'practitioner_id': reg.practitioner.id,
                'full_name': reg.practitioner.full_name,
                'first_name': reg.practitioner.first_name,
                'last_name': reg.practitioner.last_name,
                'target_grade': reg.target_grade.name if reg.target_grade else '',
                'status': reg.status,
                'score': str(reg.score) if reg.score else None,
                'photo_url': photo_url,
            })

        # Get existing scores for current examiner
        my_scores = {}
        if examiner_practitioner:
            scores_qs = ExamScore.objects.filter(
                registration__exam=exam,
                examiner=examiner_practitioner
            ).select_related('criterion', 'registration')
            for s in scores_qs:
                key = f"{s.registration_id}_{s.criterion_id}"
                my_scores[key] = {
                    'value': str(s.value),
                    'comment': s.comment,
                }

        return Response({
            'exam': {
                'id': exam.id,
                'title': exam.title,
                'date': exam.date.isoformat() if exam.date else None,
                'status': exam.status,
                'location': exam.location or '',
            },
            'modules': modules_data,
            'candidates': candidates,
            'my_scores': my_scores,
            'examiner_id': examiner_practitioner.id if examiner_practitioner else None,
            'is_examiner': examiner_practitioner is not None,
        })


class SaveScoreView(APIView):
    """
    POST: Save or update an individual score.
    Body: { registration_id, criterion_id, value, comment? }
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        from apps.grades.models import ExamScore, ExamScoringCriterion, GradeExamRegistration
        from apps.competitions.models import Practitioner
        from apps.grades.exam_scoring_service import get_score_color, calculate_criterion_score

        user = request.user
        examiner = Practitioner.objects.filter(user=user).first()
        if not examiner:
            return Response({'error': 'Examiner profile not found'}, status=403)

        registration_id = request.data.get('registration_id')
        criterion_id = request.data.get('criterion_id')
        value = request.data.get('value')

        if not all([registration_id, criterion_id, value is not None]):
            return Response({'error': 'Missing required fields'}, status=400)

        try:
            value = float(value)
            if value < 0 or value > 10:
                return Response({'error': 'Value must be between 0 and 10'}, status=400)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid value'}, status=400)

        try:
            registration = GradeExamRegistration.objects.get(id=registration_id)
            criterion = ExamScoringCriterion.objects.get(id=criterion_id)
        except (GradeExamRegistration.DoesNotExist, ExamScoringCriterion.DoesNotExist):
            return Response({'error': 'Registration or criterion not found'}, status=404)

        # Upsert score
        score, created = ExamScore.objects.update_or_create(
            registration=registration,
            criterion=criterion,
            examiner=examiner,
            defaults={
                'value': value,
                'comment': request.data.get('comment', ''),
            }
        )

        # Calculate updated average for this criterion
        criterion_result = calculate_criterion_score(registration, criterion)

        return Response({
            'success': True,
            'score_id': score.id,
            'value': str(score.value),
            'criterion_average': str(criterion_result['average']) if criterion_result['average'] else None,
            'criterion_color': criterion_result['color'],
            'created': created,
        })


class ScoringDashboardView(APIView):
    """
    GET: Returns scoring dashboard data (stats, progress, candidate rankings).
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, exam_id):
        from apps.grades.models import GradeExam
        from apps.grades.exam_scoring_service import get_scoring_dashboard_data

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Exam not found'}, status=404)

        dashboard = get_scoring_dashboard_data(exam)

        # Serialize practitioner data
        rankings = []
        for pd in dashboard['practitioner_data']:
            reg = pd['registration']
            module_scores = []
            for ms in pd['module_scores']:
                module_scores.append({
                    'module_name': ms['module'].name,
                    'score': str(ms['score']) if ms['score'] is not None else None,
                    'color': ms['color'],
                    'scored_criteria': ms['scored_criteria'],
                    'total_criteria': ms['total_criteria'],
                })
            rankings.append({
                'registration_id': reg.id,
                'practitioner_name': reg.practitioner.full_name,
                'target_grade': reg.target_grade.name if reg.target_grade else '',
                'status': reg.status,
                'total_score': str(pd['total_score']) if pd['total_score'] is not None else None,
                'total_color': pd['total_color'],
                'module_scores': module_scores,
            })

        return Response({
            'exam': {
                'id': exam.id,
                'title': exam.title,
                'status': exam.status,
            },
            'stats': {
                'total_registrations': dashboard['total_registrations'],
                'expected_scores': dashboard['expected_scores'],
                'actual_scores': dashboard['actual_scores'],
                'progress_percent': dashboard['progress_percent'],
                'avg_score': str(dashboard['avg_score']) if dashboard['avg_score'] else None,
                'max_score': str(dashboard['max_score']) if dashboard['max_score'] else None,
                'min_score': str(dashboard['min_score']) if dashboard['min_score'] else None,
            },
            'rankings': rankings,
        })


class PublishResultsView(APIView):
    """
    POST: Publish exam results (mark pass/fail, create PractitionerGrade records).
    Body: { passing_threshold?: number (default 5.0) }
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, exam_id):
        from apps.grades.models import GradeExam
        from apps.grades.exam_scoring_service import publish_results

        if not _is_club_manager(request.user):
            return Response({'error': 'Permission denied'}, status=403)

        try:
            exam = GradeExam.objects.get(id=exam_id)
        except GradeExam.DoesNotExist:
            return Response({'error': 'Exam not found'}, status=404)

        threshold = float(request.data.get('passing_threshold', 5.0))
        results = publish_results(exam, threshold)

        return Response({
            'success': True,
            'passed': results['passed'],
            'failed': results['failed'],
            'exam_status': exam.status,
        })


# Local URLConf to allow include('apps.grades.api')
from django.urls import path  # noqa: E402

urlpatterns = [
    path('', GradesListView.as_view(), name='grades_list_api'),
    path('categories/', GradeCategoriesView.as_view(), name='grade_categories_api'),
    path('exams/', GradeExamsView.as_view(), name='grade_exams_api'),
    path('practitioner/', PractitionerGradesView.as_view(), name='practitioner_grades_api'),
    # Management endpoints
    path('management/exams/', ExamManagementView.as_view(), name='exam_management_api'),
    path('management/exams/<int:exam_id>/', ExamDetailManagementView.as_view(), name='exam_detail_management_api'),
    path('management/exams/<int:exam_id>/register/', ExamRegisterPractitionerView.as_view(), name='exam_register_api'),
    path('management/exams/<int:exam_id>/practitioners/', ClubPractitionersForExamView.as_view(), name='exam_practitioners_api'),
    path('management/registrations/<int:registration_id>/', ExamRegistrationStatusView.as_view(), name='exam_registration_status_api'),
    path('management/available-grades/', AvailableGradesForExamView.as_view(), name='available_grades_api'),
    path('management/practitioners/', ClubPractitionersForExamView.as_view(), name='club_practitioners_api'),
    # Scoring endpoints
    path('scoring/exam/<int:exam_id>/', ExamScoringDataView.as_view(), name='exam_scoring_data_api'),
    path('scoring/save-score/', SaveScoreView.as_view(), name='save_score_api'),
    path('scoring/exam/<int:exam_id>/dashboard/', ScoringDashboardView.as_view(), name='scoring_dashboard_api'),
    path('scoring/exam/<int:exam_id>/publish/', PublishResultsView.as_view(), name='publish_results_api'),
]
