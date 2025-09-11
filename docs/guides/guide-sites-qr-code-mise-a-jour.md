# Guide mis à jour : Système de sites en sous-domaine et QR codes pour les organisations

## Contexte et objectifs

Dans le cadre de la plateforme MartialComp, nous mettons en place un système permettant à chaque organisation enregistrée (fédérations, clubs, coachs sportifs) de disposer automatiquement d'un site web dédié en sous-domaine, intégrant un système de QR codes pour les inscriptions et le suivi des pratiquants.

Suite aux tests effectués par Maxence, plusieurs ajustements et corrections sont nécessaires pour assurer une expérience utilisateur optimale. Ce document intègre ces retours et précise les spécifications techniques pour les développeurs.

## 1. Création automatique de sous-domaines

### Spécifications initiales
- Format : `[identifiant-organisation].martialcomp.com`
- Identifiant généré à partir du nom de l'organisation (caractères spéciaux et espaces remplacés par des tirets, en minuscules)

### Implémentation technique
```python
def generate_subdomain(organization_name):
    """
    Génère un sous-domaine valide à partir du nom d'une organisation.
    """
    # Convertir en minuscules
    subdomain = organization_name.lower()
    # Remplacer les caractères spéciaux et espaces par des tirets
    subdomain = re.sub(r'[^\w\s-]', '', subdomain)
    subdomain = re.sub(r'[\s_]+', '-', subdomain)
    # Limiter la longueur
    if len(subdomain) > 63:  # Limite DNS
        subdomain = subdomain[:63]
    # Éliminer les tirets consécutifs et les tirets en début/fin
    subdomain = re.sub(r'-+', '-', subdomain).strip('-')
    
    return subdomain
```

## 2. Système de QR codes - CORRECTIONS PRIORITAIRES

Suite aux tests de Maxence, plusieurs problèmes ont été identifiés dans le système de QR codes. Voici les correctifs à apporter en priorité :

### 2.1 Redirection QR code pour inscription au club

#### Problème identifié
Le QR code d'une organisation ne redirige pas correctement vers la page d'inscription du club concerné.

#### Solution à implémenter
```python
def generate_organization_qr_code(organization, purpose='registration'):
    """
    Génère un QR code pour une organisation avec un objectif spécifique.
    
    Args:
        organization: Instance de l'organisation
        purpose: Objectif du QR code ('registration', 'homepage', 'event', etc.)
    
    Returns:
        QR code au format PNG (BytesIO)
    """
    # Construire l'URL avec des paramètres explicites
    base_url = f"https://{organization.subdomain}.martialcomp.com"
    
    if purpose == 'registration':
        # S'assurer que la redirection mène directement au formulaire d'inscription
        target_url = f"{base_url}/inscription/?source=qr_code&org_id={organization.id}"
    elif purpose == 'homepage':
        target_url = base_url
    elif purpose == 'event':
        target_url = f"{base_url}/evenements/?source=qr_code"
    else:
        target_url = base_url
    
    # Ajouter des paramètres de tracking
    target_url += f"&timestamp={int(time.time())}"
    
    # Générer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    # Créer l'image avec le logo de l'organisation au centre si disponible
    img = qr.make_image(fill_color="black", back_color="white")
    
    if organization.logo:
        # Ajouter le logo au centre du QR code
        logo = Image.open(organization.logo.path)
        # Redimensionner le logo
        logo_size = img.size[0] // 4
        logo = logo.resize((logo_size, logo_size))
        
        # Calculer la position pour centrer le logo
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        
        # Coller le logo
        img.paste(logo, pos, logo.convert('RGBA'))
    
    # Convertir en BytesIO pour le stockage ou l'affichage
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer
```

#### Modifications requises dans la vue d'inscription

