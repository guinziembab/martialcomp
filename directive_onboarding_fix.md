# Directive Développeur : Correction du Processus d'Onboarding et QR Codes

## 🎯 **Objectif**

Corriger les dysfonctionnements du processus d'onboarding et implémenter un système de QR codes unifié pour améliorer l'expérience utilisateur des clubs et pratiquants.

## 🚨 **Problèmes Identifiés**

### **Problème 1 : Dashboard Incorrect**
- Les utilisateurs créés par un responsable de club héritent systématiquement du dashboard "practitioner" générique
- Ils n'accèdent pas au dashboard spécifique du club

### **Problème 2 : Manque de QR Code Club**
- Aucun moyen pour le responsable de générer un QR code permettant l'inscription autonome au club
- Les nouveaux pratiquants ne peuvent pas s'inscrire directement via QR code

### **Problème 3 : Manque d'Accès Direct**
- Les pratiquants créés n'ont pas de QR code personnel pour accès direct au dashboard du club
- Processus de connexion complexe et non optimisé

---

## 📋 **Spécifications Techniques**

### **1. Correction du Système d'Onboarding**

#### **1.1 Modifier le modèle UserProfile**

**Fichier : `competitions/models/users.py`**

```python
class UserProfile(models.Model):
    # ... champs existants ...
    
    # NOUVEAU : Champ pour tracker la création par responsable
    created_by_club_manager = models.BooleanField(
        _("Créé par un responsable de club"), 
        default=False
    )
    
    # NOUVEAU : Club de rattachement principal
    primary_club = models.ForeignKey(
        'competitions.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_members',
        verbose_name=_("Club principal")
    )
    
    def get_dashboard_redirect_url(self):
        """Détermine l'URL de redirection dashboard appropriée"""
        if self.primary_club and (self.role == 'participant' or self.created_by_club_manager):
            return reverse('competitions:club:dashboard', kwargs={'club_id': self.primary_club.id})
        elif self.role == 'club_manager' and self.club:
            return reverse('competitions:club:manager_dashboard', kwargs={'club_id': self.club.id})
        elif self.role == 'federation_admin':
            return reverse('competitions:federation:dashboard')
        else:
            return reverse('competitions:dashboard')
```

#### **1.2 Créer un Manager pour la Création d'Utilisateurs Club**

**Fichier : `competitions/managers/club_user_manager.py`** (NOUVEAU)

```python
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from ..models import UserProfile, Club
from ..utils.qr_generator import PersonalQRCodeGenerator

class ClubUserManager:
    """Manager pour la création d'utilisateurs par les responsables de club"""
    
    def create_club_member(self, club, user_data, created_by_user):
        """
        Crée un nouveau membre pour un club avec le contexte approprié
        
        Args:
            club: Instance du club
            user_data: Dict avec les données utilisateur (email, first_name, last_name, etc.)
            created_by_user: Utilisateur qui crée ce membre (responsable club)
            
        Returns:
            tuple: (user, profile, personal_qr_code)
        """
        # Générer un mot de passe temporaire
        temp_password = get_random_string(12)
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password=temp_password
        )
        
        # Créer le profil avec les bonnes associations
        profile = UserProfile.objects.create(
            user=user,
            role='participant',
            club=club,  # Club de rattachement
            primary_club=club,  # Club principal pour dashboard
            created_by_club_manager=True,
            onboarding_completed=True,  # Skip l'onboarding classique
            onboarding_step='completed'
        )
        
        # Générer le QR code personnel
        qr_generator = PersonalQRCodeGenerator()
        personal_qr = qr_generator.generate_club_member_qr(user, club)
        
        # Envoyer email de bienvenue avec informations de connexion
        self._send_welcome_email(user, club, temp_password, personal_qr)
        
        return user, profile, personal_qr
    
    def _send_welcome_email(self, user, club, temp_password, qr_code_path):
        """Envoie l'email de bienvenue avec QR code personnel"""
        context = {
            'user': user,
            'club': club,
            'temp_password': temp_password,
            'club_url': f"https://{club.get_subdomain()}.martialcomp.com",
            'qr_code_path': qr_code_path
        }
        
        subject = f"Bienvenue au {club.name} - Votre accès personnel"
        message = render_to_string('emails/club_member_welcome.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@martialcomp.com',
            recipient_list=[user.email],
            html_message=message
        )
```

