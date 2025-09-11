# Intégration des Sous-domaines dans la Création de Club - MartialComp

## Problème Identifié

Le script de création de club actuel ne crée pas automatiquement de sous-domaine pour le club, contrairement au système d'organisations qui dispose déjà de cette fonctionnalité. Il manque l'intégration avec le système de templates de sites.

## Analyse du Système Existant

### 1. Système d'Organisations (`organizations/`)

**Modèle Organization :**

```python
class Organization(models.Model):
    name = models.CharField(_("Nom"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    organization_type = models.CharField(max_length=30, choices=OrganizationType.choices)
    # ... autres champs
```

**Signaux automatiques :**

```python
@receiver(post_save, sender=Organization)
def create_organization_site_disabled(sender, instance, created, **kwargs):
    if created:
        # 1. Générer le sous-domaine
        generator = SubdomainGenerator()
        subdomain = generator.generate_subdomain(instance)

        # 2. Créer le tenant
        tenant = create_organization_tenant(instance, subdomain)

        # 3. Générer les QR codes
        qr_codes = generate_organization_qr_codes(instance, tenant)
```

### 2. Générateur de Sous-domaines (`competitions/utils/subdomain_generator.py`)

**Classe SubdomainGenerator :**

```python
class SubdomainGenerator:
    def generate_subdomain(self, organization, force_prefix=False):
        # Déterminer le nom et le type de l'organisation
        org_name = self._extract_organization_name(organization)
        org_type = self._extract_organization_type(organization)

        # Générer le slug de base
        base_slug = self._create_slug(org_name)

        # Ajouter le préfixe si nécessaire
        if force_prefix or self._needs_prefix(base_slug):
            prefix = self.ORG_TYPE_PREFIXES.get(org_type, 'org')
            base_slug = f"{prefix}-{base_slug}"

        # Assurer l'unicité
        subdomain = self._ensure_uniqueness(base_slug)

        return subdomain
```

**Fonctionnalités clés :**

- Génération automatique de sous-domaines uniques
- Validation RFC 1123
- Préfixes par type d'organisation (club, federation, etc.)
- Gestion des conflits et résolution automatique

### 3. Création de Tenants

**Fonction `create_organization_tenant` :**

```python
def create_organization_tenant(organization, subdomain=None):
    if not subdomain:
        subdomain = self.generate_subdomain(organization)

    full_domain = f"{subdomain}.{self.base_domain}"

    # Déterminer le plan d'abonnement par défaut
    org_type = self._extract_organization_type(organization)
    default_plan = self._get_default_plan(org_type)

    # Créer le tenant
    tenant = Tenant.objects.create(
        domain=full_domain,
        name=self._extract_organization_name(organization),
        organization_type=org_type,
        is_active=True,
        plan=default_plan,
        max_users=self._get_plan_limits(default_plan)['max_users'],
        max_disciplines=self._get_plan_limits(default_plan)['max_disciplines']
    )

    # Associer l'organisation au tenant
    self._link_organization_to_tenant(organization, tenant)

    return tenant
```

## Solution Proposée

### 1. Modification du Modèle Club

**Ajouter la relation avec Organization :**

```python
# Dans competitions/models.py
class Club(models.Model):
    # ... champs existants ...

    # Relation avec le système d'organisations
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='club_instance',
        verbose_name=_("Organisation associée")
    )

    # Métadonnées pour le sous-domaine
    subdomain = models.CharField(
        _("Sous-domaine"),
        max_length=100,
        blank=True,
        help_text=_("Sous-domaine généré automatiquement")
    )

    def save(self, *args, **kwargs):
        # Créer l'organisation associée si elle n'existe pas
        if not self.organization:
            self.organization = self._create_associated_organization()

        super().save(*args, **kwargs)

    def _create_associated_organization(self):
        """Crée l'organisation associée au club."""
        from organizations.models import Organization, OrganizationType

        organization = Organization.objects.create(
            name=self.name,
            organization_type=OrganizationType.CLUB,
            description=self.description or f"Club {self.name}",
            email=self.contact_email,
            phone=self.contact_phone,
            website=self.website,
            address=self.address,
            city=self.city,
            postal_code=self.postal_code,
            logo=self.logo,
            created_by=self.owner,
            is_active=True
        )

        # Associer les disciplines
        if hasattr(self, 'disciplines'):
            organization.disciplines.set(self.disciplines.all())

        return organization
```

### 2. Modification de la Vue de Création de Club