```python
def registration_view(request):
    """Vue pour le formulaire d'inscription."""
    # Récupérer l'ID de l'organisation depuis les paramètres
    org_id = request.GET.get('org_id')
    source = request.GET.get('source')
    
    # Journaliser l'accès pour debugging
    logger.info(f"Accès au formulaire d'inscription - org_id: {org_id}, source: {source}")
    
    organization = None
    if org_id:
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            # Log l'erreur mais continuer avec la logique du tenant
            logger.error(f"Organisation avec ID {org_id} non trouvée")
    
    # Si pas d'org_id ou organisation non trouvée, utiliser la logique du tenant
    if not organization:
        # Récupérer l'organisation basée sur le sous-domaine
        current_tenant = get_current_tenant()
        if current_tenant:
            organization = Organization.objects.filter(tenant=current_tenant).first()
    
    # Suite de la logique d'inscription...
```

### 2.2 Contrôle de présence manuel (alternative au QR code)

#### Problème identifié
Le système actuel oblige à scanner un QR code pour marquer la présence d'un pratiquant, sans alternative manuelle.

#### Solution à implémenter

Créer une nouvelle vue pour le pointage manuel des présences :

```python
@login_required
def manual_attendance(request):
    """Vue pour le pointage manuel des présences."""
    # Récupérer l'organisation de l'utilisateur connecté
    user_orgs = get_user_organizations(request.user)
    
    if not user_orgs:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('dashboard')
    
    # Par défaut, utiliser la première organisation
    organization = user_orgs[0]
    
    # Si plusieurs organisations, permettre de choisir
    if len(user_orgs) > 1 and request.method == 'POST' and 'organization' in request.POST:
        org_id = request.POST.get('organization')
        organization = Organization.objects.get(id=org_id)
    
    # Récupérer tous les pratiquants de l'organisation
    practitioners = Practitioner.objects.filter(organizations=organization)
    
    # Traiter le formulaire de présence
    if request.method == 'POST' and 'mark_attendance' in request.POST:
        practitioner_ids = request.POST.getlist('practitioners')
        event_id = request.POST.get('event')
        date = request.POST.get('date', datetime.now().date())
        
        for practitioner_id in practitioner_ids:
            # Créer ou mettre à jour l'enregistrement de présence
            Attendance.objects.update_or_create(
                practitioner_id=practitioner_id,
                event_id=event_id if event_id else None,
                date=date,
                defaults={
                    'present': True,
                    'marked_by': request.user,
                    'marked_manually': True
                }
            )
        
        messages.success(request, f"{len(practitioner_ids)} pratiquants marqués présents.")
        
    # Récupérer les événements à venir pour le menu déroulant
    upcoming_events = Event.objects.filter(
        organization=organization,
        date__gte=datetime.now().date()
    ).order_by('date')
    
    context = {
        'practitioners': practitioners,
        'organization': organization,
        'organizations': user_orgs,
        'upcoming_events': upcoming_events,
    }
    
    return render(request, 'competitions/attendance/manual_attendance.html', context)
```

Template HTML correspondant (à créer) :

