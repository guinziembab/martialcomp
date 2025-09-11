**Cahier des charges** application Martial\_hub, intégrant les règles du document "Règlement d'Arbitrage du Qwan Ki Do" et les nouvelles recommandations :

### **1\. Objectifs de l'application**

Fournir une interface permettant la gestion des compétitions de Qwan Ki Do avec un suivi des combats en temps réel, incluant l'attribution des scores, la gestion des équipes et la prise en compte des règles d'arbitrage spécifiques.

### **2\. Fonctionnalités principales**

#### **2.1 Gestion des compétitions**

* **Types de compétition** : Sélection entre les formats *individuel* et *par équipe*.  
* **Configuration des équipes** : Définir des équipes composées de 1 à 5 pratiquants avec des remplaçants.  
* **Système de poules** : (Toujours privilégier les poules de 3, cela permet à chaque équipe de faire au moins de 2 combats)  
  * Éviter les affrontements directs entre athlètes ou équipes du même club ou pays lors des premiers tours, sauf cas de force majeure.  
  * **Automatisation des poules** selon le nombre d’équipes : 3 équipes (poules), 4 équipes (demi-finales et finales), 5 équipes (poules de 3 et de 2). 6 équipes de poules de 3 équipes. 7 équipes ( 1 poule de 3 et une poule de 4). 8 équipes (2 poules de 3 et 1 poule de 2). 9 équipes ( 3 poules de 3, les vainqueurs s’affrontent en triangulaire), 10 équipes ( 2 poules de 3 et une poules de 4). (11 équipes, 3 poules de 3 et une poule de 2), (12 équipes , 4 poule de 3, quart de finale, demi finale et finale) etc;;  
  * Intégration d’un **tirage au sort aléatoire**, respectant les contraintes de séparation par club et par pays.

#### **2.2 Paramétrage des combats**

* **Durée des combats**( la durée de combat doit être paramétrable ) : Sélection de la durée (1mn, 1mn30, 2mn) avec options de prolongation (30s, 1mn).  
* **Pause pour les arbitres** : Fonctionnalité de pause pour permettre aux arbitres de se concerter.

#### **2.3 Gestion des points et des pénalités**

* **Incrémentation des points** : Système permettant l’attribution des points en temps réel (0.25, 0.5, 1, 1.5, 2).  
* **Pénalités dégressives** : Gestion des pénalités de manière ascendante et dégressive (-0.25, \-0.5, \-1, \-2) avec des sanctions spéciales après 3 avertissements (-1) et disqualification après répétition (-2).  
* **Comptabilisation des sorties** : Décrémentation après 3 sorties, avec un paramétrage flexible des valeurs de pénalités.  
* Exemple de Système de points QWAN KI DO  


| Voici un tableau récapitulatif basé sur le règlement d'arbitrage du Qwan Ki Do. Il inclut le système de points, les sanctions, et les pénalités en utilisant les termes vietnamiens comme décrits dans le document. |  |
| :---- | :---- |
|  |  |
| | Système de notation des points et sanctions en combat \- Qwan Ki Do | |------------------------------------|---------------------------------------------| |  |
|  |  |
| Points | Description |
| Phân Tu Ðiểm (¼ point) | Attribution d’un quart de point pour un coup de poing correct avec bonne attitude, technique et puissance mais non décisif. |
| Nửa Ðiểm (½ point) | Demi-point pour un coup de pied correct au corps, mais avec moins de précision ou de force. |
| Một Ðiểm (1 point) | Un point pour un coup de poing ou coup de pied bien exécuté et contrôlé sur une partie autorisée du corps. |
| Một Ðiểm Dưới (1,5 points) | Un point et demi pour une combinaison réussie de coups de poing/pied ou une projection sans décoller les deux pieds. |
| Hai Ðiểm (2 points) | Deux points pour une projection avec suivi d’une attaque au sol, ou une technique acrobatique bien exécutée. |
| Sanctions et pénalités | Description |
| Cảnh Cáo (Avertissement verbal) | Premier avertissement sans retrait de points pour une faute mineure (sortie du tapis, comportement passif). |
| Kém Ðiểm (Retrait de ½ point) | Retrait d’un demi-point pour des techniques non conformes ou des comportements perturbateurs (parler à l’adversaire, etc.). |
| Phạt (Retrait de 1 point) | Retrait d’un point pour des fautes plus graves comme des coups portés à des zones interdites (genoux, testicules). |
| Phạt Hai (Retrait de 1 point \+ Disqualification) | En cas de faute répétée après un premier avertissement, disqualification automatique avec perte de 1 point. |
| Loại (Disqualification immédiate) | Pour des actions violentes volontaires (KO, coup dangereux à la tête), comportement antisportif flagrant. |
|  |  |
| Autres points importants : |  |
|  |  |
| Sorties de l’aire de combat : à la troisième sortie, le compétiteur reçoit un Kém Ðiểm (½ point de pénalité), à la cinquième sortie, il est disqualifié (Phạt Hai). |  |
| Techniques interdites : Toutes les techniques non maîtrisées ou frappes dangereuses à la tête, au dos, ou dans les parties génitales sont sanctionnées par Phạt (1 point retiré) ou Loại pour les fautes graves. |  |
|  |  |
| Ce tableau présente un aperçu des principales règles de compétition en combat, avec les termes vietnamiens utilisés pour l'arbitrage​. |  |


#### **2.4 Affichage en temps réel**

* **Interface d'affichage épurée** :  
  * Écran divisé en deux sections, représentant les équipes Rouge et Blanc, avec affichage des scores, des pénalités et des sanctions en temps réel.  
  * Visualisation des **photos des combattants** en lien avec la gestion des membres.  
  * Affichage des couleurs des drapeaux des pays et des logos des clubs respectifs des athlètes.  
  * Highlignt du score en cas de marquage avec une durée de \+-3s. 

![][image1]

* **Visibilité publique** : Affichage des résultats pour les combattants, les spectateurs et les officiels.

### **3\. Interface utilisateur (UI)**

#### **3.1 Écran d'affichage des scores**

* **Séparation claire des équipes** (Rouge et Blanc) avec les scores, les pénalités et les détails des combattants (photos, pays, clubs).  
* **Graphisme sobre** et facilement lisible par les spectateurs et les arbitres.

#### **3.2 Interface des arbitres**

* Interface simplifiée pour une attribution rapide et intuitive des points et des pénalités, avec gestion des pauses et des prolongations.

### **4\. Performances**

* **Réactivité en temps réel** : Les modifications des points doivent être instantanément visibles sur l’écran d’affichage public.  
* **Sécurité et fiabilité** : Gestion sécurisée des données avec possibilité de corriger les erreurs d’attribution de points ou de pénalités.

### **5\. Considérations techniques**

* **Choix technologique** : Utilisation d’un framework web dynamique (comme React.js ou Vue.js) et d’une API temps réel (comme Node.js avec WebSocket) pour la gestion des événements en direct.  
* **Gestion des données** : Synchronisation avec une base de données sécurisée pour la sauvegarde des résultats et des informations des compétiteurs.  
* **Accessibilité** : Prévoir une version mobile ou tablette pour les arbitres et les gestionnaires.

---

### **Recommandations supplémentaires**

* **Tests de scénario de compétition** : Inclure des tests de simulation de combats pour vérifier l’exactitude des points et des pénalités selon les règles.  
* **Amélioration continue** : Prévoir des mises à jour de l’application en fonction des modifications des règlements d’arbitrage.

Ce cahier des charges complet inclut les règles et exigences spécifiques issues du document ainsi que les recommandations supplémentaires fournies. Cela constitue une base solide pour le développement de votre application de suivi des compétitions de Qwan Ki Do.

R**ègles d'organisation des compétitions et d'attribution des points** spécifiques à l'arbitrage de Qwan Ki Do. Voici les points clés :

1. **Éviter les affrontements directs entre athlètes du même club ou pays** :  
   * Le fichier précise l'importance d'organiser les poules de manière à éviter les confrontations entre combattants issus d’un même club ou pays, particulièrement au début des compétitions. J'ai intégré cette règle dans le système de poules avec une gestion du tirage au sort prenant en compte ces contraintes.  
2. **Photos des combattants, logos des clubs et drapeaux** :  
   * Le fichier indique que chaque compétiteur doit être identifiable par son club et son pays. J'ai ajouté une fonctionnalité de visualisation des photos des combattants, d’affichage des couleurs de drapeau de chaque pays et des logos des clubs dans l’application.  
3. **Durées de combat et prolongations** :  
   * En accord avec le règlement, les différentes durées de combat et les options de prolongation ont été incluses. Le chronomètre doit pouvoir être suspendu à la demande des arbitres, ce qui est également mentionné dans le fichier.  
4. **Attribution des points et pénalités** :  
   * Le système de points et de pénalités que vous avez décrit correspond bien aux règles établies dans le fichier, incluant les valeurs et la gestion des avertissements successifs qui mènent à une disqualification. Par exemple, j'ai intégré les pénalités graduelles (-0.25, \-0.5, \-1, \-2) et les sanctions en cas de sortie répétée de l’aire de combat.  
5. **Système de poules** :  
   * J'ai tenu compte des règles mentionnées dans le document concernant l'organisation des poules, la formation de demi-finales et de finales, ainsi que les configurations spécifiques selon le nombre d'équipes.

Pour rendre ce projet **modulaire, standard et adaptable** à diverses disciplines martiales tout en utilisant **Python avec Django**, il est essentiel de suivre une approche structurée. Voici un plan d'implémentation, des recommandations techniques, et des pistes pour rendre l'application flexible.

### **1\. Architecture de l'application et modèles de données**

* **Modèle de compétition** : Définir une classe `Competition` qui contient les informations de base d'une compétition (nom, date, lieu, type : individuel ou équipe, etc.). Elle doit également être associée à une **discipline martiale**.  
* **Modèle de discipline martiale** (`MartialArtDiscipline`) : Inclure les règles spécifiques, les points, les pénalités et les critères de victoire pour chaque discipline (Qwan Ki Do, Karaté, Taekwondo, etc.). Cela peut être un champ JSON pour stocker des règles spécifiques à chaque art martial, ce qui permet une **personnalisation par discipline**.

python

Copier le code

`class MartialArtDiscipline(models.Model):`

    `name = models.CharField(max_length=100)`

    `scoring_system = models.JSONField()  # Stocker les règles spécifiques sous forme JSON`

    `penalty_rules = models.JSONField()`

    `duration_options = models.JSONField()  # Ex: {'1min': 60, '1min30': 90, '2min': 120}`

* **Modèle de compétition** avec association de règles :

python

Copier le code

`class Competition(models.Model):`

    `name = models.CharField(max_length=200)`

    `date = models.DateField()`

    `location = models.CharField(max_length=200)`

    `discipline = models.ForeignKey(MartialArtDiscipline, on_delete=models.CASCADE)`

    `type = models.CharField(choices=[('individual', 'Individual'), ('team', 'Team')], max_length=10)`

* **Modèle des équipes et combattants** : Associer les équipes et combattants à une compétition et gérer les informations spécifiques comme les photos, les drapeaux, les logos de club.

python

Copier le code

`class Team(models.Model):`

    `name = models.CharField(max_length=100)`

    `competition = models.ForeignKey(Competition, on_delete=models.CASCADE)`

    `country_flag = models.ImageField(upload_to='flags/')`

    `club_logo = models.ImageField(upload_to='logos/')`