**Intégrer la création de sous-domaine :**

```python
# Dans competitions/views/onboarding/club.py
from competitions.utils.subdomain_generator import SubdomainGenerator
from organizations.signals import create_organization_tenant

@login_required
def handle_club_creation(request):
    """Gestion de la création d'un club avec sous-domaine."""
    # ... vérifications existantes ...

    if request.method == 'POST':
        form = ClubCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Création du club
                    club = form.save(commit=False)
                    club.owner = request.user

                    # Gestion du logo
                    if 'logo' in request.FILES:
                        from ...utils.upload import handle_club_logo_upload
                        club.logo = handle_club_logo_upload(request.FILES['logo'], club.name)

                    # Sauvegarder le club (cela créera automatiquement l'organisation)
                    club.save()

                    # Gestion de la discipline
                    discipline = form.cleaned_data.get('discipline')
                    if discipline:
                        club.main_discipline = discipline
                        club.disciplines.add(discipline)

                    # CRÉATION DU SOUS-DOMAIN ET TENANT
                    if club.organization:
                        # Générer le sous-domaine
                        generator = SubdomainGenerator()
                        subdomain = generator.generate_subdomain(club.organization)

                        # Créer le tenant
                        tenant = create_organization_tenant(club.organization, subdomain)

                        # Mettre à jour le club avec le sous-domaine
                        club.subdomain = subdomain
                        club.save()

                        # Générer les QR codes
                        from competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
                        qr_codes = generate_organization_qr_codes_set(club.organization)

                        logger.info(f"Sous-domaine créé pour {club.name}: {subdomain}")
                        logger.info(f"Tenant créé: {tenant.domain}")
                        logger.info(f"QR codes générés: {list(qr_codes.keys())}")

                    # Mise à jour du profil utilisateur
                    request.user.profile.club = club
                    request.user.profile.onboarding_step = 'completed'
                    request.user.profile.onboarding_completed = True
                    request.user.profile.save()

                    # Supprimer l'étape d'onboarding de la session
                    if 'onboarding_step' in request.session:
                        del request.session['onboarding_step']

                    messages.success(request, _("Votre club a été créé avec succès! Site web disponible."))

                    return redirect('competitions:dashboard:club')

            except Exception as e:
                logger.error(f"Erreur lors de la création du club: {str(e)}")
                messages.error(request, _("Une erreur est survenue lors de la création du club."))
```

### 3. Modification du Formulaire de Création

**Ajouter les champs de sous-domaine :**

```python
# Dans competitions/forms/onboarding.py
class ClubCreationForm(forms.ModelForm):
    """Formulaire pour la création d'un club avec sous-domaine."""

    # Champ pour personnaliser le sous-domaine
    custom_subdomain = forms.CharField(
        label=_("Sous-domaine personnalisé (optionnel)"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('mon-club'),
            'pattern': '^[a-z0-9-]+$'
        }),
        help_text=_("Laissez vide pour génération automatique. Seules les lettres minuscules, chiffres et tirets sont autorisés.")
    )

    class Meta:
        model = Club
        fields = ['name', 'address', 'city', 'logo', 'description', 'website', 'contact_email', 'contact_phone', 'custom_subdomain']
        # ... reste inchangé ...

    def clean_custom_subdomain(self):
        """Validation du sous-domaine personnalisé."""
        custom_subdomain = self.cleaned_data.get('custom_subdomain')

        if custom_subdomain:
            # Validation des caractères
            if not re.match(r'^[a-z0-9-]+$', custom_subdomain):
                raise forms.ValidationError(_("Le sous-domaine ne peut contenir que des lettres minuscules, chiffres et tirets."))

            # Vérifier la longueur
            if len(custom_subdomain) > 50:
                raise forms.ValidationError(_("Le sous-domaine ne peut pas dépasser 50 caractères."))

            # Vérifier qu'il ne commence/finit pas par un tiret
            if custom_subdomain.startswith('-') or custom_subdomain.endswith('-'):
                raise forms.ValidationError(_("Le sous-domaine ne peut pas commencer ou finir par un tiret."))

            # Vérifier l'unicité
            from competitions.utils.subdomain_generator import SubdomainGenerator
            generator = SubdomainGenerator()
            if generator._subdomain_exists(custom_subdomain):
                raise forms.ValidationError(_("Ce sous-domaine est déjà utilisé."))

        return custom_subdomain
```

### 4. Modification du Template

**Ajouter la section sous-domaine :**

