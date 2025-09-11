# 🔧 CORRECTIONS ONBOARDING PARTICIPANT

## Problèmes Identifiés et Corrigés

### 1. **Problème de Date de Naissance**
❌ **Problème**: Le formulaire utilisait `date_of_birth` mais le template utilisait `birth_date`
✅ **Correction**: Renommé le champ en `birth_date` dans le formulaire pour correspondre au modèle Practitioner

### 2. **Champs Manquants**
❌ **Problème**: Le template faisait référence à des champs non définis dans le formulaire
✅ **Corrections**:
- `avatar` → `photo` (correspondance avec le modèle)
- Ajout de `nationality`
- Ajout de `main_discipline`
- Ajout de `other_discipline`
- Ajout de `medical_certificate` (fichier)
- Ajout de `selected_grade_id` et `selected_grade_name` (champs cachés)

### 3. **Récupération des Données d'Inscription**
❌ **Problème**: La vue n'initialisait pas le formulaire avec les données utilisateur existantes
✅ **Correction**: Ajout de l'initialisation automatique avec:
- Données utilisateur (prénom, nom, email)
- Données pratiquant existant (si disponible)
- Pré-sélection des disciplines

### 4. **Contexte du Template**
❌ **Problème**: Le template nécessitait des données non fournies par la vue
✅ **Corrections**:
- Ajout des `disciplines` actives
- Ajout des `grades_by_discipline` pour le JavaScript
- Gestion de l'application grades (avec fallback)

## Fichiers Modifiés

### 1. `competitions/forms/onboarding.py`
```python
# Changements principaux:
- date_of_birth → birth_date
- avatar → photo
+ nationality
+ main_discipline
+ other_discipline
+ medical_certificate
+ selected_grade_id
+ selected_grade_name
+ clean_photo()
+ clean_medical_certificate()
```

### 2. `competitions/views/onboarding/participant.py`
```python
# Changements principaux:
+ Initialisation avec données utilisateur
+ Récupération pratiquant existant
+ Ajout disciplines dans le contexte
+ Ajout grades_by_discipline
+ Gestion fallback pour l'app grades
```

## Fonctionnalités Améliorées

### ✅ Saisie de Date de Naissance
- Utilise `input type="date"` pour une interface moderne
- Validation côté client et serveur
- Format automatique JJ/MM/AAAA

### ✅ Récupération des Données
- Pré-remplit automatiquement avec les données d'inscription
- Récupère le profil pratiquant existant si disponible
- Conserve les disciplines déjà sélectionnées

### ✅ Gestion des Disciplines
- Liste déroulante des disciplines actives
- Option "Autre discipline" avec saisie libre
- Multi-sélection des disciplines pratiquées

### ✅ Gestion des Grades
- Grades organisés par discipline
- Interface dynamique avec JavaScript
- Fallback en cas d'absence de l'app grades

### ✅ Upload de Fichiers
- Photo de profil (JPG, PNG - 2Mo max)
- Certificat médical (PDF, JPG, PNG - 5Mo max)
- Validation de taille et format

## Tests à Effectuer

### 1. Interface Utilisateur
```
1. Aller sur https://martialcomp.com/fr/onboarding/participant/
2. Vérifier que le champ date de naissance fonctionne
3. Sélectionner une discipline et vérifier les grades
4. Tester l'upload de fichiers
5. Vérifier la validation du formulaire
```

### 2. Récupération des Données
```
1. S'inscrire avec un compte
2. Commencer l'onboarding
3. Vérifier que les données sont pré-remplies
4. Modifier et sauvegarder
5. Vérifier que les modifications sont conservées
```

### 3. Validation
```
1. Essayer de soumettre sans champs obligatoires
2. Tester avec des fichiers trop volumineux
3. Tester avec des formats non autorisés
4. Vérifier les messages d'erreur
```

## Commandes de Déploiement

### Sur le serveur de production:
```bash
# 1. Redémarrer Django
pkill -f gunicorn && sleep 3
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --daemon

# 2. Redémarrer nginx
systemctl restart nginx

# 3. Collecter les fichiers statiques (si nécessaire)
python3 manage.py collectstatic --noinput
```

## Résultat Attendu

Après ces corrections:
- ✅ La date de naissance se saisit correctement
- ✅ Tous les champs du template fonctionnent
- ✅ Les données d'inscription sont récupérées automatiquement
- ✅ L'interface est complète et intuitive
- ✅ La validation fonctionne correctement
- ✅ Les fichiers peuvent être uploadés

## Notes Techniques

- **Compatibilité**: Fonctionne avec ou sans l'application grades
- **Performance**: Requêtes optimisées pour les disciplines et grades
- **Sécurité**: Validation stricte des fichiers uploadés
- **UX**: Interface moderne avec input type="date" et JavaScript dynamique