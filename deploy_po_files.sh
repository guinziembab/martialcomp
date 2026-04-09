#!/bin/bash
cd /mnt/c/martial_hub_django/martialcomp
for lang in en de es it pt ar ja ko zh ru hi no sw vi yo am zu; do
    scp "locale/${lang}/LC_MESSAGES/django.po" "martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/locale/${lang}/LC_MESSAGES/django.po" && echo "OK: ${lang}" || echo "FAIL: ${lang}"
done
echo "All .po files deployed. Compiling on server..."
ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py compilemessages 2>&1 | tail -5'
echo "Restarting gunicorn..."
ssh martialcomp-production 'sudo systemctl restart gunicorn-martialcomp'
echo "Done!"
