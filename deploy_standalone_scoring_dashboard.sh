#!/bin/bash
# Script de déploiement pour les améliorations visuelles du dashboard standalone scoring
# Améliorations : couleurs vives, dégradés professionnels, design moderne

echo "=== Déploiement des améliorations visuelles - Standalone Scoring Dashboard ==="
echo ""

# Configuration
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_FILE="apps/competitions/templates/competitions/standalone_scoring/admin/dashboard.html"
REMOTE_FILE="$REMOTE_PATH/$LOCAL_FILE"

# Vérifier que le fichier local existe
if [ ! -f "$LOCAL_FILE" ]; then
    echo "ERREUR: Le fichier $LOCAL_FILE n'existe pas localement"
    exit 1
fi

# Vérifier que les améliorations sont présentes
echo "Vérification des améliorations dans le fichier local..."

# Vérifier les variables CSS
if grep -q "Variables de couleurs professionnelles" "$LOCAL_FILE"; then
    echo "✓ Variables CSS professionnelles trouvées"
else
    echo "✗ ATTENTION: Variables CSS non trouvées"
fi

# Vérifier le dégradé de l'en-tête
if grep -q "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)" "$LOCAL_FILE"; then
    echo "✓ Dégradé violet/bleu de l'en-tête trouvé"
else
    echo "✗ ATTENTION: Dégradé de l'en-tête non trouvé"
fi

# Vérifier les cartes de statistiques colorées
if grep -q "stats-competitions" "$LOCAL_FILE" && grep -q "stats-performances" "$LOCAL_FILE"; then
    echo "✓ Cartes de statistiques colorées trouvées"
else
    echo "✗ ATTENTION: Cartes de statistiques non trouvées"
fi

# Vérifier les badges de statut
if grep -q "status-pending" "$LOCAL_FILE" && grep -q "status-completed" "$LOCAL_FILE"; then
    echo "✓ Badges de statut colorés trouvés"
else
    echo "✗ ATTENTION: Badges de statut non trouvés"
fi

# Vérifier les actions rapides
if grep -q "quick-action-btn" "$LOCAL_FILE" && grep -q "action-create" "$LOCAL_FILE"; then
    echo "✓ Actions rapides colorées trouvées"
else
    echo "✗ ATTENTION: Actions rapides non trouvées"
fi

echo ""
echo "Le fichier local contient les améliorations. Déploiement vers la production..."
echo ""

# Créer un backup sur le serveur distant
echo "Création d'un backup sur le serveur distant..."
BACKUP_FILE="${REMOTE_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
ssh "$REMOTE_HOST" "if [ -f \"$REMOTE_FILE\" ]; then cp \"$REMOTE_FILE\" \"$BACKUP_FILE\" && echo \"✓ Backup créé: $BACKUP_FILE\"; else echo \"⚠ Fichier distant n'existe pas encore\"; fi"

# Copier le fichier vers la production
echo ""
echo "Copie du fichier vers la production..."
scp "$LOCAL_FILE" "$REMOTE_HOST:$REMOTE_FILE"
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ ERREUR: Impossible de copier le fichier vers la production"
    echo ""
    echo "Veuillez exécuter manuellement :"
    echo "  scp $LOCAL_FILE $REMOTE_HOST:$REMOTE_FILE"
    echo "  ssh $REMOTE_HOST \"cd $REMOTE_PATH && sudo systemctl reload gunicorn\""
    exit 1
fi

echo "✓ Fichier copié avec succès"
echo ""

# Vérifier que le fichier a été copié correctement
echo "Vérification du fichier sur le serveur distant..."
ssh "$REMOTE_HOST" "if [ -f '$REMOTE_FILE' ]; then echo '✓ Fichier présent sur le serveur'; grep -q 'Variables de couleurs professionnelles' '$REMOTE_FILE' && echo '✓ Améliorations présentes dans le fichier distant'; else echo '✗ ERREUR: Fichier non trouvé sur le serveur'; exit 1; fi"

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ ERREUR: Vérification échouée"
    exit 1
fi

# Redémarrer le service Django
echo ""
echo "Redémarrage du service Django (martialcomp.service)..."
ssh "$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl reload martialcomp.service"
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ ATTENTION: Erreur lors du reload, tentative avec restart..."
    ssh "$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl restart martialcomp.service"
    if [ $? -ne 0 ]; then
        echo ""
        echo "✗ ERREUR: Impossible de redémarrer le service"
        echo "Veuillez redémarrer manuellement :"
        echo "  ssh $REMOTE_HOST \"cd $REMOTE_PATH && sudo systemctl restart martialcomp.service\""
        exit 1
    fi
fi

echo "✓ Service Django redémarré avec succès"
echo ""

# Vérification finale
echo "=== Déploiement terminé avec succès ==="
echo ""
echo "Améliorations visuelles appliquées :"
echo "  ✓ Variables CSS professionnelles"
echo "  ✓ En-tête avec dégradé violet/bleu"
echo "  ✓ Cartes de statistiques colorées (vert, bleu, orange, violet)"
echo "  ✓ Tableaux avec en-têtes colorés"
echo "  ✓ Badges de statut avec couleurs et dégradés"
echo "  ✓ Actions rapides avec couleurs distinctes"
echo "  ✓ Effets visuels améliorés (ombres, hover, transitions)"
echo ""
echo "Vérifiez que la page fonctionne maintenant :"
echo "  https://martialcomp.com/fr/competitions/standalone-scoring/admin/dashboard/"
echo ""
echo "Backup créé sur le serveur : $BACKUP_FILE"
