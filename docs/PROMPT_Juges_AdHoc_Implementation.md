# 🥋 Prompt d'Implémentation : Système de Juges Ad-Hoc pour MartialComp

## 📋 Contexte du Problème

Dans l'interface de gestion des juges techniques (`/competitions/club/competitions/{id}/manage/pro/`), le système actuel ne propose que les juges officiellement enregistrés. Or, lors des compétitions locales/régionales, il est fréquent de faire appel aux **pratiquants adultes présents** pour aider à juger et arbitrer.

### Besoins Identifiés
1. Sélectionner parmi les **participants inscrits à la compétition** (18+ ans)
2. Sélectionner parmi les **pratiquants adultes des disciplines concernées** (même non inscrits)
3. Attribuer un **statut intermédiaire** de "juge ad-hoc" ou "juge bénévole"
4. Activer un **dashboard juge limité** dans leur profil pour la durée de la compétition

---

## 🏗️ Architecture de la Solution

### Nouveau Modèle : `AdHocJudge`

```python
# apps/competitions/models/adhoc_judges.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

class AdHocJudge(models.Model):
    """
    Juge temporaire recruté parmi les participants pour une compétition.
    Permet de gérer les juges bénévoles qui ne sont pas des juges officiels.
    """
    
    STATUS_CHOICES = [
        ('pending', _('En attente de confirmation')),
        ('active', _('Actif')),
        ('completed', _('Mission terminée')),
        ('declined', _('A décliné')),
        ('revoked', _('Révoqué')),
    ]
    
    JUDGE_TYPE_CHOICES = [
        ('technical_judge', _('Juge Technique')),
        ('combat_referee', _('Arbitre Combat')),
        ('assistant_referee', _('Arbitre Assistant')),
        ('timekeeper', _('Chronométreur')),
        ('scorekeeper', _('Marqueur')),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('novice', _('Novice - Première expérience')),
        ('beginner', _('Débutant - Quelques compétitions')),
        ('intermediate', _('Intermédiaire - Expérience régulière')),
        ('experienced', _('Expérimenté - Nombreuses compétitions')),
    ]
    
    # Relations principales
    competition = models.ForeignKey(
        'Competition', 
        on_delete=models.CASCADE,
        related_name='adhoc_judges',
        verbose_name=_("Compétition")
    )
    practitioner = models.ForeignKey(
        'Practitioner',
        on_delete=models.CASCADE,
        related_name='adhoc_judge_assignments',
        verbose_name=_("Pratiquant")
    )
    
    # Source du recrutement
    SOURCE_CHOICES = [
        ('competition_participant', _('Participant à cette compétition')),
        ('club_member', _('Membre du club organisateur')),
        ('discipline_practitioner', _('Pratiquant de la discipline')),
        ('external_volunteer', _('Bénévole externe')),
    ]
    source = models.CharField(
        _("Source de recrutement"),
        max_length=30,
        choices=SOURCE_CHOICES,
        default='competition_participant'
    )
    
    # Type et statut
    judge_type = models.CharField(
        _("Type de juge"),
        max_length=20,
        choices=JUDGE_TYPE_CHOICES,
        default='technical_judge'
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    experience_level = models.CharField(
        _("Niveau d'expérience"),
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        default='novice'
    )
    
    # Catégories assignées
    assigned_categories = models.ManyToManyField(
        'CompetitionCategory',
        related_name='adhoc_judges',
        verbose_name=_("Catégories assignées"),
        blank=True
    )
    
    # Période d'activation
    activated_at = models.DateTimeField(_("Activé le"), null=True, blank=True)
    deactivated_at = models.DateTimeField(_("Désactivé le"), null=True, blank=True)
    
    # Traçabilité
    recruited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recruited_adhoc_judges',
        verbose_name=_("Recruté par")
    )
    recruitment_date = models.DateTimeField(_("Date de recrutement"), auto_now_add=True)
    
    # Consentement et briefing
    has_accepted = models.BooleanField(_("A accepté la mission"), default=False)
    briefing_completed = models.BooleanField(_("Briefing effectué"), default=False)
    briefing_date = models.DateTimeField(_("Date du briefing"), null=True, blank=True)
    
    # Notes et évaluation
    notes = models.TextField(_("Notes"), blank=True)
    performance_rating = models.PositiveSmallIntegerField(
        _("Évaluation de performance"),
        null=True,
        blank=True,
        help_text=_("Note de 1 à 5 sur la qualité du travail")
    )
    performance_comments = models.TextField(_("Commentaires sur la performance"), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Juge ad-hoc")
        verbose_name_plural = _("Juges ad-hoc")
        unique_together = ['competition', 'practitioner', 'judge_type']
        ordering = ['-recruitment_date']
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_judge_type_display()} ({self.competition.title})"
    
    def activate(self, user=None):
        """Active le juge ad-hoc et lui donne accès au dashboard."""
        self.status = 'active'
        self.activated_at = timezone.now()
        self.has_accepted = True
        self.save()
        
        # Activer le flag juge dans la registration si existante
        self._update_registration_flags(True)
        
        # Créer un compte utilisateur si nécessaire
        if not self.practitioner.user:
            self.practitioner.create_user_account()
        
        return True
    
    def deactivate(self, reason='completed'):
        """Désactive le juge ad-hoc."""
        self.status = reason
        self.deactivated_at = timezone.now()
        self.save()
        
        # Retirer le flag juge de la registration
        self._update_registration_flags(False)
    
    def _update_registration_flags(self, is_judge: bool):
        """Met à jour les flags de juge dans l'inscription."""
        from .registrations import CompetitionRegistration
        
        try:
            registration = CompetitionRegistration.objects.get(
                competition=self.competition,
                practitioner=self.practitioner
            )
            if self.judge_type == 'technical_judge':
                registration.is_technical_judge = is_judge
            elif self.judge_type in ['combat_referee', 'assistant_referee']:
                registration.is_combat_referee = is_judge
            registration.save()
        except CompetitionRegistration.DoesNotExist:
            pass
    
    @property
    def is_active(self):
        """Vérifie si le juge est actuellement actif."""
        return self.status == 'active'
    
    @property
    def practitioner_age(self):
        """Retourne l'âge du pratiquant."""
        return self.practitioner.age if self.practitioner else None
    
    @classmethod
    def get_eligible_participants(cls, competition, judge_type='technical_judge', min_age=18):
        """
        Retourne les participants éligibles pour être juges ad-hoc.
        
        Critères:
        - Âge minimum (par défaut 18 ans)
        - Inscrits à la compétition OU pratiquants adultes de la discipline
        - Pas déjà assignés comme juges pour ce type
        """
        from .practitioners import Practitioner
        from .registrations import CompetitionRegistration
        from django.db.models import Q
        from datetime import date
        
        # Calculer la date de naissance maximum pour avoir min_age
        today = date.today()
        max_birth_date = date(today.year - min_age, today.month, today.day)
        
        # Pratiquants déjà assignés comme juges ad-hoc
        already_assigned = cls.objects.filter(
            competition=competition,
            judge_type=judge_type,
            status__in=['pending', 'active']
        ).values_list('practitioner_id', flat=True)
        
        # Option 1: Participants inscrits à la compétition (adultes)
        registered_ids = CompetitionRegistration.objects.filter(
            competition=competition,
            status='approved'
        ).values_list('practitioner_id', flat=True)
        
        eligible_registered = Practitioner.objects.filter(
            id__in=registered_ids,
            birth_date__lte=max_birth_date,
            is_active=True
        ).exclude(id__in=already_assigned)
        
        # Option 2: Pratiquants adultes de la discipline (non inscrits)
        discipline_ids = competition.disciplines.values_list('id', flat=True)
        
        eligible_discipline = Practitioner.objects.filter(
            disciplines__id__in=discipline_ids,
            birth_date__lte=max_birth_date,
            is_active=True
        ).exclude(
            id__in=registered_ids  # Exclure ceux déjà dans la liste des inscrits
        ).exclude(
            id__in=already_assigned
        ).distinct()
        
        return {
            'registered_participants': eligible_registered,
            'discipline_practitioners': eligible_discipline,
        }
```

