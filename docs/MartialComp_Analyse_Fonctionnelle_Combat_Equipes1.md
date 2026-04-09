# MARTIALCOMP - Analyse Fonctionnelle
## Module de Gestion des Combats
### Compétitions Individuelles & Par Équipes

---

| Information | Valeur |
|-------------|--------|
| **Document** | Analyse Fonctionnelle - Gestion des Combats |
| **Version** | 1.1 |
| **Date** | 9 décembre 2025 |
| **Statut** | À valider |
| **Priorité** | 🔴 Haute |

---

## 1. Résumé Exécutif

### 1.1 Contexte

Le module Combat de MartialComp gère actuellement les compétitions de combat (assauts, kumité, randori, etc.) avec une structure basique. Suite aux retours de la compétition **Zone Nord du 6 décembre 2025** et à l'analyse des besoins métier, une refonte majeure est nécessaire pour supporter les compétitions par équipes et améliorer la gestion des phases de compétition.

### 1.2 Objectifs

- Supporter les deux modes de compétition : **Individuel** et **Par Équipes**
- Permettre une configuration flexible des équipes (composition, remplaçants)
- Automatiser le basculement Équipe → Individuel si conditions non remplies
- **Gérer les mécanismes d'entente et de fusion d'équipes**
- Gérer les phases de poules, élimination directe et finale
- **Afficher clairement l'état des matchs dans les tableaux de poules**
- Afficher les résultats avec tous les membres de l'équipe au podium

### 1.3 Périmètre

| ✅ Dans le périmètre | ❌ Hors périmètre |
|----------------------|-------------------|
| Configuration des équipes | Streaming vidéo |
| Génération des poules | Application mobile arbitre |
| Gestion des matchs | Intégration fédérations externes |
| Basculement automatique | Statistiques avancées IA |
| **Ententes entre équipes** | |
| **Fusion d'équipes** | |
| Consolidation des points | |
| **Affichage état matchs (couleurs)** | |
| Affichage podium équipe | |

---

## 2. Exigences Fonctionnelles

### 2.1 Types de Compétition Combat

Le système doit supporter deux modes de compétition distincts avec des règles de gestion spécifiques :

| Type | Description | Caractéristiques |
|------|-------------|------------------|
| **INDIVIDUEL** | Chaque combattant participe en son nom propre | • 1 combattant par match<br>• Classement individuel<br>• Podium : 1 personne |
| **PAR ÉQUIPES** | Les combattants participent au sein d'une équipe (club, région, etc.) | • N combattants par équipe<br>• Classement par équipe<br>• Podium : tous les membres |

### 2.2 Configuration des Équipes

La composition des équipes doit être **configurable** selon les règlements de la compétition. Les formats standards sont :

| Format | Titulaires | Remplaçants | Total Max |
|--------|------------|-------------|-----------|
| **2+1** | 2 | 0 à 1 (optionnel) | 3 |
| **3+1** | 3 | 0 à 1 (optionnel) | 4 |
| **3+2** | 3 | 0 à 2 (optionnel) | 5 |
| **5+2** | 5 | 0 à 2 (optionnel) | 7 |
| *Personnalisé* | N (configurable) | M (configurable) | N + M |

> **Note importante** : Les remplaçants sont toujours **optionnels** par défaut. L'organisateur peut les rendre obligatoires via la configuration.

---

### 2.3 Liste des Exigences Détaillées

#### REQ-01 : Basculement Automatique Équipe → Individuel

**Description** : Lorsqu'une compétition par équipes ne remplit pas les conditions minimales requises, le système doit automatiquement proposer ou effectuer un basculement vers une compétition individuelle.

**Conditions de déclenchement** :
- Nombre d'équipes inscrites insuffisant (< seuil configurable, par défaut 3)
- Équipes incomplètes ne respectant pas le nombre minimum de titulaires
- Déclenchement manuel par l'organisateur

**Actions du système** :
1. Afficher une alerte avec proposition de basculement
2. Sur confirmation, dissoudre les équipes existantes
3. Convertir chaque membre d'équipe en participant individuel
4. Générer automatiquement les nouvelles poules individuelles
5. Conserver l'historique de l'équipe d'origine (traçabilité)

**Critères d'acceptation** :
- [ ] L'alerte s'affiche automatiquement quand conditions non remplies
- [ ] Le basculement préserve toutes les inscriptions des combattants
- [ ] L'historique de l'équipe d'origine est conservé en base

---

#### REQ-02 : Affichage des Équipes par Catégorie

**Description** : Le système doit afficher clairement toutes les équipes regroupées par catégorie de compétition.

