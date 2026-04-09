# TODOLIST - CONSOLIDATION SYSTÈME DE SCORING

**Date de création :** 3 novembre 2025  
**Objectif :** Consolider et améliorer le système de scoring des compétitions  
**Statut global :** 🟡 En attente

---

## 📋 VUE D'ENSEMBLE

Cette todolist couvre 4 axes principaux :
1. **Consolidation des systèmes** (6 tâches)
2. **Amélioration des notifications** (4 tâches)
3. **Documentation** (4 tâches)
4. **Tests** (4 tâches)

**Total : 18 tâches**

---

## 1️⃣ CONSOLIDATION DES SYSTÈMES DE SCORING

### 📊 Phase 1 : Analyse et évaluation

#### ✅ Tâche 1.1 : Analyse des systèmes existants
**ID :** `consolidation-1`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 3-5 jours

**Description :**
Analyser en profondeur les 3 systèmes de scoring existants pour comprendre :
- `technical_scoring` (apps/competitions/views/technical_scoring.py)
- `standalone_scoring` (apps/competitions/views/standalone_scoring.py)
- `management` (apps/competitions/views/management/scoring.py)

**Sous-tâches :**
- [ ] Comparer les modèles de données de chaque système
- [ ] Identifier les vues et fonctionnalités de chaque système
- [ ] Analyser les URLs et routage
- [ ] Examiner les templates utilisés
- [ ] Comparer les systèmes de calcul de scores
- [ ] Analyser les intégrations WebSocket
- [ ] Créer un tableau comparatif

**Livrables :**
- Document d'analyse comparative
- Tableau de fonctionnalités
- Diagramme d'architecture de chaque système

**Fichiers à analyser :**
```
apps/competitions/views/technical_scoring.py
apps/competitions/views/standalone_scoring.py
apps/competitions/views/management/scoring.py
apps/competitions/models/technical_scoring.py
apps/competitions/models/standalone_scoring.py
apps/competitions/urls/technical_scoring.py
apps/competitions/urls/standalone_scoring.py
```

---

#### ✅ Tâche 1.2 : Identifier les fonctionnalités uniques
**ID :** `consolidation-2`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 2-3 jours

**Description :**
Identifier les fonctionnalités uniques de chaque système qui doivent être préservées lors de la consolidation.

**Sous-tâches :**
- [ ] Lister les fonctionnalités exclusives à `technical_scoring`
- [ ] Lister les fonctionnalités exclusives à `standalone_scoring`
- [ ] Lister les fonctionnalités exclusives à `management`
- [ ] Identifier les fonctionnalités communes
- [ ] Prioriser les fonctionnalités à conserver
- [ ] Documenter les dépendances entre fonctionnalités

**Livrables :**
- Liste des fonctionnalités uniques par système
- Matrice de compatibilité
- Plan de préservation des fonctionnalités

**Exemples de fonctionnalités à vérifier :**
- Système de ranking et snapshots (standalone)
- Gestion des performances (technical)
- Configuration par catégorie (management)
- Intégration WebSocket (tous)
- Système de notification (tous)

---

### 🔨 Phase 2 : Développement du système unifié

#### ✅ Tâche 1.3 : Créer le système de scoring unifié
**ID :** `consolidation-3`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 10-15 jours

**Description :**
Développer un nouveau système de scoring unifié qui intègre toutes les meilleures fonctionnalités des 3 systèmes existants.

**Sous-tâches :**
- [ ] Créer les nouveaux modèles unifiés dans `models/unified_scoring_v2.py`
- [ ] Développer les vues unifiées dans `views/scoring_unified.py`
- [ ] Créer les templates unifiés dans `templates/scoring/unified/`
- [ ] Implémenter l'API de scoring unifiée
- [ ] Intégrer le système WebSocket
- [ ] Créer le système de calcul de scores
- [ ] Implémenter le système de ranking et snapshots
- [ ] Développer l'interface de gestion
- [ ] Créer l'interface juge unifiée
- [ ] Ajouter la gestion des performances
- [ ] Implémenter la configuration par catégorie

**Livrables :**
- Système de scoring unifié fonctionnel
- Modèles de données migrés
- Vues et templates unifiés
- Tests unitaires de base

