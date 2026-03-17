import os
from decouple import config

# Fetch Environment with auto-detection for Vercel/Railway
ENVIRONMENT = config('ENVIRONMENT', default='development')
IS_VERCEL = 'VERCEL' in os.environ
IS_RAILWAY = 'RAILWAY_ENVIRONMENT' in os.environ

if ENVIRONMENT == 'production' or IS_VERCEL or IS_RAILWAY:
    from .production import *
else:
    from .development import *

# Final sanity check for Secret Key
if not globals().get('SECRET_KEY'):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-for-cloud-boot')