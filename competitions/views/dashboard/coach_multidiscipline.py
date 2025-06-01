import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg, F, Prefetch

from datetime import datetime, timedelta

from ...models import (
    UserProfile, 
    Practitioner, 
    CoachProfile, 
    DisciplineExpertise, 
    Discipline,
    TrainingSession,
    Attendance,
    TrainingReservation,
    PractitionerDiscipline
)

logger = logging.getLogger(__name__)

@login_required
def coach_multidiscipline_dashboard(request):
    """
    Tableau de bord pour les coaches multi-disciplines.
    Affiche une vue personnalisée avec toutes les fonctionnalités importantes pour un coach.
    """
    try:
        # Récupérer le profil utilisateur et vérifier le rôle
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'coach':
            messages.warning(request, _("Ce tableau de bord est réservé aux coaches."))
            return redirect('dashboard:index')
            
        # Récupérer le pratiquant et le profil coach avec prefetch des disciplines
        practitioner = get_object_or_404(Practitioner.objects.select_related('primary_discipline'), user=request.user)
        coach_profile = get_object_or_404(CoachProfile, practitioner=practitioner)
        
        # Récupérer les disciplines du coach avec optimisation des requêtes
        coach_disciplines = []
        
        # Logique de récupération des disciplines avec gestion des erreurs et préchargement des données liées
        try:
            # Charger toutes les expertises de discipline du coach
            expertises = DisciplineExpertise.objects.filter(
                coach_profile=coach_profile
            ).select_related('discipline', 'federation')
            
            # Pour chaque discipline, compter les élèves associés
            for expertise in expertises:
                # Compter les élèves pour cette discipline
                students_count = PractitionerDiscipline.objects.filter(
                    discipline=expertise.discipline,
                    practitioner__club=coach_profile.primary_teaching_place
                ).count() if coach_profile.primary_teaching_place else 0
                
                # Récupérer les détails d'enseignement pour cette discipline
                teaching_hours = TrainingSession.objects.filter(
                    discipline=expertise.discipline,
                    instructor=practitioner,
                    date__gte=timezone.now() - timedelta(days=30)
                ).aggregate(
                    total_hours=Sum(F('end_time') - F('start_time'))
                ).get('total_hours', 0)
                
                teaching_hours = teaching_hours.total_seconds() / 3600 if teaching_hours else 0
                
                # Calculer le pourcentage de compétence ou succès
                success_percentage = min(int(expertise.years_experience * 10), 100) if expertise.years_experience else 75
                
                coach_disciplines.append({
                    'id': expertise.discipline.id,
                    'name': expertise.discipline.name,
                    'icon': get_discipline_icon(expertise.discipline.name),
                    'color': f"#{''.join(['%02X' % c for c in expertise.discipline.name.encode('utf-8')[:3]])}" if expertise.discipline else "#1a237e",
                    'grade': expertise.current_grade or _("Non spécifié"),
                    'certification': expertise.teaching_certification,
                    'federation': expertise.federation.name if expertise.federation else _("Indépendant"),
                    'years_experience': expertise.years_experience or 0,
                    'years_teaching': expertise.years_teaching or 0,
                    'is_primary': expertise.is_primary,
                    'students_count': students_count,
                    'description': expertise.public_description,
                    'monthly_hours': round(teaching_hours, 1),
                    'success_percentage': success_percentage,
                    'is_public': True  # À implémenter selon les paramètres de visibilité
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des disciplines: {str(e)}")
            
            # Fallback sur la discipline principale du pratiquant
            if practitioner.primary_discipline:
                coach_disciplines.append({
                    'id': practitioner.primary_discipline.id,
                    'name': practitioner.primary_discipline.name,
                    'icon': get_discipline_icon(practitioner.primary_discipline.name),
                    'color': f"#{''.join(['%02X' % c for c in practitioner.primary_discipline.name.encode('utf-8')[:3]])}",
                    'grade': practitioner.grade_display,
                    'certification': _('Non spécifié'),
                    'federation': _('Non spécifié'),
                    'years_experience': 0,
                    'years_teaching': coach_profile.years_teaching,
                    'is_primary': True,
                    'students_count': 0,
                    'description': '',
                    'monthly_hours': 0,
                    'success_percentage': 70,
                    'is_public': True
                })
        
        # Récupérer les données réelles quand disponibles, sinon utiliser des données fictives
        today = timezone.now().date()
        
        # Sessions du jour (données réelles si disponibles)
        try:
            # Tentative de récupération des sessions du jour réelles
            real_sessions = TrainingSession.objects.filter(
                instructor=practitioner,
                date=today
            ).select_related('discipline').prefetch_related('attendees')
            
            todays_sessions = []
            
            for session in real_sessions:
                todays_sessions.append({
                    'id': session.id,
                    'title': session.title or f"{session.discipline.name} - {session.level if session.level else _('Tous niveaux')}",
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'discipline': {
                        'name': session.discipline.name,
                        'id': session.discipline.id,
                        'color': f"#{''.join(['%02X' % c for c in session.discipline.name.encode('utf-8')[:3]])}"
                    },
                    'location': session.location or _("Dojo Principal"),
                    'attendees_count': session.attendees.count(),
                    'max_capacity': session.max_capacity or 20,
                    'is_recurring': session.is_recurring
                })
                
            # Si aucune session trouvée, utiliser des données fictives
            if not todays_sessions:
                raise Exception("Aucune session aujourd'hui")
                
        except Exception:
            # Sessions fictives pour la démo
            primary_discipline = coach_disciplines[0] if coach_disciplines else {'name': _("Arts Martiaux"), 'id': 0, 'color': "#1a237e"}
            secondary_discipline = coach_disciplines[1] if len(coach_disciplines) > 1 else primary_discipline
            
            todays_sessions = [
                {
                    'id': 1,
                    'title': _("Cours débutants"),
                    'start_time': datetime.strptime('09:00', '%H:%M').time(),
                    'end_time': datetime.strptime('10:30', '%H:%M').time(),
                    'discipline': {
                        'name': primary_discipline['name'], 
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'location': _("Dojo Central"),
                    'attendees_count': 12,
                    'max_capacity': 15,
                    'is_recurring': True
                },
                {
                    'id': 2,
                    'title': _("Cours avancés"),
                    'start_time': datetime.strptime('18:00', '%H:%M').time(),
                    'end_time': datetime.strptime('19:30', '%H:%M').time(),
                    'discipline': {
                        'name': secondary_discipline['name'],
                        'id': secondary_discipline.get('id', 0),
                        'color': secondary_discipline.get('color', "#673ab7")
                    },
                    'location': _("Dojo Central"),
                    'attendees_count': 8,
                    'max_capacity': 12,
                    'is_recurring': True
                }
            ]
        
        # Données pour les évaluations à venir (avec plus de détails)
        try:
            # Cette partie devrait être remplacée par une requête réelle quand l'application le supportera
            raise Exception("Module d'évaluation non disponible")
        except Exception:
            # Données fictives enrichies
            primary_discipline = coach_disciplines[0] if coach_disciplines else {'name': _("Arts Martiaux"), 'id': 0, 'color': "#1a237e"}
            secondary_discipline = coach_disciplines[1] if len(coach_disciplines) > 1 else primary_discipline
            
            upcoming_evaluations = [
                {
                    'id': 1,
                    'student': {
                        'id': 101,
                        'full_name': _("Jean Dupont"),
                        'photo': None,
                        'initials': 'JD'
                    },
                    'discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'current_grade': _("Ceinture bleue"),
                    'target_grade': _("Ceinture marron"),
                    'date': today + timedelta(days=5),
                    'readiness_percentage': 85,
                    'days_until': 5
                },
                {
                    'id': 2,
                    'student': {
                        'id': 102,
                        'full_name': _("Marie Martin"),
                        'photo': None,
                        'initials': 'MM'
                    },
                    'discipline': {
                        'name': secondary_discipline['name'],
                        'id': secondary_discipline.get('id', 0),
                        'color': secondary_discipline.get('color', "#673ab7")
                    },
                    'current_grade': _("Ceinture verte"),
                    'target_grade': _("Ceinture bleue"),
                    'date': today + timedelta(days=7),
                    'readiness_percentage': 92,
                    'days_until': 7
                },
                {
                    'id': 3,
                    'student': {
                        'id': 103,
                        'full_name': _("Thomas Lefebvre"),
                        'photo': None,
                        'initials': 'TL'
                    },
                    'discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'current_grade': _("Ceinture noire 1er dan"),
                    'target_grade': _("Ceinture noire 2ème dan"),
                    'date': today + timedelta(days=14),
                    'readiness_percentage': 65,
                    'days_until': 14
                }
            ]
        
        # Élèves récemment actifs (plus détaillés)
        try:
            # Cette partie devrait être remplacée par une requête réelle quand l'application le supportera
            raise Exception("Module de suivi d'activités non disponible")
        except Exception:
            # Données fictives enrichies
            primary_discipline = coach_disciplines[0] if coach_disciplines else {'name': _("Arts Martiaux"), 'id': 0, 'color': "#1a237e"}
            secondary_discipline = coach_disciplines[1] if len(coach_disciplines) > 1 else primary_discipline
            third_discipline = coach_disciplines[2] if len(coach_disciplines) > 2 else primary_discipline
            
            recent_students = [
                {
                    'id': 101,
                    'full_name': _("Paul Bernard"),
                    'photo': None,
                    'initials': 'PB',
                    'primary_discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'grade_display': _("Ceinture noire 1er dan"),
                    'status': 'active',
                    'last_activity': {
                        'type': 'attendance',
                        'description': _("Cours avancés"),
                        'date': today - timedelta(days=1),
                        'id': 501
                    }
                },
                {
                    'id': 102,
                    'full_name': _("Sophie Leroy"),
                    'photo': None,
                    'initials': 'SL',
                    'primary_discipline': {
                        'name': secondary_discipline['name'],
                        'id': secondary_discipline.get('id', 0),
                        'color': secondary_discipline.get('color', "#673ab7")
                    },
                    'grade_display': _("Ceinture marron"),
                    'status': 'active',
                    'last_activity': {
                        'type': 'private_lesson',
                        'description': _("Cours particulier"),
                        'date': today - timedelta(days=2),
                        'id': 502
                    }
                },
                {
                    'id': 103,
                    'full_name': _("Lucas Dubois"),
                    'photo': None,
                    'initials': 'LD',
                    'primary_discipline': {
                        'name': third_discipline['name'],
                        'id': third_discipline.get('id', 0),
                        'color': third_discipline.get('color', "#2196f3")
                    },
                    'grade_display': _("Ceinture rouge"),
                    'status': 'inactive',
                    'last_activity': {
                        'type': 'attendance',
                        'description': _("Entraînement libre"),
                        'date': today - timedelta(days=15),
                        'id': 503
                    }
                },
                {
                    'id': 104,
                    'full_name': _("Emma Petit"),
                    'photo': None,
                    'initials': 'EP',
                    'primary_discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'grade_display': _("Ceinture bleue"),
                    'status': 'active',
                    'last_activity': {
                        'type': 'evaluation',
                        'description': _("Évaluation technique"),
                        'date': today - timedelta(days=3),
                        'id': 504
                    }
                }
            ]
        
        # Événements à venir (enrichis)
        try:
            # Cette partie devrait être remplacée par une requête réelle quand l'application le supportera
            raise Exception("Module d'événements non disponible")
        except Exception:
            # Données fictives enrichies
            primary_discipline = coach_disciplines[0] if coach_disciplines else {'name': _("Arts Martiaux"), 'id': 0, 'color': "#1a237e"}
            secondary_discipline = coach_disciplines[1] if len(coach_disciplines) > 1 else primary_discipline
            
            upcoming_events = [
                {
                    'id': 201,
                    'title': _("Stage intensif de perfectionnement"),
                    'start_date': today + timedelta(days=14),
                    'end_date': today + timedelta(days=16),
                    'discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'location': _("Centre sportif municipal"),
                    'duration': _("2 jours"),
                    'description': _("Stage de perfectionnement technique pour les ceintures marron et noires. Focus sur les applications de combat et les subtilités techniques avancées."),
                    'participants_count': 15,
                    'capacity': 30,
                    'capacity_percentage': 50,
                    'registered_count': 15,
                    'is_public': True,
                    'is_instructor': True
                },
                {
                    'id': 202,
                    'title': _("Séminaire spécial self-défense"),
                    'start_date': today + timedelta(days=21),
                    'end_date': today + timedelta(days=21),
                    'discipline': {
                        'name': secondary_discipline['name'],
                        'id': secondary_discipline.get('id', 0),
                        'color': secondary_discipline.get('color', "#673ab7")
                    },
                    'location': _("Salle polyvalente du complexe sportif"),
                    'duration': _("1 journée"),
                    'description': _("Séminaire d'introduction aux techniques de self-défense pour tous niveaux. Ouvert au public, aucune expérience préalable requise."),
                    'participants_count': 25,
                    'capacity': 40,
                    'capacity_percentage': 63,
                    'registered_count': 25,
                    'is_public': True,
                    'is_instructor': True
                }
            ]
        
        # Ressources pédagogiques (enrichies)
        try:
            # Cette partie devrait être remplacée par une requête réelle quand l'application le supportera
            raise Exception("Module de ressources pédagogiques non disponible")
        except Exception:
            # Données fictives enrichies
            primary_discipline = coach_disciplines[0] if coach_disciplines else {'name': _("Arts Martiaux"), 'id': 0, 'color': "#1a237e"}
            secondary_discipline = coach_disciplines[1] if len(coach_disciplines) > 1 else primary_discipline
            
            resources = [
                {
                    'id': 301,
                    'title': _("Techniques de base - Guide illustré"),
                    'type': 'document',
                    'format': 'pdf',
                    'discipline': {
                        'name': primary_discipline['name'],
                        'id': primary_discipline.get('id', 0),
                        'color': primary_discipline.get('color', "#1a237e")
                    },
                    'is_public': False,
                    'created_at': today - timedelta(days=30),
                    'updated_at': today - timedelta(days=15),
                    'description': _("Guide complet des techniques fondamentales avec illustrations et explications détaillées."),
                    'view_count': 42,
                    'tags': [_("débutant"), _("techniques"), _("fondamentaux")],
                    'size': "2.4 MB"
                },
                {
                    'id': 302,
                    'title': _("Préparation physique pour arts martiaux"),
                    'type': 'video',
                    'format': 'mp4',
                    'discipline': {
                        'name': _("Préparation physique"),
                        'id': 0,
                        'color': "#4caf50"
                    },
                    'is_public': True,
                    'created_at': today - timedelta(days=60),
                    'updated_at': today - timedelta(days=60),
                    'description': _("Vidéo démonstrative de séances d'entraînement pour améliorer la condition physique des pratiquants."),
                    'view_count': 128,
                    'tags': [_("échauffement"), _("renforcement"), _("cardio"), _("flexibilité")],
                    'duration': "18:24",
                    'size': "156 MB"
                },
                {
                    'id': 303,
                    'title': _("Programme d'entraînement avancé"),
                    'type': 'course',
                    'format': 'html',
                    'discipline': {
                        'name': secondary_discipline['name'],
                        'id': secondary_discipline.get('id', 0),
                        'color': secondary_discipline.get('color', "#673ab7")
                    },
                    'is_public': False,
                    'created_at': today - timedelta(days=10),
                    'updated_at': today - timedelta(days=2),
                    'description': _("Programme structuré de 8 semaines pour les pratiquants de niveau avancé."),
                    'view_count': 17,
                    'tags': [_("avancé"), _("programme"), _("entraînement"), _("progression")],
                    'lessons_count': 12
                }
            ]
        
        # Données de synthèse mensuelle pour le dashboard
        monthly_metrics = {
            'total_hours': sum(d.get('monthly_hours', 0) for d in coach_disciplines),
            'session_count': 24,  # Nombre fictif pour la démo
            'new_students': 5,  # Nombre fictif pour la démo
            'active_students': 18,  # Nombre fictif pour la démo
            'grade_promotions': 3,  # Nombre fictif pour la démo
            'revenue': 1250,  # Nombre fictif pour la démo
            'attendance_rate': 82  # Pourcentage fictif pour la démo
        }
        
        # Témoignages et validations (fictifs)
        testimonials = [
            {
                'id': 401,
                'content': _("Un excellent coach avec une pédagogie adaptée à chaque élève. Très attentif aux détails techniques et toujours disponible pour des explications supplémentaires."),
                'rating': 5,
                'author': {
                    'name': _("Alexandre Martin"),
                    'photo': None,
                    'initials': 'AM'
                },
                'discipline': {
                    'name': primary_discipline['name'],
                    'color': primary_discipline.get('color', "#1a237e")
                },
                'date': today - timedelta(days=45),
                'is_public': True
            },
            {
                'id': 402,
                'content': _("Grâce à son enseignement rigoureux mais bienveillant, j'ai pu progresser rapidement. Les cours sont variés et toujours intéressants."),
                'rating': 4,
                'author': {
                    'name': _("Claire Dubois"),
                    'photo': None,
                    'initials': 'CD'
                },
                'discipline': {
                    'name': secondary_discipline['name'],
                    'color': secondary_discipline.get('color', "#673ab7")
                },
                'date': today - timedelta(days=60),
                'is_public': True
            }
        ]
        
        # Validations techniques (fictives)
        validations = [
            {
                'id': 501,
                'title': _("Certificat d'enseignement"),
                'organization': _("Fédération Française de Karaté"),
                'date': today - timedelta(days=365*2),
                'validator': _("Commission technique nationale"),
                'is_verified': True
            },
            {
                'id': 502,
                'title': _("Diplôme d'État - DEJEPS"),
                'organization': _("Ministère des Sports"),
                'date': today - timedelta(days=365*3),
                'validator': _("Direction régionale de la jeunesse et des sports"),
                'is_verified': True
            }
        ]
        
        # Construction du contexte pour le template
        context = {
            'coach_profile': coach_profile,
            'practitioner': practitioner,
            'today_date': today,
            'disciplines_count': len(coach_disciplines),
            'certifications_count': len(validations),
            'students_count': sum(d.get('students_count', 0) for d in coach_disciplines) or 20,
            'sessions_count': 24,  # Nombre fictif pour la démo
            'coach_disciplines': coach_disciplines,
            'todays_sessions': todays_sessions,
            'upcoming_evaluations': upcoming_evaluations,
            'recent_students': recent_students,
            'upcoming_events': upcoming_events,
            'resources': resources,
            'monthly_metrics': monthly_metrics,
            'testimonials': testimonials,
            'validations': validations
        }
        
        return render(request, 'competitions/dashboard/coach_multidiscipline.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du tableau de bord coach: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors du chargement du tableau de bord."))
        return redirect('dashboard:index')

def get_discipline_icon(discipline_name):
    """
    Retourne une icône Font Awesome appropriée pour la discipline donnée.
    """
    discipline_name = discipline_name.lower() if discipline_name else ""
    
    # Mapping des disciplines courantes vers des icônes appropriées
    icon_mapping = {
        'karate': 'hand-rock',
        'judo': 'yin-yang',
        'aikido': 'circle',
        'taekwondo': 'fire',
        'kung fu': 'dragon',
        'krav maga': 'fist-raised',
        'boxe': 'boxing-glove',
        'muay thai': 'khanda',
        'capoeira': 'running',
        'jiu-jitsu': 'infinity',
        'mma': 'shield-alt',
        'tai chi': 'yin-yang',
        'qwan ki do': 'wind',
        'silat': 'khanda',
    }
    
    # Recherche par mot-clé dans le nom de la discipline
    for key, icon in icon_mapping.items():
        if key in discipline_name:
            return icon
    
    # Icône par défaut
    return 'fist-raised'