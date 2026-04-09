# 🥋 MartialComp - Prompts d'Ajustements
## Module Tracking Grade & Calendrier Pratiquant

**Date:** 17 décembre 2025  
**Version:** 1.0  
**Auteur:** Bertrand / Claude AI  
**Module concerné:** Dashboard Pratiquant (`participant.html`)

---

## 📋 Table des matières

1. [Contexte et Objectifs](#contexte-et-objectifs)
2. [Analyse de l'Existant](#analyse-de-lexistant)
3. [Prompt 1 - Widget Progression Grade](#prompt-1--widget-progression-vers-le-prochain-grade)
4. [Prompt 2 - Système d'Alertes](#prompt-2--système-dalertes-et-notifications-proactives)
5. [Prompt 3 - Visualisation Résultats](#prompt-3--visualisation-des-résultats-du-pratiquant)
6. [Prompt 4 - Calendrier Unifié](#prompt-4--calendrier-unifié-des-événements)
7. [Prompt 5 - Service Éligibilité Backend](#prompt-5--service-de-calcul-déligibilité-backend)
8. [Plan d'Implémentation](#plan-dimplémentation)
9. [Annexes](#annexes)

---

## Contexte et Objectifs

### 🎯 Objectif Principal

Enrichir le dashboard du pratiquant avec des fonctionnalités de **tracking de progression de grade**, incluant :

1. **Suivi automatique** de l'éligibilité au prochain grade
2. **Alertes et notifications** proactives (dates de passage, examens disponibles)
3. **Visualisation des résultats** de compétitions (palmarès)
4. **Calendrier unifié** des événements (discipline + club)

### 👤 Persona Cible

- **Pratiquant** (rôle `participant`)
- Souhaite suivre sa progression sans intervention manuelle
- Veut être informé des opportunités de passage de grade
- Consulte régulièrement son dashboard sur mobile et desktop

### 📱 Plateformes

- Application web (Django templates)
- Application mobile (React Native/Expo) - synchronisation API
- Notifications push et email

---

## Analyse de l'Existant

### ✅ Composants Existants

| Composant | État | Fichier |
|-----------|------|---------|
| Historique grades | ✅ Présent | `participant_profile.html` |
| Notifications sidebar | ✅ Présent | `participant.html` |
| Modèle `Grade` | ✅ Complet | `models.py` (min_age, min_time_in_previous_grade, next_grade) |
| Modèle `GradeExam` | ✅ Complet | `models.py` (sessions examens, registration_deadline) |
| Modèle `GradeRequirement` | ✅ Complet | `models.py` (exigences par grade) |
| Événements à venir | ⚠️ Basique | `participant_enhanced.html` |
| Calendrier JS | ✅ Club uniquement | `club.html` (fonction renderCalendar()) |

### ❌ Composants Manquants

| Composant | Priorité | Description |
|-----------|----------|-------------|
| Calcul éligibilité | 🔴 Haute | Service automatique de calcul |
| Widget progression | 🔴 Haute | Affichage visuel dans dashboard |
| Alertes proactives | 🟡 Moyenne | Notifications J-30, J-0, rappels |
| Calendrier pratiquant | 🟢 Basse | Vue calendrier personnalisée |
| Export palmarès | 🟢 Basse | PDF/partage résultats |

### 📊 Modèles de Données Clés

```python
# Grade - Définition des grades par discipline
class Grade:
    name: str
    discipline: FK(Discipline)
    level: int  # Ordre hiérarchique
    min_age: int  # Âge minimum requis
    min_time_in_previous_grade: int  # Mois requis
    
    @property
    def next_grade(self) -> Optional[Grade]
    
    @property
    def previous_grade(self) -> Optional[Grade]

# PractitionerGrade - Historique des grades obtenus
class PractitionerGrade:
    practitioner: FK(Practitioner)
    grade: FK(Grade)
    date_obtained: date
    examiner: str
    location: str

# GradeExam - Sessions d'examens
class GradeExam:
    title: str
    date: date
    discipline: FK(Discipline)
    available_grades: M2M(Grade)
    registration_deadline: date
    status: str  # scheduled, in_progress, completed, cancelled

# GradeRequirement - Exigences par grade
class GradeRequirement:
    grade: FK(Grade)
    name: str
    is_mandatory: bool
    min_age: int
    required_points: int
```

---

## Prompt 1 – Widget Progression vers le Prochain Grade

### 📝 Description

Créer un widget visuel de tracking de progression de grade pour le dashboard pratiquant, affichant le temps restant avant éligibilité, les exigences à remplir, et les examens disponibles.

### 🎯 Prompt Complet

```
OBJECTIF: Créer un widget de tracking de progression de grade pour le dashboard pratiquant

CONTEXTE EXISTANT:
- Modèle Grade avec properties: next_grade, min_age, min_time_in_previous_grade
- Modèle PractitionerGrade avec date_obtained
- Modèle GradeRequirement avec is_mandatory, required_points
- Template actuel: competitions/templates/competitions/dashboard/participant.html

FONCTIONNALITÉS REQUISES:

1. CALCUL D'ÉLIGIBILITÉ
   - Calculer automatiquement la date d'éligibilité au prochain grade
   - Basé sur: min_time_in_previous_grade + date_obtained du grade actuel
   - Vérifier critère d'âge (min_age)
   - Retourner: date_eligible, days_remaining, is_eligible, blocking_reasons[]

2. AFFICHAGE WIDGET
   Structure visuelle:
   ┌─────────────────────────────────────────────────────────┐
   │ 🎯 PROGRESSION VERS LE PROCHAIN GRADE                  │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   [CEINTURE JAUNE]  ───────────►  [CEINTURE ORANGE]    │
   │      (actuel)           75%          (cible)           │
   │                                                         │
   │   ┌─────────────────────────────────────────────┐      │
   │   │████████████████████████░░░░░░░░│ 75%        │      │
   │   └─────────────────────────────────────────────┘      │
   │                                                         │
   │   ⏱️ 45 jours restants (éligible le 01/02/2026)        │
   │                                                         │
   │   📋 Exigences:                                         │
   │   ✅ Âge minimum (8 ans) - OK                          │
   │   ✅ Temps dans grade précédent (6 mois) - OK          │
   │   ⬜ Maîtrise kata Heian Shodan - En cours             │
   │   ⬜ 10 séances d'entraînement - 7/10                  │
   │                                                         │
   │   📅 Prochain examen: 15/02/2026 - Lyon                │
   │   [S'inscrire à l'examen]                              │
   │                                                         │
   └─────────────────────────────────────────────────────────┘

   Éléments visuels:
   - Barre de progression circulaire ou linéaire (% temps écoulé)
   - Représentation visuelle des ceintures avec couleurs réelles
   - Grade actuel → Grade cible avec flèche
   - Compteur jours restants animé
   - Badge "ÉLIGIBLE ✓" si conditions remplies (avec animation pulse)
   - Liste des exigences (GradeRequirement) avec checkboxes état
   - Lien vers inscription examen si éligible + examen disponible

3. DONNÉES NÉCESSAIRES (Context View)
   ```python
   context = {
       'grade_progression': {
           'current_grade': Grade,  # Grade actuel du pratiquant
           'next_grade': Grade,  # Grade suivant (via Grade.next_grade)
           'date_obtained': date,  # Date obtention grade actuel
           'eligibility_date': date,  # Date calculée d'éligibilité
           'days_remaining': int,  # Jours restants (0 si éligible)
           'is_eligible': bool,  # True si toutes conditions remplies
           'progress_percentage': float,  # % progression temporelle (0-100)
           'blocking_reasons': List[str],  # Raisons si non éligible
           'requirements_status': [
               {
                   'requirement': GradeRequirement,
                   'is_completed': bool,
                   'current_value': Any,
                   'target_value': Any,
                   'notes': str
               }
           ],
           'upcoming_exams': QuerySet[GradeExam],  # Examens disponibles
           'next_exam': GradeExam,  # Prochain examen le plus proche
       }
   }
   ```

4. ÉTATS DU WIDGET
   
   État 1: EN PROGRESSION
   - Barre de progression partielle
   - Compteur jours restants
   - Couleur: bleu/neutre
   
   État 2: ÉLIGIBLE
   - Badge "ÉLIGIBLE" avec animation
   - Bouton "S'inscrire à l'examen" proéminent
   - Couleur: vert
   
   État 3: BLOQUÉ
   - Icône warning
   - Liste des conditions non remplies
   - Couleur: orange
   
   État 4: PAS DE GRADE SUIVANT
   - Message "Grade maximum atteint"
   - Afficher palmarès/accomplissements
   - Couleur: or

5. RESPONSIVE DESIGN
   - Desktop: Widget complet dans sidebar ou section principale
   - Tablet: Version compacte avec expansion au clic
   - Mobile: Card collapsible, infos essentielles visibles

6. ANIMATIONS
   - Progression de la barre au chargement (ease-out)
   - Pulse sur badge "ÉLIGIBLE"
   - Transition smooth au changement d'état
   - Confetti animation lors du passage de grade

FICHIERS À MODIFIER/CRÉER:

1. competitions/services/grade_eligibility.py
   - Classe GradeEligibilityService (voir Prompt 5)

2. competitions/views/dashboard.py
   - Modifier ParticipantDashboardView.get_context_data()
   - Ajouter appel au service d'éligibilité

3. competitions/templatetags/grade_tags.py
   - Template tag {% grade_progress_widget %}
   - Filtres: |grade_color, |days_to_text

4. competitions/templates/components/grade_progress_widget.html
   - Template du widget réutilisable

5. competitions/templates/competitions/dashboard/participant.html
   - Intégrer le widget dans la page

6. competitions/static/css/grade_progress.css
   - Styles du widget

7. competitions/static/js/grade_progress.js
   - Animations et interactions

OUTPUT ATTENDU:
- Code Python complet (service + view + templatetags)
- Template HTML du widget
- Fichiers CSS et JS
- Tests unitaires pour le service
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `services/grade_eligibility.py` | Créer | Service de calcul |
| `views/dashboard.py` | Modifier | Ajouter context |
| `templatetags/grade_tags.py` | Créer | Tags personnalisés |
| `templates/components/grade_progress_widget.html` | Créer | Widget HTML |
| `static/css/grade_progress.css` | Créer | Styles |
| `static/js/grade_progress.js` | Créer | Animations |

---

## Prompt 2 – Système d'Alertes et Notifications Proactives

### 📝 Description

Implémenter un système d'alertes automatiques pour informer les pratiquants de leur éligibilité aux passages de grade et des examens disponibles.

### 🎯 Prompt Complet

```
OBJECTIF: Implémenter des alertes automatiques pour les passages de grade

CONTEXTE EXISTANT:
- Modèle Notification existant avec types: competition, grade, training, payment, message
- Template notification dans sidebar participant.html
- GradeExam avec registration_deadline
- Celery configuré pour les tâches asynchrones
- Redis comme broker

ARCHITECTURE NOTIFICATIONS EXISTANTE:
```python
class Notification(models.Model):
    TYPE_CHOICES = [
        ('competition', 'Compétition'),
        ('grade', 'Grade'),
        ('training', 'Entraînement'),
        ('payment', 'Paiement'),
        ('message', 'Message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    priority = models.CharField(max_length=10)  # normal, high, urgent
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

NOUVEAUX TYPES DE NOTIFICATIONS À AJOUTER:

1. ALERTES ÉLIGIBILITÉ GRADE
   ```python
   # Tâche Celery quotidienne: check_grade_eligibility_notifications
   
   Scénarios:
   
   a) J-30 avant éligibilité
      Type: 'grade_eligibility_upcoming'
      Titre: "Bientôt éligible au grade {grade_name}"
      Message: "Dans 30 jours, vous serez éligible au passage de grade {grade_name}. 
                Préparez-vous et consultez les exigences."
      Priority: 'normal'
      Action: "Voir les exigences" → /dashboard/grade-progress/
   
   b) J-7 avant éligibilité
      Type: 'grade_eligibility_soon'
      Titre: "Plus que 7 jours avant éligibilité"
      Message: "Vous serez éligible au grade {grade_name} le {date}. 
                Un examen est disponible le {exam_date}."
      Priority: 'high'
      Action: "S'inscrire à l'examen" → /grades/exam/{id}/register/
   
   c) J-0 éligibilité atteinte
      Type: 'grade_eligibility_reached'
      Titre: "🎉 Vous êtes éligible au grade {grade_name} !"
      Message: "Félicitations ! Vous remplissez toutes les conditions pour passer 
                au grade {grade_name}. Inscrivez-vous au prochain examen."
      Priority: 'high'
      Action: "Voir les examens disponibles" → /grades/exams/?grade={id}
   
   d) Rappel mensuel si éligible sans inscription
      Type: 'grade_eligibility_reminder'
      Titre: "Rappel : Vous êtes éligible au grade {grade_name}"
      Message: "Vous êtes éligible depuis {days} jours. Le prochain examen a lieu 
                le {exam_date}. N'attendez plus !"
      Priority: 'normal'
      Action: "S'inscrire" → /grades/exam/{id}/register/
   ```

2. ALERTES EXAMENS DISPONIBLES
   ```python
   # Signal: post_save sur GradeExam
   
   a) Nouvel examen créé
      Déclencheur: Création GradeExam avec status='scheduled'
      Destinataires: Tous pratiquants éligibles au grade concerné
      Type: 'grade_exam_available'
      Titre: "Nouvel examen de grade disponible"
      Message: "Un examen pour le grade {grade_name} est programmé le {date} 
                à {location}. Inscriptions ouvertes jusqu'au {deadline}."
      Priority: 'normal'
      Action: "S'inscrire" → /grades/exam/{id}/register/
   
   b) J-14 avant deadline inscription
      Type: 'grade_exam_deadline_warning'
      Titre: "⚠️ Inscription examen : plus que 14 jours"
      Message: "La date limite d'inscription à l'examen du {date} approche. 
                Inscrivez-vous avant le {deadline}."
      Priority: 'high'
      Action: "S'inscrire maintenant" → /grades/exam/{id}/register/
   
   c) J-3 avant deadline inscription
      Type: 'grade_exam_deadline_urgent'
      Titre: "🚨 URGENT : Inscription examen dans 3 jours"
      Message: "Dernière chance ! L'inscription à l'examen du {date} ferme 
                dans 3 jours ({deadline})."
      Priority: 'urgent'
      Action: "S'inscrire d'urgence" → /grades/exam/{id}/register/
   
   d) J-1 avant examen (rappel inscrit)
      Destinataires: Pratiquants inscrits à l'examen
      Type: 'grade_exam_reminder'
      Titre: "📅 Rappel : Examen demain"
      Message: "Votre examen de passage au grade {grade_name} a lieu demain 
                à {time} - {location}. Bonne chance !"
      Priority: 'high'
      Action: "Voir les détails" → /grades/exam/{id}/
   ```

3. ALERTES RÉSULTATS
   ```python
   # Signal: post_save sur GradeExamRegistration (status change)
   
   a) Examen réussi
      Déclencheur: status changé en 'passed'
      Type: 'grade_exam_passed'
      Titre: "🎉 Félicitations ! Grade {grade_name} obtenu"
      Message: "Vous avez réussi votre examen de passage au grade {grade_name}. 
                Votre nouveau grade a été enregistré dans votre profil."
      Priority: 'high'
      Action: "Voir mon profil" → /dashboard/profile/
   
   b) Examen non réussi
      Déclencheur: status changé en 'failed'
      Type: 'grade_exam_failed'
      Titre: "Résultat examen de grade"
      Message: "Vous n'avez pas obtenu le grade {grade_name} cette fois-ci. 
                Continuez vos efforts ! Prochain examen disponible le {next_exam_date}."
      Priority: 'normal'
      Action: "Voir les prochains examens" → /grades/exams/
   ```

4. PRÉFÉRENCES UTILISATEUR
   ```python
   class NotificationPreferences(models.Model):
       user = models.OneToOneField(User, on_delete=models.CASCADE)
       
       # Canaux
       email_enabled = models.BooleanField(default=True)
       push_enabled = models.BooleanField(default=True)
       in_app_enabled = models.BooleanField(default=True)
       
       # Types de notifications grade
       grade_eligibility_alerts = models.BooleanField(default=True)
       grade_exam_alerts = models.BooleanField(default=True)
       grade_result_alerts = models.BooleanField(default=True)
       
       # Fréquence rappels
       FREQUENCY_CHOICES = [
           ('daily', 'Quotidien'),
           ('weekly', 'Hebdomadaire'),
           ('monthly', 'Mensuel'),
           ('never', 'Jamais'),
       ]
       reminder_frequency = models.CharField(
           max_length=10, 
           choices=FREQUENCY_CHOICES, 
           default='weekly'
       )
       
       # Heures de notification préférées
       quiet_hours_start = models.TimeField(default='22:00')
       quiet_hours_end = models.TimeField(default='08:00')
   ```

STRUCTURE COMPLÈTE NOTIFICATION:
```python
{
    'type': str,  # Type de notification
    'priority': 'normal' | 'high' | 'urgent',
    'title': str,
    'message': str,
    'action_url': str,  # URL d'action
    'action_text': str,  # Texte du bouton
    'metadata': {
        'grade_id': int,
        'exam_id': int,
        'days_remaining': int,
        'eligibility_date': str,
    },
    'channels': ['in_app', 'email', 'push'],  # Canaux à utiliser
    'scheduled_at': datetime,  # Pour notifications programmées
}
```

TÂCHES CELERY À CRÉER:

```python
# competitions/tasks/grade_notifications.py

