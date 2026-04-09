# -*- coding: utf-8 -*-
"""
Vue dashboard coach - VERSION DARK THEME avec touche verte
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import get_organization_queryset

logger = logging.getLogger(__name__)


@login_required
def coach_dashboard(request):
    """
    Dashboard coach - VERSION DARK THEME
    Template moderne avec theme sombre et accents verts
    """
    logger.info(f"Coach dashboard accessed by: {request.user.username}")

    # Recuperer le profil coach et les donnees
    coach_profile = None
    practitioner = None
    disciplines_count = 0
    students_count = 0

    try:
        from apps.competitions.models import CoachProfile, Practitioner, DisciplineExpertise

        # Recuperer le practitioner
        practitioner = Practitioner.objects.filter(user=request.user).first()

        if practitioner:
            # Recuperer ou creer le profil coach
            coach_profile, created = CoachProfile.objects.get_or_create(
                practitioner=practitioner,
                defaults={
                    'profile_type': 'traditional',
                    'years_teaching': 0,
                }
            )

            # Compter les disciplines
            disciplines_count = DisciplineExpertise.objects.filter(
                coach_profile=coach_profile
            ).count()

            # Compter les eleves (mock pour l'instant)
            students_count = 25

    except Exception as e:
        logger.warning(f"Erreur recuperation profil coach: {e}")

    # Recuperer les temoignages
    testimonials = [
        {
            'student_name': 'Marie Dupont',
            'rating': 5,
            'comment': _('Excellent coach ! Tres pedagogue et patient.'),
            'discipline': 'Karate'
        },
        {
            'student_name': 'Pierre Martin',
            'rating': 5,
            'comment': _('Grace a lui, j\'ai progresse tres rapidement.'),
            'discipline': 'Taekwondo'
        }
    ]

    # Construire le contexte complet
    context = {
        'user': request.user,
        'page_title': _('Dashboard Coach'),
        'dashboard_type': 'coach',
        'coach_profile': coach_profile,
        'practitioner': practitioner,
        'disciplines_count': disciplines_count,
        'students_count': students_count,
        'classes_this_week': 8,
        'monthly_revenue': '2,450',
        'total_income': '3,250',
        'total_expenses': '800',
        'net_profit': '2,450',
        'pending_amount': '1,200',
        'testimonials': testimonials,
        'today_classes': [],
        'recent_transactions': [],
        # Slug pour le site public du coach
        'coach_slug': practitioner.club.slug if practitioner and hasattr(practitioner, 'club') and practitioner.club else 'coach',
    }

    try:
        # Utiliser le nouveau template dark
        return render(request, 'competitions/dashboard/coach_dark.html', context)
    except Exception as e:
        logger.error(f"Erreur template coach_dark: {e}")

        try:
            # Fallback vers l'ancien template
            return render(request, 'competitions/dashboard/coach.html', context)
        except Exception as e2:
            logger.error(f"Erreur template coach: {e2}")

            # Dernier fallback
            context['fallback_message'] = f'Dashboard coach temporairement indisponible'
            return render(request, 'competitions/dashboard/spectator.html', context)