#!/bin/bash
# Script de correction pour l'onboarding des clubs - Problème d'assignation de discipline par défaut
# Date: 2025-11-25
# Problème: La discipline "Aïkido" est assignée par défaut lors de la création d'un club

echo "=== CORRECTION ONBOARDING DISCIPLINE - PRODUCTION ==="
echo "Ce script corrige le problème d'assignation automatique de discipline Aïkido"
echo ""

# 1. Se connecter au serveur
# ssh root@martialcomp.com

# 2. Aller dans le répertoire
cd /var/www/vhosts/martialcomp.com/httpdocs

# 3. Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# 4. Backup des fichiers
echo "=== Backup des fichiers ==="
cp apps/competitions/views/onboarding/club.py apps/competitions/views/onboarding/club.py.backup_$(date +%Y%m%d_%H%M%S)
cp apps/competitions/forms/onboarding.py apps/competitions/forms/onboarding.py.backup_$(date +%Y%m%d_%H%M%S)

# 5. Vérifier le code actuel sur production
echo "=== Vérification du code actuel ==="
echo "--- Vue club.py (lignes 55-75) ---"
sed -n '55,75p' apps/competitions/views/onboarding/club.py

echo ""
echo "--- Recherche de 'first()' dans le code ---"
grep -n "first()" apps/competitions/views/onboarding/club.py
grep -n "Discipline.objects" apps/competitions/views/onboarding/club.py

echo ""
echo "=== FIN DE LA VÉRIFICATION ==="
echo "Si le code contient une assignation par défaut de discipline, exécutez les commandes suivantes manuellement:"
echo ""
echo "# Pour corriger la vue club.py:"
echo "nano apps/competitions/views/onboarding/club.py"
echo ""
echo "# Cherchez et corrigez les lignes qui assignent une discipline par défaut"
echo "# La vue devrait ressembler à:"
cat << 'EXPECTED_CODE'

# Dans handle_club_creation, après club.save():
# Gestion des disciplines sélectionnées (checkboxes multiples)
discipline_ids = request.POST.getlist('disciplines')
if discipline_ids:
    selected_disciplines = Discipline.objects.filter(id__in=discipline_ids)
    # Ajouter toutes les disciplines sélectionnées
    club.disciplines.set(selected_disciplines)
    # Définir la première comme discipline principale
    first_discipline = selected_disciplines.first()
    if first_discipline:
        club.main_discipline = first_discipline
        club.save(update_fields=['main_discipline'])

    # CRUCIAL: Assigner les disciplines à l'organisation du club
    if club.organization:
        club.organization.disciplines.set(selected_disciplines)
        club.organization.save()

        # Créer l'OrganizationMember pour le propriétaire
        from apps.organizations.models import OrganizationMember, OrganizationRole
        OrganizationMember.objects.get_or_create(
            organization=club.organization,
            user=request.user,
            defaults={'role': OrganizationRole.OWNER, 'is_active': True}
        )
# NE PAS assigner de discipline si aucune n'est sélectionnée

EXPECTED_CODE

echo ""
echo "# Après avoir modifié le fichier, redémarrez gunicorn:"
echo "pkill -f gunicorn"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 config.wsgi:application --daemon"
echo ""
echo "# Vérifier que gunicorn fonctionne:"
echo "ps aux | grep gunicorn"