**Structure proposée :**
```
apps/competitions/
├── models/
│   └── unified_scoring_v2.py      # Nouveaux modèles unifiés
├── views/
│   └── scoring_unified.py         # Vues unifiées
├── templates/
│   └── scoring/
│       └── unified/
│           ├── judge_dashboard.html
│           ├── score_entry.html
│           └── management.html
├── urls/
│   └── scoring_unified.py         # URLs unifiées
└── forms/
    └── scoring_unified.py         # Formulaires unifiés
```

**Points d'attention :**
- Maintenir la compatibilité avec l'existant
- Préserver toutes les fonctionnalités uniques
- Améliorer l'architecture et la maintenabilité
- Documenter chaque composant

---

#### ✅ Tâche 1.4 : Migrer les données existantes
**ID :** `consolidation-4`  
**Priorité :** 🟠 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 5-7 jours

**Description :**
Créer et exécuter les scripts de migration pour transférer toutes les données existantes vers le système unifié.

**Sous-tâches :**
- [ ] Analyser la structure des données existantes
- [ ] Créer le script de migration `technical_scoring` → `unified`
- [ ] Créer le script de migration `standalone_scoring` → `unified`
- [ ] Créer le script de migration `management` → `unified`
- [ ] Créer des backups complets avant migration
- [ ] Tester les migrations sur données de test
- [ ] Valider l'intégrité des données après migration
- [ ] Créer un script de rollback
- [ ] Documenter le processus de migration

**Livrables :**
- Scripts de migration automatisés
- Scripts de validation
- Scripts de rollback
- Documentation du processus

**Scripts à créer :**
```
apps/competitions/management/commands/
├── migrate_technical_to_unified.py
├── migrate_standalone_to_unified.py
├── migrate_management_to_unified.py
├── validate_migration.py
└── rollback_migration.py
```

**Points critiques :**
- Aucune perte de données
- Préservation des relations
- Validation complète
- Possibilité de rollback

---

#### ✅ Tâche 1.5 : Mettre à jour toutes les URLs
**ID :** `consolidation-5`  
**Priorité :** 🟠 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 3-4 jours

**Description :**
Mettre à jour toutes les URLs pour pointer vers le système unifié, en créant des redirections pour l'ancien système.

**Sous-tâches :**
- [ ] Créer les nouvelles URLs unifiées
- [ ] Identifier toutes les références aux anciennes URLs
- [ ] Mettre à jour les liens dans les templates
- [ ] Mettre à jour les vues qui génèrent des URLs
- [ ] Créer des redirections pour les anciennes URLs
- [ ] Mettre à jour les formulaires
- [ ] Mettre à jour les scripts JavaScript
- [ ] Tester toutes les redirections

**Livrables :**
- Nouvelles URLs unifiées fonctionnelles
- Redirections automatiques
- Mise à jour complète des références

**Fichiers à modifier :**
```
apps/competitions/urls/
├── __init__.py                    # Intégrer nouvelles URLs
├── scoring_unified.py             # Nouvelles URLs
└── technical_scoring.py            # Ajouter redirections
    └── standalone_scoring.py      # Ajouter redirections
```

**Nouvelle structure d'URLs proposée :**
```python
# Ancien : /technical-scoring/judge/dashboard/
# Nouveau : /scoring/judge/dashboard/

# Ancien : /standalone-scoring/judge/performances/
# Nouveau : /scoring/judge/performances/

# Ancien : /combat/combats/<id>/interface/
# Nouveau : /scoring/combat/<id>/interface/
```

---

#### ✅ Tâche 1.6 : Déprécier progressivement les anciens systèmes
**ID :** `consolidation-6`  
**Priorité :** 🟢 Faible  
**Statut :** ⏳ En attente  
**Durée estimée :** 2-3 jours

**Description :**
Déprécier progressivement les anciens systèmes en ajoutant des warnings et en planifiant leur suppression.

**Sous-tâches :**
- [ ] Ajouter des warnings de dépréciation dans les anciennes vues
- [ ] Créer une période de transition (ex: 3 mois)
- [ ] Documenter la date de fin de support
- [ ] Ajouter des messages dans les templates anciens
- [ ] Créer un guide de migration pour les utilisateurs
- [ ] Informer les utilisateurs des changements
- [ ] Planifier la suppression complète après transition

**Livrables :**
- Messages de dépréciation
- Documentation de transition
- Plan de suppression

**Timeline proposée :**
- **J+0** : Nouveau système disponible
- **J+30** : Warnings activés
- **J+60** : Support réduit des anciens systèmes
- **J+90** : Dépréciation complète

