#!/bin/bash
echo "=== E-RECYCLO Vercel Build (Robust) ==="

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Database Migration Check..."
if [[ -z "$DATABASE_URL" && -z "$POSTGRES_URL" && -z "$NEON_DATABASE_URL" ]]; then
    echo "⚠️  WARNING: No Database URL found in environment variables!"
else
    echo "✅ Database connection string detected."
    echo "Running migrations..."
    python3 manage.py migrate --noinput || { echo "❌ Migration failed!"; exit 1; }
fi

echo "=== Build complete ==="
