"""apps/payments/urls.py"""
from django.urls import path
from apps.payments import views

app_name = 'payments'

urlpatterns = [
    # Vendor: top-up wallet
    path('topup/initiate/',         views.topup_initiate,    name='topup_initiate'),
    path('topup/verify/',           views.topup_verify,      name='topup_verify'),
    # Razorpay server-side webhook (no CSRF)
    path('webhook/',                views.razorpay_webhook,  name='razorpay_webhook'),
    # Client / Collector: withdraw
    path('withdraw/request/',       views.request_withdrawal, name='request_withdrawal'),
    # Admin: approve withdrawal and trigger Razorpay Payout
    path('withdraw/<int:pk>/process/', views.process_withdrawal, name='process_withdrawal'),
]
