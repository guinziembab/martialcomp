"""
URLs pour le module de gestion de club.
Ce fichier définit tous les chemins d'URL pour les fonctionnalités liées aux clubs.
"""
from django.urls import path
from django.contrib.auth.decorators import login_required

# Imports des vues du module club
# Vues des pratiquants
from competitions.views.club import (
    practitioners_list, practitioner_form, practitioner_detail, practitioner_delete,
    create_user_for_practitioner, link_user_to_practitioner
)

# Import des vues d'entraînement
from competitions.views.club.training import (
    training_sessions, attendance_list, create_training_session
)

# Vues des profils utilisateurs
from competitions.views.club.profiles import (
    user_profile, practitioner_profile, update_practitioner_profile
)

# Vues des qualifications
from competitions.views.club.qualifications import qualification_form

# Vues des inscriptions
from competitions.views.club.registrations import (
    registrations_list, register_practitioner, available_competitions,
    register_multiple_practitioners, competition_registration_form,
    club_bulk_registration, cancel_registration
)

# Vue d'import/export
from competitions.views.club.import_export import import_export_data

# Import de la vue dashboard du club
from competitions.views.dashboard.club import club_dashboard

# Import des vues principales du club
from competitions.views.club import (
    club_competitions, 
    club_competition_detail,
    judges_list, 
    judge_add,
    judge_assignments,
    #technical_scoring,  # Commenté à cause de l'erreur BACH HAC
    competition_scoring, 
    performance_detail,
    create_custom_category,
    club_settings
)

# Import du hotfix pour technical_scoring
from competitions.views.club.technical_scoring_hotfix import technical_scoring_hotfix

# Import des modules résultats
from competitions.views.club import results

# Import du module de paramètres du club
from competitions.views.club import settings

# Import des vues de gestion des rôles
from competitions.views.roles import (
    manage_roles, 
    create_role, 
    edit_role, 
    delete_role, 
    assign_role, 
    revoke_role
)

app_name = 'club'

