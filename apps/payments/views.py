"""
apps/payments/views.py
──────────────────────────────────────────────────────────────────
Razorpay-integrated wallet system for eRecyclo.

Money flow:
  Vendor top-up   →  Razorpay Order → User pays → Webhook verifies → Wallet credited
  Internal payout →  vendor.wallet.debit() / client.wallet.credit()  (already works)
  Withdrawal      →  WithdrawalRequest (pending) → Admin approves → Razorpay Payout
──────────────────────────────────────────────────────────────────
"""

import json
import hmac
import hashlib
import logging

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.payments.models import (
    RazorpayOrder, Transaction, Wallet, WithdrawalRequest,
)

logger = logging.getLogger(__name__)

# ── Razorpay client (lazy so missing key doesn't crash on import) ─────────────
def _rzp():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


# ══════════════════════════════════════════════════════════════════════════════
#  VENDOR  — Top-up wallet
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def topup_initiate(request):
    """
    POST: Create a Razorpay order for vendor wallet top-up.
    Returns JSON {order_id, amount, currency, key_id} for Razorpay checkout.js.
    """
    try:
        if not request.user.is_vendor:
            return JsonResponse({'error': 'Access denied: Only vendors can perform this action.'}, status=403)

        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method. POST is required.'}, status=405)

        try:
            data   = json.loads(request.body)
            amount = int(float(data.get('amount', 0)))   # ₹ rupees
        except (ValueError, KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid amount provided.'}, status=400)

        if amount < 100:
            return JsonResponse({'error': 'Minimum top-up is ₹100'}, status=400)
        
        amount_paise = amount * 100   # Razorpay uses paise

        try:
            # Check if keys are set
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                logger.error("Razorpay keys are missing from settings.")
                return JsonResponse({'error': 'Payment gateway is not configured on the server. Please check environment variables.'}, status=500)

            rzp_order = _rzp().order.create({
                'amount':   amount_paise,
                'currency': 'INR',
                'receipt':  f'topup_{request.user.pk}_{timezone.now().strftime("%Y%m%d%H%M%S")}',
                'notes': {
                    'user_id':   str(request.user.pk),
                    'purpose':   'wallet_topup',
                },
                'payment_capture': 1,
            })
        except Exception as exc:
            logger.exception('Razorpay order creation failed: %s', exc)
            return JsonResponse({'error': f'Gateway Error: {str(exc)}'}, status=502)

        # Store order in DB so webhook can look it up
        RazorpayOrder.objects.create(
            user=request.user,
            razorpay_order_id=rzp_order['id'],
            amount=amount,
            purpose='wallet_topup',
            status='created',
        )

        return JsonResponse({
            'order_id':  rzp_order['id'],
            'amount':    amount_paise,
            'currency':  'INR',
            'key_id':    settings.RAZORPAY_KEY_ID,
            'name':      'eRecyclo',
            'description': f'Wallet top-up ₹{amount}',
            'prefill': {
                'name':  request.user.get_full_name(),
                'email': request.user.email,
            },
        })
    except Exception as e:
        logger.exception("Final safety catch in topup_initiate: %s", e)
        return JsonResponse({'error': 'A server-side error occurred. Please check logs.'}, status=500)


@login_required
@require_POST
def topup_verify(request):
    """
    POST: Client-side verification after Razorpay checkout succeeds.
    Validates signature and credits wallet immediately (backup to webhook).
    """
    if not request.user.is_vendor:
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        data = json.loads(request.body)
        rzp_order_id   = data['razorpay_order_id']
        rzp_payment_id = data['razorpay_payment_id']
        rzp_signature  = data['razorpay_signature']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    # Signature verification
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f'{rzp_order_id}|{rzp_payment_id}'.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, rzp_signature):
        logger.warning('Razorpay signature mismatch for order %s', rzp_order_id)
        return JsonResponse({'error': 'Signature verification failed'}, status=400)

    # Find local order record
    try:
        order_rec = RazorpayOrder.objects.get(
            razorpay_order_id=rzp_order_id,
            user=request.user,
            status='created',
        )
    except RazorpayOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found or already processed'}, status=404)

    # Idempotent credit — only once
    order_rec.razorpay_payment_id = rzp_payment_id
    order_rec.status = 'paid'
    order_rec.save()

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.credit(
        order_rec.amount,
        description=f'Wallet top-up via Razorpay (#{rzp_payment_id})',
    )

    logger.info('Wallet credited ₹%s for user %s (payment %s)', order_rec.amount, request.user.email, rzp_payment_id)
    return JsonResponse({'status': 'ok', 'new_balance': str(wallet.balance)})


