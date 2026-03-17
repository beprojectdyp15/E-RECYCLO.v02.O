#!/bin/bash
echo "=== E-RECYCLO Vercel Build (Fast Mode) ==="

# 1. Install dependencies first
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# 2. Collect static files
# Note: On Vercel, use 'python3' and ensure it's run AFTER pip install
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "=== Build complete (Migrations handled by WSGI) ==="
