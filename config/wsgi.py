"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

# --- AUTO-MIGRATION SAFEGUARD (For Vercel/Cloud) ---
# This ensures the database tables are created automatically on the first run.
if os.environ.get('ENVIRONMENT') == 'production' or 'VERCEL' in os.environ:
    try:
        from django.db import connection
        from django.core.management import call_command
        
        # Check if the main user table exists
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            
        if "accounts_account" not in tables:
            print("🚀 Database is empty. Running migrations...")
            call_command('migrate', interactive=False)
            print("✅ Migrations completed successfully.")
        else:
            print("✅ Database tables confirmed. Skipping migration.")
            
    except Exception as e:
        print(f"⚠️ Auto-migration skipped/failed: {e}")

app = application
