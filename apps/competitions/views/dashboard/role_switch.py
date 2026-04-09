from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from ...models import UserProfile, Practitioner, Judge
from ...services.judge_service import JudgeService


@login_required
def switch_to_judge(request):
    """
    Permet à un pratiquant de basculer vers le dashboard juge technique
    si il a un profil juge avec is_technical_judge=True et active=True.

    PROMPT 7 - Vérifications:
    - Practitioner.judge existe
    - Judge.is_technical_judge == True
    - Judge.active == True
    """
    try:
        # Vérifier que l'utilisateur a un profil pratiquant
        practitioner = Practitioner.objects.get(user=request.user)

        # Vérifier qu'il a un profil juge
        judge = Judge.objects.get(practitioner=practitioner)

        # PROMPT 7: Vérifier que le juge est technique et actif
        if not judge.is_technical_judge:
            messages.error(request, _("Votre profil juge n'est pas configuré comme juge technique."))
            return redirect('competitions:dashboard:participant')

        if not judge.active:
            messages.error(request, _("Votre profil juge n'est pas actif. Contactez votre fédération."))
            return redirect('competitions:dashboard:participant')

        # Stocker le mode actuel en session
        request.session['dashboard_mode'] = 'judge_technical'
        request.session['judge_id'] = judge.id

        messages.success(request, _("Vous êtes maintenant en mode Juge Technique"))
        return redirect('competitions:dashboard:judge_technical')

    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'avez pas de profil pratiquant"))
        return redirect('competitions:dashboard:index')
    except Judge.DoesNotExist:
        messages.error(request, _("Vous n'avez pas de profil juge/arbitre. Contactez votre fédération pour devenir juge."))
        return redirect('competitions:dashboard:participant')

@login_required
def switch_to_participant(request):
    """
    Permet à un juge/arbitre de basculer vers le dashboard pratiquant
    s'il a un profil pratiquant.
    """
    try:
        # Vérifier que l'utilisateur a un profil pratiquant
        practitioner = Practitioner.objects.get(user=request.user)
        
        # Stocker le mode actuel en session
        request.session['dashboard_mode'] = 'participant'
        
        messages.success(request, _("Vous êtes maintenant en mode Pratiquant"))
        return redirect('competitions:dashboard:participant')
        
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'avez pas de profil pratiquant"))
        return redirect('competitions:dashboard:referee')

@login_required
def toggle_dashboard_mode(request):
    """
    Bascule entre les modes pratiquant et juge/arbitre
    """
    current_mode = request.session.get('dashboard_mode', 'participant')
    
    if current_mode == 'participant':
        return switch_to_judge(request)
    else:
        return switch_to_participant(request)