---

## 2️⃣ AMÉLIORATION DES NOTIFICATIONS AUX JUGES

### 📧 Phase 1 : Système de notifications automatiques

#### ✅ Tâche 2.1 : Créer le système de notifications automatiques
**ID :** `notifications-1`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 5-7 jours

**Description :**
Implémenter un système de notifications automatiques lors de l'assignation de juges à des compétitions/catégories.

**Sous-tâches :**
- [ ] Créer le modèle `JudgeAssignmentNotification` dans `models/notifications.py`
- [ ] Créer un signal Django pour détecter les nouvelles assignations
- [ ] Implémenter le système de notifications in-app
- [ ] Créer le template de notification
- [ ] Ajouter l'API pour marquer les notifications comme lues
- [ ] Intégrer avec le système de notifications existant
- [ ] Créer une interface de gestion des notifications

**Livrables :**
- Système de notifications in-app fonctionnel
- Templates de notifications
- API de gestion des notifications

**Fichiers à créer/modifier :**
```
apps/competitions/
├── models/
│   └── notifications.py           # Modèles de notifications
├── signals.py                      # Signal pour assignations
├── services/
│   └── notification_service.py    # Service de notifications
└── templates/
    └── notifications/
        └── judge_assignment.html
```

**Fonctionnalités :**
- Notification immédiate lors d'assignation
- Liste des notifications dans le dashboard
- Marquage comme lu/non lu
- Suppression des notifications

---

#### ✅ Tâche 2.2 : Implémenter l'envoi d'emails avec liens directs
**ID :** `notifications-2`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 4-5 jours

**Description :**
Créer un système d'envoi d'emails automatiques lors de l'assignation, avec des liens directs vers les templates de notation.

**Sous-tâches :**
- [ ] Créer le template d'email `judge_assignment_email.html`
- [ ] Implémenter la fonction d'envoi d'email dans `services/email_service.py`
- [ ] Ajouter les liens directs vers les templates de notation
- [ ] Personnaliser le contenu de l'email (compétition, catégorie, performances)
- [ ] Gérer les erreurs d'envoi (retry, logs)
- [ ] Créer un système de préférences (email ou non)
- [ ] Tester l'envoi avec différents clients email
- [ ] Ajouter un lien de désinscription

**Livrables :**
- Système d'envoi d'emails fonctionnel
- Templates d'emails personnalisés
- Gestion des préférences utilisateur

**Template d'email proposé :**
```html
Sujet : Vous avez été assigné comme juge - {{ competition.name }}

Bonjour {{ judge.first_name }},

Vous avez été assigné comme juge pour la compétition "{{ competition.name }}".

Catégorie : {{ category.name }}
Date : {{ competition.date }}

Accédez directement à votre interface de notation :
👉 https://example.com/scoring/judge/competition/{{ competition.id }}/category/{{ category.id }}/

Liste des performances à noter :
{{ performances_list }}

Cordialement,
L'équipe de gestion des compétitions
```

**Fichiers à créer/modifier :**
```
apps/competitions/
├── services/
│   └── email_service.py
├── templates/
│   └── emails/
│       └── judge_assignment.html
└── forms/
    └── judge_preferences.py        # Préférences notifications
```

---

#### ✅ Tâche 2.3 : Créer un dashboard personnalisé avec notifications
**ID :** `notifications-3`  
**Priorité :** 🟠 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 5-6 jours

**Description :**
Améliorer le dashboard des juges avec un système de notifications in-app complet.

**Sous-tâches :**
- [ ] Redesigner le dashboard juge avec section notifications
- [ ] Ajouter un compteur de notifications non lues
- [ ] Créer une liste des notifications récentes
- [ ] Implémenter le marquage rapide comme lu
- [ ] Ajouter des filtres (toutes, non lues, par type)
- [ ] Créer des notifications pour événements importants
- [ ] Ajouter des notifications push (si possible)
- [ ] Intégrer avec le système de notifications email

**Livrables :**
- Dashboard amélioré avec notifications
- Interface de gestion des notifications
- Système de filtres et recherche

**Fonctionnalités du dashboard :**
- Badge avec nombre de notifications non lues
- Liste déroulante des notifications récentes
- Popup de notification pour nouvelles assignations
- Liens directs vers les actions (noter, consulter)
- Historique des notifications

