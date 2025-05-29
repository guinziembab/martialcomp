# competitions/context_processors.py
from django.conf import settings
from .models import Federation, Club, Practitioner, Competition, Judge


def federation_sidebar_context(request):
    """
    Context processor pour ajouter les données nécessaires au menu latéral de la fédération.
    """
    if not request.resolver_match or 'federation_id' not in request.resolver_match.kwargs:
        return {}
    
    try:
        federation_id = request.resolver_match.kwargs['federation_id']
        federation = Federation.objects.get(id=federation_id)
        
        # Compter les éléments liés à la fédération
        competition_count = Competition.objects.filter(
            discipline__in=federation.disciplines.all()
        ).count()
        
        club_count = Club.objects.filter(federation=federation).count()
        
        practitioner_count = Practitioner.objects.filter(
            club__federation=federation
        ).count()
        
        judge_count = Judge.objects.filter(
            practitioner__club__federation=federation
        ).count()
        
        return {
            'federation': federation,
            'competition_count': competition_count,
            'club_count': club_count,
            'practitioner_count': practitioner_count,
            'judge_count': judge_count,
        }
    except Federation.DoesNotExist:
        return {}
    except Exception as e:
        # Log the error in production
        return {}

# Vous pouvez aussi créer un mixin pour appliquer ce contexte à vos vues
class FederationContextMixin:
    """
    Mixin pour ajouter le contexte de la fédération aux vues.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'federation'):
            federation = self.federation
        elif 'federation_id' in self.kwargs:
            try:
                federation = Federation.objects.get(id=self.kwargs['federation_id'])
            except Federation.DoesNotExist:
                return context
        else:
            return context
        
        # Ajouter les compteurs
        context.update({
            'federation': federation,
            'competition_count': Competition.objects.filter(
                discipline__in=federation.disciplines.all()
            ).count(),
            'club_count': Club.objects.filter(federation=federation).count(),
            'practitioner_count': Practitioner.objects.filter(
                club__federation=federation
            ).count(),
            'judge_count': Judge.objects.filter(
                practitioner__club__federation=federation
            ).count(),
        })
        
        return context