### **2. Système de QR Codes Amélioré**

#### **2.1 Générateur de QR Codes Personnels**

**Fichier : `competitions/utils/qr_generator.py`** (AMÉLIORER)

```python
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from ..models import PersonalAccessToken

class PersonalQRCodeGenerator:
    """Générateur de QR codes personnels pour les membres de club"""
    
    def generate_club_member_qr(self, user, club):
        """Génère un QR code personnel pour accès direct au dashboard club"""
        
        # Créer un token d'accès personnel sécurisé
        access_token = self._create_personal_access_token(user, club)
        
        # URL d'accès direct
        access_url = f"https://{club.get_subdomain()}.martialcomp.com/access/{access_token.token}"
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(access_url)
        qr.make(fit=True)
        
        # Créer l'image avec logo du club si disponible
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder et retourner le chemin
        filename = f"qr_personal_{user.id}_{club.id}.png"
        filepath = f"media/qr_codes/personal/{filename}"
        
        with open(filepath, 'wb') as f:
            img.save(f, 'PNG')
            
        return filepath
    
    def generate_club_registration_qr(self, club):
        """Génère un QR code pour inscription au club"""
        
        # URL d'inscription avec paramètres club
        registration_url = f"https://{club.get_subdomain()}.martialcomp.com/inscription"
        params = f"?source=qr_club&club_id={club.id}&auto_club=true"
        full_url = registration_url + params
        
        # Générer QR code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(full_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder
        filename = f"qr_registration_{club.id}.png"
        filepath = f"media/qr_codes/clubs/{filename}"
        
        with open(filepath, 'wb') as f:
            img.save(f, 'PNG')
            
        return filepath
    
    def _create_personal_access_token(self, user, club):
        """Crée un token d'accès personnel sécurisé"""
        token = get_random_string(32)
        
        access_token = PersonalAccessToken.objects.create(
            user=user,
            club=club,
            token=token,
            is_active=True
        )
        
        return access_token

# NOUVEAU MODÈLE pour les tokens d'accès
class PersonalAccessToken(models.Model):
    """Tokens d'accès personnel pour QR codes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    club = models.ForeignKey('competitions.Club', on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'club']
```

### **3. Vues et URLs**

#### **3.1 Vue pour Accès via QR Personnel**

**Fichier : `competitions/views/qr_access.py`** (NOUVEAU)

```python
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from ..models import PersonalAccessToken

@csrf_exempt
def personal_qr_access(request, token):
    """Vue pour l'accès via QR code personnel"""
    
    try:
        # Récupérer le token d'accès
        access_token = get_object_or_404(
            PersonalAccessToken, 
            token=token, 
            is_active=True
        )
        
        # Vérifier la validité (optionnel : expiration)
        if access_token.created_at < timezone.now() - timezone.timedelta(days=365):
            messages.error(request, "Ce QR code a expiré. Contactez votre club.")
            return redirect('home')
        
        # Connecter l'utilisateur automatiquement
        login(request, access_token.user)
        
        # Mettre à jour last_used
        access_token.last_used = timezone.now()
        access_token.save()
        
        # Rediriger vers le dashboard du club
        club_dashboard_url = reverse('competitions:club:dashboard', 
                                   kwargs={'club_id': access_token.club.id})
        
        messages.success(request, f"Bienvenue dans l'espace {access_token.club.name} !")
        return redirect(club_dashboard_url)
        
    except Exception as e:
        messages.error(request, "QR code invalide ou expiré.")
        return redirect('home')

def club_registration_qr(request):
    """Vue pour inscription via QR code club"""
    
    club_id = request.GET.get('club_id')
    source = request.GET.get('source')
    auto_club = request.GET.get('auto_club') == 'true'
    
    if club_id and auto_club:
        # Pré-remplir le formulaire avec les infos du club
        club = get_object_or_404(Club, id=club_id)
        
        # Stocker en session pour pré-remplissage
        request.session['preselected_club'] = club.id
        request.session['registration_source'] = source
        
    return redirect('onboarding:register')
```