`class Competitor(models.Model):`

    `name = models.CharField(max_length=100)`

    `team = models.ForeignKey(Team, on_delete=models.CASCADE)`

    `photo = models.ImageField(upload_to='photos/')`

### **2\. Gestion des règles de points, pénalités et sanctions**

#### **Modularité des points et pénalités**

* Créer des modèles pour les **règles de score et pénalités** personnalisables par discipline :

python

Copier le code

`class ScoreRule(models.Model):`

    `discipline = models.ForeignKey(MartialArtDiscipline, on_delete=models.CASCADE)`

    `description = models.CharField(max_length=255)`

    `point_value = models.DecimalField(max_digits=4, decimal_places=2)`

`class PenaltyRule(models.Model):`

    `discipline = models.ForeignKey(MartialArtDiscipline, on_delete=models.CASCADE)`

    `description = models.CharField(max_length=255)`

    `penalty_value = models.DecimalField(max_digits=4, decimal_places=2)`

    `cumulative = models.BooleanField(default=False)`

* **Gestion dynamique** : En fonction de la discipline sélectionnée, charger dynamiquement les règles et options de pénalités, durées de combat, etc., via des **formulaires Django** ou **interfaces React/Vue.js** si une approche frontend avancée est choisie.

### **3\. Paramétrage des durées de compétition et des événements**

* Permettre aux arbitres et organisateurs de sélectionner ou définir des durées spécifiques via une **interface d’administration Django** avec des formulaires personnalisables.  
* Exemple d’implémentation :

python

Copier le code

`class CombatDuration(models.Model):`

    `discipline = models.ForeignKey(MartialArtDiscipline, on_delete=models.CASCADE)`

    `name = models.CharField(max_length=50)  # Ex: "Prolongation"`

    `duration_seconds = models.IntegerField()  # Ex: 30, 60, 120`

### **4\. Interface de gestion dynamique des combats et des scores**

* **Vue en temps réel** avec Django Channels pour gérer la **synchronisation des scores en direct**.  
* Créer une **interface distincte pour les arbitres** où ils peuvent attribuer des points et pénalités à l’aide de boutons (ex: \+0.25, \-0.25, avertissement, etc.). Les actions des arbitres doivent déclencher des événements WebSocket qui mettent à jour les scores de manière synchrone sur tous les écrans.

### **5\. Personnalisation des règles pour chaque discipline**

* Dans l’**interface d’administration Django**, permettre aux utilisateurs de configurer les points et pénalités spécifiques à chaque discipline. Utilisez les champs JSON pour stocker des règles détaillées et permettre aux arbitres de sélectionner celles-ci lors de la création d'une compétition.  
* Exemple de règles JSON :

json

Copier le code

`{`

    `"points": [0.25, 0.5, 1, 1.5, 2],`

    `"penalties": [-0.25, -0.5, -1, -2],`

    `"sanctions": {`

        `"3_warnings": -1,`

        `"2_major_penalties": -2`

    `},`

    `"durations": [60, 90, 120]`

`}`

### **6\. Adaptabilité à diverses disciplines**

* Pour chaque nouvelle discipline, les règles de scoring, de pénalités, de durées, etc., peuvent être configurées dans l’**interface administrateur** et stockées de manière dynamique, ce qui rend l'application **flexible et extensible**.

### **7\. Recommandations supplémentaires**

* **Tests unitaires et validation** des règles de discipline : Inclure des tests automatisés pour valider l’intégrité des règles selon les arts martiaux configurés.  
* **Système de gestion de base de données robuste** : Utiliser PostgreSQL pour bénéficier des capacités de gestion de JSON natifs et des index dynamiques, facilitant la recherche de règles spécifiques.

### **8\. Technologies recommandées**

* **Backend Django avec Django Rest Framework (DRF)** : Pour gérer les API REST, les événements WebSocket et l’administration.  
* **Django Channels** : Pour la gestion des WebSocket et la mise à jour en temps réel.  
* **Frontend (optionnel)** : Utilisation de React ou Vue.js pour une interface utilisateur moderne et dynamique.

### **9\. Exemple d'implémentation API Django**

Voici une vue simple pour l'attribution des scores et pénalités en fonction des règles spécifiques :

python

Copier le code

`from rest_framework import viewsets`

`from .models import Competition, Competitor, ScoreRule`

`from .serializers import CompetitionSerializer`

`class CompetitionViewSet(viewsets.ModelViewSet):`

    `queryset = Competition.objects.all()`

    `serializer_class = CompetitionSerializer`

    `def update_score(self, request, *args, **kwargs):`

        `competition = self.get_object()`

        `score_rule = ScoreRule.objects.get(pk=request.data.get("score_rule_id"))`

        `competitor = Competitor.objects.get(pk=request.data.get("competitor_id"))`

        

        `# Logique de mise à jour des scores et validation des règles`

        `new_score = competitor.score + score_rule.point_value`

        `competitor.score = new_score`

        `competitor.save()`

        `return Response({"new_score": new_score})`

---

### **Résumé des avantages de cette approche :**

* **Personnalisation totale** pour chaque discipline via des règles dynamiques.  
* **Interface utilisateur intuitive** pour les arbitres et les spectateurs.  
* **Gestion flexible des scores et pénalités** avec une architecture adaptable et des champs JSON.  
* **Mises à jour en temps réel** pour une meilleure expérience utilisateur.

Cela vous permettrait de développer une application robuste et extensible tout en respectant les spécificités des divers arts martiaux.

Voici la configuration actuelle de l’application compétitions : 

1. Modèle compétitions : **models.py**  

from django.db import models

from django.contrib.gis.db import models as geomodels  \# Utilisation des géomodèles pour le support GIS

from django.conf import settings  \# Pour la référence de l'utilisateur authentifié

from django.utils import timezone  \# Pour gérer les dates et heures

class Competition(models.Model):

   *"""*

   *Modèle représentant une compétition. Inclut des informations telles que le nom,*

   *la description, les dates, l'adresse, le type et les catégories associées.*

   *"""*

   nom \= models.CharField(

       max\_length\=**255,**

       verbose\_name\="Nom de la compétition"**,**

       default\="Compétition sans nom"

   )

   description \= models.TextField(

       blank\=True**,**

       verbose\_name\="Description de la compétition"

   )

   \# Champs pour les dates avec des valeurs par défaut pour la date de début

   date\_debut \= models.DateTimeField(

       verbose\_name\="Date de début"**,**

       default\=timezone.now

   )

   date\_fin \= models.DateTimeField(

       verbose\_name\="Date de fin"**,**

       blank\=True**,**

       null\=True

   )

   \# Lieu géographique avec possibilité de le laisser vide

   lieu \= geomodels.PointField(

       null\=True**,**

       blank\=True**,**

       geography\=True**,**

       verbose\_name\="Lieu de la compétition"

   )

   adresse \= models.CharField(

       max\_length\=**255,**

       verbose\_name\="Adresse de la compétition"**,**

       default\="Adresse à définir"

   )

   \# Ajout de la bannière de la compétition

   bannière \= models.ImageField(

       upload\_to\='competitions/banners/'**,**

       blank\=True**,**

       null\=True

   )

   \# Choix du type de compétition avec des valeurs prédéfinies

   TYPE\_COMPETITION\_CHOICES \= \[

       ('quyen'**,** 'Techniques Traditionnelles (Quyen/Kata)')**,**

       ('quyen\_sync'**,** 'Quyen/Kata Synchronisé')**,**

       ('combat\_libre'**,** 'Combat Libre (Vo Dai/Full Contact)')**,**

       ('combat\_codifie'**,** 'Combat Codifié')**,**

       ('song\_luyen'**,** 'Song Luyen (Combat Synchronisé)')**,**

       ('armes'**,** 'Combat avec Armes')**,**

       ('demonstration'**,** 'Démonstration')**,**

       ('casse'**,** 'Épreuves de Casse')**,**

       ('armes\_trad'**,** 'Kata/Quyen avec Armes Traditionnelles')

   \]

   type\_competition \= models.CharField(

       max\_length\=**50,**

       choices\=TYPE\_COMPETITION\_CHOICES**,**

       verbose\_name\="Type de compétition"**,**

       default\='quyen'

   )

   \# Références vers les organisateurs possibles

   club \= models.ForeignKey(

       'clubs.Club'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       blank\=True**,**

       related\_name\="competitions\_club"**,**

       verbose\_name\="Club organisateur"

   )

   federation \= models.ForeignKey(

       'federations.Federation'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       blank\=True**,**

       related\_name\="competitions\_federation"**,**

       verbose\_name\="Fédération organisatrice"

   )

   academie \= models.ForeignKey(

       'academies.Academie'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       blank\=True**,**

       related\_name\="competitions\_academie"**,**

       verbose\_name\="Académie organisatrice"

   )

   \# Références vers les catégories et tranches d'âge

   tranches\_age \= models.ManyToManyField(

       'categories\_app.TrancheAge'**,**

       related\_name\="competitions\_age"**,**

       verbose\_name\="Tranches d'âge"

   )

   categories\_grades \= models.ManyToManyField(

       'categories\_app.CategoryGrade'**,**

       related\_name\="competitions\_grades"**,**

       verbose\_name\="Catégories de grades"

   )

   \# Autres catégories comme les armes, les combats, et les démonstrations

   categories\_armes \= models.ManyToManyField(

       'categories\_app.CategoryArme'**,**

       related\_name\="competitions\_armes"**,**

       verbose\_name\="Catégories d'armes"

   )

   categories\_combats \= models.ManyToManyField(

       'categories\_app.CategoryCombat'**,**

       related\_name\="competitions\_combats"**,**

       verbose\_name\="Catégories de combats"

   )

   categories\_demonstrations \= models.ManyToManyField(

       'categories\_app.CategoryDemonstration'**,**

       related\_name\="competitions\_demonstrations"**,**

       verbose\_name\="Catégories de démonstrations"

   )

   \# Arbitres de la compétition

   arbitres \= models.ManyToManyField(

       settings.AUTH\_USER\_MODEL**,**

       related\_name\="competitions\_arbitres"**,**

       verbose\_name\="Arbitres"

   )

   def \_\_str\_\_(self):

       return self.nom

class ExternalClub(models.Model):

   *"""*

   *Modèle représentant un club externe, non enregistré dans l'application Martial Hub.*

   *"""*

   nom \= models.CharField(max\_length\=**255**)

   adresse \= models.CharField(max\_length\=**255**)

   contact \= models.CharField(max\_length\=**100,** blank\=True**,** null\=True)

   email \= models.EmailField(blank\=True**,** null\=True)

   def \_\_str\_\_(self):

       return self.nom

