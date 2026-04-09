#!/bin/bash
# Deploy task management improvements to production
H=/var/www/vhosts/martialcomp.com/httpdocs

echo "=== Backing up files ==="
cp $H/apps/task_management/views/tasks.py $H/apps/task_management/views/tasks.py.bak_20260224
cp $H/apps/task_management/urls.py $H/apps/task_management/urls.py.bak_20260224
cp $H/apps/task_management/templates/task_management/tasks/task_detail.html $H/apps/task_management/templates/task_management/tasks/task_detail.html.bak_20260224
cp $H/apps/task_management/templates/task_management/base/kanban_base.html $H/apps/task_management/templates/task_management/base/kanban_base.html.bak_20260224
echo "Backup done"

echo "=== Deploying new files ==="
cp /tmp/tm_deploy/tasks.py $H/apps/task_management/views/tasks.py
cp /tmp/tm_deploy/urls.py $H/apps/task_management/urls.py
cp /tmp/tm_deploy/task_detail.html $H/apps/task_management/templates/task_management/tasks/task_detail.html
cp /tmp/tm_deploy/kanban_base.html $H/apps/task_management/templates/task_management/base/kanban_base.html
echo "Deploy done"

echo "=== Restarting gunicorn ==="
sudo systemctl restart gunicorn-martialcomp
sleep 2
sudo systemctl is-active gunicorn-martialcomp
echo "=== ALL DONE ==="
