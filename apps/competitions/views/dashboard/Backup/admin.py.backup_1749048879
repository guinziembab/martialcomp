from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ...models import Federation, Club, Competition, Practitioner, UserProfile



@login_required
def admin_dashboard(request):
    """
    Dashboard pour les administrateurs système et administrateurs de fédération.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Si c'est un admin système
        if profile.role == 'admin' and request.user.is_staff:
            # Récupération des statistiques globales
            context = {
                'users_count': UserProfile.objects.count(),
                'clubs_count': Club.objects.count(),
                'competitions_count': Competition.objects.count(),
                'practitioners_count': Practitioner.objects.count(),
                'upcoming_competitions': Competition.objects.filter(
                    start_date__gte=timezone.now().date()
                ).order_by('start_date')[:5],
                'is_federation_admin': False,
                'is_system_admin': True
            }
        # Si c'est un admin de fédération
        elif profile.role == 'federation_admin':
            try:
                # Récupération de la fédération de l'utilisateur
                federation = Federation.objects.get(owner=request.user)
                
                # Récupérer toutes les disciplines associées à cette fédération
                disciplines = federation.disciplines.all()
                
                # Filtrage des données par fédération/disciplines
                clubs = Club.objects.filter(federation=federation)
                
                # Si le modèle Competition a un champ discipline, filtrer par disciplines
                if hasattr(Competition, 'discipline'):
                    competitions = Competition.objects.filter(discipline__in=disciplines)
                else:
                    # Sinon, filtrer par fédération si possible ou ne pas filtrer
                    competitions = Competition.objects.filter(federation=federation) if hasattr(Competition, 'federation') else Competition.objects.all()
                
                practitioners = Practitioner.objects.filter(club__in=clubs)
                
                context = {
                    'federation': federation,
                    'disciplines': disciplines,
                    'disciplines_count': disciplines.count(),
                    'clubs_count': clubs.count(),
                    'competitions_count': competitions.count(),
                    'practitioners_count': practitioners.count(),
                    'upcoming_competitions': competitions.filter(
                        start_date__gte=timezone.now().date(),
                        status='published'
                    ).order_by('start_date')[:5],
                    'is_federation_admin': True,
                    'is_system_admin': False
                }
            except Federation.DoesNotExist:
                messages.warning(request, _("Vous n'êtes associé à aucune fédération."))
                return redirect('onboarding:federation')
        else:
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('dashboard:spectator')
        
        return render(request, 'competitions/dashboard/admin.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')  # Changé ici - utilisation du nom URL racine