urlpatterns = [
    # Dashboard du club
    path('dashboard/', login_required(club_dashboard), name='dashboard'),
    
    # =========================================================
    # URLs pour les pratiquants
    # =========================================================
    # Liste et ajout de pratiquants
    path('practitioners/', login_required(practitioners_list), name='practitioners'),
    path('practitioners/add/', login_required(practitioner_form), name='practitioner_add'),
    
    # Détails, modification et suppression de pratiquants
    path('practitioners/<int:pk>/', login_required(practitioner_detail), name='practitioner_detail'),
    path('practitioners/<int:practitioner_id>/edit/', login_required(practitioner_form), name='practitioner_edit'),
    path('practitioners/delete/<int:practitioner_id>/', login_required(practitioner_delete), name='practitioner_delete'),
    
    # Gestion des utilisateurs associés aux pratiquants
    path('practitioners/create-user/<int:practitioner_id>/', 
         login_required(create_user_for_practitioner), 
         name='create_user_for_practitioner'),
    path('practitioners/link-user/<int:practitioner_id>/', 
         login_required(link_user_to_practitioner), 
         name='link_user_to_practitioner'),
    
    # Profil du pratiquant connecté
    path('practitioners/profile/', login_required(practitioner_profile), name='practitioner_profile'),
    path('practitioners/profile/edit/', login_required(update_practitioner_profile), name='edit_practitioner_profile'),
    
    # =========================================================
    # URLs pour les qualifications (juges/arbitres)
    # =========================================================
    path('practitioners/<int:practitioner_id>/qualification/add/', 
         login_required(qualification_form), 
         name='qualification_add'),
    path('practitioners/<int:practitioner_id>/qualification/<int:qualification_id>/edit/', 
         login_required(qualification_form), 
         name='qualification_edit'),
    
    # URLs pour les juges
    path('judges/', login_required(judges_list), name='judges_list'),
    # Gestion des affectations de juges aux compétitions
    path('judges/assignments/', login_required(judge_assignments), name='judge_assignments'),
    path('judges/add/', login_required(judge_add), name='judge_add'),
    
    # URLs pour la notation technique - Utilisation du hotfix
    path('technical-scoring/', login_required(technical_scoring_hotfix), name='technical_scoring'),
    path('technical-scoring/competition/<int:competition_id>/', login_required(competition_scoring), name='competition_scoring'),
    path('technical-scoring/performance/<int:performance_id>/', login_required(performance_detail), name='performance_detail'),
    
    # Autres URLs de club pour les résultats
    path('results/', login_required(results.club_competition_results), name='results'),
    path('results/<int:competition_id>/', login_required(results.competition_result_detail), name='result_detail'),
    
    # =========================================================
    # URLs pour les inscriptions aux compétitions
    # =========================================================
    # Liste des compétitions disponibles et inscriptions
    path('competitions/', login_required(club_competitions), name='club_competitions'),
    path('competitions/<int:competition_id>/', login_required(club_competition_detail), name='club_competition_detail'),
    
    path('competitions/available/', login_required(available_competitions), name='available_competitions'),
    path('registrations/', login_required(registrations_list), name='registrations_list'),
    
    # Inscription individuelle de pratiquants
    path('competitions/<int:competition_id>/register/', 
         login_required(register_practitioner), 
         name='register_practitioner'),  # Sélection d'un pratiquant
    path('competitions/<int:competition_id>/register/<int:practitioner_id>/', 
         login_required(register_practitioner), 
         name='register_practitioner_with_id'),  # Avec pratiquant spécifié
    
    # Inscription multiple et en masse
    path('competitions/<int:competition_id>/register-multiple/', 
         login_required(register_multiple_practitioners), 
         name='register_multiple_practitioners'),
    path('competitions/<int:competition_id>/register-form/', 
         login_required(competition_registration_form), 
         name='competition_registration_form'),
    path('bulk-registration/', 
         login_required(club_bulk_registration), 
         name='bulk_registration'),
    
    # Annulation d'inscription
    path('registrations/<int:registration_id>/cancel/',
         login_required(cancel_registration),
         name='cancel_registration'),
    
    # =========================================================
    # Import/Export de données
    # =========================================================
    path('import-export/', 
         login_required(import_export_data), 
         name='import_export'),
    
    # =========================================================
    # Profil utilisateur
    # =========================================================
    path('profile/', login_required(user_profile), name='user_profile'),
    
    # =========================================================
    # Settings
    # =========================================================
    path('settings/<int:club_id>/', login_required(club_settings), name='settings'),
    path('categories/create/', login_required(create_custom_category), name='create_custom_category'),
    
    # =========================================================
    # URLs pour les paramètres du club
    # =========================================================
    path('disciplines/', login_required(settings.manage_club_disciplines), name='manage_disciplines'),
    path('join-federation/', login_required(settings.join_federation), name='join_federation'),
    path('requests/', login_required(settings.manage_requests), name='manage_requests'),
    
    # =========================================================
    # URLs de gestion des rôles et permissions
    # =========================================================
    path('roles/', login_required(manage_roles), name='manage_roles'),
    path('roles/create/', login_required(create_role), name='create_role'),
    path('roles/<int:role_id>/edit/', login_required(edit_role), name='edit_role'),
    path('roles/<int:role_id>/delete/', login_required(delete_role), name='delete_role'),
    path('roles/assign/', login_required(assign_role), name='assign_role'),
    path('roles/revoke/<int:user_role_id>/', login_required(revoke_role), name='revoke_role'),
    
    # =========================================================
    # URLs pour les entraînements
    # =========================================================
    path('training/sessions/', login_required(training_sessions), name='training_sessions'),
    path('training/sessions/create/', login_required(create_training_session), name='create_training_session'),
    path('training/sessions/<int:session_id>/attendance/', login_required(attendance_list), name='attendance_list'),
]