**Fichiers à modifier :**
```
apps/competitions/
├── templates/
│   └── scoring/
│       └── unified/
│           └── judge_dashboard.html    # Améliorer avec notifications
└── views/
    └── scoring_unified.py              # Ajouter logique notifications
```

---

#### ✅ Tâche 2.4 : Notifications pour performances à venir
**ID :** `notifications-4`  
**Priorité :** 🟡 Moyenne-Faible  
**Statut :** ⏳ En attente  
**Durée estimée :** 3-4 jours

**Description :**
Créer un système de notifications pour informer les juges des performances à venir.

**Sous-tâches :**
- [ ] Créer le système de rappels (X minutes/heures avant)
- [ ] Implémenter les notifications "performance à venir"
- [ ] Ajouter les liens directs vers le template de notation
- [ ] Créer des notifications pour les performances en cours
- [ ] Ajouter des notifications pour les performances manquées
- [ ] Implémenter les préférences de rappel

**Livrables :**
- Système de rappels fonctionnel
- Notifications pour performances à venir
- Gestion des performances manquées

**Exemple de notification :**
```
📢 Performance à noter dans 15 minutes

Participant : {{ practitioner.full_name }}
Catégorie : {{ category.name }}
Ordre : {{ performance.order }}

👉 Noter maintenant
```

---

## 3️⃣ DOCUMENTATION DES TEMPLATES

### 📚 Phase 1 : Documentation technique

#### ✅ Tâche 3.1 : Documenter chaque template
**ID :** `documentation-1`  
**Priorité :** 🟠 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 7-10 jours

**Description :**
Créer une documentation complète pour chaque template de notation avec usage, paramètres et exemples.

**Sous-tâches :**
- [ ] Inventorier tous les templates de notation
- [ ] Créer un template de documentation standardisé
- [ ] Documenter `judge_score_performance.html` (template principal scoring)
- [ ] Documenter `interface_combat.html` (template principal combat)
- [ ] Documenter tous les templates de scoring technique
- [ ] Documenter tous les templates de combat
- [ ] Documenter tous les templates standalone
- [ ] Documenter les templates de management
- [ ] Ajouter des exemples d'utilisation
- [ ] Ajouter des schémas et diagrammes
- [ ] Créer un index de tous les templates

**Livrables :**
- Documentation complète de chaque template
- Guide de référence rapide
- Index de tous les templates

**Structure de documentation proposée :**
```markdown
# Template : judge_score_performance.html

## Description
Interface principale pour noter une performance technique.

## Localisation
`apps/competitions/templates/competitions/technical_scoring/judge_score_performance.html`

## URL associée
`/technical-scoring/performance/<performance_id>/score/`

## Paramètres du contexte
- `practitioner` : Pratiquant à noter
- `competition` : Compétition
- `category` : Catégorie
- `criteria` : Liste des critères
- `forms` : Formulaires par critère
- `config` : Configuration de scoring

## Exemple d'utilisation
[Code exemple]

## Dépendances
- CSS : scoring.css
- JS : scoring.js

## Notes
[Notes importantes]
```

**Fichiers à créer :**
```
docs/
└── templates/
    ├── index.md                    # Index général
    ├── scoring_technical.md        # Templates scoring technique
    ├── scoring_combat.md           # Templates combat
    └── scoring_management.md        # Templates management
```

---

#### ✅ Tâche 3.2 : Créer un guide utilisateur pour les juges
**ID :** `documentation-2`  
**Priorité :** 🟠 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 4-5 jours

**Description :**
Créer un guide utilisateur complet et accessible pour les juges expliquant comment utiliser le système de notation.

**Sous-tâches :**
- [ ] Créer la structure du guide utilisateur
- [ ] Section : Comment accéder au système
- [ ] Section : Comment noter une performance technique
- [ ] Section : Comment noter un combat en temps réel
- [ ] Section : Comprendre les critères de notation
- [ ] Section : Soumettre les scores
- [ ] Section : Consulter l'historique
- [ ] Section : Gérer les notifications
- [ ] Ajouter des captures d'écran
- [ ] Créer des tutoriels vidéo (optionnel)
- [ ] Traduire en plusieurs langues si nécessaire

**Livrables :**
- Guide utilisateur complet
- Version HTML accessible
- Version PDF téléchargeable

