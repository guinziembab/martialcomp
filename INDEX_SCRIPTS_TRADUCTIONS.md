# 📚 Index des Scripts de Traduction - MartialComp

**Date de création** : 2 Octobre 2025  
**Version** : 1.0

---

## 🎯 Vue d'Ensemble

Ce document liste tous les scripts et outils disponibles pour gérer les traductions du projet MartialComp.

---

## 📜 Scripts Disponibles

### 1. `translation_stats.sh`

**Description** : Affiche les statistiques détaillées de toutes les langues

**Usage** :
```bash
bash translation_stats.sh
```

**Sortie** :
- Tableau avec toutes les langues
- Nombre de chaînes traduites/manquantes
- Pourcentage de complétion
- Statut par langue

**Exemple** :
```
┌─────────────────────┬──────────┬──────────┬──────────┬──────┬──────────┐
│ Langue              │ Total    │ Traduits │ Manquant │   %  │ Statut   │
├─────────────────────┼──────────┼──────────┼──────────┼──────┼──────────┤
│ English             │    11880 │    11880 │        0 │ 100% │ ✅ OK   │
│ Português          │    11683 │     6277 │     5406 │  53% │ ❌ À faire │
└─────────────────────┴──────────┴──────────┴──────────┴──────┴──────────┘
```

---

### 2. `extract_translations.sh`

**Description** : Extrait et compile toutes les traductions

**Usage** :
```bash
bash extract_translations.sh
```

**Actions** :
1. Crée un backup automatique dans `backups/`
2. Extrait les chaînes (si xgettext disponible)
3. Compile tous les fichiers `.mo`
4. Affiche un résumé

**Sortie** :
```
✅ Langues compilées: 18
❌ Erreurs: 0
📦 Backup: backups/locale_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

### 3. `analyze_untranslated_v2.py`

**Description** : Analyse les templates pour détecter les chaînes non traduites

**Usage** :
```bash
python analyze_untranslated_v2.py
```

**Sortie** :
- Nombre de templates analysés
- Chaînes uniques trouvées
- Top 20 des chaînes détectées

**Exemple** :
```
Templates analysés: 501
Chaînes uniques trouvées: 350

Exemples de chaînes trouvées:
1. Accueil
2. Actions
3. Administration des federations
...
```

---

### 4. `translate_portuguese.py`

**Description** : Traduit automatiquement le portugais avec DeepL API

**Usage** :
```bash
# Rapport uniquement
python translate_portuguese.py --report-only

# Traduction complète
python translate_portuguese.py --api-key VOTRE_CLE_DEEPL

# Test sur 10 chaînes
python translate_portuguese.py --api-key VOTRE_CLE --limit 10 --dry-run
```

**Prérequis** :
```bash
pip install deepl polib
```

**Obtenir une clé gratuite** : https://www.deepl.com/pro-api

---

### 5. `add_translations.sh`

**Description** : Script d'aide pour ajouter des traductions manuellement

**Usage** :
```bash
bash add_translations.sh en
```

**Note** : Éditer le script pour ajouter vos traductions avant exécution

---

### 6. `COMMANDES_AUJOURDHUI.sh`

**Description** : Commandes rapides pour les corrections immédiates

**Usage** :
```bash
bash COMMANDES_AUJOURDHUI.sh
```

**Actions** :
- Recompile le portugais
- Affiche les chaînes manquantes FR/ES
- Génère les statistiques

---

## 📄 Rapports et Documentation

### Rapports d'Audit

1. **`RAPPORT_AUDIT_TRADUCTIONS_FINAL.md`**
   - Audit complet des 18 langues
   - Analyse détaillée du portugais
   - Plan d'action avec DeepL

2. **`RAPPORT_MISE_A_JOUR_TRADUCTIONS_20251002.md`**
   - Mise à jour et compilation
   - Statistiques globales
   - Scripts créés

3. **`TABLEAU_RECAPITULATIF.txt`**
   - Vue d'ensemble rapide
   - Tableau ASCII des langues

### Corrections Appliquées

4. **`CORRECTION_NoReverseMatch_20251002.md`**
   - Correction erreur URL dashboard

5. **`CORRECTION_TRADUCTIONS_20251002.md`**
   - Traductions anglaises ajoutées
   - Procédures détaillées

---

## 🔄 Workflows Courants

### Workflow 1 : Après Modification de Templates

```bash
# 1. Analyser les nouveaux textes
python analyze_untranslated_v2.py

