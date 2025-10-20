# 🚀 COMMANDES POUR LA PRODUCTION

## 1. Transfert des fichiers
```bash
# Depuis votre machine locale, dans le dossier martialcomp
scp check_disciplines_production.py martialcomp-production:/tmp/
scp fix_disciplines_production.py martialcomp-production:/tmp/
scp quick_fix_disciplines.sh martialcomp-production:/tmp/
```

## 2. Connexion au serveur
```bash
ssh martialcomp-production
```

## 3. Correction rapide (RECOMMANDÉ)
```bash
# Une fois connecté au serveur
cd /var/www/vhosts/martialcomp.com/httpdocs
chmod +x /tmp/quick_fix_disciplines.sh
bash /tmp/quick_fix_disciplines.sh
```

## 4. Alternative : Correction one-liner
```bash
# Si vous voulez juste créer une discipline rapidement
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py shell --settings=config.settings.production -c "from apps.competitions.models import Discipline; Discipline.objects.get_or_create(name='Karaté', defaults={'is_active': True})[0]; print(f'✅ {Discipline.objects.count()} discipline(s) en base')"
```

## 5. Test après correction
```bash
# Vérifier que les disciplines sont créées
python manage.py shell --settings=config.settings.production -c "from apps.competitions.models import Discipline; print(f'Disciplines: {list(Discipline.objects.values_list(\"name\", flat=True))}')"

# Tester la création d'un practitioner
python manage.py shell --settings=config.settings.production << 'EOF'
from apps.competitions.models import Practitioner
from apps.organizations.models import Organization

org = Organization.objects.first()
if org:
    p = Practitioner.objects.create(
        first_name="Test",
        last_name="Production",
        organization=org
    )
    print(f"✅ Practitioner créé sans erreur (ID: {p.id})")
    p.delete()
else:
    print("⚠️ Pas d'organisation disponible")
EOF
```

## 6. Si tout fonctionne, désactiver le blocage
```bash
# Éditer le fichier de configuration
nano /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py

# Commenter ou supprimer la ligne :
# 'apps.core.middleware.block_practitioner.BlockPractitionerMiddleware',

# Sauvegarder (Ctrl+X, Y, Enter)

# Redémarrer Apache
sudo systemctl restart apache2
```

## 7. Vérification finale
Accéder à https://martialcomp.com/fr/admin/competitions/practitioner/
- La page doit s'afficher sans erreur
- Vous devez pouvoir ajouter un practitioner

---
💡 **Astuce** : Commencez par l'étape 3 (correction rapide) qui fait tout automatiquement !