@shared_task
def check_grade_eligibility_daily():
    """
    Tâche quotidienne pour vérifier l'éligibilité de tous les pratiquants
    et créer les notifications appropriées.
    Exécution: Tous les jours à 8h00
    """
    pass

@shared_task
def check_exam_deadlines_daily():
    """
    Tâche quotidienne pour vérifier les deadlines d'inscription.
    Exécution: Tous les jours à 9h00
    """
    pass

@shared_task
def send_exam_reminders():
    """
    Envoie les rappels J-1 aux inscrits.
    Exécution: Tous les jours à 18h00
    """
    pass

@shared_task
def send_monthly_eligibility_reminders():
    """
    Envoie les rappels mensuels aux éligibles non inscrits.
    Exécution: 1er de chaque mois à 10h00
    """
    pass
```

CONFIGURATION CELERY BEAT:
```python
# settings.py ou celery.py

CELERY_BEAT_SCHEDULE = {
    'check-grade-eligibility-daily': {
        'task': 'competitions.tasks.grade_notifications.check_grade_eligibility_daily',
        'schedule': crontab(hour=8, minute=0),
    },
    'check-exam-deadlines-daily': {
        'task': 'competitions.tasks.grade_notifications.check_exam_deadlines_daily',
        'schedule': crontab(hour=9, minute=0),
    },
    'send-exam-reminders': {
        'task': 'competitions.tasks.grade_notifications.send_exam_reminders',
        'schedule': crontab(hour=18, minute=0),
    },
    'send-monthly-eligibility-reminders': {
        'task': 'competitions.tasks.grade_notifications.send_monthly_eligibility_reminders',
        'schedule': crontab(day_of_month=1, hour=10, minute=0),
    },
}
```

SIGNALS À CRÉER:
```python
# competitions/signals/grade_signals.py