# 2. Extraire et compiler
bash extract_translations.sh

# 3. Vérifier les stats
bash translation_stats.sh

# 4. Redémarrer Django
python manage.py runserver 127.0.0.1:8080
```

### Workflow 2 : Ajouter une Nouvelle Langue

```bash
# 1. Créer la structure
mkdir -p locale/<code_langue>/LC_MESSAGES

# 2. Copier un fichier .po existant
cp locale/fr/LC_MESSAGES/django.po locale/<code_langue>/LC_MESSAGES/

# 3. Traduire avec Poedit Pro ou DeepL

# 4. Compiler
msgfmt -o locale/<code_langue>/LC_MESSAGES/django.mo \
       locale/<code_langue>/LC_MESSAGES/django.po

# 5. Ajouter au script translation_stats.sh
```

### Workflow 3 : Compléter le Portugais

```bash
# 1. Obtenir clé DeepL gratuite
# https://www.deepl.com/pro-api

# 2. Installer dépendances
pip install deepl polib

# 3. Traduire
python translate_portuguese.py --api-key VOTRE_CLE

# 4. Réviser avec Poedit Pro
# Ouvrir locale/pt/LC_MESSAGES/django.po

# 5. Compiler
bash extract_translations.sh

# 6. Tester
http://127.0.0.1:8080/pt/competitions/dashboard/club/
```

---

## 🛠️ Commandes Django Utiles

### Extraction

```bash
# Extraire pour toutes les langues
python manage.py makemessages --all

# Extraire pour une langue
python manage.py makemessages -l pt

# Ignorer certains fichiers
python manage.py makemessages --all --ignore=venv/*

# Ne pas marquer comme obsolètes
python manage.py makemessages --all --no-obsolete
```

### Compilation

```bash
# Compiler toutes les langues
python manage.py compilemessages

# Compiler une langue
python manage.py compilemessages -l pt

# Avec verbosité
python manage.py compilemessages -v 2
```

### Vérification

```bash
# Vérifier les fichiers .mo
find locale -name "django.mo" -ls

# Vérifier un fichier .po
msgfmt --check locale/pt/LC_MESSAGES/django.po
```

---

## 📊 Statistiques Actuelles

**Date** : 2 Octobre 2025

| Métrique | Valeur |
|----------|--------|
| Langues supportées | 18 |
| Total de traductions | 211,933 |
| Traduites | 206,525 (97.4%) |
| Manquantes | 5,408 (2.6%) |
| Langues à 100% | 15 |
| Langues incomplètes | 3 (fr: 99.9%, es: 99.9%, pt: 53.7%) |

---

## 🔗 Ressources Externes

### Outils

- **Poedit Pro** : https://poedit.net/pro (29€/an)
- **DeepL API** : https://www.deepl.com/pro-api (gratuit 500k/mois)
- **Django Rosetta** : Interface web pour traductions

### Documentation

- **Django i18n** : https://docs.djangoproject.com/en/4.2/topics/i18n/
- **Format .po** : https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html
- **msgfmt** : https://www.gnu.org/software/gettext/manual/html_node/msgfmt-Invocation.html

---

## 📞 Aide et Support

### En Cas de Problème

1. **Erreur de compilation** :
   ```bash
   # Vérifier le fichier .po pour les doublons
   grep "^msgid" locale/<langue>/LC_MESSAGES/django.po | sort | uniq -d
   ```

2. **Traductions ne s'affichent pas** :
   ```bash
   # Recompiler
   bash extract_translations.sh
   
   # Redémarrer Django
   # Vider le cache navigateur
   ```

3. **Nouveau texte non traduit** :
   ```bash
   # Vérifier que {% trans %} est utilisé dans le template
   # Extraire les nouvelles chaînes
   python manage.py makemessages --all
   ```

---

**Index créé le 2 Octobre 2025**  
**Tous les scripts sont dans** : `/mnt/c/martial_hub_django/martialcomp/`
