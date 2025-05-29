#!/bin/bash

# ============================================================================
# SCRIPT DE DÉPLOIEMENT COMPLET MARTIALCOMP - DIGITALOCEAN
# ============================================================================
# Droplet: martialcomp-prod (165.232.94.248)
# Database: Cluster DigitalOcean
# Usage: export DB_PASSWORD="AVNS_CVAFerporCOA7pDH9h0" && ./deploy_complete_martialcomp.sh
# ============================================================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🥋 DÉPLOIEMENT COMPLET MARTIALCOMP - DIGITALOCEAN"
echo "================================================"
echo "Serveur : martialcomp-prod (165.232.94.248)"
echo "Date    : $(date)"
echo "Utilisateur : $(whoami)"
echo "================================================"

# ================================
# VÉRIFICATION DES PRÉREQUIS
# ================================

log_info "Vérification des prérequis..."

# Vérifier qu'on est root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root"
    log_info "Utilisez: sudo ./deploy_complete_martialcomp.sh"
    exit 1
fi

# Vérifier les variables d'environnement
if [ -z "$DB_PASSWORD" ]; then
    log_error "Variable DB_PASSWORD manquante"
    echo ""
    echo "Usage:"
    echo "  export DB_PASSWORD='AVNS_CVAFerporCOA7pDH9h0'"
    echo "  ./deploy_complete_martialcomp.sh"
    echo ""
    exit 1
fi

# Variables par défaut avec vos informations DigitalOcean
export DB_HOST="${DB_HOST:-martialcomp-do-user-22855185-0.f.db.ondigitalocean.com}"
export DB_PORT="${DB_PORT:-25060}"
export DB_NAME="${DB_NAME:-defaultdb}"
export DB_USER="${DB_USER:-doadmin}"
export DOMAIN="${DOMAIN:-martialcomp.com}"
export SERVER_IP="${SERVER_IP:-165.232.94.248}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-bertrand.guinziemba@gmail.com}"

# Générer SECRET_KEY si non définie
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || echo "django-insecure-$(openssl rand -hex 25)")
fi

log_success "Prérequis validés"
log_info "DB_HOST: $DB_HOST"
log_info "DB_PORT: $DB_PORT"
log_info "DB_NAME: $DB_NAME"
log_info "DB_USER: $DB_USER"
log_info "DOMAIN: $DOMAIN"

# ================================
# TEST DE CONNEXION BASE DE DONNÉES
# ================================

log_info "Test de connexion à la base de données DigitalOcean..."

# Installer psql si nécessaire
if ! command -v psql &> /dev/null; then
    log_info "Installation de postgresql-client..."
    apt update -qq
    apt install -y postgresql-client
fi

# Test de connexion
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" >/dev/null 2>&1; then
    log_success "Connexion à la base DigitalOcean réussie"
else
    log_error "Impossible de se connecter à la base DigitalOcean"
    log_info "Vérifiez les paramètres de connexion dans votre dashboard DigitalOcean"
    exit 1
fi

# ================================
# INSTALLATION DES DÉPENDANCES SYSTÈME
# ================================

log_info "Installation des dépendances système..."

# Mise à jour système
apt update && apt upgrade -y

# Installation des paquets essentiels
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    nginx \
    supervisor \
    redis-server \
    postgresql-client \
    curl \
    wget \
    git \
    ufw \
    htop \
    nano \
    certbot \
    python3-certbot-nginx

log_success "Dépendances système installées"

# ================================
# CONFIGURATION SÉCURITÉ
# ================================

log_info "Configuration de la sécurité..."

# Firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

log_success "Firewall configuré"

# ================================
# CRÉATION UTILISATEUR DEPLOY
# ================================

log_info "Configuration de l'utilisateur deploy..."

# Créer l'utilisateur deploy
if ! id "deploy" &>/dev/null; then
    useradd -m -s /bin/bash deploy
    log_success "Utilisateur deploy créé"
else
    log_info "Utilisateur deploy existe déjà"
fi

# Créer la structure des répertoires
mkdir -p /home/deploy/{logs,backups,static,media}
chown -R deploy:deploy /home/deploy/

# Copier les clés SSH si elles existent
if [ -d ~/.ssh ]; then
    mkdir -p /home/deploy/.ssh
    cp ~/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys 2>/dev/null || true
fi

log_success "Utilisateur deploy configuré"

# ================================
# CRÉATION DE L'APPLICATION DJANGO
# ================================

log_info "Création de l'application Django MartialComp..."

# Nettoyer et créer le répertoire du projet
rm -rf /home/deploy/martialcomp
mkdir -p /home/deploy/martialcomp
cd /home/deploy/martialcomp