class ExternalParticipant(models.Model):

   *"""*

   *Modèle représentant un participant externe, qui n'est pas inscrit dans l'application Martial Hub.*

   *Permet de gérer les inscriptions externes.*

   *"""*

   nom \= models.CharField(max\_length\=**255**)

   prenom \= models.CharField(max\_length\=**255**)

   email \= models.EmailField(blank\=False**,** null\=False**,** verbose\_name\="Adresse e-mail")

   date\_naissance \= models.DateField(verbose\_name\="Date de naissance")

   grade \= models.ForeignKey(

       'categories\_app.CategoryGrade'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       verbose\_name\="Grade"

   )

   club\_externe \= models.ForeignKey(

       ExternalClub**,**

       on\_delete\=models.CASCADE**,**

       related\_name\='participants'

   )

   competition \= models.ForeignKey(

       Competition**,**

       on\_delete\=models.CASCADE**,**

       related\_name\='external\_participants'

   )

   \# Champs booléens pour les types de participation

   participe\_technique \= models.BooleanField(default\=False**,** verbose\_name\="Participe à la compétition Technique")

   categorie\_technique \= models.ForeignKey(

       'categories\_app.CategoryGrade'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       related\_name\="technique\_participants"

   )

   participe\_combat \= models.BooleanField(default\=False**,** verbose\_name\="Participe à la compétition Combat")

   categorie\_combat \= models.ForeignKey(

       'categories\_app.CategoryCombat'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       related\_name\="combat\_participants"

   )

   participe\_demonstration \= models.BooleanField(default\=False**,**

                                                 verbose\_name\="Participe à la compétition Démonstration")

   categorie\_demonstration \= models.ForeignKey(

       'categories\_app.CategoryDemonstration'**,**

       on\_delete\=models.SET\_NULL**,**

       null\=True**,**

       related\_name\="demonstration\_participants"

   )

   \# Autres types de participation spécifiques

   participe\_technique\_sync \= models.BooleanField(default\=False**,**

                                                  verbose\_name\="Participe à la compétition technique synchronisé")

   participe\_song\_luyen \= models.BooleanField(default\=False**,** verbose\_name\="Participe à la compétition Song Luyen")

   participe\_technique\_individuelle \= models.BooleanField(default\=False**,**

                                                          verbose\_name\="Participe à la technique individuelle Co Vo Dao")

   participe\_combat\_arme \= models.BooleanField(default\=False**,** verbose\_name\="Participe aux combats armes Co Vo Dao")

   def \_\_str\_\_(self):

       return f'{self.prenom} {self.nom} ({self.club\_externe.nom})'

1. Modèle de vue de l’application compétitions : **views.py** 

from django.shortcuts import render**,** redirect**,** get\_object\_or\_404  
from django.contrib import messages  
from django.contrib.auth.decorators import login\_required  
from django.contrib.auth import get\_user\_model  
from django.views.decorators.csrf import csrf\_exempt  
from django.http import JsonResponse

\# Importation des formulaires nécessaires  
from .forms import (  
   CompetitionForm**,** TrancheAgeForm**,** CategoryGradeForm**,** CategoryArmeForm**,** CategoryCombatForm**,**  
   CategoryDemonstrationForm**,** NoteForm**,** ExternalParticipantForm  
)

\# Importation des modèles depuis le module 'competitions' et 'categories'  
from .models import Competition**,** ExternalParticipant  
from categories.models import TrancheAge**,** CategoryGrade**,** CategoryArme**,** CategoryCombat**,** CategoryDemonstration  
from .note import Note  \# Import du modèle Note depuis le fichier note.py

\# Vue pour lister toutes les compétitions  
@login\_required  
def liste\_competitions(request):  
   *"""*  
   *Affiche la liste de toutes les compétitions.*  
   *"""*  
   competitions \= Competition.objects.all()  
   return render(request**,** 'competitions/liste\_competitions.html'**,** {'competitions': competitions})

\# Vue pour créer une nouvelle compétition  
@login\_required  
def creer\_competition(request):  
   *"""*  
   *Permet de créer une nouvelle compétition.*  
   *"""*  
   if request.method \== 'POST':  
       form \= CompetitionForm(request.POST**,** request.FILES)  
       if form.is\_valid():  
           competition \= form.save()  
           messages.success(request**,** 'Compétition créée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de la création de la compétition.')  
   else:  
       form \= CompetitionForm()

   return render(request**,** 'competitions/creer\_competition.html'**,** {'form': form})

\# Vue pour afficher les détails d'une compétition  
@login\_required  
def detail\_competition(request**,** competition\_id):  
   *"""*  
   *Affiche les détails d'une compétition spécifique, y compris les participants externes.*  
   *"""*  
   competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)  
   participants\_externes \= ExternalParticipant.objects.filter(competition\=competition)  
   return render(request**,** 'competitions/detail\_competition.html'**,** {'competition': competition**,** 'participants\_externes': participants\_externes})

\# Vue pour modifier une compétition existante  
@login\_required  
def modifier\_competition(request**,** competition\_id):  
   *"""*  
   *Permet de modifier les informations d'une compétition existante.*  
   *"""*  
   competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)  
   if request.method \== 'POST':  
       form \= CompetitionForm(request.POST**,** request.FILES**,** instance\=competition)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Compétition modifiée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de la modification de la compétition.')  
   else:  
       form \= CompetitionForm(instance\=competition)

   return render(request**,** 'competitions/modifier\_competition.html'**,** {'form': form**,** 'competition': competition})

\# Vue pour supprimer une compétition  
@login\_required  
def supprimer\_competition(request**,** competition\_id):  
   *"""*  
   *Permet de supprimer une compétition.*  
   *"""*  
   competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)  
   if request.method \== 'POST':  
       competition.delete()  
       messages.success(request**,** 'Compétition supprimée avec succès.')  
       return redirect('competitions:liste\_competitions')

   return render(request**,** 'competitions/supprimer\_competition.html'**,** {'competition': competition})

\# Vue pour ajouter une tranche d'âge  
@login\_required  
def ajouter\_tranche\_age(request):  
   *"""*  
   *Permet d'ajouter une tranche d'âge.*  
   *"""*  
   if request.method \== 'POST':  
       form \= TrancheAgeForm(request.POST)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Tranche d\\'âge ajoutée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la tranche d\\'âge.')  
   else:  
       form \= TrancheAgeForm()

   return render(request**,** 'competitions/ajouter\_tranche\_age.html'**,** {'form': form})

\# Vue pour ajouter une catégorie de grade  
@login\_required  
def ajouter\_category\_grade(request):  
   *"""*  
   *Permet d'ajouter une catégorie de grade.*  
   *"""*  
   if request.method \== 'POST':  
       form \= CategoryGradeForm(request.POST)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Catégorie de grade ajoutée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la catégorie de grade.')  
   else:  
       form \= CategoryGradeForm()

   return render(request**,** 'competitions/ajouter\_category\_grade.html'**,** {'form': form})

\# Vue pour ajouter une catégorie d'arme  
@login\_required  
def ajouter\_category\_arme(request):  
   *"""*  
   *Permet d'ajouter une catégorie d'arme.*  
   *"""*  
   if request.method \== 'POST':  
       form \= CategoryArmeForm(request.POST)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Catégorie d\\'arme ajoutée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la catégorie d\\'arme.')  
   else:  
       form \= CategoryArmeForm()

   return render(request**,** 'competitions/ajouter\_category\_arme.html'**,** {'form': form})

\# Vue pour ajouter une catégorie de combat  
@login\_required  
def ajouter\_category\_combat(request):  
   *"""*  
   *Permet d'ajouter une catégorie de combat.*  
   *"""*  
   if request.method \== 'POST':  
       form \= CategoryCombatForm(request.POST)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Catégorie de combat ajoutée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la catégorie de combat.')  
   else:  
       form \= CategoryCombatForm()

   return render(request**,** 'competitions/ajouter\_category\_combat.html'**,** {'form': form})

\# Vue pour ajouter une catégorie de démonstration  
@login\_required  
def ajouter\_category\_demonstration(request):  
   *"""*  
   *Permet d'ajouter une catégorie de démonstration.*  
   *"""*  
   if request.method \== 'POST':  
       form \= CategoryDemonstrationForm(request.POST)  
       if form.is\_valid():  
           form.save()  
           messages.success(request**,** 'Catégorie de démonstration ajoutée avec succès.')  
           return redirect('competitions:liste\_competitions')  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la catégorie de démonstration.')  
   else:  
       form \= CategoryDemonstrationForm()

   return render(request**,** 'competitions/ajouter\_category\_demonstration.html'**,** {'form': form})

\# Vue pour noter un membre  
@login\_required  
def noter\_membre(request**,** competition\_id**,** membre\_id):  
   *"""*  
   *Permet de noter un membre pendant une compétition.*  
   *"""*  
   competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)  
   if request.method \== 'POST':  
       form \= NoteForm(request.POST)  
       if form.is\_valid():  
           note \= form.save(commit\=False)  
           note.competition \= competition  
           note.membre\_id \= membre\_id  
           note.save()  
           messages.success(request**,** 'Note ajoutée avec succès.')  
           return redirect('competitions:detail\_competition'**,** competition\_id\=competition.id)  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout de la note.')  
   else:  
       form \= NoteForm()

   return render(request**,** 'competitions/noter\_membre.html'**,** {'form': form**,** 'competition': competition})

\# Vue pour ajouter un membre à une compétition via un glisser-déposer  
@csrf\_exempt  
@login\_required  
def ajouter\_membre\_competition(request):  
   *"""*  
   *Permet d'ajouter un membre à une compétition via un glisser-déposer.*  
   *"""*  
   if request.method \== 'POST':  
       membre\_id \= request.POST.get('membre\_id')  
       competition\_id \= request.POST.get('competition\_id')

       membre \= get\_object\_or\_404(Membre**,** id\=membre\_id)  
       competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)

       competition.membres.add(membre)  
       return JsonResponse({"success": True})

