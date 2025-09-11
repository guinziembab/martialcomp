# Directive d'Implémentation Globale pour le Nouveau Modèle MartialComp

## Objectifs stratégiques

Cette directive vise à transformer le modèle économique de MartialComp en adoptant:
1. Une tarification par membre avec adaptation géographique et dégressivité par volume
2. Un système de commission pour les fédérations (7% reversés)
3. Des fonctionnalités stand-alone accessibles à prix modique pour les organisations non-abonnées
4. L'activation systématique du module vente lors de la création d'événements

## I. Refonte du modèle principal d'abonnement

### 1. Structure tarifaire

#### 1.1 Tarification de base par région
| Région | Prix par membre (facturation annuelle) |
|--------|---------------------------------------|
| Afrique | 2,99€ |
| Asie du Sud-Est | 3,99€ |
| Amérique du Sud/Centrale | 4,99€ |
| Europe de l'Est | 5,99€ |
| Europe de l'Ouest/Amérique du Nord/Océanie | 6,99€ |
| Moyen-Orient | 5,99€ |

#### 1.2 Dégressivité par nombre de membres
| Nombre de membres | Réduction | Exemple Europe |
|-------------------|-----------|---------------|
| 1-99 | Prix standard | 6,99€ |
| 100-249 | -15% | 5,94€ |
| 250-499 | -25% | 5,24€ |
| 500-999 | -35% | 4,54€ |
| 1000+ | -45% | 3,84€ |

#### 1.3 Facturation et paiement
- Facturation annuelle uniquement
- Options de paiement: carte bancaire, virement, prélèvement SEPA
- Possibilité de paiements échelonnés pour les petites structures (3-4 versements)

### 2. Système de commission pour fédérations

#### 2.1 Paramètres clés
- Commission standard: 7% du montant payé par le club
- Reversement automatique dans le portefeuille virtuel de la fédération
- Utilisation possible pour l'abonnement de la fédération ou demande de retrait

#### 2.2 Modèles et infrastructure technique
- Création des modèles `Wallet`, `Transaction` et `Commission`
- Extension du modèle `Affiliation` avec le champ `commission_percentage`
- Système de calcul automatique des commissions lors des paiements
- Interface de gestion du portefeuille pour les fédérations

#### 2.3 Implémentation technique
```python
# Principales classes à implémenter
class Wallet(models.Model):
    # Portefeuille virtuel pour les organisations
    organization = models.OneToOneField('organizations.Organization', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
class Commission(models.Model):
    # Commission générée par un abonnement de club
    source_organization = models.ForeignKey('organizations.Organization', related_name='commissions_paid')
    beneficiary_organization = models.ForeignKey('organizations.Organization', related_name='commissions_received')
    subscription = models.ForeignKey('finances.Subscription', related_name='commissions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(choices=STATUS_CHOICES, default='PENDING')
```

## II. Fonctionnalités stand-alone pour non-abonnés

### 1. Principes directeurs pour les offres stand-alone

#### 1.1 Accessibilité financière
- Prix bas pour tenir compte des budgets limités des petites organisations
- Pas de frais cachés ou de coûts supplémentaires imprévus
- Options gratuites ou à très bas prix pour la première utilisation (essai)

#### 1.2 Simplicité d'accès
- Inscription rapide et minimale (email + mot de passe)
- Interface utilisateur simplifiée pour utilisateurs occasionnels
- Documentation claire et concise
- Support par chat ou email inclus

#### 1.3 Fonctionnalités ciblées
- Expérience limitée mais complète pour le besoin spécifique
- Pas de fonctionnalités superflues qui augmenteraient le prix
- Possibilité d'étendre progressivement selon les besoins

### 2. Packages stand-alone principaux

#### 2.1 Package "Compétiteur Essential" - 15€ par compétition
- Inscription de base à un événement unique
- Jusqu'à 10 athlètes par inscription
- Documents essentiels uniquement (certificats médicaux)
- QR codes d'identification
- Notifications email basiques

#### 2.2 Package "Résultats Live" - 3,99€ par jour
- Suivi des résultats en temps réel
- Tableau des compétitions
- Notifications de résultats
- Pas de statistiques avancées ni d'historique

#### 2.3 Package "Juge invité" - Gratuit (payé par l'organisateur)
- Interface de notation simplifiée
- Synchronisation en temps réel
- Accès limité à l'événement spécifique

#### 2.4 Boutique événement - Commission 10%
- Accès gratuit pour les visiteurs
- 10% de commission sur les ventes (vs 15-25% pour les non-membres)
- Produits liés à l'événement uniquement

### 3. Conception technique pour les accès temporaires

