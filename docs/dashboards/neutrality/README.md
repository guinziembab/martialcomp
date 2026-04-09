# Analyse de Neutralité des Juges

## Objectif

Le module d'analyse de neutralité permet d'évaluer objectivement l'impartialité de chaque juge lors d'une compétition. Il détecte automatiquement les biais potentiels en comparant les notes attribuées selon plusieurs critères statistiques.

Ce module est un outil de **formation et d'amélioration continue** pour les juges, et non un outil disciplinaire. Il permet à chaque juge de prendre conscience de ses tendances inconscientes afin de progresser.

---

## Score de Neutralité (0-100)

Chaque juge reçoit un **score global de neutralité** calculé sur 100 points. Plus le score est élevé, plus le juge est considéré comme impartial.

Le score est calculé en soustrayant des pénalités au score parfait de 100, selon 4 critères pondérés :

| Critère | Poids | Pénalité maximale |
|---------|-------|-------------------|
| Biais de club | 30% | -30 points |
| Biais de nationalité | 25% | -25 points |
| Biais de positionnement | 20% | -20 points |
| Concordance avec les pairs | 25% | -25 points |

### Niveaux de risque

| Score | Niveau | Signification |
|-------|--------|---------------|
| **80-100** | Risque faible (vert) | Le juge note de manière cohérente et impartiale |
| **60-79** | Risque modéré (orange) | Des tendances détectées, à surveiller |
| **0-59** | Risque élevé (rouge) | Biais significatifs détectés, formation recommandée |

---

## Critère 1 : Biais de Club

### Principe
Ce critère compare la moyenne des notes qu'un juge attribue aux pratiquants de **son propre club** par rapport aux pratiquants **des autres clubs**.

### Calcul
```
Différence = Moyenne(notes aux pratiquants du même club) - Moyenne(notes aux autres pratiquants)
```

### Seuils de détection

| Différence (valeur absolue) | Sévérité | Interprétation |
|-----------------------------|----------|----------------|
| < 0.3 point | Neutre | Pas de biais détecté |
| 0.3 à 0.5 point | Faible | Léger favoritisme ou défavoritisme |
| 0.5 à 0.8 point | Modéré | Tendance significative à surveiller |
| > 0.8 point | Élevé | Biais marqué, action corrective recommandée |

### Comment interpréter
- **Valeur positive** (+) : le juge a tendance à noter plus favorablement les pratiquants de son club
- **Valeur négative** (-) : le juge a tendance à être plus sévère avec les pratiquants de son club (surcompensation)
- Les deux situations sont des biais à corriger

### Pénalité sur le score global

| Sévérité | Pénalité |
|----------|----------|
| Neutre | 0 point |
| Faible | -10 points |
| Modéré | -20 points |
| Élevé | -30 points |

---

## Critère 2 : Biais de Nationalité

### Principe
Ce critère compare la moyenne des notes attribuées aux pratiquants de **la même nationalité** que le juge par rapport aux pratiquants **d'autres nationalités**.

### Calcul
```
Différence = Moyenne(notes même nationalité) - Moyenne(notes autres nationalités)
```

### Seuils de détection

| Différence (valeur absolue) | Sévérité | Interprétation |
|-----------------------------|----------|----------------|
| < 0.2 point | Neutre | Pas de biais détecté |
| 0.2 à 0.4 point | Faible | Léger favoritisme ou défavoritisme |
| 0.4 à 0.6 point | Modéré | Tendance significative |
| > 0.6 point | Élevé | Biais marqué |

### Comment interpréter
- **Seuils plus stricts** que le biais de club, car la nationalité ne devrait avoir aucune influence sur la notation technique
- **Valeur positive** : favoritisme envers sa nationalité
- **Valeur négative** : sévérité excessive envers sa nationalité

### Pénalité sur le score global

| Sévérité | Pénalité |
|----------|----------|
| Neutre | 0 point |
| Faible | -8 points |
| Modéré | -16 points |
| Élevé | -25 points |

---

## Critère 3 : Biais de Positionnement

### Principe
Ce critère compare la **moyenne générale des notes** d'un juge par rapport à la **moyenne de tous les juges** de la compétition. Il détecte les juges systématiquement trop généreux ou trop sévères.

### Calcul
```
Différence = Moyenne(toutes les notes du juge) - Moyenne(toutes les notes de tous les juges)
```

### Seuils de détection

| Différence (valeur absolue) | Sévérité | Interprétation |
|-----------------------------|----------|----------------|
| < 0.2 point | Neutre | Dans la moyenne, notation calibrée |
| 0.2 à 0.4 point | Faible | Légèrement généreux ou sévère |
| 0.4 à 0.6 point | Modéré | Généreux ou sévère de manière notable |
| > 0.6 point | Élevé | Très généreux ou très sévère |

