#!/bin/bash
set -e
cd "$(dirname "$0")"

DEST="martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/locale"

for loc in de es it pt ar hi ja ko no ru sw vi yo zh zu am; do
    scp "locale/${loc}/LC_MESSAGES/django.po" "locale/${loc}/LC_MESSAGES/django.mo" "${DEST}/${loc}/LC_MESSAGES/"
    echo "${loc} OK"
done

echo "=== Restarting Gunicorn ==="
ssh martialcomp-production "sudo systemctl restart gunicorn-martialcomp"
echo "=== All translations deployed! ==="
