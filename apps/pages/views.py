from django.shortcuts import render, redirect
from django.contrib import messages as django_messages

# ── Category list for "How It Works" page ────────────────────────────────────
_CATEGORIES = [
    {'icon': 'smartphone',            'label': 'Smartphone & Mobile'},
    {'icon': 'laptop_mac',            'label': 'Laptop & Notebook'},
    {'icon': 'computer',              'label': 'Desktop Computer'},
    {'icon': 'tablet_mac',            'label': 'Tablet & E-Reader'},
    {'icon': 'monitor',               'label': 'Monitor & Television'},
    {'icon': 'battery_charging_full', 'label': 'Battery & Charger'},
    {'icon': 'keyboard',              'label': 'Computer Peripheral'},
    {'icon': 'headphones',            'label': 'Audio & Camera'},
    {'icon': 'storage',               'label': 'Storage & Networking'},
    {'icon': 'sports_esports',        'label': 'Gaming Equipment'},
    {'icon': 'kitchen',               'label': 'Large Appliance'},
    {'icon': 'blender',               'label': 'Small Appliance'},
    {'icon': 'cable',                 'label': 'Cable, Printer & Component'},
]

def about_view(request):
    return render(request, 'pages/about.html')

def how_it_works_view(request):
    return render(request, 'pages/how_it_works.html', {'categories': _CATEGORIES})

def impact_view(request):
    return render(request, 'pages/impact.html')

def faq_view(request):
    return render(request, 'pages/faq.html')

def privacy_view(request):
    return render(request, 'pages/privacy.html')

def terms_view(request):
    return render(request, 'pages/terms.html')

def contact_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        subject    = request.POST.get('subject', '').strip()
        message    = request.POST.get('message', '').strip()

        if not all([first_name, last_name, email, subject, message]):
            django_messages.error(request, 'Please fill in all required fields.')
            return render(request, 'pages/contact.html')

        # Logic for sending email could go here
        
        django_messages.success(
            request,
            f"Thanks {first_name}! We've received your message and will get back to you within 24 hours."
        )
        return redirect('pages:contact')

    return render(request, 'pages/contact.html')

# ── Custom error handlers ─────────────────────────────────────────────────────

def handler_404(request, exception=None):
    return render(request, '404.html', status=404)

def handler_403(request, exception=None):
    return render(request, '403.html', status=403)

def handler_500(request):
    return render(request, '500.html', status=500)

def media_check_view(request):
    """Diagnose media storage settings on Vercel"""
    from django.conf import settings
    import os
    
    # We use a dictionary to keep track of what we find
    results = {
        'ENVIRONMENT': os.environ.get('ENVIRONMENT', 'Not Set'),
        'VERCEL': os.environ.get('VERCEL', 'Not Set'),
        'AWS_ACCESS_KEY_ID_FOUND': bool(os.environ.get('AWS_ACCESS_KEY_ID')),
        'AWS_SECRET_ACCESS_KEY_FOUND': bool(os.environ.get('AWS_SECRET_ACCESS_KEY')),
        'AWS_S3_ENDPOINT_URL_FOUND': bool(os.environ.get('AWS_S3_ENDPOINT_URL')),
        'AWS_STORAGE_BUCKET_NAME': os.environ.get('AWS_STORAGE_BUCKET_NAME', 'Not Set'),
        'MEDIA_URL': settings.MEDIA_URL,
        'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage'),
    }
    
    # For security, we NEVER show the actual keys, only if they are present
    return render(request, 'pages/media_check.html', {'results': results})
