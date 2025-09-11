# GUIDE DE RESTAURATION MANUELLE DE LA BASE DE DONNÉES

## Fichier de sauvegarde localisé
```
Fichier: C:\martial_hub_django\martialcomp_backup_local\martialcomp_light_backup_20250716_235217\martialcomp_db_backup.sql
Taille: 876K
Type: Sauvegarde PostgreSQL complète avec données
```

## Option 1: Transfert via interface web (Plesk/cPanel)

1. Connectez-vous à votre interface Plesk
2. Allez dans "Files" ou "Gestionnaire de fichiers"  
3. Uploadez le fichier `martialcomp_db_backup.sql` dans `/tmp/`

## Option 2: Transfert via ligne de commande (depuis votre machine Windows)

```cmd
scp "C:\martial_hub_django\martialcomp_backup_local\martialcomp_light_backup_20250716_235217\martialcomp_db_backup.sql" root@martialcomp.com:/tmp/
```

## Option 3: Copier le contenu directement

Si les options précédentes ne fonctionnent pas, vous pouvez copier le contenu du fichier SQL et le créer directement sur le serveur.

## ÉTAPES DE RESTAURATION SUR LE SERVEUR

Une fois le fichier transféré, connectez-vous en SSH au serveur:
```bash
ssh root@martialcomp.com
```

### 1. Arrêter les services temporairement
```bash
sudo systemctl stop gunicorn
```

### 2. Sauvegarder l'état actuel (sécurité)
```bash
pg_dump -U martialcomp_user -h localhost martialcomp_db > /tmp/current_state_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Restaurer la base de données
```bash
# Vider la base actuelle (ATTENTION: ceci supprime tout!)
psql -U martialcomp_user -h localhost -d martialcomp_db -c "
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO martialcomp_user;
GRANT ALL ON SCHEMA public TO public;
"

# Restaurer à partir de la sauvegarde
psql -U martialcomp_user -h localhost -d martialcomp_db < /tmp/martialcomp_db_backup.sql
```

### 4. Vérifier la restauration
```bash
# Compter les tables
psql -U martialcomp_user -h localhost -d martialcomp_db -c "\dt" | wc -l

# Vérifier quelques tables importantes
psql -U martialcomp_user -h localhost -d martialcomp_db -c "
SELECT 'competitions_club' as table_name, count(*) as records FROM competitions_club
UNION ALL
SELECT 'competitions_practitioner', count(*) FROM competitions_practitioner  
UNION ALL
SELECT 'auth_user', count(*) FROM auth_user;
"
```

### 5. Recréer les schémas multi-tenant si nécessaire
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source .venv/bin/activate

# Créer les schémas pour chaque tenant
python3 manage.py shell << EOF
from multitenant.models import Client
clients = Client.objects.all()
for client in clients:
    print(f"Client: {client.name} - Schema: {client.schema_name}")
EOF

# Migrer chaque schéma tenant
python3 manage.py migrate --tenant-only
```

### 6. Redémarrer les services
```bash
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

### 7. Tester l'application
```bash
# Tester la page d'accueil
curl -I https://martialcomp.com

# Tester l'admin
curl -I https://martialcomp.com/admin/
```

## VÉRIFICATIONS FINALES

1. **Site principal**: https://martialcomp.com
2. **Interface admin**: https://martialcomp.com/admin/
3. **Logs en cas de problème**: 
   ```bash
   tail -f /var/log/gunicorn/error.log
   ```

## EN CAS DE PROBLÈME

Si la restauration échoue, vous pouvez revenir à l'état précédent:
```bash
sudo systemctl stop gunicorn
psql -U martialcomp_user -h localhost -d martialcomp_db < /tmp/current_state_backup_*.sql  
sudo systemctl start gunicorn
```

## NOTES IMPORTANTES

- La sauvegarde date du 16/07/2025 23:52
- Elle contient les vraies données de production
- Les tables tenant seront automatiquement recréées lors des migrations
- En cas de doute, n'hésitez pas à faire une sauvegarde avant de commencer