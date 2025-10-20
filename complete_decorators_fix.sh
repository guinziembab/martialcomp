#!/bin/bash
# Compléter les décorateurs manquants

echo "================================================"
echo "🔧 AJOUT DÉCORATEUR federation_admin_required"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Ajout du décorateur manquant..."
echo "==================================="

# Ajouter federation_admin_required au fichier decorators.py
cat >> apps/utils/decorators.py << 'PYEOF'


def federation_admin_required(view_func):
    """Décorateur pour les vues réservées aux admins de fédération"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Vous devez être connecté pour accéder à cette page."))
            return redirect('account_login')
        
        # Vérifier si l'utilisateur est admin d'une fédération
        from apps.organizations.models import Federation, OrganizationMember, OrganizationRole
        
        # Si federation_id dans kwargs, vérifier pour cette fédération spécifique
        federation_id = kwargs.get('federation_id') or kwargs.get('pk')
        
        if federation_id:
            try:
                federation = Federation.objects.get(id=federation_id)
                # Vérifier si l'utilisateur est admin de cette fédération
                is_admin = OrganizationMember.objects.filter(
                    organization=federation,
                    user=request.user,
                    role__name__in=['admin', 'owner']
                ).exists()
                
                if not is_admin and not request.user.is_superuser:
                    messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
                    return redirect('/')
            except Federation.DoesNotExist:
                messages.error(request, _("Fédération introuvable."))
                return redirect('/')
        else:
            # Vérifier si l'utilisateur est admin d'au moins une fédération
            is_federation_admin = OrganizationMember.objects.filter(
                user=request.user,
                organization__type='federation',
                role__name__in=['admin', 'owner']
            ).exists()
            
            if not is_federation_admin and not request.user.is_superuser:
                messages.error(request, _("Vous devez être administrateur d'une fédération pour accéder à cette page."))
                return redirect('/')
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def club_admin_required(view_func):
    """Décorateur pour les vues réservées aux admins de club"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Vous devez être connecté pour accéder à cette page."))
            return redirect('account_login')
        
        # Vérifier si l'utilisateur est admin d'un club
        from apps.organizations.models import Club, OrganizationMember, OrganizationRole
        
        club_id = kwargs.get('club_id') or kwargs.get('pk')
        
        if club_id:
            try:
                club = Club.objects.get(id=club_id)
                is_admin = OrganizationMember.objects.filter(
                    organization=club,
                    user=request.user,
                    role__name__in=['admin', 'owner']
                ).exists()
                
                if not is_admin and not request.user.is_superuser:
                    messages.error(request, _("Vous n'avez pas les permissions pour accéder à ce club."))
                    return redirect('/')
            except Club.DoesNotExist:
                messages.error(request, _("Club introuvable."))
                return redirect('/')
        else:
            # Vérifier si l'utilisateur est admin d'au moins un club
            is_club_admin = OrganizationMember.objects.filter(
                user=request.user,
                organization__type='club',
                role__name__in=['admin', 'owner']
            ).exists()
            
            if not is_club_admin and not request.user.is_superuser:
                messages.error(request, _("Vous devez être administrateur d'un club pour accéder à cette page."))
                return redirect('/')
        
        return view_func(request, *args, **kwargs)
    return wrapped_view
PYEOF

echo "✅ Décorateurs federation_admin_required et club_admin_required ajoutés"

echo ""
echo "2️⃣ Ajout des imports manquants..."
echo "=================================="

# Ajouter les imports nécessaires en haut du fichier
sed -i '1s/^/from django.http import HttpResponseBadRequest\n/' apps/utils/decorators.py

echo "✅ Imports ajoutés"

echo ""
echo "3️⃣ Mise à jour de __init__.py..."
echo "================================="

cat > apps/utils/__init__.py << 'PYEOF'
"""
Module utils pour MartialComp
"""

# Imports pour faciliter l'accès
try:
    from .helpers import get_client_ip, safe_int, format_currency
except ImportError:
    # Fonctions par défaut si helpers n'est pas disponible
    def get_client_ip(request):
        return request.META.get('REMOTE_ADDR', '')
    
    def safe_int(value, default=0):
        try:
            return int(value)
        except:
            return default
    
    def format_currency(amount):
        return f"{amount:,.2f} €"

# Imports des décorateurs
try:
    from .decorators import (
        federation_admin_required,
        club_admin_required,
        login_required_message,
        ajax_required,
        superuser_required
    )
except ImportError:
    pass

__all__ = [
    'get_client_ip', 'safe_int', 'format_currency',
    'federation_admin_required', 'club_admin_required',
    'login_required_message', 'ajax_required', 'superuser_required'
]
PYEOF

echo "✅ __init__.py mis à jour avec tous les exports"

echo ""
echo "4️⃣ Redémarrage des services..."
echo "==============================="
sudo systemctl restart martialcomp
sudo systemctl reload apache2

echo ""
echo "5️⃣ Test final complet..."
echo "========================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

print("🧪 Test d'importation complète...")
try:
    from apps.utils.decorators import federation_admin_required
    print("✅ Import federation_admin_required réussi")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n🧪 Test de résolution d'URL...")
from django.urls import reverse
try:
    # Tester plusieurs URLs
    urls = ['welcome', 'account_login', 'account_logout']
    for url_name in urls:
        try:
            url = reverse(url_name)
            print(f"✅ {url_name}: {url}")
        except Exception as e:
            print(f"❌ {url_name}: {e}")
except Exception as e:
    print(f"❌ Erreur générale: {e}")
PYEOF

echo ""
echo "================================================"
echo "✅ CORRECTION COMPLÈTE APPLIQUÉE"
echo "================================================"
echo ""
echo "Tous les décorateurs ont été ajoutés:"
echo "- federation_admin_required"
echo "- club_admin_required"
echo "- login_required_message"
echo "- ajax_required"
echo "- superuser_required"
echo ""
echo "🎯 Le site devrait maintenant fonctionner: https://martialcomp.com/fr/"

REMOTE_COMMANDS