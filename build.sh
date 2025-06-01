#!/usr/bin/env bash
  set -o errexit

  echo "🚀 Starting MartialComp build process..."

  pip install --upgrade pip
  pip install -r requirements.txt

  export DJANGO_SETTINGS_MODULE=config.settings_render

  echo "🗄️ Running database migrations..."
  python manage.py migrate --noinput

  echo "🏗️ Collecting static files..."
  python manage.py collectstatic --noinput --clear

  echo "✅ Build process completed successfully!"