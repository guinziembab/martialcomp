# ⚡ ACTIONS IMMÉDIATES - Traductions MartialComp

**Date** : 2 Octobre 2025  
**Priorité** : Compléter le Portugais (pt)

---

## 🎯 RÉSUMÉ ULTRA-RAPIDE

- ✅ 16 langues sur 18 sont complètes (100%)
- ⚠️ Français et Espagnol : 99% (1 chaîne manquante chacun)
- ❌ **Portugais : 54%** (5,314 chaînes manquantes) **← ACTION REQUISE**

---

## 🚀 COMMANDES À EXÉCUTER MAINTENANT

### Étape 1 : Recompiler le Portugais (30 secondes)

```bash
cd /mnt/c/martial_hub_django/martialcomp
python manage.py compilemessages -l pt
```

**Résultat** : Active les 6,368 traductions existantes

---

### Étape 2 : Option A - Traduction Automatique DeepL (RECOMMANDÉ)

#### 2.1 Installer les dépendances (1 minute)

```bash
pip install deepl polib
```

#### 2.2 Obtenir clé API DeepL GRATUITE (5 minutes)

1. Aller sur : https://www.deepl.com/pro-api
2. Cliquer : "Sign up for free"
3. Créer compte (email + mot de passe)
4. Confirmer email
5. Copier la clé API (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx`)

**Quota gratuit** : 500,000 caractères/mois (largement suffisant pour 5,314 chaînes)

#### 2.3 Traduire automatiquement (2 heures)

```bash
cd /mnt/c/martial_hub_django/martialcomp

# Test sur 10 chaînes d'abord
python translate_portuguese.py --api-key VOTRE_CLE_ICI --limit 10 --dry-run

# Si OK, traduction complète
python translate_portuguese.py --api-key VOTRE_CLE_ICI
```

**Résultat attendu** :
```
✅ Traduites:  5,314
❌ Erreurs:     0
✅ Fichier sauvegardé: locale/pt/LC_MESSAGES/django.po
```

#### 2.4 Réviser avec Poedit (2-3 heures)

```bash
# 1. Télécharger Poedit Pro: https://poedit.net/pro (29€/an)
# 2. Ouvrir: locale/pt/LC_MESSAGES/django.po
# 3. Filtrer: Afficher "Récemment ajoutées" ou "Toutes"
# 4. Réviser ~500 traductions (10% échantillon)
#    - Vérifier contexte métier
#    - Adapter terminologie arts martiaux
#    - Vérifier variables %(...)s
# 5. Sauvegarder (compile automatiquement)
```

#### 2.5 Compiler et tester (30 minutes)

```bash
# Compiler
python manage.py compilemessages -l pt

# Lancer le serveur
python manage.py runserver

# Tester dans le navigateur
# Ouvrir: http://localhost:8000/pt/
# Changer de langue via le sélecteur
# Vérifier:
#   - Page d'accueil
#   - Formulaires
#   - Messages d'erreur
#   - Navigation
```

---

### Étape 3 : Option B - Traduction Manuelle Poedit (Si pas DeepL)

```bash
# 1. Télécharger Poedit Pro: https://poedit.net/pro
# 2. Ouvrir: locale/pt/LC_MESSAGES/django.po
# 3. Activer suggestions automatiques (Ctrl+M)
# 4. Traduire les 5,314 chaînes une par une
# 5. Temps estimé: 30-40 heures
```

**Note** : Option B déconseillée (trop long). Utilisez Option A (DeepL).

---

## 📝 APRÈS TRADUCTION

### Vérification Qualité

```bash
# 1. Vérifier qu'il n'y a plus de chaînes vides
grep -c '^msgstr ""$' locale/pt/LC_MESSAGES/django.po
# Devrait retourner: 0

# 2. Vérifier le pourcentage
total=$(grep -c '^msgid ' locale/pt/LC_MESSAGES/django.po)
trans=$(grep '^msgstr ' locale/pt/LC_MESSAGES/django.po | grep -v '^msgstr ""$' | wc -l)
echo "Portugais: $trans/$total ($(($trans*100/$total))%)"
# Devrait retourner: 100%

# 3. Vérifier les caractères spéciaux portugais
grep -E 'ã|õ|ç|á|é|ó' locale/pt/LC_MESSAGES/django.po | head -10
# Devrait afficher des mots portugais corrects
```

### Déploiement Production

```bash
# 1. Créer backup production
ssh root@serveur
cd /var/www/vhosts/martialcomp.com/apps/martialcomp
tar -czf backups/locale_pt_backup_$(date +%Y%m%d_%H%M%S).tar.gz locale/pt/

# 2. Copier depuis dev
scp -r /mnt/c/martial_hub_django/martialcomp/locale/pt \
  root@serveur:/var/www/vhosts/martialcomp.com/apps/martialcomp/locale/

# 3. Compiler sur production
source venv/bin/activate
python manage.py compilemessages -l pt

# 4. Redémarrer
systemctl restart martialcomp.service

# 5. Tester
curl -I https://martialcomp.com/pt/
# Devrait retourner: HTTP/2 200

# 6. Vérifier dans le navigateur
# https://martialcomp.com/pt/
```

---

## 🐛 RÉSOLUTION DE PROBLÈMES

### Problème 1 : DeepL rate limit

**Symptôme** : Erreur "Quota exceeded"

**Solution** :
```bash
# Traduire par lots de 1000
python translate_portuguese.py --api-key VOTRE_CLE --limit 1000
# Attendre 1 heure
python translate_portuguese.py --api-key VOTRE_CLE --limit 1000
# Répéter jusqu'à complétion
```

### Problème 2 : Erreur de compilation

**Symptôme** : `Error: problems with the character set used`

**Solution** :
```bash
# Vérifier l'encodage
file locale/pt/LC_MESSAGES/django.po
# Devrait être: UTF-8

# Si pas UTF-8, convertir
iconv -f ISO-8859-1 -t UTF-8 locale/pt/LC_MESSAGES/django.po > locale/pt/LC_MESSAGES/django.po.new
mv locale/pt/LC_MESSAGES/django.po.new locale/pt/LC_MESSAGES/django.po
```

### Problème 3 : Variables non préservées

**Symptôme** : Erreur `invalid format string`

**Solution** :
```bash
# Vérifier les variables
grep '%(.*%)s' locale/pt/LC_MESSAGES/django.po | grep -v msgid | head -20

# Corriger manuellement avec Poedit
# Les variables comme %(name)s doivent être EXACTEMENT préservées
```

---

## 📊 ESTIMATION DU TRAVAIL

### Avec DeepL (Recommandé)

| Tâche | Temps | Personne |
|-------|-------|----------|
| Installation dépendances | 5 min | Dev |
| Obtenir clé API | 5 min | Dev |
| Traduction automatique | 2h | Script |
| Révision échantillon 20% | 3h | Traducteur PT |
| Révision ciblée | 2h | Traducteur PT |
| Tests | 1h | QA |
| **TOTAL** | **~8h** | **+2h script** |

**Coût estimé** : 240€ (si traducteur freelance à 30€/h)

### Sans DeepL (Manuel)

| Tâche | Temps | Personne |
|-------|-------|----------|
| Traduction manuelle | 35-40h | Traducteur PT |
| Révision | 5h | Traducteur PT |
| Tests | 2h | QA |
| **TOTAL** | **~42-47h** | |

**Coût estimé** : 1,260-1,410€

**Économie avec DeepL** : ~1,000€ et 34-39 heures

---

## ✅ CHECKLIST D'EXÉCUTION

### Phase 1 : Préparation (10 min)

```
□ pip install deepl polib
□ Créer compte DeepL (gratuit)
□ Copier clé API
□ Tester connexion : python translate_portuguese.py --report-only
```

### Phase 2 : Traduction (2h)

```
□ Test sur 10 chaînes : --limit 10 --dry-run
□ Traduction complète : python translate_portuguese.py --api-key CLE
□ Vérifier résultat : grep -c '^msgstr ""$' locale/pt/LC_MESSAGES/django.po
□ Devrait être 0
```

### Phase 3 : Révision (5h)

```
□ Télécharger Poedit Pro
□ Ouvrir locale/pt/LC_MESSAGES/django.po
□ Réviser 500 chaînes échantillon (10%)
□ Corriger problèmes trouvés
□ Réviser sections critiques :
  □ Messages d'erreur
  □ Formulaires
  □ Admin Django
  □ Terminologie arts martiaux
```

### Phase 4 : Tests (2h)

```
□ Compiler : python manage.py compilemessages -l pt
□ Lancer serveur : python manage.py runserver
□ Tester navigation complète en portugais
□ Vérifier caractères spéciaux (ã, õ, ç)
□ Tester formulaires
□ Vérifier messages d'erreur
```

### Phase 5 : Déploiement Production (30 min)

```
□ Backup production
□ Copier fichiers traduits
□ Compiler sur production
□ Redémarrer service
□ Tester https://martialcomp.com/pt/
```

---

## 🎓 POUR APPRENDRE

### Clé API DeepL Gratuite

**Lien** : https://www.deepl.com/pro-api

**Étapes** :
1. Cliquer "Sign up for free"
2. Email + mot de passe
3. Confirmer email
4. Dashboard → Clé API → Copier

**Limites gratuites** :
- 500,000 caractères/mois
- Toutes les langues supportées
- Qualité identique à la version payante

**Pour ce projet** :
- Estimation : ~270,000 caractères pour PT
- Reste largement sous la limite gratuite

### Utilisation de Poedit Pro

**Lien** : https://poedit.net/pro

**Licence** : 29€/an

**Fonctionnalités** :
- Suggestions automatiques (DeepL intégré)
- Validation en temps réel
- Gestion des pluriels
- Recherche/remplacement
- Statistiques

**Raccourcis utiles** :
- `Ctrl+M` : Suggérer traduction
- `Ctrl+F` : Rechercher
- `Ctrl+D` : Marquer comme traduit
- `Ctrl+U` : Marquer comme non traduit

---

## 📞 SUPPORT

Si vous rencontrez des problèmes :

1. **Module non trouvé** : `pip install deepl polib`
2. **Quota dépassé** : Attendre le mois prochain ou upgrade DeepL
3. **Erreur de compilation** : Vérifier encodage UTF-8
4. **Traduction incorrecte** : Réviser manuellement avec Poedit

---

## 🎉 RÉSULTAT ATTENDU

Après toutes les actions :

```
✅ Français : 100% (11,648/11,648)
✅ Espagnol : 100% (11,648/11,648)
✅ Portugais : 100% (11,682/11,682) ← NOUVEAU
✅ Toutes les autres : 100%

SCORE GLOBAL : 100% 🎉
```

---

**Prêt à commencer ? Suivez les étapes dans l'ordre et le portugais sera complet en ~10 heures au lieu de 40 !**