---

## 📱 Interface Utilisateur Modifiée

### Template : Section Juges Ad-Hoc

```html
<!-- templates/competitions/manage/adhoc_judges_section.html -->

<div class="card mt-4">
    <div class="card-header bg-warning text-dark d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
            <i class="fas fa-user-plus me-2"></i>
            {% trans "Recrutement de Juges Ad-Hoc" %}
        </h5>
        <button class="btn btn-sm btn-dark" data-bs-toggle="modal" data-bs-target="#recruitJudgeModal">
            <i class="fas fa-plus me-1"></i>{% trans "Recruter un juge" %}
        </button>
    </div>
    <div class="card-body">
        <div class="alert alert-info mb-3">
            <i class="fas fa-info-circle me-2"></i>
            {% trans "Sélectionnez des participants adultes (18+) ou des pratiquants de la discipline pour les recruter temporairement comme juges." %}
        </div>
        
        <!-- Onglets: Participants inscrits / Pratiquants discipline -->
        <ul class="nav nav-tabs" id="adhocJudgeTabs" role="tablist">
            <li class="nav-item">
                <a class="nav-link active" data-bs-toggle="tab" href="#registeredParticipants">
                    <i class="fas fa-users me-1"></i>
                    {% trans "Participants inscrits" %}
                    <span class="badge bg-primary ms-1">{{ eligible_registered_count }}</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" data-bs-toggle="tab" href="#disciplinePractitioners">
                    <i class="fas fa-user-ninja me-1"></i>
                    {% trans "Pratiquants de la discipline" %}
                    <span class="badge bg-secondary ms-1">{{ eligible_discipline_count }}</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" data-bs-toggle="tab" href="#activeAdhocJudges">
                    <i class="fas fa-gavel me-1"></i>
                    {% trans "Juges ad-hoc actifs" %}
                    <span class="badge bg-success ms-1">{{ active_adhoc_count }}</span>
                </a>
            </li>
        </ul>
        
        <div class="tab-content p-3 border border-top-0">
            <!-- Tab 1: Participants inscrits -->
            <div class="tab-pane fade show active" id="registeredParticipants">
                <div class="table-responsive">
                    <table class="table table-hover" id="eligibleParticipantsTable">
                        <thead>
                            <tr>
                                <th>{% trans "Pratiquant" %}</th>
                                <th>{% trans "Âge" %}</th>
                                <th>{% trans "Grade" %}</th>
                                <th>{% trans "Club" %}</th>
                                <th>{% trans "Catégorie inscrite" %}</th>
                                <th class="text-center">{% trans "Actions" %}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for participant in eligible_registered %}
                            <tr data-practitioner-id="{{ participant.id }}">
                                <td>
                                    <strong>{{ participant.full_name }}</strong>
                                    {% if participant.user %}
                                    <i class="fas fa-check-circle text-success ms-1" title="{% trans 'Compte actif' %}"></i>
                                    {% endif %}
                                </td>
                                <td>
                                    <span class="badge bg-info">{{ participant.age }} {% trans "ans" %}</span>
                                </td>
                                <td>{{ participant.current_grade|default:"-" }}</td>
                                <td>{{ participant.club.name|default:"-" }}</td>
                                <td>
                                    {% for cat in participant.competition_categories %}
                                    <span class="badge bg-secondary">{{ cat.name }}</span>
                                    {% endfor %}
                                </td>
                                <td class="text-center">
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary btn-recruit-judge" 
                                                data-practitioner-id="{{ participant.id }}"
                                                data-practitioner-name="{{ participant.full_name }}"
                                                data-judge-type="technical_judge"
                                                title="{% trans 'Recruter comme Juge Technique' %}">
                                            <i class="fas fa-clipboard-list"></i>
                                        </button>
                                        <button class="btn btn-outline-danger btn-recruit-judge"
                                                data-practitioner-id="{{ participant.id }}"
                                                data-practitioner-name="{{ participant.full_name }}"
                                                data-judge-type="combat_referee"
                                                title="{% trans 'Recruter comme Arbitre Combat' %}">
                                            <i class="fas fa-gavel"></i>
                                        </button>
                                        <button class="btn btn-outline-secondary btn-recruit-judge"
                                                data-practitioner-id="{{ participant.id }}"
                                                data-practitioner-name="{{ participant.full_name }}"
                                                data-judge-type="timekeeper"
                                                title="{% trans 'Recruter comme Chronométreur' %}">
                                            <i class="fas fa-stopwatch"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="6" class="text-center text-muted py-4">
                                    <i class="fas fa-user-slash fa-2x mb-2"></i>
                                    <p>{% trans "Aucun participant adulte éligible trouvé" %}</p>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Tab 2: Pratiquants discipline -->
            <div class="tab-pane fade" id="disciplinePractitioners">
                <!-- Structure similaire pour les pratiquants de la discipline non inscrits -->
                <div class="alert alert-warning mb-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    {% trans "Ces pratiquants ne sont pas inscrits à la compétition. Un compte temporaire sera créé si nécessaire." %}
                </div>
                <!-- Table similaire... -->
            </div>
            
            <!-- Tab 3: Juges ad-hoc actifs -->
            <div class="tab-pane fade" id="activeAdhocJudges">
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>{% trans "Juge" %}</th>
                                <th>{% trans "Type" %}</th>
                                <th>{% trans "Catégories" %}</th>
                                <th>{% trans "Statut" %}</th>
                                <th>{% trans "Activé le" %}</th>
                                <th>{% trans "Actions" %}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for adhoc in active_adhoc_judges %}
                            <tr>
                                <td>{{ adhoc.practitioner.full_name }}</td>
                                <td>
                                    <span class="badge bg-{{ adhoc.judge_type|judge_type_color }}">
                                        {{ adhoc.get_judge_type_display }}
                                    </span>
                                </td>
                                <td>
                                    {% for cat in adhoc.assigned_categories.all %}
                                    <span class="badge bg-light text-dark">{{ cat.name }}</span>
                                    {% endfor %}
                                </td>
                                <td>
                                    <span class="badge bg-success">{% trans "Actif" %}</span>
                                    {% if adhoc.briefing_completed %}
                                    <i class="fas fa-graduation-cap text-info ms-1" title="{% trans 'Briefing effectué' %}"></i>
                                    {% endif %}
                                </td>
                                <td>{{ adhoc.activated_at|date:"d/m H:i" }}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-warning btn-manage-adhoc"
                                            data-adhoc-id="{{ adhoc.id }}">
                                        <i class="fas fa-cog"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger btn-deactivate-adhoc"
                                            data-adhoc-id="{{ adhoc.id }}">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="6" class="text-center text-muted py-4">
                                    {% trans "Aucun juge ad-hoc actuellement actif" %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal de recrutement rapide -->
<div class="modal fade" id="recruitJudgeModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-warning">
                <h5 class="modal-title">
                    <i class="fas fa-user-plus me-2"></i>
                    {% trans "Recruter un juge ad-hoc" %}
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="recruitJudgeForm">
                    {% csrf_token %}
                    <input type="hidden" name="practitioner_id" id="recruitPractitionerId">
                    <input type="hidden" name="competition_id" value="{{ competition.id }}">
                    
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="form-label">{% trans "Pratiquant" %}</label>
                            <input type="text" class="form-control" id="recruitPractitionerName" readonly>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{% trans "Type de juge" %}</label>
                            <select name="judge_type" class="form-select" id="recruitJudgeType">
                                <option value="technical_judge">{% trans "Juge Technique" %}</option>
                                <option value="combat_referee">{% trans "Arbitre Combat" %}</option>
                                <option value="assistant_referee">{% trans "Arbitre Assistant" %}</option>
                                <option value="timekeeper">{% trans "Chronométreur" %}</option>
                                <option value="scorekeeper">{% trans "Marqueur" %}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">{% trans "Niveau d'expérience" %}</label>
                        <select name="experience_level" class="form-select">
                            <option value="novice">{% trans "Novice - Première expérience" %}</option>
                            <option value="beginner">{% trans "Débutant - Quelques compétitions" %}</option>
                            <option value="intermediate">{% trans "Intermédiaire - Expérience régulière" %}</option>
                            <option value="experienced">{% trans "Expérimenté - Nombreuses compétitions" %}</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">{% trans "Catégories à assigner" %}</label>
                        <div class="row" id="categoryCheckboxes">
                            {% for category in competition.categories.all %}
                            <div class="col-md-6">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" 
                                           name="categories" value="{{ category.id }}" 
                                           id="cat_{{ category.id }}">
                                    <label class="form-check-label" for="cat_{{ category.id }}">
                                        {{ category.name }}
                                    </label>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">{% trans "Notes" %}</label>
                        <textarea name="notes" class="form-control" rows="2" 
                                  placeholder="{% trans 'Notes ou instructions particulières...' %}"></textarea>
                    </div>
                    
                    <div class="form-check mb-3">
                        <input class="form-check-input" type="checkbox" name="activate_immediately" 
                               id="activateImmediately" checked>
                        <label class="form-check-label" for="activateImmediately">
                            {% trans "Activer immédiatement et donner accès au dashboard juge" %}
                        </label>
                    </div>
                    
                    <div class="form-check mb-3">
                        <input class="form-check-input" type="checkbox" name="send_notification" 
                               id="sendNotification" checked>
                        <label class="form-check-label" for="sendNotification">
                            {% trans "Envoyer une notification au pratiquant" %}
                        </label>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    {% trans "Annuler" %}
                </button>
                <button type="button" class="btn btn-warning" id="confirmRecruitBtn">
                    <i class="fas fa-check me-1"></i>{% trans "Recruter ce juge" %}
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🔧 Vues et API

### Vue de Recrutement

```python
# apps/competitions/views/adhoc_judges.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone

