#!/usr/bin/env python3
"""
Diagnostic approfondi du problème BACH HAC
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import TechnicalPerformance, Practitioner, Club, Judge
from django.db import connection
import traceback

def deep_diagnose():
    """Diagnostic approfondi"""
    print("=== Diagnostic approfondi du problème BACH HAC ===\n")
    
    # 1. Vérifier la structure exacte du problème
    print("1. Recherche de 'BACH HAC' dans toutes les tables pertinentes")
    
    with connection.cursor() as cursor:
        # Vérifier dans la table Club
        cursor.execute("""
            SELECT id, name FROM competitions_club 
            WHERE name LIKE '%BACH%' OR name LIKE '%HAC%'
        """)
        clubs = cursor.fetchall()
        print(f"\nClubs trouvés: {len(clubs)}")
        for club in clubs:
            print(f"  - Club {club[0]}: {club[1]}")
        
        # Vérifier dans la table Practitioner
        cursor.execute("""
            SELECT id, full_name, club_id FROM competitions_practitioner 
            WHERE full_name LIKE '%BACH%' OR full_name LIKE '%HAC%'
        """)
        practitioners = cursor.fetchall()
        print(f"\nPratiquants trouvés: {len(practitioners)}")
        for p in practitioners:
            print(f"  - Practitioner {p[0]}: {p[1]} (club_id: {p[2]})")
        
        # Vérifier dans la table Judge
        cursor.execute("""
            SELECT j.id, p.full_name, j.practitioner_id 
            FROM competitions_judge j
            LEFT JOIN competitions_practitioner p ON j.practitioner_id = p.id
            WHERE p.full_name LIKE '%BACH%' OR p.full_name LIKE '%HAC%'
        """)
        judges = cursor.fetchall()
        print(f"\nJuges trouvés: {len(judges)}")
        for j in judges:
            print(f"  - Judge {j[0]}: {j[1]} (practitioner_id: {j[2]})")
    
    # 2. Examiner la vue technical_scoring pour voir où l'erreur se produit
    print("\n2. Test de la requête problématique")
    
    # Simuler ce que fait la vue
    try:
        # Obtenir un club pour tester
        test_club = Club.objects.first()
        if test_club:
            print(f"\nTest avec le club: {test_club.name}")
            
            # Tester la requête des juges
            try:
                judges = Judge.objects.filter(
                    practitioner__club=test_club,
                    is_technical_judge=True
                ).select_related('practitioner')
                print(f"  - Juges trouvés: {judges.count()}")
            except Exception as e:
                print(f"  - Erreur lors de la requête des juges: {e}")
                traceback.print_exc()
            
            # Tester la requête des performances
            try:
                from django.db.models import Q
                from django.utils import timezone
                
                now = timezone.now().date()
                
                # Test direct
                performances = TechnicalPerformance.objects.filter(
                    practitioner__club=test_club
                )[:5]
                print(f"  - Performances directes trouvées: {performances.count()}")
                
            except Exception as e:
                print(f"  - Erreur lors de la requête des performances: {e}")
                traceback.print_exc()
    
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        traceback.print_exc()
    
    # 3. Vérifier s'il y a une confusion entre Club et Practitioner
    print("\n3. Vérification des types de données")
    
    # Chercher si "BACH HAC" est utilisé incorrectement quelque part
    with connection.cursor() as cursor:
        # Vérifier les contraintes de clé étrangère
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name LIKE 'competitions_%'
                AND (kcu.column_name LIKE '%practitioner%' OR kcu.column_name LIKE '%club%')
        """)
        constraints = cursor.fetchall()
        print("\nContraintes de clé étrangère pertinentes:")
        for c in constraints:
            print(f"  - {c[1]}.{c[2]} -> {c[3]}.{c[4]}")

def check_specific_error():
    """Vérifie l'erreur spécifique dans la vue"""
    print("\n4. Test spécifique de l'erreur")
    
    # Importer le code problématique
    try:
        from competitions.views.club.technical_scoring import technical_scoring
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        
        # Créer une requête de test
        factory = RequestFactory()
        request = factory.get('/competitions/club/technical-scoring/')
        
        # Simuler un utilisateur avec un club
        user = User.objects.first()
        if user:
            request.user = user
            
            # Chercher un club associé
            try:
                from competitions.models import UserProfile
                profile = UserProfile.objects.filter(user=user).first()
                if profile and profile.club:
                    request.club = profile.club
                    print(f"Test avec user: {user.username}, club: {request.club.name}")
                else:
                    # Créer un club de test
                    test_club = Club.objects.first()
                    request.club = test_club
                    print(f"Test avec user: {user.username}, club de test: {test_club.name if test_club else 'None'}")
            except:
                test_club = Club.objects.first()
                request.club = test_club
                print(f"Test avec club de test: {test_club.name if test_club else 'None'}")
            
            # Appeler la vue
            try:
                response = technical_scoring(request)
                print("Vue exécutée avec succès")
            except Exception as e:
                print(f"Erreur lors de l'exécution de la vue: {e}")
                traceback.print_exc()
    
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        traceback.print_exc()