**Structure du guide :**
```
docs/
└── user_guide/
    ├── index.md                    # Introduction
    ├── getting_started.md          # Débuter
    ├── scoring_technical.md         # Notation technique
    ├── scoring_combat.md            # Notation combat
    ├── criteria.md                  # Critères
    ├── submissions.md               # Soumission
    ├── history.md                   # Historique
    └── notifications.md              # Notifications
```

**Points à couvrir :**
- Connexion et accès au dashboard
- Navigation dans les compétitions assignées
- Processus de notation étape par étape
- Compréhension des critères
- Validation et soumission
- Résolution de problèmes courants

---

#### ✅ Tâche 3.3 : Identifier et marquer les templates obsolètes
**ID :** `documentation-3`  
**Priorité :** 🟡 Moyenne-Faible  
**Statut :** ⏳ En attente  
**Durée estimée :** 2-3 jours

**Description :**
Identifier les templates obsolètes, les marquer clairement et planifier leur suppression.

**Sous-tâches :**
- [ ] Analyser l'utilisation de chaque template
- [ ] Identifier les templates non référencés
- [ ] Identifier les templates dupliqués
- [ ] Vérifier les templates de backup
- [ ] Créer une liste des templates obsolètes
- [ ] Ajouter des warnings dans les templates obsolètes
- [ ] Déplacer les templates obsolètes vers un dossier `deprecated/`
- [ ] Documenter les templates obsolètes et leur remplacement
- [ ] Planifier la suppression après période de transition

**Livrables :**
- Liste des templates obsolètes
- Warnings de dépréciation
- Plan de suppression

**Templates suspects identifiés :**
```
apps/competitions/templates/competitions/
├── combat_taekwondo/               # Ancien module ?
├── *.backup_*                       # Backups
└── management/                     # Vérifier usage
```

**Actions proposées :**
1. Déplacer vers `deprecated/`
2. Ajouter un commentaire dans le template
3. Créer une redirection si nécessaire
4. Supprimer après 3 mois

---

#### ✅ Tâche 3.4 : Créer une documentation technique pour développeurs
**ID :** `documentation-4`  
**Priorité :** 🟡 Moyenne-Faible  
**Statut :** ⏳ En attente  
**Durée estimée :** 5-6 jours

**Description :**
Créer une documentation technique complète pour les développeurs incluant architecture, API, et exemples de code.

**Sous-tâches :**
- [ ] Documenter l'architecture du système unifié
- [ ] Documenter les modèles de données
- [ ] Documenter l'API de scoring
- [ ] Documenter les endpoints WebSocket
- [ ] Créer des exemples de code
- [ ] Documenter les tests
- [ ] Créer un guide de contribution
- [ ] Documenter les conventions de code
- [ ] Créer des diagrammes d'architecture
- [ ] Documenter le système de migration

**Livrables :**
- Documentation technique complète
- API Reference
- Guide de développement

**Structure proposée :**
```
docs/
└── technical/
    ├── architecture.md             # Architecture système
    ├── models.md                    # Modèles de données
    ├── api.md                       # API Reference
    ├── websocket.md                 # WebSocket API
    ├── examples/                    # Exemples de code
    │   ├── create_scoring.py
    │   ├── assign_judge.py
    │   └── submit_score.py
    ├── testing.md                   # Guide de tests
    └── contributing.md             # Guide de contribution
```

---

## 4️⃣ TESTS DU FLUX COMPLET

### 🧪 Phase 1 : Tests unitaires

#### ✅ Tâche 4.1 : Tests unitaires pour chaque template
**ID :** `tests-1`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 7-10 jours

**Description :**
Créer des tests unitaires complets pour chaque template de notation.

**Sous-tâches :**
- [ ] Créer la structure de tests
- [ ] Tests pour `judge_score_performance.html`
- [ ] Tests pour `interface_combat.html`
- [ ] Tests pour `scoring_interface.html`
- [ ] Tests pour tous les templates de scoring technique
- [ ] Tests pour tous les templates de combat
- [ ] Tests pour les templates standalone
- [ ] Tests de validation des formulaires
- [ ] Tests de rendu des templates
- [ ] Tests d'intégration avec les vues

**Livrables :**
- Suite complète de tests unitaires
- Couverture de code > 80%
- Documentation des tests

