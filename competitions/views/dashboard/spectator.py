from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings
import os

# Maintenant que match.py existe, nous pouvons importer Match
from competitions.models import Competition, Match, Discipline, Club

@login_required
def spectator_dashboard(request, extra_context=None):
    """
    Dashboard pour les spectateurs.
    Affiche les compétitions à venir, les matchs en direct, et les disciplines populaires.
    """
    # Date actuelle pour les filtres
    now = timezone.now()
    
    # Récupérer les compétitions à venir
    upcoming_competitions = Competition.objects.filter(
        start_date__gte=now.date(),
        is_published=True
    ).order_by('start_date')[:5]
    
    # Récupérer les matchs en direct
    live_matches = Match.objects.filter(
        status='in_progress'
    ).order_by('date_match')[:3]
    
    # Récupérer les résultats récents
    recent_results = Match.objects.filter(
        status='completed'
    ).order_by('-end_time')[:5]
    
    # Récupérer les disciplines de la base de données
    disciplines_list = Discipline.objects.filter(is_active=True).order_by('name')
    
    # Préparer les données des disciplines avec les URLs des images
    disciplines = []
    
    # Dictionnaire des URLs d'images pour les disciplines
    discipline_images = {
        'qwan ki do': 'https://images.unsplash.com/photo-1594381898411-846e7d193883?q=80&w=800&auto=format&fit=crop',
        'viet vo dao': 'https://images.pexels.com/photos/7045664/pexels-photo-7045664.jpeg?auto=compress&cs=tinysrgb&w=800',
        'vo co truyen': 'https://images.unsplash.com/photo-1591117207239-788bf8de6c3b?q=80&w=800&auto=format&fit=crop',
        'karaté': 'https://images.unsplash.com/photo-1555597673-b21d5c935865?q=80&w=800&auto=format&fit=crop',
        'judo': 'https://images.unsplash.com/photo-1550747528-cdb45925b3f7?q=80&w=800&auto=format&fit=crop',
        'taekwondo': 'https://images.unsplash.com/photo-1571513800374-df1bbe650e56?q=80&w=800&auto=format&fit=crop',
        'kung fu': 'https://images.unsplash.com/photo-1579722820903-01d3e776f85e?q=80&w=800&auto=format&fit=crop',
        'aïkido': 'https://images.unsplash.com/photo-1602827167732-d2714841630a?q=80&w=800&auto=format&fit=crop',
        'jiu-jitsu brésilien': 'https://images.unsplash.com/photo-1542466500-dccb2789cbbb?q=80&w=800&auto=format&fit=crop',
        'muay thaï': 'https://images.unsplash.com/photo-1599058917765-a780eda07a3e?q=80&w=800&auto=format&fit=crop',
        'krav maga': 'https://images.unsplash.com/photo-1517438476312-10d79c077509?q=80&w=800&auto=format&fit=crop',
        'capoeira': 'https://images.unsplash.com/photo-1519121347263-ced01d31511d?q=80&w=800&auto=format&fit=crop',
        'wing chun': 'https://images.pexels.com/photos/6765836/pexels-photo-6765836.jpeg?auto=compress&cs=tinysrgb&w=800',
        'sambo': 'https://images.pexels.com/photos/9643603/pexels-photo-9643603.jpeg?auto=compress&cs=tinysrgb&w=800',
        'pencak silat': 'https://images.unsplash.com/photo-1630091003936-aea522432151?q=80&w=800&auto=format&fit=crop',
        'hapkido': 'https://images.pexels.com/photos/8224967/pexels-photo-8224967.jpeg?auto=compress&cs=tinysrgb&w=800',
        'kyokushin': 'https://images.unsplash.com/photo-1574453905018-eebc4e3f8d5c?q=80&w=800&auto=format&fit=crop',
        'systema': 'https://images.pexels.com/photos/7045690/pexels-photo-7045690.jpeg?auto=compress&cs=tinysrgb&w=800',
        'bokator': 'https://images.pexels.com/photos/7045485/pexels-photo-7045485.jpeg?auto=compress&cs=tinysrgb&w=800',
        'ninjutsu': 'https://images.unsplash.com/photo-1645811621851-9ca32bcb1328?q=80&w=800&auto=format&fit=crop',
        'kali': 'https://images.pexels.com/photos/7045476/pexels-photo-7045476.jpeg?auto=compress&cs=tinysrgb&w=800',
        'escrima': 'https://images.pexels.com/photos/7045476/pexels-photo-7045476.jpeg?auto=compress&cs=tinysrgb&w=800',
        'arnis': 'https://images.pexels.com/photos/7045476/pexels-photo-7045476.jpeg?auto=compress&cs=tinysrgb&w=800',
        'lethwei': 'https://images.pexels.com/photos/6765094/pexels-photo-6765094.jpeg?auto=compress&cs=tinysrgb&w=800',
        'sanda': 'https://images.unsplash.com/photo-1636473397316-85b1e8c0b800?q=80&w=800&auto=format&fit=crop',
        'sanshou': 'https://images.unsplash.com/photo-1636473397316-85b1e8c0b800?q=80&w=800&auto=format&fit=crop',
        'tang soo do': 'https://images.unsplash.com/photo-1620622586072-e51bba2fc0af?q=80&w=800&auto=format&fit=crop',
        'panantukan': 'https://images.pexels.com/photos/4752861/pexels-photo-4752861.jpeg?auto=compress&cs=tinysrgb&w=800',
        'kendo': 'https://images.unsplash.com/photo-1529630218527-7df22fc2d4ee?q=80&w=800&auto=format&fit=crop',
        'iaido': 'https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop',
        'baguazhang': 'https://images.pexels.com/photos/8810268/pexels-photo-8810268.jpeg?auto=compress&cs=tinysrgb&w=800',
        'kajukenbo': 'https://images.pexels.com/photos/7045650/pexels-photo-7045650.jpeg?auto=compress&cs=tinysrgb&w=800',
        'dambe': 'https://images.pexels.com/photos/7045604/pexels-photo-7045604.jpeg?auto=compress&cs=tinysrgb&w=800',
    }
    
    # Image par défaut si la discipline n'est pas trouvée dans le dictionnaire
    default_image = 'https://images.unsplash.com/photo-1574894709920-11b28e7367e3?q=80&w=800&auto=format&fit=crop'
    
    for discipline in disciplines_list:
        # Prendre le nom en minuscules pour comparer avec les clés du dictionnaire
        discipline_name_lower = discipline.name.lower()
        
        # Chercher l'image correspondante dans le dictionnaire
        image_url = discipline_images.get(discipline_name_lower, default_image)
            
        # Créer un extrait de la description s'il y en a une
        short_description = "Découvrez les bases"
        if discipline.description:
            # Limiter la description à 80 caractères et ajouter '...' si nécessaire
            short_description = (discipline.description[:80] + '...') if len(discipline.description) > 80 else discipline.description
            
        # Ajouter les données à la liste
        disciplines.append({
            'id': discipline.id,
            'name': discipline.name,
            'description': discipline.description,
            'short_description': short_description,
            'country_origin': discipline.country_origin,
            'image_url': image_url
        })
    
    # Récupérer la localisation de l'utilisateur (si disponible)
    user_city = None
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'city'):
        user_city = request.user.profile.city
    
    # Récupérer les clubs
    nearby_clubs = Club.objects.filter(is_active=True)
    
    # Si l'utilisateur a une ville définie, filtrer les clubs de la même ville
    if user_city:
        nearby_clubs = nearby_clubs.filter(city=user_city)
    
    # Sinon, simplement récupérer quelques clubs populaires
    if not nearby_clubs.exists():
        nearby_clubs = Club.objects.filter(is_active=True)
    
    # Limiter à 5 clubs
    nearby_clubs = nearby_clubs[:5]
    
    context = {
        'upcoming_competitions': upcoming_competitions,
        'live_matches': live_matches,
        'recent_results': recent_results,
        'disciplines': disciplines[:5],  # Limiter à 5 pour l'affichage initial
        'all_disciplines': disciplines,  # Toutes les disciplines pour la vue complète
        'nearby_clubs': nearby_clubs,
        'role': 'spectator',
        'page_title': _('Tableau de bord spectateur')
    }
    
    if extra_context:
        context.update(extra_context)
    
    return render(request, 'competitions/dashboard/spectator.html', context)