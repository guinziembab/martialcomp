# Commandes pour corriger la table documents_document

## Méthode 1: Transfert automatique (depuis votre machine locale)

```bash
# Depuis le répertoire du projet
cd /mnt/c/martial_hub_django/martialcomp
./deploy_fix_documents.sh
```

## Méthode 2: Transfert manuel

### Étape 1: Transfert des fichiers
```bash
# Depuis votre machine locale
scp fix_documents_table.py root@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/
scp fix_documents_simple.py root@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/
```

### Étape 2: Exécution sur le serveur
```bash
# Connexion SSH au serveur
ssh root@martialcomp.com

# Navigation et activation de l'environnement
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

# Exécution du script de correction
python fix_documents_table.py
```

## Méthode 3: Commandes directes dans le shell Django

Si les méthodes précédentes ne marchent pas, vous pouvez exécuter directement dans le shell Django :

```bash
# Sur le serveur
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py shell
```

Puis dans le shell Django, copier-coller :

```python
from django.db import connection

print("🔧 Correction de la table documents_document...")

with connection.cursor() as cursor:
    try:
        # Vérifier les colonnes existantes
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'documents_document' AND column_name IN ('created_by_id', 'modified_by_id');")
        existing = [row[0] for row in cursor.fetchall()]
        
        # Ajouter created_by_id si manquant
        if 'created_by_id' not in existing:
            cursor.execute('ALTER TABLE documents_document ADD COLUMN created_by_id INTEGER;')
            cursor.execute('ALTER TABLE documents_document ADD CONSTRAINT fk_docs_created_by FOREIGN KEY (created_by_id) REFERENCES auth_user(id) ON DELETE SET NULL;')
            print("✅ created_by_id ajouté")
        else:
            print("✅ created_by_id existe")
            
        # Ajouter modified_by_id si manquant
        if 'modified_by_id' not in existing:
            cursor.execute('ALTER TABLE documents_document ADD COLUMN modified_by_id INTEGER;')
            cursor.execute('ALTER TABLE documents_document ADD CONSTRAINT fk_docs_modified_by FOREIGN KEY (modified_by_id) REFERENCES auth_user(id) ON DELETE SET NULL;')
            print("✅ modified_by_id ajouté")
        else:
            print("✅ modified_by_id existe")
            
        print("🎉 Table corrigée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

# Test rapide
from django.contrib.auth.models import User
import time

try:
    test_user = User.objects.create_user(username=f'test_{int(time.time())}', email='test@test.com', password='test123')
    print("✅ Test création OK")
    test_user.delete()
    print("✅ Test suppression OK")
    print("🎯 Signup/onboarding prêt!")
except Exception as e:
    print(f"❌ Test échoué: {e}")
    
exit()
```

## Résultat attendu

Après exécution, vous devriez voir :
```
🔧 Correction de la table documents_document...
✅ created_by_id ajouté
✅ modified_by_id ajouté
🎉 Table corrigée!
✅ Test création OK
✅ Test suppression OK
🎯 Signup/onboarding prêt!
```

## Vérification finale

Une fois la correction effectuée, testez le processus de signup sur https://martialcomp.com/signup/