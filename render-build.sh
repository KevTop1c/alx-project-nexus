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

# Ensure all superusers have profiles
python manage.py shell -c "
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()
for user in User.objects.filter(is_superuser=True):
    UserProfile.objects.get_or_create(user=user)
"

# Collect static files
python manage.py collectstatic --no-input