from competitions.models import Competition, Practitioner, AdHocJudge
from competitions.utils.decorators import competition_manager_required


@login_required
@competition_manager_required
def adhoc_judges_dashboard(request, competition_id):
    """Dashboard de gestion des juges ad-hoc."""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Récupérer les participants éligibles
    eligible = AdHocJudge.get_eligible_participants(competition)
    
    # Juges ad-hoc actifs
    active_adhoc = AdHocJudge.objects.filter(
        competition=competition,
        status='active'
    ).select_related('practitioner')
    
    context = {
        'competition': competition,
        'eligible_registered': eligible['registered_participants'],
        'eligible_discipline': eligible['discipline_practitioners'],
        'eligible_registered_count': eligible['registered_participants'].count(),
        'eligible_discipline_count': eligible['discipline_practitioners'].count(),
        'active_adhoc_judges': active_adhoc,
        'active_adhoc_count': active_adhoc.count(),
    }
    
    return render(request, 'competitions/manage/adhoc_judges_dashboard.html', context)


@login_required
@require_POST
def recruit_adhoc_judge(request, competition_id):
    """API pour recruter un juge ad-hoc."""
    competition = get_object_or_404(Competition, id=competition_id)
    
    practitioner_id = request.POST.get('practitioner_id')
    judge_type = request.POST.get('judge_type', 'technical_judge')
    experience_level = request.POST.get('experience_level', 'novice')
    category_ids = request.POST.getlist('categories')
    notes = request.POST.get('notes', '')
    activate_immediately = request.POST.get('activate_immediately') == 'on'
    send_notification = request.POST.get('send_notification') == 'on'
    
    try:
        practitioner = Practitioner.objects.get(id=practitioner_id)
        
        # Vérifier l'âge
        if practitioner.age < 18:
            return JsonResponse({
                'success': False,
                'error': _("Le pratiquant doit avoir au moins 18 ans.")
            }, status=400)
        
        # Vérifier s'il n'est pas déjà assigné
        existing = AdHocJudge.objects.filter(
            competition=competition,
            practitioner=practitioner,
            judge_type=judge_type,
            status__in=['pending', 'active']
        ).exists()
        
        if existing:
            return JsonResponse({
                'success': False,
                'error': _("Ce pratiquant est déjà assigné comme juge pour cette compétition.")
            }, status=400)
        
        # Déterminer la source
        from competitions.models import CompetitionRegistration
        is_registered = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner=practitioner
        ).exists()
        source = 'competition_participant' if is_registered else 'discipline_practitioner'
        
        # Créer le juge ad-hoc
        adhoc = AdHocJudge.objects.create(
            competition=competition,
            practitioner=practitioner,
            judge_type=judge_type,
            experience_level=experience_level,
            source=source,
            recruited_by=request.user,
            notes=notes,
            status='pending'
        )
        
        # Assigner les catégories
        if category_ids:
            from competitions.models import CompetitionCategory
            categories = CompetitionCategory.objects.filter(
                id__in=category_ids,
                competition=competition
            )
            adhoc.assigned_categories.set(categories)
        
        # Activer immédiatement si demandé
        if activate_immediately:
            adhoc.activate(user=request.user)
            
            # Créer un compte utilisateur si nécessaire
            if not practitioner.user:
                user, password, created = practitioner.create_user_account()
                if created and send_notification:
                    # Envoyer les identifiants par email/SMS
                    pass  # TODO: Implémenter l'envoi de notification
        
        # Envoyer notification si demandé
        if send_notification and practitioner.user:
            # TODO: Créer une notification
            pass
        
        return JsonResponse({
            'success': True,
            'message': _("Juge ad-hoc recruté avec succès."),
            'adhoc_id': adhoc.id,
            'activated': activate_immediately
        })
        
    except Practitioner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _("Pratiquant non trouvé.")
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def deactivate_adhoc_judge(request, adhoc_id):
    """Désactive un juge ad-hoc."""
    adhoc = get_object_or_404(AdHocJudge, id=adhoc_id)
    
    reason = request.POST.get('reason', 'completed')
    adhoc.deactivate(reason=reason)
    
    return JsonResponse({
        'success': True,
        'message': _("Juge ad-hoc désactivé.")
    })


