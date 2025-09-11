# 🚀 Correction Production PostgreSQL - is_training_score

## 📋 Plan d'exécution

### Phase 1: Préparation (5 min)

```bash
# 1. Se connecter au serveur de production
ssh user@martialcomp.com

# 2. Aller dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# 3. Activer l'environnement virtuel
source venv/bin/activate

# 4. Vérifier l'état actuel
python3 check_postgresql_column.py
```

### Phase 2: Sauvegarde (3 min)

```bash
# 1. Créer un répertoire de sauvegarde
BACKUP_DIR="/tmp/martialcomp_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 2. Sauvegarder les migrations
cp -r */migrations $BACKUP_DIR/

# 3. Sauvegarder la base de données (adapter selon votre config)
pg_dump -h localhost -U votre_user -d votre_base > $BACKUP_DIR/database_backup.sql

# 4. Vérifier la sauvegarde
ls -la $BACKUP_DIR/
```

### Phase 3: Arrêt des services (1 min)

```bash
# Arrêter Gunicorn (adapter selon votre configuration)
sudo systemctl stop gunicorn

# Arrêter Nginx si nécessaire
sudo systemctl stop nginx

# Ou si vous utilisez un autre système:
# supervisorctl stop martialcomp
# pkill -f "gunicorn"
```

### Phase 4: Application de la correction (2 min)

```bash
# 1. Vérifier les migrations disponibles
python3 manage.py showmigrations competitions

# 2. Appliquer la migration de correction
python3 manage.py migrate competitions 0007 --verbosity=2

# 3. Vérifier que la colonne existe maintenant
python3 check_postgresql_column.py
```

### Phase 5: Tests (2 min)

```bash
# 1. Test du modèle
python3 manage.py shell -c "
from competitions.models.scoring_results import TechnicalScoreResult
from django.contrib.auth.models import User

print('🔍 Test du modèle TechnicalScoreResult...')
try:
    count = TechnicalScoreResult.objects.filter(is_training_score=False).count()
    print(f'✅ Requête réussie: {count} résultats')
    
    user = User.objects.first()
    if user:
        scores = user.technical_score_results.all()
        print(f'✅ Relation inverse OK: {scores.count()} scores')
    
    print('✅ Tous les tests sont passés')
except Exception as e:
    print(f'❌ Erreur: {e}')
    exit(1)
"

# 2. Test de collecte des fichiers statiques
python3 manage.py collectstatic --noinput
```

### Phase 6: Redémarrage des services (1 min)

```bash
# Redémarrer Gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn

# Redémarrer Nginx
sudo systemctl start nginx
sudo systemctl status nginx

# Vérifier que les services sont actifs
sudo systemctl is-active gunicorn nginx
```

### Phase 7: Vérification finale (2 min)

```bash
# 1. Test d'accès à l'application
curl -I http://martialcomp.com/

# 2. Test de l'interface admin (remplacer par votre URL)
curl -I http://martialcomp.com/admin/

# 3. Vérifier les logs pour les erreurs
tail -f /var/log/nginx/error.log &
tail -f /var/log/your-app/error.log &
# Ctrl+C pour arrêter

# 4. Test final via le shell
python3 manage.py shell -c "
from django.test import Client
from django.contrib.auth.models import User

client = Client()
user = User.objects.filter(is_superuser=True).first()

if user:
    client.force_login(user)
    response = client.get('/admin/auth/user/')
    print(f'✅ Admin accessible: {response.status_code == 200}')
else:
    print('⚠️  Aucun superutilisateur pour le test')
"
```

## 🆘 En cas de problème

### Rollback rapide
```bash
# 1. Revenir à la migration précédente
python3 manage.py migrate competitions 0006

# 2. Restaurer les fichiers de migration si nécessaire
cp $BACKUP_DIR/migrations/* ./competitions/migrations/

# 3. Redémarrer les services
sudo systemctl restart gunicorn nginx
```

### Vérification des logs
```bash
# Logs Django/Gunicorn
tail -n 50 /var/log/gunicorn/error.log

# Logs Nginx
tail -n 50 /var/log/nginx/error.log

# Logs système
journalctl -u gunicorn -n 50
```

## ✅ Script automatisé

**Option recommandée**: Utiliser le script automatisé

```bash
# Rendre le script exécutable
chmod +x fix_postgresql_production.sh

# Exécuter avec confirmation
./fix_postgresql_production.sh
```

## 🔍 Commandes de diagnostic

### Vérifier la base de données
```sql
-- Se connecter à PostgreSQL
psql -h localhost -U votre_user -d votre_base

-- Vérifier la structure de la table
\d competitions_technicalscoreresult

-- Vérifier que la colonne existe
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'competitions_technicalscoreresult' 
AND column_name = 'is_training_score';

-- Quitter PostgreSQL
\q
```

### Vérifier les migrations Django
```bash
# État des migrations
python3 manage.py showmigrations

# Migrations non appliquées
python3 manage.py showmigrations --plan

# Dernière migration appliquée
python3 manage.py showmigrations competitions | tail -5
```

## 📞 Support

En cas de problème, conserver:
- Le répertoire de sauvegarde: `$BACKUP_DIR`
- Les logs d'erreur
- La sortie des commandes de diagnostic

**Temps total estimé: 15-20 minutes**
**Downtime: ~5 minutes**