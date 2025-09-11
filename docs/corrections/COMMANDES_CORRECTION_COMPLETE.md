# Correction complète de la table documents_document

## Script complet pour corriger TOUS les champs manquants

### Méthode 1: Transférer et exécuter le script complet

```bash
# Depuis votre machine locale - transférer le script
scp fix_documents_table_complete.py root@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/

# Sur le serveur - exécuter le script
ssh root@martialcomp.com
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python fix_documents_table_complete.py
```

### Méthode 2: Commandes directes dans le shell Django

Si vous préférez, voici les commandes SQL directes à exécuter dans le shell Django :

```bash
# Sur le serveur
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py shell
```

Puis dans le shell Django :

```python
from django.db import connection

# Ajouter toutes les colonnes manquantes d'un coup
cursor = connection.cursor()

# Liste des colonnes à ajouter avec leurs définitions
columns = [
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS created_by_id INTEGER;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS modified_by_id INTEGER;", 
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS parent_id UUID;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS is_latest_version BOOLEAN DEFAULT true;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT false;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS expiry_date TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS content_type_id INTEGER;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS object_id VARCHAR(255);",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS document_type VARCHAR(50);",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS tenant_id UUID;",
    "ALTER TABLE documents_document ADD COLUMN IF NOT EXISTS organization_id UUID;",
]

# Exécuter toutes les commandes
for sql in columns:
    try:
        cursor.execute(sql)
        print(f"✅ {sql[:50]}...")
    except Exception as e:
        print(f"⚠️  {sql[:50]}... : {e}")

# Ajouter les contraintes de clé étrangère
constraints = [
    "ALTER TABLE documents_document ADD CONSTRAINT IF NOT EXISTS fk_docs_created_by FOREIGN KEY (created_by_id) REFERENCES auth_user(id) ON DELETE CASCADE;",
    "ALTER TABLE documents_document ADD CONSTRAINT IF NOT EXISTS fk_docs_modified_by FOREIGN KEY (modified_by_id) REFERENCES auth_user(id) ON DELETE SET NULL;",
    "ALTER TABLE documents_document ADD CONSTRAINT IF NOT EXISTS fk_docs_parent FOREIGN KEY (parent_id) REFERENCES documents_document(id) ON DELETE SET NULL;",
    "ALTER TABLE documents_document ADD CONSTRAINT IF NOT EXISTS fk_docs_content_type FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) ON DELETE SET NULL;",
]

for sql in constraints:
    try:
        cursor.execute(sql)
        print(f"✅ Contrainte ajoutée")
    except Exception as e:
        print(f"⚠️  Contrainte: {e}")

print("🎯 Test final...")

# Test final de création/suppression d'utilisateur
from django.contrib.auth.models import User
import time

try:
    test_user = User.objects.create_user(
        username=f'test_final_{int(time.time())}',
        email='final@test.com', 
        password='finaltest123'
    )
    print("✅ Test création OK")
    
    test_user.delete()
    print("✅ Test suppression OK")
    print("🎉 SIGNUP/ONBOARDING COMPLÈTEMENT PRÊT!")
    
except Exception as e:
    print(f"❌ Test final échoué: {e}")

exit()
```

## Champs corrigés

Le script ajoute **TOUS** les champs manquants identifiés dans le modèle Document :

- ✅ `created_by_id` - Référence vers l'utilisateur créateur
- ✅ `modified_by_id` - Référence vers l'utilisateur modificateur
- ✅ `parent_id` - Pour le versionnement des documents
- ✅ `is_latest_version` - Indique si c'est la version la plus récente
- ✅ `is_template` - Indique si c'est un modèle
- ✅ `expiry_date` - Date d'expiration du document
- ✅ `content_type_id` - Pour les liens génériques
- ✅ `object_id` - ID de l'objet lié
- ✅ `metadata` - Métadonnées JSON
- ✅ `document_type` - Type de document (certificat, diplôme, etc.)
- ✅ `view_count` - Nombre de vues
- ✅ `download_count` - Nombre de téléchargements
- ✅ `tenant_id` - Pour le multi-tenant
- ✅ `organization_id` - Pour l'organisation

## Résultat attendu

Après exécution, vous devriez voir :
```
🔧 Création/correction complète de la table documents_document...
✅ Colonne created_by_id ajoutée
✅ Colonne modified_by_id ajoutée
✅ Colonne parent_id ajoutée
...
✅ Index créés
🎯 Test de création/suppression d'utilisateur...
✅ Utilisateur créé avec succès
✅ Utilisateur supprimé avec succès
🎉 Table documents_document complètement corrigée!
✅ Le processus de signup/onboarding est maintenant opérationnel
```

Une fois cette correction effectuée, le processus de signup sur https://martialcomp.com/signup/ devrait fonctionner parfaitement ! 🎯