**Structure de tests :**
```
apps/competitions/tests/
├── __init__.py
├── test_scoring_templates.py       # Tests templates scoring
├── test_combat_templates.py         # Tests templates combat
├── test_forms.py                   # Tests formulaires
└── fixtures/
    └── scoring_data.json           # Données de test
```

**Points à tester :**
- Rendu correct des templates
- Affichage des données
- Validation des formulaires
- Gestion des erreurs
- Liens et redirections
- Intégration JavaScript

---

### 🔄 Phase 2 : Tests d'intégration

#### ✅ Tâche 4.2 : Tests d'intégration pour le flux d'assignation
**ID :** `tests-2`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 5-7 jours

**Description :**
Créer des tests d'intégration pour valider le flux complet d'assignation de juges.

**Sous-tâches :**
- [ ] Test : Assignation d'un juge à une catégorie
- [ ] Test : Notification envoyée après assignation
- [ ] Test : Juge voit la compétition dans son dashboard
- [ ] Test : Accès aux templates de notation
- [ ] Test : Soumission de scores
- [ ] Test : Calcul des résultats
- [ ] Test : Affichage des résultats
- [ ] Test : Scénarios d'erreur
- [ ] Test : Cas limites (plusieurs juges, etc.)

**Livrables :**
- Suite de tests d'intégration
- Scénarios de test documentés
- Rapport de couverture

**Scénarios de test :**
```
1. Assignation simple
   Admin → Assigner juge → Notification → Juge voit compétition

2. Assignation multiple
   Admin → Assigner plusieurs juges → Tous reçoivent notification

3. Assignation avec performances
   Admin → Assigner → Juge voit performances → Peut noter

4. Flux complet
   Assignation → Notification → Accès → Notation → Soumission → Résultats
```

---

#### ✅ Tâche 4.3 : Tester le flux complet end-to-end
**ID :** `tests-3`  
**Priorité :** 🔴 Haute  
**Statut :** ⏳ En attente  
**Durée estimée :** 4-5 jours

**Description :**
Tester manuellement et automatiquement le flux complet depuis l'assignation jusqu'à la soumission des scores.

**Sous-tâches :**
- [ ] Créer un scénario de test end-to-end
- [ ] Test manuel : Assignation → Notification → Accès → Notation → Soumission
- [ ] Test automatique avec Selenium/Cypress
- [ ] Test avec plusieurs juges simultanés
- [ ] Test avec plusieurs performances
- [ ] Test du système de combat en temps réel
- [ ] Test des notifications en temps réel
- [ ] Test de récupération après erreur
- [ ] Documenter les résultats

**Livrables :**
- Scénarios de test end-to-end
- Tests automatisés fonctionnels
- Rapport de test

**Flux complet à tester :**
```
1. ADMINISTRATEUR
   ├─ Créer compétition
   ├─ Créer catégorie
   ├─ Configurer critères de notation
   ├─ Assigner juges à catégorie
   └─ Créer performances

2. SYSTÈME
   ├─ Envoie notifications aux juges
   ├─ Ajoute compétition au dashboard juge
   └─ Prépare templates de notation

3. JUGE 1
   ├─ Reçoit notification (email + in-app)
   ├─ Accède au dashboard
   ├─ Voit compétition assignée
   ├─ Clique sur "Noter"
   ├─ Accède au template de notation
   ├─ Remplit la grille de notation
   └─ Soumet les scores

4. JUGE 2
   └─ (Même processus)

5. SYSTÈME
   ├─ Reçoit scores de tous les juges
   ├─ Calcule les résultats agrégés
   ├─ Applique les pondérations
   └─ Affiche les résultats

6. ADMINISTRATEUR
   ├─ Consulte les résultats
   └─ Publie si nécessaire
```

**Outils proposés :**
- **Selenium** : Tests automatisés navigateur
- **Django TestCase** : Tests backend
- **Cypress** : Tests E2E modernes (alternative)
- **Postman** : Tests API

---

#### ✅ Tâche 4.4 : Tests de charge pour le temps réel
**ID :** `tests-4`  
**Priorité :** 🟡 Moyenne  
**Statut :** ⏳ En attente  
**Durée estimée :** 3-4 jours

**Description :**
Créer des tests de charge pour valider les performances du système en temps réel avec plusieurs juges simultanés.

