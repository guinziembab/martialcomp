"""
Fonctions utilitaires pour le module club.
"""
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from competitions.utils.decorators import club_required
from competitions.models import Practitioner, Club, CategoryGrade  # Ajout de CategoryGrade

# Importation de notre helper de permission personnalisé
from competitions.utils.permission_helpers import manual_permission_check, get_user_club as get_user_club_from_helper

import uuid
import logging

logger = logging.getLogger(__name__)

# Nous gardons cette définition pour maintenir la rétrocompatibilité
def get_user_club(request):
    """
    Récupère le club associé à l'utilisateur.
    Cette fonction est maintenant importée depuis permission_helpers.
    """
    return get_user_club_from_helper(request)

def filter_practitioners_by_age_group(practitioners_queryset, age_group):
    """
    Filtre les pratiquants par groupe d'âge.
    
    Args:
        practitioners_queryset: QuerySet des pratiquants
        age_group: Chaîne de caractères indiquant le groupe d'âge
    
    Returns:
        QuerySet filtré
    """
    today = timezone.now().date()
    
    if age_group == 'children':
        # Enfants (6-11 ans)
        max_birth_date = today.replace(year=today.year - 6)
        min_birth_date = today.replace(year=today.year - 11, day=31, month=12)
        return practitioners_queryset.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
    elif age_group == 'teenagers':
        # Adolescents (12-17 ans)
        max_birth_date = today.replace(year=today.year - 12)
        min_birth_date = today.replace(year=today.year - 17, day=31, month=12)
        return practitioners_queryset.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
    elif age_group == 'adults':
        # Adultes (18-39 ans)
        max_birth_date = today.replace(year=today.year - 18)
        min_birth_date = today.replace(year=today.year - 39, day=31, month=12)
        return practitioners_queryset.filter(birth_date__gte=min_birth_date, birth_date__lte=max_birth_date)
    elif age_group == 'seniors':
        # Seniors (40+ ans)
        min_birth_date = today.replace(year=today.year - 40)
        return practitioners_queryset.filter(birth_date__lte=min_birth_date)
    
    return practitioners_queryset

def generate_username_from_name(first_name, last_name):
    """
    Génère un nom d'utilisateur unique basé sur le prénom et le nom.
    
    Args:
        first_name: Prénom
        last_name: Nom
    
    Returns:
        Nom d'utilisateur unique
    """
    from django.contrib.auth.models import User
    
    # Normaliser et nettoyer les noms
    first_name = first_name.lower().strip()
    last_name = last_name.lower().strip()
    
    # Supprimer les accents et caractères spéciaux
    import unicodedata
    first_name = unicodedata.normalize('NFKD', first_name).encode('ASCII', 'ignore').decode('utf-8')
    last_name = unicodedata.normalize('NFKD', last_name).encode('ASCII', 'ignore').decode('utf-8')
    
    # Remplacer les espaces par des tirets
    first_name = first_name.replace(' ', '-')
    last_name = last_name.replace(' ', '-')
    
    # Générer le nom d'utilisateur
    base_username = f"{first_name}.{last_name}"
    username = base_username
    counter = 1
    
    # Vérifier l'unicité
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def generate_password():
    """
    Génère un mot de passe temporaire aléatoire.
    
    Returns:
        Mot de passe temporaire
    """
    return str(uuid.uuid4())[:8]


@login_required
def club_settings(request, club_id):
    """Vue pour mettre à jour les paramètres du club"""
    # Vérifier manuellement les permissions
    club = get_object_or_404(Club, id=club_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce club
    if club.owner != request.user:
        messages.error(request, _("Vous n'avez pas la permission de modifier ce club."))
        return redirect('competitions:dashboard:club')
    
    if request.method == 'POST':
        try:
            # Mettre à jour les catégories acceptées
            club.accepts_children = 'accepts_children' in request.POST
            club.accepts_teenagers = 'accepts_teenagers' in request.POST
            club.accepts_adults = 'accepts_adults' in request.POST
            club.accepts_seniors = 'accepts_seniors' in request.POST
            
            club.save()
            messages.success(request, _("Les paramètres du club ont été mis à jour avec succès."))
            return redirect('competitions:dashboard:club')
        except Exception as e:
            messages.error(request, _("Une erreur est survenue lors de la mise à jour des paramètres : {}").format(str(e)))
            return redirect('competitions:dashboard:club')
    
    # Si GET, rediriger vers le dashboard
    return redirect('competitions:dashboard:club')


@login_required
@club_required
def create_custom_category(request):
    """Vue pour créer une catégorie personnalisée pour le club"""
    # Récupérer le club de l'utilisateur
    club = request.club or Club.objects.filter(owner=request.user).first()
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard:club')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_type = request.POST.get('type')
            
            if not name or not category_type:
                messages.error(request, _("Le nom et le type de catégorie sont requis."))
                return redirect('competitions:dashboard:club')
            
            # Créer la catégorie selon le type
            if category_type == 'age':
                # Créer une catégorie d'âge
                category = CategoryGrade.objects.create(
                    nom=name,
                    description=f"Catégorie d'âge personnalisée pour {club.name}",
                    is_active=True
                )
                
                # Associer la catégorie au club si possible
                # club.categories.add(category)  # À adapter selon votre modèle
                
                messages.success(request, _("Catégorie d'âge créée avec succès."))
            
            elif category_type == 'grade':
                # Créer une catégorie de grade
                category = CategoryGrade.objects.create(
                    nom=name,
                    description=f"Catégorie de grade personnalisée pour {club.name}",
                    is_active=True
                )
                
                # Associer la catégorie au club si possible
                # club.categories.add(category)  # À adapter selon votre modèle
                
                messages.success(request, _("Catégorie de grade créée avec succès."))
            
            else:
                messages.error(request, _("Type de catégorie non valide."))
            
            return redirect('competitions:dashboard:club')
            
        except Exception as e:
            messages.error(request, _("Une erreur est survenue lors de la création de la catégorie : {}").format(str(e)))
            return redirect('competitions:dashboard:club')
    
    # Si GET, rediriger vers le dashboard
    return redirect('competitions:dashboard:club')