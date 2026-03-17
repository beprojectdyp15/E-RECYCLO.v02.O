"""
Production settings for E-RECYCLO on Railway
GMAIL SMTP Configuration
"""

from .base import *
import os
from decouple import config
import dj_database_url

# ========================================
# DEBUG - allow override from Env Vars
# ========================================
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# ========================================
# ALLOWED HOSTS
# ========================================

ALLOWED_HOSTS = [
    '.railway.app',
    '.vercel.app',
    'localhost',
    '127.0.0.1',
]

# Add custom domain if you set one later
if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('RAILWAY_PUBLIC_DOMAIN'))
if os.environ.get('VERCEL_URL'):
    ALLOWED_HOSTS.append(os.environ.get('VERCEL_URL'))

# ========================================
# DATABASE - COMPLETELY OVERRIDE base.py
# ========================================

db_url = (
    os.environ.get('DATABASE_URL') or 
    os.environ.get('POSTGRES_URL') or 
    os.environ.get('NEON_DATABASE_URL') or 
    os.environ.get('STORAGE_URL')
)

if db_url:
    DATABASES = {
        'default': dj_database_url.parse(
            db_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,  # Vercel postgres requires SSL
        )
    }
else:
    # Fallback to base.py settings
    pass

# ========================================
# SECURITY SETTINGS
# ========================================

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.vercel.app',
]

# ========================================
# EMAIL SETTINGS (GMAIL SMTP)
# ========================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='E-RECYCLO <noreply@erecyclo.in>')

# OTP Settings
OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', default=10, cast=int)

# ========================================
# STATIC & MEDIA FILES (WhiteNoise & Supabase S3)
# ========================================

# WhiteNoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Storage Configuration (Django 4.2+ Style)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'media')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')

# If Supabase S3 keys are present, enable cloud storage
if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT_URL]):
    # Define STORAGES for Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    # Supabase Specific S3 Settings
    AWS_QUERYSTRING_AUTH = False  # Critical for public URLs
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_FILE_OVERWRITE = False
    
    # Generate Public Media URL for Supabase
    try:
        # Extract project ID from endpoint: https://[project-id].storage.supabase.co
        project_id = AWS_S3_ENDPOINT_URL.replace('https://', '').split('.storage')[0]
        MEDIA_URL = f'https://{project_id}.supabase.co/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}/'
        # Important for django-storages to build correct URLs
        AWS_S3_CUSTOM_DOMAIN = f'{project_id}.supabase.co/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}'
    except Exception:
        MEDIA_URL = '/media/'
        
else:
    # Local fallback
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ========================================
# REDIS CACHING
# ========================================

if 'REDIS_URL' in os.environ:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'KEY_PREFIX': 'erecyclo',
            'TIMEOUT': 300,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ========================================
# CELERY (if using)
# ========================================

if 'REDIS_URL' in os.environ:
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

# ========================================
# LOGGING
# ========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ========================================
# ADMINS
# ========================================

ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='erecyclo.web@gmail.com')),
]

MANAGERS = ADMINS