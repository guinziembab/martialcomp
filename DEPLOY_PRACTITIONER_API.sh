#!/bin/bash
# =============================================================================
# Deployment: Practitioner Mobile API Fix
# Date: 2026-01-23
# =============================================================================

set -e

PROD_HOST="martialcomp-production"
PROD_PATH="/var/www/martialcomp/martialcomp"

echo "=========================================="
echo "Deploying Practitioner Mobile API Fix"
echo "=========================================="

# Copy updated API files
echo "1. Copying mobile_api.py..."
scp api/mobile_api.py ${PROD_HOST}:${PROD_PATH}/api/mobile_api.py

echo "2. Copying mobile_urls.py..."
scp api/mobile_urls.py ${PROD_HOST}:${PROD_PATH}/api/mobile_urls.py

# Restart Gunicorn
echo "3. Restarting Gunicorn..."
ssh ${PROD_HOST} "sudo kill -HUP 3991819"

echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Test the API with:"
echo "curl -H 'Authorization: Bearer <token>' https://martialcomp.com/api/v1/mobile/practitioners/1/"