```html
{% extends "base.html" %}
{% load i18n %}

{% block content %}
<div class="container">
    <h1>{% translate "Pointage manuel des présences" %}</h1>
    
    {% if organizations|length > 1 %}
    <form method="post" class="mb-4">
        {% csrf_token %}
        <div class="form-group">
            <label for="organization">{% translate "Sélectionner l'organisation" %}</label>
            <select name="organization" id="organization" class="form-control" onchange="this.form.submit()">
                {% for org in organizations %}
                <option value="{{ org.id }}" {% if org.id == organization.id %}selected{% endif %}>{{ org.name }}</option>
                {% endfor %}
            </select>
        </div>
    </form>
    {% endif %}
    
    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="mark_attendance" value="1">
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="event">{% translate "Événement (optionnel)" %}</label>
                    <select name="event" id="event" class="form-control">
                        <option value="">{% translate "Présence régulière (pas d'événement spécifique)" %}</option>
                        {% for event in upcoming_events %}
                        <option value="{{ event.id }}">{{ event.name }} - {{ event.date|date:"d/m/Y" }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <div class="col-md-6">
                <div class="form-group">
                    <label for="date">{% translate "Date" %}</label>
                    <input type="date" name="date" id="date" class="form-control" value="{{ today|date:'Y-m-d' }}">
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">{% translate "Liste des pratiquants" %}</h5>
                <div>
                    <button type="button" class="btn btn-sm btn-outline-primary" id="select-all">{% translate "Tout sélectionner" %}</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="deselect-all">{% translate "Tout désélectionner" %}</button>
                </div>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th style="width: 50px;"></th>
                                <th>{% translate "Nom" %}</th>
                                <th>{% translate "Prénom" %}</th>
                                <th>{% translate "Discipline" %}</th>
                                <th>{% translate "Dernière présence" %}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for practitioner in practitioners %}
                            <tr>
                                <td>
                                    <div class="form-check">
                                        <input type="checkbox" name="practitioners" value="{{ practitioner.id }}" id="practitioner-{{ practitioner.id }}" class="form-check-input practitioner-checkbox">
                                    </div>
                                </td>
                                <td><label for="practitioner-{{ practitioner.id }}">{{ practitioner.last_name }}</label></td>
                                <td>{{ practitioner.first_name }}</td>
                                <td>{{ practitioner.primary_discipline.name }}</td>
                                <td>{{ practitioner.last_attendance|default:"-" }}</td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="5" class="text-center">{% translate "Aucun pratiquant trouvé" %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-check-circle me-2"></i>{% translate "Marquer les pratiquants sélectionnés comme présents" %}
            </button>
        </div>
    </form>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Sélectionner/désélectionner tous les pratiquants
    document.getElementById('select-all').addEventListener('click', function() {
        document.querySelectorAll('.practitioner-checkbox').forEach(function(checkbox) {
            checkbox.checked = true;
        });
    });
    
    document.getElementById('deselect-all').addEventListener('click', function() {
        document.querySelectorAll('.practitioner-checkbox').forEach(function(checkbox) {
            checkbox.checked = false;
        });
    });
});
</script>
{% endblock %}
```

Ajouter l'URL dans `urls.py` :

```python
path('attendance/manual/', views.manual_attendance, name='manual_attendance'),
```

Ajouter un lien vers cette page dans le dashboard et la page de scan QR :

```html
<a href="{% url 'competitions:manual_attendance' %}" class="btn btn-outline-primary">
    <i class="fas fa-clipboard-check me-2"></i>{% translate "Pointage manuel des présences" %}
</a>
```

## 3. Dashboard et navigation - CORRECTIONS NÉCESSAIRES

### 3.1 Bouton de retour au dashboard principal depuis Shop

#### Problème identifié
Absence d'un bouton de retour au tableau de bord principal depuis le dashboard Shop.

#### Solution à implémenter

Ajouter le bouton suivant dans le template `shop/dashboard/base.html` au début de la barre latérale :

```html
<!-- Bouton de retour au dashboard principal -->
<div class="mb-4">
  <a href="{% url 'competitions:club:dashboard' %}" class="btn btn-outline-primary w-100">
    <i class="fas fa-arrow-left me-2"></i>{% translate "Retour au tableau de bord" %}
  </a>
</div>
```

### 3.2 Barre latérale cohérente

#### Problème identifié
Incohérence dans l'affichage/masquage de la barre latérale.

#### Solution à implémenter

Créer un script JavaScript global pour gérer l'état de la barre latérale :

