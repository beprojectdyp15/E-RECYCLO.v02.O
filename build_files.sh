#!/bin/bash
echo "=== E-RECYCLO Vercel Build (Ultimate Fix) ==="

# 1. Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt --quiet

# 2. Fix PYTHONPATH (Vercel installs to a specific location)
export PYTHONPATH=$PYTHONPATH:$(pwd)
export PYTHONPATH=$PYTHONPATH:$(python3 -m site --user-site)

# 3. Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "=== Build complete. Migrations will run on app start. ==="