# Créer la structure des répertoires
mkdir -p {config,competitions,shop/{models,management/commands},static,media,templates}

# ================================
# manage.py
# ================================

cat > manage.py << 'EOF'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
EOF

chmod +x manage.py

# ================================
# requirements.txt
# ================================

cat > requirements.txt << 'EOF'
# Core Django
django>=5.1.4
django-extensions

# Database
psycopg2-binary

# Production server
gunicorn

# Cache
django-redis
redis

# Images
Pillow

# Forms
django-widget-tweaks

# Utils
python-dateutil
pytz
EOF

# ================================
# Configuration Django
# ================================

# config/__init__.py
mkdir -p config
touch config/__init__.py

# config/settings.py
cat > config/settings.py << 'EOF'
"""
Django settings for MartialComp project.
"""
from pathlib import Path
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'competitions',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'defaultdb'),
        'USER': os.environ.get('DB_USER', 'doadmin'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '25060'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 20,
        },
        'CONN_MAX_AGE': 600,
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/home/deploy/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/deploy/media/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin
ADMIN_URL = 'admin/'
EOF

# config/urls.py
cat > config/urls.py << 'EOF'
"""
URL configuration for MartialComp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home(request):
    return HttpResponse("""
    <html>
    <head><title>MartialComp</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin: 50px;">
        <h1>🥋 Bienvenue sur MartialComp!</h1>
        <p>Plateforme de gestion des arts martiaux</p>
        <p><a href="/admin/" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Interface d'Administration</a></p>
        <p><a href="/health/" style="color: #666;">Health Check</a></p>
        <hr style="margin: 30px 0;">
        <small>Version de développement - DigitalOcean</small>
    </body>
    </html>
    """)

def health(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('health/', health, name='health'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOF

# config/wsgi.py
cat > config/wsgi.py << 'EOF'
"""
WSGI config for MartialComp project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
EOF

# ================================
# Application Competitions
# ================================

# competitions/__init__.py
touch competitions/__init__.py

# competitions/apps.py
cat > competitions/apps.py << 'EOF'
from django.apps import AppConfig

class CompetitionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'competitions'
EOF

# competitions/models.py
cat > competitions/models.py << 'EOF'
from django.db import models
from django.contrib.auth.models import User

class Club(models.Model):
    name = models.CharField("Nom du club", max_length=200)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    address = models.TextField("Adresse", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubs"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Discipline(models.Model):
    name = models.CharField("Nom de la discipline", max_length=100)
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Discipline"
        verbose_name_plural = "Disciplines"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Practitioner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='practitioners')
    disciplines = models.ManyToManyField(Discipline, blank=True)
    birth_date = models.DateField("Date de naissance", null=True, blank=True)
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    emergency_contact = models.CharField("Contact d'urgence", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pratiquant"
        verbose_name_plural = "Pratiquants"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.club.name}"
EOF

# competitions/admin.py
cat > competitions/admin.py << 'EOF'
from django.contrib import admin
from .models import Club, Discipline, Practitioner

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ['user', 'club', 'birth_date', 'created_at']
    list_filter = ['club', 'disciplines', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'club__name']
    filter_horizontal = ['disciplines']
    readonly_fields = ['created_at', 'updated_at']
EOF

# ================================
# Application Shop
# ================================

# shop/__init__.py
touch shop/__init__.py

# shop/apps.py
cat > shop/apps.py << 'EOF'
from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
EOF

# shop/models/__init__.py
mkdir -p shop/models
cat > shop/models/__init__.py << 'EOF'
from .category import Category
EOF

