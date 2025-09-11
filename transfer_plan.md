# Plan de Transfert des Modifications

## Étapes du Transfert

### 1. Préparation
```bash
# Créer une branche pour le transfert
git checkout -b transfer-august-2025-changes

# Créer un patch du commit principal
git format-patch -1 80e4485 -o patches/
```

### 2. Fichiers à transférer

#### A. Commit principal (80e4485)
- **api_auth/views.py**: Nouvelles vues pour l'API mobile
  - UserProfileView
  - SocialLoginGoogleView
  - SocialLoginFacebookView

#### B. Modifications non committées importantes
1. **api/urls.py**
   - Nouveaux endpoints health et info
   - Mobile dashboard endpoint
   - Payment methods endpoint
   - Organisation API endpoints
   - Certificate/License generation endpoints

2. **api_auth/** (plusieurs fichiers)
   - models.py
   - serializers.py
   - urls.py
   - migrations/0001_initial.py

### 3. Structure apps/
Le dossier apps contient tous les modules de l'application:
- accounts/
- competitions/
- documents/
- family_management/
- finances/
- grades/
- organizations/
- payment/
- permissions_manager/
- security/
- shop/
- task_management/

### 4. Script de transfert automatisé

```bash
#!/bin/bash
# transfer_changes.sh

# Variables
SOURCE_DIR="/mnt/c/martial_hub_django/martialcomp"
TARGET_DIR="<VOTRE_REPERTOIRE_CIBLE>"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

# Créer un backup
echo "Création du backup..."
mkdir -p $BACKUP_DIR

# Appliquer le patch du commit
echo "Application du patch..."
git apply patches/0001-Backend-expose-enriched-organization.patch

# Copier les fichiers modifiés
echo "Copie des fichiers modifiés..."
cp api/urls.py $TARGET_DIR/api/
cp api_auth/views.py $TARGET_DIR/api_auth/
cp api_auth/models.py $TARGET_DIR/api_auth/
cp api_auth/serializers.py $TARGET_DIR/api_auth/
cp api_auth/urls.py $TARGET_DIR/api_auth/

# Copier le dossier apps
echo "Copie du dossier apps..."
cp -r apps/ $TARGET_DIR/

echo "Transfert terminé!"
```

### 5. Tests recommandés après transfert

1. **API Authentication**
   - Tester `/api/v1/auth/profile/`
   - Tester social login (Google/Facebook)

2. **Mobile Endpoints**
   - `/api/health/`
   - `/api/v1/mobile/dashboard/`
   - `/api/payment/methods/`

3. **Modules apps**
   - Vérifier que tous les modules se chargent correctement
   - Tester les migrations

### 6. Notes importantes

- Nombreux fichiers ont été supprimés (scripts, docs)
- Vérifier les dépendances dans requirements.txt
- Les fichiers de traduction ont été modifiés
- Configuration settings.py et urls.py modifiées

### 7. Commandes utiles

```bash
# Voir tous les fichiers modifiés
git diff --name-only

# Créer une archive des modifications
git archive --format=tar HEAD $(git diff --name-only) -o changes.tar

# Vérifier l'état des migrations
python manage.py showmigrations
```