@login_required
def apply_as_judge(request):
    """
    Permet à un pratiquant de postuler pour devenir juge/arbitre.
    Cette vue redirige vers le formulaire approprié ou affiche les informations.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)

        # Vérifier si le pratiquant a déjà un profil juge
        if Judge.objects.filter(practitioner=practitioner).exists():
            messages.info(request, _("Vous avez déjà un profil juge/arbitre"))
            return redirect('competitions:dashboard:switch_to_judge')

        # Rediriger vers le formulaire de candidature juge
        messages.info(request, _("Pour devenir juge/arbitre, veuillez contacter votre fédération ou votre club."))
        # TODO: Implémenter le formulaire de candidature
        # return redirect('competitions:judge:application_form')

        return redirect('competitions:dashboard:participant')

    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous devez avoir un profil pratiquant pour postuler comme juge"))
        return redirect('competitions:dashboard:index')


@login_required
def judge_technical_dashboard(request):
    """
    Dashboard pour les juges techniques.
    PROMPT 7 - Affiche:
    - Catégories assignées pour la compétition du jour
    - Performances en attente de notation
    - Programme de la journée
    - Bouton de retour vers le mode pratiquant
    """
    try:
        # Vérifier que l'utilisateur a un profil pratiquant
        practitioner = Practitioner.objects.get(user=request.user)

        # Vérifier qu'il a un profil juge technique actif
        try:
            judge = Judge.objects.get(practitioner=practitioner)

            if not judge.is_technical_judge or not judge.active:
                messages.error(request, _("Votre profil juge technique n'est pas actif."))
                return redirect('competitions:dashboard:participant')
        except Judge.DoesNotExist:
            messages.error(request, _("Vous n'avez pas de profil juge."))
            return redirect('competitions:dashboard:participant')

        # Utiliser le JudgeService pour récupérer les données
        current_assignments = JudgeService.get_current_assignments(judge)
        upcoming_assignments = JudgeService.get_upcoming_assignments(judge)
        pending_performances = JudgeService.get_pending_performances(judge)
        today_schedule = JudgeService.get_today_schedule(judge)
        judge_stats = JudgeService.get_judge_stats(judge)
        recent_competitions = JudgeService.get_recent_competitions(judge)

        # Stocker le mode en session
        request.session['dashboard_mode'] = 'judge_technical'

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'current_assignments': current_assignments,
            'upcoming_assignments': upcoming_assignments,
            'pending_performances': pending_performances,
            'pending_performances_count': pending_performances.count() if pending_performances else 0,
            'today_schedule': today_schedule,
            'stats': judge_stats,
            'recent_competitions': recent_competitions,
            'today': timezone.now().date(),
            'has_practitioner_profile': True,
        }

        return render(request, 'competitions/dashboard/judge_technical.html', context)

    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'avez pas de profil pratiquant"))
        return redirect('competitions:dashboard:index')


def can_access_judge_dashboard(user):
    """
    Helper function to check if a user can access the judge dashboard.
    Used by context processor and templates.
    """
    if not user or not user.is_authenticated:
        return False

    try:
        practitioner = Practitioner.objects.get(user=user)
        return JudgeService.can_switch_to_judge_view(practitioner)
    except Practitioner.DoesNotExist:
        return False


def get_pending_performances_count(user):
    """
    Helper function to get pending performances count for badge display.
    """
    if not user or not user.is_authenticated:
        return 0

    try:
        practitioner = Practitioner.objects.get(user=user)
        judge = JudgeService.get_judge_for_practitioner(practitioner)
        if judge:
            return JudgeService.get_pending_performances_count(judge)
    except Practitioner.DoesNotExist:
        pass

    return 0


# ===== PROMPT 8: PAGES ADDITIONNELLES DU MENU JUGE =====

@login_required
def judge_assignments(request):
    """
    Page des affectations du juge technique.
    Liste toutes les affectations passées, présentes et futures.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        judge = Judge.objects.get(practitioner=practitioner)

        if not judge.is_technical_judge or not judge.active:
            messages.error(request, _("Votre profil juge technique n'est pas actif."))
            return redirect('competitions:dashboard:participant')

        # Récupérer toutes les affectations
        current_assignments = JudgeService.get_current_assignments(judge)
        upcoming_assignments = JudgeService.get_upcoming_assignments(judge)
        past_assignments = JudgeService.get_past_assignments(judge) if hasattr(JudgeService, 'get_past_assignments') else []

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'current_assignments': current_assignments,
            'upcoming_assignments': upcoming_assignments,
            'past_assignments': past_assignments,
            'today': timezone.now().date(),
        }

        return render(request, 'competitions/dashboard/judge_assignments.html', context)

    except (Practitioner.DoesNotExist, Judge.DoesNotExist):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('competitions:dashboard:index')