#### 3.1 Modèle d'accès
```python
class TemporaryAccess(models.Model):
    # Accès temporaire pour utilisateurs non-abonnés
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('competitions.Event', on_delete=models.CASCADE)
    access_type = models.CharField(choices=ACCESS_TYPES)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    payment = models.ForeignKey('finances.Payment', null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

#### 3.2 Contrôle d'accès
- Middleware spécifique pour vérifier les droits d'accès temporaires
- Système de jetons éphémères pour l'API
- Limitations automatiques basées sur la durée et le type d'accès

## III. Intégration du module vente aux événements

### 1. Activation automatique

#### 1.1 Modifications au processus de création d'événement
- Case à cocher "Activer la boutique" présélectionnée par défaut
- Options de personnalisation de la boutique dans le flux de création
- Assistant de configuration simplifié pour les produits de base

#### 1.2 Catégories de produits prédéfinies
- Merchandising de l'événement (t-shirts, casquettes)
- Équipement technique (protection, uniformes)
- Médias (photos, vidéos)
- Billets d'entrée spectateurs
- Consommables (eau, barres énergétiques)

### 2. Système de commission flexible

#### 2.1 Structure de commission
- Organisations abonnées: 5% de commission sur les ventes
- Utilisateurs stand-alone: 10% de commission sur les ventes
- Réduction progressive selon le volume (>1000€: -2%, >5000€: -3%)

#### 2.2 Paiement et versements
- Paiement direct aux organisateurs
- Versement J+7 après la fin de l'événement
- Reporting complet des ventes et commissions

## IV. Plan d'implémentation en phases

### Phase 1: Fondations techniques (2 mois)
- Développement des modèles de données pour le nouveau système tarifaire
- Création de l'infrastructure de portefeuille et commissions
- Refonte du système de facturation
- Tests techniques et validation

### Phase 2: Déploiement du modèle principal (3 mois)
- Lancement du modèle par membre pour les nouveaux clients
- Communication et formation pour les clients existants
- Migration progressive des clients actuels
- Période de transition avec double modèle

### Phase 3: Fonctionnalités stand-alone (2 mois)
- Développement des packages "Compétiteur" et "Résultats Live"
- Système d'accès temporaire
- Interface simplifiée pour utilisateurs occasionnels
- Tests utilisateurs et optimisation

### Phase 4: Intégration commerce et finalisation (3 mois)
- Intégration automatique du module vente aux événements
- Développement des packages "Juge invité"
- Optimisation des performances et de l'expérience utilisateur
- Déploiement complet et marketing

## V. Considérations spéciales pour la transition

### 1. Migration des clients existants
- Analyse individuelle de l'impact tarifaire pour chaque client
- Options de grandfathering pour les clients potentiellement impactés négativement
- Période de transition de 6-12 mois selon le profil client
- Formation et accompagnement personnalisé

### 2. Mesures d'incitation à l'adoption
- Bonus de 50€ dans le portefeuille des fédérations lors de la migration
- Remise de 10% la première année pour les clubs qui migrent volontairement
- Webinaires de formation gratuits
- Support dédié pendant la transition

### 3. Suivi et optimisation
- KPIs spécifiques pour mesurer le succès de la transition
- Feedback régulier des utilisateurs
- Comité d'amélioration avec clients représentatifs
- Révision trimestrielle des tarifs et de la structure des packages

## VI. Documentation et formation

### 1. Documentation technique
- Spécifications détaillées pour l'équipe de développement
- Documentation API pour les intégrations
- Guide de référence pour l'administration système

### 2. Documentation utilisateur
- Guides utilisateurs spécifiques par profil (fédération, club, utilisateur stand-alone)
- Tutoriels vidéo et interactifs
- FAQ et base de connaissances

### 3. Programme de formation
- Webinaires hebdomadaires pendant la phase de lancement
- Sessions personnalisées pour les grands comptes
- Formation des agents de support client
- Certification pour les "ambassadeurs" MartialComp

## VII. Mesures de succès

### 1. KPIs primaires
- Taux de conversion des essais gratuits vers abonnements (+15% cible)
- Augmentation du revenu moyen par organisation (+25% cible)
- Taux de satisfaction client (>85% cible)
- Nombre d'utilisateurs stand-alone convertis en abonnés (5% mensuel cible)

### 2. KPIs secondaires
- Nombre d'organisations inscrites via le système de commission (15+ cible)
- Taux d'activation de la boutique lors des événements (>70% cible)
- Revenu moyen par événement stand-alone (>75€ cible)
- Réduction du taux de désabonnement (-30% cible)

## Conclusion

Cette directive d'implémentation établit une feuille de route claire pour transformer le modèle économique de MartialComp vers une approche plus flexible, équitable et génératrice de croissance. L'accent mis sur l'accessibilité des fonctionnalités stand-alone permettra d'élargir l'écosystème tout en créant un canal d'acquisition naturel vers les abonnements complets. L'intégration systématique du module vente aux événements diversifiera les sources de revenus et créera de la valeur supplémentaire pour tous les acteurs de l'écosystème.