#### **3.2 URLs**

**Fichier : `competitions/urls.py`** (AJOUTER)

```python
# Ajouter ces patterns
urlpatterns = [
    # ... patterns existants ...
    
    # QR Code Access
    path('access/<str:token>/', views.personal_qr_access, name='personal_qr_access'),
    path('inscription/', views.club_registration_qr, name='club_registration_qr'),
]
```

### **4. Interface Responsable de Club**

#### **4.1 Vue Dashboard Club avec QR Codes**

**Fichier : `competitions/views/club_dashboard.py`** (MODIFIER)

```python
from ..managers.club_user_manager import ClubUserManager
from ..utils.qr_generator import PersonalQRCodeGenerator

@login_required
def club_dashboard(request, club_id):
    """Dashboard du club avec gestion QR codes"""
    
    club = get_object_or_404(Club, id=club_id)
    
    # Vérifier les permissions
    if not request.user.profile.can_manage_club(club):
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    # Générer/récupérer QR code d'inscription du club
    qr_generator = PersonalQRCodeGenerator()
    club_registration_qr = qr_generator.generate_club_registration_qr(club)
    
    # Récupérer les membres avec leurs QR codes
    club_members = User.objects.filter(
        profile__primary_club=club,
        profile__role='participant'
    ).select_related('profile')
    
    # Formulaire d'ajout de membre
    if request.method == 'POST' and 'add_member' in request.POST:
        user_data = {
            'email': request.POST.get('email'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
        }
        
        try:
            club_manager = ClubUserManager()
            user, profile, qr_code = club_manager.create_club_member(
                club=club,
                user_data=user_data,
                created_by_user=request.user
            )
            
            messages.success(request, f"Membre {user.get_full_name()} ajouté avec succès!")
            return redirect('competitions:club:dashboard', club_id=club.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du membre: {str(e)}")
    
    context = {
        'club': club,
        'club_registration_qr': club_registration_qr,
        'club_members': club_members,
        'can_add_members': True,
    }
    
    return render(request, 'clubs/dashboard.html', context)
```

### **5. Templates**

#### **5.1 Template Dashboard Club**

**Fichier : `competitions/templates/clubs/dashboard.html`** (MODIFIER)

```html
{% extends "base.html" %}
{% load i18n %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1><i class="fas fa-home me-2"></i>{{ club.name }}</h1>
            <p class="text-muted">{{ club.description }}</p>
        </div>
    </div>
    
    <!-- QR Codes Section -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-qrcode me-2"></i>QR Code d'Inscription</h5>
                </div>
                <div class="card-body text-center">
                    <img src="{{ club_registration_qr }}" alt="QR Code Inscription" class="img-fluid mb-3" style="max-width: 200px;">
                    <p class="text-muted">Partagez ce QR code pour permettre l'inscription directe au club</p>
                    <a href="{{ club_registration_qr }}" download class="btn btn-primary">
                        <i class="fas fa-download me-2"></i>Télécharger
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-user-plus me-2"></i>Ajouter un Membre</h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control" id="email" name="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="first_name" class="form-label">Prénom</label>
                            <input type="text" class="form-control" id="first_name" name="first_name" required>
                        </div>
                        <div class="mb-3">
                            <label for="last_name" class="form-label">Nom</label>
                            <input type="text" class="form-control" id="last_name" name="last_name" required>
                        </div>
                        <button type="submit" name="add_member" class="btn btn-success">
                            <i class="fas fa-plus me-2"></i>Ajouter
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Membres Section -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-users me-2"></i>Membres du Club</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Email</th>
                                    <th>Date d'inscription</th>
                                    <th>QR Personnel</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for member in club_members %}
                                <tr>
                                    <td>{{ member.get_full_name }}</td>
                                    <td>{{ member.email }}</td>
                                    <td>{{ member.date_joined|date:"d/m/Y" }}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary" onclick="showMemberQR({{ member.id }})">
                                            <i class="fas fa-qrcode"></i>
                                        </button>
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-info">
                                            <i class="fas fa-eye"></i>
                                        </button>
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
</div>

<!-- Modal QR Personnel -->
<div class="modal fade" id="memberQRModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">QR Code Personnel</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
                <div id="qr-content">
                    <!-- QR code sera chargé ici -->
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function showMemberQR(memberId) {
    // Charger le QR code du membre
    fetch(`/api/member/${memberId}/qr/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('qr-content').innerHTML = `
                <img src="${data.qr_url}" alt="QR Personnel" class="img-fluid mb-3">
                <p class="text-muted">${data.member_name}</p>
                <a href="${data.qr_url}" download class="btn btn-primary">
                    <i class="fas fa-download me-2"></i>Télécharger
                </a>
            `;
            new bootstrap.Modal(document.getElementById('memberQRModal')).show();
        });
}
</script>
{% endblock %}
```

---

## ✅ **Tests à Effectuer**

### **Test 1 : Création de Membre par Responsable**
```python
def test_club_manager_creates_member():
    # Créer un club et un responsable
    club = Club.objects.create(name="Test Club")
    manager = User.objects.create_user("manager@test.com")
    manager.profile.role = 'club_manager'
    manager.profile.club = club
    manager.profile.save()
    
    # Créer un membre
    club_manager = ClubUserManager()
    user, profile, qr = club_manager.create_club_member(
        club=club,
        user_data={
            'email': 'member@test.com',
            'first_name': 'John',
            'last_name': 'Doe'
        },
        created_by_user=manager
    )
    
    # Vérifications
    assert profile.role == 'participant'
    assert profile.primary_club == club
    assert profile.created_by_club_manager == True
    assert profile.onboarding_completed == True
    assert qr is not None
