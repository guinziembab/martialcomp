# COMMANDES MANUELLES DE CORRECTION - PRODUCTION

## 1. Se connecter au serveur de production
ssh user@martialcomp.com  # ou votre méthode de connexion

## 2. Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

## 3. Faire une sauvegarde
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

## 4. Corriger la base de données
python manage.py shell

# Dans le shell Django:
from django.db import connection
cursor = connection.cursor()

# Vérifier si la colonne criterion_id existe
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'competitions_technicalscoreresult' 
    AND column_name = 'criterion_id';
""")

if not cursor.fetchone():
    cursor.execute("""
        ALTER TABLE competitions_technicalscoreresult 
        ADD COLUMN criterion_id INTEGER REFERENCES competitions_scoringcriterion(id) ON DELETE CASCADE;
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_technicalscoreresult_criterion 
        ON competitions_technicalscoreresult(criterion_id);
    """)
    print("✅ Colonne criterion_id ajoutée")
else:
    print("✅ Colonne criterion_id existe déjà")

exit()

## 5. Corriger le fichier auth.py
# Utiliser le contenu du fichier auth.py corrigé (voir auth_py_corrected.py)

## 6. Redémarrer Gunicorn
pkill -f gunicorn
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &

## 7. Vérifier
ps aux | grep gunicorn
curl -I https://martialcomp.com/signup/

## RÉSULTAT ATTENDU:
# ✅ Plus d'erreur "Une erreur inattendue est survenue"
# ✅ Redirection vers le dashboard après inscription
# ✅ Processus d'inscription fonctionnel
