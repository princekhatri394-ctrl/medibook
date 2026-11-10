#!/usr/bin/env bash
# Build steps for hosting platforms (e.g. Render "Build Command": ./build.sh)
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