@receiver(post_save, sender=GradeExam)
def notify_eligible_practitioners_new_exam(sender, instance, created, **kwargs):
    """Notifie les pratiquants éligibles lors de la création d'un examen."""
    pass

@receiver(post_save, sender=GradeExamRegistration)
def notify_exam_result(sender, instance, **kwargs):
    """Notifie le pratiquant du résultat de son examen."""
    pass

@receiver(post_save, sender=PractitionerGrade)
def notify_grade_obtained(sender, instance, created, **kwargs):
    """Notification et mise à jour lors de l'obtention d'un grade."""
    pass
```

FICHIERS À CRÉER/MODIFIER:

1. competitions/tasks/grade_notifications.py
   - Toutes les tâches Celery

2. competitions/signals/grade_signals.py
   - Signals pour événements grade/examen

3. competitions/models/notifications.py
   - Nouveau modèle NotificationPreferences
   - Nouveaux types de notification

4. competitions/services/notification_service.py
   - Service d'envoi multi-canal

5. settings.py
   - Configuration CELERY_BEAT_SCHEDULE

6. competitions/templates/emails/grade_notifications/
   - eligibility_upcoming.html
   - eligibility_reached.html
   - exam_available.html
   - exam_deadline.html
   - exam_result.html

7. competitions/templates/components/notification_preferences.html
   - Formulaire préférences utilisateur

OUTPUT ATTENDU:
- Code Python complet (tasks + signals + models + services)
- Templates email HTML
- Configuration Celery
- Tests unitaires pour chaque tâche
- Documentation des flux de notification
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `tasks/grade_notifications.py` | Créer | Tâches Celery |
| `signals/grade_signals.py` | Créer | Signals Django |
| `models/notifications.py` | Modifier | Nouveaux types + Preferences |
| `services/notification_service.py` | Créer | Service multi-canal |
| `settings.py` | Modifier | CELERY_BEAT_SCHEDULE |
| `templates/emails/grade_notifications/` | Créer | Templates email |

---

## Prompt 3 – Visualisation des Résultats du Pratiquant

### 📝 Description

Dashboard complet de visualisation des résultats de compétitions et du palmarès du pratiquant, avec graphiques et options d'export.

### 🎯 Prompt Complet

```
OBJECTIF: Dashboard de visualisation des résultats et palmarès du pratiquant

CONTEXTE EXISTANT:
- Template participant_results.html existe (version basique)
- Modèles disponibles: CompetitionResult, Match, PractitionerGrade
- Statistiques basiques dans participant.html (total_competitions, medals, points)

FONCTIONNALITÉS REQUISES:

1. SECTION "MON PALMARÈS"
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🏆 MON PALMARÈS                                         │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   🥇 12    🥈 8     🥉 15    Total: 35 médailles        │
   │                                                         │
   │   Filtres: [2024 ▼] [Karaté ▼] [Kumite ▼]              │
   │                                                         │
   │   Timeline:                                             │
   │   ──●────●──────●────●───────●────●──────►             │
   │   2020  2021   2022  2023   2024  2025                  │
   │    🥉   🥇      🥈    🥇🥉   🥇🥇  🥈                   │
   │                                                         │
   │   [Voir détails] [Exporter PDF]                        │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```
   
   Composants:
   - Compteur médailles animé (🥇 X | 🥈 Y | 🥉 Z)
   - Timeline visuelle des podiums (chronologique, interactive)
   - Filtres: par année, par discipline, par type compétition
   - Détail au survol de chaque médaille

2. SECTION "STATISTIQUES"
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 📊 MES STATISTIQUES                                     │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   Taux de victoire     Évolution classement 12 mois    │
   │   ┌─────────┐         ┌─────────────────────────┐      │
   │   │   68%   │         │    ___/\                │      │
   │   │  ████   │         │ __/    \___/\          │      │
   │   │  ████   │         │/            \___       │      │
   │   └─────────┘         └─────────────────────────┘      │
   │                                                         │
   │   vs Moyenne catégorie: +12%                           │
   │                                                         │
   │   Points cumulés par discipline:                       │
   │   Karaté Kumite  ████████████████  450 pts            │
   │   Karaté Kata    ████████          200 pts            │
   │   Judo           ████              100 pts            │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```
   
   Graphiques (Chart.js):
   - Gauge/Donut: Taux de victoire global (%)
   - Line chart: Évolution classement sur 12 mois
   - Bar chart horizontal: Points par discipline
   - Comparaison avec moyenne catégorie (overlay)

