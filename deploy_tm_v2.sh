#!/bin/bash
H=/var/www/vhosts/martialcomp.com/httpdocs
cp /tmp/tm_deploy/tasks.py $H/apps/task_management/views/tasks.py
cp /tmp/tm_deploy/task_detail.html $H/apps/task_management/templates/task_management/tasks/task_detail.html
echo "Files copied"
sudo systemctl restart gunicorn-martialcomp
sleep 2
sudo systemctl is-active gunicorn-martialcomp
