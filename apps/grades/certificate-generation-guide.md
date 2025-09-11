# Guide d'implémentation de la génération de certificats et diplômes

Ce guide explique comment implémenter le système de génération de certificats et diplômes élégants pour MartialComp.

## Vue d'ensemble

Le système de génération de certificats permet de :

1. Créer des certificats et diplômes PDF élégants et personnalisables
2. Générer des numéros de certificat uniques basés sur la discipline, l'organisation et la date de naissance
3. Vérifier l'authenticité des certificats via QR code
4. Générer des certificats en masse pour plusieurs pratiquants

## Composants du système

Le système est composé de plusieurs modules :

1. **Module PDF (ReportLab)** : Génère les documents PDF avec des designs élégants
2. **Service de génération de numéros de certificat** : Crée des numéros uniques et traçables
3. **Vues Django** : Interface utilisateur pour la génération et la gestion des certificats
4. **Système de vérification** : Vérifie l'authenticité des certificats via QR code

## Installation et prérequis

### 1. Installer les dépendances

```bash
pip install reportlab qrcode pillow weasyprint
```

### 2. Structure des fichiers

```
grades/
├── utils/
│   ├── __init__.py
│   └── pdf.py          # Module de génération PDF
├── services/
│   ├── __init__.py
│   └── certificate.py  # Service de génération de numéros
├── views/
│   ├── __init__.py
│   └── certificates.py # Vues pour les certificats
├── templates/
│   └── grades/
│       ├── certificate_generator.html
│       ├── bulk_certificate_generator.html
│       └── verify_certificate.html
├── urls.py
└── models.py
```

### 3. Ressources statiques nécessaires

Créer les dossiers suivants :

```
static/
├── fonts/
│   ├── Montserrat-Regular.ttf
│   ├── Montserrat-Bold.ttf
│   ├── Montserrat-Italic.ttf
│   ├── NotoSans-Regular.ttf
│   └── NotoSans-Bold.ttf
└── images/
    └── certificate/
        ├── corner_decoration.png
        ├── background.jpg
        ├── template_standard.jpg
        ├── template_gold.jpg
        ├── template_silver.jpg
        ├── certificate.jpg
        └── diploma.jpg
```

## Étapes d'implémentation

### 1. Mettre à jour le modèle PractitionerGrade

Assurez-vous que votre modèle `PractitionerGrade` contient les champs suivants :

```python
# grades/models.py
class PractitionerGrade(models.Model):
    # Champs existants...
    
    # Ajoutez ces champs s'ils n'existent pas déjà
    certificate_number = models.CharField(_("Numéro de certificat"), max_length=50, blank=True)
    certificate_file = models.FileField(_("Certificat"), upload_to='grades/certificates/', null=True, blank=True)
    date_obtained = models.DateField(_("Date d'obtention"), default=timezone.now)
    date_expiry = models.DateField(_("Date d'expiration"), null=True, blank=True)
    awarded_by = models.CharField(_("Décerné par"), max_length=100, blank=True)
    location = models.CharField(_("Lieu d'obtention"), max_length=100, blank=True)
```

### 2. Copier les fichiers du module

1. Copier le contenu de `certificate-generator-utility.py` dans `grades/utils/pdf.py`
2. Copier le contenu de `certificate-number-generator-service.py` dans `grades/services/certificate.py`
3. Copier le contenu de `certificate-generator-view.py` dans `grades/views/certificates.py`

### 3. Ajouter les templates HTML

1. Copier `certificate-generator-template.html` dans `grades/templates/grades/certificate_generator.html`
2. Copier `bulk-certificate-generator-template.html` dans `grades/templates/grades/bulk_certificate_generator.html`
3. Copier `certificate-verification-template.html` dans `grades/templates/grades/verify_certificate.html`

### 4. Configurer les URLs

Ajouter les routes suivantes dans `grades/urls.py` :

```python
from django.urls import path
from grades.views import certificates

urlpatterns = [
    # Autres URLs...
    
    # URLs pour les certificats
    path('certificate/generate/<int:grade_id>/', certificates.certificate_generator, name='certificate_generator'),
    path('certificate/bulk/', certificates.bulk_certificate_generator, name='bulk_certificate_generator'),
    path('certificate/verify/<str:certificate_number>/', certificates.verify_certificate, name='verify_certificate'),
    path('certificate/qr/<str:certificate_number>/', certificates.generate_verification_qr, name='verification_qr'),
    path('certificate/download/<int:grade_id>/', certificates.download_certificate, name='download_certificate'),
    path('api/generate-certificate-number/', certificates.generate_certificate_number_ajax, name='generate_certificate_number_ajax'),
]
```

