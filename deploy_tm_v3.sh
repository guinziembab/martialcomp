#!/bin/bash
H=/var/www/vhosts/martialcomp.com/httpdocs
cp /tmp/tm_deploy/tasks.py $H/apps/task_management/views/tasks.py
echo "tasks.py deployed"
sudo systemctl restart gunicorn-martialcomp
sleep 2
sudo systemctl is-active gunicorn-martialcomp