```

### **Test 2 : Accès via QR Personnel**
```python
def test_personal_qr_access():
    # Créer token d'accès
    user = User.objects.create_user("test@test.com")
    club = Club.objects.create(name="Test Club")
    token = PersonalAccessToken.objects.create(
        user=user, club=club, token="test123"
    )
    
    # Tester l'accès
    response = client.get(f'/access/test123/')
    assert response.status_code == 302  # Redirection
    assert 'club/dashboard' in response.url
```

### **Test 3 : Redirection Dashboard**
```python
def test_dashboard_redirect():
    user = User.objects.create_user("test@test.com")
    club = Club.objects.create(name="Test Club")
    user.profile.primary_club = club
    user.profile.role = 'participant'
    user.profile.save()
    
    url = user.profile.get_dashboard_redirect_url()
    assert 'club/dashboard' in url
    assert str(club.id) in url
```

---

## 📋 **Critères d'Acceptation**

### ✅ **Fonctionnalités Obligatoires**

1. **Création Membre** : Un responsable peut créer un membre qui accède directement au dashboard du club
2. **QR Club** : Génération automatique d'un QR code d'inscription pour le club
3. **QR Personnel** : Chaque membre a un QR code personnel pour accès direct
4. **Redirection Intelligente** : Les utilisateurs sont redirigés vers le bon dashboard selon leur contexte
5. **Sécurité** : Les tokens d'accès sont sécurisés et peuvent être révoqués

### ✅ **Tests de Non-Régression**

- L'onboarding classique continue de fonctionner
- Les autres rôles (federation_admin, judge, etc.) ne sont pas impactés
- La compatibilité avec le système multi-tenant est maintenue

---

## 🚀 **Déploiement**

### **Phase 1 : Backend** (2-3 jours)
1. Implémenter les modèles et managers
2. Créer les vues et URLs
3. Tests unitaires

### **Phase 2 : Frontend** (1-2 jours)
1. Templates dashboard club
2. Interface QR codes
3. Tests d'intégration

### **Phase 3 : Production** (1 jour)
1. Migration base de données
2. Génération QR codes existants
3. Tests utilisateur

---

## 📞 **Support**

Pour toute question technique concernant cette directive :
- Consulter la documentation existante du projet
- Tester en local avant déploiement
- Documenter les changements apportés

**Priorité : HAUTE** - Cette correction améliore significativement l'expérience utilisateur et résout des problèmes critiques d'onboarding.