def suggest_immediate_fix():
    """Suggère une correction immédiate"""
    print("\n=== Solution immédiate ===")
    
    fix_code = '''# competitions/views/club/technical_scoring_emergency_fix.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.db import connection
import logging

from ...models import (
    Club, Competition, TechnicalPerformance, ScoringCriterion, 
    Score, Judge, Practitioner
)
from ...utils.decorators import club_required

logger = logging.getLogger(__name__)

@login_required
@club_required
def technical_scoring_emergency(request):
    """Version d'urgence de technical_scoring avec diagnostic intégré"""
    club = request.club
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Log pour debug
    logger.info(f"Technical scoring accessed - Club: {club.name} (ID: {club.id})")
    
    # Date actuelle
    now = timezone.now().date()
    
    # Vérifier l'organisation associée
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    logger.info(f"Club organization: {club_organization}")
    
    # Compétitions actives - requête sécurisée
    try:
        active_competitions = Competition.objects.filter(
            end_date__gte=now,
            status__in=['published', 'ongoing']
        ).distinct().order_by('start_date')
        logger.info(f"Active competitions found: {active_competitions.count()}")
    except Exception as e:
        logger.error(f"Error getting competitions: {e}")
        active_competitions = Competition.objects.none()
    
    # Juges techniques - requête sécurisée avec ID
    judges = []
    try:
        # Utiliser une requête SQL brute pour éviter les problèmes de type
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT j.id, p.full_name, p.id as practitioner_id
                FROM competitions_judge j
                JOIN competitions_practitioner p ON j.practitioner_id = p.id
                WHERE p.club_id = %s AND j.is_technical_judge = true
            """, [club.id])
            
            judge_data = cursor.fetchall()
            logger.info(f"Judges found: {len(judge_data)}")
            
            # Convertir en objets Judge
            for jid, pname, pid in judge_data:
                try:
                    judge = Judge.objects.get(id=jid)
                    judges.append(judge)
                except:
                    logger.error(f"Could not load judge {jid}")
    except Exception as e:
        logger.error(f"Error getting judges: {e}")
        judges = []
    
    # Performances récentes - requête ultra-sécurisée
    recent_performances = []
    try:
        # Requête SQL brute pour éviter tout problème de type
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT tp.id
                FROM competitions_technicalperformance tp
                JOIN competitions_practitioner p ON tp.practitioner_id = p.id
                JOIN competitions_competition c ON tp.competition_id = c.id
                WHERE p.club_id = %s
                AND c.end_date >= %s
                ORDER BY tp.created_at DESC
                LIMIT 10
            """, [club.id, now - timezone.timedelta(days=30)])
            
            perf_ids = [row[0] for row in cursor.fetchall()]
            logger.info(f"Performance IDs found: {perf_ids}")
            
            # Charger les performances par ID
            if perf_ids:
                recent_performances = TechnicalPerformance.objects.filter(
                    id__in=perf_ids
                ).select_related('practitioner', 'category', 'competition')
    except Exception as e:
        logger.error(f"Error getting performances: {e}")
        recent_performances = []
    
    context = {
        'club': club,
        'active_competitions': active_competitions,
        'judges': judges,
        'recent_performances': recent_performances,
        'current_section': 'technical_scoring',
    }
    
    return render(request, 'competitions/club/technical_scoring.html', context)
'''
    
    with open('competitions/views/club/technical_scoring_emergency_fix.py', 'w', encoding='utf-8') as f:
        f.write(fix_code)
    
    print("Fichier de correction d'urgence créé: technical_scoring_emergency_fix.py")
    print("\nPour utiliser cette correction:")
    print("1. Copiez le fichier dans le bon répertoire")
    print("2. Modifiez competitions/urls/club.py pour utiliser technical_scoring_emergency")
    print("3. Redémarrez le serveur Django")

if __name__ == "__main__":
    deep_diagnose()
    check_specific_error()
    suggest_immediate_fix()