```javascript
// sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    
    // Fonction pour mettre à jour l'affichage
    function updateSidebarState(isExpanded) {
        if (isExpanded) {
            sidebar.classList.remove('collapsed');
            content.classList.remove('expanded');
        } else {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
        }
        
        // Enregistrer la préférence
        localStorage.setItem('sidebarExpanded', isExpanded);
    }
    
    // Récupérer l'état enregistré
    const savedState = localStorage.getItem('sidebarExpanded');
    const initialState = savedState !== null ? savedState === 'true' : true;
    
    // Appliquer l'état initial
    updateSidebarState(initialState);
    
    // Gérer le clic sur le bouton de toggle
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const currentState = sidebar.classList.contains('collapsed');
            updateSidebarState(!currentState);
        });
    }
    
    // S'assurer que tous les boutons de menu hamburger fonctionnent
    document.querySelectorAll('.navbar-toggler').forEach(function(button) {
        button.addEventListener('click', function() {
            const currentState = sidebar.classList.contains('collapsed');
            updateSidebarState(!currentState);
        });
    });
});
```

Inclure ce script dans tous les templates de base :

```html
{% block extra_js %}
<script src="{% static 'js/sidebar.js' %}"></script>
{% endblock %}
```

## 4. Gestion des événements - CORRECTIONS NÉCESSAIRES

### 4.1 Intégration dashboard

#### Problème identifié
Les événements créés ne sont pas pris en compte dans le dashboard.

#### Solution à implémenter

Modifier la vue du dashboard pour inclure tous les événements :

```python
def club_dashboard(request):
    """Vue du tableau de bord du club."""
    # Code existant...
    
    # Récupérer tous les événements, y compris ceux créés récemment
    recent_events = Event.objects.filter(
        organization=organization,
        date__gte=datetime.now().date()
    ).order_by('date')[:5]
    
    # S'assurer que les événements sont bien inclus dans le contexte
    context.update({
        'recent_events': recent_events,
        # Autres données de contexte...
    })
    
    return render(request, 'competitions/dashboard/club.html', context)
```

### 4.2 Simplification du formulaire d'événement

#### Problème identifié
Le champ "organisation" est redondant lors de la création d'événements puisque par défaut, c'est l'organisation actuelle qui est l'organisatrice.

#### Solution à implémenter

Modifier le formulaire d'événement :

```python
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name', 'description', 'date', 'start_time', 'end_time',
            'location', 'event_type', 'disciplines', 'is_public'
        ]  # Retirer 'organization' des champs
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        # Autres initialisations...

class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passer l'organisation au formulaire
        kwargs['organization'] = self.request.user.get_current_organization()
        return kwargs
    
    def form_valid(self, form):
        # Assigner automatiquement l'organisation actuelle
        form.instance.organization = self.request.user.get_current_organization()
        return super().form_valid(form)
```

### 4.3 Amélioration des notifications

#### Problème identifié
Problème de notifications multiples et options de personnalisation insuffisantes.

#### Solution à implémenter

1. Éliminer les doubles notifications :

```python
def send_event_notification(event, recipients=None):
    """
    Envoie des notifications pour un événement en évitant les doublons.
    """
    # Si aucun destinataire n'est spécifié, utiliser tous les membres de l'organisation
    if recipients is None:
        recipients = Practitioner.objects.filter(organizations=event.organization)
    
    # Vérifier si des notifications existent déjà pour cet événement et ces destinataires
    existing_notifications = Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(Event),
        object_id=event.id
    )
    
    # Récupérer les IDs des pratiquants ayant déjà reçu une notification
    notified_ids = existing_notifications.values_list('recipient_id', flat=True)
    
    # Filtrer pour ne garder que les destinataires qui n'ont pas encore reçu de notification
    new_recipients = recipients.exclude(id__in=notified_ids)
    
    # Créer les notifications pour les nouveaux destinataires
    notifications = []
    for recipient in new_recipients:
        # Vérifier les préférences de notification du destinataire
        if should_send_notification(recipient, event):
            notification = Notification(
                recipient=recipient,
                content_object=event,
                type='event',
                title=f"Nouvel événement : {event.name}",
                message=f"Un nouvel événement {event.name} aura lieu le {event.date}",
                created_by=event.created_by
            )
            notifications.append(notification)
    
    # Créer les notifications en masse
    if notifications:
        Notification.objects.bulk_create(notifications)
    
    return len(notifications)

def should_send_notification(recipient, event):
    """
    Vérifie si une notification doit être envoyée à un destinataire en fonction de ses préférences.
    """
    # Récupérer les préférences du destinataire
    preferences = NotificationPreference.objects.filter(user=recipient.user).first()
    
    if not preferences:
        # Par défaut, envoyer la notification
        return True
    
    # Vérifier si le destinataire veut recevoir des notifications pour ce type d'événement
    if event.event_type and not preferences.get_preference(f'event_{event.event_type}'):
        return False
    
    # Vérifier si l'événement concerne une discipline qui intéresse le destinataire
    if event.disciplines.exists():
        recipient_disciplines = recipient.disciplines.all()
        # Si l'événement a des disciplines spécifiques et que le destinataire n'en pratique aucune
        if not set(event.disciplines.all()).intersection(set(recipient_disciplines)):
            return False
    
    return True
```