### Comment interpréter
- **Valeur positive** (+) : le juge note systématiquement au-dessus de la moyenne (généreux)
- **Valeur négative** (-) : le juge note systématiquement en dessous de la moyenne (sévère)
- Un bon juge se situe dans la fourchette neutre (< 0.2 point d'écart)

### Pénalité sur le score global

| Sévérité | Pénalité |
|----------|----------|
| Neutre | 0 point |
| Faible | -5 points |
| Modéré | -12 points |
| Élevé | -20 points |

---

## Critère 4 : Concordance avec les Pairs

### Principe
Ce critère mesure à quel point les notes d'un juge sont **en accord avec celles des autres juges** pour les mêmes prestations. Un juge dont les notes divergent constamment de ses collègues peut présenter un problème de calibrage ou de biais.

### Calcul
Pour chaque prestation notée par le juge :
```
Moyenne des autres = Moyenne(notes des autres juges pour cette prestation)
Écart = |Note du juge - Moyenne des autres|
Concordance individuelle = max(0, 100 - (Écart × 20))
```

Le **score de concordance global** est la moyenne de toutes les concordances individuelles.

### Interprétation

| Concordance | Signification |
|-------------|---------------|
| **90-100%** | Excellente concordance, notation très alignée |
| **75-89%** | Bonne concordance |
| **60-74%** | Concordance acceptable mais à améliorer |
| **< 60%** | Concordance faible, **alerte générée** |

### Impact sur le score global
La concordance influence le score de neutralité via un bonus/malus :
```
Ajustement = (Concordance - 50) / 2
```
- Concordance de 100% : bonus de +25 points
- Concordance de 50% : ni bonus ni malus
- Concordance de 0% : malus de -25 points

### Conditions
- Un minimum de **3 prestations** notées est requis pour que le calcul soit significatif
- Seules les notes actives (non-entraînement) sont prises en compte

---

## Système d'Alertes

Des alertes sont automatiquement générées dans les cas suivants :

| Condition | Alerte |
|-----------|--------|
| Biais de club modéré ou élevé | "Biais club détecté" avec la valeur d'écart |
| Biais de nationalité modéré ou élevé | "Biais nationalité détecté" avec la valeur d'écart |
| Positionnement élevé uniquement | "Position extrême" avec l'écart par rapport à la moyenne |
| Concordance < 60% | "Faible concordance avec les autres juges" |

Les alertes sont visibles sur la fiche détaillée de chaque juge dans l'interface d'analyse.

---

## Podium des Juges les Plus Impartiaux

À la fin de l'analyse, un **podium** met en avant les 3 juges ayant obtenu les meilleurs scores de neutralité :

- **1re place (Or)** : Score de neutralité le plus élevé
- **2e place (Argent)** : Deuxième meilleur score
- **3e place (Bronze)** : Troisième meilleur score

Ce classement récompense l'impartialité et encourage l'ensemble des juges à progresser.

---

## Recommandations pour les Juges

### Pour améliorer son score de neutralité

1. **Biais de club** : Soyez particulièrement attentif lorsque vous notez un pratiquant de votre propre club. Appliquez les mêmes critères techniques que pour les autres.

2. **Biais de nationalité** : Concentrez-vous uniquement sur la technique et l'exécution. La nationalité du pratiquant ne doit pas influencer votre évaluation.

3. **Positionnement** : Calibrez vos notes en vous alignant sur les critères définis. Ni trop généreux, ni trop sévère. En cas de doute, référez-vous au barème officiel.

4. **Concordance** : Si vos notes divergent souvent de celles de vos collègues, cela peut indiquer un problème de compréhension des critères. Participez aux sessions de calibrage.

### Bonnes pratiques

- Notez chaque prestation de manière indépendante, sans regarder les notes des autres juges
- Utilisez toute l'étendue de l'échelle de notation
- Ne modifiez pas vos notes après avoir vu celles des autres
- Prenez le temps d'évaluer chaque critère séparément
- En cas de fatigue, faites une pause pour maintenir votre concentration

---

## Accès et Confidentialité

- L'analyse de neutralité est accessible aux **organisateurs de compétition** et aux **administrateurs de fédération**
- Chaque juge peut consulter **ses propres résultats**
- Les données sont calculées en **temps réel** à partir des notes existantes (aucune donnée de neutralité n'est stockée de manière permanente)
- L'analyse nécessite un nombre suffisant de notes pour être fiable (minimum 3 prestations pour la concordance)