3. SECTION "HISTORIQUE DÉTAILLÉ"
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 📋 HISTORIQUE DES COMPÉTITIONS                          │
   ├─────────────────────────────────────────────────────────┤
   │ Recherche: [________________] Trier par: [Date ▼]      │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ 🥇 15/11/2024 - Championnat Régional Karaté            │
   │    Kumite Senior -75kg | 1ère place | 50 pts           │
   │    [▼ Voir les matchs]                                  │
   │    ┌─────────────────────────────────────────────┐     │
   │    │ 1/4: vs J. Martin (Lyon) - Victoire 5-2    │     │
   │    │ 1/2: vs P. Dubois (Paris) - Victoire 3-1   │     │
   │    │ Finale: vs M. Bernard (Marseille) - V. 4-2 │     │
   │    └─────────────────────────────────────────────┘     │
   │                                                         │
   │ 🥉 02/09/2024 - Open International Kata                │
   │    Kata Senior | 3ème place | 30 pts                   │
   │    [▼ Voir les détails]                                │
   │                                                         │
   │ [Charger plus...]                                       │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```
   
   Fonctionnalités:
   - Liste paginée (infinite scroll ou pagination)
   - Pour chaque: date, compétition, catégorie, résultat, points
   - Expandable pour voir détail matchs
   - Recherche full-text
   - Tri: date, résultat, points

4. SECTION "GRADES OBTENUS"
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🥋 MES GRADES                                           │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   Karaté:                                               │
   │   ○────○────○────●────○────○────○                      │
   │   Bl   Ja   Or   Ve   Bl   Ma   No                     │
   │                  ↑                                      │
   │              Actuel                                     │
   │                                                         │
   │   Historique:                                           │
   │   ┌──────────────────────────────────────────────┐     │
   │   │ 🟢 Ceinture Verte | 15/06/2024              │     │
   │   │    Examinateur: Sensei Yamamoto              │     │
   │   │    Lieu: Dojo Central Lyon                   │     │
   │   │    [📄 Certificat]                           │     │
   │   ├──────────────────────────────────────────────┤     │
   │   │ 🟠 Ceinture Orange | 10/01/2024             │     │
   │   │    Examinateur: Sensei Martin                │     │
   │   │    Lieu: Club Karaté Paris                   │     │
   │   │    [📄 Certificat]                           │     │
   │   └──────────────────────────────────────────────┘     │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```
   
   Composants:
   - Frise horizontale des grades (progression visuelle)
   - Liste chronologique avec détails
   - Téléchargement certificats (PDF)
   - Multi-discipline si applicable

5. EXPORT & PARTAGE
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 📤 EXPORT & PARTAGE                                     │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   [📄 Exporter PDF]  [📊 Exporter Excel]               │
   │                                                         │
   │   Partage public:                                       │
   │   ☐ Activer mon profil public                          │
   │                                                         │
   │   Lien: martialcomp.com/athlete/jean-dupont-12345     │
   │   [📋 Copier] [QR Code]                                │
   │                                                         │
   │   Réseaux sociaux:                                      │
   │   [Facebook] [Twitter] [LinkedIn] [Instagram]          │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```
   
   Fonctionnalités:
   - Export PDF "Palmarès officiel" (template branded MartialComp)
   - Export Excel (données brutes)
   - Profil public optionnel (toggle)
   - QR code vers profil
   - Partage réseaux sociaux

DONNÉES CONTEXT VIEW:
```python
context = {
    'results_dashboard': {
        # Palmarès
        'medals': {
            'gold': 12,
            'silver': 8,
            'bronze': 15,
            'total': 35,
        },
        'medals_timeline': [
            {'date': '2024-11-15', 'medal': 'gold', 'competition': '...', 'category': '...'},
            # ...
        ],
        
        # Statistiques
        'stats': {
            'win_rate': 68.5,
            'win_rate_vs_category_avg': 12.3,  # Différence avec moyenne
            'total_competitions': 45,
            'total_matches': 156,
            'total_points': 750,
        },
        'ranking_evolution': [
            {'month': '2024-01', 'rank': 45},
            {'month': '2024-02', 'rank': 38},
            # ... 12 mois
        ],
        'points_by_discipline': [
            {'discipline': 'Karaté Kumite', 'points': 450},
            {'discipline': 'Karaté Kata', 'points': 200},
            {'discipline': 'Judo', 'points': 100},
        ],
        
        # Historique
        'competition_history': QuerySet[CompetitionResult],  # Paginé
        
        # Grades
        'grades': QuerySet[PractitionerGrade],
        'grade_progression': [...],  # Pour la frise
        
        # Partage
        'public_profile_enabled': bool,
        'public_profile_url': str,
    }
}
```

DESIGN & UX:
- Utiliser Chart.js pour tous les graphiques
- Cards avec animations au scroll (AOS ou custom)
- Mode sombre compatible
- Responsive mobile-first
- Skeleton loading pour les données async
- Empty states avec illustrations

FICHIERS À CRÉER/MODIFIER:

1. competitions/views/dashboard.py
   - Ajouter ResultsDashboardView ou enrichir ParticipantDashboardView

2. competitions/templates/competitions/dashboard/participant_results.html
   - Refonte complète du template

3. competitions/static/js/results_charts.js
   - Configuration Chart.js
   - Animations et interactions

4. competitions/static/css/results_dashboard.css
   - Styles spécifiques

5. competitions/services/results_service.py
   - Service de calcul des statistiques

6. competitions/api/results.py (optionnel)
   - Endpoints API pour chargement async

7. competitions/templates/pdf/palmares.html
   - Template PDF pour export

OUTPUT ATTENDU:
- Template HTML complet avec toutes les sections
- JavaScript pour graphiques Chart.js
- Styles CSS responsive
- Service Python de calcul statistiques
- Template PDF pour export
- Tests unitaires
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `views/dashboard.py` | Modifier | Ajouter ResultsDashboardView |
| `templates/.../participant_results.html` | Refonte | Nouveau dashboard |
| `static/js/results_charts.js` | Créer | Graphiques Chart.js |
| `static/css/results_dashboard.css` | Créer | Styles |
| `services/results_service.py` | Créer | Calculs statistiques |
| `templates/pdf/palmares.html` | Créer | Export PDF |

---

## Prompt 4 – Calendrier Unifié des Événements

### 📝 Description

Calendrier interactif agrégeant tous les événements pertinents pour le pratiquant : compétitions, examens de grade, événements du club.

### 🎯 Prompt Complet

```
OBJECTIF: Calendrier interactif des événements (discipline + club) pour le pratiquant

CONTEXTE EXISTANT:
- Fonction renderCalendar() dans club.html (JavaScript vanilla)
- Modèles disponibles: Competition, GradeExam, Event
- Section upcoming_events dans participant_enhanced.html (liste simple)
- upcoming_competitions dans club.html

SOURCES D'ÉVÉNEMENTS À AGRÉGER:

1. COMPÉTITIONS
   - Compétitions de ma/mes discipline(s)
   - Filtrer: ouvertes à inscription, dans ma région/niveau
   - Modèle: Competition
   
2. EXAMENS DE GRADE
   - Examens pour mon grade cible
   - Filtrer: discipline correspondante, inscription ouverte
   - Modèle: GradeExam
   
3. ÉVÉNEMENTS CLUB
   - Stages, séminaires, entraînements spéciaux
   - Événements de mon club uniquement
   - Modèle: Event
   
4. DEADLINES
   - Dates limites d'inscription (compétitions, examens)
   - Générées automatiquement depuis les autres événements

VUES CALENDRIER:

1. VUE MOIS (Défaut)
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  < Décembre 2024 >                    [Mois][Sem][Liste]│
   ├─────────────────────────────────────────────────────────┤
   │  Lun   Mar   Mer   Jeu   Ven   Sam   Dim               │
   ├──────┬──────┬──────┬──────┬──────┬──────┬──────────────┤
   │      │      │      │      │      │      │   1          │
   │      │      │      │      │      │      │              │
   ├──────┼──────┼──────┼──────┼──────┼──────┼──────────────┤
   │  2   │  3   │  4   │  5   │  6   │  7   │   8          │
   │      │      │      │      │      │ 🔵   │              │
   │      │      │      │      │      │Champ.│              │
   ├──────┼──────┼──────┼──────┼──────┼──────┼──────────────┤
   │  9   │ 10   │ 11   │ 12   │ 13   │ 14   │  15          │
   │      │ 🟡   │      │ 🔴   │      │      │ 🟢           │
   │      │Examen│      │Dead. │      │      │Stage         │
   ├──────┼──────┼──────┼──────┼──────┼──────┼──────────────┤
   │ 16   │ 17   │ 18   │ 19   │ 20   │ 21   │  22          │
   │ 🟣   │      │      │      │      │ 🔵   │              │
   │Inscr.│      │      │      │      │Open  │              │
   └──────┴──────┴──────┴──────┴──────┴──────┴──────────────┘
   
   Légende: 🔵 Compétition  🟡 Examen  🟢 Club  🔴 Deadline  🟣 Mes inscriptions
   ```

2. VUE SEMAINE
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  < Semaine du 9 au 15 décembre >      [Mois][Sem][Liste]│
   ├─────────────────────────────────────────────────────────┤
   │        Lun 9   Mar 10   Mer 11   Jeu 12   Ven 13  ...  │
   ├────────┬───────┬────────┬────────┬────────┬────────────┤
   │ 08:00  │       │        │        │        │            │
   ├────────┼───────┼────────┼────────┼────────┼────────────┤
   │ 09:00  │       │ 🟡     │        │        │            │
   │        │       │ Examen │        │        │            │
   │        │       │ 9h-12h │        │        │            │
   ├────────┼───────┼────────┼────────┼────────┼────────────┤
   │ 10:00  │       │        │        │        │            │
   ├────────┼───────┼────────┼────────┼────────┼────────────┤
   │ ...    │       │        │        │        │            │
   └────────┴───────┴────────┴────────┴────────┴────────────┘
   ```