2. Ajouter des options de personnalisation pour les rappels :

Créer un modèle pour les préférences de notification :

```python
class NotificationPreference(models.Model):
    """Préférences de notification d'un utilisateur."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Types d'événements
    notify_competitions = models.BooleanField(default=True, verbose_name=_("Compétitions"))
    notify_trainings = models.BooleanField(default=True, verbose_name=_("Entraînements"))
    notify_seminars = models.BooleanField(default=True, verbose_name=_("Séminaires"))
    notify_meetings = models.BooleanField(default=True, verbose_name=_("Réunions"))
    notify_social = models.BooleanField(default=True, verbose_name=_("Événements sociaux"))
    
    # Canaux de notification
    email_notifications = models.BooleanField(default=True, verbose_name=_("Recevoir par email"))
    app_notifications = models.BooleanField(default=True, verbose_name=_("Recevoir dans l'application"))
    
    # Rappels
    reminder_enabled = models.BooleanField(default=True, verbose_name=_("Activer les rappels"))
    reminder_days_before = models.IntegerField(default=1, verbose_name=_("Jours avant l'événement"))
    
    def get_preference(self, key):
        """Récupère une préférence par son nom."""
        if hasattr(self, key):
            return getattr(self, key)
        return True  # Par défaut, activer les notifications
```

Créer une vue pour gérer ces préférences :

```python
@login_required
def notification_preferences(request):
    """Vue pour gérer les préférences de notification."""
    # Récupérer ou créer les préférences de l'utilisateur
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vos préférences de notification ont été mises à jour."))
            return redirect('notification_preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    return render(request, 'notifications/preferences.html', {'form': form})
```

## 5. Importation en masse et IA - AMÉLIORATIONS FUTURES

Pour l'importation en masse à l'aide d'IA, une approche par étapes est recommandée :

1. Intégrer une bibliothèque Python pour l'analyse intelligente des fichiers (pandas, sklearn)
2. Développer un système d'apprentissage pour reconnaître les formats courants
3. Créer une interface utilisateur pour la prévisualisation et l'ajustement

Voici un exemple conceptuel pour l'importation intelligente :

```python
def analyze_file_structure(file_path):
    """
    Analyse la structure d'un fichier et suggère un mapping de colonnes.
    """
    # Détecter le type de fichier et le lire
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Format de fichier non supporté")
    
    # Analyser les en-têtes
    headers = df.columns.tolist()
    
    # Détecter les colonnes contenant des informations spécifiques
    column_mapping = {}
    
    # Recherche de motifs dans les noms de colonnes
    name_patterns = ['nom', 'name', 'lastname', 'last name', 'family name']
    firstname_patterns = ['prénom', 'prenom', 'firstname', 'first name', 'given name']
    email_patterns = ['email', 'e-mail', 'courriel', 'mail']
    
    # Analyser chaque colonne
    for col in headers:
        col_lower = col.lower()
        
        # Détecter les colonnes de nom
        if any(pattern in col_lower for pattern in name_patterns):
            column_mapping['last_name'] = col
        
        # Détecter les colonnes de prénom
        elif any(pattern in col_lower for pattern in firstname_patterns):
            column_mapping['first_name'] = col
        
        # Détecter les colonnes d'email
        elif any(pattern in col_lower for pattern in email_patterns):
            column_mapping['email'] = col
    
    # Analyser le contenu des colonnes non identifiées
    for col in headers:
        if col not in column_mapping.values():
            # Échantillon de valeurs
            sample = df[col].dropna().head(10).tolist()
            
            # Si toutes les valeurs ressemblent à des emails
            if all('@' in str(val) for val in sample if isinstance(val, str)):
                column_mapping.setdefault('email', col)
            
            # Si toutes les valeurs ressemblent à des dates
            elif all(re.match(r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}', str(val)) for val in sample if isinstance(val, str)):
                column_mapping.setdefault('birth_date', col)
    
    return {
        'headers': headers,
        'suggested_mapping': column_mapping,
        'preview': df.head(5).to_dict('records')
    }
```

