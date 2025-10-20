# CORRECTION DIRECTE POSTGRESQL

## 1. Accès direct à PostgreSQL
```bash
# Option A : Avec sudo
sudo -u postgres psql -d martialcomp

# Option B : Si vous avez les credentials
psql -h localhost -U martialcomp -d martialcomp
```

## 2. Commandes SQL à exécuter
```sql
-- Vérifier l'état actuel
SELECT COUNT(*) FROM competitions_discipline;

-- Si 0, insérer les disciplines
INSERT INTO competitions_discipline 
(name, description, country_origin, is_active, minimum_age, created_at, updated_at, organization_id, grading_system_id)
VALUES 
('Karaté', 'Art martial japonais', 'Japon', true, 0, NOW(), NOW(), NULL, NULL),
('Judo', 'Art martial japonais de projection', 'Japon', true, 0, NOW(), NOW(), NULL, NULL),
('Taekwondo', 'Art martial coréen', 'Corée', true, 0, NOW(), NOW(), NULL, NULL),
('Long Phai', 'Art martial vietnamien', 'Vietnam', true, 0, NOW(), NOW(), NULL, NULL),
('Aikido', 'Art martial japonais défensif', 'Japon', true, 0, NOW(), NOW(), NULL, NULL),
('Kung Fu', 'Arts martiaux chinois', 'Chine', true, 0, NOW(), NOW(), NULL, NULL),
('Boxe', 'Sport de combat', 'International', true, 0, NOW(), NOW(), NULL, NULL),
('MMA', 'Arts martiaux mixtes', 'International', true, 0, NOW(), NOW(), NULL, NULL);

-- Vérifier le résultat
SELECT id, name FROM competitions_discipline;

-- Sortir
\q
```

## 3. Alternative : Désactiver temporairement les signaux problématiques
```bash
# Faire une copie de sauvegarde
cp /var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/apps.py /tmp/apps.py.backup

# Éditer le fichier
nano /var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/apps.py
```

Remplacer le contenu par :
```python
from django.apps import AppConfig

class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.organizations'
    
    def ready(self):
        # TEMPORAIREMENT DÉSACTIVÉ
        pass
```

Puis :
```bash
# Tester à nouveau
/var/www/vhosts/martialcomp.com/venv/bin/python3 manage.py shell --settings=config.settings.production

# Dans le shell
from apps.competitions.models.discipline import Discipline
Discipline.objects.get_or_create(name='Karaté', defaults={'is_active': True})
Discipline.objects.get_or_create(name='Long Phai', defaults={'is_active': True})
print(f"✅ {Discipline.objects.count()} disciplines")
exit()

# Restaurer le fichier original
cp /tmp/apps.py.backup /var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/apps.py
```

## 4. Solution la plus rapide
Si vous avez accès à psql :
```bash
# Commande one-liner
echo "INSERT INTO competitions_discipline (name, is_active, created_at, updated_at, minimum_age) VALUES ('Karaté', true, NOW(), NOW(), 0), ('Long Phai', true, NOW(), NOW(), 0) ON CONFLICT DO NOTHING;" | sudo -u postgres psql -d martialcomp
```