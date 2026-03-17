#!/bin/bash
echo "=== E-RECYCLO Ultimate Vercel Build ==="

# 1. Install dependencies into the local user space
echo "Installing dependencies..."
python3 -m pip install --user -r requirements.txt --quiet

# 2. Force the path to include the local user site-packages
export PYTHONUSERBASE=$(python3 -m site --user-base)
export PATH=$PATH:$PYTHONUSERBASE/bin

# 3. Verify Django is reachable
if python3 -c "import django; print('Django version:', django.get_version())" > /dev/null 2>&1; then
    echo "✅ Django is successfully installed and reachable."
    
    # 4. Collect static files
    echo "Collecting static files..."
    python3 manage.py collectstatic --noinput --clear
else
    echo "❌ ERROR: Django still not found. Attempting emergency fallbacks..."
    # Fallback to direct library search
    export PYTHONPATH=$PYTHONPATH:$(python3 -m site --user-site)
    python3 manage.py collectstatic --noinput --clear
fi

echo "=== Build complete. Migrations will run at runtime. ==="
