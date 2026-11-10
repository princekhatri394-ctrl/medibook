#!/usr/bin/env bash
# Build steps for hosting platforms (e.g. Render "Build Command": ./build.sh)
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Create the admin from DJANGO_SUPERUSER_* variables (skipped if it already exists)
if [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  python manage.py createsuperuser --no-input || echo "Admin already exists, skipping."
fi

if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo --skip-admin
fi
