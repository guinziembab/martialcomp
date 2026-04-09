# MARTIALCOMP - Analyse Fonctionnelle
## Module de Gestion des Combats
### Compétitions Individuelles & Par Équipes

---

| Information | Valeur |
|-------------|--------|
| **Document** | Analyse Fonctionnelle - Gestion des Combats |
| **Version** | 1.0 |
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
- Gérer les phases de poules, élimination directe et finale
- Afficher les résultats avec tous les membres de l'équipe au podium

### 1.3 Périmètre

| ✅ Dans le périmètre | ❌ Hors périmètre |
|----------------------|-------------------|
| Configuration des équipes | Streaming vidéo |
| Génération des poules | Application mobile arbitre |
| Gestion des matchs | Intégration fédérations externes |
| Basculement automatique | Statistiques avancées IA |
| Consolidation des points | |
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
│ │ Titulaires (3/3):   │  │ Titulaires (2/3):   │            │
│ │ • Jean Dupont       │  │ • Marc Martin       │            │
│ │ • Paul Bernard      │  │ • Luc Durand        │            │
│ │ • Pierre Moreau     │  │ • [Manquant]        │            │
│ │ ─────────────────── │  │ ─────────────────── │            │
│ │ Remplaçants (1/2):  │  │ Remplaçants (0/2):  │            │
│ │ • Alex Petit        │  │ • [Optionnel]       │            │
│ │ ─────────────────── │  │ ─────────────────── │            │
│ │ ✅ Équipe complète  │  │ ⚠️ Équipe incomplète│            │
│ └─────────────────────┘  └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Critères d'acceptation** :
- [ ] Les équipes sont groupées par catégorie
- [ ] Les titulaires et remplaçants sont visuellement distincts
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
│            │ M. Martin ││ A. Petit* ││ T. Leroy  │                  │
│            │ L. Durand ││           ││ S. Simon  │                  │
│            └───────────┘└───────────┘└───────────┘                  │
│                                                                     │
│            * = Remplaçant ayant combattu                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Critères d'acceptation** :
- [ ] Tous les membres de l'équipe sont listés nominativement
- [ ] Les rôles (titulaire/remplaçant) sont identifiables
- [ ] L'indication "a combattu" ou "n'a pas combattu" est visible

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

---

## 4. Synthèse et Recommandations

### 4.1 Matrice de Priorisation

| Exigence | Priorité | Complexité | Sprint |
|----------|----------|------------|--------|
| Config équipes (N+M) | 🔴 P1 - Critique | Moyenne | Sprint 1 |
| Génération poules (fix) | 🔴 P1 - Critique | Faible | Sprint 1 |
| Enregistrement scores (fix) | 🔴 P1 - Critique | Faible | Sprint 1 |
| Basculement Équipe↔Indiv | 🟠 P2 - Haute | Haute | Sprint 2 |
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
│  • Fix génération poules         • UI équipes par catégories       │
│  • Fix enregistrement scores     • Tests d'intégration             │
│  • Migration base de données     • Documentation utilisateur       │
│                                                                     │
│  Livrable: Module stable         Livrable: Basculement fonctionnel │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SPRINT 3 (Semaines 5-6)                                           │
│  ════════════════════════                                          │
│  🟡 Finitions & Enrichissements                                    │
│                                                                     │
│  • Modèle PhaseFinale + EliminationBracket                         │
│  • Génération automatique du bracket                               │
│  • Podium avec tous les membres                                    │
│  • Tests end-to-end compétition complète                           │
│                                                                     │
│  Livrable: Module Combat Équipes complet                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Estimation des Charges

| Sprint | Durée | Effort Estimé | Livrables |
|--------|-------|---------------|-----------|
| Sprint 1 | 2 semaines | 8-10 jours/homme | Module stable, bugs corrigés |
| Sprint 2 | 2 semaines | 10-12 jours/homme | Basculement fonctionnel |
| Sprint 3 | 2 semaines | 8-10 jours/homme | Module complet |
| **Total** | **6 semaines** | **26-32 jours/homme** | |

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
    
    def is_team_valid(self, equipe):
        """Vérifie si une équipe respecte cette configuration."""
        nb_titulaires = equipe.membres.filter(role='titulaire').count()
        nb_remplacants = equipe.membres.filter(role='remplacant').count()
        
        if nb_titulaires < self.min_titulaires:
            return False
        if nb_titulaires > self.max_titulaires:
            return False
        if self.remplacants_obligatoires and nb_remplacants < self.min_remplacants:
            return False
        if nb_remplacants > self.max_remplacants:
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
    
    class Meta:
        unique_together = ['equipe', 'practitioner']
        ordering = ['role', 'ordre']
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

---

## 6. Prompt d'Implémentation

Utilisez le prompt suivant pour demander l'implémentation des fonctionnalités manquantes :

---

