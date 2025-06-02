#!/bin/bash

# Vérifier que Django est installé
if ! python -c "import django" &> /dev/null; then
    echo "Django is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Patcher Django pour accepter tous les hôtes
echo "Patching Django host validation..."
DJANGO_REQUEST_PATH="$(python -c 'import django.http.request; print(django.http.request.__file__)')"
echo "Django request module path: $DJANGO_REQUEST_PATH"

# Créer une sauvegarde
cp "$DJANGO_REQUEST_PATH" "${DJANGO_REQUEST_PATH}.bak"

# Appliquer le patch pour toujours accepter martialcomp.onrender.com
sed -i 's/raise DisallowedHost(msg)/if "martialcomp.onrender.com" in host: return host\n        raise DisallowedHost(msg)/' "$DJANGO_REQUEST_PATH"

echo "Django patched. Starting application..."

# Démarrer gunicorn (vérifier qu'il est installé)
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn is not installed. Installing..."
    pip install gunicorn
fi

# Démarrer l'application
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT