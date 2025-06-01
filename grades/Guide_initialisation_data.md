Guide pour réinitialiser complètement vos migrations et données Django
Je vais vous guider pas à pas pour supprimer toutes les données et migrations afin de repartir de zéro. Cette approche est utile en développement, mais ne doit jamais être utilisée en production.
Étape 1: Sauvegarde (par sécurité)
Avant tout, faites une sauvegarde de votre base de données et de votre code:
bash# Sauvegarde de la base de données PostgreSQL
pg_dump -U postgres -d martialcomp > backup_db.sql

# Sauvegarde du dossier de migrations (facultatif)

mkdir -p backup_migrations
cp -r \*/migrations backup_migrations/
Étape 2: Supprimer la base de données
bash# Se connecter à PostgreSQL
psql -U postgres

# Dans l'interface PostgreSQL

DROP DATABASE votre_base;
CREATE DATABASE votre_base;
\q
Étape 3: Supprimer toutes les migrations
Supprimez tous les fichiers de migration sauf les fichiers **init**.py:
bash# Pour Windows (PowerShell)
Get-ChildItem -Path "competitions\migrations" -Exclude **init**.py | Remove-Item
Get-ChildItem -Path "grades\migrations" -Exclude **init**.py | Remove-Item

# Pour Windows (CMD)

del competitions\migrations\*.py
del grades\migrations\*.py
echo. > competitions\migrations\_\_init**.py
echo. > grades\migrations\_\_init**.py
Étape 4: Vérifier et nettoyer les références croisées
Vérifiez que vos modèles sont bien définis sans référence circulaire:

Dans competitions/models.py ou les fichiers de modèles associés:

Assurez-vous que les références à des modèles de l'application grades utilisent la syntaxe correcte:

pythongrade = models.ForeignKey('grades.Grade', on_delete=models.SET_NULL, ...)

Dans grades/models.py:

Vérifiez les références aux modèles de competitions:

pythonpractitioner = models.ForeignKey('competitions.Practitioner', on_delete=models.CASCADE, ...)

Étape 5: Créer de nouvelles migrations
Maintenant, créez de nouvelles migrations propres:
bashpython manage.py makemigrations competitions
python manage.py makemigrations grades
Étape 6: Appliquer les migrations
bashpython manage.py migrate
Étape 7: Créer un superutilisateur (facultatif)
bashpython manage.py createsuperuser
Étape 8: Charger des données initiales (facultatif)
Si vous avez des fixtures ou des scripts pour initialiser vos données:
bashpython manage.py loaddata initial_data.json
Solutions alternatives si les problèmes persistent
Option 1: Utiliser squashmigrations au lieu de tout supprimer
bashpython manage.py squashmigrations competitions 0001_initial
python manage.py squashmigrations grades 0001_initial
Option 2: Utiliser --fake pour les migrations problématiques
bashpython manage.py migrate competitions --fake
python manage.py migrate grades --fake
python manage.py migrate
Option 3: Migration en deux temps pour les champs problématiques

Créez une migration intermédiaire qui ajoute un champ temporaire
Migrez les données de l'ancien champ vers le nouveau
Supprimez l'ancien champ
Renommez le champ temporaire

Conseils supplémentaires

Pour les problèmes spécifiques au type JSONB - Si votre problème était lié à la conversion JSON vers entier:

Assurez-vous d'avoir des migrations qui convertissent proprement les données
Évitez les changements de type directs sur des champs contenant des données

Débogage des migrations - Utilisez l'option --verbosity 3 pour voir plus de détails:
bashpython manage.py migrate --verbosity 3

Récupération de l'état des migrations - Pour voir quelles migrations ont été appliquées:
bashpython manage.py showmigrations

Cette approche radicale devrait résoudre vos problèmes de migration, mais n'oubliez pas que vous perdrez toutes vos données existantes. Assurez-vous d'avoir une procédure pour recréer les données nécessaires au développement.

Pour effectuer cette opération sous Windows avec PowerShell, vous devez utiliser la commande Copy-Item (alias cp) avec la syntaxe correcte. Le problème est que le dossier backup_migrations existe déjà ou qu'il y a un problème avec la façon dont vous essayez de copier les dossiers.
Voici la commande correcte pour PowerShell:
powershell# D'abord, créez le dossier de sauvegarde s'il n'existe pas
if (-not (Test-Path -Path ".\backup_migrations")) {
New-Item -Path ".\backup_migrations" -ItemType Directory
}

# Copiez les dossiers de migrations pour chaque application

Copy-Item -Path ".\competitions\migrations" -Destination ".\backup_migrations\competitions_migrations" -Recurse
Copy-Item -Path ".\grades\migrations" -Destination ".\backup_migrations\grades_migrations" -Recurse
Alternativement, vous pouvez utiliser cette version plus simple:
powershell# Créer le dossier de sauvegarde
mkdir -Force backup_migrations

# Copier chaque dossier de migrations individuellement

Copy-Item -Path "competitions\migrations" -Destination "backup_migrations\competitions_migrations" -Recurse
Copy-Item -Path "grades\migrations" -Destination "backup_migrations\grades_migrations" -Recurse