@login_required
def get_eligible_practitioners_api(request, competition_id):
    """API pour récupérer les pratiquants éligibles (AJAX)."""
    competition = get_object_or_404(Competition, id=competition_id)
    judge_type = request.GET.get('judge_type', 'technical_judge')
    min_age = int(request.GET.get('min_age', 18))
    
    eligible = AdHocJudge.get_eligible_participants(
        competition,
        judge_type=judge_type,
        min_age=min_age
    )
    
    def serialize_practitioner(p, is_registered=False):
        return {
            'id': p.id,
            'full_name': p.full_name,
            'age': p.age,
            'club': p.club.name if p.club else None,
            'grade': str(p.current_grade) if hasattr(p, 'current_grade') and p.current_grade else None,
            'has_account': bool(p.user),
            'is_registered': is_registered
        }
    
    return JsonResponse({
        'registered': [serialize_practitioner(p, True) for p in eligible['registered_participants']],
        'discipline': [serialize_practitioner(p, False) for p in eligible['discipline_practitioners']],
    })
```

---

## 🛤️ URLs à Ajouter

```python
# apps/competitions/urls/adhoc_judges.py

from django.urls import path
from competitions.views import adhoc_judges

app_name = 'adhoc_judges'

urlpatterns = [
    path(
        'competition/<int:competition_id>/adhoc-judges/',
        adhoc_judges.adhoc_judges_dashboard,
        name='dashboard'
    ),
    path(
        'competition/<int:competition_id>/adhoc-judges/recruit/',
        adhoc_judges.recruit_adhoc_judge,
        name='recruit'
    ),
    path(
        'adhoc-judge/<int:adhoc_id>/deactivate/',
        adhoc_judges.deactivate_adhoc_judge,
        name='deactivate'
    ),
    path(
        'competition/<int:competition_id>/adhoc-judges/eligible/',
        adhoc_judges.get_eligible_practitioners_api,
        name='eligible_api'
    ),
]
```

---

## 📋 Modification du Dashboard Juge

Le dashboard juge existant doit détecter les juges ad-hoc et leur montrer une interface adaptée :

```python
# Dans la vue du dashboard juge (referee.html context)