### 5. Ajouter une fonction pour générer des QR codes

Ajouter cette fonction dans `grades/views/certificates.py` :

```python
def generate_verification_qr(request, certificate_number):
    """
    Génère un QR code pour la vérification du certificat.
    """
    import qrcode
    from django.http import HttpResponse
    from io import BytesIO
    
    verification_url = f"{request.scheme}://{request.get_host()}/grades/certificate/verify/{certificate_number}/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    response = HttpResponse(content_type="image/png")
    img_io = BytesIO()
    img.save(img_io)
    img_io.seek(0)
    response.write(img_io.read())
    
    return response
```

### 6. Ajouter une fonction pour télécharger un certificat existant

Ajouter cette fonction dans `grades/views/certificates.py` :

```python
@login_required
def download_certificate(request, grade_id):
    """
    Télécharge un certificat existant ou en génère un nouveau.
    """
    grade_record = get_object_or_404(PractitionerGrade, id=grade_id)
    
    # Vérifier les permissions
    if not request.user.is_staff:
        club = get_user_club(request)
        if not club or grade_record.practitioner.club != club:
            messages.error(request, _("Vous n'avez pas accès à ce certificat."))
            return redirect('dashboard:index')
    
    # Si le certificat est déjà stocké, le servir
    if grade_record.certificate_file and os.path.exists(grade_record.certificate_file.path):
        response = HttpResponse(grade_record.certificate_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat_{grade_record.practitioner.last_name}_{grade_record.grade.name}.pdf"'
        return response
    
    # Sinon, générer un nouveau certificat
    return generate_grade_certificate(
        practitioner=grade_record.practitioner,
        grade_info=grade_record,
        organization=grade_record.practitioner.club,
    )
```

## Personnalisation

### Styles visuels des certificats

Vous pouvez personnaliser l'apparence des certificats en modifiant les fonctions dans `grades/utils/pdf.py` :

- `draw_certificate_background()` : Arrière-plan et bordures
- `get_certificate_styles()` : Styles de texte

### Numérotation des certificats

Vous pouvez personnaliser la génération des numéros de certificat en modifiant les fonctions dans `grades/services/certificate.py` :

- `_get_discipline_code()` : Code de la discipline
- `_get_organization_code()` : Code de l'organisation
- `_get_birth_date_code()` : Format de la date de naissance

## Utilisation

### Génération d'un certificat individuel

1. Accéder à la page de détail d'un pratiquant
2. Cliquer sur le grade pour lequel générer un certificat
3. Cliquer sur "Générer un certificat"
4. Personnaliser le certificat selon les besoins
5. Cliquer sur "Générer le PDF"

### Génération en masse

1. Accéder à "Génération de certificats en masse"
2. Sélectionner les pratiquants concernés
3. Configurer les certificats
4. Cliquer sur "Générer les certificats"

### Vérification d'un certificat

1. Scanner le QR code présent sur le certificat
2. Visualiser les informations de vérification
3. Télécharger le certificat si nécessaire

## Fonctionnalités avancées

- **Stockage des certificats** : Enregistrez les PDF générés dans le système de fichiers pour éviter de les régénérer
- **Signatures numériques** : Ajoutez des images de signatures pour les responsables techniques
- **Envoi par email** : Intégrez une fonction d'envoi des certificats par email aux pratiquants
- **Modèles personnalisés par fédération** : Permettez à chaque fédération d'avoir ses propres modèles de certificats

## Dépannage

### Problèmes courants

1. **Erreurs de police** : Assurez-vous que les polices sont correctement installées dans le dossier `static/fonts/`
2. **QR codes non générés** : Vérifiez que la bibliothèque `qrcode` est bien installée
3. **Images manquantes** : Vérifiez les chemins des images dans le dossier `static/images/certificate/`

### Support multilingue

Le système utilise `gettext` pour la traduction. Assurez-vous que les chaînes de caractères sont correctement marquées avec `_()` pour permettre la traduction.

## Conclusion

Ce système de génération de certificats et diplômes offre une solution complète et élégante pour valoriser les grades de vos pratiquants. Il est conçu pour être facilement intégré dans votre application MartialComp existante et peut être personnalisé selon vos besoins spécifiques.
