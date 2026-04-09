#!/bin/bash
set -x
scp /mnt/c/martial_hub_django/martialcomp/api/mobile_api.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/api/mobile_api.py && echo "SCP OK" || echo "SCP FAILED"
ssh martialcomp-production 'sudo systemctl restart gunicorn-martialcomp' && echo "RESTART OK" || echo "RESTART FAILED"
