#!/usr/bin/env bash

# Exit on error
set -o errexit

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Apply any outstanding database migrations
python manage.py migrate --noinput

# Create an admin user (make sure initadmin handles idempotency)
python manage.py initadmin || true

# Collect static files
python manage.py collectstatic --no-input