**Sous-tâches :**
- [ ] Créer des scripts de charge pour WebSocket
- [ ] Test : 10 juges simultanés notant
- [ ] Test : 50 juges simultanés
- [ ] Test : 100 juges simultanés
- [ ] Test : Système de combat avec 20 observateurs
- [ ] Mesurer les temps de réponse
- [ ] Identifier les goulots d'étranglement
- [ ] Optimiser si nécessaire
- [ ] Documenter les résultats

**Livrables :**
- Scripts de test de charge
- Rapport de performances
- Recommandations d'optimisation

**Métriques à mesurer :**
- Temps de réponse des templates
- Latence WebSocket
- Temps de calcul des scores
- Utilisation mémoire/CPU
- Nombre de connexions simultanées supportées

**Outils proposés :**
- **Locust** : Tests de charge Python
- **JMeter** : Tests de charge (alternative)
- **Django Debug Toolbar** : Profiling
- **New Relic / Sentry** : Monitoring production

---

## 📊 RÉSUMÉ ET PRIORISATION

### Ordre d'exécution recommandé

#### **Phase 1 : Fondations (Semaines 1-3)**
1. ✅ consolidation-1 : Analyse des systèmes (3-5 jours)
2. ✅ consolidation-2 : Identifier fonctionnalités uniques (2-3 jours)
3. ✅ documentation-1 : Documenter templates (7-10 jours) *En parallèle*
4. ✅ tests-1 : Tests unitaires (7-10 jours) *En parallèle*

#### **Phase 2 : Développement (Semaines 4-7)**
5. ✅ consolidation-3 : Système unifié (10-15 jours)
6. ✅ notifications-1 : Système notifications (5-7 jours) *En parallèle*
7. ✅ notifications-2 : Emails avec liens (4-5 jours) *En parallèle*

#### **Phase 3 : Migration et améliorations (Semaines 8-10)**
8. ✅ consolidation-4 : Migration données (5-7 jours)
9. ✅ consolidation-5 : Mise à jour URLs (3-4 jours)
10. ✅ notifications-3 : Dashboard amélioré (5-6 jours)
11. ✅ tests-2 : Tests intégration (5-7 jours)

#### **Phase 4 : Finalisation (Semaines 11-12)**
12. ✅ tests-3 : Tests E2E (4-5 jours)
13. ✅ notifications-4 : Notifications performances (3-4 jours)
14. ✅ documentation-2 : Guide utilisateur (4-5 jours)
15. ✅ documentation-4 : Doc technique (5-6 jours)
16. ✅ tests-4 : Tests de charge (3-4 jours)

#### **Phase 5 : Nettoyage (Semaines 13-14)**
17. ✅ documentation-3 : Marquer templates obsolètes (2-3 jours)
18. ✅ consolidation-6 : Dépréciation anciens systèmes (2-3 jours)

---

## 📈 MÉTRIQUES DE SUCCÈS

### Objectifs quantitatifs
- ✅ 100% des templates documentés
- ✅ 100% des fonctionnalités préservées après migration
- ✅ 100% de couverture de tests pour templates critiques
- ✅ 0 perte de données lors de la migration
- ✅ < 2 secondes de temps de réponse pour les templates de notation
- ✅ Support de 50+ juges simultanés

### Objectifs qualitatifs
- ✅ Système unifié plus maintenable
- ✅ Expérience utilisateur améliorée pour les juges
- ✅ Documentation complète et accessible
- ✅ Système testé et fiable

---

## 🚨 RISQUES IDENTIFIÉS

### Risques techniques
1. **Perte de données lors de la migration**
   - *Mitigation :* Backups complets, scripts de validation, rollback

2. **Régression de fonctionnalités**
   - *Mitigation :* Tests complets, période de transition, tests de régression

3. **Performance dégradée**
   - *Mitigation :* Tests de charge, optimisation, monitoring

### Risques utilisateurs
1. **Résistance au changement**
   - *Mitigation :* Communication, formation, période de transition

2. **Confusion pendant la transition**
   - *Mitigation :* Documentation claire, support, migration progressive

---

## 📝 NOTES IMPORTANTES

- Toutes les tâches doivent être validées par l'équipe avant de commencer
- Les backups sont obligatoires avant toute migration
- La communication avec les utilisateurs est essentielle
- Les tests doivent être exécutés à chaque étape
- La documentation doit être mise à jour en continu

---

**Dernière mise à jour :** 3 novembre 2025  
**Responsable projet :** À définir  
**Statut global :** 🟡 Prêt à commencer
