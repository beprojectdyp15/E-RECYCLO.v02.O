"""
Management command: mark_system_transactions
============================================
Marks all pre-existing e-waste transactions (PhotoPost lifecycle)
as "E-RECYCLO System" transactions for clean Razorpay testing.

Usage:
    python manage.py mark_system_transactions           # dry-run (preview only)
    python manage.py mark_system_transactions --apply  # actually apply changes
    python manage.py mark_system_transactions --apply --reset-posts  # also archive old posts
"""

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Mark all old e-waste lifecycle transactions as E-RECYCLO System records for clean testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Actually apply changes (default is dry-run preview)',
        )
        parser.add_argument(
            '--reset-posts',
            action='store_true',
            default=False,
            help='Also mark all completed PhotoPosts as archived system records',
        )

    def handle(self, *args, **options):
        apply   = options['apply']
        dry_run = not apply

        self.stdout.write(self.style.WARNING(
            '\n' + ('=' * 60) +
            '\n  E-RECYCLO - Mark System Transactions' +
            ('\n  MODE: DRY RUN (use --apply to commit)' if dry_run else '\n  MODE: APPLYING CHANGES') +
            '\n' + ('=' * 60) + '\n'
        ))

        from apps.payments.models import Wallet, Transaction, WithdrawalRequest
        from apps.client.models import PhotoPost

        # ------------------------------------------------------------------
        # 1. Report existing transactions
        # ------------------------------------------------------------------
        all_transactions = Transaction.objects.all().select_related('wallet__user')
        total = all_transactions.count()

        self.stdout.write('\n[STATS] Transactions in database: %d\n' % total)

        credit_txns   = all_transactions.filter(transaction_type='credit')
        debit_txns    = all_transactions.filter(transaction_type='debit')
        system_tagged = all_transactions.filter(description__startswith='[SYSTEM]')

        self.stdout.write('   Credits               : %d' % credit_txns.count())
        self.stdout.write('   Debits                : %d' % debit_txns.count())
        self.stdout.write('   Already [SYSTEM] tagged: %d\n' % system_tagged.count())

        # ------------------------------------------------------------------
        # 2. Identify transactions to tag
        # ------------------------------------------------------------------
        to_tag = all_transactions.exclude(
            description__startswith='[SYSTEM]'
        ).exclude(
            description__icontains='Razorpay'
        ).exclude(
            description__icontains='Withdrawal'
        )

        self.stdout.write('[TAG] Transactions to tag as system: %d\n' % to_tag.count())

        if to_tag.exists():
            for txn in to_tag[:10]:
                self.stdout.write(
                    '   [%s] Rs.%s | %s | "%s"' % (
                        txn.transaction_type.upper(),
                        txn.amount,
                        txn.wallet.user.email,
                        txn.description[:60],
                    )
                )
            if to_tag.count() > 10:
                self.stdout.write('   ... and %d more' % (to_tag.count() - 10))

        # ------------------------------------------------------------------
        # 3. Show PhotoPost stats
        # ------------------------------------------------------------------
        posts = PhotoPost.objects.all()
        post_counts = {
            'Total':     posts.count(),
            'Completed': posts.filter(status='completed').count(),
            'Pending':   posts.filter(status='pending').count(),
            'Assigned':  posts.filter(status='assigned').count(),
            'Collected': posts.filter(status='collected').count(),
            'Others':    posts.exclude(status__in=['completed', 'pending', 'assigned', 'collected']).count(),
        }

        self.stdout.write('\n[POSTS] PhotoPost Records:')
        for label, count in post_counts.items():
            self.stdout.write('   %-12s: %d' % (label, count))

        # ------------------------------------------------------------------
        # 4. Show Wallet stats
        # ------------------------------------------------------------------
        wallets = Wallet.objects.all().select_related('user')
        self.stdout.write('\n[WALLETS] Wallet Summary (%d wallets):' % wallets.count())
        for w in wallets:
            role = w.user.get_role()
            self.stdout.write(
                '   [%-10s] %-40s  Balance: Rs.%-10s  Earned: Rs.%s' % (
                    role, w.user.email, w.balance, w.total_earned,
                )
            )

        # ------------------------------------------------------------------
        # 5. Apply if --apply flag is set
        # ------------------------------------------------------------------
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n[DRY RUN] Nothing was changed.'
                '\nRun with --apply to commit all changes.\n'
            ))
            return

        # Actually apply
        with db_transaction.atomic():

            # Tag old lifecycle transactions
            tagged_count = 0
            for txn in to_tag:
                txn.description = ('[SYSTEM] ' + txn.description)[:300]
                txn.save(update_fields=['description'])
                tagged_count += 1

            self.stdout.write(self.style.SUCCESS(
                '\n[OK] Tagged %d transaction(s) as [SYSTEM]' % tagged_count
            ))

            # Archive completed posts if --reset-posts
            if options['reset_posts']:
                self.stdout.write('\n[POSTS] Archiving completed PhotoPosts...')
                completed_posts = PhotoPost.objects.filter(status='completed')
                archived = 0
                for post in completed_posts:
                    if not post.vendor_remarks:
                        post.vendor_remarks = '[SYSTEM ARCHIVE] Pre-existing transaction record'
                    elif '[SYSTEM ARCHIVE]' not in post.vendor_remarks:
                        post.vendor_remarks = '[SYSTEM ARCHIVE] ' + post.vendor_remarks
                    post.save(update_fields=['vendor_remarks'])
                    archived += 1

                self.stdout.write(self.style.SUCCESS(
                    '[OK] Archived %d completed PhotoPost(s)' % archived
                ))

        # ------------------------------------------------------------------
        # 6. Final summary
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            '\n' + ('=' * 60) +
            '\n  DONE! Database is clean for Razorpay testing.' +
            '\n' + ('=' * 60) + '\n'
        ))

        self.stdout.write('\n[FINAL STATE]')
        self.stdout.write('   Total transactions  : %d' % Transaction.objects.count())
        self.stdout.write('   [SYSTEM] tagged     : %d' % Transaction.objects.filter(description__startswith='[SYSTEM]').count())
        self.stdout.write('   Razorpay txns       : %d' % Transaction.objects.filter(description__icontains='Razorpay').count())
        self.stdout.write('   Withdrawal txns     : %d' % Transaction.objects.filter(description__icontains='Withdrawal').count())
        self.stdout.write('')