# ══════════════════════════════════════════════════════════════════════════════
#  WEBHOOK  — Server-side payment confirmation from Razorpay
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def razorpay_webhook(request):
    """
    Razorpay sends POST to /payments/webhook/ on every payment event.
    Handles payment.captured as a reliable server-side confirmation.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    payload   = request.body
    signature = request.headers.get('X-Razorpay-Signature', '')

    # Verify webhook signature
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        logger.warning('Webhook signature mismatch')
        return HttpResponse(status=400)

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if event.get('event') == 'payment.captured':
        payment    = event['payload']['payment']['entity']
        order_id   = payment.get('order_id')
        payment_id = payment['id']
        amount_paise = payment['amount']

        try:
            order_rec = RazorpayOrder.objects.get(razorpay_order_id=order_id)
        except RazorpayOrder.DoesNotExist:
            logger.error('Webhook: order %s not found', order_id)
            return HttpResponse(status=200)   # ack anyway

        if order_rec.status == 'paid':
            return HttpResponse(status=200)   # already credited via verify endpoint

        order_rec.razorpay_payment_id = payment_id
        order_rec.status = 'paid'
        order_rec.save()

        if order_rec.purpose == 'wallet_topup':
            wallet, _ = Wallet.objects.get_or_create(user=order_rec.user)
            # Only credit if verify endpoint didn't already do it
            already = Transaction.objects.filter(
                wallet=wallet,
                description__icontains=payment_id,
            ).exists()
            if not already:
                wallet.credit(
                    order_rec.amount,
                    description=f'Wallet top-up via Razorpay (#{payment_id})',
                )
                logger.info('Webhook credited ₹%s for %s', order_rec.amount, order_rec.user.email)

    return HttpResponse(status=200)


# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT / COLLECTOR  — Withdrawal request
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def request_withdrawal(request):
    """
    POST: Client or Collector submits a withdrawal request.
    Admin approves → process_withdrawal sends Razorpay Payout.
    """
    if not (request.user.is_client or request.user.is_collector):
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        data   = json.loads(request.body)
        amount = float(data.get('amount', 0))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    if amount < 50:
        return JsonResponse({'error': 'Minimum withdrawal is ₹50'}, status=400)

    try:
        wallet = request.user.wallet
    except Exception:
        return JsonResponse({'error': 'Wallet not found'}, status=404)

    from decimal import Decimal
    if wallet.balance < Decimal(str(amount)):
        return JsonResponse({'error': 'Insufficient balance'}, status=400)

    # Validate payout details
    method = data.get('payment_method', 'upi')
    wr_kwargs = dict(
        user=request.user,
        amount=amount,
        payment_method=method,
    )
    if method == 'bank':
        required = ['bank_name', 'account_number', 'ifsc_code', 'account_holder_name']
        for field in required:
            if not data.get(field, '').strip():
                return JsonResponse({'error': f'Missing field: {field}'}, status=400)
        wr_kwargs.update({
            'bank_name':           data['bank_name'].strip(),
            'account_number':      data['account_number'].strip(),
            'ifsc_code':           data['ifsc_code'].strip().upper(),
            'account_holder_name': data['account_holder_name'].strip(),
        })
    else:
        upi_id = data.get('upi_id', '').strip()
        if not upi_id or '@' not in upi_id:
            return JsonResponse({'error': 'Valid UPI ID required (e.g. name@upi)'}, status=400)
        wr_kwargs['upi_id'] = upi_id

    # Lock balance immediately (hold)
    from decimal import Decimal as D
    wallet.balance -= D(str(amount))
    wallet.save()
    Transaction.objects.create(
        wallet=wallet,
        transaction_type='debit',
        amount=amount,
        description=f'Withdrawal request (pending admin approval)',
        balance_after=wallet.balance,
    )

    WithdrawalRequest.objects.create(**wr_kwargs)

    return JsonResponse({'status': 'ok', 'message': 'Withdrawal request submitted. Admin will process within 24 hours.'})


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN  — Process approved withdrawal via Razorpay Payout
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def process_withdrawal(request, pk):
    """
    Admin-only: approve and trigger a Razorpay Payout for a WithdrawalRequest.
    Money flows: eRecyclo Razorpay account → user's bank/UPI.
    """
    if not (request.user.is_staff or getattr(request.user, 'is_admin', False)):
        return JsonResponse({'error': 'Admin access required'}, status=403)

    wr = get_object_or_404(WithdrawalRequest, pk=pk, status='pending')

    if request.method == 'POST':
        try:
            data    = json.loads(request.body)
            action  = data.get('action', 'approve')
        except json.JSONDecodeError:
            action = request.POST.get('action', 'approve')

        if action == 'reject':
            remarks = data.get('remarks', '') if request.content_type == 'application/json' else request.POST.get('remarks', '')
            # Refund balance
            try:
                wallet = wr.user.wallet
                from decimal import Decimal as D
                wallet.balance += D(str(wr.amount))
                wallet.save()
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=wr.amount,
                    description=f'Withdrawal rejected — amount refunded',
                    balance_after=wallet.balance,
                )
            except Exception:
                pass
            wr.status = 'rejected'
            wr.admin_remarks = remarks
            wr.processed_at = timezone.now()
            wr.save()
            return JsonResponse({'status': 'rejected'})

        # ── Send Razorpay Payout ──────────────────────────────────────────────
        payout_payload = {
            'account_number': settings.RAZORPAY_ACCOUNT_NUMBER,
            'amount':         int(float(wr.amount) * 100),
            'currency':       'INR',
            'mode':           'UPI' if wr.payment_method == 'upi' else 'NEFT',
            'purpose':        'payout',
            'queue_if_low_balance': True,
            'reference_id':   f'erecyclo_wr_{wr.pk}',
            'narration':      f'eRecyclo withdrawal #{wr.pk}',
        }

        if wr.payment_method == 'upi':
            payout_payload['fund_account'] = {
                'account_type': 'vpa',
                'vpa':          {'address': wr.upi_id},
                'contact': {
                    'name':    wr.user.get_full_name(),
                    'email':   wr.user.email,
                    'contact': getattr(wr.user, 'phone', ''),
                    'type':    'customer',
                },
            }
        else:
            payout_payload['fund_account'] = {
                'account_type': 'bank_account',
                'bank_account': {
                    'name':           wr.account_holder_name,
                    'ifsc':           wr.ifsc_code,
                    'account_number': wr.account_number,
                },
                'contact': {
                    'name':    wr.user.get_full_name(),
                    'email':   wr.user.email,
                    'contact': getattr(wr.user, 'phone', ''),
                    'type':    'customer',
                },
            }

        try:
            payout = _rzp().payout.create(payout_payload)
            wr.razorpay_payout_id = payout.get('id', '')
            wr.status = 'processing'
            wr.processed_at = timezone.now()
            wr.save()
            return JsonResponse({'status': 'processing', 'payout_id': payout.get('id')})
        except Exception as exc:
            logger.exception('Razorpay payout failed for WR %s: %s', wr.pk, exc)
            return JsonResponse({'error': f'Payout failed: {str(exc)}'}, status=502)

    return JsonResponse({'error': 'POST required'}, status=405)