**Informations à afficher pour chaque équipe** :
- Nom de l'équipe
- Club d'appartenance
- Liste des membres (titulaires et remplaçants différenciés)
- **Indication des membres en entente (provenant d'autres clubs)**
- Statut de validation (complète / incomplète)
- Indicateur visuel si l'équipe ne remplit pas les conditions

**Maquette fonctionnelle** :

```
┌─────────────────────────────────────────────────────────────┐
│ CATÉGORIE : Kumité Senior Masculin -75kg                    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌─────────────────────┐            │
│ │ 🟢 Équipe Alpha     │  │ 🟡 Équipe Beta      │            │
│ │ Club: Karaté Lyon   │  │ Club: Judo Paris    │            │
│ │ ─────────────────── │  │ ─────────────────── │            │
│ │ Titulaires (3/3):   │  │ Titulaires (3/3):   │            │
│ │ • Jean Dupont       │  │ • Marc Martin       │            │
│ │ • Paul Bernard      │  │ • Luc Durand        │            │
│ │ • Pierre Moreau     │  │ • 🤝 Alex Petit*    │            │
│ │ ─────────────────── │  │ ─────────────────── │            │
│ │ Remplaçants (1/2):  │  │ Remplaçants (0/2):  │            │
│ │ • Alex Petit        │  │ • [Optionnel]       │            │
│ │ ─────────────────── │  │ ─────────────────── │            │
│ │ ✅ Équipe complète  │  │ ✅ Équipe complète  │            │
│ │                     │  │ 🤝 1 entente        │            │
│ └─────────────────────┘  └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
  * = Membre en entente (Club origine: Karaté Lyon)
```

**Critères d'acceptation** :
- [ ] Les équipes sont groupées par catégorie
- [ ] Les titulaires et remplaçants sont visuellement distincts
- [ ] **Les membres en entente sont clairement identifiés avec leur club d'origine**
- [ ] Un indicateur clair montre le statut de validation

---

#### REQ-03 : Basculement Manuel du Type de Compétition

**Description** : L'organisateur doit pouvoir basculer manuellement le type de compétition dans les deux sens.

**Transitions possibles** :

| Transition | Action système |
|------------|----------------|
| ÉQUIPE → INDIVIDUEL | Dissolution des équipes, récupération des membres comme participants individuels |
| INDIVIDUEL → ÉQUIPE | Interface de formation d'équipes à partir des participants inscrits |

**Contrainte** : Le basculement n'est autorisé que si **aucun combat n'a encore démarré**.

**Critères d'acceptation** :
- [ ] Bouton de basculement visible uniquement avant le premier combat
- [ ] Confirmation obligatoire avec récapitulatif des impacts
- [ ] Journalisation de l'action (qui, quand, pourquoi)

---

#### REQ-04 : Gestion des Poules et Matchs

**Description** : Le système doit gérer l'intégralité du parcours compétitif, des poules jusqu'à la finale.

**Phases de compétition** :

| Phase | Description |
|-------|-------------|
| **1. Poules** | Génération automatique des poules (round-robin), affichage clair des matchs de chaque poule, calcul automatique des points (victoire, égalité, défaite) |
| **2. Classement** | Classement automatique par poule, critères : Points > Différence > Confrontation directe, qualification des N premiers de chaque poule |
| **3. Élimination** | Tableau d'élimination directe (bracket), seeding basé sur le classement des poules, option : repêchage pour la 3ème place |
| **4. Finale** | Match pour la 1ère place, petite finale pour la 3ème place (si activée), proclamation des résultats et génération du podium |

**Diagramme de flux** :

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   POULES     │────▶│  CLASSEMENT  │────▶│ ÉLIMINATION  │────▶│   FINALE     │
│  Round-Robin │     │  par poule   │     │   Bracket    │     │   Podium     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
 Tous vs Tous         Top N qualifiés      1/4, 1/2 finale     1ère, 2ème, 3ème
```

**Critères d'acceptation** :
- [ ] Les poules se génèrent automatiquement selon le nombre d'équipes/participants
- [ ] Le classement se met à jour en temps réel après chaque combat
- [ ] Le bracket d'élimination se génère automatiquement après les poules
- [ ] La petite finale est optionnelle (configurable)

---

#### REQ-05 : Affichage du Podium Équipe Complet

**Description** : Pour les compétitions par équipes, le podium doit afficher **TOUS les membres** de l'équipe gagnante, pas uniquement le nom de l'équipe.

**Éléments à afficher** :
- Nom de l'équipe et classement (1ère, 2ème, 3ème place)
- Photo de groupe (si disponible)
- Liste nominative de tous les membres :
  - 🥋 Titulaires ayant combattu
  - 🔄 Remplaçants ayant combattu
  - 👥 Remplaçants n'ayant pas combattu (mention spéciale)
  - **🤝 Membres en entente (avec club d'origine)**
- Club d'appartenance

**Maquette fonctionnelle** :

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🏆 PODIUM ÉQUIPES                            │
│                     Kumité Senior Masculin                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                         ┌───────────┐                               │
│                         │  🥇 1ER   │                               │
│                         │  ÉQUIPE   │                               │
│            ┌───────────┐│   ALPHA   │┌───────────┐                  │
│            │  🥈 2ÈME  ││           ││  🥉 3ÈME  │                  │
│            │  ÉQUIPE   ││  ───────  ││  ÉQUIPE   │                  │
│            │   BETA    ││ J. Dupont ││   GAMMA   │                  │
│            │           ││ P. Bernard││           │                  │
│            │  ───────  ││ P. Moreau ││  ───────  │                  │
│            │ M. Martin ││ 🤝A.Petit*││ T. Leroy  │                  │
│            │ L. Durand ││           ││ S. Simon  │                  │
│            └───────────┘└───────────┘└───────────┘                  │
│                                                                     │
│  * = Remplaçant ayant combattu                                      │
│  🤝 = Membre en entente (Club Judo Paris)                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Critères d'acceptation** :
- [ ] Tous les membres de l'équipe sont listés nominativement
- [ ] Les rôles (titulaire/remplaçant) sont identifiables
- [ ] L'indication "a combattu" ou "n'a pas combattu" est visible
- [ ] **Les membres en entente sont identifiés avec leur club d'origine**

---

#### REQ-06 : Mécanisme d'Entente 🆕

**Description** : Le système doit permettre d'intégrer un membre d'une équipe adverse (ou d'un autre club) dans une équipe, selon le mécanisme d'**entente** courant dans les sports d'équipe.

**Cas d'usage** :
- Une équipe n'a pas assez de membres dans une catégorie
- Un club souhaite "prêter" un combattant à un autre club
- Création d'équipes mixtes inter-clubs pour certaines compétitions

**Règles métier** :

| Règle | Description |
|-------|-------------|
| **Limite par équipe** | Maximum N membres en entente par équipe (configurable, défaut: 2) |
| **Exclusivité** | Un combattant ne peut être en entente que dans UNE seule équipe par compétition |
| **Traçabilité** | Le club d'origine du membre en entente est toujours affiché |
| **Validation** | L'entente doit être validée par l'organisateur (optionnel selon config) |
| **Priorité** | Un membre en entente ne peut pas remplacer un titulaire de son équipe d'origine |

**Workflow d'entente** :

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   DEMANDE    │────▶│  VALIDATION  │────▶│ INTÉGRATION  │────▶│   ACTIF      │
│   d'entente  │     │ (si requis)  │     │  à l'équipe  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
 Équipe A demande    Organisateur        Membre visible       Peut combattre
 membre de Équipe B  approuve/refuse     dans Équipe A        pour Équipe A
```

**Maquette - Interface de gestion des ententes** :

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🤝 GESTION DES ENTENTES                          │
│                    Équipe Alpha - Karaté Lyon                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Membres actuels en entente (1/2) :                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🤝 Alex Petit                                                │   │
│  │    Club origine : Judo Paris                                 │   │
│  │    Rôle : Titulaire                                          │   │
│  │    Statut : ✅ Validé                          [Retirer]     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Ajouter un membre en entente :                                     │
│                                                                     │
│  Club : [Sélectionner un club      ▼]                               │
│  Membre : [Sélectionner un membre  ▼]                               │
│  Rôle dans l'équipe : ○ Titulaire  ● Remplaçant                    │
│                                                                     │
│                              [Demander l'entente]                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Critères d'acceptation** :
- [ ] Un membre peut être ajouté en entente depuis n'importe quel club
- [ ] La limite de membres en entente par équipe est respectée
- [ ] Le club d'origine est toujours visible
- [ ] L'entente peut être révoquée tant que le membre n'a pas combattu
- [ ] Le workflow de validation fonctionne si activé

---

#### REQ-07 : Fusion d'Équipes 🆕

**Description** : Le système doit permettre de **fusionner plusieurs équipes** pour n'en former qu'une seule, avec possibilité de la renommer.

**Cas d'usage** :
- Deux clubs partenaires souhaitent former une équipe commune
- Équipes incomplètes qui se regroupent pour participer
- Formation d'équipes régionales à partir de plusieurs clubs

**Règles métier** :

| Règle | Description |
|-------|-------------|
| **Minimum** | Au moins 2 équipes pour une fusion |
| **Maximum membres** | La fusion ne peut pas dépasser le maximum de membres autorisé |
| **Même catégorie** | Seules les équipes de la même catégorie peuvent fusionner |
| **Avant compétition** | La fusion n'est possible que si aucun combat n'a commencé |
| **Nouveau nom** | Obligatoire de définir un nouveau nom pour l'équipe fusionnée |
| **Traçabilité** | Les équipes d'origine sont conservées en historique |

**Workflow de fusion** :

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ÉQUIPE A              ÉQUIPE B                   ÉQUIPE FUSIONNÉE       │
│  (Club Lyon)           (Club Paris)               (Entente Lyon-Paris)   │
│  ┌──────────┐         ┌──────────┐               ┌──────────────────┐    │
│  │ Jean D.  │         │ Marc M.  │               │ Jean D. (Lyon)   │    │
│  │ Paul B.  │   ───▶  │ Luc D.   │   ═══════▶   │ Paul B. (Lyon)   │    │
│  │          │         │ Alex P.  │               │ Marc M. (Paris)  │    │
│  └──────────┘         └──────────┘               │ Luc D. (Paris)   │    │
│   2 membres            3 membres                 │ Alex P. (Paris)  │    │
│                                                  └──────────────────┘    │
│                                                   5 membres              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Maquette - Interface de fusion** :

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🔗 FUSION D'ÉQUIPES                              │
│                    Catégorie : Kumité Senior -75kg                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Équipes sélectionnées pour fusion :                                │
│                                                                     │
│  ☑ Équipe Alpha (Karaté Lyon) - 2 membres                          │
│  ☑ Équipe Beta (Judo Paris) - 3 membres                            │
│  ☐ Équipe Gamma (Taekwondo Marseille) - 3 membres                  │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Récapitulatif de la fusion :                                       │
│  • Total membres : 5 (max autorisé : 7)                    ✅       │
│  • Titulaires : 4 (à définir)                                       │
│  • Remplaçants : 1 (à définir)                                      │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Nouveau nom de l'équipe fusionnée :                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Entente Lyon-Paris                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Définir les rôles des membres :                                    │
│                                                                     │
│  │ Membre           │ Club origine │ Rôle         │                │
│  ├──────────────────┼──────────────┼──────────────┤                │
│  │ Jean Dupont      │ Lyon         │ ● Titulaire  │                │
│  │ Paul Bernard     │ Lyon         │ ● Titulaire  │                │
│  │ Marc Martin      │ Paris        │ ● Titulaire  │                │
│  │ Luc Durand       │ Paris        │ ○ Remplaçant │                │
│  │ Alex Petit       │ Paris        │ ○ Remplaçant │                │
│                                                                     │
│              [Annuler]              [Confirmer la fusion]           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Critères d'acceptation** :
- [ ] La fusion crée une nouvelle équipe avec tous les membres
- [ ] Les équipes d'origine sont archivées (soft delete)
- [ ] Le nouveau nom est obligatoire et unique dans la catégorie
- [ ] Les rôles (titulaire/remplaçant) sont redéfinis lors de la fusion
- [ ] Le club d'origine de chaque membre est conservé
- [ ] La fusion est impossible si des combats ont déjà commencé

---

#### REQ-08 : Affichage État des Matchs dans les Poules 🆕

**Description** : Le tableau des poules doit afficher clairement l'état de chaque match avec un **code couleur** (similaire aux tableaux de football) et les scores des matchs terminés.

**États des matchs et couleurs** :

| État | Couleur | Code Hex | Description |
|------|---------|----------|-------------|
| **À jouer** | ⬜ Blanc/Gris clair | `#F5F5F5` | Match programmé, non commencé |
| **En cours** | 🟨 Jaune/Orange | `#FFF3CD` | Match actuellement en cours |
| **Terminé** | 🟩 Vert | `#D4EDDA` | Match joué, score final enregistré |
| **Forfait** | 🟥 Rouge | `#F8D7DA` | Match non joué (forfait, disqualification) |
| **Reporté** | 🟦 Bleu | `#D1ECF1` | Match reporté à une date ultérieure |

**Maquette - Tableau de poule avec états** :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POULE A - Kumité Senior -75kg                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     │ Équipe Alpha │ Équipe Beta │ Équipe Gamma │ Équipe Delta │ Pts │ Diff│
│ ────┼──────────────┼─────────────┼──────────────┼──────────────┼─────┼─────│
│  α  │      ██      │ 🟩 3-1     │ 🟩 2-0      │ 🟨 En cours  │  6  │ +4  │
│ ────┼──────────────┼─────────────┼──────────────┼──────────────┼─────┼─────│
│  β  │   🟩 1-3    │      ██      │ ⬜ 14h30    │ 🟩 2-2      │  2  │ -2  │
│ ────┼──────────────┼─────────────┼──────────────┼──────────────┼─────┼─────│
│  γ  │   🟩 0-2    │ ⬜ 14h30    │      ██      │ 🟥 Forfait   │  3  │ -1  │
│ ────┼──────────────┼─────────────┼──────────────┼──────────────┼─────┼─────│
│  δ  │ 🟨 En cours │ 🟩 2-2     │ 🟩 +3 pts   │      ██      │  4  │ +2  │
│ ────┴──────────────┴─────────────┴──────────────┴──────────────┴─────┴─────│
│                                                                             │
│  Légende : 🟩 Terminé  🟨 En cours  ⬜ À jouer  🟥 Forfait  🟦 Reporté     │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  CLASSEMENT PROVISOIRE :                                                    │
│  1. 🏆 Équipe Alpha    - 6 pts (+4)  ──▶ Qualifiée                         │
│  2. 🥈 Équipe Delta    - 4 pts (+2)  ──▶ Qualifiée                         │
│  3.    Équipe Gamma    - 3 pts (-1)                                         │
│  4.    Équipe Beta     - 2 pts (-2)                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Informations affichées par cellule** :

| Type de match | Affichage |
|---------------|-----------|
| **Terminé** | Score (ex: `3-1`), couleur verte |
| **En cours** | Texte "En cours" ou score live, couleur jaune |
| **À jouer** | Heure prévue ou "-", couleur grise |
| **Forfait** | Texte "Forfait" + points attribués, couleur rouge |

**Critères d'acceptation** :
- [ ] Chaque cellule du tableau a une couleur selon l'état du match
- [ ] Les scores sont affichés pour les matchs terminés
- [ ] Le classement se met à jour automatiquement
- [ ] Une légende explique le code couleur
- [ ] L'heure est affichée pour les matchs à venir
- [ ] Les matchs en cours sont visuellement distincts (animation optionnelle)

---

## 3. Analyse de l'Existant (Gap Analysis)

### 3.1 État Actuel du Système

L'analyse du code source et des templates existants révèle la situation suivante :

| Fonctionnalité | Statut | Observations |
|----------------|--------|--------------|
| Création d'équipes | ✅ Existe | URL: `/combat/creer_equipe/` |
| Liste des équipes | ✅ Existe | Affichage basique |
| Création de combats | ✅ Existe | URL: `/combat/creer_combat/` |
| Configuration combat | ✅ Existe | Durée, discipline, règles |
| Génération de poules | ⚠️ Partiel | UI existe mais bug signalé |
| Enregistrement scores | ❌ Défaillant | Bug critique - scores non sauvés |
| Config équipes (N+M) | ❌ Manquant | Pas de paramétrage titulaires/remplaçants |
| Basculement Équipe↔Indiv | ❌ Manquant | Pas de mécanisme de transition |
| **Mécanisme d'entente** | ❌ Manquant | Pas de gestion des prêts de joueurs |
| **Fusion d'équipes** | ❌ Manquant | Pas de possibilité de fusionner |
| **Affichage état matchs** | ❌ Manquant | Pas de code couleur dans les poules |
| Phase finale/élimination | ❌ Manquant | Uniquement poules actuellement |
| Podium équipe complet | ❌ Manquant | Pas d'affichage membres au podium |

### 3.2 Modèles Existants Identifiés

```python
# Modèles actuels dans competitions/models/
- Combat          # Gestion des combats individuels
- Equipe          # Équipes basiques (sans distinction titulaire/remplaçant)
- Poule           # Génération de poules
- CombatConfiguration  # Configuration des règles de combat
- CompetitionType # Type de compétition (team_based: Boolean)
```

### 3.3 Écarts Identifiés (Gaps)

#### GAP-01 : Absence de Configuration Flexible des Équipes

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🔴 Critique |
| **État actuel** | Le modèle `Equipe` existe mais ne distingue pas titulaires/remplaçants |
| **Solution requise** | Ajouter un modèle `TeamConfiguration` avec min/max titulaires et remplaçants |

#### GAP-02 : Pas de Mécanisme de Basculement

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🔴 Critique |
| **État actuel** | Le champ `team_based` existe dans `CompetitionType` mais pas de logique de transition |
| **Solution requise** | Implémenter un service `CompetitionModeService` avec méthodes `switch_to_individual()` et `switch_to_team()` |

#### GAP-03 : Génération de Poules Non Fonctionnelle

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟠 Haute |
| **État actuel** | Interface existe mais bug signalé lors de Zone Nord (6 déc 2025) |
| **Solution requise** | Débugger et compléter `PoolGenerator` avec support round-robin et seeding |

#### GAP-04 : Absence de Phase Éliminatoire

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟠 Haute |
| **État actuel** | Aucun modèle ni logique pour gérer les phases post-poules |
| **Solution requise** | Créer modèle `PhaseFinale` + `EliminationBracket` avec génération automatique du tableau |

#### GAP-05 : Podium Équipe Incomplet

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟡 Moyenne |
| **État actuel** | Le podium affiche uniquement le nom de l'équipe |
| **Solution requise** | Modifier le template podium pour afficher tous les membres de l'équipe avec leurs rôles |

#### GAP-06 : Absence de Mécanisme d'Entente 🆕

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟠 Haute |
| **État actuel** | Aucune possibilité d'intégrer un membre d'un autre club |
| **Solution requise** | Créer modèle `Entente` avec workflow de validation et limites configurables |

#### GAP-07 : Absence de Fusion d'Équipes 🆕

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟠 Haute |
| **État actuel** | Impossible de fusionner des équipes incomplètes |
| **Solution requise** | Créer service `TeamMergeService` avec interface de sélection et renommage |

#### GAP-08 : Pas d'Affichage État des Matchs 🆕

| Attribut | Valeur |
|----------|--------|
| **Impact** | 🟡 Moyenne |
| **État actuel** | Le tableau des poules n'affiche pas l'état des matchs |
| **Solution requise** | Modifier le template poule pour ajouter couleurs et scores |

---

## 4. Synthèse et Recommandations

### 4.1 Matrice de Priorisation

| Exigence | Priorité | Complexité | Sprint |
|----------|----------|------------|--------|
| Config équipes (N+M) | 🔴 P1 - Critique | Moyenne | Sprint 1 |
| Génération poules (fix) | 🔴 P1 - Critique | Faible | Sprint 1 |
| Enregistrement scores (fix) | 🔴 P1 - Critique | Faible | Sprint 1 |
| **Affichage état matchs** 🆕 | 🔴 P1 - Critique | Faible | Sprint 1 |
| Basculement Équipe↔Indiv | 🟠 P2 - Haute | Haute | Sprint 2 |
| **Mécanisme d'entente** 🆕 | 🟠 P2 - Haute | Moyenne | Sprint 2 |
| **Fusion d'équipes** 🆕 | 🟠 P2 - Haute | Moyenne | Sprint 2 |
| Affichage équipes/catégorie | 🟠 P2 - Haute | Faible | Sprint 2 |
| Phase éliminatoire/finale | 🟡 P3 - Moyenne | Haute | Sprint 3 |
| Podium équipe complet | 🟡 P3 - Moyenne | Faible | Sprint 3 |

### 4.2 Planning d'Implémentation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ROADMAP IMPLÉMENTATION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SPRINT 1 (Semaines 1-2)         SPRINT 2 (Semaines 3-4)           │
│  ════════════════════════        ════════════════════════          │
│  🔴 Fondations Critiques         🟠 Logique Métier                  │
│                                                                     │
│  • Modèle TeamConfiguration      • Service CompetitionModeService  │
│  • Fix génération poules         • 🆕 Modèle Entente + workflow    │
│  • Fix enregistrement scores     • 🆕 Service TeamMergeService     │
│  • 🆕 Affichage état matchs      • UI équipes par catégories       │
│  • Migration base de données     • Tests d'intégration             │
│                                                                     │
│  Livrable: Module stable         Livrable: Entente + Fusion        │
│           + Tableau poules                  fonctionnels            │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SPRINT 3 (Semaines 5-6)                                           │
│  ════════════════════════                                          │
│  🟡 Finitions & Enrichissements                                    │
│                                                                     │
│  • Modèle PhaseFinale + EliminationBracket                         │
│  • Génération automatique du bracket                               │
│  • Podium avec tous les membres (+ ententes)                       │
│  • Tests end-to-end compétition complète                           │
│                                                                     │
│  Livrable: Module Combat Équipes complet                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Estimation des Charges

| Sprint | Durée | Effort Estimé | Livrables |
|--------|-------|---------------|-----------|
| Sprint 1 | 2 semaines | 10-12 jours/homme | Module stable, tableau poules coloré |
| Sprint 2 | 2 semaines | 12-14 jours/homme | Entente, fusion, basculement |
| Sprint 3 | 2 semaines | 8-10 jours/homme | Phase finale, podium complet |
| **Total** | **6 semaines** | **30-36 jours/homme** | |

---

## 5. Spécifications Techniques

### 5.1 Modèles de Données à Créer

#### TeamConfiguration

```python
class TeamConfiguration(models.Model):
    """Configuration de la composition des équipes pour une compétition."""
    
    # Présets standards
    FORMAT_2_1 = '2+1'
    FORMAT_3_1 = '3+1'
    FORMAT_3_2 = '3+2'
    FORMAT_5_2 = '5+2'
    FORMAT_CUSTOM = 'custom'
    
    FORMAT_CHOICES = [
        (FORMAT_2_1, '2 titulaires + 1 remplaçant'),
        (FORMAT_3_1, '3 titulaires + 1 remplaçant'),
        (FORMAT_3_2, '3 titulaires + 2 remplaçants'),
        (FORMAT_5_2, '5 titulaires + 2 remplaçants'),
        (FORMAT_CUSTOM, 'Personnalisé'),
    ]
    
    competition = models.OneToOneField('Competition', on_delete=models.CASCADE)
    format_preset = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=FORMAT_3_1)
    
    min_titulaires = models.PositiveSmallIntegerField(default=3)
    max_titulaires = models.PositiveSmallIntegerField(default=3)
    min_remplacants = models.PositiveSmallIntegerField(default=0)
    max_remplacants = models.PositiveSmallIntegerField(default=1)
    remplacants_obligatoires = models.BooleanField(default=False)
    
    # Seuil minimum d'équipes pour maintenir le mode équipe
    min_equipes_required = models.PositiveSmallIntegerField(default=3)
    
    # Configuration des ententes
    max_ententes_par_equipe = models.PositiveSmallIntegerField(default=2)
    entente_validation_required = models.BooleanField(default=False)
    
    def is_team_valid(self, equipe):
        """Vérifie si une équipe respecte cette configuration."""
        nb_titulaires = equipe.membres.filter(role='titulaire').count()
        nb_remplacants = equipe.membres.filter(role='remplacant').count()
        nb_ententes = equipe.membres.filter(is_entente=True).count()
        
        if nb_titulaires < self.min_titulaires:
            return False
        if nb_titulaires > self.max_titulaires:
            return False
        if self.remplacants_obligatoires and nb_remplacants < self.min_remplacants:
            return False
        if nb_remplacants > self.max_remplacants:
            return False
        if nb_ententes > self.max_ententes_par_equipe:
            return False
        return True
```

#### EquipeMembre (modification)

```python
class EquipeMembre(models.Model):
    """Membre d'une équipe avec son rôle."""
    
    ROLE_TITULAIRE = 'titulaire'
    ROLE_REMPLACANT = 'remplacant'
    
    ROLE_CHOICES = [
        (ROLE_TITULAIRE, 'Titulaire'),
        (ROLE_REMPLACANT, 'Remplaçant'),
    ]
    
    equipe = models.ForeignKey('Equipe', on_delete=models.CASCADE, related_name='membres')
    practitioner = models.ForeignKey('Practitioner', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_TITULAIRE)
    ordre = models.PositiveSmallIntegerField(default=0)  # Ordre de passage
    a_combattu = models.BooleanField(default=False)  # Pour le podium
    
    # Gestion des ententes
    is_entente = models.BooleanField(default=False)
    club_origine = models.ForeignKey('Club', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='membres_en_entente')
    equipe_origine = models.ForeignKey('Equipe', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='membres_pretes')
    
    # Traçabilité fusion
    equipe_avant_fusion = models.ForeignKey('Equipe', on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='anciens_membres')
    
    class Meta:
        unique_together = ['equipe', 'practitioner']
        ordering = ['role', 'ordre']
    
    def save(self, *args, **kwargs):
        # Auto-set club_origine si entente
        if self.is_entente and not self.club_origine:
            self.club_origine = self.practitioner.club
        super().save(*args, **kwargs)
```

#### Entente (nouveau) 🆕

```python
class Entente(models.Model):
    """Gestion des ententes (prêt de joueur entre clubs)."""
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente de validation'),
        (STATUS_APPROVED, 'Approuvée'),
        (STATUS_REJECTED, 'Refusée'),
        (STATUS_CANCELLED, 'Annulée'),
    ]
    
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='ententes')
    
    # Le membre concerné
    practitioner = models.ForeignKey('Practitioner', on_delete=models.CASCADE)
    club_origine = models.ForeignKey('Club', on_delete=models.CASCADE, related_name='ententes_sortantes')
    equipe_origine = models.ForeignKey('Equipe', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='ententes_sortantes')
    
    # L'équipe d'accueil
    equipe_accueil = models.ForeignKey('Equipe', on_delete=models.CASCADE, related_name='ententes_entrantes')
    role_dans_equipe = models.CharField(max_length=20, choices=EquipeMembre.ROLE_CHOICES)
    
    # Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    demande_par = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='ententes_demandees')
    valide_par = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='ententes_validees')
    date_demande = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_refus = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['competition', 'practitioner']  # Un joueur = une seule entente par compétition
    
    def approve(self, validated_by):
        """Approuve l'entente et intègre le membre dans l'équipe."""
        from django.utils import timezone
        
        self.status = self.STATUS_APPROVED
        self.valide_par = validated_by
        self.date_validation = timezone.now()
        self.save()
        
        # Créer le membre dans l'équipe d'accueil
        EquipeMembre.objects.create(
            equipe=self.equipe_accueil,
            practitioner=self.practitioner,
            role=self.role_dans_equipe,
            is_entente=True,
            club_origine=self.club_origine,
            equipe_origine=self.equipe_origine
        )
    
    def reject(self, validated_by, motif=''):
        """Refuse l'entente."""
        from django.utils import timezone
        
        self.status = self.STATUS_REJECTED
        self.valide_par = validated_by
        self.date_validation = timezone.now()
        self.motif_refus = motif
        self.save()
```

#### TeamMerge (nouveau) 🆕

```python
class TeamMerge(models.Model):
    """Historique des fusions d'équipes."""
    
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='fusions')
    
    # L'équipe résultante
    equipe_fusionnee = models.ForeignKey('Equipe', on_delete=models.CASCADE, related_name='fusion_result')
    nouveau_nom = models.CharField(max_length=255)
    
    # Équipes d'origine (JSON pour flexibilité)
    equipes_origine_ids = models.JSONField()  # Liste des IDs des équipes fusionnées
    equipes_origine_noms = models.JSONField()  # Liste des noms pour historique
    
    # Métadonnées
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_equipes_origine_display(self):
        """Retourne une chaîne lisible des équipes d'origine."""
        return " + ".join(self.equipes_origine_noms)
```

#### MatchPoule (modification pour état) 🆕

```python
class MatchPoule(models.Model):
    """Match dans une poule avec état visuel."""
    
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FORFEIT = 'forfeit'
    STATUS_POSTPONED = 'postponed'
    
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'À jouer'),
        (STATUS_IN_PROGRESS, 'En cours'),
        (STATUS_COMPLETED, 'Terminé'),
        (STATUS_FORFEIT, 'Forfait'),
        (STATUS_POSTPONED, 'Reporté'),
    ]
    
    STATUS_COLORS = {
        STATUS_SCHEDULED: '#F5F5F5',    # Gris clair
        STATUS_IN_PROGRESS: '#FFF3CD',  # Jaune
        STATUS_COMPLETED: '#D4EDDA',    # Vert
        STATUS_FORFEIT: '#F8D7DA',      # Rouge
        STATUS_POSTPONED: '#D1ECF1',    # Bleu
    }
    
    poule = models.ForeignKey('Poule', on_delete=models.CASCADE, related_name='matchs')
    
    # Participants (équipes ou individus selon le mode)
    equipe_1 = models.ForeignKey('Equipe', on_delete=models.CASCADE, related_name='matchs_poule_1', null=True)
    equipe_2 = models.ForeignKey('Equipe', on_delete=models.CASCADE, related_name='matchs_poule_2', null=True)
    
    # Scores
    score_1 = models.PositiveSmallIntegerField(default=0)
    score_2 = models.PositiveSmallIntegerField(default=0)
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    heure_prevue = models.TimeField(null=True, blank=True)
    
    # Forfait
    forfait_equipe = models.ForeignKey('Equipe', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='forfaits')
    
    @property
    def color(self):
        """Retourne la couleur CSS selon le statut."""
        return self.STATUS_COLORS.get(self.status, '#FFFFFF')
    
    @property
    def display_score(self):
        """Retourne l'affichage approprié selon le statut."""
        if self.status == self.STATUS_COMPLETED:
            return f"{self.score_1}-{self.score_2}"
        elif self.status == self.STATUS_IN_PROGRESS:
            return "En cours"
        elif self.status == self.STATUS_FORFEIT:
            return "Forfait"
        elif self.status == self.STATUS_POSTPONED:
            return "Reporté"
        elif self.heure_prevue:
            return self.heure_prevue.strftime("%H:%M")
        return "-"
```

#### PhaseFinale

```python
class PhaseFinale(models.Model):
    """Phase éliminatoire après les poules."""
    
    FORMAT_DIRECT = 'direct'
    FORMAT_DOUBLE = 'double'
    FORMAT_BEST_OF = 'best_of'
    
    FORMAT_CHOICES = [
        (FORMAT_DIRECT, 'Élimination directe'),
        (FORMAT_DOUBLE, 'Double élimination'),
        (FORMAT_BEST_OF, 'Meilleurs des poules'),
    ]
    
    competition = models.OneToOneField('Competition', on_delete=models.CASCADE)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=FORMAT_DIRECT)
    qualifies_per_pool = models.PositiveSmallIntegerField(default=2)
    petite_finale = models.BooleanField(default=True)  # Match pour 3ème place
    
    def generate_bracket(self):
        """Génère le tableau d'élimination à partir des qualifiés des poules."""
        pass
```

### 5.2 Services à Implémenter

#### CompetitionModeService

```python
class CompetitionModeService:
    """Service de gestion du basculement entre modes de compétition."""
    
    def __init__(self, competition):
        self.competition = competition
    
    def check_team_conditions(self):
        """Vérifie si les conditions pour une compétition par équipes sont remplies."""
        config = self.competition.team_configuration
        equipes = self.competition.equipes.all()
        
        # Vérifier le nombre minimum d'équipes
        if equipes.count() < config.min_equipes_required:
            return False, f"Nombre d'équipes insuffisant ({equipes.count()}/{config.min_equipes_required})"
        
        # Vérifier la validité de chaque équipe
        invalid_teams = [e for e in equipes if not config.is_team_valid(e)]
        if invalid_teams:
            return False, f"{len(invalid_teams)} équipe(s) incomplète(s)"
        
        return True, "Conditions remplies"
    
    def switch_to_individual(self, confirm=False):
        """Bascule la compétition en mode individuel."""
        if self.competition.has_started_combats():
            raise ValidationError("Impossible de basculer : des combats ont déjà commencé")
        
        if not confirm:
            return self._preview_switch_to_individual()
        
        with transaction.atomic():
            # Récupérer tous les membres des équipes
            practitioners = []
            for equipe in self.competition.equipes.all():
                for membre in equipe.membres.all():
                    practitioners.append(membre.practitioner)
            
            # Dissoudre les équipes
            self.competition.equipes.all().delete()
            
            # Créer les inscriptions individuelles
            for practitioner in practitioners:
                Registration.objects.get_or_create(
                    competition=self.competition,
                    practitioner=practitioner,
                    defaults={'origin_team': equipe.nom}  # Traçabilité
                )
            
            # Mettre à jour le type de compétition
            self.competition.competition_type.team_based = False
            self.competition.competition_type.save()
            
            # Régénérer les poules
            PoolGenerator(self.competition).generate_pools()
        
        return True
    
    def switch_to_team(self, confirm=False):
        """Bascule la compétition en mode équipe."""
        # Implémentation similaire en sens inverse
        pass
```

#### EntenteService (nouveau) 🆕

```python
class EntenteService:
    """Service de gestion des ententes entre équipes."""
    
    def __init__(self, competition):
        self.competition = competition
        self.config = competition.team_configuration
    
    def can_add_entente(self, equipe_accueil, practitioner):
        """Vérifie si une entente peut être ajoutée."""
        # Vérifier la limite d'ententes
        current_ententes = equipe_accueil.membres.filter(is_entente=True).count()
        if current_ententes >= self.config.max_ententes_par_equipe:
            return False, f"Limite d'ententes atteinte ({current_ententes}/{self.config.max_ententes_par_equipe})"
        
        # Vérifier que le pratiquant n'est pas déjà en entente ailleurs
        existing = Entente.objects.filter(
            competition=self.competition,
            practitioner=practitioner,
            status__in=[Entente.STATUS_PENDING, Entente.STATUS_APPROVED]
        ).exists()
        if existing:
            return False, "Ce membre est déjà en entente dans une autre équipe"
        
        # Vérifier que le pratiquant n'est pas dans l'équipe d'accueil
        if equipe_accueil.membres.filter(practitioner=practitioner).exists():
            return False, "Ce membre fait déjà partie de l'équipe"
        
        return True, "Entente possible"
    
    def request_entente(self, equipe_accueil, practitioner, role, requested_by):
        """Crée une demande d'entente."""
        can_add, message = self.can_add_entente(equipe_accueil, practitioner)
        if not can_add:
            raise ValidationError(message)
        
        entente = Entente.objects.create(
            competition=self.competition,
            practitioner=practitioner,
            club_origine=practitioner.club,
            equipe_accueil=equipe_accueil,
            role_dans_equipe=role,
            demande_par=requested_by,
            status=Entente.STATUS_PENDING if self.config.entente_validation_required else Entente.STATUS_APPROVED
        )
        
        # Auto-approve si pas de validation requise
        if not self.config.entente_validation_required:
            entente.approve(requested_by)
        
        return entente
    
    def revoke_entente(self, entente):
        """Révoque une entente (si le membre n'a pas combattu)."""
        membre = EquipeMembre.objects.filter(
            equipe=entente.equipe_accueil,
            practitioner=entente.practitioner,
            is_entente=True
        ).first()
        
        if membre and membre.a_combattu:
            raise ValidationError("Impossible de révoquer : le membre a déjà combattu")
        
        if membre:
            membre.delete()
        
        entente.status = Entente.STATUS_CANCELLED
        entente.save()
```

#### TeamMergeService (nouveau) 🆕

```python
class TeamMergeService:
    """Service de fusion d'équipes."""
    
    def __init__(self, competition):
        self.competition = competition
        self.config = competition.team_configuration
    
    def can_merge(self, equipes):
        """Vérifie si les équipes peuvent être fusionnées."""
        if len(equipes) < 2:
            return False, "Il faut au moins 2 équipes pour fusionner"
        
        # Vérifier que les équipes sont de la même catégorie
        categories = set(e.category_id for e in equipes)
        if len(categories) > 1:
            return False, "Les équipes doivent être de la même catégorie"
        
        # Vérifier le nombre total de membres
        total_membres = sum(e.membres.count() for e in equipes)
        max_allowed = self.config.max_titulaires + self.config.max_remplacants
        if total_membres > max_allowed:
            return False, f"Trop de membres ({total_membres}/{max_allowed})"
        
        # Vérifier qu'aucun combat n'a commencé
        for equipe in equipes:
            if equipe.has_started_combats():
                return False, f"L'équipe {equipe.nom} a déjà commencé à combattre"
        
        return True, "Fusion possible"
    
    def preview_merge(self, equipes):
        """Retourne un aperçu de la fusion."""
        membres = []
        for equipe in equipes:
            for membre in equipe.membres.all():
                membres.append({
                    'practitioner': membre.practitioner,
                    'club_origine': equipe.club,
                    'equipe_origine': equipe,
                    'role_actuel': membre.role,
                })
        
        return {
            'equipes': [e.nom for e in equipes],
            'total_membres': len(membres),
            'membres': membres,
            'max_titulaires': self.config.max_titulaires,
            'max_remplacants': self.config.max_remplacants,
        }
    
    def merge(self, equipes, nouveau_nom, roles_membres, merged_by):
        """
        Fusionne les équipes.
        
        Args:
            equipes: Liste des équipes à fusionner
            nouveau_nom: Nom de la nouvelle équipe
            roles_membres: Dict {practitioner_id: 'titulaire'|'remplacant'}
            merged_by: User qui effectue la fusion
        """
        can_merge, message = self.can_merge(equipes)
        if not can_merge:
            raise ValidationError(message)
        
        with transaction.atomic():
            # Créer la nouvelle équipe
            nouvelle_equipe = Equipe.objects.create(
                competition=self.competition,
                nom=nouveau_nom,
                category=equipes[0].category,
                club=None,  # Équipe multi-clubs
                is_fusion=True
            )
            
            # Transférer les membres avec leurs nouveaux rôles
            ordre = 0
            for equipe in equipes:
                for membre in equipe.membres.all():
                    nouveau_role = roles_membres.get(str(membre.practitioner.id), membre.role)
                    EquipeMembre.objects.create(
                        equipe=nouvelle_equipe,
                        practitioner=membre.practitioner,
                        role=nouveau_role,
                        ordre=ordre,
                        is_entente=membre.is_entente,
                        club_origine=membre.club_origine or equipe.club,
                        equipe_avant_fusion=equipe
                    )
                    ordre += 1
            
            # Enregistrer l'historique de fusion
            TeamMerge.objects.create(
                competition=self.competition,
                equipe_fusionnee=nouvelle_equipe,
                nouveau_nom=nouveau_nom,
                equipes_origine_ids=[e.id for e in equipes],
                equipes_origine_noms=[e.nom for e in equipes],
                created_by=merged_by
            )
            
            # Archiver les anciennes équipes (soft delete)
            for equipe in equipes:
                equipe.is_active = False
                equipe.merged_into = nouvelle_equipe
                equipe.save()
        
        return nouvelle_equipe
```

---

## 6. Prompt d'Implémentation

Utilisez le prompt suivant pour demander l'implémentation des fonctionnalités manquantes :

---

```
PROMPT D'IMPLÉMENTATION - MODULE COMBAT ÉQUIPES MARTIALCOMP v1.1

Implémente le système complet de gestion des compétitions combat par équipes 
pour MartialComp selon l'analyse fonctionnelle v1.1.

═══════════════════════════════════════════════════════════════════════════════
PHASE 1 - Configuration des Équipes + Affichage Poules (Sprint 1)
═══════════════════════════════════════════════════════════════════════════════

1. Crée le modèle TeamConfiguration dans competitions/models/combat.py avec :
   - min_titulaires, max_titulaires (Integer)
   - min_remplacants, max_remplacants (Integer)
   - remplacants_obligatoires (Boolean)
   - format_preset avec choix : FORMAT_2_1, FORMAT_3_1, FORMAT_3_2, FORMAT_5_2, CUSTOM
   - max_ententes_par_equipe (Integer, défaut: 2)
   - entente_validation_required (Boolean)
   - Méthode is_team_valid(equipe) qui vérifie la conformité

2. Modifie le modèle Equipe pour ajouter :
   - is_fusion (Boolean) pour identifier les équipes fusionnées
   - merged_into (ForeignKey vers Equipe) pour la traçabilité
   - is_active (Boolean, défaut True) pour soft delete

3. Modifie le modèle EquipeMembre pour ajouter :
   - is_entente (Boolean) pour identifier les membres en entente
   - club_origine (ForeignKey vers Club) 
   - equipe_origine (ForeignKey vers Equipe) pour les ententes
   - equipe_avant_fusion (ForeignKey vers Equipe) pour la traçabilité fusion

4. 🆕 Modifie le modèle MatchPoule pour ajouter :
   - status avec choix : scheduled, in_progress, completed, forfeit, postponed
   - heure_prevue (TimeField)
   - forfait_equipe (ForeignKey vers Equipe)
   - Propriété color qui retourne le code couleur selon le status :
     * scheduled: #F5F5F5 (gris clair)
     * in_progress: #FFF3CD (jaune)
     * completed: #D4EDDA (vert)
     * forfait: #F8D7DA (rouge)
     * postponed: #D1ECF1 (bleu)
   - Propriété display_score qui retourne le score ou l'état

5. 🆕 Modifie le template poule_detail.html pour :
   - Afficher chaque cellule avec la couleur de fond selon match.color
   - Afficher match.display_score dans chaque cellule
   - Ajouter une légende en bas du tableau avec les codes couleur
   - Afficher le classement provisoire avec indication des qualifiés

═══════════════════════════════════════════════════════════════════════════════
PHASE 2 - Ententes et Fusions (Sprint 2)
═══════════════════════════════════════════════════════════════════════════════

6. 🆕 Crée le modèle Entente dans competitions/models/combat.py avec :
   - competition (ForeignKey)
   - practitioner (ForeignKey vers Practitioner)
   - club_origine, equipe_origine (ForeignKey)
   - equipe_accueil (ForeignKey vers Equipe)
   - role_dans_equipe (CharField avec choix titulaire/remplacant)
   - status avec choix : pending, approved, rejected, cancelled
   - demande_par, valide_par (ForeignKey vers User)
   - date_demande, date_validation (DateTimeField)
   - motif_refus (TextField)
   - Contrainte unique_together : ['competition', 'practitioner']
   - Méthode approve(validated_by) qui crée le EquipeMembre
   - Méthode reject(validated_by, motif)

7. 🆕 Crée le modèle TeamMerge dans competitions/models/combat.py avec :
   - competition (ForeignKey)
   - equipe_fusionnee (ForeignKey vers Equipe)
   - nouveau_nom (CharField)
   - equipes_origine_ids (JSONField)
   - equipes_origine_noms (JSONField)
   - created_by (ForeignKey vers User)
   - created_at (DateTimeField)

8. 🆕 Crée EntenteService dans competitions/services/entente_service.py :
   - can_add_entente(equipe_accueil, practitioner) : vérifie limites et unicité
   - request_entente(equipe_accueil, practitioner, role, requested_by)
   - revoke_entente(entente) : annule si membre n'a pas combattu

9. 🆕 Crée TeamMergeService dans competitions/services/merge_service.py :
   - can_merge(equipes) : vérifie catégorie, limites membres, pas de combats
   - preview_merge(equipes) : retourne aperçu de la fusion
   - merge(equipes, nouveau_nom, roles_membres, merged_by) :
     * Crée nouvelle équipe avec is_fusion=True
     * Transfère membres avec club_origine et equipe_avant_fusion
     * Archive anciennes équipes (is_active=False, merged_into)
     * Crée entrée TeamMerge pour historique

10. 🆕 Crée les templates :
    - combat/entente_list.html : liste des ententes de la compétition
    - combat/entente_form.html : formulaire de demande d'entente
    - combat/merge_form.html : interface de fusion avec :
      * Sélection des équipes (checkboxes)
      * Champ nouveau nom
      * Tableau de réassignation des rôles (titulaire/remplaçant)
      * Récapitulatif avant confirmation

11. Crée CompetitionModeService dans competitions/services/mode_service.py :
    - check_team_conditions() : vérifie nb équipes et validité
    - switch_to_individual() : dissout équipes, crée participants
    - switch_to_team() : forme équipes depuis participants

12. Modifie le template team_list.html pour :
    - Afficher l'icône 🤝 à côté des membres en entente
    - Afficher "(Club origine: X)" pour les membres en entente
    - Afficher le badge "Équipe fusionnée" si is_fusion=True
    - Boutons "Gérer ententes" et "Fusionner" pour chaque équipe

═══════════════════════════════════════════════════════════════════════════════
PHASE 3 - Phases Finales et Podium (Sprint 3)
═══════════════════════════════════════════════════════════════════════════════

13. Crée le modèle PhaseFinale avec :
    - format (élimination directe, double, best of)
    - qualifies_per_pool (Integer)
    - petite_finale (Boolean)
    - Méthode generate_bracket()

14. Crée EliminationBracket avec :
    - Génération automatique du tableau
    - Seeding basé sur classement poules
    - Gestion petite finale

15. Modifie template podium.html pour les équipes :
    - Liste TOUS les membres avec distinction :
      * 🥋 Titulaires ayant combattu
      * 🔄 Remplaçants ayant combattu
      * 👥 Remplaçants n'ayant pas combattu
      * 🤝 Membres en entente avec "(Club: X)"
    - Si équipe fusionnée, affiche "Entente X + Y"

═══════════════════════════════════════════════════════════════════════════════
CONTRAINTES TECHNIQUES
═══════════════════════════════════════════════════════════════════════════════

- Respecter l'architecture existante : apps/competitions/
- Compatibilité avec les modèles existants : Combat, Equipe, Poule
- Traduction i18n pour tous les textes (français par défaut)
- Tests unitaires pour : EntenteService, TeamMergeService, CompetitionModeService
- Migrations Django pour les nouveaux modèles
- CSS pour les couleurs des cellules de poule (inline style ou classes)

═══════════════════════════════════════════════════════════════════════════════
FICHIERS À MODIFIER/CRÉER
═══════════════════════════════════════════════════════════════════════════════

Modèles :
- competitions/models/combat.py (TeamConfiguration, Entente, TeamMerge, MatchPoule modifié)
- competitions/models/team.py (Equipe modifié, EquipeMembre modifié)

Services :
- competitions/services/entente_service.py (nouveau)
- competitions/services/merge_service.py (nouveau)
- competitions/services/mode_service.py (nouveau)
- competitions/services/pool_generator.py (modification)

Vues :
- competitions/views/entente.py (nouveau)
- competitions/views/merge.py (nouveau)
- competitions/views/combat.py (modification)

Templates :
- competitions/templates/combat/entente_list.html
- competitions/templates/combat/entente_form.html
- competitions/templates/combat/merge_form.html
- competitions/templates/combat/poule_detail.html (modification)
- competitions/templates/combat/team_list.html (modification)
- competitions/templates/combat/podium.html (modification)

CSS :
- static/css/poule_colors.css (nouveau) ou inline styles

Tests :
- competitions/tests/test_entente_service.py
- competitions/tests/test_merge_service.py
- competitions/tests/test_mode_service.py
```

---

## 7. Annexes

### 7.1 Glossaire

| Terme | Définition |
|-------|------------|
| **Titulaire** | Combattant principal de l'équipe, participe obligatoirement aux matchs |
| **Remplaçant** | Combattant de réserve, peut remplacer un titulaire en cas de besoin |
| **Entente** | 🆕 Mécanisme permettant d'intégrer un membre d'un autre club dans une équipe |
| **Fusion** | 🆕 Regroupement de plusieurs équipes en une seule nouvelle équipe |
| **Poule** | Groupe de participants/équipes qui s'affrontent tous (round-robin) |
| **Bracket** | Tableau d'élimination directe après les poules |
| **Seeding** | Classement initial des qualifiés pour le bracket |
| **Petite finale** | Match pour la 3ème place entre les perdants des demi-finales |
| **Forfait** | 🆕 Match non joué suite à l'absence ou disqualification d'une équipe |

### 7.2 Codes Couleur des Matchs 🆕

| État | Couleur | Code Hex | Utilisation |
|------|---------|----------|-------------|
| À jouer | ⬜ Blanc/Gris | `#F5F5F5` | Match programmé |
| En cours | 🟨 Jaune | `#FFF3CD` | Match en train de se jouer |
| Terminé | 🟩 Vert | `#D4EDDA` | Match joué avec score |
| Forfait | 🟥 Rouge | `#F8D7DA` | Match non joué |
| Reporté | 🟦 Bleu | `#D1ECF1` | Match décalé |

### 7.3 Références

- Document de conception MartialComp v2.3
- Retours compétition Zone Nord (6 décembre 2025)
- Règlements FFK (Fédération Française de Karaté)
- Règlements WKF (World Karate Federation)
- Règles UEFA pour les ententes inter-clubs

---

## 8. Historique des Versions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | 09/12/2025 | Version initiale |
| 1.1 | 09/12/2025 | Ajout REQ-06 (Entente), REQ-07 (Fusion), REQ-08 (Couleurs poules) |

---

*Document généré le 9 décembre 2025*  
*MartialComp - Plateforme de gestion des compétitions d'arts martiaux*
