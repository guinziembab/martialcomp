#!/bin/bash
scp /mnt/c/martial_hub_django/martialcomp/api/mobile_api.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/api/mobile_api.py
echo "SCP done"
ssh martialcomp-production 'sudo systemctl restart gunicorn-martialcomp'
echo "Restart done"