def get_judge_context(request, user):
    """Récupère le contexte pour un utilisateur qui peut être juge officiel ou ad-hoc."""
    
    context = {
        'is_official_judge': False,
        'is_adhoc_judge': False,
        'adhoc_assignments': [],
        'official_assignments': [],
    }
    
    # Vérifier si juge officiel
    if hasattr(user, 'judge_profile'):
        context['is_official_judge'] = True
        # ... récupérer les assignations officielles
    
    # Vérifier si juge ad-hoc actif
    if hasattr(user, 'practitioner'):
        practitioner = user.practitioner
        adhoc_active = AdHocJudge.objects.filter(
            practitioner=practitioner,
            status='active',
            competition__end_date__gte=timezone.now().date()
        ).select_related('competition').prefetch_related('assigned_categories')
        
        if adhoc_active.exists():
            context['is_adhoc_judge'] = True
            context['adhoc_assignments'] = adhoc_active
    
    return context
```

---

## 🚀 Prompt d'Exécution

Utilisez ce prompt pour démarrer l'implémentation :

---

**PROMPT:**

> Implémente le système de juges ad-hoc pour MartialComp. Commence par créer le modèle `AdHocJudge` dans `apps/competitions/models/adhoc_judges.py` avec les champs décrits (competition, practitioner, judge_type, status, assigned_categories, etc.). Ajoute la méthode de classe `get_eligible_participants()` qui retourne les participants adultes (18+) inscrits à la compétition et les pratiquants de la discipline non inscrits.
>
> Ensuite, crée les vues dans `apps/competitions/views/adhoc_judges.py` :
> - `adhoc_judges_dashboard` : affiche les pratiquants éligibles dans 2 onglets (inscrits / discipline)
> - `recruit_adhoc_judge` : API POST pour recruter un juge avec activation optionnelle
> - `deactivate_adhoc_judge` : API pour désactiver un juge
>
> Modifie le template `competition_management_pro.html` pour ajouter la section de recrutement de juges ad-hoc après la section des juges techniques officiels. Intègre le modal de recrutement rapide avec sélection du type de juge et des catégories.
>
> Enfin, modifie le dashboard juge (`referee.html`) pour détecter si l'utilisateur est un juge ad-hoc actif et lui afficher ses assignations avec un badge "Juge Temporaire".

---

## ✅ Checklist d'Implémentation

- [ ] Créer le modèle `AdHocJudge`
- [ ] Ajouter la migration
- [ ] Créer les vues de gestion
- [ ] Ajouter les URLs
- [ ] Modifier le template de gestion de compétition
- [ ] Ajouter le modal de recrutement
- [ ] Modifier le dashboard juge pour les ad-hoc
- [ ] Ajouter les notifications (optionnel)
- [ ] Créer les tests unitaires
- [ ] Documenter l'utilisation