```
PROMPT D'IMPLÉMENTATION - MODULE COMBAT ÉQUIPES MARTIALCOMP

Implémente le système complet de gestion des compétitions combat par équipes 
pour MartialComp selon l'analyse fonctionnelle fournie.

═══════════════════════════════════════════════════════════════════════════════
PHASE 1 - Configuration des Équipes (Sprint 1)
═══════════════════════════════════════════════════════════════════════════════

1. Crée le modèle TeamConfiguration dans competitions/models/combat.py avec :
   - min_titulaires, max_titulaires (Integer)
   - min_remplacants, max_remplacants (Integer)
   - remplacants_obligatoires (Boolean)
   - format_preset avec choix : FORMAT_2_1, FORMAT_3_1, FORMAT_3_2, FORMAT_5_2, CUSTOM
   - Méthode is_team_valid(equipe) qui vérifie la conformité

2. Modifie le modèle Equipe pour ajouter le modèle EquipeMembre avec :
   - ForeignKey vers Equipe et Practitioner
   - Champ role : 'titulaire' ou 'remplacant'
   - Champ ordre (ordre de passage)
   - Champ a_combattu (Boolean pour le podium)

3. Crée le formulaire TeamConfigurationForm avec :
   - Sélection du format preset (dropdown)
   - Champs min/max personnalisables si CUSTOM sélectionné
   - Validation croisée (min <= max)

4. Crée la vue et le template team_configuration.html

═══════════════════════════════════════════════════════════════════════════════
PHASE 2 - Basculement Automatique (Sprint 2)
═══════════════════════════════════════════════════════════════════════════════

1. Crée CompetitionModeService dans competitions/services/mode_service.py

2. Implémente check_team_conditions() qui vérifie :
   - Nombre minimum d'équipes atteint
   - Toutes les équipes sont valides selon TeamConfiguration

3. Implémente switch_to_individual() qui :
   - Vérifie qu'aucun combat n'a commencé
   - Récupère tous les membres de toutes les équipes
   - Dissout les équipes (suppression)
   - Crée des inscriptions individuelles pour chaque membre
   - Conserve l'origine (nom équipe) pour traçabilité
   - Régénère les poules en mode individuel

4. Implémente switch_to_team() qui :
   - Permet de former des équipes à partir des participants
   - Interface de drag & drop pour composer les équipes

5. Ajoute des alertes visuelles dans le dashboard organisateur :
   - Alerte si conditions équipes non remplies
   - Bouton "Basculer en individuel" avec confirmation

═══════════════════════════════════════════════════════════════════════════════
PHASE 3 - Poules et Matchs (Sprint 1-2)
═══════════════════════════════════════════════════════════════════════════════

1. Corrige PoolGenerator.generate_pools() pour :
   - Générer correctement les matchs round-robin
   - Supporter les équipes ET les individuels
   - Éviter les équipes du même club dans la même poule (si possible)

2. Implémente la consolidation des points par équipe :
   - Somme des victoires des membres
   - Critères de départage : Points > Différence > Confrontation directe

3. Crée le modèle PhaseFinale avec :
   - Lien vers Competition
   - Format (élimination directe, double, best of)
   - Nombre de qualifiés par poule
   - Option petite finale (3ème place)

4. Crée EliminationBracket avec méthode generate_bracket() :
   - Seed les qualifiés selon leur classement
   - Génère les matchs 1/4, 1/2, finale
   - Gère la petite finale si activée

═══════════════════════════════════════════════════════════════════════════════
PHASE 4 - Interface et Résultats (Sprint 3)
═══════════════════════════════════════════════════════════════════════════════

1. Crée template team_list_by_category.html :
   - Groupement des équipes par catégorie
   - Affichage des membres avec distinction titulaire/remplaçant
   - Indicateur visuel de validité (complet/incomplet)

2. Modifie template podium.html pour les équipes :
   - Affiche TOUS les membres de l'équipe gagnante
   - Distingue visuellement :
     • 🥋 Titulaires ayant combattu
     • 🔄 Remplaçants ayant combattu  
     • 👥 Remplaçants n'ayant pas combattu
   - Affiche le club d'appartenance

3. Crée template bracket_elimination.html :
   - Affichage visuel du tableau d'élimination
   - Mise à jour en temps réel des résultats
   - Navigation vers les détails de chaque match

═══════════════════════════════════════════════════════════════════════════════
CONTRAINTES TECHNIQUES
═══════════════════════════════════════════════════════════════════════════════

- Respecter l'architecture existante : apps/competitions/
- Compatibilité avec les modèles existants : Combat, Equipe, Poule
- Traduction i18n pour tous les textes (français par défaut)
- Tests unitaires pour CompetitionModeService et PoolGenerator
- Migrations Django pour les nouveaux modèles
- Documentation des APIs créées

═══════════════════════════════════════════════════════════════════════════════
FICHIERS À MODIFIER/CRÉER
═══════════════════════════════════════════════════════════════════════════════

Modèles :
- competitions/models/combat.py (ajout TeamConfiguration, EquipeMembre, PhaseFinale)

Services :
- competitions/services/mode_service.py (nouveau)
- competitions/services/pool_generator.py (modification)
- competitions/services/bracket_generator.py (nouveau)

Vues :
- competitions/views/combat.py (modification)
- competitions/views/teams.py (nouveau)

Templates :
- competitions/templates/combat/team_configuration.html
- competitions/templates/combat/team_list_by_category.html
- competitions/templates/combat/bracket_elimination.html
- competitions/templates/combat/podium.html (modification)

Tests :
- competitions/tests/test_mode_service.py
- competitions/tests/test_pool_generator.py
```

---

## 7. Annexes

### 7.1 Glossaire

| Terme | Définition |
|-------|------------|
| **Titulaire** | Combattant principal de l'équipe, participe obligatoirement aux matchs |
| **Remplaçant** | Combattant de réserve, peut remplacer un titulaire en cas de besoin |
| **Poule** | Groupe de participants/équipes qui s'affrontent tous (round-robin) |
| **Bracket** | Tableau d'élimination directe après les poules |
| **Seeding** | Classement initial des qualifiés pour le bracket |
| **Petite finale** | Match pour la 3ème place entre les perdants des demi-finales |

### 7.2 Références

- Document de conception MartialComp v2.3
- Retours compétition Zone Nord (6 décembre 2025)
- Règlements FFK (Fédération Française de Karaté)
- Règlements WKF (World Karate Federation)

---

*Document généré le 9 décembre 2025*  
*MartialComp - Plateforme de gestion des compétitions d'arts martiaux*
