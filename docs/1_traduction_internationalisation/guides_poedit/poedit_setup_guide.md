# Configuration Poedit pour MartialComp

## 1. Installation Poedit
- Téléchargez depuis : https://poedit.net/
- Version recommandée : Poedit Pro (essai gratuit 30 jours)

## 2. Configuration initiale

### A. Nouveau catalogue
1. **Fichier** → **Nouveau catalogue**
2. **Langue de traduction** : Choisir (Espagnol, Portugais, ou Norvégien)
3. **Langue source** : Français
4. **Domaine de traduction** : `django`

### B. Propriétés du projet
**Catalogue** → **Propriétés**

```
Informations du projet :
- Nom du projet : MartialComp
- Version : 1.0
- Équipe de traduction : [Votre nom]
- Email : [Votre email]
- Charset : UTF-8
- Plural-Forms : nplurals=2; plural=(n != 1);
```

### C. Chemins et mots-clés
**Onglet "Chemins sources"** :
```
Chemin de base : /mnt/c/martial_hub_django/martialcomp
Chemins :
- .
- competitions
- organizations
- grades
- finances
- shop
- documents

Exclusions :
- venv
- __pycache__
- .git
- node_modules
- static
- media
```

**Onglet "Mots-clés"** :
```
Mots-clés Django à ajouter :
- _
- gettext
- gettext_lazy
- gettext_noop
- ngettext
- ngettext_lazy
- ugettext
- ugettext_lazy
- ungettext
- ungettext_lazy
- trans
- blocktrans
```

## 3. Fichiers à ouvrir dans Poedit

### Espagnol
```
Fichier : /mnt/c/martial_hub_django/martialcomp/locale/es/LC_MESSAGES/django.po
Lignes : 1382 entrées
Taille : ~27KB compilé
```

### Portugais  
```
Fichier : /mnt/c/martial_hub_django/martialcomp/locale/pt/LC_MESSAGES/django.po
Lignes : 1268 entrées
Taille : ~23KB compilé
```

### Norvégien
```
Fichier : /mnt/c/martial_hub_django/martialcomp/locale/no/LC_MESSAGES/django.po
Lignes : 1331 entrées
Taille : ~26KB compilé
```

## 4. Workflow de traduction recommandé

### Étape 1: Ouvrir le fichier
1. **Fichier** → **Ouvrir** → Sélectionner le fichier `.po`
2. Poedit détectera automatiquement la langue

### Étape 2: Trier et filtrer
- **Affichage** → **Trier par** → "État de traduction"
- Commencer par les entrées **non traduites** (rouge)
- Puis les entrées **floues** (jaune)

### Étape 3: Sections prioritaires
1. **Navigation** (Accueil, Contact, À propos)
2. **Authentification** (Connexion, Inscription)
3. **Rôles** (Club, Fédération, Arbitre)
4. **Fonctionnalités principales**
5. **FAQ et descriptions**

### Étape 4: Validation
- **Catalogue** → **Valider** (Ctrl+V)
- Corriger les erreurs signalées
- **Catalogue** → **Mise à jour depuis les sources**

## 5. Raccourcis clavier utiles

```
Ctrl+Enter     : Valider et passer au suivant
Ctrl+Shift+A   : Marquer comme traduit
Ctrl+U         : Marquer comme flou
F1             : Aide contextuelle
Ctrl+F         : Rechercher
Ctrl+Shift+F   : Rechercher dans les traductions
Ctrl+S         : Sauvegarder
```

## 6. Fonctionnalités avancées Poedit Pro

### Suggestions automatiques
- **DeepL** : Traductions de qualité
- **Google Translate** : Suggestions de base
- **Mémoire de traduction** : Réutilise vos traductions précédentes

### Validation
- **Vérifications automatiques** : Ponctuation, variables, cohérence
- **Glossaire** : Terminologie spécialisée

## 7. Compilation automatique
Poedit compile automatiquement en `.mo` lors de la sauvegarde.

## 8. Sauvegarde et versioning
```bash
# Avant de commencer
cp locale/ locale_backup_$(date +%Y%m%d)/

# Après chaque session
git add locale/
git commit -m "Traductions [langue]: [section traduite]"
```

## 9. Test des traductions
Après modification :
```bash
cd /mnt/c/martial_hub_django/martialcomp
python manage.py runserver
# Tester sur http://localhost:8000/es/ (pour espagnol)
```

## 10. Glossaire recommandé MartialComp

| Français | Espagnol | Portugais | Norvégien |
|----------|----------|-----------|-----------|
| Compétition | Competición | Competição | Konkurranse |
| Arts martiaux | Artes marciales | Artes marciais | Kampsport |
| Fédération | Federación | Federação | Forbund |
| Arbitre | Árbitro | Árbitro | Dommer |
| Grade/Ceinture | Grado/Cinturón | Graduação/Faixa | Grad/Belte |
| Inscription | Inscripción | Inscrição | Påmelding |
| Tableau de bord | Panel de control | Painel de controle | Kontrollpanel |

## Support
En cas de problème :
1. Documentation Poedit : https://poedit.net/trac/wiki
2. Documentation Django i18n : https://docs.djangoproject.com/en/stable/topics/i18n/