3. VUE LISTE
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  Prochains événements                 [Mois][Sem][Liste]│
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │  📅 Samedi 7 décembre 2024                             │
   │  ┌───────────────────────────────────────────────────┐ │
   │  │ 🔵 Championnat Régional Karaté                    │ │
   │  │    09:00 - 18:00 | Lyon, Palais des Sports        │ │
   │  │    Kumite Senior -75kg                            │ │
   │  │    [Détails] [S'inscrire]              12 places  │ │
   │  └───────────────────────────────────────────────────┘ │
   │                                                         │
   │  📅 Mardi 10 décembre 2024                             │
   │  ┌───────────────────────────────────────────────────┐ │
   │  │ 🟡 Examen Passage Grade - Ceinture Orange         │ │
   │  │    09:00 - 12:00 | Dojo Central                   │ │
   │  │    ⚠️ Inscription avant le 5 décembre             │ │
   │  │    [Détails] [S'inscrire]                         │ │
   │  └───────────────────────────────────────────────────┘ │
   │                                                         │
   │  [Charger plus...]                                      │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

CODE COULEUR PAR TYPE:
```css
.event-competition { background-color: #3498db; }    /* 🔵 Bleu */
.event-exam { background-color: #f1c40f; }           /* 🟡 Jaune */
.event-club { background-color: #2ecc71; }           /* 🟢 Vert */
.event-deadline { background-color: #e74c3c; }       /* 🔴 Rouge */
.event-registered { background-color: #9b59b6; }     /* 🟣 Violet */
```

INTERACTIONS:

1. Click sur événement → Modal détail
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ 🔵 Championnat Régional Karaté                    [X]  │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │ 📅 Date: Samedi 7 décembre 2024                        │
   │ ⏰ Horaire: 09:00 - 18:00                              │
   │ 📍 Lieu: Palais des Sports, Lyon                       │
   │                                                         │
   │ 🥋 Discipline: Karaté                                  │
   │ 📋 Catégories: Kumite Senior (-75kg, +75kg)           │
   │                Kata Senior                             │
   │                                                         │
   │ 👥 Places restantes: 12 / 50                           │
   │ ⚠️ Inscription avant le: 1er décembre 2024             │
   │                                                         │
   │ 💰 Frais: 25€                                          │
   │                                                         │
   │ [S'inscrire]  [Ajouter au calendrier]  [Partager]     │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
   ```

2. Bouton "S'inscrire" → Redirection ou modal inscription

3. Export calendrier
   - Bouton "Ajouter à mon calendrier"
   - Export .ics (compatible Google Calendar, Apple, Outlook)
   - Sync automatique optionnelle (OAuth Google Calendar)

4. Filtres
   ```
   Filtres: [✓ Compétitions] [✓ Examens] [✓ Club] [□ Deadlines]
            [Karaté ▼] [Ma région ▼]
   ```

API ENDPOINT:
```
GET /api/practitioner/calendar-events/

Query params:
- start_date: ISO date (required)
- end_date: ISO date (required)
- types[]: competition, exam, club, deadline (optional, default: all)
- disciplines[]: IDs (optional, default: user's disciplines)
- include_registered_only: bool (optional, default: false)

Response:
{
    "events": [
        {
            "id": 123,
            "type": "competition",
            "title": "Championnat Régional Karaté",
            "start": "2024-12-07T09:00:00",
            "end": "2024-12-07T18:00:00",
            "all_day": false,
            "color": "#3498db",
            "url": "/competitions/123/",
            "location": "Lyon, Palais des Sports",
            "discipline": "Karaté",
            "is_registered": false,
            "registration_open": true,
            "registration_deadline": "2024-12-01",
            "spots_remaining": 12,
            "spots_total": 50,
            "fee": "25.00",
            "metadata": {
                "categories": ["Kumite Senior -75kg", "Kata Senior"]
            }
        },
        // ...
    ],
    "total": 15,
    "has_more": false
}
```

MOBILE:
- Swipe gauche/droite pour changer de mois/semaine
- Pull-to-refresh
- Notification reminder configurable (J-7, J-1, J-0)
- Vue liste par défaut sur mobile

LIBRAIRIE: FullCalendar.js
```javascript
// Configuration recommandée
const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'fr',
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,listWeek'
    },
    events: '/api/practitioner/calendar-events/',
    eventClick: handleEventClick,
    eventDidMount: customizeEventDisplay,
    // ...
});
```

FICHIERS À CRÉER:

1. competitions/api/calendar.py
   - CalendarEventsAPIView
   - Sérialiseurs pour chaque type d'événement

2. competitions/templates/components/unified_calendar.html
   - Template du composant calendrier

3. competitions/templates/components/calendar_event_modal.html
   - Modal détail événement

4. competitions/static/js/practitioner_calendar.js
   - Initialisation FullCalendar
   - Handlers d'événements
   - Gestion filtres

5. competitions/static/css/calendar.css
   - Styles personnalisés
   - Override FullCalendar

6. competitions/services/calendar_service.py
   - Agrégation des événements
   - Génération fichiers .ics

7. competitions/urls.py
   - Route API calendar-events

OUTPUT ATTENDU:
- API endpoint complet avec tests
- Template HTML intégrable
- JavaScript FullCalendar configuré
- Styles CSS
- Service de génération .ics
- Documentation API
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `api/calendar.py` | Créer | Endpoint API |
| `templates/components/unified_calendar.html` | Créer | Composant calendrier |
| `static/js/practitioner_calendar.js` | Créer | JavaScript FullCalendar |
| `static/css/calendar.css` | Créer | Styles |
| `services/calendar_service.py` | Créer | Agrégation + .ics |
| `urls.py` | Modifier | Nouvelle route API |

---

## Prompt 5 – Service de Calcul d'Éligibilité (Backend)

### 📝 Description

Service Python réutilisable pour calculer l'éligibilité aux passages de grade. Ce service est la fondation utilisée par les autres fonctionnalités.

### 🎯 Prompt Complet

```
OBJECTIF: Créer un service réutilisable pour calculer l'éligibilité aux grades

CONTEXTE:
- Ce service sera appelé par:
  - Widget dashboard (Prompt 1)
  - Notifications Celery (Prompt 2)
  - API REST
  - Interface Admin
- Doit être performant (utiliser cache Redis)
- Doit être précis et testable

MODÈLES EXISTANTS:
```python
class Grade(models.Model):
    name = models.CharField(max_length=100)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(default=0)
    min_age = models.PositiveSmallIntegerField(default=0)
    min_time_in_previous_grade = models.PositiveSmallIntegerField(default=0)  # En mois
    
    @property
    def next_grade(self) -> Optional['Grade']:
        return Grade.objects.filter(
            discipline=self.discipline,
            level__gt=self.level,
            is_active=True
        ).order_by('level').first()

class PractitionerGrade(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    date_obtained = models.DateField()
    examiner = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)

class GradeRequirement(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    min_age = models.PositiveSmallIntegerField(default=0)
    required_points = models.PositiveSmallIntegerField(default=0)

class GradeExam(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    available_grades = models.ManyToManyField(Grade)
    registration_deadline = models.DateField()
    status = models.CharField(max_length=20)  # scheduled, completed, cancelled
```

CLASSES À CRÉER:

```python
# competitions/services/grade_eligibility.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from django.core.cache import cache
from django.db.models import QuerySet
from django.utils import timezone

from competitions.models import (
    Practitioner, Grade, PractitionerGrade, 
    GradeRequirement, GradeExam, Discipline
)


@dataclass
class RequirementStatus:
    """Statut d'une exigence de grade."""
    requirement: GradeRequirement
    is_completed: bool
    current_value: Any
    target_value: Any
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            'id': self.requirement.id,
            'name': self.requirement.name,
            'description': self.requirement.description,
            'is_mandatory': self.requirement.is_mandatory,
            'is_completed': self.is_completed,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'notes': self.notes,
        }


@dataclass
class EligibilityResult:
    """Résultat complet du calcul d'éligibilité."""
    is_eligible: bool
    eligibility_date: Optional[date]
    days_remaining: int
    progress_percentage: float  # 0-100
    blocking_reasons: List[str]
    requirements_status: List[RequirementStatus]
    current_grade: Optional[Grade]
    next_grade: Optional[Grade]
    available_exams: List[GradeExam]
    date_grade_obtained: Optional[date]
    
    def to_dict(self) -> dict:
        """Conversion en dictionnaire pour templates/API."""
        return {
            'is_eligible': self.is_eligible,
            'eligibility_date': self.eligibility_date.isoformat() if self.eligibility_date else None,
            'days_remaining': self.days_remaining,
            'progress_percentage': round(self.progress_percentage, 1),
            'blocking_reasons': self.blocking_reasons,
            'requirements_status': [r.to_dict() for r in self.requirements_status],
            'current_grade': {
                'id': self.current_grade.id,
                'name': self.current_grade.name,
                'color': self.current_grade.color,
                'color_code': self.current_grade.color_code,
            } if self.current_grade else None,
            'next_grade': {
                'id': self.next_grade.id,
                'name': self.next_grade.name,
                'color': self.next_grade.color,
                'color_code': self.next_grade.color_code,
                'min_age': self.next_grade.min_age,
                'min_time_in_previous_grade': self.next_grade.min_time_in_previous_grade,
            } if self.next_grade else None,
            'available_exams': [
                {
                    'id': e.id,
                    'title': e.title,
                    'date': e.date.isoformat(),
                    'location': e.location,
                    'registration_deadline': e.registration_deadline.isoformat(),
                    'is_registration_open': e.is_registration_open,
                }
                for e in self.available_exams
            ],
            'date_grade_obtained': self.date_grade_obtained.isoformat() if self.date_grade_obtained else None,
        }


class GradeEligibilityService:
    """
    Service de calcul d'éligibilité aux passages de grade.
    
    Usage:
        service = GradeEligibilityService(practitioner)
        result = service.calculate_eligibility(discipline)
        
        # Ou pour vérification en masse
        results = GradeEligibilityService.bulk_check_eligibility(practitioners, discipline)
    """
    
    CACHE_PREFIX = "grade_eligibility"
    CACHE_TTL = 86400  # 24 heures
    
    def __init__(self, practitioner: Practitioner):
        """
        Initialise le service pour un pratiquant.
        
        Args:
            practitioner: Instance du pratiquant
        """
        self.practitioner = practitioner
        self._cache_key_base = f"{self.CACHE_PREFIX}:{practitioner.id}"
    
    def _get_cache_key(self, discipline_id: int) -> str:
        """Génère la clé de cache pour une discipline."""
        return f"{self._cache_key_base}:{discipline_id}"
    
    def _invalidate_cache(self, discipline_id: Optional[int] = None):
        """
        Invalide le cache pour ce pratiquant.
        
        Args:
            discipline_id: Si fourni, invalide uniquement cette discipline
        """
        if discipline_id:
            cache.delete(self._get_cache_key(discipline_id))
        else:
            # Invalider toutes les disciplines (pattern delete)
            # Note: nécessite Redis avec support pattern
            pass
    
    def get_current_grade(self, discipline: Discipline) -> Optional[Grade]:
        """
        Retourne le grade actuel pour une discipline.
        
        Args:
            discipline: La discipline concernée
            
        Returns:
            Le grade actuel ou None si aucun grade
        """
        practitioner_grade = PractitionerGrade.objects.filter(
            practitioner=self.practitioner,
            grade__discipline=discipline
        ).select_related('grade').order_by('-date_obtained', '-grade__level').first()
        
        return practitioner_grade.grade if practitioner_grade else None
    
    def get_current_practitioner_grade(self, discipline: Discipline) -> Optional[PractitionerGrade]:
        """
        Retourne l'enregistrement PractitionerGrade actuel.
        
        Args:
            discipline: La discipline concernée
            
        Returns:
            L'enregistrement PractitionerGrade ou None
        """
        return PractitionerGrade.objects.filter(
            practitioner=self.practitioner,
            grade__discipline=discipline
        ).select_related('grade').order_by('-date_obtained', '-grade__level').first()
    
    def get_next_grade(self, discipline: Discipline) -> Optional[Grade]:
        """
        Retourne le prochain grade possible.
        
        Args:
            discipline: La discipline concernée
            
        Returns:
            Le prochain grade ou None si grade maximum atteint
        """
        current = self.get_current_grade(discipline)
        if current:
            return current.next_grade
        else:
            # Pas de grade actuel, retourner le premier grade de la discipline
            return Grade.objects.filter(
                discipline=discipline,
                is_active=True
            ).order_by('level').first()
    
    def calculate_eligibility(
        self, 
        discipline: Discipline, 
        use_cache: bool = True
    ) -> EligibilityResult:
        """
        Calcule l'éligibilité complète pour une discipline.
        
        Args:
            discipline: La discipline concernée
            use_cache: Utiliser le cache (défaut: True)
            
        Returns:
            EligibilityResult avec toutes les informations
        """
        # Vérifier le cache
        cache_key = self._get_cache_key(discipline.id)
        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        # Récupérer les grades
        current_grade = self.get_current_grade(discipline)
        next_grade = self.get_next_grade(discipline)
        practitioner_grade = self.get_current_practitioner_grade(discipline)
        
        # Cas: pas de grade suivant (maximum atteint)
        if not next_grade:
            result = EligibilityResult(
                is_eligible=False,
                eligibility_date=None,
                days_remaining=0,
                progress_percentage=100.0,
                blocking_reasons=["Grade maximum atteint pour cette discipline"],
                requirements_status=[],
                current_grade=current_grade,
                next_grade=None,
                available_exams=[],
                date_grade_obtained=practitioner_grade.date_obtained if practitioner_grade else None,
            )
            if use_cache:
                cache.set(cache_key, result, self.CACHE_TTL)
            return result
        
        # Calculer l'éligibilité
        blocking_reasons = []
        today = timezone.now().date()
        
        # 1. Vérifier l'âge minimum
        practitioner_age = self._calculate_age(self.practitioner.birth_date)
        if practitioner_age < next_grade.min_age:
            blocking_reasons.append(
                f"Âge minimum requis: {next_grade.min_age} ans (actuellement {practitioner_age} ans)"
            )
        
        # 2. Calculer la date d'éligibilité basée sur le temps dans le grade précédent
        eligibility_date = None
        days_remaining = 0
        progress_percentage = 0.0
        
        if practitioner_grade and next_grade.min_time_in_previous_grade > 0:
            # Date d'éligibilité = date obtention + temps requis (en mois)
            months_required = next_grade.min_time_in_previous_grade
            eligibility_date = self._add_months(
                practitioner_grade.date_obtained, 
                months_required
            )
            
            # Calculer les jours restants
            if eligibility_date > today:
                days_remaining = (eligibility_date - today).days
                blocking_reasons.append(
                    f"Temps minimum dans le grade actuel: {months_required} mois "
                    f"(éligible le {eligibility_date.strftime('%d/%m/%Y')})"
                )
            
            # Calculer le pourcentage de progression
            total_days = (eligibility_date - practitioner_grade.date_obtained).days
            elapsed_days = (today - practitioner_grade.date_obtained).days
            if total_days > 0:
                progress_percentage = min(100.0, (elapsed_days / total_days) * 100)
            else:
                progress_percentage = 100.0
        elif not practitioner_grade:
            # Pas de grade actuel - éligible au premier grade
            eligibility_date = today
            progress_percentage = 100.0
        else:
            # Pas de temps minimum requis
            eligibility_date = today
            progress_percentage = 100.0
        
        # 3. Vérifier les exigences spécifiques (GradeRequirement)
        requirements_status = self._check_requirements(next_grade)
        mandatory_incomplete = [
            r for r in requirements_status 
            if r.requirement.is_mandatory and not r.is_completed
        ]
        if mandatory_incomplete:
            for req in mandatory_incomplete:
                blocking_reasons.append(
                    f"Exigence non remplie: {req.requirement.name}"
                )
        
        # 4. Déterminer si éligible
        is_eligible = len(blocking_reasons) == 0
        
        # 5. Récupérer les examens disponibles
        available_exams = self._get_available_exams(next_grade)
        
        # Construire le résultat
        result = EligibilityResult(
            is_eligible=is_eligible,
            eligibility_date=eligibility_date,
            days_remaining=max(0, days_remaining),
            progress_percentage=progress_percentage,
            blocking_reasons=blocking_reasons,
            requirements_status=requirements_status,
            current_grade=current_grade,
            next_grade=next_grade,
            available_exams=list(available_exams),
            date_grade_obtained=practitioner_grade.date_obtained if practitioner_grade else None,
        )
        
        # Mettre en cache
        if use_cache:
            cache.set(cache_key, result, self.CACHE_TTL)
        
        return result
    
    def _calculate_age(self, birth_date: date) -> int:
        """Calcule l'âge à partir de la date de naissance."""
        today = timezone.now().date()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    
    def _add_months(self, source_date: date, months: int) -> date:
        """Ajoute un nombre de mois à une date."""
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    
    def _check_requirements(self, grade: Grade) -> List[RequirementStatus]:
        """
        Vérifie les exigences pour un grade.
        
        Args:
            grade: Le grade cible
            
        Returns:
            Liste des statuts d'exigences
        """
        requirements = GradeRequirement.objects.filter(grade=grade).order_by('order')
        statuses = []
        
        for req in requirements:
            status = self._check_single_requirement(req)
            statuses.append(status)
        
        return statuses
    
    def _check_single_requirement(self, requirement: GradeRequirement) -> RequirementStatus:
        """
        Vérifie une exigence spécifique.
        
        Note: Cette méthode peut être étendue pour vérifier différents types
        d'exigences (points, présence, techniques validées, etc.)
        
        Args:
            requirement: L'exigence à vérifier
            
        Returns:
            RequirementStatus
        """
        # Vérification de l'âge minimum de l'exigence
        if requirement.min_age > 0:
            age = self._calculate_age(self.practitioner.birth_date)
            if age < requirement.min_age:
                return RequirementStatus(
                    requirement=requirement,
                    is_completed=False,
                    current_value=age,
                    target_value=requirement.min_age,
                    notes=f"Âge requis: {requirement.min_age} ans"
                )
        
        # Vérification des points requis
        if requirement.required_points > 0:
            # TODO: Implémenter la récupération des points du pratiquant
            current_points = 0  # Placeholder
            return RequirementStatus(
                requirement=requirement,
                is_completed=current_points >= requirement.required_points,
                current_value=current_points,
                target_value=requirement.required_points,
                notes=f"{current_points}/{requirement.required_points} points"
            )
        
        # Pour les autres exigences (techniques, etc.), retourner non complété par défaut
        # TODO: Implémenter la logique spécifique selon le type d'exigence
        return RequirementStatus(
            requirement=requirement,
            is_completed=False,
            current_value=None,
            target_value=None,
            notes="À valider par l'instructeur"
        )
    
    def _get_available_exams(self, grade: Grade) -> QuerySet[GradeExam]:
        """
        Récupère les examens disponibles pour un grade.
        
        Args:
            grade: Le grade cible
            
        Returns:
            QuerySet des examens disponibles
        """
        today = timezone.now().date()
        return GradeExam.objects.filter(
            available_grades=grade,
            status='scheduled',
            date__gte=today,
            registration_deadline__gte=today
        ).order_by('date')
    
    def get_upcoming_exams(self, discipline: Discipline) -> QuerySet[GradeExam]:
        """
        Retourne les examens disponibles pour le grade cible du pratiquant.
        
        Args:
            discipline: La discipline concernée
            
        Returns:
            QuerySet des examens
        """
        next_grade = self.get_next_grade(discipline)
        if not next_grade:
            return GradeExam.objects.none()
        return self._get_available_exams(next_grade)
    
    @staticmethod
    def bulk_check_eligibility(
        practitioners: QuerySet, 
        discipline: Discipline
    ) -> Dict[int, EligibilityResult]:
        """
        Vérification en masse de l'éligibilité (optimisé pour listes).
        
        Args:
            practitioners: QuerySet de pratiquants
            discipline: La discipline à vérifier
            
        Returns:
            Dictionnaire {practitioner_id: EligibilityResult}
        """
        results = {}
        
        # Précharger les grades des pratiquants
        practitioner_grades = PractitionerGrade.objects.filter(
            practitioner__in=practitioners,
            grade__discipline=discipline
        ).select_related('practitioner', 'grade')
        
        grades_by_practitioner = {}
        for pg in practitioner_grades:
            if pg.practitioner_id not in grades_by_practitioner:
                grades_by_practitioner[pg.practitioner_id] = pg
            elif pg.grade.level > grades_by_practitioner[pg.practitioner_id].grade.level:
                grades_by_practitioner[pg.practitioner_id] = pg
        
        # Calculer pour chaque pratiquant
        for practitioner in practitioners:
            service = GradeEligibilityService(practitioner)
            results[practitioner.id] = service.calculate_eligibility(
                discipline, 
                use_cache=True
            )
        
        return results
    
    @staticmethod
    def invalidate_practitioner_cache(practitioner_id: int, discipline_id: Optional[int] = None):
        """
        Invalide le cache d'éligibilité pour un pratiquant.
        
        À appeler lors de:
        - Obtention d'un nouveau grade
        - Modification des informations du pratiquant
        - Changement dans les exigences de grade
        
        Args:
            practitioner_id: ID du pratiquant
            discipline_id: ID de la discipline (optionnel)
        """
        if discipline_id:
            cache.delete(f"{GradeEligibilityService.CACHE_PREFIX}:{practitioner_id}:{discipline_id}")
        else:
            # Supprimer toutes les clés pour ce pratiquant
            # Note: nécessite Redis avec SCAN ou pattern delete
            pass
```

TESTS UNITAIRES:
```python
# competitions/tests/test_grade_eligibility.py

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from competitions.models import (
    Practitioner, Grade, PractitionerGrade, 
    GradeRequirement, GradeExam, Discipline
)
from competitions.services.grade_eligibility import (
    GradeEligibilityService, EligibilityResult, RequirementStatus
)


class GradeEligibilityServiceTest(TestCase):
    """Tests pour le service d'éligibilité aux grades."""
    
    @classmethod
    def setUpTestData(cls):
        """Créer les données de test."""
        # Créer une discipline
        cls.discipline = Discipline.objects.create(name="Karaté")
        
        # Créer les grades (ceinture blanche → jaune → orange)
        cls.grade_white = Grade.objects.create(
            name="Ceinture Blanche",
            discipline=cls.discipline,
            level=1,
            min_age=6,
            min_time_in_previous_grade=0
        )
        cls.grade_yellow = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=cls.discipline,
            level=2,
            min_age=7,
            min_time_in_previous_grade=6  # 6 mois
        )
        cls.grade_orange = Grade.objects.create(
            name="Ceinture Orange",
            discipline=cls.discipline,
            level=3,
            min_age=8,
            min_time_in_previous_grade=6
        )
        
        # Créer un pratiquant adulte
        cls.practitioner_adult = Practitioner.objects.create(
            first_name="Jean",
            last_name="Dupont",
            birth_date=date(1990, 1, 15)
        )
        
        # Créer un pratiquant enfant (7 ans)
        cls.practitioner_child = Practitioner.objects.create(
            first_name="Lucas",
            last_name="Martin",
            birth_date=date.today() - timedelta(days=7*365)
        )
    
    def test_no_current_grade_eligible_for_first(self):
        """Sans grade actuel, devrait être éligible au premier grade."""
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        self.assertTrue(result.is_eligible)
        self.assertIsNone(result.current_grade)
        self.assertEqual(result.next_grade, self.grade_white)
        self.assertEqual(result.progress_percentage, 100.0)
    
    def test_time_restriction_not_met(self):
        """Avec grade récent, devrait avoir temps restant."""
        # Donner la ceinture blanche il y a 3 mois
        PractitionerGrade.objects.create(
            practitioner=self.practitioner_adult,
            grade=self.grade_white,
            date_obtained=date.today() - timedelta(days=90)
        )
        
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        self.assertFalse(result.is_eligible)
        self.assertEqual(result.current_grade, self.grade_white)
        self.assertEqual(result.next_grade, self.grade_yellow)
        self.assertGreater(result.days_remaining, 0)
        self.assertLess(result.progress_percentage, 100)
    
    def test_time_restriction_met(self):
        """Avec assez de temps dans le grade, devrait être éligible."""
        # Donner la ceinture blanche il y a 7 mois
        PractitionerGrade.objects.create(
            practitioner=self.practitioner_adult,
            grade=self.grade_white,
            date_obtained=date.today() - timedelta(days=210)
        )
        
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        self.assertTrue(result.is_eligible)
        self.assertEqual(result.days_remaining, 0)
        self.assertEqual(result.progress_percentage, 100.0)
    
    def test_age_restriction(self):
        """Enfant trop jeune pour le grade suivant."""
        # Donner la ceinture jaune à l'enfant
        PractitionerGrade.objects.create(
            practitioner=self.practitioner_child,
            grade=self.grade_yellow,
            date_obtained=date.today() - timedelta(days=365)
        )
        
        service = GradeEligibilityService(self.practitioner_child)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        # L'enfant a 7 ans, orange nécessite 8 ans
        self.assertFalse(result.is_eligible)
        self.assertIn("Âge minimum", result.blocking_reasons[0])
    
    def test_max_grade_reached(self):
        """Grade maximum atteint."""
        # Créer un grade maximum
        grade_black = Grade.objects.create(
            name="Ceinture Noire",
            discipline=self.discipline,
            level=10,
            min_age=16,
            min_time_in_previous_grade=12
        )
        
        PractitionerGrade.objects.create(
            practitioner=self.practitioner_adult,
            grade=grade_black,
            date_obtained=date.today() - timedelta(days=365)
        )
        
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        self.assertFalse(result.is_eligible)
        self.assertIsNone(result.next_grade)
        self.assertIn("maximum", result.blocking_reasons[0].lower())
    
    def test_available_exams_returned(self):
        """Les examens disponibles sont retournés."""
        PractitionerGrade.objects.create(
            practitioner=self.practitioner_adult,
            grade=self.grade_white,
            date_obtained=date.today() - timedelta(days=210)
        )
        
        # Créer un examen disponible
        exam = GradeExam.objects.create(
            title="Examen Ceinture Jaune",
            date=date.today() + timedelta(days=30),
            discipline=self.discipline,
            registration_deadline=date.today() + timedelta(days=15),
            status='scheduled',
            location="Dojo Central"
        )
        exam.available_grades.add(self.grade_yellow)
        
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        self.assertEqual(len(result.available_exams), 1)
        self.assertEqual(result.available_exams[0].id, exam.id)
    
    def test_to_dict_serialization(self):
        """Le résultat se sérialise correctement."""
        service = GradeEligibilityService(self.practitioner_adult)
        result = service.calculate_eligibility(self.discipline, use_cache=False)
        
        data = result.to_dict()
        
        self.assertIn('is_eligible', data)
        self.assertIn('next_grade', data)
        self.assertIn('progress_percentage', data)
        self.assertIsInstance(data['blocking_reasons'], list)
    
    def test_bulk_check_eligibility(self):
        """Vérification en masse fonctionne."""
        practitioners = Practitioner.objects.all()
        
        results = GradeEligibilityService.bulk_check_eligibility(
            practitioners, 
            self.discipline
        )
        
        self.assertEqual(len(results), 2)
        self.assertIn(self.practitioner_adult.id, results)
        self.assertIn(self.practitioner_child.id, results)
```

INTÉGRATION AVEC CACHE INVALIDATION:
```python
# competitions/signals/grade_signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from competitions.models import PractitionerGrade, GradeRequirement
from competitions.services.grade_eligibility import GradeEligibilityService


@receiver(post_save, sender=PractitionerGrade)
def invalidate_eligibility_on_grade_change(sender, instance, **kwargs):
    """Invalide le cache quand un grade est attribué."""
    GradeEligibilityService.invalidate_practitioner_cache(
        instance.practitioner_id,
        instance.grade.discipline_id
    )


@receiver(post_delete, sender=PractitionerGrade)
def invalidate_eligibility_on_grade_delete(sender, instance, **kwargs):
    """Invalide le cache quand un grade est supprimé."""
    GradeEligibilityService.invalidate_practitioner_cache(
        instance.practitioner_id,
        instance.grade.discipline_id
    )


@receiver(post_save, sender=GradeRequirement)
def invalidate_all_eligibility_on_requirement_change(sender, instance, **kwargs):
    """
    Invalide le cache de tous les pratiquants quand les exigences changent.
    Note: Opération coûteuse, à optimiser si nécessaire.
    """
    # TODO: Implémenter invalidation ciblée
    pass
```

FICHIERS À CRÉER:

1. competitions/services/__init__.py
   - Export du service

2. competitions/services/grade_eligibility.py
   - Classe GradeEligibilityService complète
   - Dataclasses EligibilityResult, RequirementStatus

3. competitions/tests/test_grade_eligibility.py
   - Tests unitaires complets

4. competitions/signals/grade_signals.py
   - Signals pour invalidation cache

OUTPUT ATTENDU:
- Code Python complet et fonctionnel
- Tests unitaires avec couverture > 90%
- Documentation des méthodes
- Exemples d'utilisation
```

### 📁 Fichiers Impactés

| Fichier | Action | Description |
|---------|--------|-------------|
| `services/__init__.py` | Créer/Modifier | Export |
| `services/grade_eligibility.py` | Créer | Service complet |
| `tests/test_grade_eligibility.py` | Créer | Tests unitaires |
| `signals/grade_signals.py` | Modifier | Invalidation cache |

---

## Plan d'Implémentation

### 📅 Planning Recommandé

| Phase | Prompt | Durée estimée | Priorité | Dépendances |
|-------|--------|---------------|----------|-------------|
| **1** | Prompt 5 - Service éligibilité | 2-3 jours | 🔴 Critique | Aucune |
| **2** | Prompt 1 - Widget progression | 2-3 jours | 🔴 Haute | Phase 1 |
| **3** | Prompt 2 - Alertes | 3-4 jours | 🟡 Moyenne | Phase 1 + Celery |
| **4** | Prompt 3 - Visualisation résultats | 2-3 jours | 🟡 Moyenne | Aucune |
| **5** | Prompt 4 - Calendrier unifié | 3-4 jours | 🟢 Basse | Aucune |

### 🔗 Dépendances Techniques

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │            PROMPT 5: Service Éligibilité            │   │
│   │         (GradeEligibilityService)                   │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│           ┌─────────────┼─────────────┐                     │
│           ▼             ▼             ▼                     │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│   │ PROMPT 1  │  │ PROMPT 2  │  │   API     │              │
│   │  Widget   │  │  Alertes  │  │  Externe  │              │
│   └───────────┘  └─────┬─────┘  └───────────┘              │
│                        │                                     │
│                        ▼                                     │
│                 ┌───────────┐                                │
│                 │  Celery   │                                │
│                 │  + Redis  │                                │
│                 └───────────┘                                │
│                                                              │
│   ┌───────────┐  ┌───────────┐                              │
│   │ PROMPT 3  │  │ PROMPT 4  │  (Indépendants)              │
│   │ Résultats │  │Calendrier │                              │
│   └───────────┘  └───────────┘                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### ✅ Checklist de Validation

Pour chaque prompt implémenté :

- [ ] Code Python fonctionnel
- [ ] Tests unitaires passants (couverture > 80%)
- [ ] Templates responsives testés
- [ ] Traductions i18n ajoutées
- [ ] Documentation mise à jour
- [ ] Revue de code effectuée
- [ ] Tests sur environnement de staging
- [ ] Déploiement production

---

## Annexes

### A. Modèles de Données Complets

Voir fichier `models.py` dans le projet.

### B. URLs Existantes

Voir fichier `urls.txt` dans le projet.

### C. Templates Existants

- `participant.html` - Dashboard principal
- `participant_profile.html` - Profil avec historique grades
- `participant_enhanced.html` - Version enrichie
- `participant_results.html` - Résultats (à refondre)
- `participant_competitions.html` - Liste compétitions

### D. Ressources Externes

- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [FullCalendar Documentation](https://fullcalendar.io/docs)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Django Signals](https://docs.djangoproject.com/en/5.0/topics/signals/)

---

## Historique des Versions

| Version | Date | Auteur | Modifications |
|---------|------|--------|---------------|
| 1.0 | 17/12/2025 | Claude AI | Création initiale |

---

*Document généré pour le projet MartialComp*  
*© 2025 - Tous droits réservés*
