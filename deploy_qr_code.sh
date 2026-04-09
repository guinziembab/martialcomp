#!/bin/bash
# Deploy QR code and updated welcome template to production
set -e

HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Deploying QR Code to production ==="

# 1. Create QR directory on server
echo "Creating QR directory..."
ssh martialcomp-production "mkdir -p $HTTPDOCS/static/images/qr"

# 2. Copy QR code images
echo "Copying QR code images..."
scp /tmp/martialcomp_qr_gold.png martialcomp-production:$HTTPDOCS/static/images/qr/
scp /tmp/martialcomp_qr_print.png martialcomp-production:$HTTPDOCS/static/images/qr/
scp /tmp/martialcomp_qr_web.png martialcomp-production:$HTTPDOCS/static/images/qr/

# 3. Copy updated welcome template
echo "Copying updated welcome template..."
scp /tmp/welcome.html martialcomp-production:$HTTPDOCS/apps/competitions/templates/competitions/welcome.html

# 4. Collect static files and restart
echo "Collecting static files and restarting..."
ssh martialcomp-production "cd $HTTPDOCS && source ../venv/bin/activate && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn-martialcomp"

echo "=== Deployment complete ==="
