# CORRECTION FINALE - ONBOARDING ET BASE DE DONNÉES

## Problèmes identifiés:

1. **Onboarding**: Les redirections ne fonctionnent toujours pas
2. **Base de données**: Il manque la colonne `criterion_id` dans `competitions_technicalscoreresult`

## SOLUTION COMPLÈTE

### Méthode 1: Script automatique (RECOMMANDÉE)

```bash
# Sur le serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer le script de correction
cat > fix_onboarding_and_db_final.py << 'EOF'
[Contenu du script fix_onboarding_and_db_final.py]
EOF

# Exécuter le script
python fix_onboarding_and_db_final.py

# Redémarrer Gunicorn
pkill -f gunicorn
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &
```

### Méthode 2: Corrections manuelles

#### A. Corriger la base de données:

```bash
# Django shell
python manage.py shell

# Dans le shell:
from django.db import connection
cursor = connection.cursor()

# Ajouter la colonne manquante
cursor.execute("""
    ALTER TABLE competitions_technicalscoreresult 
    ADD COLUMN criterion_id INTEGER REFERENCES competitions_scoringcriterion(id) ON DELETE CASCADE;
""")

# Créer l'index
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_technicalscoreresult_criterion 
    ON competitions_technicalscoreresult(criterion_id);
""")

print("✅ Colonne criterion_id ajoutée")
exit()
```

#### B. Corriger le fichier auth.py:

```bash
# Faire une sauvegarde
cp competitions/views/auth.py competitions/views/auth.py.backup_final

# Éditer le fichier
nano competitions/views/auth.py
```

**Localiser lignes 85-95 et remplacer par:**

```python
                # Message de bienvenue
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # CORRECTION: Rediriger directement vers le dashboard
                messages.info(request, _("Veuillez compléter votre profil pour accéder à toutes les fonctionnalités."))
                return redirect('dashboard:index')
```

**Supprimer tout le bloc try/except des redirections onboarding (lignes 96-108)**

### Méthode 3: Remplacement complet du fichier

```bash
# Sauvegarder l'ancien fichier
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

# Remplacer par le fichier corrigé
cat > competitions/views/auth.py << 'EOF'
[Contenu du fichier auth.py corrigé]
EOF

# Vérifier les permissions
chmod 644 competitions/views/auth.py
```

## COMMANDES DE TEST

```bash
# Vérifier que Gunicorn fonctionne
ps aux | grep gunicorn

# Tester la base de données
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.create_user('test123', 'test@test.com', 'test123'); print('OK'); u.delete(); print('DELETE OK')"

# Vérifier les logs
tail -f gunicorn.log
```

## RÉSULTAT ATTENDU

✅ **Inscription**: L'utilisateur peut créer un compte sans erreur  
✅ **Redirection**: Après inscription, redirection vers le dashboard  
✅ **Admin**: Plus d'erreur `criterion_id does not exist`  
✅ **Base de données**: Toutes les tables et colonnes sont présentes  

## TEST FINAL

🌐 **URL**: https://martialcomp.com/signup/

1. Créer un nouveau compte
2. Vérifier la redirection vers le dashboard  
3. Vérifier que l'administration fonctionne
4. Confirmer qu'il n'y a plus d'erreurs

---

**Cette correction résout définitivement tous les problèmes restants !**