## 6. Tests et intégration continue

Pour s'assurer que les correctifs sont efficaces, mettre en place une suite de tests automatisés :

```python
# tests/test_qr_codes.py
from django.test import TestCase, Client
from django.urls import reverse
from competitions.models import Organization, Practitioner, Event, Attendance

class QRCodeTests(TestCase):
    def setUp(self):
        # Créer une organisation de test
        self.organization = Organization.objects.create(
            name="Club Test",
            subdomain="club-test",
            organization_type="club"
        )
        
        # Créer un pratiquant de test
        self.practitioner = Practitioner.objects.create(
            first_name="Jean",
            last_name="Test",
            email="jean@test.com"
        )
        self.practitioner.organizations.add(self.organization)
        
        # Créer un événement de test
        self.event = Event.objects.create(
            name="Événement Test",
            organization=self.organization,
            date=datetime.now().date() + timedelta(days=7)
        )
        
        # Client de test
        self.client = Client()
    
    def test_qr_code_generation(self):
        """Teste la génération du QR code."""
        response = self.client.get(reverse('generate_qr_code', args=[self.organization.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
    
    def test_qr_code_redirection(self):
        """Teste la redirection du QR code vers la page d'inscription."""
        url = f"https://{self.organization.subdomain}.martialcomp.com/inscription/?source=qr_code&org_id={self.organization.id}"
        # Simuler une requête à l'URL générée
        response = self.client.get(f"/inscription/?source=qr_code&org_id={self.organization.id}", HTTP_HOST=f"{self.organization.subdomain}.martialcomp.com")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.organization.name)
    
    def test_manual_attendance(self):
        """Teste le pointage manuel des présences."""
        # Connexion d'un utilisateur administrateur
        # ...
        
        response = self.client.post(
            reverse('manual_attendance'),
            {
                'mark_attendance': '1',
                'practitioners': [self.practitioner.id],
                'event': self.event.id,
                'date': datetime.now().date().strftime('%Y-%m-%d')
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        
        # Vérifier que la présence a été enregistrée
        attendance = Attendance.objects.filter(
            practitioner=self.practitioner,
            event=self.event
        ).first()
        
        self.assertIsNotNone(attendance)
        self.assertTrue(attendance.present)
        self.assertTrue(attendance.marked_manually)
```

## Conclusion

Ces spécifications détaillées et les correctifs proposés répondent aux problèmes identifiés lors des tests de Maxence. En intégrant ces modifications, le système de sites en sous-domaine et de QR codes offrira une expérience utilisateur améliorée et plus flexible.

Les priorités de développement devraient être :

1. Corriger la redirection des QR codes pour l'inscription
2. Implémenter l'alternative manuelle au pointage par QR code
3. Ajouter le bouton de retour au dashboard principal depuis le Shop
4. Simplifier le formulaire d'événement et améliorer le système de notifications

Pour les aspects liés à l'IA pour l'importation en masse, une phase d'exploration et de prototypage est recommandée avant l'implémentation complète.
