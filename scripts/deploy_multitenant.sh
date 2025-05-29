#!/bin/bash
#
# MartialComp Multi-tenant Deployment Script
# This script handles the deployment of the multi-tenant application
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/martialcomp"
VENV_DIR="/var/www/martialcomp/venv"
BACKUP_DIR="/var/backups/martialcomp"
LOG_DIR="/var/log/martialcomp"
USER="www-data"
GROUP="www-data"

# Functions
function print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

function print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Create directories if they don't exist
function create_directories() {
    print_status "Creating necessary directories..."
    
    sudo mkdir -p $BACKUP_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p $PROJECT_DIR/static
    sudo mkdir -p $PROJECT_DIR/media
    
    sudo chown -R $USER:$GROUP $PROJECT_DIR
    sudo chown -R $USER:$GROUP $LOG_DIR
}

# Backup current deployment
function backup_current() {
    print_status "Backing up current deployment..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    
    if [ -d "$PROJECT_DIR" ]; then
        sudo tar -czf $BACKUP_FILE -C $PROJECT_DIR .
        print_status "Backup created: $BACKUP_FILE"
    else
        print_warning "No existing deployment to backup"
    fi
}

# Pull latest code
function pull_code() {
    print_status "Pulling latest code from repository..."
    
    cd $PROJECT_DIR
    git pull origin main
    
    # Update permissions
    sudo chown -R $USER:$GROUP $PROJECT_DIR
}

# Install/update dependencies
function install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    # Install multi-tenant specific packages
    pip install psycopg2-binary stripe django-tenants
}

# Run database migrations
function run_migrations() {
    print_status "Running database migrations..."
    
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    # Run migrations for public schema
    python manage.py migrate_schemas --shared
    
    # Run migrations for all tenants
    python manage.py migrate_schemas --tenant
}

# Collect static files
function collect_static() {
    print_status "Collecting static files..."
    
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    python manage.py collectstatic --noinput
    
    # Set permissions
    sudo chown -R $USER:$GROUP $PROJECT_DIR/static
}

# Update translations
function update_translations() {
    print_status "Compiling translations..."
    
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    python manage.py compilemessages
}

# Run tests
function run_tests() {
    print_status "Running tests..."
    
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    # Run multi-tenant specific tests
    python manage.py test multitenant --keepdb || {
        print_error "Tests failed!"
        exit 1
    }
}

# Restart services
function restart_services() {
    print_status "Restarting services..."
    
    # Restart Gunicorn
    sudo systemctl restart gunicorn
    
    # Restart Nginx
    sudo nginx -t && sudo systemctl reload nginx
    
    # Restart Celery (if used)
    if systemctl is-active --quiet celery; then
        sudo systemctl restart celery
        sudo systemctl restart celery-beat
    fi
}

# Create initial tenant
function create_demo_tenant() {
    print_status "Creating demo tenant..."
    
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    # Check if demo tenant already exists
    python manage.py shell -c "
from multitenant.models import Tenant
if not Tenant.objects.filter(slug='demo').exists():
    from django.core.management import call_command
    call_command('create_tenant', 'Demo Club', 'demo', '--continent', 'europe_west', '--plan', 'trial')
    print('Demo tenant created')
else:
    print('Demo tenant already exists')
"
}

# Health check
function health_check() {
    print_status "Performing health check..."
    
    # Check web server
    curl -sf http://localhost/health/ > /dev/null || {
        print_error "Web server health check failed!"
        exit 1
    }
    
    # Check database connection
    source $VENV_DIR/bin/activate
    cd $PROJECT_DIR/martialcomp
    
    python manage.py dbshell -c "SELECT 1;" > /dev/null || {
        print_error "Database connection failed!"
        exit 1
    }
    
    print_status "Health check passed!"
}

# Main deployment flow
function main() {
    print_status "Starting multi-tenant deployment..."
    
    create_directories
    backup_current
    pull_code
    install_dependencies
    run_migrations
    collect_static
    update_translations
    run_tests
    restart_services
    create_demo_tenant
    health_check
    
    print_status "Deployment completed successfully!"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Check command line arguments
if [ "$1" == "--quick" ]; then
    print_status "Quick deployment (skipping tests)..."
    create_directories
    pull_code
    install_dependencies
    run_migrations
    collect_static
    restart_services
    health_check
elif [ "$1" == "--rollback" ]; then
    if [ -z "$2" ]; then
        print_error "Please specify backup file to rollback to"
        exit 1
    fi
    
    print_status "Rolling back to $2..."
    
    if [ ! -f "$2" ]; then
        print_error "Backup file not found: $2"
        exit 1
    fi
    
    # Extract backup
    rm -rf $PROJECT_DIR/*
    tar -xzf $2 -C $PROJECT_DIR
    
    # Restart services
    restart_services
    health_check
else
    main
fi