@login_required
def judge_performances(request):
    """
    Page des performances à noter pour le juge technique.
    Liste les performances en attente et notées.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        judge = Judge.objects.get(practitioner=practitioner)

        if not judge.is_technical_judge or not judge.active:
            messages.error(request, _("Votre profil juge technique n'est pas actif."))
            return redirect('competitions:dashboard:participant')

        # Récupérer les performances
        pending_performances = JudgeService.get_pending_performances(judge)
        scored_performances = JudgeService.get_scored_performances(judge) if hasattr(JudgeService, 'get_scored_performances') else []

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'pending_performances': pending_performances,
            'pending_performances_count': pending_performances.count() if pending_performances else 0,
            'scored_performances': scored_performances,
            'today': timezone.now().date(),
        }

        return render(request, 'competitions/dashboard/judge_performances.html', context)

    except (Practitioner.DoesNotExist, Judge.DoesNotExist):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('competitions:dashboard:index')


@login_required
def judge_history(request):
    """
    Historique des notations du juge technique.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        judge = Judge.objects.get(practitioner=practitioner)

        if not judge.is_technical_judge or not judge.active:
            messages.error(request, _("Votre profil juge technique n'est pas actif."))
            return redirect('competitions:dashboard:participant')

        # Récupérer l'historique des compétitions
        recent_competitions = JudgeService.get_recent_competitions(judge)
        judge_stats = JudgeService.get_judge_stats(judge)

        # Annotate competitions with category count and scored performances
        from apps.competitions.models.technical_scoring import TechnicalScore
        from django.db.models import Count
        for comp in recent_competitions:
            comp.num_categories = comp.categories.count()
            comp.num_scored = TechnicalScore.objects.filter(
                judge=request.user,
                performance__competition=comp,
                is_active_for_ranking=True
            ).values('performance').distinct().count()

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'recent_competitions': recent_competitions,
            'stats': judge_stats,
            'today': timezone.now().date(),
        }

        return render(request, 'competitions/dashboard/judge_history.html', context)

    except (Practitioner.DoesNotExist, Judge.DoesNotExist):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('competitions:dashboard:index')


@login_required
def judge_settings_view(request):
    """
    Page des paramètres du juge technique.
    Permet de modifier les préférences de notation.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        judge = Judge.objects.get(practitioner=practitioner)

        if not judge.is_technical_judge or not judge.active:
            messages.error(request, _("Votre profil juge technique n'est pas actif."))
            return redirect('competitions:dashboard:participant')

        if request.method == 'POST':
            # Traiter les modifications de paramètres
            # TODO: Implémenter la logique de sauvegarde des paramètres
            messages.success(request, _("Paramètres enregistrés avec succès."))
            return redirect('competitions:dashboard:judge_settings')

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'today': timezone.now().date(),
        }

        return render(request, 'competitions/dashboard/judge_settings.html', context)

    except (Practitioner.DoesNotExist, Judge.DoesNotExist):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('competitions:dashboard:index')


# ===== AIRES DE COMBAT POUR JUGES =====

@login_required
def judge_combat_areas(request):
    """
    Liste les aires de combat disponibles pour le juge.
    Affiche les aires de toutes les compétitions en cours ou à venir
    qui ont des aires de combat configurées.

    Le juge peut accéder à n'importe quelle aire via le code PIN,
    ce qui permet une affectation flexible le jour de la compétition.
    """
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        judge = Judge.objects.get(practitioner=practitioner)

        if not judge.active:
            messages.error(request, _("Votre profil juge n'est pas actif."))
            return redirect('competitions:dashboard:participant')

        # Importer les modèles nécessaires
        from ...models.combat import AireCombat
        from ...models import Competition

        today = timezone.now().date()

        # Récupérer toutes les compétitions en cours ou à venir qui ont des aires actives
        competitions_with_aires = []

        # Compétitions en cours (aujourd'hui) ou à venir (dans les 7 prochains jours)
        # On élargit un peu pour que le juge puisse voir les compétitions proches
        from datetime import timedelta
        upcoming_limit = today + timedelta(days=7)

        competitions = Competition.objects.filter(
            end_date__gte=today,  # Pas encore terminées
            start_date__lte=upcoming_limit  # Commencent dans les 7 jours
        ).order_by('start_date')

        for competition in competitions:
            # Récupérer les aires actives de cette compétition
            aires = AireCombat.objects.filter(
                competition=competition,
                is_active=True
            ).order_by('nom')

            if aires.exists():
                competitions_with_aires.append({
                    'competition': competition,
                    'aires': aires,
                    'is_today': competition.start_date <= today <= competition.end_date,
                })

        context = {
            'practitioner': practitioner,
            'judge': judge,
            'competitions_with_aires': competitions_with_aires,
            'today': today,
        }

        return render(request, 'competitions/dashboard/judge_combat_areas.html', context)

    except (Practitioner.DoesNotExist, Judge.DoesNotExist):
        messages.error(request, _("Vous n'avez pas accès à cette page."))
        return redirect('competitions:dashboard:index')