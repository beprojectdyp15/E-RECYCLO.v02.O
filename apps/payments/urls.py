"""apps/payments/urls.py"""
from django.urls import path
from apps.payments import views

app_name = 'payments'

urlpatterns = [
    # Vendor: top-up wallet (dedicated page)
    path('topup/',                      views.topup_page,             name='topup_page'),
    path('topup/initiate/',             views.topup_initiate,         name='topup_initiate'),
    path('topup/verify/',               views.topup_verify,           name='topup_verify'),

    # Client & Collector: withdraw (shared dedicated page)
    path('withdraw/',                   views.withdraw_page,          name='withdraw_page'),
    path('withdraw/request/',           views.request_withdrawal,     name='request_withdrawal'),

    # Admin: manage all withdrawal requests
    path('withdraw/admin/',             views.withdrawal_requests_page, name='withdrawal_requests'),
    path('withdraw/<int:pk>/process/',  views.process_withdrawal,     name='process_withdrawal'),

    # Razorpay webhook (no CSRF)
    path('webhook/',                    views.razorpay_webhook,       name='razorpay_webhook'),
]