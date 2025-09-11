"""
URLs competitions - Version finale avec tous les dashboards
"""
from django.urls import path, include
from django.shortcuts import render
from competitions.views import pages, auth
from competitions.views.dashboard_router import (
    dashboard_router,
    club_dashboard_view,
    coach_dashboard_view,
    participant_dashboard_view,
    federation_dashboard_view,
    admin_dashboard_view,
    judge_dashboard_view,
    referee_dashboard_view,
    combat_dashboard_view,
    manager_dashboard_view,
    spectator_dashboard_view
)

app_name = "competitions"

# Vue temporaire pour les sections non implémentées
def temp_section_view(request, section="Section"):
    context = {
        "user": request.user,
        "page_title": section,
        "section_info": f"Cette section ({section}) est en développement."
    }
    return render(request, "competitions/dashboard/temp_section.html", context)

urlpatterns = [
    # Page d'accueil
    path("", pages.welcome, name="welcome"),
    
    # Dashboard principal avec routage intelligent
    path("dashboard/", dashboard_router, name="dashboard"),
    
    # Dashboards spécifiques - utilisent templates du dev
    path("dashboard/club/", club_dashboard_view, name="dashboard_club"),
    path("dashboard/federation/", federation_dashboard_view, name="dashboard_federation"),
    path("dashboard/admin/", admin_dashboard_view, name="dashboard_admin"),
    path("dashboard/coach/", coach_dashboard_view, name="dashboard_coach"),
    path("dashboard/participant/", participant_dashboard_view, name="dashboard_participant"),
    path("dashboard/judge/", judge_dashboard_view, name="dashboard_judge"),
    path("dashboard/referee/", referee_dashboard_view, name="dashboard_referee"),
    path("dashboard/combat/", combat_dashboard_view, name="dashboard_combat"),
    path("dashboard/manager/", manager_dashboard_view, name="dashboard_manager"),
    path("dashboard/spectator/", spectator_dashboard_view, name="dashboard_spectator"),
    
    # === SECTIONS CLUB ===
    path("club/practitioners/", lambda r: temp_section_view(r, "Pratiquants"), name="club_practitioners"),
    path("club/competitions/", lambda r: temp_section_view(r, "Compétitions Club"), name="club_competitions"),
    path("club/registrations/", lambda r: temp_section_view(r, "Inscriptions"), name="club_registrations"),
    path("club/judges/", lambda r: temp_section_view(r, "Juges"), name="club_judges"),
    path("club/scoring/", lambda r: temp_section_view(r, "Notation"), name="club_scoring"),
    path("club/roles/", lambda r: temp_section_view(r, "Gestion des rôles"), name="club_roles"),
    
    # === COMPETITIONS ===
    path("competitions/", lambda r: temp_section_view(r, "Compétitions"), name="competitions_list"),
    path("competitions/create/", lambda r: temp_section_view(r, "Nouvelle Compétition"), name="competitions_create"),
    path("competitions/<int:pk>/", lambda r, pk: temp_section_view(r, f"Compétition #{pk}"), name="competitions_detail"),
    
    # === EVENTS ===
    path("events/", lambda r: temp_section_view(r, "Événements"), name="events_list"),
    path("events/planning/", lambda r: temp_section_view(r, "Planning"), name="events_planning"),
    path("events/polls/", lambda r: temp_section_view(r, "Sondages"), name="events_polls"),
    
    # === GRADES ===
    path("grades/club/", lambda r: temp_section_view(r, "Grades"), name="grades_club"),
    path("grades/management/", lambda r: temp_section_view(r, "Gestion Grades"), name="grades_management"),
    
    # === FINANCES ===
    path("finances/", lambda r: temp_section_view(r, "Finances"), name="finances_dashboard"),
    path("finances/payments/", lambda r: temp_section_view(r, "Paiements"), name="finances_payments"),
    
    # === SHOP ===
    path("shop/club/", lambda r: temp_section_view(r, "Boutique"), name="shop_club"),
    path("shop/dashboard/", lambda r: temp_section_view(r, "Dashboard Boutique"), name="shop_dashboard"),
    path("shop/products/create/", lambda r: temp_section_view(r, "Créer Produit"), name="shop_products_create"),
    
    # === QR CODE ===
    path("qr/scan/", lambda r: temp_section_view(r, "Scanner QR"), name="qr_scan"),
    path("qr/history/", lambda r: temp_section_view(r, "Historique QR"), name="qr_history"),
    
    # Auth
    path("auth/", include([
        path("login/", auth.custom_login, name="custom_login"),
        path("logout/", auth.custom_logout, name="custom_logout"),
        path("signup/", auth.custom_signup, name="signup"),
    ])),
]
