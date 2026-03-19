"""
Main URL configuration for E-RECYCLO
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as account_views
from apps.pages import views as page_views
from django.views.generic.base import RedirectView

urlpatterns = [
    # Home
    path('', account_views.home_view, name='home'),

    # Django Admin
    path('admin/', admin.site.urls),

    # Public informational pages                    ← NEW
    path('', include('apps.pages.urls')),

    # Apps
    path('accounts/', include('apps.accounts.urls')),
    path('client/', include('apps.client.urls')),
    path('vendor/', include('apps.vendor.urls')),
    path('collector/', include('apps.collector.urls')),
    path('admin-panel/', include('apps.admin_custom.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.ai_services.urls')),
    path("payments/", include("apps.payments.urls", namespace="payments")),
    
    # Favicon redirect for browsers that ignore the link tag
    path('favicon.ico', RedirectView.as_view(url=settings.MEDIA_URL + 'system_images/favicon/favicon.ico', permanent=True)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site headers
admin.site.site_header = "E-RECYCLO Administration"
admin.site.site_title  = "E-RECYCLO Admin"
admin.site.index_title = "Welcome to E-RECYCLO Administration"

# ── Custom error handlers ──────────────────────────────────────────────────
# These replace Django's default error pages with your branded 404 and 403.
# Works in both DEBUG=True and DEBUG=False.
handler404 = 'apps.pages.views.handler_404'
handler403 = 'apps.pages.views.handler_403'
handler500 = 'apps.pages.views.handler_500'