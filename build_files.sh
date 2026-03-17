#!/bin/bash
echo "=== E-RECYCLO Build Started ==="
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo "=== E-RECYCLO Build Finished ==="
