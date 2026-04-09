"""
Vues pour le Centre de Tutoriels MartialComp
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count

from apps.competitions.models.tutorials import TutorialSection, Tutorial
from apps.competitions.models import UserProfile

import logging

logger = logging.getLogger('django')


@login_required
def tutorial_center(request):
    """Page principale du centre de tutoriels"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('welcome')

    # Filtres
    current_audience = request.GET.get('audience', '')
    search_query = request.GET.get('q', '').strip()

    # Sections actives avec tutoriels
    sections = TutorialSection.objects.filter(
        is_active=True
    ).prefetch_related('tutorials')

    # Filtrer les tutoriels
    tutorial_filter = Q(is_active=True)
    if current_audience:
        tutorial_filter &= Q(audience=current_audience) | Q(audience='all')
    if search_query:
        tutorial_filter &= (
            Q(title__icontains=search_query) |
            Q(tip__icontains=search_query) |
            Q(steps__icontains=search_query)
        )

    # Construire les sections avec tutoriels filtrés
    sections_data = []
    for section in sections:
        tutorials = section.tutorials.filter(tutorial_filter).order_by('order', 'number')
        if tutorials.exists():
            sections_data.append({
                'section': section,
                'tutorials': tutorials,
            })

    # Stats
    total_tutorials = Tutorial.objects.filter(is_active=True).count()
    total_sections = TutorialSection.objects.filter(is_active=True).count()
    total_videos = Tutorial.objects.filter(is_active=True).exclude(youtube_url='').count()

    # Choix d'audience pour le filtre
    audiences = Tutorial.AUDIENCE_CHOICES

    context = {
        'sections_data': sections_data,
        'audiences': audiences,
        'current_audience': current_audience,
        'search_query': search_query,
        'stats': {
            'total_tutorials': total_tutorials,
            'total_sections': total_sections,
            'total_videos': total_videos,
        },
    }

    return render(request, 'competitions/dashboard/tutorials/tutorial_center.html', context)


@login_required
def tutorial_detail(request, tutorial_id):
    """Page de detail d'un tutoriel"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('welcome')

    tutorial = get_object_or_404(
        Tutorial.objects.select_related('section'),
        id=tutorial_id,
        is_active=True
    )

    # Navigation prev/next dans la section
    section_tutorials = Tutorial.objects.filter(
        section=tutorial.section,
        is_active=True
    ).order_by('order', 'number')

    tutorials_list = list(section_tutorials)
    current_index = None
    for i, t in enumerate(tutorials_list):
        if t.id == tutorial.id:
            current_index = i
            break

    prev_tutorial = tutorials_list[current_index - 1] if current_index and current_index > 0 else None
    next_tutorial = tutorials_list[current_index + 1] if current_index is not None and current_index < len(tutorials_list) - 1 else None

    context = {
        'tutorial': tutorial,
        'steps': tutorial.get_steps_list(),
        'embed_url': tutorial.get_youtube_embed_url(),
        'prev_tutorial': prev_tutorial,
        'next_tutorial': next_tutorial,
    }

    return render(request, 'competitions/dashboard/tutorials/tutorial_detail.html', context)


@login_required
def tutorial_search_api(request):
    """API AJAX pour recherche temps reel"""
    q = request.GET.get('q', '').strip()
    audience = request.GET.get('audience', '')

    if len(q) < 2 and not audience:
        return JsonResponse({'results': []})

    filters = Q(is_active=True)
    if q:
        filters &= (
            Q(title__icontains=q) |
            Q(tip__icontains=q) |
            Q(steps__icontains=q)
        )
    if audience:
        filters &= Q(audience=audience) | Q(audience='all')

    tutorials = Tutorial.objects.filter(filters).select_related('section').order_by(
        'section__order', 'order', 'number'
    )[:20]

    results = []
    for t in tutorials:
        results.append({
            'id': t.id,
            'title': t.title,
            'section': t.section.title,
            'section_icon': t.section.icon,
            'audience': t.audience,
            'format': t.format,
            'duration': t.duration,
            'has_video': t.has_video,
        })

    return JsonResponse({'results': results})
