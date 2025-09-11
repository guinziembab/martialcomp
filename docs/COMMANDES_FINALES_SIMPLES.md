# Commandes finales simples pour corriger MartialComp

## Méthode 1: Script simple pour les tables survey

```bash
# Sur le serveur
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

# Créer le fichier directement
cat > fix_missing_survey_tables.py << 'EOF'
#!/usr/bin/env python
import os, sys, django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    try:
        print("🔧 Création des tables survey...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitions_survey (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                event_id INTEGER REFERENCES competitions_event(id) ON DELETE CASCADE,
                created_by_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            );
        """)
        print("✅ competitions_survey créée")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitions_surveyresponse (
                id SERIAL PRIMARY KEY,
                response_data JSONB DEFAULT '{}',
                submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                participant_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                survey_id INTEGER REFERENCES competitions_survey(id) ON DELETE CASCADE
            );
        """)
        print("✅ competitions_surveyresponse créée")
        
        from django.contrib.auth.models import User
        import time
        
        test_user = User.objects.create_user(
            username=f'test_final_{int(time.time())}',
            email='final@test.com',
            password='finalpass123'
        )
        print("✅ Test utilisateur créé")
        
        test_user.delete()
        print("✅ Test utilisateur supprimé - SUCCÈS COMPLET!")
        print("🌐 Testez maintenant: https://martialcomp.com/signup/")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
EOF

# Exécuter le script
python fix_missing_survey_tables.py
```

## Méthode 2: Commandes SQL directes

Si le script ne marche pas, exécutez directement en SQL :

```bash
# Shell Django
python manage.py shell

# Dans le shell, exécuter:
from django.db import connection
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS competitions_survey (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        event_id INTEGER REFERENCES competitions_event(id) ON DELETE CASCADE,
        created_by_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS competitions_surveyresponse (
        id SERIAL PRIMARY KEY,
        response_data JSONB DEFAULT '{}',
        submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        participant_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
        survey_id INTEGER REFERENCES competitions_survey(id) ON DELETE CASCADE
    );
""")

print("✅ Tables créées")

# Test final
from django.contrib.auth.models import User
import time

test_user = User.objects.create_user(username=f'test_{int(time.time())}', email='test@test.com', password='test123')
print("✅ Utilisateur créé")

test_user.delete()
print("✅ Utilisateur supprimé - SUCCÈS!")

exit()
```

## Méthode 3: Si problème persiste

Créer les tables une par une:

```sql
-- Dans psql directement
\c martialcomp_db

CREATE TABLE IF NOT EXISTS competitions_survey (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_id INTEGER REFERENCES competitions_event(id) ON DELETE CASCADE,
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS competitions_surveyresponse (
    id SERIAL PRIMARY KEY,
    response_data JSONB DEFAULT '{}',
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    participant_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES competitions_survey(id) ON DELETE CASCADE
);
```

## Résultat attendu

Après exécution réussie:
```
✅ competitions_survey créée
✅ competitions_surveyresponse créée
✅ Test utilisateur créé
✅ Test utilisateur supprimé - SUCCÈS COMPLET!
🌐 Testez maintenant: https://martialcomp.com/signup/
```

Le processus signup devrait maintenant fonctionner à 100% !