# shop/models/category.py
cat > shop/models/category.py << 'EOF'
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True)
    description = models.TextField("Description", blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="Catégorie parente"
    )
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Retourne le chemin complet de la catégorie."""
        parts = [self.name]
        parent = self.parent
        while parent:
            parts.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(parts)
EOF

# shop/admin.py
cat > shop/admin.py << 'EOF'
from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
EOF

# ================================
# Commande de création des catégories
# ================================

# shop/management/__init__.py
mkdir -p shop/management/commands
touch shop/management/__init__.py
touch shop/management/commands/__init__.py

# shop/management/commands/create_martial_arts_categories.py
cat > shop/management/commands/create_martial_arts_categories.py << 'EOF'
from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Créer les catégories d\'arts martiaux pour la boutique'

    def handle(self, *args, **options):
        self.stdout.write("🥋 Création des catégories d'arts martiaux...")
        
        categories_data = [
            {
                'name': 'Tenues & Kimonos',
                'description': 'Tenues traditionnelles et modernes pour tous les arts martiaux',
                'order': 1,
                'children': [
                    'Kimonos Karaté',
                    'Kimonos Judo', 
                    'Kimonos Jiu-Jitsu',
                    'Tenues Taekwondo',
                    'Tenues Kung-Fu',
                    'Tenues Arts Martiaux Mixtes'
                ]
            },
            {
                'name': 'Grades & Ceintures',
                'description': 'Ceintures et systèmes de grades pour tous les arts martiaux',
                'order': 2,
                'children': [
                    'Ceintures de Karaté',
                    'Ceintures de Judo',
                    'Ceintures de Taekwondo',
                    'Ceintures de Jiu-Jitsu',
                    'Accessoires de Grade'
                ]
            },
            {
                'name': 'Protections & Sécurité',
                'description': 'Équipements de protection pour l\'entraînement et la compétition',
                'order': 3,
                'children': [
                    'Protège-Tibias',
                    'Gants de Combat',
                    'Casques de Protection',
                    'Protections Corporelles',
                    'Protège-Dents'
                ]
            },
            {
                'name': 'Matériel d\'Entraînement',
                'description': 'Équipements pour l\'entraînement technique et physique',
                'order': 4,
                'children': [
                    'Sacs de Frappe',
                    'Pattes d\'Ours',
                    'Makiwaras',
                    'Mannequins d\'Entraînement',
                    'Accessoires de Forme'
                ]
            },
            {
                'name': 'Équipement Dojo/Club',
                'description': 'Matériel pour l\'équipement des dojos et clubs',
                'order': 5,
                'children': [
                    'Tatamis',
                    'Miroirs de Dojo',
                    'Matériel de Rangement',
                    'Signalétique'
                ]
            }
        ]
        
        with transaction.atomic():
            for cat_data in categories_data:
                # Créer la catégorie principale
                main_category, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={
                        'slug': slugify(cat_data['name']),
                        'description': cat_data['description'],
                        'order': cat_data['order'],
                    }
                )
                
                if created:
                    self.stdout.write(f"✅ {main_category.name}")
                
                # Créer les sous-catégories
                for i, child_name in enumerate(cat_data['children'], 1):
                    child_category, created = Category.objects.get_or_create(
                        name=child_name,
                        defaults={
                            'slug': slugify(child_name),
                            'parent': main_category,
                            'order': i,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"  ↳ {child_category.name}")
        
        total_categories = Category.objects.count()
        main_categories = Category.objects.filter(parent=None).count()
        sub_categories = Category.objects.filter(parent__isnull=False).count()
        
        self.stdout.write("")
        self.stdout.write("🎉 Catégories créées avec succès!")
        self.stdout.write(f"📊 {main_categories} catégories principales")
        self.stdout.write(f"📋 {sub_categories} sous-catégories")
        self.stdout.write(f"🔢 {total_categories} catégories au total")
EOF

log_success "Application Django créée"

# ================================
# ENVIRONNEMENT PYTHON
# ================================

log_info "Configuration de l'environnement Python..."

# Créer l'environnement virtuel
sudo -u deploy python3 -m venv /home/deploy/venv

# Activer et installer les dépendances
sudo -u deploy /home/deploy/venv/bin/pip install --upgrade pip
sudo -u deploy /home/deploy/venv/bin/pip install -r requirements.txt

log_success "Environnement Python configuré"

# ================================
# CONFIGURATION DJANGO
# ================================

log_info "Configuration de Django..."

# Créer le fichier d'environnement
cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF

# Changer les permissions
chown -R deploy:deploy /home/deploy/martialcomp

# Configuration Django
sudo -u deploy bash -c "
cd /home/deploy/martialcomp
source /home/deploy/venv/bin/activate
export \$(grep -v '^#' .env | xargs)

# Migrations
python manage.py makemigrations competitions
python manage.py makemigrations shop
python manage.py migrate

# Superuser
echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', '$ADMIN_EMAIL', 'MartialComp2024!') if not User.objects.filter(username='admin').exists() else None\" | python manage.py shell

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Créer les catégories
python manage.py create_martial_arts_categories

# Créer quelques disciplines de base
echo \"
from competitions.models import Discipline
disciplines = ['Karaté', 'Judo', 'Taekwondo', 'Jiu-Jitsu Brésilien', 'Kung-Fu', 'MMA']
for name in disciplines:
    Discipline.objects.get_or_create(name=name)
print('Disciplines créées')
\" | python manage.py shell
"

log_success "Django configuré"

# ================================
# CONFIGURATION REDIS
# ================================

log_info "Configuration de Redis..."

systemctl start redis-server
systemctl enable redis-server

log_success "Redis configuré"

# ================================
# CONFIGURATION GUNICORN + SUPERVISOR
# ================================

log_info "Configuration de Gunicorn avec Supervisor..."

# Configuration Supervisor
cat > /etc/supervisor/conf.d/martialcomp.conf << EOF
[program:martialcomp]
command=/home/deploy/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 30 config.wsgi:application
directory=/home/deploy/martialcomp
user=deploy
group=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/deploy/logs/gunicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=SECRET_KEY="$SECRET_KEY",DB_HOST="$DB_HOST",DB_PORT="$DB_PORT",DB_NAME="$DB_NAME",DB_USER="$DB_USER",DB_PASSWORD="$DB_PASSWORD"
EOF

# Redémarrer Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start martialcomp

log_success "Gunicorn configuré"

# ================================
# CONFIGURATION NGINX
# ================================

log_info "Configuration de Nginx..."

# Configuration Nginx
cat > /etc/nginx/sites-available/martialcomp << EOF
# Configuration Nginx pour MartialComp

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $SERVER_IP;
    
    client_max_body_size 50M;
    
    # Logs
    access_log /var/log/nginx/martialcomp_access.log;
    error_log /var/log/nginx/martialcomp_error.log;
    
    # Fichiers statiques
    location /static/ {
        alias /home/deploy/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias /home/deploy/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
    
    # Application Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Activer la configuration
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/martialcomp /etc/nginx/sites-enabled/

# Test et redémarrage Nginx
nginx -t
systemctl restart nginx

log_success "Nginx configuré"

# ================================
# TESTS FINAUX
# ================================

log_info "Tests de fonctionnement..."

# Attendre que les services démarrent
sleep 10

# Test local
if curl -f -s http://localhost:8000/health/ >/dev/null 2>&1; then
    log_success "Application accessible localement"
else
    log_warning "Application non accessible localement"
fi

# Test via IP publique
if curl -f -s http://$SERVER_IP/health/ >/dev/null 2>&1; then
    log_success "Application accessible via IP publique"
else
    log_warning "Application non accessible via IP publique"
fi

# Status des services
log_info "Status des services:"
systemctl is-active nginx && log_success "Nginx: actif" || log_warning "Nginx: problème"
systemctl is-active redis-server && log_success "Redis: actif" || log_warning "Redis: problème"
supervisorctl status martialcomp | grep RUNNING && log_success "Gunicorn: actif" || log_warning "Gunicorn: problème"

# ================================
# RAPPORT FINAL
# ================================

echo ""
echo "=============================================="
echo "🎉 DÉPLOIEMENT MARTIALCOMP TERMINÉ !"
echo "=============================================="
echo ""
echo "📋 Informations de connexion :"
echo "  🌐 Site web        : http://$SERVER_IP"
echo "  🌐 Domaine (si DNS): http://$DOMAIN"
echo "  👤 Admin Django    : http://$SERVER_IP/admin/"
echo "  🔑 Utilisateur     : admin"
echo "  🔐 Mot de passe    : MartialComp2024!"
echo ""
echo "🗄️ Base de données :"
echo "  🏛️  DigitalOcean   : $DB_HOST:$DB_PORT"
echo "  📊 Database        : $DB_NAME"
echo "  👤 Utilisateur     : $DB_USER"
echo ""
echo "📁 Répertoires :"
echo "  📂 Application     : /home/deploy/martialcomp"
echo "  📊 Logs            : /home/deploy/logs"
echo "  📄 Statiques       : /home/deploy/static"
echo "  📷 Médias          : /home/deploy/media"
echo ""
echo "🔧 Commandes utiles :"
echo "  Status services    : supervisorctl status"
echo "  Logs Django        : tail -f /home/deploy/logs/gunicorn.log"
echo "  Logs Nginx         : tail -f /var/log/nginx/martialcomp_error.log"
echo "  Redémarrer app     : supervisorctl restart martialcomp"
echo ""
echo "🎯 Prochaines étapes :"
echo "  1. 🔒 Configurez SSL avec: certbot --nginx -d $DOMAIN"
echo "  2. 📧 Configurez l'email dans /home/deploy/martialcomp/.env"
echo "  3. 👥 Créez les utilisateurs pilotes via l'admin"
echo "  4. 🧪 Testez toutes les fonctionnalités"
echo ""
echo "=============================================="

# Sauvegarder les informations
echo "$(date): Déploiement MartialComp terminé avec succès" >> /home/deploy/logs/deployment.log
echo "Domain: $DOMAIN, IP: $SERVER_IP, Admin: $ADMIN_EMAIL" >> /home/deploy/logs/deployment.log

log_success "🎉 Déploiement terminé avec succès !"
echo ""
echo "✅ MartialComp est maintenant accessible sur:"
echo "   http://$SERVER_IP"
echo "   http://$SERVER_IP/admin/ (admin / MartialComp2024!)"