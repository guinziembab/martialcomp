#!/bin/bash
# =============================================================================
# DEPLOIEMENT MODULE FINANCES - PRODUCTION
# Date: 2024-12-02
# Description: Transfert des fichiers du module d'import bancaire et rapprochement
# =============================================================================

# Configuration SSH
SSH_HOST="martialcomp-production"
REMOTE_BASE="/var/www/vhosts/martialcomp.com/httpdocs"

echo "========================================"
echo "DEPLOIEMENT MODULE FINANCES - PRODUCTION"
echo "========================================"
echo ""

# =============================================================================
# 1. PARSEURS BANCAIRES
# =============================================================================
echo "1. Transfert des parseurs bancaires..."

# Base parser (si modifié)
scp apps/finances/parsers/base.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/base.py

# Parseur BNP Paribas Fortis Belgique (EXISTANT - requis)
scp apps/finances/parsers/bnp_fortis.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/bnp_fortis.py

# Parseur Société Générale France (NOUVEAU)
scp apps/finances/parsers/societe_generale.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/societe_generale.py

# Parseur Orange Money Côte d'Ivoire (NOUVEAU)
scp apps/finances/parsers/orange_money.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/orange_money.py

# Parseur Wave Sénégal (NOUVEAU)
scp apps/finances/parsers/wave.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/wave.py

# Registry des parseurs (MODIFIÉ - ajout des nouveaux parseurs)
scp apps/finances/parsers/__init__.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/parsers/__init__.py

echo "   -> Parseurs transférés"
echo ""

# =============================================================================
# 2. SERVICES
# =============================================================================
echo "2. Transfert des services..."

# Service d'import bancaire (MODIFIÉ - matching référence structurée belge)
scp apps/finances/services/bank_import_service.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/services/bank_import_service.py

echo "   -> Services transférés"
echo ""

# =============================================================================
# 3. VUES
# =============================================================================
echo "3. Transfert des vues..."

# Vues banking (MODIFIÉ - ajout dashboard rapprochement + export PDF)
scp apps/finances/views/banking.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/views/banking.py

# Dashboard financier (MODIFIÉ - période par défaut 'all')
scp apps/finances/views/dashboard.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/views/dashboard.py

echo "   -> Vues transférées"
echo ""

# =============================================================================
# 4. TEMPLATES
# =============================================================================
echo "4. Transfert des templates..."

# Créer le répertoire banking si nécessaire
ssh ${SSH_HOST} "mkdir -p ${REMOTE_BASE}/apps/finances/templates/finances/banking"

# Dashboard import bancaire
scp apps/finances/templates/finances/banking/import_dashboard.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/import_dashboard.html

# Upload fichier
scp apps/finances/templates/finances/banking/import_upload.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/import_upload.html

# Prévisualisation import
scp apps/finances/templates/finances/banking/import_preview.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/import_preview.html

# Historique imports
scp apps/finances/templates/finances/banking/import_history.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/import_history.html

# Détail d'un lot d'import
scp apps/finances/templates/finances/banking/import_detail.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/import_detail.html

# Liste transactions en attente de réconciliation
scp apps/finances/templates/finances/banking/reconciliation_pending.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/reconciliation_pending.html

# Réconciliation d'une transaction
scp apps/finances/templates/finances/banking/transaction_reconcile.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/transaction_reconcile.html

# NOUVEAU: Tableau de bord de rapprochement
scp apps/finances/templates/finances/banking/reconciliation_dashboard.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/banking/reconciliation_dashboard.html

# Dashboard financier principal (si modifié)
scp apps/finances/templates/finances/dashboard/index.html ${SSH_HOST}:${REMOTE_BASE}/apps/finances/templates/finances/dashboard/index.html

echo "   -> Templates transférés"
echo ""

# =============================================================================
# 5. URLs
# =============================================================================
echo "5. Transfert des URLs..."

# URLs finances (MODIFIÉ - ajout routes dashboard et export PDF)
scp apps/finances/urls.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/urls.py

echo "   -> URLs transférées"
echo ""

# =============================================================================
# 6. MODÈLES (si modifiés)
# =============================================================================
echo "6. Transfert des modèles..."

# Modèles banking
scp apps/finances/models/banking.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/models/banking.py

# Init des modèles
scp apps/finances/models/__init__.py ${SSH_HOST}:${REMOTE_BASE}/apps/finances/models/__init__.py

echo "   -> Modèles transférés"
echo ""

# =============================================================================
# 7. COMMANDES POST-DEPLOIEMENT (à exécuter sur le serveur)
# =============================================================================
echo "========================================"
echo "COMMANDES POST-DEPLOIEMENT"
echo "========================================"
echo ""
echo "Connectez-vous au serveur et exécutez:"
echo ""
echo "  ssh ${SSH_HOST}"
echo ""
echo "  cd ${REMOTE_BASE}"
echo "  source venv/bin/activate"
echo ""
echo "  # Vérifier la syntaxe Python"
echo "  python -m py_compile apps/finances/parsers/societe_generale.py"
echo "  python -m py_compile apps/finances/parsers/orange_money.py"
echo "  python -m py_compile apps/finances/parsers/wave.py"
echo "  python -m py_compile apps/finances/views/banking.py"
echo ""
echo "  # Appliquer les migrations si nécessaire"
echo "  python manage.py migrate --check"
echo ""
echo "  # Collecter les fichiers statiques"
echo "  python manage.py collectstatic --noinput"
echo ""
echo "  # Redémarrer le serveur"
echo "  sudo systemctl restart gunicorn"
echo "  # ou"
echo "  sudo systemctl restart apache2"
echo ""
echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
echo ""
echo "Nouvelles fonctionnalités déployées:"
echo "  - Parseur Société Générale France"
echo "  - Parseur Orange Money Côte d'Ivoire"
echo "  - Parseur Wave Sénégal"
echo "  - Matching par référence structurée belge"
echo "  - Tableau de bord de rapprochement bancaire"
echo "  - Export PDF du rapport de rapprochement"
echo ""
echo "URLs disponibles:"
echo "  - /finances/banking/                          -> Dashboard import"
echo "  - /finances/banking/reconciliation/           -> Transactions en attente"
echo "  - /finances/banking/reconciliation/dashboard/ -> Tableau de bord rapprochement"
echo "  - /finances/banking/reconciliation/export-pdf/ -> Export PDF"
echo ""