\# Vue pour ajouter un participant externe à une compétition  
@login\_required  
def ajouter\_participant\_externe(request**,** competition\_id):  
   *"""*  
   *Permet d'ajouter un participant externe à une compétition spécifique.*  
   *"""*  
   competition \= get\_object\_or\_404(Competition**,** id\=competition\_id)  
   if request.method \== 'POST':  
       form \= ExternalParticipantForm(request.POST)  
       if form.is\_valid():  
           participant \= form.save(commit\=False)  
           participant.competition \= competition  
           participant.save()  
           messages.success(request**,** 'Participant externe ajouté avec succès.')  
           return redirect('competitions:detail\_competition'**,** competition\_id\=competition.id)  
       else:  
           messages.error(request**,** 'Erreur lors de l\\'ajout du participant externe.')  
   else:  
       form \= ExternalParticipantForm()

   return render(request**,** 'competitions/ajouter\_participant\_externe.html'**,**

1. Voici le modèle forme : **forms.py** 

**from django import forms**  
**from .note import Note**  
**from .models import Competition, ExternalParticipant**  
**from categories.models import TrancheAge, CategoryGrade, CategoryArme, CategoryCombat, CategoryDemonstration**

**\# Formulaire principal pour gérer les compétitions**  
**class CompetitionForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une compétition. Gère les relations avec les catégories,***  
   ***les tranches d'âge, les arbitres, et la bannière de la compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= Competition**  
       **fields \= \[**  
           **'nom', 'description', 'date\_debut', 'date\_fin', 'lieu', 'adresse',**  
           **'type\_competition', 'club', 'federation', 'academie', 'tranches\_age',**  
           **'categories\_grades', 'categories\_armes', 'categories\_combats',**  
           **'categories\_demonstrations', 'arbitres', 'bannière'**  
       **\]**  
       **widgets \= {**  
           **'date\_debut': forms.DateTimeInput(attrs\={'type': 'datetime-local', 'class': 'form-control'}),**  
           **'date\_fin': forms.DateTimeInput(attrs\={'type': 'datetime-local', 'class': 'form-control'}),**  
           **'lieu': forms.TextInput(attrs\={'placeholder': 'Latitude, Longitude', 'class': 'form-control'}),**  
           **'adresse': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'description': forms.Textarea(attrs\={'rows': 3, 'class': 'form-control'}),**  
           **'tranches\_age': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
           **'categories\_grades': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
           **'categories\_armes': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
           **'categories\_combats': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
           **'categories\_demonstrations': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
           **'arbitres': forms.CheckboxSelectMultiple(attrs\={'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter une tranche d'âge**  
**class TrancheAgeForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une tranche d'âge associée à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= TrancheAge**  
       **fields \= \['nom', 'age\_min', 'age\_max'\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'age\_min': forms.NumberInput(attrs\={'placeholder': 'Âge minimum', 'class': 'form-control'}),**  
           **'age\_max': forms.NumberInput(attrs\={'placeholder': 'Âge maximum', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter une catégorie de grade**  
**class CategoryGradeForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une catégorie de grade associée à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= CategoryGrade**  
       **fields \= \['nom', 'grade\_min', 'grade\_max'\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'grade\_min': forms.TextInput(attrs\={'placeholder': 'Grade minimum', 'class': 'form-control'}),**  
           **'grade\_max': forms.TextInput(attrs\={'placeholder': 'Grade maximum', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter une catégorie d'arme**  
**class CategoryArmeForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une catégorie d'arme associée à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= CategoryArme**  
       **fields \= \['nom', 'description'\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'description': forms.Textarea(attrs\={'rows': 3, 'placeholder': 'Description de la catégorie d\\'arme', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter une catégorie de combat**  
**class CategoryCombatForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une catégorie de combat associée à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= CategoryCombat**  
       **fields \= \['nom', 'description'\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'description': forms.Textarea(attrs\={'rows': 3, 'placeholder': 'Description de la catégorie de combat', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter une catégorie de démonstration**  
**class CategoryDemonstrationForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour créer ou modifier une catégorie de démonstration associée à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= CategoryDemonstration**  
       **fields \= \['nom', 'description'\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'description': forms.Textarea(attrs\={'rows': 3, 'placeholder': 'Description de la démonstration', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour noter un membre**  
**class NoteForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour noter un membre lors d'une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= Note**  
       **fields \= \['membre', 'competition', 'arbitre', 'score'\]**  
       **widgets \= {**  
           **'membre': forms.Select(attrs\={'class': 'form-control'}),**  
           **'competition': forms.Select(attrs\={'class': 'form-control'}),**  
           **'arbitre': forms.Select(attrs\={'class': 'form-control'}),**  
           **'score': forms.NumberInput(attrs\={'step': 0.01, 'placeholder': 'Score du membre', 'class': 'form-control'}),**  
       **}**

**\# Formulaire pour ajouter un participant externe**  
**class ExternalParticipantForm(forms.ModelForm):**  
   ***"""***  
   ***Formulaire pour enregistrer un participant externe à une compétition.***  
   ***"""***  
   **class Meta:**  
       **model \= ExternalParticipant**  
       **fields \= \[**  
           **'nom', 'prenom', 'email', 'date\_naissance', 'grade', 'club\_externe',**  
           **'participe\_technique', 'categorie\_technique',**  
           **'participe\_combat', 'categorie\_combat',**  
           **'participe\_demonstration', 'categorie\_demonstration',**  
           **'participe\_technique\_sync', 'participe\_song\_luyen',**  
           **'participe\_technique\_individuelle', 'participe\_combat\_arme'**  
       **\]**  
       **widgets \= {**  
           **'nom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'prenom': forms.TextInput(attrs\={'class': 'form-control'}),**  
           **'email': forms.EmailInput(attrs\={'class': 'form-control'}),**  
           **'date\_naissance': forms.DateInput(attrs\={'type': 'date', 'class': 'form-control'}),**  
           **'grade': forms.Select(attrs\={'class': 'form-control'}),**  
           **'club\_externe': forms.Select(attrs\={'class': 'form-control'}),**  
           **'participe\_technique': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'categorie\_technique': forms.Select(attrs\={'class': 'form-control'}),**  
           **'participe\_combat': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'categorie\_combat': forms.Select(attrs\={'class': 'form-control'}),**  
           **'participe\_demonstration': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'categorie\_demonstration': forms.Select(attrs\={'class': 'form-control'}),**  
           **'participe\_technique\_sync': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'participe\_song\_luyen': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'participe\_technique\_individuelle': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
           **'participe\_combat\_arme': forms.CheckboxInput(attrs\={'class': 'form-check-input'}),**  
       **}**

1. **Voici le modèle de notation : note.py** 

**from django.db import models**  
**from membres.models import Membre  \# Importation correcte du modèle Membre**  
**from django.contrib.auth import get\_user\_model**  
**from competitions.models import Competition  \# Importation correcte du modèle Competition**

**User \= get\_user\_model()**

**class Note(models.Model):**  
   ***"""***  
   ***Modèle représentant une note donnée par un arbitre à un membre lors d'une compétition.***  
   ***"""***  
   **membre \= models.ForeignKey(**  
       **Membre,**  
       **on\_delete\=models.CASCADE,**  
       **related\_name\="notes\_membre",**  
       **verbose\_name\="Membre"**  
   **)**  
   **competition \= models.ForeignKey(**  
       **Competition,**  
       **on\_delete\=models.CASCADE,**  
       **related\_name\="notes\_competition",**  
       **verbose\_name\="Compétition"**  
   **)**  
   **arbitre \= models.ForeignKey(**  
       **User,**  
       **on\_delete\=models.CASCADE,**  
       **related\_name\="notes\_arbitre",**  
       **verbose\_name\="Arbitre"**  
   **)**  
   **score \= models.DecimalField(**  
       **max\_digits\=5,**  
       **decimal\_places\=2,**  
       **verbose\_name\="Score",**  
       **help\_text\="Le score doit être compris entre 0 et 10 avec un pas de 0.25."**  
   **)**

   **def \_\_str\_\_(self):**  
       **return f'Note de {self.membre} par {self.arbitre}'**

   **class Meta:**  
       **verbose\_name \= "Note"**  
       **verbose\_name\_plural \= "Notes"**  
       **ordering \= \['competition', 'arbitre', 'membre'\]**

   **def clean(self):**  
       ***"""***  
       ***Validation du score pour s'assurer qu'il se situe entre 0 et 10 avec un incrément de 0.25.***  
       ***"""***  
       **from django.core.exceptions import ValidationError**

       **if not (0 \<= self.score \<= 10):**  
           **raise ValidationError("Le score doit être compris entre 0 et 10.")**  
       **if (self.score \* 100) % 25 \!= 0:**  
           **raise ValidationError("Le score doit être un multiple de 0.25.")**

   **def save(self, \*args, \*\*kwargs):**  
       ***"""***  
       ***Override de la méthode save pour inclure la validation custom du score.***  
       ***"""***  
       **self.clean()  \# Appeler la validation avant l'enregistrement**  
       **super().save(\*args, \*\*kwargs)**

1. **Voici le fichier urls.py**

**from django.urls import path**  
**from . import views**

**app\_name \= 'competitions'**

**urlpatterns \= \[**  
   **\# Liste des compétitions disponibles**  
   **path('', views.liste\_competitions, name\='liste\_competitions'),**

   **\# Création d'une nouvelle compétition**  
   **path('creer/', views.creer\_competition, name\='creer\_competition'),**

   **\# Détail d'une compétition spécifique**  
   **path('\<int:competition\_id\>/', views.detail\_competition, name\='detail\_competition'),**

   **\# Modification d'une compétition existante**  
   **path('\<int:competition\_id\>/modifier/', views.modifier\_competition, name\='modifier\_competition'),**

   **\# Suppression d'une compétition existante**  
   **path('\<int:competition\_id\>/supprimer/', views.supprimer\_competition, name\='supprimer\_competition'),**

   **\# Ajout d'une tranche d'âge pour une compétition**  
   **path('tranches-age/ajouter/', views.ajouter\_tranche\_age, name\='ajouter\_tranche\_age'),**

   **\# Ajout d'une catégorie de grade pour une compétition**  
   **path('categories/grades/ajouter/', views.ajouter\_category\_grade, name\='ajouter\_category\_grade'),**

   **\# Ajout d'une catégorie d'arme pour une compétition**  
   **path('categories/armes/ajouter/', views.ajouter\_category\_arme, name\='ajouter\_category\_arme'),**

   **\# Ajout d'une catégorie de combat pour une compétition**  
   **path('categories/combats/ajouter/', views.ajouter\_category\_combat, name\='ajouter\_category\_combat'),**

   **\# Ajout d'une catégorie de démonstration pour une compétition**  
   **path('categories/demonstrations/ajouter/', views.ajouter\_category\_demonstration, name\='ajouter\_category\_demonstration'),**

   **\# Route pour noter un membre lors d'une compétition**  
   **path('\<int:competition\_id\>/noter/\<int:membre\_id\>/', views.noter\_membre, name\='noter\_membre'),**

   **\# Ajout d'un membre à une compétition par glisser-déposer via AJAX**  
   **path('ajouter\_membre/', views.ajouter\_membre\_competition, name\='ajouter\_membre\_competition'),**

   **\# Ajout d'un participant externe à une compétition**  
   **path('\<int:competition\_id\>/ajouter\_participant\_externe/', views.ajouter\_participant\_externe, name\='ajouter\_participant\_externe'),**  
**\]**

1. **Voici le modèle competition.py**

   **from django.db import models**  
2. **from django.contrib.gis.db import models as geomodels  \# Pour gérer les champs géographiques avec PostGIS**  
3. **from django.conf import settings  \# Pour utiliser le modèle d'utilisateur authentifié**  
4. **from categories.models import TrancheAge, CategoryGrade, CategoryArme, CategoryCombat, CategoryDemonstration**  
5.   
6.   
7. **class Competition(models.Model):**  
8.    ***"""***  
9.    ***Modèle représentant une compétition.***  
10.    ***"""***  
11.    **nom \= models.CharField(**  
12.        **max\_length\=255,**  
13.        **verbose\_name\="Nom de la compétition",**  
14.        **default\="Compétition sans nom"  \# Valeur par défaut si le nom n'est pas fourni**  
15.    **)**  
16.    **description \= models.TextField(**  
17.        **blank\=True,**  
18.        **verbose\_name\="Description de la compétition"**  
19.    **)**  
20.   
21.    **\# Champs pour les dates avec des valeurs par défaut pour la date de début**  
22.    **date\_debut \= models.DateTimeField(**  
23.        **verbose\_name\="Date de début",**  
24.        **default\=models.DateTimeField.now**  
25.    **)**  
26.    **date\_fin \= models.DateTimeField(**  
27.        **verbose\_name\="Date de fin",**  
28.        **blank\=True,**  
29.        **null\=True**  
30.    **)**  
31.   
32.    **\# Lieu géographique avec possibilité de le laisser vide**  
33.    **lieu \= geomodels.PointField(**  
34.        **null\=True,**  
35.        **blank\=True,**  
36.        **geography\=True,**  
37.        **verbose\_name\="Lieu de la compétition"**  
38.    **)**  
39.   
40.    **adresse \= models.CharField(**  
41.        **max\_length\=255,**  
42.        **verbose\_name\="Adresse de la compétition",**  
43.        **default\="Adresse à définir"**  
44.    **)**  
45.   
46.    **\# Ajout de la bannière de la compétition**  
47.    **bannière \= models.ImageField(**  
48.        **upload\_to\='competitions/banners/',**  
49.        **blank\=True,**  
50.        **null\=True**  
51.    **)**  
52.   
53.    **\# Choix du type de compétition avec des valeurs prédéfinies**  
54.    **TYPE\_COMPETITION\_CHOICES \= \[**  
55.        **('quyen', 'Techniques Traditionnelles (Quyen/Kata)'),**  
56.        **('quyen\_sync', 'Quyen/Kata Synchronisé'),**  
57.        **('combat\_libre', 'Combat Libre (Vo Dai/Full Contact)'),**  
58.        **('combat\_codifie', 'Combat Codifié'),**  
59.        **('song\_luyen', 'Song Luyen (Combat Synchronisé)'),**  
60.        **('armes', 'Combat avec Armes'),**  
61.        **('demonstration', 'Démonstration'),**  
62.        **('casse', 'Épreuves de Casse'),**  
63.        **('armes\_trad', 'Kata/Quyen avec Armes Traditionnelles')**  
64.    **\]**  
65.    **type\_competition \= models.CharField(**  
66.        **max\_length\=50,**  
67.        **choices\=TYPE\_COMPETITION\_CHOICES,**  
68.        **verbose\_name\="Type de compétition",**  
69.        **default\='quyen'**  
70.    **)**  
71.   
72.    **\# Références vers les organisateurs possibles**  
73.    **club \= models.ForeignKey(**  
74.        **'clubs.Club',**  
75.        **on\_delete\=models.SET\_NULL,**  
76.        **null\=True,**  
77.        **blank\=True,**  
78.        **related\_name\="competitions\_club",**  
79.        **verbose\_name\="Club organisateur"**  
80.    **)**  
81.    **federation \= models.ForeignKey(**  
82.        **'federations.Federation',**  
83.        **on\_delete\=models.SET\_NULL,**  
84.        **null\=True,**  
85.        **blank\=True,**  
86.        **related\_name\="competitions\_federation",**  
87.        **verbose\_name\="Fédération organisatrice"**  
88.    **)**  
89.    **academie \= models.ForeignKey(**  
90.        **'academies.Academie',**  
91.        **on\_delete\=models.SET\_NULL,**  
92.        **null\=True,**  
93.        **blank\=True,**  
94.        **related\_name\="competitions\_academie",**  
95.        **verbose\_name\="Académie organisatrice"**  
96.    **)**  
97.   
98.    **\# Références vers les catégories et tranches d'âge**  
99.    **tranches\_age \= models.ManyToManyField(**  
100.        **TrancheAge,**  
101.        **related\_name\="competitions\_age",**  
102.        **verbose\_name\="Tranches d'âge"**  
103.    **)**  
104.    **categories\_grades \= models.ManyToManyField(**  
105.        **CategoryGrade,**  
106.        **related\_name\="competitions\_grades",**  
107.        **verbose\_name\="Catégories de grades"**  
108.    **)**  
109.   
110.    **\# Autres catégories comme les armes, les combats, et les démonstrations**  
111.    **categories\_armes \= models.ManyToManyField(**  
112.        **CategoryArme,**  
113.        **related\_name\="competitions\_armes",**  
114.        **verbose\_name\="Catégories d'armes"**  
115.    **)**  
116.    **categories\_combats \= models.ManyToManyField(**  
117.        **CategoryCombat,**  
118.        **related\_name\="competitions\_combats",**  
119.        **verbose\_name\="Catégories de combats"**  
120.    **)**  
121.    **categories\_demonstrations \= models.ManyToManyField(**  
122.        **CategoryDemonstration,**  
123.        **related\_name\="competitions\_demonstrations",**  
124.        **verbose\_name\="Catégories de démonstrations"**  
125.    **)**  
126.   
127.    **\# Arbitres de la compétition**  
128.    **arbitres \= models.ManyToManyField(**  
129.        **settings.AUTH\_USER\_MODEL,**  
130.        **related\_name\="competitions\_arbitres",**  
131.        **verbose\_name\="Arbitres"**  
132.    **)**  
133.   
134.    **def \_\_str\_\_(self):**  
135.        **return self.nom**  
136.   
137.    **class Meta:**  
138.        **verbose\_name \= "Compétition"**  
139.        **verbose\_name\_plural \= "Compétitions"**  
140.        **ordering \= \['date\_debut', 'nom'\]**  
141.   
142.   
143. **class ExternalClub(models.Model):**  
144.    ***"""***  
145.    ***Modèle représentant un club externe, non enregistré dans l'application Martial Hub.***  
146.    ***"""***  
147.    **nom \= models.CharField(max\_length\=255, verbose\_name\="Nom du club externe")**  
148.    **adresse \= models.CharField(max\_length\=255, verbose\_name\="Adresse du club externe")**  
149.    **contact \= models.CharField(max\_length\=100, blank\=True, null\=True, verbose\_name\="Contact du club")**  
150.    **email \= models.EmailField(blank\=True, null\=True, verbose\_name\="Email du club")**  
151.   
152.    **def \_\_str\_\_(self):**  
153.        **return self.nom**  
154.   
155.    **class Meta:**  
156.        **verbose\_name \= "Club Externe"**  
157.        **verbose\_name\_plural \= "Clubs Externes"**  
158.        **ordering \= \['nom'\]**  
159.   
160.   
161. **class ExternalParticipant(models.Model):**  
162.    ***"""***  
163.    ***Modèle représentant un participant externe, qui n'est pas inscrit dans l'application Martial Hub.***  
164.    ***Permet de gérer les inscriptions externes.***  
165.    ***"""***  
166.    **nom \= models.CharField(max\_length\=255, verbose\_name\="Nom du participant")**  
167.    **prenom \= models.CharField(max\_length\=255, verbose\_name\="Prénom du participant")**  
168.    **email \= models.EmailField(blank\=False, null\=False, verbose\_name\="Adresse e-mail")**  
169.    **date\_naissance \= models.DateField(verbose\_name\="Date de naissance")**  
170.    **grade \= models.ForeignKey(**  
171.        **CategoryGrade,**  
172.        **on\_delete\=models.SET\_NULL,**  
173.        **null\=True,**  
174.        **verbose\_name\="Grade"**  
175.    **)**  
176.    **club\_externe \= models.ForeignKey(**  
177.        **ExternalClub,**  
178.        **on\_delete\=models.CASCADE,**  
179.        **related\_name\='participants',**  
180.        **verbose\_name\="Club Externe"**  
181.    **)**  
182.    **competition \= models.ForeignKey(**  
183.        **Competition,**  
184.        **on\_delete\=models.CASCADE,**  
185.        **related\_name\='external\_participants',**  
186.        **verbose\_name\="Compétition"**  
187.    **)**  
188.   
189.    **\# Champs booléens pour les types de participation**  
190.    **participe\_technique \= models.BooleanField(default\=False, verbose\_name\="Participe à la compétition Technique")**  
191.    **categorie\_technique \= models.ForeignKey(**  
192.        **CategoryGrade,**  
193.        **on\_delete\=models.SET\_NULL,**  
194.        **null\=True,**  
195.        **related\_name\="technique\_participants",**  
196.        **verbose\_name\="Catégorie Technique"**  
197.    **)**  
198.   
199.    **participe\_combat \= models.BooleanField(default\=False, verbose\_name\="Participe à la compétition Combat")**  
200.    **categorie\_combat \= models.ForeignKey(**  
201.        **CategoryCombat,**  
202.        **on\_delete\=models.SET\_NULL,**  
203.        **null\=True,**  
204.        **related\_name\="combat\_participants",**  
205.        **verbose\_name\="Catégorie Combat"**  
206.    **)**  
207.   
208.    **participe\_demonstration \= models.BooleanField(default\=False, verbose\_name\="Participe à la compétition Démonstration")**  
209.    **categorie\_demonstration \= models.ForeignKey(**  
210.        **CategoryDemonstration,**  
211.        **on\_delete\=models.SET\_NULL,**  
212.        **null\=True,**  
213.        **related\_name\="demonstration\_participants",**  
214.        **verbose\_name\="Catégorie Démonstration"**  
215.    **)**  
216.   
217.    **\# Autres types de participation spécifiques**  
218.    **participe\_technique\_sync \= models.BooleanField(default\=False, verbose\_name\="Participe à la compétition technique synchronisé")**  
219.    **participe\_song\_luyen \= models.BooleanField(default\=False, verbose\_name\="Participe à la compétition Song Luyen")**  
220.    **participe\_technique\_individuelle \= models.BooleanField(default\=False, verbose\_name\="Participe à la technique individuelle Co Vo Dao")**  
221.    **participe\_combat\_arme \= models.BooleanField(default\=False, verbose\_name\="Participe aux combats armes Co Vo Dao")**  
222.   
223.    **def \_\_str\_\_(self):**  
224.        **return f'{self.prenom} {self.nom} ({self.club\_externe.nom})'**  
225.   
226.    **class Meta:**  
227.        **verbose\_name \= "Participant Externe"**  
228.        **verbose\_name\_plural \= "Participants Externes"**  
229.        **ordering \= \['nom', 'prenom'\]**  
230. 

**D'accord, je vais clarifier l'ensemble des scripts à générer, en mentionnant les noms des fichiers, les applications concernées, ainsi que leur contenu. Je vais vous fournir une liste complète des évolutions avec les fichiers correspondants et leur emplacement dans votre projet.**

## **Applications impactées :**

1. **Competitions (pour gérer les compétitions, matchs, scores, types de compétitions)**  
2. **Membres (pour gérer les participants)**  
3. **Clubs (pour les équipes et affiliations)**

### **1\. Application Competitions**

**Fichier : models.py**

* **Script : Modèle des compétitions, des matchs et des équipes**  
* **Explication : Ce fichier inclut les types de compétitions (Kata, Quyen, Combat), ainsi que les systèmes de notation spécifiques pour chaque type.**

**python**  
**Copier le code**  
**`# Application : competitions`**

**`from django.db import models`**  
**`from django.contrib.gis.db import models as geomodels`**

**`class DisciplineArtMartial(models.Model):`**  
    **`"""`**  
    **`Modèle représentant une discipline d'art martial (Kata, Quyen, Combat).`**  
    **`"""`**  
    **`nom = models.CharField(max_length=100)`**  
    **`systeme_score = models.JSONField()  # Stocker les règles de score spécifiques à la discipline`**  
    **`regles_penalites = models.JSONField()  # Stocker les règles de pénalités spécifiques à la discipline`**

    **`def __str__(self):`**  
        **`return self.nom`**

**`class Competition(models.Model):`**  
    **`"""`**  
    **`Modèle représentant une compétition. Peut être de type Combat, Kata, Quyen, ou Katas synchronisés.`**  
    **`"""`**  
    **`nom = models.CharField(max_length=255)`**  
    **`description = models.TextField(blank=True)`**  
    **`date_debut = models.DateTimeField()`**  
    **`date_fin = models.DateTimeField(blank=True, null=True)`**  
    **`lieu = geomodels.PointField(null=True, blank=True, geography=True)`**  
    **`adresse = models.CharField(max_length=255)`**

    **`TYPE_COMPETITION_CHOICES = [`**  
        **`('kata', 'Kata/Quyen'),`**  
        **`('kata_sync', 'Kata/Quyen Synchronisé'),`**  
        **`('combat', 'Combat'),`**  
    **`]`**  
    **`type_competition = models.CharField(max_length=20, choices=TYPE_COMPETITION_CHOICES)`**  
    **`discipline = models.ForeignKey(DisciplineArtMartial, on_delete=models.CASCADE)`**

    **`equipe = models.BooleanField(default=False)`**  
    **`taille_equipe = models.IntegerField(default=1)  # Pour les compétitions par équipe`**

    **`def __str__(self):`**  
        **`return self.nom`**

**`class Match(models.Model):`**  
    **`"""`**  
    **`Modèle représentant un match dans une compétition (Combat, Kata ou Kata synchronisé).`**  
    **`"""`**  
    **`competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="matchs")`**  
    **`participant_a = models.ForeignKey('membres.Membre', on_delete=models.CASCADE, related_name="matchs_a")`**  
    **`participant_b = models.ForeignKey('membres.Membre', on_delete=models.CASCADE, related_name="matchs_b")`**

    **`score_a = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Score pour les combats`**  
    **`score_b = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)`**

    **`# Notation pour les compétitions techniques (Kata, Quyen)`**  
    **`score_technique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`**  
    **`score_esthetique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`**  
    **`score_precision = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`**

    **`def __str__(self):`**  
        **`return f'Match {self.competition.nom} : {self.participant_a} vs {self.participant_b}'`**

---

**Fichier : views.py**

* **Script : Vues pour gérer la création de compétitions, la gestion des scores (différents pour chaque type de compétition).**  
* **Explication : Cette vue contient les actions pour créer des compétitions et gérer les scores des matchs.**

**python**  
**Copier le code**  
**`# Application : competitions`**

**`from django.shortcuts import render, get_object_or_404, redirect`**  
**`from django.http import JsonResponse`**  
**`from .models import Competition, Match`**  
**`from .forms import CompetitionForm, MatchForm`**

**`# Vue pour créer une nouvelle compétition`**  
**`def creer_competition(request):`**  
    **`if request.method == 'POST':`**  
        **`form = CompetitionForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`return redirect('competitions:liste_competitions')`**  
    **`else:`**  
        **`form = CompetitionForm()`**  
    **`return render(request, 'competitions/creer_competition.html', {'form': form})`**

**`# Vue pour mettre à jour les scores des matchs`**  
**`def maj_score(request, match_id):`**  
    **`match = get_object_or_404(Match, id=match_id)`**  
    **`if request.method == 'POST':`**  
        **`# Si c'est une compétition de combat, utiliser un score simple`**  
        **`if match.competition.type_competition == 'combat':`**  
            **`match.score_a = request.POST.get('score_a')`**  
            **`match.score_b = request.POST.get('score_b')`**  
        **`else:`**  
            **`# Si c'est une compétition technique (Kata/Quyen)`**  
            **`match.score_technique = request.POST.get('score_technique')`**  
            **`match.score_esthetique = request.POST.get('score_esthetique')`**  
            **`match.score_precision = request.POST.get('score_precision')`**  
        **`match.save()`**  
        **`return JsonResponse({'success': True})`**  
    **`return render(request, 'competitions/maj_score.html', {'match': match})`**

---

**Fichier : forms.py**

* **Script : Formulaires pour créer des compétitions et gérer les matchs.**  
* **Explication : Ce formulaire permet de créer une compétition en choisissant le type (Combat, Kata ou Kata synchronisé), et de mettre à jour les scores.**

**python**  
**Copier le code**  
**`# Application : competitions`**

**`from django import forms`**  
**`from .models import Competition, Match`**

**`class CompetitionForm(forms.ModelForm):`**  
    **`class Meta:`**  
        **`model = Competition`**  
        **`fields = ['nom', 'description', 'date_debut', 'date_fin', 'lieu', 'type_competition', 'discipline', 'equipe', 'taille_equipe']`**

**`class MatchForm(forms.ModelForm):`**  
    **`class Meta:`**  
        **`model = Match`**  
        **`fields = ['participant_a', 'participant_b', 'score_a', 'score_b', 'score_technique', 'score_esthetique', 'score_precision']`**

---

**Fichier : urls.py**

* **Script : Routage pour les compétitions**  
* **Explication : Liste les routes pour la création et la gestion des compétitions.**

**python**  
**Copier le code**  
**`# Application : competitions`**

**`from django.urls import path`**  
**`from . import views`**

**`app_name = 'competitions'`**

**`urlpatterns = [`**  
    **`path('creer/', views.creer_competition, name='creer_competition'),`**  
    **`path('maj_score/<int:match_id>/', views.maj_score, name='maj_score'),`**  
    **`path('', views.liste_competitions, name='liste_competitions'),`**  
**`]`**

---

**Fichier : templates/competitions/creer\_competition.html**

* **Script : Template pour créer une compétition**  
* **Explication : Interface utilisateur pour créer une nouvelle compétition avec les différents types.**

**html**  
**Copier le code**  
**`{% extends "base_generic.html" %}`**

**`{% block content %}`**  
**`<div class="container mt-5">`**  
    **`<h2>Créer une nouvelle compétition</h2>`**  
    **`<form method="post">`**  
        **`{% csrf_token %}`**  
        **`{{ form.as_p }}`**  
        **`<button type="submit" class="btn btn-primary">Créer</button>`**  
    **`</form>`**  
**`</div>`**  
**`{% endblock %}`**

---

**Fichier : templates/competitions/maj\_score.html**

* **Script : Template pour gérer les scores**  
* **Explication : Template pour la mise à jour des scores (différents selon le type de compétition).**

**`{% extends "base_generic.html" %}`**

**`{% block content %}`**  
**`<div class="container mt-5">`**  
    **`<h2>Mettre à jour les scores pour le match {{ match.participant_a }} vs {{ match.participant_b }}</h2>`**  
    **`<form method="post" id="score-form">`**  
        **`{% csrf_token %}`**  
        **`{% if match.competition.type_competition == 'combat' %}`**  
            **`<div class="form-group">`**  
                **`<label for="score_a">Score de {{ match.participant_a }} :</label>`**  
                **`<input type="number" step="0.1" name="score_a" value="{{ match.score_a }}" class="form-control">`**  
            **`</div>`**  
            **`<div class="form-group">`**  
                **`<label for="score_b">Score de {{ match.participant_b }} :</label>`**  
                **`<input type="number" step="0.1" name="score_b" value="{{ match.score_b }}" class="form-control">`**  
            **`</div>`**  
        **`{% else %}`**  
            **`<div class="form-group">`**  
                **`<label for="score_technique">Score Technique :</label>`**  
                **`<input type="number" step="0.1" name="score_technique" value="{{ match.score_technique }}" class="form-control">`**  
            **`</div>`**  
            **`<div class="form-group">`**  
                **`<label for="score_esthetique">Score Esthétique :</label>`**  
                **`<input type="number" step="0.1" name="score_esthetique" value="{{ match.score_esthetique }}" class="form-control">`**  
            **`</div>`**  
            **`<div class="form-group">`**  
                **`<label for="score_precision">Score Précision :</label>`**  
                **`<input`**  
               **`<input type="number" step="0.1" name="score_precision" value="{{ match.score_precision }}" class="form-control">`**  
            **`</div>`**  
        **`{% endif %}`**  
        **`<button type="submit" class="btn btn-primary mt-4">Mettre à jour les scores</button>`**  
    **`</form>`**  
**`</div>`**

**`<script>`**  
    **`document.getElementById('score-form').addEventListener('submit', function(event) {`**  
        **`event.preventDefault();`**  
        **`var form = new FormData(this);`**  
          
        **`fetch("{% url 'competitions:maj_score' match.id %}", {`**  
            **`method: 'POST',`**  
            **`body: form,`**  
            **`headers: {`**  
                **`'X-CSRFToken': "{{ csrf_token }}"`**  
            **`}`**  
        **`}).then(response => response.json())`**  
        **`.then(data => {`**  
            **`if (data.success) {`**  
                **`alert('Scores mis à jour avec succès');`**  
            **`}`**  
        **`});`**  
    **`});`**  
**`</script>`**  
**`{% endblock %}`**

### **2\. Application Membres**

**Fichier : models.py**

* **Script : Gestion des membres participant aux compétitions.**  
* **Explication : Modèle pour gérer les membres et leur inscription aux différentes compétitions (combat, kata, etc.).**

**python**  
**Copier le code**  
**`# Application : membres`**

**`from django.db import models`**  
**`from django.contrib.auth import get_user_model`**  
**`from clubs.models import Club`**

**`User = get_user_model()`**

**`class Membre(models.Model):`**  
    **`"""`**  
    **`Modèle représentant un membre participant à des compétitions.`**  
    **`"""`**  
    **`user = models.OneToOneField(User, on_delete=models.CASCADE)`**  
    **`nom = models.CharField(max_length=100)`**  
    **`prenom = models.CharField(max_length=100)`**  
    **`date_naissance = models.DateField()`**  
    **`club = models.ForeignKey(Club, on_delete=models.CASCADE)`**

    **`def __str__(self):`**  
        **`return f'{self.prenom} {self.nom}'`**

---

**Fichier : views.py**

* **Script : Vues pour gérer les membres et leur participation aux compétitions.**  
* **Explication : Gestion des membres participants et leur affiliation à une compétition.**

**python**  
**Copier le code**  
**`# Application : membres`**

**`from django.shortcuts import render, get_object_or_404`**  
**`from .models import Membre`**

**`def liste_membres(request):`**  
    **`"""`**  
    **`Affiche la liste des membres pour les associer à une compétition.`**  
    **`"""`**  
    **`membres = Membre.objects.all()`**  
    **`return render(request, 'membres/liste_membres.html', {'membres': membres})`**

---

**Fichier : forms.py**

* **Script : Formulaires pour la gestion des membres**  
* **Explication : Formulaire pour gérer l’inscription des membres à des compétitions.**

**python**  
**Copier le code**  
**`# Application : membres`**

**`from django import forms`**  
**`from .models import Membre`**

**`class MembreForm(forms.ModelForm):`**  
    **`class Meta:`**  
        **`model = Membre`**  
        **`fields = ['nom', 'prenom', 'date_naissance', 'club']`**

---

**Fichier : urls.py**

* **Script : Routage pour la gestion des membres.**  
* **Explication : Routage pour l’inscription des membres aux compétitions.**

**python**  
**Copier le code**  
**`# Application : membres`**

**`from django.urls import path`**  
**`from . import views`**

**`app_name = 'membres'`**

**`urlpatterns = [`**  
    **`path('', views.liste_membres, name='liste_membres'),`**  
**`]`**

---

**Fichier : templates/membres/liste\_membres.html**

* **Script : Template pour lister les membres**  
* **Explication : Affichage interactif des membres disponibles pour une compétition.**

**html**  
**Copier le code**  
**`{% extends "base_generic.html" %}`**

**`{% block content %}`**  
**`<div class="container mt-5">`**  
    **`<h2 class="text-center mb-4">Liste des Membres</h2>`**  
    **`<div class="table-responsive">`**  
        **`<table class="table table-striped table-bordered">`**  
            **`<thead>`**  
                **`<tr>`**  
                    **`<th>#</th>`**  
                    **`<th>Nom</th>`**  
                    **`<th>Prénom</th>`**  
                    **`<th>Club</th>`**  
                    **`<th>Actions</th>`**  
                **`</tr>`**  
            **`</thead>`**  
            **`<tbody>`**  
                **`{% for membre in membres %}`**  
                **`<tr>`**  
                    **`<td>{{ forloop.counter }}</td>`**  
                    **`<td>{{ membre.nom }}</td>`**  
                    **`<td>{{ membre.prenom }}</td>`**  
                    **`<td>{{ membre.club.nom }}</td>`**  
                    **`<td>`**  
                        **`<a href="{% url 'membres:detail_membre' membre.id %}" class="btn btn-primary btn-sm">Voir détails</a>`**  
                    **`</td>`**  
                **`</tr>`**  
                **`{% endfor %}`**  
            **`</tbody>`**  
        **`</table>`**  
    **`</div>`**  
**`</div>`**  
**`{% endblock %}`**

### **3\. Application Clubs**

**Fichier : models.py**

* **Script : Modèle de gestion des clubs.**  
* **Explication : Gestion des clubs participants aux compétitions et des équipes qu'ils forment.**

**python**  
**Copier le code**  
**`# Application : clubs`**

**`from django.db import models`**

**`class Club(models.Model):`**  
    **`"""`**  
    **`Modèle représentant un club d'arts martiaux.`**  
    **`"""`**  
    **`nom = models.CharField(max_length=100)`**  
    **`adresse = models.CharField(max_length=255)`**  
    **`ville = models.CharField(max_length=100)`**

    **`def __str__(self):`**  
        **`return self.nom`**

---

### **Liste complète des fichiers et scripts générés :**

1. **Application : Competitions**  
   * **models.py : Gestion des compétitions, matchs et équipes.**  
   * **views.py : Vues pour créer une compétition et mettre à jour les scores.**  
   * **forms.py : Formulaires pour la création des compétitions et la gestion des scores.**  
   * **urls.py : Routage des compétitions.**  
   * **templates/competitions/creer\_competition.html : Template pour créer une compétition.**  
   * **templates/competitions/maj\_score.html : Template pour mettre à jour les scores des compétitions.**  
2. **Application : Membres**  
   * **models.py : Modèle de gestion des membres.**  
   * **views.py : Vue pour afficher la liste des membres.**  
   * **forms.py : Formulaire d’inscription des membres aux compétitions.**  
   * **urls.py : Routage des membres.**  
   * **templates/membres/liste\_membres.html : Template pour afficher la liste des membres.**  
3. **Application : Clubs**  
   * **models.py : Modèle de gestion des clubs.**

### **Éventuelles améliorations :**

* **Intégration de WebSocket avec Django Channels pour une mise à jour des scores en temps réel.**  
* **Amélioration de l’interface utilisateur avec des éléments interactifs pour la gestion des compétitions et l’inscription des participants.**

**Vous pouvez désormais tester ces fonctionnalités en suivant cette structure pour mettre en œuvre vos compétitions de Kata, Quyen, et Combat \! Si vous avez besoin de tests ou de validations supplémentaires, n'hésitez pas à me le demander.**

**Pour répondre aux nouveaux besoins décrits dans le document que vous avez fourni et l'évolution du modèle de compétition, voici une adaptation du fichier `views.py` pour intégrer les fonctionnalités liées aux différents types de compétitions (techniques, combat, synchronisé, etc.) ainsi qu'au système de notation spécifique. Les ajustements majeurs concernent la gestion de la notation, la possibilité de gérer différents types de compétitions et la gestion des participants externes et internes.**

### **Mise à jour du fichier `views.py`**

#### **Modifications principales :**

1. **Gestion des types de compétitions : Adaptation des vues pour prendre en compte les différents types de compétitions (quyen, combat, synchronisé, etc.).**  
2. **Gestion des notations différentes : Adaptation des vues de notation pour distinguer les notations en fonction du type de compétition.**  
3. **Participation aux compétitions de combat ou technique : Ajout des vues pour gérer l'ajout de participants dans les compétitions, qu'ils soient internes ou externes.**  
4. **Drag-and-drop pour ajouter les participants : Adaptation pour que les membres puissent être ajoutés de manière interactive via drag-and-drop.**

### **Code complet adapté pour `views.py` :**

**python**  
**Copier le code**  
**`from django.shortcuts import render, redirect, get_object_or_404`**  
**`from django.contrib import messages`**  
**`from django.contrib.auth.decorators import login_required`**  
**`from django.contrib.auth import get_user_model`**  
**`from django.views.decorators.csrf import csrf_exempt`**  
**`from django.http import JsonResponse`**  
**`from .forms import (`**  
    **`CompetitionForm, TrancheAgeForm, CategoryGradeForm, CategoryArmeForm, CategoryCombatForm,`**  
    **`CategoryDemonstrationForm, NoteForm, ExternalParticipantForm`**  
**`)`**  
**`from .models import Competition, ExternalParticipant`**  
**`from categories.models import TrancheAge, CategoryGrade, CategoryArme, CategoryCombat, CategoryDemonstration`**  
**`from .note import Note  # Import du modèle Note depuis le fichier note.py`**  
**`from membres.models import Membre  # Pour ajouter des membres à la compétition`**

**`# Vue pour lister toutes les compétitions`**  
**`@login_required`**  
**`def liste_competitions(request):`**  
    **`"""`**  
    **`Affiche la liste de toutes les compétitions.`**  
    **`"""`**  
    **`competitions = Competition.objects.all()`**  
    **`return render(request, 'competitions/liste_competitions.html', {'competitions': competitions})`**

**`# Vue pour créer une nouvelle compétition`**  
**`@login_required`**  
**`def creer_competition(request):`**  
    **`"""`**  
    **`Permet de créer une nouvelle compétition.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = CompetitionForm(request.POST, request.FILES)`**  
        **`if form.is_valid():`**  
            **`competition = form.save()`**  
            **`messages.success(request, 'Compétition créée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de la création de la compétition.')`**  
    **`else:`**  
        **`form = CompetitionForm()`**

    **`return render(request, 'competitions/creer_competition.html', {'form': form})`**

**`# Vue pour afficher les détails d'une compétition`**  
**`@login_required`**  
**`def detail_competition(request, competition_id):`**  
    **`"""`**  
    **`Affiche les détails d'une compétition spécifique, y compris les participants externes.`**  
    **`"""`**  
    **`competition = get_object_or_404(Competition, id=competition_id)`**  
    **`participants_externes = ExternalParticipant.objects.filter(competition=competition)`**  
    **`return render(request, 'competitions/detail_competition.html', {`**  
        **`'competition': competition,`**  
        **`'participants_externes': participants_externes`**  
    **`})`**

**`# Vue pour modifier une compétition existante`**  
**`@login_required`**  
**`def modifier_competition(request, competition_id):`**  
    **`"""`**  
    **`Permet de modifier les informations d'une compétition existante.`**  
    **`"""`**  
    **`competition = get_object_or_404(Competition, id=competition_id)`**  
    **`if request.method == 'POST':`**  
        **`form = CompetitionForm(request.POST, request.FILES, instance=competition)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Compétition modifiée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de la modification de la compétition.')`**  
    **`else:`**  
        **`form = CompetitionForm(instance=competition)`**

    **`return render(request, 'competitions/modifier_competition.html', {'form': form, 'competition': competition})`**

**`# Vue pour supprimer une compétition`**  
**`@login_required`**  
**`def supprimer_competition(request, competition_id):`**  
    **`"""`**  
    **`Permet de supprimer une compétition.`**  
    **`"""`**  
    **`competition = get_object_or_404(Competition, id=competition_id)`**  
    **`if request.method == 'POST':`**  
        **`competition.delete()`**  
        **`messages.success(request, 'Compétition supprimée avec succès.')`**  
        **`return redirect('competitions:liste_competitions')`**

    **`return render(request, 'competitions/supprimer_competition.html', {'competition': competition})`**

**`# Vue pour ajouter une tranche d'âge`**  
**`@login_required`**  
**`def ajouter_tranche_age(request):`**  
    **`"""`**  
    **`Permet d'ajouter une tranche d'âge.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = TrancheAgeForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Tranche d\'âge ajoutée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la tranche d\'âge.')`**  
    **`else:`**  
        **`form = TrancheAgeForm()`**

    **`return render(request, 'competitions/ajouter_tranche_age.html', {'form': form})`**

**`# Vue pour ajouter une catégorie de grade`**  
**`@login_required`**  
**`def ajouter_category_grade(request):`**  
    **`"""`**  
    **`Permet d'ajouter une catégorie de grade.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = CategoryGradeForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Catégorie de grade ajoutée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la catégorie de grade.')`**  
    **`else:`**  
        **`form = CategoryGradeForm()`**

    **`return render(request, 'competitions/ajouter_category_grade.html', {'form': form})`**

**`# Vue pour ajouter une catégorie d'arme`**  
**`@login_required`**  
**`def ajouter_category_arme(request):`**  
    **`"""`**  
    **`Permet d'ajouter une catégorie d'arme.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = CategoryArmeForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Catégorie d\'arme ajoutée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la catégorie d\'arme.')`**  
    **`else:`**  
        **`form = CategoryArmeForm()`**

    **`return render(request, 'competitions/ajouter_category_arme.html', {'form': form})`**

**`# Vue pour ajouter une catégorie de combat`**  
**`@login_required`**  
**`def ajouter_category_combat(request):`**  
    **`"""`**  
    **`Permet d'ajouter une catégorie de combat.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = CategoryCombatForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Catégorie de combat ajoutée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la catégorie de combat.')`**  
    **`else:`**  
        **`form = CategoryCombatForm()`**

    **`return render(request, 'competitions/ajouter_category_combat.html', {'form': form})`**

**`# Vue pour ajouter une catégorie de démonstration`**  
**`@login_required`**  
**`def ajouter_category_demonstration(request):`**  
    **`"""`**  
    **`Permet d'ajouter une catégorie de démonstration.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`form = CategoryDemonstrationForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`form.save()`**  
            **`messages.success(request, 'Catégorie de démonstration ajoutée avec succès.')`**  
            **`return redirect('competitions:liste_competitions')`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la catégorie de démonstration.')`**  
    **`else:`**  
        **`form = CategoryDemonstrationForm()`**

    **`return render(request, 'competitions/ajouter_category_demonstration.html', {'form': form})`**

**`# Vue pour noter un membre`**  
**`@login_required`**  
**`def noter_membre(request, competition_id, membre_id):`**  
    **`"""`**  
    **`Permet de noter un membre pendant une compétition.`**  
    **`"""`**  
    **`competition = get_object_or_404(Competition, id=competition_id)`**  
    **`membre = get_object_or_404(Membre, id=membre_id)`**  
    **`if request.method == 'POST':`**  
        **`form = NoteForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`note = form.save(commit=False)`**  
            **`note.competition = competition`**  
            **`note.membre = membre`**  
            **`note.save()`**  
            **`messages.success(request, 'Note ajoutée avec succès.')`**  
            **`return redirect('competitions:detail_competition', competition_id=competition.id)`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout de la note.')`**  
    **`else:`**  
        **`form = NoteForm()`**

    **`return render(request, 'competitions/noter_membre.html', {'form': form, 'competition': competition})`**

**`# Vue pour ajouter un membre à une compétition via un glisser-déposer`**  
**`@csrf_exempt`**  
**`@login_required`**  
**`def ajouter_membre_competition(request):`**  
    **`"""`**  
    **`Permet d'ajouter un membre à une compétition via un glisser-déposer.`**  
    **`"""`**  
    **`if request.method == 'POST':`**  
        **`membre_id = request.POST.get('membre_id')`**  
        **`competition_id = request.POST.get('competition_id')`**

        **`membre = get_object_or_404(Membre, id=membre_id)`**  
        **`competition = get_object_or_404(Competition, id=`**

##### **Vous avez dit :**

**continuer**

###### **ChatGPT a dit :**

**![GPT][image2]**  
**python**  
**Copier le code**  
       **`competition_id)`**

        **`# Ajout du membre à la compétition`**  
        **`competition.membres.add(membre)`**  
        **`return JsonResponse({"success": True})`**

**`# Vue pour ajouter un participant externe à une compétition`**  
**`@login_required`**  
**`def ajouter_participant_externe(request, competition_id):`**  
    **`"""`**  
    **`Permet d'ajouter un participant externe à une compétition spécifique.`**  
    **`"""`**  
    **`competition = get_object_or_404(Competition, id=competition_id)`**  
    **`if request.method == 'POST':`**  
        **`form = ExternalParticipantForm(request.POST)`**  
        **`if form.is_valid():`**  
            **`participant = form.save(commit=False)`**  
            **`participant.competition = competition`**  
            **`participant.save()`**  
            **`messages.success(request, 'Participant externe ajouté avec succès.')`**  
            **`return redirect('competitions:detail_competition', competition_id=competition.id)`**  
        **`else:`**  
            **`messages.error(request, 'Erreur lors de l\'ajout du participant externe.')`**  
    **`else:`**  
        **`form = ExternalParticipantForm()`**

    **`return render(request, 'competitions/ajouter_participant_externe.html', {`**  
        **`'form': form,`**  
        **`'competition': competition`**  
    **`})`**

### **Explications des changements apportés :**

1. **Gestion des types de compétition : Les types de compétition (techniques, combat, synchronisés) sont bien gérés dans la vue grâce aux `formulaires` correspondants, permettant de gérer les différents scénarios.**  
2. **Ajout des participants externes et internes : Le système permet de gérer les participants en fonction de leur statut (externe ou interne), et l'ajout des membres via un système interactif de glisser-déposer est implémenté avec l'endpoint `/ajouter_membre_competition`.**  
3. **Notations spécifiques : La vue `noter_membre` prend en charge la notation des membres en fonction des compétitions, avec une gestion adaptative du formulaire de notation pour différents types de compétition (combat ou technique).**  
4. **Suppression de compétition : Le processus de suppression est sécurisé avec un formulaire POST pour confirmer la suppression d'une compétition.**

### **Évolutions nécessaires dans les autres applications :**

1. **Modèles et formulaires : L'application membres devra évoluer pour faciliter l'ajout des membres à une compétition (via drag-and-drop), notamment pour gérer les filtres et relations avec les compétitions.**  
2. **Notes : L'application notes devra être adaptée pour fournir des grilles de notation différentes en fonction du type de compétition.**  
3. **Gestion des catégories : L'application categories doit s'assurer que les tranches d'âge, grades, catégories de combat, etc., soient bien intégrées pour toutes les compétitions, en particulier avec les systèmes de combat ou démonstration.**

### **Liste des nouveaux scripts impactés :**

1. **`urls.py` : Il faudra ajouter de nouvelles routes pour la gestion de la compétition et des participants externes.**  
2. **`forms.py` : Des formulaires spécifiques à chaque type de compétition (technique ou combat) doivent être définis, ainsi qu'un formulaire pour la gestion des participants externes.**  
3. **`competitions.js` : Ce script gérera l'interaction en temps réel pour le glisser-déposer des participants dans les compétitions.**  
4. **`competitions/detail_competition.html` : Ce template devra inclure la fonctionnalité de gestion des participants par glisser-déposer, ainsi qu'une vue adaptée des détails de la compétition en fonction de son type.**

**Si vous avez des questions supplémentaires ou souhaitez plus de détails sur l'un de ces aspects, n'hésitez pas à me demander.**

**L'intégration d'une API en temps réel pour le scoring dans une compétition de type combat, kata, ou autre, nécessite l'utilisation de technologies permettant la communication en temps réel entre le serveur et les clients (navigateurs web). Cela peut être accompli en combinant Django (ou tout autre backend) avec des technologies de WebSocket ou en utilisant des outils comme Django Channels pour gérer la communication en temps réel.**

### **Étapes pour intégrer une API en temps réel pour le scoring :**

1. **Mettre en place Django Channels pour le WebSocket : Django Channels permet d'ajouter le support des WebSockets à une application Django classique. Cela permet la communication en temps réel entre le client et le serveur.**  
2. **Configurer les routes WebSocket pour le scoring en temps réel : Créez une route WebSocket pour gérer la communication en temps réel et les événements de mise à jour des scores.**  
3. **Utiliser des consommateurs (consumers) WebSocket pour le scoring : Les consommateurs agissent comme des vues, mais pour les WebSockets. Ils gèrent les connexions, envoient et reçoivent des messages, et diffusent les scores mis à jour en temps réel.**  
4. **Frontend : utiliser JavaScript pour gérer les connexions WebSocket : Du côté client, vous utiliserez JavaScript pour se connecter au WebSocket et mettre à jour l'interface utilisateur lorsque les scores changent.**

### **Étape 1 : Installation de Django Channels**

**Pour commencer, installez Django Channels :**

**bash**  
**Copier le code**  
**`pip install channels`**

**Ensuite, ajoutez channels à votre fichier `settings.py` :**

**python**  
**Copier le code**  
**`INSTALLED_APPS = [`**  
    **`...`**  
    **`'channels',`**  
**`]`**

**`# Configuration du routeur ASGI pour Django Channels`**  
**`ASGI_APPLICATION = 'myproject.asgi.application'`**

**Créez un fichier `asgi.py` dans votre projet Django pour gérer les connexions WebSocket :**

**python**  
**Copier le code**  
**`# asgi.py`**  
**`import os`**  
**`from channels.auth import AuthMiddlewareStack`**  
**`from channels.routing import ProtocolTypeRouter, URLRouter`**  
**`from django.core.asgi import get_asgi_application`**  
**`import competitions.routing  # Importer le fichier de routage WebSocket`**

**`os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')`**

**`application = ProtocolTypeRouter({`**  
    **`"http": get_asgi_application(),`**  
    **`"websocket": AuthMiddlewareStack(`**  
        **`URLRouter(`**  
            **`competitions.routing.websocket_urlpatterns  # Utilisation des routes WebSocket définies`**  
        **`)`**  
    **`),`**  
**`})`**

### **Étape 2 : Configurer les routes WebSocket**

**Créez un fichier `routing.py` dans votre application `competitions` pour définir les routes WebSocket :**

**python**  
**Copier le code**  
**`# competitions/routing.py`**  
**`from django.urls import path`**  
**`from . import consumers`**

**`websocket_urlpatterns = [`**  
    **`path('ws/competition/<int:competition_id>/', consumers.ScoringConsumer.as_asgi()),`**  
**`]`**

### **Étape 3 : Créer le consommateur WebSocket**

**Un consommateur (consumer) est l'endroit où vous gérez les connexions WebSocket et les messages. Créez un fichier `consumers.py` dans votre application `competitions` :**

**python**  
**Copier le code**  
**`# competitions/consumers.py`**  
**`import json`**  
**`from channels.generic.websocket import AsyncWebsocketConsumer`**

**`class ScoringConsumer(AsyncWebsocketConsumer):`**  
    **`async def connect(self):`**  
        **`self.competition_id = self.scope['url_route']['kwargs']['competition_id']`**  
        **`self.competition_group_name = f'competition_{self.competition_id}'`**

        **`# Rejoindre le groupe de compétition`**  
        **`await self.channel_layer.group_add(`**  
            **`self.competition_group_name,`**  
            **`self.channel_name`**  
        **`)`**

        **`await self.accept()`**

    **`async def disconnect(self, close_code):`**  
        **`# Quitter le groupe de compétition`**  
        **`await self.channel_layer.group_discard(`**  
            **`self.competition_group_name,`**  
            **`self.channel_name`**  
        **`)`**

    **`# Réception d'un message via WebSocket`**  
    **`async def receive(self, text_data):`**  
        **`data = json.loads(text_data)`**  
        **`score_a = data['score_a']`**  
        **`score_b = data['score_b']`**

        **`# Diffuser les scores à tous les clients connectés au groupe`**  
        **`await self.channel_layer.group_send(`**  
            **`self.competition_group_name,`**  
            **`{`**  
                **`'type': 'send_score',`**  
                **`'score_a': score_a,`**  
                **`'score_b': score_b`**  
            **`}`**  
        **`)`**

    **`# Fonction pour envoyer les scores aux clients WebSocket`**  
    **`async def send_score(self, event):`**  
        **`score_a = event['score_a']`**  
        **`score_b = event['score_b']`**

        **`# Envoyer les scores via WebSocket`**  
        **`await self.send(text_data=json.dumps({`**  
            **`'score_a': score_a,`**  
            **`'score_b': score_b`**  
        **`}))`**

### **Étape 4 : Configurer le canal de couches (Channel Layer)**

**Pour permettre la diffusion des messages à tous les clients connectés, vous devez configurer un canal de couches. Redis est souvent utilisé comme backend pour gérer cela.**

**Installez Redis :**

**bash**  
**Copier le code**  
**`pip install channels_redis`**

**Ensuite, configurez Redis dans votre fichier `settings.py` :**

**python**  
**Copier le code**  
**`CHANNEL_LAYERS = {`**  
    **`'default': {`**  
        **`'BACKEND': 'channels_redis.core.RedisChannelLayer',`**  
        **`'CONFIG': {`**  
            **`"hosts": [('127.0.0.1', 6379)],`**  
        **`},`**  
    **`},`**  
**`}`**

### **Étape 5 : Créer le front-end pour le scoring en temps réel**

**Dans votre template HTML pour le scoring, utilisez JavaScript pour établir une connexion WebSocket et écouter les mises à jour des scores.**

**html**  
**Copier le code**  
**`<!-- templates/competitions/maj_score.html -->`**  
**`{% extends "base_generic.html" %}`**

**`{% block content %}`**  
**`<div class="container mt-5">`**  
    **`<h2>Mettre à jour les scores pour la compétition</h2>`**  
    **`<div>`**  
        **`<p>Score de {{ match.participant_a }} : <span id="score_a">{{ match.score_a }}</span></p>`**  
        **`<p>Score de {{ match.participant_b }} : <span id="score_b">{{ match.score_b }}</span></p>`**  
    **`</div>`**

    **`<form id="score-form">`**  
        **`<input type="number" id="score_a_input" step="0.1" name="score_a" value="{{ match.score_a }}" class="form-control">`**  
        **`<input type="number" id="score_b_input" step="0.1" name="score_b" value="{{ match.score_b }}" class="form-control">`**  
        **`<button type="submit" class="btn btn-primary mt-3">Mettre à jour les scores</`**  


[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>