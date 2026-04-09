#!/bin/bash
# =============================================================================
# DIAGNOSTIC PRODUCTION - BUG AIKIDO
# Date: 2025-11-26
# =============================================================================
#
# Ce script vérifie EXACTEMENT ce qui se passe sur le serveur de production
# pour identifier la source du bug AIKIDO.
#
# =============================================================================

echo "=== DIAGNOSTIC PRODUCTION - BUG AIKIDO ==="
echo "Date: $(date)"
echo ""

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
TEMPLATE_FILE="$PRODUCTION_PATH/apps/competitions/templates/competitions/onboarding/club_creation.html"

echo "=== 1. VÉRIFIER LE TEMPLATE CLUB_CREATION.HTML EN PRODUCTION ==="
echo ""
echo "Recherche de 'checked' dans le template :"
ssh martialcomp-production "grep -n 'checked' $TEMPLATE_FILE 2>/dev/null || echo 'Aucun checked trouvé'"
echo ""
echo "Affichage des lignes 550-570 (section disciplines) :"
ssh martialcomp-production "sed -n '550,570p' $TEMPLATE_FILE 2>/dev/null"
echo ""

echo "=== 2. VÉRIFIER LES CLUBS RÉCENTS EN BASE ==="
echo ""
cat << 'DJANGO_CMD' | ssh martialcomp-production "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py shell"
from apps.competitions.models import Club, Discipline

# Derniers clubs créés
print("=== DERNIERS CLUBS CRÉÉS ===")
clubs = Club.objects.order_by('-created_at')[:5]
for c in clubs:
    print(f"\nClub: {c.name} (ID={c.id})")
    print(f"  Owner: {c.owner}")
    print(f"  Created: {c.created_at}")
    print(f"  main_discipline: {c.main_discipline}")
    print(f"  disciplines: {list(c.disciplines.values_list('name', flat=True))}")
    if c.organization:
        print(f"  org.disciplines: {list(c.organization.disciplines.values_list('name', flat=True))}")

# Chercher AIKIDO
print("\n=== DISCIPLINE AIKIDO ===")
aikido = Discipline.objects.filter(name__icontains='aikido').first()
if aikido:
    print(f"Discipline AIKIDO: ID={aikido.id}, name={aikido.name}")

    # Clubs avec AIKIDO récemment créés
    from datetime import datetime, timedelta
    from django.utils import timezone
    recent = timezone.now() - timedelta(days=7)
    recent_clubs_aikido = Club.objects.filter(
        disciplines=aikido,
        created_at__gte=recent
    ).order_by('-created_at')

    print(f"\nClubs avec AIKIDO créés ces 7 derniers jours: {recent_clubs_aikido.count()}")
    for c in recent_clubs_aikido[:5]:
        print(f"  - {c.name} (owner: {c.owner}, {c.created_at})")

exit()
DJANGO_CMD

echo ""
echo "=== 3. VÉRIFIER LE CODE SOURCE DE LA VUE ONBOARDING ==="
echo ""
echo "Lignes 55-75 de la vue club.py (gestion des disciplines) :"
ssh martialcomp-production "sed -n '55,75p' $PRODUCTION_PATH/apps/competitions/views/onboarding/club.py 2>/dev/null"
echo ""

echo "=== 4. VÉRIFIER LE LOG D'ERREURS RÉCENT ==="
echo ""
ssh martialcomp-production "tail -50 /var/www/vhosts/martialcomp.com/logs/gunicorn/error.log 2>/dev/null | grep -i 'discipline\|aikido' || echo 'Pas de mention de discipline/aikido dans les derniers logs'"
echo ""

echo "=== FIN DU DIAGNOSTIC ==="
echo ""
echo "COMMANDES À EXÉCUTER MANUELLEMENT SI LE SCRIPT NE FONCTIONNE PAS :"
echo "================================================================="
echo ""
echo "1. Vérifier le template :"
echo "   ssh martialcomp-production \"grep -n 'checked' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/onboarding/club_creation.html\""
echo ""
echo "2. Vérifier les clubs en base :"
echo "   ssh martialcomp-production"
echo "   cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "   /var/www/vhosts/martialcomp.com/venv/bin/python manage.py shell"
echo "   >>> from apps.competitions.models import Club"
echo "   >>> c = Club.objects.order_by('-created_at').first()"
echo "   >>> print(c.name, list(c.disciplines.values_list('name', flat=True)))"
echo ""