```html
<!-- Dans competitions/templates/competitions/onboarding/club_creation.html -->
<div class="form-section animate-in">
  <div class="section-header">
    <i class="fas fa-globe"></i>
    <h3>{% trans "Site web du club" %}</h3>
  </div>
  <div class="section-body">
    <div class="form-group">
      <label for="{{ form.custom_subdomain.id_for_label }}" class="form-label">
        {{ form.custom_subdomain.label }}
      </label>
      {{ form.custom_subdomain }} {% if form.custom_subdomain.help_text %}
      <small class="form-text text-muted"
        >{{ form.custom_subdomain.help_text }}</small
      >
      {% endif %} {% if form.custom_subdomain.errors %}
      <div class="invalid-feedback">{{ form.custom_subdomain.errors }}</div>
      {% endif %}

      <!-- Prévisualisation du sous-domaine -->
      <div class="mt-2">
        <small class="text-muted">
          {% trans "Votre site sera accessible à :" %}
          <span id="subdomain-preview" class="text-primary fw-bold">
            https://<span id="subdomain-text">votre-club</span>.martialcomp.com
          </span>
        </small>
      </div>
    </div>
  </div>
</div>
```

**Ajouter le JavaScript pour la prévisualisation :**

```javascript
// Dans le bloc extra_js
document.addEventListener("DOMContentLoaded", function () {
  // Prévisualisation du sous-domaine
  const subdomainInput = document.getElementById(
    "{{ form.custom_subdomain.id_for_label }}"
  );
  const subdomainText = document.getElementById("subdomain-text");

  if (subdomainInput) {
    subdomainInput.addEventListener("input", function (e) {
      let value = e.target.value.toLowerCase();
      // Nettoyer les caractères non autorisés
      value = value.replace(/[^a-z0-9-]/g, "");
      // Éviter les tirets multiples
      value = value.replace(/-+/g, "-");
      // Enlever les tirets en début/fin
      value = value.replace(/^-+|-+$/g, "");

      subdomainText.textContent = value || "votre-club";
    });
  }
});
```

### 5. Signaux pour la Synchronisation

**Ajouter des signaux pour maintenir la cohérence :**

```python
# Dans competitions/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Club

@receiver(post_save, sender=Club)
def sync_club_organization(sender, instance, created, **kwargs):
    """Synchronise le club avec son organisation associée."""
    if created and instance.organization:
        try:
            # Mettre à jour l'organisation avec les données du club
            org = instance.organization
            org.name = instance.name
            org.description = instance.description or f"Club {instance.name}"
            org.email = instance.contact_email
            org.phone = instance.contact_phone
            org.website = instance.website
            org.address = instance.address
            org.city = instance.city
            org.postal_code = instance.postal_code
            org.logo = instance.logo
            org.save()

            logger.info(f"Organisation synchronisée pour le club: {instance.name}")

        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation club/organisation: {e}")
```

## Avantages de cette Intégration

### 1. Cohérence du Système

- Tous les clubs auront automatiquement un site web
- Utilisation du même système de sous-domaines que les organisations
- Gestion centralisée des tenants

### 2. Fonctionnalités Avancées

- QR codes automatiquement générés
- Templates de sites personnalisables
- Système multi-tenant complet

### 3. Expérience Utilisateur

- Création transparente du site web
- Prévisualisation en temps réel du sous-domaine
- Possibilité de personnalisation

### 4. Évolutivité

- Facilite l'ajout de fonctionnalités web
- Intégration avec le système de templates
- Support pour les fonctionnalités avancées (e-commerce, etc.)

## Plan de Déploiement

### Phase 1 : Préparation

1. Ajouter les champs nécessaires au modèle Club
2. Créer la migration de base de données
3. Tester la création d'organisations associées

### Phase 2 : Intégration

1. Modifier la vue de création de club
2. Ajouter les champs au formulaire
3. Mettre à jour le template

### Phase 3 : Tests et Validation

1. Tests de création de clubs avec sous-domaines
2. Validation des QR codes générés
3. Tests de personnalisation des sous-domaines

### Phase 4 : Déploiement

1. Déploiement en environnement de test
2. Migration des clubs existants (optionnel)
3. Déploiement en production

## Conclusion

Cette intégration permettra aux clubs d'avoir automatiquement leur propre site web avec sous-domaine, tout en maintenant la cohérence avec le système d'organisations existant. Cela enrichira considérablement l'expérience utilisateur et ouvrira la voie à de nombreuses fonctionnalités web avancées.
